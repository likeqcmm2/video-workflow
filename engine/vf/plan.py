"""Timeline: script.md + voice durations -> out/timeline.json + per-chapter ASS files.

Scene time = lead + voice + gap (+ chapter_end_extra for the last scene of a chapter, + scene option
pause=<s>). Times are snapped to frames.
Shots inside a scene:
  * as many VIS lines as sentences -> each cut lands in the silence between two sentences
    (so a picture appears exactly when the narration names it)
  * otherwise -> split by weights  w=<number>  (default 1)
Subtitles: one event per sentence (or per <=2-line chunk of a long sentence), timed to the silences
inside the scene's wav. Scene option subs=off hides them (e.g. when the picture already shows the words).
Grades: shot option grade=<name> > chapter option grade=<name> > "main".
"""
import json
import os
import re
import subprocess
from pathlib import Path

from . import config
from .assets import AssetError, resolve
from .scriptfmt import parse, parse_vis
from .subtitles import _ass_color, ass_header, ass_time, esc, events
from .textproc import sentences

OUT = Path("out")


def wav_dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]))


def silences(p, noise="-34dB", d=0.12):
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", str(p), "-af", f"silencedetect=noise={noise}:d={d}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    en = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(st, en))


def align(chunks, dur, sil):
    """(start, end) of each text chunk inside a wav; joins snap to the silence nearest the expected time."""
    total = sum(len(c) for c in chunks) or 1
    t0 = sil[0][1] if sil and sil[0][0] < 0.05 else 0.0
    t1 = sil[-1][0] if sil and sil[-1][1] > dur - 0.05 else dur
    if t1 - t0 < 0.3:            # silent / unusual wav: fall back to the whole file
        t0, t1, sil = 0.0, dur, []
    inner = [((a + b) / 2, b - a) for a, b in sil if a > t0 + 0.2 and b < t1 - 0.2]
    times, acc, used = [t0], 0, set()
    for c in chunks[:-1]:
        acc += len(c)
        exp = t0 + (t1 - t0) * acc / total
        best, bd = None, 9e9
        for i, (mid, ln) in enumerate(inner):
            if i in used or mid <= times[-1] + 0.3:
                continue
            dd = abs(mid - exp) - 0.6 * ln
            if dd < bd:
                best, bd = i, dd
        if best is not None and abs(inner[best][0] - exp) < max(1.2, 0.25 * (t1 - t0)):
            used.add(best)
            times.append(inner[best][0])
        else:
            times.append(exp)
    times.append(t1)
    return [(times[i], times[i + 1]) for i in range(len(chunks))]


def _subs_off(s):
    return s["opts"].get("subs") == "off"


