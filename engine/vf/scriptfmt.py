"""script.md parser + the hard length gate.

Format (full spec: docs/05-script-format.md):

    ## HOOK
    #### S001
    NAR: narration (display text; digits allowed)
    VIS: <source> | key=value | key=value
    ## BODY
    ### CH1 | 第1章 | 夢の宇宙船            (or legacy "### CH1 第1章　夢の宇宙船")
    #### S101 | pause=1.5
    NAR: ...
    VIS: ...
    VIS: ...                                  (several VIS lines = several shots in the scene)

Sources:  gfx:<name> (custom_gfx.py)   anim:<clip> [@m:ss.s]   cm:<Commons file title>   nasa:<NASA id>
          img:<path>   vid:<path> @m:ss.s   <ASSET_ID> @m:ss.s   (ASSET_ID registered in project.yaml assets)
"""
import datetime
import re
import sys
from pathlib import Path

from . import config
from .textproc import count, to_tts


def _opts(parts):
    o = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            o[k.strip()] = v.strip()
        elif p.strip():
            o[p.strip()] = "1"
    return o


def ts(s):
    if s is None:
        return None
    if ":" in s:
        parts = [float(x) for x in s.split(":")]
        v = 0.0
        for x in parts:
            v = v * 60 + x
        return v
    return float(s)


def parse_vis(v):
    parts = [p.strip() for p in v.split(" | ")]
    head, opts = parts[0], _opts(parts[1:])
    if head.startswith(("cm:", "img:", "nasa:", "gfx:")):
        src, at = head, None
        m = re.match(r"^(img:\S+)\s+@(\S+)$", head)
        if m:
            src, at = m.group(1), m.group(2)
    else:
        m = re.match(r"^(\S+)(?:\s+@(\S+))?$", head)
        if not m:
            raise ValueError(f"cannot parse VIS source: {head!r}")
        src, at = m.group(1), m.group(2)
    return {"src": src, "in": ts(at), "opts": opts, "raw": v}


def parse(path="script.md"):
    section, chapter = None, None
    scenes, chapters = [], {}
    cur = None
    for n, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.startswith("## "):
            section = line[3:].strip().split()[0].upper()
            if section == "HOOK":
                chapter = "HOOK"
                chapters["HOOK"] = {"id": "HOOK", "num": "", "title": "", "opts": {"card": "none"}}
        elif line.startswith("### "):
            body = line[4:].strip()
            if " | " in body:
                parts = [p.strip() for p in body.split(" | ")]
                cid = parts[0]
                plain = [p for p in parts[1:] if "=" not in p]
                num = plain[0] if len(plain) > 0 else ""
                title = plain[1] if len(plain) > 1 else ""
                opts = _opts([p for p in parts[1:] if "=" in p])
            else:
                cid, _, rest = body.partition(" ")
                num, sep, title = rest.partition("　")
                if not sep:
                    num, _, title = rest.partition(" — ")
                opts = {}
            chapter = cid
            chapters[cid] = {"id": cid, "num": num.strip(), "title": title.strip(), "opts": opts}
        elif line.startswith("#### "):
            parts = [p.strip() for p in line[5:].split(" | ")]
            cur = {"id": parts[0].split()[0], "section": section, "chapter": chapter, "nar": "",
                   "vis": [], "opts": _opts(parts[1:]), "line": n}
            scenes.append(cur)
        elif line.startswith("NAR:") and cur is not None:
            cur["nar"] += line[4:].strip()
        elif line.startswith("VIS:") and cur is not None:
            cur["vis"].append(line[4:].strip())
    return scenes, chapters


