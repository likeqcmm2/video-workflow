"""Review sheets for visual review performed by the main agent (see docs/10-qa-review.md).

  vf sheets CH3 [CH4 ...] [--every 3]     sheets for chapters (from out/ch_<id>.mp4, subtitles burned in)
  vf sheets all --every 6                  skim of the whole film
Each tile is labelled "m:ss  S123" (film time + scene id) so a reviewer can report issues by scene.
Sheets: 4 x 5 tiles of 400x225 -> 1600 px wide JPEG, 20 frames per sheet. A manifest JSON lists every
tile with time, scene, source and template so reviewers never need the timeline.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from . import config
from .media import _font

OUT = Path("out")
COLS, ROWS, TW, TH = 4, 5, 400, 225


def _at(tl, t):
    for e in tl["timeline"]:
        if e["type"] in ("shot", "card") and e["t0"] <= t < e["t1"]:
            return e
    return None


def sheets(chapters, every=None, tag=None):
    cfg = config.load()
    every = every or cfg["review"]["every"]
    tl = json.loads((OUT / "timeline.json").read_text())
    rdir = OUT / "review"
    rdir.mkdir(parents=True, exist_ok=True)
    if chapters == ["all"]:
        chapters = [c["id"] for c in tl["chapters"]]
    font = _font(16)
    produced = []
    for chid in chapters:
        ch = next(c for c in tl["chapters"] if c["id"] == chid)
        src = OUT / f"ch_{chid}.mp4"
        if not src.exists():
            print("missing", src)
            continue
        name = f"{tag or 'rv'}_{chid}"
        for old in rdir.glob(f"{name}_*.jpg"):
            old.unlink()
        with tempfile.TemporaryDirectory() as tmp:
            fps = tl["fps"]
            step, off = max(1, round(every * fps)), round(every * fps / 2)
            # frame-exact sampling (the fps filter drifts by one interval): frame n = off + k*step
            subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vf",
                            f"select='gte(n\\,{off})*not(mod(n-{off}\\,{step}))',scale={TW}:{TH}",
                            "-fps_mode", "passthrough", f"{tmp}/f_%05d.jpg"], check=True)
            frames = sorted(Path(tmp).glob("f_*.jpg"))
            manifest = []
            per = COLS * ROWS
            for p0 in range(0, len(frames), per):
                chunk = frames[p0:p0 + per]
                sheet = Image.new("RGB", (COLS * TW, ((len(chunk) - 1) // COLS + 1) * (TH + 22)), "white")
                d = ImageDraw.Draw(sheet)
                for i, f in enumerate(chunk):
                    k = p0 + i
                    t = ch["start"] + (off + k * step) / fps
                    e = _at(tl, t)
                    sid = e.get("scene", e.get("ch")) if e else "-"
                    x, y = (i % COLS) * TW, (i // COLS) * (TH + 22)
                    sheet.paste(Image.open(f), (x, y))
                    d.text((x + 3, y + TH + 2), f"{int(t // 60)}:{t % 60:04.1f}  {sid}", fill="black", font=font)
                    manifest.append({"sheet": f"{name}_{p0 // per:02d}.jpg", "tile": i + 1, "t": round(t, 1),
                                     "scene": sid, "src": e.get("src") if e else None,
                                     "kind": (e.get("kind") or e["type"]) if e else None})
                out = rdir / f"{name}_{p0 // per:02d}.jpg"
                sheet.save(out, quality=80)
                produced.append(str(out))
            (rdir / f"{name}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
    print(f"{len(produced)} sheets ({every:g}s spacing):")
    for p in produced:
        print(" ", p)
    return produced
