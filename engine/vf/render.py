"""Render chapters: compositor frames -> ffmpeg (subtitles/credits burned here, final quality, ONE encode).

  vf render --changed        render every chapter whose inputs changed since its last good render
  vf render CH3 CH5          force these chapters
  vf render all              force everything
Chapters are independent files encoded with identical settings, so `vf final` joins them with
`concat -c copy` without re-encoding video. Inputs of every chapter are hashed into out/render_state.json.
"""
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np

from . import config
from .compositor import OverlayReader, VideoReader, composite, image_frame, load_image, video_frame
from .look import Look

OUT = Path("out")
STATE = OUT / "render_state.json"
ENGINE = Path(__file__).resolve().parent


def _tl():
    return json.loads((OUT / "timeline.json").read_text())


def _file_sig(p):
    try:
        st = os.stat(p)
        return f"{p}:{st.st_size}:{int(st.st_mtime)}"
    except OSError:
        return f"{p}:missing"


def _engine_sig():
    h = hashlib.sha256()
    # only modules that change pixels (editing qa/review/report must not invalidate renders)
    for p in sorted(list(ENGINE.glob("gfx/*.py")) + [ENGINE / f for f in
                    ("render.py", "compositor.py", "look.py", "media.py", "config.py", "assets.py")]):
        h.update(p.read_bytes())
    for p in ("custom_gfx.py", "graphics.yaml", "project.yaml"):
        if os.path.exists(p):
            h.update(Path(p).read_bytes())
    return h.hexdigest()


def chapter_hash(tl, chid, engine_sig=None):
    items = [e for e in tl["timeline"] if e.get("ch") == chid and e["type"] in ("card", "shot")]
    ch = next(c for c in tl["chapters"] if c["id"] == chid)
    h = hashlib.sha256()
    h.update(json.dumps([items, ch, tl["chapters"][0]["id"] == chid, tl["total"] if chid == tl["chapters"][-1]["id"] else 0],
                        sort_keys=True, ensure_ascii=False).encode())
    ass = OUT / f"ass_{chid}.ass"
    h.update(ass.read_bytes() if ass.exists() else b"")
    for e in items:
        ov = e.get("opts", {}).get("overlay", "")
        if ov.startswith("anim:"):
            h.update(_file_sig(ov[5:]).encode())
        if e["type"] == "shot" and e.get("path") and e["kind"] != "gfx":
            h.update(_file_sig(e["path"]).encode())
            if e["kind"] == "video":
                h.update(_file_sig(f"assets/scenes/{Path(e['path']).stem}.json").encode())
    h.update((engine_sig or _engine_sig()).encode())
    return h.hexdigest()


def _state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def changed(tl=None):
    tl = tl or _tl()
    st, sig = _state(), _engine_sig()
    out = []
    for c in tl["chapters"]:
        f = OUT / f"ch_{c['id']}.mp4"
        if not f.exists() or st.get(c["id"]) != chapter_hash(tl, c["id"], sig):
            out.append(c["id"])
    return out


def encoder_args(threads):
    e = config.load()["encode"]
    _, _, FPS = config.size()
    return ["-c:v", "libx264", "-preset", e["preset"], "-crf", str(e["crf"]), "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-r", str(FPS), "-g", str(FPS * 2), "-threads", str(threads)]


def _trans(spec):
    """'fade:0.5' | 'dissolve:0.6' | 'cut' | None -> (kind or None, seconds)."""
    if not spec or spec == "cut":
        return None, 0.0
    kind, _, sec = str(spec).partition(":")
    return kind, float(sec or 0.5)


