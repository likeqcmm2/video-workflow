"""Footage tools: cut/black scan, availability, contact sheets, GIF -> MP4.

`vf media scan <video>` writes assets/scenes/<stem>.json = {"cuts": [...], "black": [[a, b], ...]}.
The renderer never plays a shot past the next cut OR into a black/fade-out range: it slows the shot
(>= 0.5x) instead; preflight flags speeds below 0.6x.
"""
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from . import config

SCENES = Path("assets/scenes")


def probe(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                   "stream=width,height,r_frame_rate:format=duration", "-of", "json", path])
    j = json.loads(out)
    st = j["streams"][0]
    num, den = st["r_frame_rate"].split("/")
    return {"w": st["width"], "h": st["height"], "fps": float(num) / float(den or 1),
            "dur": float(j["format"]["duration"])}


def scan(path, threshold=0.30):
    """Detect hard cuts and black ranges (incl. fades to black)."""
    SCENES.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "info", "-i", path, "-an", "-vf",
           f"scale=480:-2,blackdetect=d=0.15:pic_th=0.92:pix_th=0.08,select='gt(scene,{threshold})',showinfo",
           "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    cuts = sorted({round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", err)})
    black = [[round(float(a), 2), round(float(b), 2)]
             for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]
    info = probe(path)
    black = [[fade_start(path, a, cuts), b] for a, b in black]
    res = {"path": path, "duration": info["dur"], "cuts": cuts, "black": black}
    out = SCENES / (Path(path).stem + ".json")
    out.write_text(json.dumps(res, indent=1))
    print(f"{path}: {len(cuts)} cuts, {len(black)} black ranges, {info['dur']:.1f}s -> {out}")
    return res


def luma_trace(path, start, length, fps=10):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(0, start):.3f}", "-t", f"{length:.3f}", "-i", path, "-an", "-vf",
           f"fps={fps},scale=160:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-", "-f", "null", "-"]
    out = subprocess.run(cmd, capture_output=True, text=True).stdout
    ts = [float(x) for x in re.findall(r"pts_time:([\d.]+)", out)]
    ys = [float(x) for x in re.findall(r"YAVG=([\d.]+)", out)]
    return [(max(0, start) + t, y) for t, y in zip(ts, ys)]


