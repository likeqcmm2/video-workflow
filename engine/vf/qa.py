"""Automated QA.  Machines check what machines can check, so human/agent review time goes to taste.

  vf preflight     before rendering: script gate, voice, every asset, every graphic, subtitles, ratio.
                   Each check exists because the reference production lost hours to that exact defect.
  vf qa            after `vf final`: container/codec/fps/size/duration, loudness, unexpected black in
                   footage, frame count.
Full results: out/qa/*.json. Console output stays short (counts + first items).
"""
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from . import config
from .subtitles import NO_LINE_START

OUT = Path("out")
QA = OUT / "qa"


class Report:
    def __init__(self, name):
        self.name, self.items = name, []

    def add(self, level, where, msg):
        it = {"level": level, "where": where, "msg": msg}
        if it not in self.items:
            self.items.append(it)

    def err(self, where, msg):
        self.add("ERROR", where, msg)

    def warn(self, where, msg):
        self.add("WARN", where, msg)

    def info(self, where, msg):
        self.add("INFO", where, msg)

    def finish(self, max_lines=40):
        QA.mkdir(parents=True, exist_ok=True)
        (QA / f"{self.name}.json").write_text(json.dumps(self.items, ensure_ascii=False, indent=1))
        c = Counter(i["level"] for i in self.items)
        print(f"{self.name}: {c.get('ERROR', 0)} errors, {c.get('WARN', 0)} warnings, {c.get('INFO', 0)} info "
              f"(full list: {QA / (self.name + '.json')})")
        shown = 0
        for lvl in ("ERROR", "WARN"):
            for i in self.items:
                if i["level"] == lvl and shown < max_lines:
                    print(f"  {lvl:5s} {i['where']:12s} {i['msg']}")
                    shown += 1
        return c.get("ERROR", 0) == 0


def font_families():
    """{family or full name (lower) -> font file} for every font in vendor/fonts (what libass can see)."""
    out = {}
    for f in sorted(config.FONTS_DIR.glob("*.[ot]tf")):
        res = subprocess.run(["fc-scan", "--format", "%{family}|%{fullname}\n", str(f)], capture_output=True, text=True).stdout
        for line in res.splitlines():
            for name in line.replace("|", ",").split(","):
                if name.strip():
                    out.setdefault(name.strip().lower(), str(f))
    return out


_cmaps = {}


def missing_glyphs(font_file, text):
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return set()
    if font_file not in _cmaps:
        _cmaps[font_file] = set(TTFont(font_file, fontNumber=0, lazy=True).getBestCmap() or {})
    return {ch for ch in text if not ch.isspace() and ord(ch) not in _cmaps[font_file] and ch not in "\u3000"}


def _design(r):
    for m in config.design_missing():
        r.err("design", f"decide and set {m} - the engine assumes no style (docs/02, docs/07)")


def _fonts_ok(r, tl=None):
    cfg = config.load()
    d = cfg["design"]
    for k, f in d["fonts"].items():
        if not (config.FONTS_DIR / f).exists() and not os.path.exists(f):
            r.err("fonts", f"font file {f} (role {k}) missing - scripts/fetch_fonts.py \"Family:weights\"")
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    if " ass " not in out:
        r.err("env", "ffmpeg lacks the libass 'ass' filter")
    fam = font_families()
    ass_fonts = {"subtitle": d["subtitle"]["font"], "credit": d["credit"]["font"], "stamp": d["stamp"]["font"],
                 "lower_third name": d["lower_third"]["name_font"], "lower_third role": d["lower_third"]["role_font"]}
    files = {}
    for role, name in ass_fonts.items():
        if not name:
            continue
        f = fam.get(name.lower())
        if not f:
            r.err("fonts", f"{role} font {name!r} is not installed in vendor/fonts - libass would silently use another "
                           f"font (installed: {sorted(set(fam))[:8]}...)")
        files[role] = f
    if tl:   # every character on screen must exist in its font (otherwise: tofu boxes)
        texts = {"subtitle": "", "credit": "", "stamp": "", "lower_third name": "", "lower_third role": ""}
        for e in tl["timeline"]:
            if e["type"] == "vo":
                texts["subtitle"] += "".join(x[2].replace("\\N", "") for x in e["subs"])
            elif e["type"] == "shot":
                texts["credit"] += e.get("credit") or ""
                texts["stamp"] += e["opts"].get("stamp", "")
                nm, _, role = e["opts"].get("lt", "").replace(" / ", "／").partition("／")
                texts["lower_third name"] += nm
                texts["lower_third role"] += role
        for role, txt in texts.items():
            if files.get(role) and txt:
                miss = missing_glyphs(files[role], txt)
                if miss:
                    r.err("fonts", f"{role} font lacks glyphs {''.join(sorted(miss))[:30]!r} (would render as boxes)")