def plan(strict=True):
    miss = config.design_missing()
    if miss and strict:
        raise SystemExit("design incomplete - decide these first (docs/02, docs/07):\n  " + "\n  ".join(miss))
    cfg = config.load()
    W, H, FPS = config.size()
    T = cfg["timing"]
    card_cfg = cfg["design"]["chapter_card"]
    scenes, chapters = parse()
    order = []
    for s in scenes:
        if not order or order[-1] != s["chapter"]:
            order.append(s["chapter"])
    t, timeline, chs, errors = 0.0, [], [], []
    for cid in order:
        ch = chapters.get(cid, {"id": cid, "num": "", "title": "", "opts": {}})
        start = t
        if cid != "HOOK" and card_cfg["enabled"] and ch["opts"].get("card") != "none":
            dur = float(ch["opts"].get("card_dur", card_cfg["duration"]))
            timeline.append({"type": "card", "ch": cid, "t0": t, "t1": t + dur, "num": ch["num"], "title": ch["title"],
                             "opts": dict(ch["opts"]), "grade": ch["opts"].get("grade") or "main"})
            t += dur
        ch_scenes = [s for s in scenes if s["chapter"] == cid]
        for si, s in enumerate(ch_scenes):
            wav = OUT / "vo" / f"{s['id']}.wav"
            if wav.exists():
                d = wav_dur(wav)
            elif not strict:
                d = max(1.5, len(s["nar"]) / (7.0 if config.is_cjk() else 15.0))
            else:
                raise SystemExit(f"voice missing for {s['id']} - run: vf tts")
            gap = T["gap"]
            if si == len(ch_scenes) - 1:
                gap += T["chapter_end_extra"]
            gap += float(s["opts"].get("pause", 0))
            lead = T["lead"]
            dur = lead + d + gap
            t0, t1 = round(t * FPS) / FPS, round((t + dur) * FPS) / FPS
            sents = sentences(s["nar"])
            sil = silences(wav) if wav.exists() else []
            st = align(sents, d, sil) if len(sents) > 1 else [(0.0, d)]
            shots = []
            for v in s["vis"]:
                try:
                    shots.append(parse_vis(v))
                except ValueError as e:
                    if strict:
                        raise SystemExit(f"{s['id']}: {e}")
                    errors.append(f"{s['id']}: {e}")
            if not shots:
                errors.append(f"{s['id']}: no usable VIS line")
                shots = [{"src": "", "in": None, "opts": {}, "raw": ""}]
            if len(shots) == len(sents) and len(shots) > 1:
                cuts = [t0] + [t0 + lead + (st[i][1] + st[i + 1][0]) / 2 for i in range(len(st) - 1)] + [t1]
                split = "sentence"
            else:
                ws = [float(sh["opts"].get("w", 1)) for sh in shots]
                cuts, tot = [t0], sum(ws)
                for w_ in ws[:-1]:
                    cuts.append(cuts[-1] + (t1 - t0) * w_ / tot)
                cuts.append(t1)
                split = "weight" if len(shots) > 1 else "single"
            cuts = [round(c * FPS) / FPS for c in cuts]
            for i, sh in enumerate(shots):
                try:
                    r = resolve(sh)
                except AssetError as e:
                    errors.append(f"{s['id']}: {e}")
                    r = {"kind": "missing", "path": None, "credit": None, "used_alt": False, "cls": "real"}
                in_pt = sh["in"]
                opts = sh["opts"]
                if r.get("used_alt"):
                    in_pt, opts = r["alt_shot"]["in"], {**r["alt_shot"]["opts"]}
                timeline.append({"type": "shot", "scene": s["id"], "ch": cid, "t0": cuts[i], "t1": cuts[i + 1],
                                 "kind": r["kind"], "cls": r.get("cls", "real"), "path": r["path"], "in": in_pt,
                                 "opts": opts, "credit": r.get("credit"), "src": sh["src"],
                                 "used_alt": r.get("used_alt", False), "split": split, "line": s["line"],
                                 "grade": opts.get("grade") or ch["opts"].get("grade") or "main"})
            subs = []
            if not _subs_off(s):
                for (a, b), sent in zip(st, sents):
                    chunks = events(sent)
                    tot = sum(len(c) for c in chunks)
                    x = a
                    for c in chunks:
                        y = x + (b - a) * len(c) / tot
                        subs.append((t0 + lead + x, t0 + lead + y, c))
                        x = y
            timeline.append({"type": "vo", "scene": s["id"], "ch": cid, "t0": t0 + lead, "wav": str(wav), "dur": d,
                             "subs": subs, "scene_t0": t0, "scene_t1": t1})
            t = t1
        chs.append({"id": cid, "num": ch["num"], "title": ch["title"], "start": start, "end": t})
    total = t + T["end_black"]
    timeline.append({"type": "end", "t0": t, "t1": total})
    chs[-1]["end_film"] = total
    OUT.mkdir(exist_ok=True)
    data = {"total": total, "fps": FPS, "size": [W, H], "chapters": chs, "timeline": timeline, "errors": errors}
    (OUT / "timeline.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))
    write_ass(data)
    print(f"total {total:.2f}s = {int(total // 60)}:{total % 60:05.2f}  ({len(scenes)} scenes, "
          f"{sum(1 for e in timeline if e['type'] == 'shot')} shots)")
    for c in chs:
        print(f"  {c['id']:5s} {c['start']:8.1f} {c['end']:8.1f}  {c['title']}")
    if errors:
        print(f"ASSET ERRORS ({len(errors)}):")
        for e in errors[:30]:
            print("  ", e)
    return data


def write_ass(data=None):
    data = data or json.loads((OUT / "timeline.json").read_text())
    H = data["size"][1]
    for ch in data["chapters"]:
        base = ch["start"]
        lines = [ass_header()]
        for e in data["timeline"]:
            if e.get("ch") != ch["id"]:
                continue
            if e["type"] == "vo":
                for a, b, txt in e["subs"]:
                    lines.append(f"Dialogue: 0,{ass_time(a - base)},{ass_time(b - base)},Sub,,0,0,0,,{esc(txt)}")
            if e["type"] == "shot":
                a, b = e["t0"] - base, e["t1"] - base
                if e["credit"]:
                    lines.append(f"Dialogue: 1,{ass_time(a)},{ass_time(b)},Credit,,0,0,0,,{{\\fad(300,200)}}{esc(e['credit'])}")
                if e["opts"].get("stamp"):
                    lines.append(f"Dialogue: 1,{ass_time(a + 0.2)},{ass_time(b)},Stamp,,0,0,0,,{{\\fad(500,300)}}{esc(e['opts']['stamp'])}")
                if e["opts"].get("lt"):
                    nm, _, role = e["opts"]["lt"].replace(" / ", "／").partition("／")   # "Name／Role"
                    st = config.load()["design"]["lower_third"]
                    wbox = int(max(st["name_size"] * len(nm), st["role_size"] * len(role)) *
                               (1.0 if config.is_cjk() else 0.55) + 120)
                    py = int(H * 0.733)
                    if st["plate"]:
                        px = 60 if st["position"] == "left" else data["size"][0] - 60 - wbox
                        pc = _ass_color(st["plate_colour"])[4:]
                        pa = _ass_color(st["plate_colour"], st["plate_opacity"])[2:4]
                        plate = (f"{{\\an7\\pos({px},{py})\\p1\\bord0\\shad0\\1c&H{pc}&\\1a&H{pa}&\\blur28\\fad(400,300)}}"
                                 f"m 0 0 l {wbox} 0 {wbox} 150 0 150{{\\p0}}")
                        lines.append(f"Dialogue: 0,{ass_time(a + 0.4)},{ass_time(b - 0.1)},LTRole,,0,0,0,,{plate}")
                    lines.append(f"Dialogue: 1,{ass_time(a + 0.4)},{ass_time(b - 0.1)},LTName,,0,0,0,,{{\\fad(400,300)}}{esc(nm)}")
                    if role:
                        lines.append(f"Dialogue: 1,{ass_time(a + 0.6)},{ass_time(b - 0.1)},LTRole,,0,0,0,,{{\\fad(400,300)}}{esc(role)}")
        (OUT / f"ass_{ch['id']}.ass").write_text("\n".join(lines) + "\n")