def render_chapter(chid, threads=2):
    from . import gfx
    W, H, FPS = config.size()
    cfg = config.load()
    tl = _tl()
    if tl.get("errors"):
        raise SystemExit(f"timeline has asset errors - fix them first (vf preflight): {tl['errors'][:3]}")
    chs = tl["chapters"]
    ch = next(c for c in chs if c["id"] == chid)
    first, last = chs[0]["id"] == chid, chs[-1]["id"] == chid
    items = [e for e in tl["timeline"] if e.get("ch") == chid and e["type"] in ("card", "shot")]
    end = ch.get("end_film", ch["end"]) if last else ch["end"]
    end_t0 = ch["end"]
    f0, f1 = round(ch["start"] * FPS), round(end * FPS)
    look = Look()
    out = OUT / f"ch_{chid}.mp4"
    tmp = OUT / f"ch_{chid}.part.mp4"
    ass = OUT / f"ass_{chid}.ass"
    vf = f"ass={ass}:fontsdir={config.FONTS_DIR}"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf", vf, *encoder_args(threads), "-an", str(tmp)],
                           stdin=subprocess.PIPE)
    d = cfg["design"]
    tr = d["transitions"]
    card_gfx = d["chapter_card"].get("gfx") or "chapter"
    reader, ov_reader, idx = None, None, -1
    card_ends = {round(c["t1"], 3) for c in items if c["type"] == "card"}
    prev_out = None          # last written frame of the previous item (for dissolves)
    hold = None
    t_start = time.time()
    try:
        for fi in range(f0, f1):
            t = fi / FPS
            e = None
            for k in range(max(idx, 0), len(items)):
                if items[k]["t0"] - 1e-6 <= t < items[k]["t1"] - 1e-6:
                    e = items[k]
                    if k != idx:
                        for r_ in (reader, ov_reader):
                            if r_:
                                r_.close()
                        reader = ov_reader = None
                        idx = k
                        hold = prev_out
                        if e["type"] == "shot" and e["kind"] == "video":
                            reader = VideoReader(e["path"], e["in"] or 0.0, e["t1"] - e["t0"],
                                                 float(e["opts"].get("min_speed", 0.5)),
                                                 e["opts"].get("cross_cuts") == "1")
                        ov = e.get("opts", {}).get("overlay", "")
                        if ov.startswith("anim:"):
                            ov_reader = OverlayReader(ov[5:], e["t1"] - e["t0"], float(e["opts"].get("overlay_in", 0)))
                    break
            photo = False
            if e is None:
                frame = np.zeros((H, W, 3), np.uint8)
            else:
                dur = e["t1"] - e["t0"]
                lt = t - e["t0"]
                u = lt / max(dur, 1e-3)
                if e["type"] == "card":
                    frame = np.array(gfx.render(card_gfx, {"num": e["num"], "title": e["title"], **e.get("opts", {})}, lt, dur))
                elif e["kind"] == "gfx":
                    frame = np.array(gfx.render(e["path"], e["opts"], lt, dur))
                elif e["kind"] == "image":
                    frame = image_frame(load_image(e["path"]), e["opts"], u)
                    photo = True
                elif e["kind"] == "video":
                    push = float(e["opts"]["push"]) if "push" in e["opts"] else None
                    frame = video_frame(reader.read(), reader, u, push)
                    photo = e.get("cls", "real") == "real"      # animation clips are not graded like footage
                else:
                    raise SystemExit(f"unrenderable shot {e.get('scene')} {e.get('src')}")
                dim = float(e["opts"].get("dim", 0)) if e["type"] == "shot" else 0
                if dim:
                    frame = cv2.convertScaleAbs(frame, alpha=1 - dim)
            frame = look.apply(frame, fi, photo, (e or {}).get("grade"))
            if e is not None and e["type"] == "shot":
                ov = e["opts"].get("overlay", "")
                if ov.startswith("gfx:"):
                    frame = composite(frame, gfx.render(ov[4:], e["opts"], t - e["t0"], e["t1"] - e["t0"], rgba=True))
                elif ov_reader:
                    frame = composite(frame, ov_reader.read())
            # transitions: shot option in=/out=, chapter-card and film defaults (design.transitions)
            if e is not None:
                lt, dur = t - e["t0"], e["t1"] - e["t0"]
                tin = e.get("opts", {}).get("in")
                if not tin and e["type"] == "shot" and round(e["t0"], 3) in card_ends:
                    tin = tr.get("after_card")
                kind, sec = _trans(tin)
                if kind and lt < sec:
                    a = lt / sec
                    if kind == "fade":
                        frame = cv2.convertScaleAbs(frame, alpha=a)
                    elif kind == "dissolve" and hold is not None:
                        frame = cv2.addWeighted(hold, 1 - a, frame, a, 0)
                kind, sec = _trans(e.get("opts", {}).get("out"))
                if kind == "fade" and dur - lt < sec:
                    frame = cv2.convertScaleAbs(frame, alpha=max(0.0, (dur - lt) / sec))
            kind, sec = _trans(tr.get("film_in"))
            if first and kind and t < sec:
                frame = cv2.convertScaleAbs(frame, alpha=t / sec)
            kind, sec = _trans(tr.get("film_out"))
            if last and kind and t > end_t0 - sec:
                frame = cv2.convertScaleAbs(frame, alpha=max(0.0, 1 - (t - (end_t0 - sec)) / sec))
            prev_out = frame
            enc.stdin.write(frame.tobytes())
    finally:
        for r_ in (reader, ov_reader):
            if r_:
                r_.close()
        enc.stdin.close()
        rc = enc.wait()
    if rc != 0:
        raise SystemExit(f"encoder failed for {chid}")
    os.replace(tmp, out)
    st = _state()
    st[chid] = chapter_hash(tl, chid)
    STATE.write_text(json.dumps(st, indent=1))
    el = time.time() - t_start
    print(f"rendered {chid}: {f1 - f0} frames in {el / 60:.1f} min ({(f1 - f0) / max(el, 1):.1f} fps)", flush=True)


def render_many(chids, jobs=0):
    """Render chapters in parallel subprocesses; logs in out/logs/render_<CH>.log."""
    if not chids:
        print("nothing to render (all chapters up to date)")
        return True
    cores = os.cpu_count() or 2
    jobs = jobs or config.load()["encode"]["jobs"] or max(1, min(len(chids), cores // 2))
    threads = max(1, cores // jobs)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    # longest chapters first so parallel slots finish together
    tl = _tl()
    length = {c["id"]: c.get("end_film", c["end"]) - c["start"] for c in tl["chapters"]}
    chids = sorted(chids, key=lambda c: -length.get(c, 0))
    print(f"rendering {chids} with {jobs} parallel jobs x {threads} encoder threads", flush=True)

    def one(c):
        log = OUT / "logs" / f"render_{c}.log"
        env = dict(os.environ)
        with open(log, "w") as lf:
            rc = subprocess.run([sys.executable, "-m", "vf", "render-one", c, str(threads)], stdout=lf, stderr=subprocess.STDOUT,
                                env=env).returncode
        tail = log.read_text().strip().splitlines()[-1:] if log.exists() else []
        print(f"  {c}: {'OK' if rc == 0 else 'FAILED'} {tail[0] if tail else ''}", flush=True)
        return rc == 0

    with ThreadPoolExecutor(jobs) as ex:
        ok = all(ex.map(one, chids))
    return ok