def _voice(r, scenes):
    from .textproc import to_tts
    cfg = config.load()
    ovr = {}
    if Path("tts_overrides.yaml").exists():
        import yaml
        ovr = yaml.safe_load(Path("tts_overrides.yaml").read_text()) or {}
    for s in scenes:
        js = OUT / "vo" / f"{s['id']}.json"
        if not js.exists():
            r.err(s["id"], "no voice (vf tts)")
            continue
        rec = json.loads(js.read_text())
        if rec.get("text") != (ovr.get(s["id"]) or to_tts(s["nar"])):
            r.err(s["id"], "narration changed after TTS - re-run: vf tts " + s["id"])
        elif rec.get("fake"):
            (r.warn if os.environ.get("VF_ALLOW_FAKE") else r.err)(s["id"], "placeholder voice (fake) - generate real TTS")
        elif rec["sim"] < 0.80:
            r.err(s["id"], f"ASR similarity {rec['sim']} - voice probably wrong; fix reading and regenerate")
        elif rec["sim"] < cfg["voice"]["min_similarity"] and not rec.get("accepted"):
            r.warn(s["id"], f"ASR similarity {rec['sim']}: compare text/asr in {js}; regenerate or `vf tts-accept {s['id']}`")


def _shots(r, tl):
    from .media import available, black_in_segment, probe, scan_data
    from PIL import Image
    cfg = config.load()
    W, H, _ = config.size()
    shots = [e for e in tl["timeline"] if e["type"] == "shot"]
    uses = Counter(e["path"] for e in shots if e["kind"] == "image")
    for e in shots:
        w = e["scene"]
        dur = e["t1"] - e["t0"]
        if e.get("used_alt"):
            r.warn(w, f"primary visual missing, using alt -> {e['src']} replaced; fix or accept consciously")
        if e["kind"] in ("image", "video") and e.get("cls", "real") == "real" and not e.get("credit"):
            r.err(w, f"no on-screen credit for {e['src']} (add credit=... or register the asset with a credit)")
        if e["kind"] == "image":
            try:
                with Image.open(e["path"]) as im:
                    iw, ih = im.size
            except Exception as ex:
                r.err(w, f"unreadable image {e['path']}: {ex}")
                continue
            fit = e["opts"].get("fit") or ("cover" if 1.2 <= iw / ih <= 2.2 else "contain")
            if fit == "cover" and iw < W * 0.66:
                r.warn(w, f"{os.path.basename(e['path'])} is {iw}px wide shown full-frame - soft; use fit=contain or a bigger file")
            if dur > cfg["timing"]["max_still"] and e["opts"].get("kb") == "none":
                r.warn(w, f"static still for {dur:.1f}s")
        if e["kind"] == "video":
            info = probe(e["path"])
            t_in = e["in"] or 0.0
            if t_in >= info["dur"]:
                r.err(w, f"in-point {t_in:.1f}s beyond end of {e['path']} ({info['dur']:.1f}s)")
                continue
            av = available(e["path"], t_in, e["opts"].get("cross_cuts") == "1")
            if scan_data(e["path"]) is None and e.get("cls", "real") == "real":
                r.warn(w, f"{os.path.basename(e['path'])} not scanned for cuts/black (vf media scan)")
            speed = 1.0 if dur <= av else max(float(e["opts"].get("min_speed", 0.5)), av / max(dur, 1e-3))
            if av <= 0.3:
                r.err(w, f"in-point {t_in:.1f}s sits on a cut/black range in {os.path.basename(e['path'])}")
                continue
            if speed < 0.6:
                r.err(w, f"footage too short ({av:.1f}s for {dur:.1f}s) -> would play at {speed:.2f}x; pick a longer take, "
                         f"move the in-point or split the scene into more shots (if the 'cut' is only a flash, verify on a "
                         f"contact sheet and add cross_cuts=1)")
            elif speed < 0.85:
                r.warn(w, f"footage slowed to {speed:.2f}x ({av:.1f}s for {dur:.1f}s) - fine for smoke/water/crowds, not for people talking")
            need = dur * speed
            bl = [(a, b) for a, b in black_in_segment(e["path"], t_in, need) if b - a >= 0.2]
            if bl:
                r.err(w, f"black frames inside used footage {os.path.basename(e['path'])} @ "
                          f"{', '.join(f'{t_in + a:.1f}-{t_in + b:.1f}s' for a, b in bl)} -> move the in-point")
        if e["src"].startswith("cm:"):
            from .assets import commons_meta
            m = commons_meta(e["src"][3:])
            if not m:
                r.err(w, f"no licence metadata for {e['src']} (vf commons fetch records it)")
            elif m.get("flag"):
                r.warn(w, f"licence needs checking: {m.get('license')!r} for {e['src'][3:]}")
    for p, n in uses.items():
        if n > 3:
            r.warn("repeat", f"{os.path.basename(p)} used in {n} shots")
    # same still in two consecutive scenes reads as a mistake
    prev = None
    for e in shots:
        if e["kind"] == "image" and prev and prev["kind"] == "image" and prev["path"] == e["path"] and prev["scene"] != e["scene"]:
            r.info(e["scene"], f"same still continues from {prev['scene']}")
        prev = e


