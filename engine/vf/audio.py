"""Audio: per-scene voice levelling + chapter music with ducking + loudness normalisation -> out/mix.wav
Then `final`: join chapter videos with concat -c copy (no re-encode) and mux AAC -> out/video.mp4.

project.yaml
  music:
    default: assets/music/Track.mp3          # used for chapters without their own entry (optional)
    chapters:
      HOOK: {file: assets/music/A.mp3}
      CH4:  {file: assets/music/B.mp3, offset: 120, cut_from_scene: S429}   # silence from that scene on
    level_between: 0.22                      # music gain between sentences
    level_under_voice: 0.09                  # music gain under narration
"""
import json
import os
import subprocess
from pathlib import Path

import numpy as np

from . import config

OUT = Path("out")
SR = 48000


def load_audio(path, mono=True):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1" if mono else "2",
                                   "-ar", str(SR), "-"])
    a = np.frombuffer(raw, np.float32)
    return a if mono else a.reshape(-1, 2)


def mix():
    cfg = config.load()
    M = cfg["music"]
    tl = json.loads((OUT / "timeline.json").read_text())
    n = int(tl["total"] * SR) + SR
    vo = np.zeros(n, np.float32)
    for e in tl["timeline"]:
        if e["type"] == "vo":
            a = load_audio(e["wav"])
            v = a[np.abs(a) > 0.01]
            rms = float(np.sqrt(np.mean(v ** 2))) if len(v) else 0.1
            a = a * min(4.0, 0.085 / max(rms, 1e-4))
            i = int(e["t0"] * SR)
            vo[i:i + len(a)] += a[: n - i]
    win = int(0.05 * SR)
    env = np.sqrt(np.convolve(vo ** 2, np.ones(win) / win, mode="same"))
    act = (env > 0.01).astype(np.float32)
    duck = np.zeros_like(act)
    g = 0.0
    att, rel = 1 / (0.15 * SR), 1 / (0.6 * SR)
    for i in range(0, len(act), 240):
        target = act[i:i + 240].max()
        g = min(target, g + att * 240) if target > g else max(target, g - rel * 240)
        duck[i:i + 240] = g
    music = np.zeros((n, 2), np.float32)
    shots = [e for e in tl["timeline"] if e["type"] == "shot"]
    for ci, c in enumerate(tl["chapters"]):
        spec = M["chapters"].get(c["id"]) or ({"file": M["default"]} if M.get("default") else None)
        if not spec:
            continue
        if isinstance(spec, str):
            spec = {"file": spec}
        m = load_audio(spec["file"], mono=False)[int(float(spec.get("offset", 0)) * SR):]
        t0 = c["start"]
        t1 = c.get("end_film", c["end"]) if ci == len(tl["chapters"]) - 1 else c["end"] + 1.5
        L = int((t1 - t0) * SR)
        if len(m) < L:
            m = np.concatenate([m] * (L // max(1, len(m)) + 2))
        seg = m[:L].copy()
        fi, fo = int(M["fade_in"] * SR), int(M["fade_out"] * SR)
        seg[:fi] *= np.linspace(0, 1, fi)[:, None]
        seg[-fo:] *= np.linspace(1, 0, fo)[:, None]
        if spec.get("cut_from_scene"):
            st = next(e["t0"] for e in shots if e["scene"] == spec["cut_from_scene"])
            cut = int((st - t0) * SR)
            fl = int(0.8 * SR)
            seg[max(0, cut - fl):cut] *= np.linspace(1, 0, min(fl, cut))[:, None]
            seg[cut:] = 0
        i0 = int(t0 * SR)
        music[i0:i0 + len(seg)] += seg[: n - i0]
    peak = np.percentile(np.abs(music), 99.5) + 1e-6
    music *= 0.5 / peak
    gain = M["level_between"] - (M["level_between"] - M["level_under_voice"]) * duck
    out = np.clip(music * gain[:, None] + vo[:, None], -1, 1)
    raw = OUT / "mix.f32"
    out[: int(tl["total"] * SR)].astype(np.float32).tofile(raw)
    Lc = cfg["loudness"]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(raw), "-af",
                    f"loudnorm=I={Lc['integrated']}:TP={Lc['true_peak']}:LRA={Lc['lra']}", "-ar", str(SR),
                    "-c:a", "pcm_s16le", str(OUT / "mix.wav")], check=True)
    os.remove(raw)
    print(f"mix.wav {tl['total']:.1f}s")


def final():
    cfg = config.load()
    tl = json.loads((OUT / "timeline.json").read_text())
    from .render import changed
    stale = changed(tl)
    if stale:
        raise SystemExit(f"chapters out of date: {stale} - run: vf render --changed")
    if not (OUT / "mix.wav").exists() or os.path.getmtime(OUT / "mix.wav") < os.path.getmtime(OUT / "timeline.json"):
        mix()
    lst = OUT / "concat.txt"
    paths = [(OUT / ("ch_" + c["id"] + ".mp4")).resolve() for c in tl["chapters"]]
    lst.write_text("".join(f"file '{p}'\n" for p in paths))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(OUT / "mix.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", cfg["encode"]["audio_bitrate"],
                    "-ar", "48000", "-movflags", "+faststart", "-t", f"{tl['total']:.3f}", str(OUT / "video.mp4")],
                   check=True)
    print("video.mp4 written - now run: vf qa")