def counts(path="script.md"):
    cfg = config.load()
    scenes, chapters = parse(path)
    unit = cfg["length"]["unit"]
    hook = sum(count(to_tts(s["nar"]), unit) for s in scenes if s["section"] == "HOOK")
    body = sum(count(to_tts(s["nar"]), unit) for s in scenes if s["section"] == "BODY")
    per = {}
    for s in scenes:
        if s["section"] == "BODY":
            per[s["chapter"]] = per.get(s["chapter"], 0) + count(to_tts(s["nar"]), unit)
    from .textproc import sentences
    hook_sents = sum(len(sentences(s["nar"])) for s in scenes if s["section"] == "HOOK")
    return {"hook": hook, "hook_sentences": hook_sents, "body": body, "total": hook + body,
            "chapters": per, "scenes": len(scenes), "unit": unit,
            "no_vis": [s["id"] for s in scenes if not s["vis"]],
            "no_nar": [s["id"] for s in scenes if not s["nar"]],
            "chapter_titles": {k: (v["num"] + " " + v["title"]).strip() for k, v in chapters.items()}}


def gate(path="script.md", stamp=False):
    """Print the length report; return True if the hard gate passes."""
    cfg = config.load()
    L = cfg["length"]
    c = counts(path)
    ok = True
    sample = L.get("sample_hook")
    if not sample:
        print("length.sample_hook is not set in project.yaml (measure the sample script first: vf count-sample)")
        ok = False
        lo = hi = None
    else:
        tol = L.get("hook_tolerance", 0.15)
        lo, hi = sample * (1 - tol), sample * (1 + tol)
        hook_ok = lo <= c["hook"] <= hi
        ok &= hook_ok
        print(f"HOOK  {c['hook']} {c['unit']}, {c['hook_sentences']} sentences "
              f"(sample {sample}, allowed {lo:.0f}-{hi:.0f}) -> {'OK' if hook_ok else 'OUT OF RANGE'}")
    print(f"BODY  {c['body']} {c['unit']}")
    for k, v in c["chapters"].items():
        print(f"   {k:5s} {v:6d}  {c['chapter_titles'].get(k, '')}")
    tot_ok = c["total"] >= L["min"]
    ok &= tot_ok
    print(f"TOTAL {c['total']} {c['unit']} (min {L['min']}) -> {'OK' if tot_ok else 'TOO SHORT'}")
    if c["no_vis"] or c["no_nar"]:
        ok = False
        print("scenes without VIS:", c["no_vis"], " without NAR:", c["no_nar"])
    print("GATE:", "PASS" if ok else "FAIL")
    if stamp and ok:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        line = (f"\nLength check: hook {c['hook']} {c['unit']} (sample {sample}), body {c['body']}, "
                f"total {c['total']} — PASS ({now})\n")
        txt = Path(path).read_text()
        txt = re.sub(r"\nLength check: .*— PASS \([^)]*\)\n?", "\n", txt).rstrip("\n") + "\n" + line
        Path(path).write_text(txt)
    return ok


def sample_hook(path, end_marker=None):
    """Measure a sample script: total length, sentences, hook length up to end_marker (inclusive)."""
    cfg = config.load()
    unit = cfg["length"]["unit"]
    from .textproc import sentences
    txt = Path(path).read_text()
    flat = re.sub(r"\s+", "" if config.is_cjk() else " ", txt)
    sents = sentences(flat)
    total = count(txt, unit)
    print(f"sample: {total} {unit}, {len(sents)} sentences, avg {total / max(1, len(sents)):.1f} per sentence")
    if end_marker:
        idx = flat.find(end_marker)
        if idx < 0:
            print("end marker not found")
            return
        hook = flat[: idx + len(end_marker)]
        hs = sentences(hook)
        print(f"hook: {count(hook, unit)} {unit}, {len(hs)} sentences  -> set length.sample_hook in project.yaml")
    else:
        for i, s in enumerate(sents[:20], 1):
            print(f"{i:2d} {count(s, unit):4d} {s[:60]}")
        print("re-run with the hook's last words as end marker to measure the hook")


if __name__ == "__main__":
    sys.exit(0 if gate() else 1)