def _gfx(r, tl):
    from . import gfx
    cfg = config.load()
    W, H, _ = config.size()
    m = cfg["design"]["safe_margin"]
    ztop = config.subtitle_zone_top()
    seen = set()
    items = [e for e in tl["timeline"] if (e["type"] == "shot" and e["kind"] == "gfx") or e["type"] == "card"]
    for e in items:
        name = (cfg["design"]["chapter_card"].get("gfx") or "chapter") if e["type"] == "card" else e["path"]
        opts = {"num": e["num"], "title": e["title"]} if e["type"] == "card" else e["opts"]
        key = (name, json.dumps(opts, sort_keys=True, ensure_ascii=False))
        if key in seen:
            continue
        seen.add(key)
        where = e.get("scene", e["ch"])
        dur = e["t1"] - e["t0"]
        for t in sorted({min(dur - 0.05, max(2.5, dur * 0.6)), dur - 0.05}):
            try:
                _, boxes = gfx.render(name, opts, t, dur, track=True)
            except Exception as ex:
                r.err(where, f"gfx:{name} failed: {type(ex).__name__}: {ex}")
                break
            low_ok = opts.get("allow_low") == "1"
            for (x0, y0, x1, y1, s, fp) in boxes:
                lab = s.replace("\n", " ")[:24]
                if fp:
                    miss = missing_glyphs(fp, s)
                    if miss:
                        r.err(where, f"gfx:{name} font {os.path.basename(fp)} lacks glyphs {''.join(sorted(miss))[:20]!r}")
                if x0 < W * m - 2 or x1 > W * (1 - m) + 2 or y0 < H * m - 2:
                    r.err(where, f"gfx:{name} text outside safe area: {lab!r} box=({x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f})")
                elif y1 > ztop and not low_ok:
                    r.err(where, f"gfx:{name} text in subtitle zone (y>{ztop:.0f}): {lab!r}")
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    a, b = boxes[i], boxes[j]
                    ix = min(a[2], b[2]) - max(a[0], b[0])
                    iy = min(a[3], b[3]) - max(a[1], b[1])
                    if ix > 4 and iy > 4:
                        r.err(where, f"gfx:{name} overlapping text {a[4][:14]!r} / {b[4][:14]!r}")


