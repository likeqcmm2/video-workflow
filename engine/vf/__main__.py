"""vf - video workflow engine CLI.  Run inside a project directory (or: vf --project <dir> <cmd>).

Setup / project
  doctor                         check tools, fonts, map data, env secrets (values never printed)
  init <dir> [--title T] [--lang ja]   create a project skeleton from templates/
Script
  count [--stamp]                length gate (hook vs sample, total >= min); --stamp writes the PASS line
  count-sample <file> [end]      measure the sample script (+ its hook up to the text `end`)
Voice
  tts [S001 ...] [--redo]        Gemini TTS per scene + ASR check (resumable)
  tts-report | tts-accept <id>   summary of similarities | accept a reviewed low-similarity take
Footage
  media scan <video>             cuts + black ranges -> assets/scenes/<stem>.json  (do this for every video)
  media contact <video> [every] [start] [end]   contact sheet(s) -> assets/contact/
  media images <tag> <files...>  contact sheet of stills
  media gif2mp4 <gif> [slow] [loops]
  commons test | search <q> | cat <category> | fetch <titles.txt|title> [width] | video <title> [maxh] | stats
  nasa search <q> [year_from year_to] | nasa fetch <id ...>
  ia search <q> | ia files <identifier> | ia fetch <identifier> <file>
  music fetch "<Incompetech title>" ...
Build
  plan                           timeline + ASS (prints asset errors)
  preflight                      ALL automated checks before rendering (must end with 0 errors)
  gfx-list                       the graphics defined in custom_gfx.py with their docstrings
  gfx-preview <name> [k=v ...] [t=2.5] [dur=6]   one graphic -> out/gfx_preview/<name>.png + bounds check
  render [--changed | all | CH1 CH2 ...] [-j N]
  audio | final | qa             mix | concat-copy + mux | post-render checks
  sheets <CH...|all> [--every s] [--tag t]      review sheets -> out/review/
  stats | sources                report numbers | sources_assets.md + sources.md
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import config


def _flag(args, name, default=None, cast=str):
    if name in args:
        i = args.index(name)
        v = cast(args[i + 1])
        del args[i:i + 2]
        return v
    return default


def doctor():
    ok = True
    for tool in ("ffmpeg", "ffprobe"):
        p = shutil.which(tool)
        print(f"{tool:12s} {'ok' if p else 'MISSING'}")
        ok &= bool(p)
    filt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    print(f"{'libass':12s} {'ok' if ' ass ' in filt else 'MISSING (subtitles cannot be burned)'}")
    for mod in ("cv2", "numpy", "PIL", "shapefile", "yaml", "google.genai", "budoux", "num2words", "requests"):
        try:
            __import__(mod)
            st = "ok"
        except Exception:
            st, ok = "MISSING (bash scripts/setup.sh)", False
        print(f"{mod:12s} {st}")
    fonts = sorted(p.name for p in config.FONTS_DIR.glob("*.ttf")) if config.FONTS_DIR.exists() else []
    print(f"{'fonts':12s} {len(fonts)} in vendor/fonts {fonts[:6]}")
    geo = list(config.GEO_DIR.glob("*.shp")) if config.GEO_DIR.exists() else []
    print(f"{'map data':12s} {len(geo)} Natural Earth layers")
    for k in ("GEMINI_API_KEY", "WIKIMEDIA_USER_AGENT", "WIKIMEDIA_BOT_USER", "WIKIMEDIA_BOT_PASSWORD"):
        print(f"{k:24s} {'set' if os.environ.get(k) else 'not set'}")
    print("cpu cores:", os.cpu_count())
    return ok


def init(args):
    title = _flag(args, "--title", "")
    lang = _flag(args, "--lang", "ja")
    d = Path(args[0])
    tpl = config.REPO / "templates"
    d.mkdir(parents=True, exist_ok=True)
    for sub in ("assets", "research", "out"):
        (d / sub).mkdir(exist_ok=True)
    rep = {"{{TITLE}}": title, "{{LANG}}": lang}
    for src, dst in (("project.template.yaml", "project.yaml"), ("script.template.md", "script.md"),
                     ("PROGRESS.template.md", "PROGRESS.md"), ("sources_facts.template.md", "sources_facts.md"),
                     ("custom_gfx.template.py", "custom_gfx.py")):
        p = d / dst
        if not p.exists():
            txt = (tpl / src).read_text()
            for k, v in rep.items():
                txt = txt.replace(k, v)
            p.write_text(txt)
    print(f"project created: {d}  -> edit project.yaml, then follow WORKFLOW.md")


def main(argv):
    argv = config.find_project(argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, args = argv[0], argv[1:]
    if cmd == "doctor":
        return 0 if doctor() else 1
    if cmd == "init":
        init(args)
        return 0
    config.load()
    if cmd == "count":
        from .scriptfmt import gate
        return 0 if gate(stamp="--stamp" in args) else 1
    if cmd == "count-sample":
        from .scriptfmt import sample_hook
        sample_hook(args[0], args[1] if len(args) > 1 else None)
    elif cmd == "tts":
        from .tts import run
        redo, fake = "--redo" in args, "--fake" in args
        ids = [a for a in args if not a.startswith("--")]
        run(ids or None, redo=redo, fake=fake)
    elif cmd == "tts-report":
        from .tts import report
        report()
    elif cmd == "tts-accept":
        for sid in args:
            p = Path("out/vo") / f"{sid}.json"
            rec = json.loads(p.read_text())
            rec["accepted"] = True
            p.write_text(json.dumps(rec, ensure_ascii=False, indent=1))
            print("accepted", sid, rec["sim"])
    elif cmd == "plan":
        from .plan import plan
        d = plan(strict="--draft" not in args)
        return 1 if d["errors"] else 0
    elif cmd == "preflight":
        from .qa import preflight
        return 0 if preflight() else 1
    elif cmd == "gfx-list":
        from . import gfx
        reg = gfx.registry()
        if not reg:
            print("custom_gfx.py defines no graphics yet (functions named g_<name>)")
        for name, fn in sorted(reg.items()):
            doc = " ".join((fn.__doc__ or "").split())
            print(f"{name:14s} {doc}")
    elif cmd == "gfx-preview":
        from . import gfx
        kv = dict(a.split("=", 1) for a in args[1:] if "=" in a)
        t, dur = float(kv.pop("t", 2.5)), float(kv.pop("dur", 6))
        im, boxes = gfx.render(args[0], kv, t, dur, track=True)
        out = Path("out/gfx_preview")
        out.mkdir(parents=True, exist_ok=True)
        p = out / f"{args[0]}.png"
        im.save(p)
        W, H, _ = config.size()
        m = config.load()["design"]["safe_margin"]
        bad = [b for b in boxes if b[0] < W * m or b[2] > W * (1 - m) or b[1] < H * m or b[3] > config.subtitle_zone_top()]
        print(p, f"{len(boxes)} text boxes, {len(bad)} outside safe area/subtitle zone", [b[4][:20] for b in bad])
    elif cmd == "render":
        from .render import changed, render_many
        jobs = _flag(args, "-j", 0, int)
        if "--changed" in args or not args:
            ch = changed()
        elif args == ["all"]:
            ch = [c["id"] for c in json.loads(Path("out/timeline.json").read_text())["chapters"]]
        else:
            ch = args
        return 0 if render_many(ch, jobs) else 1
    elif cmd == "render-one":
        from .render import render_chapter
        render_chapter(args[0], int(args[1]) if len(args) > 1 else 2)
    elif cmd == "audio":
        from .audio import mix
        mix()
    elif cmd == "final":
        from .audio import final
        final()
    elif cmd == "qa":
        from .qa import postqa
        return 0 if postqa(args[0] if args else "out/video.mp4") else 1
    elif cmd == "sheets":
        from .review import sheets
        every = _flag(args, "--every", None, float)
        tag = _flag(args, "--tag", None)
        sheets(args or ["all"], every, tag)
    elif cmd == "stats":
        from .report import stats
        stats()
    elif cmd == "sources":
        from .report import sources
        sources()
    elif cmd == "media":
        from . import media
        sub = args[0]
        if sub == "scan":
            for v in args[1:]:
                media.scan(v)
        elif sub == "contact":
            a = args[1:]
            media.contact_video(a[0], float(a[1]) if len(a) > 1 else 8.0, float(a[2]) if len(a) > 2 else 0.0,
                                float(a[3]) if len(a) > 3 else None)
        elif sub == "images":
            media.contact_images(args[2:], args[1])
        elif sub == "gif2mp4":
            media.gif2mp4(args[1], float(args[2]) if len(args) > 2 else 1.0, int(args[3]) if len(args) > 3 else 1)
    elif cmd == "commons":
        from .wm_client import WMClient
        sub = args[0]
        c = WMClient(login=True)
        if sub == "test":
            print("logged in:", c.logged_in, "| UA ok")
            rows = c.scout("Apollo 11 launch", limit=5)
            print(f"search ok ({len(rows)} rows); cache test:")
            c.scout("Apollo 11 launch", limit=5)
            print("stats:", {k: v for k, v in c.report().items() if k in ("requests_sent", "cache_hits", "http_429")})
            if rows:
                print("thumb 330:", c.download(rows[0]["title"], 330))
        elif sub in ("search", "cat"):
            rows = c.scout(" ".join(args[1:]), category=(sub == "cat"))
            for r in rows[:40]:
                print(f"{r['w']}x{r['h']}  {r['title'][5:][:90]}")
            print(f"({len(rows)} rows -> assets/commons/scout/)")
        elif sub == "fetch":
            src = args[1]
            width = int(args[2]) if len(args) > 2 else 1920
            titles = [x.strip() for x in Path(src).read_text().splitlines() if x.strip()] if Path(src).exists() else [src]
            for t in titles:
                try:
                    print(c.download(t, width))
                except Exception as e:
                    print("FAILED", t, str(e)[:120])
            for t, m in c.license(titles).items():
                print(f"  {m.get('license', '?'):18s} {'FLAG ' if m.get('flag') else ''}{t[5:][:70]}")
        elif sub == "video":
            dest, d = c.video(args[1], int(args[2]) if len(args) > 2 else 720)
            print(dest, d.get("height"), "p")
        elif sub == "stats":
            from .report import wm_stats
            print(json.dumps(wm_stats(), indent=1))
    elif cmd == "nasa":
        from . import sources
        if args[0] == "search":
            sources.nasa_search(args[1], year_start=args[2] if len(args) > 2 else None,
                                year_end=args[3] if len(args) > 3 else None)
        else:
            sources.nasa_fetch(args[1:])
    elif cmd == "ia":
        from . import sources
        if args[0] == "search":
            sources.ia_search(" ".join(args[1:]))
        elif args[0] == "files":
            sources.ia_files(args[1])
        else:
            sources.ia_fetch(args[1], args[2])
    elif cmd == "music":
        from . import sources
        sources.music_fetch(args[1:])
    else:
        print("unknown command", cmd)
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
