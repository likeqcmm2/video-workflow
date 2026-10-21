"""Create synthetic assets for the smoke test (no network, no licences involved)."""
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

Path("assets/img").mkdir(parents=True, exist_ok=True)
Path("assets/video").mkdir(parents=True, exist_ok=True)
Path("assets/music").mkdir(parents=True, exist_ok=True)
rs = np.random.RandomState(1)
for name, (w, h) in {"landscape": (2400, 1500), "portrait": (900, 1300), "small": (640, 420)}.items():
    y, x = np.mgrid[0:h, 0:w]
    arr = np.stack([(x / w * 200 + 30), (y / h * 150 + 50), (120 + 60 * np.sin(x / 90.0))], -1)
    arr += rs.normal(0, 6, arr.shape)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.35, h * 0.3, w * 0.65, h * 0.7], outline=(250, 250, 240), width=8)
    im.save(f"assets/img/{name}.jpg", quality=92)
# video: 8 s scene A | hard cut | 6 s scene B | 2 s fade to black | 4 s black
subprocess.run(["ffmpeg", "-v", "error", "-y",
                "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=8",
                "-f", "lavfi", "-i", "mandelbrot=size=1280x720:rate=30",
                "-f", "lavfi", "-i", "color=black:size=1280x720:rate=30:duration=4",
                "-filter_complex", "[1:v]trim=duration=8,setpts=PTS-STARTPTS,fade=t=out:st=6:d=2[b];[0:v][b][2:v]concat=n=3:v=1[v]",
                "-map", "[v]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "assets/video/clip.mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=220:duration=90",
                "-f", "lavfi", "-i", "sine=frequency=330:duration=90", "-filter_complex",
                "[0][1]amix=inputs=2,volume=0.3,aformat=channel_layouts=stereo", "assets/music/tone.mp3"], check=True)
# animation clip (stands in for a Manim/Remotion/Blender render) and an alpha overlay (VP9 + alpha)
Path("assets/anim").mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "life=s=1920x1080:mold=10:r=30:ratio=0.1:death_color=#101820:life_color=#40a0c0",
                "-t", "12", "-c:v", "libx264", "-pix_fmt", "yuv420p", "assets/anim/cells.mp4"], check=True)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=white:s=960x540:r=30:d=12,format=rgba",
                "-vf", "geq=r=255:g=255:b=255:a='if(between(Y,380,384)*between(X,100+T*40,310+T*40),230,0)',scale=1920:1080",
                "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", "-b:v", "1M", "assets/anim/line_alpha.webm"], check=True)
print("fixtures ok")