def _subs(r, tl):
    st = config.load()["design"]["subtitle"]
    lim = st["max_chars"] + st["slack"]
    for e in tl["timeline"]:
        if e["type"] != "vo":
            continue
        for a, b, txt in e["subs"]:
            lines = txt.split("\\N")
            if len(lines) > 2:
                r.err(e["scene"], f"subtitle with {len(lines)} lines: {txt[:30]}")
            for ln in lines:
                if len(ln) > lim:
                    r.warn(e["scene"], f"subtitle line {len(ln)} chars > {lim}: {ln[:30]}")
            for ln in lines[1:]:
                if ln[:1] in NO_LINE_START:
                    r.err(e["scene"], f"subtitle line starts with {ln[:1]!r}: {ln[:20]}")
            if b - a < 0.6:
                r.warn(e["scene"], f"subtitle on screen only {b - a:.2f}s: {txt[:20]}")


def ratio(tl, chapter=None):
    """Share of SHOT time (cards and end black excluded): real footage/photos vs graphics (code graphics +
    animation clips), plus the split by kind."""
    acc, kinds = Counter(), Counter()
    for e in tl["timeline"]:
        if e["type"] == "shot" and (chapter is None or e["ch"] == chapter):
            d = e["t1"] - e["t0"]
            acc[e.get("cls", "real")] += d
            kinds["anim" if e.get("cls") == "graphic" and e["kind"] == "video" else e["kind"]] += d
    tot = sum(acc.values()) or 1
    out = {"real": round(100 * acc["real"] / tot, 1), "graphic": round(100 * acc["graphic"] / tot, 1)}
    out.update({f"kind_{k}": round(100 * v / tot, 1) for k, v in kinds.items()})
    return out, tot


def _ratio_checks(r, tl):
    D = config.load()["director"]
    lo, hi = D["real_pct"].get("min"), D["real_pct"].get("max")
    rt, _ = ratio(tl)
    if lo is None or hi is None:
        return
    msg = f"real {rt['real']:.0f}% / graphics {rt['graphic']:.0f}% (director range {lo}-{hi}%)"
    if not lo <= rt["real"] <= hi:
        r.err("ratio", msg + " - find more real material or rethink graphics (docs/02, docs/04)")
    else:
        r.info("ratio", msg)
    # chapters are free (a chapter may be all archive or all animation) - their shares are shown, never judged
    per = []
    for c in tl["chapters"]:
        cr, tot = ratio(tl, c["id"])
        if tot >= 1:
            per.append(f"{c['id']} {cr['real']:.0f}%")
    if per:
        r.info("ratio", "real share per chapter (for the director, not a rule): " + ", ".join(per))


def preflight(skip_video_black=False):
    from .plan import plan
    from .scriptfmt import counts, parse
    r = Report("preflight")
    _design(r)
    cfg = config.load()
    c = counts()
    L = cfg["length"]
    if not L.get("sample_hook"):
        r.err("script", "length.sample_hook not set")
    else:
        lo, hi = L["sample_hook"] * (1 - L["hook_tolerance"]), L["sample_hook"] * (1 + L["hook_tolerance"])
        if not lo <= c["hook"] <= hi:
            r.err("script", f"hook {c['hook']} outside {lo:.0f}-{hi:.0f}")
    if c["total"] < L["min"]:
        r.err("script", f"total {c['total']} < {L['min']}")
    if "PASS" not in Path("script.md").read_text().split("Length check:")[-1][:200]:
        r.warn("script", "no 'Length check: ... PASS' line - run: vf count --stamp")
    scenes, _ = parse()
    _voice(r, scenes)
    try:
        tl = plan(strict=False)
    except (KeyError, SystemExit) as e:
        if not config.design_missing():
            raise
        r.info("design", f"timeline, graphics, subtitle and ratio checks need the design first ({e})")
        return r.finish()
    for e in tl["errors"]:
        r.err("asset", e)
    _fonts_ok(r, tl)
    _shots(r, tl)
    _gfx(r, tl)
    _subs(r, tl)
    _ratio_checks(r, tl)
    weight_split = sorted({e["scene"] for e in tl["timeline"] if e["type"] == "shot" and e.get("split") == "weight"})
    if weight_split:
        r.info("timing", f"{len(weight_split)} scenes split by weight (check sync by eye): {weight_split[:15]}")
    pend = Path("assets/commons/logs/pending.json")
    if pend.exists() and json.loads(pend.read_text()):
        r.warn("commons", f"pending Wikimedia downloads: {list(json.loads(pend.read_text()))[:5]}")
    return r.finish()