def fade_start(path, black_start, cuts, look_back=4.0):
    """Walk back from a black range to where the picture starts dimming (fade-outs are not black yet)."""
    prev_cut = max([c for c in cuts if c < black_start - 0.1], default=0.0)
    start = max(prev_cut, black_start - look_back)
    tr = luma_trace(path, start, black_start - start)
    if len(tr) < 4:
        return black_start
    base = max(y for _, y in tr[: max(2, len(tr) // 3)])
    floor = 17.0
    t0 = black_start
    for t, y in reversed(tr):
        if y < floor + 0.85 * (base - floor):
            t0 = t
        else:
            break
    return round(t0, 2)


def scan_data(path):
    p = SCENES / (Path(path).stem + ".json")
    if p.exists():
        return json.loads(p.read_text())
    return None


def available(path, t_in, cross_cuts=False):
    """Seconds of clean footage from t_in until the next cut, black range or end of file.
    cross_cuts=True ignores detected cuts (flashes/explosions trigger false cuts) but never black ranges."""
    d = scan_data(path)
    end = probe(path)["dur"] if d is None else d["duration"]
    limit = end - t_in
    if d:
        nxt = [] if cross_cuts else [c for c in d["cuts"] if c > t_in + 0.05]
        if nxt:
            limit = min(limit, nxt[0] - t_in - 0.12)
        for a, b in d["black"]:
            if b > t_in + 0.05:
                limit = min(limit, max(0.0, a - t_in - 0.25))  # a = start of the fade-out (see fade_start)
                break
    return max(0.0, limit)


def black_in_segment(path, t_in, length):
    """Black ranges (>=0.15s) inside [t_in, t_in+length] measured directly on the file."""
    cmd = ["ffmpeg", "-v", "info", "-ss", f"{t_in:.3f}", "-t", f"{length:.3f}", "-i", path, "-an", "-vf",
           "scale=320:-2,blackdetect=d=0.15:pic_th=0.92:pix_th=0.08", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    return [(float(a), float(b)) for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", err)]


def _font(size):
    from .config import FONTS_DIR
    for f in ("NotoSansJP-500.ttf", "NotoSans-500.ttf", "NotoSansSC-500.ttf"):
        if (FONTS_DIR / f).exists():
            return ImageFont.truetype(str(FONTS_DIR / f), size)
    return ImageFont.load_default()


def _sheet(tiles, labels, out_prefix, cols=6, rows=5, tw=320):
    paths = []
    font = _font(15)
    per = cols * rows
    for p in range(0, len(tiles), per):
        chunk = tiles[p:p + per]
        th = max(im.height for im in chunk)
        sheet = Image.new("RGB", (cols * tw, ((len(chunk) - 1) // cols + 1) * (th + 20)), "white")
        d = ImageDraw.Draw(sheet)
        for i, im in enumerate(chunk):
            x, y = (i % cols) * tw, (i // cols) * (th + 20)
            sheet.paste(im, (x, y))
            d.text((x + 3, y + th + 1), labels[p + i], fill="black", font=font)
        out = f"{out_prefix}_{p // per:02d}.jpg"
        sheet.save(out, quality=82)
        paths.append(out)
    return paths


def contact_video(path, every=8.0, start=0.0, end=None, tag=None, cols=6, rows=5):
    Path("assets/contact").mkdir(parents=True, exist_ok=True)
    tag = tag or Path(path).stem
    with tempfile.TemporaryDirectory() as tmp:
        cmd = ["ffmpeg", "-v", "error", "-ss", str(start), "-i", path]
        if end:
            cmd += ["-t", str(end - start)]
        cmd += ["-vf", f"fps=1/{every},scale=320:-2", f"{tmp}/f_%05d.jpg"]
        subprocess.run(cmd, check=True)
        files = sorted(os.listdir(tmp))
        tiles = [Image.open(f"{tmp}/{f}").convert("RGB") for f in files]
        labels = []
        for i in range(len(files)):
            t = start + i * every
            labels.append(f"{int(t // 60)}:{t % 60:04.1f}")
        out = _sheet(tiles, labels, f"assets/contact/{tag}", cols, rows)
    print("\n".join(out))
    return out


def contact_images(paths, tag, cols=6, rows=5):
    Path("assets/contact").mkdir(parents=True, exist_ok=True)
    tiles, labels = [], []
    for p in paths:
        try:
            im = Image.open(p).convert("RGB")
        except Exception:
            continue
        im.thumbnail((320, 240))
        canvas = Image.new("RGB", (320, 240), (235, 235, 235))
        canvas.paste(im, ((320 - im.width) // 2, (240 - im.height) // 2))
        tiles.append(canvas)
        labels.append(Path(p).stem[:40])
    out = _sheet(tiles, labels, f"assets/contact/{tag}", cols, rows)
    print("\n".join(out))
    return out


def gif2mp4(path, slow=1.0, loops=1, out=None):
    """Animated GIF -> H.264 MP4 (optionally slowed / looped). Use the result as vid:<path>."""
    out = out or str(Path("assets/derived") / (Path(path).stem + ".mp4"))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    inputs = []
    for _ in range(loops):
        inputs += ["-i", path]
    fc = "".join(f"[{i}:v]" for i in range(loops)) + f"concat=n={loops}:v=1[c];[c]setpts={1 / slow}*PTS," \
         f"fps=30,scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=lanczos,format=yuv420p[v]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]",
                    "-c:v", "libx264", "-crf", "14", "-an", out], check=True)
    print(out, probe(out))
    return out