def _probe_all(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                   "stream=codec_type,codec_name,width,height,r_frame_rate,pix_fmt,sample_rate,channels,duration:format=duration",
                                   "-of", "json", path])
    return json.loads(out)


def postqa(path="out/video.mp4"):
    cfg = config.load()
    W, H, FPS = config.size()
    r = Report("qa")
    tl = json.loads((OUT / "timeline.json").read_text())
    j = _probe_all(path)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    if (v["width"], v["height"]) != (W, H):
        r.err("video", f"size {v['width']}x{v['height']} != {W}x{H}")
    if v["codec_name"] != "h264" or v["pix_fmt"] != "yuv420p":
        r.err("video", f"codec {v['codec_name']} {v['pix_fmt']}")
    num, den = v["r_frame_rate"].split("/")
    if abs(float(num) / float(den) - FPS) > 0.01:
        r.err("video", f"fps {v['r_frame_rate']}")
    if not a or a["codec_name"] != "aac":
        r.err("audio", "no AAC audio")
    vd, ad = float(v.get("duration", 0)), float(a.get("duration", 0)) if a else 0
    if abs(vd - tl["total"]) > 2 / FPS or abs(ad - vd) > 0.1:
        r.err("duration", f"video {vd:.2f}s audio {ad:.2f}s timeline {tl['total']:.2f}s")
    nb = subprocess.check_output(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                                  "stream=nb_read_packets", "-of", "csv=p=0", path]).decode().strip()
    if abs(int(nb) - round(tl["total"] * FPS)) > 1:
        r.err("frames", f"{nb} frames, expected {round(tl['total'] * FPS)}")
    err = subprocess.run(["ffmpeg", "-nostats", "-i", path, "-map", "0:a", "-af", "loudnorm=print_format=summary",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    li = re.search(r"Input Integrated:\s*(-?[\d.]+)", err)
    tp = re.search(r"Input True Peak:\s*(-?[\d.]+)", err)
    L = cfg["loudness"]
    if li and abs(float(li.group(1)) - L["integrated"]) > 1.0:
        r.warn("loudness", f"integrated {li.group(1)} LUFS (target {L['integrated']})")
    if tp and float(tp.group(1)) > -0.5:
        r.warn("loudness", f"true peak {tp.group(1)} dBTP")
    r.info("loudness", f"integrated {li.group(1) if li else '?'} LUFS, true peak {tp.group(1) if tp else '?'} dBTP")
    # unexpected black inside footage/photo shots
    err = subprocess.run(["ffmpeg", "-v", "info", "-i", path, "-an", "-vf", "scale=480:-2,blackdetect=d=0.25:pic_th=0.92:pix_th=0.05",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    blacks = [(float(x), float(y)) for x, y in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    shots = [e for e in tl["timeline"] if e["type"] == "shot" and e["kind"] in ("image", "video") and e.get("cls", "real") == "real"]
    from .render import _trans
    fade_in = _trans(cfg["design"]["transitions"].get("film_in"))[1]
    end_t0 = tl["chapters"][-1]["end"] - _trans(cfg["design"]["transitions"].get("film_out"))[1]
    for b0, b1 in blacks:
        if b1 <= fade_in + 0.1 or b0 >= end_t0 - 0.1:
            continue
        def window(e):
            a0 = e["t0"] + max(0.5, _trans(e["opts"].get("in"))[1])
            a1 = e["t1"] - _trans(e["opts"].get("out"))[1]
            return a0, a1
        hit = [e for e in shots if window(e)[0] < b1 and b0 < window(e)[1]]
        if hit:
            r.err("black", f"{b0:.1f}-{b1:.1f}s black during {hit[0]['scene']} ({hit[0]['src']})")
    _ratio_checks(r, tl)
    return r.finish()
