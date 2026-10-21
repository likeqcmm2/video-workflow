"""Frame sources: stills (Ken Burns / contained on blurred background) and archival video readers."""
import subprocess

import cv2
import numpy as np

from . import config
from .assets import video_opts
from .media import available, probe

_img_cache, _bg_cache = {}, {}


def load_image(path):
    if path in _img_cache:
        return _img_cache[path]
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None:
        from PIL import Image
        im = cv2.cvtColor(np.array(Image.open(path).convert("RGB")), cv2.COLOR_RGB2BGR)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]
    s = min(1.0, 2600 / max(w, h))
    if s < 1:
        im = cv2.resize(im, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    _img_cache.clear()
    _img_cache[path] = im
    return im


def blur_bg(small):
    W, H, _ = config.size()
    b = cv2.resize(np.ascontiguousarray(small), (192, 108), interpolation=cv2.INTER_AREA)
    b = cv2.GaussianBlur(b, (0, 0), 6)
    b = cv2.convertScaleAbs(b, alpha=0.35)
    return cv2.resize(b, (W, H), interpolation=cv2.INTER_LINEAR)


def kb_params(kb, u, amp):
    if kb == "in":
        return 1.0 + amp * u, 0, 0
    if kb == "out":
        return 1.0 + amp - amp * u, 0, 0
    if kb in ("l", "r", "u", "d"):
        s = -1 if kb in ("l", "u") else 1
        mv = s * (-0.8 + 1.6 * u)
        return 1.0 + amp, (mv if kb in ("l", "r") else 0), (mv if kb in ("u", "d") else 0)
    if kb == "none":
        return 1.0, 0, 0
    return 1.03, 0, 0


def image_frame(img, opts, u):
    """fit=cover (fills frame, Ken Burns) | contain (whole picture on a blurred copy of itself).
    Default: cover for landscape 1.2-2.2 aspect, contain otherwise (portraits, documents)."""
    W, H, _ = config.size()
    amp = config.load()["design"]["kenburns"]
    h, w = img.shape[:2]
    asp = w / h
    fit = opts.get("fit") or ("cover" if 1.2 <= asp <= 2.2 else "contain")
    fx, fy = [float(x) for x in opts.get("focus", "0.5,0.5").split(",")]
    sc, dx, dy = kb_params(opts.get("kb", "in"), u, amp)
    if fit == "cover":
        base = max(W / w, H / h)
        s = base * sc
        vw, vh = W / s, H / s
        cx = min(max(fx * w + dx * (w - vw) / 2, vw / 2), w - vw / 2)
        cy = min(max(fy * h + dy * (h - vh) / 2, vh / 2), h - vh / 2)
        M = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
        return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    base = min(W * 0.86 / w, H * 0.80 / h)
    s = base * (1.0 + (sc - 1.0) * 0.4)
    key = id(img)
    if _bg_cache.get("k") != key:
        _bg_cache["k"] = key
        _bg_cache["bg"] = blur_bg(cv2.resize(img, (W // 4, max(1, int(W / 4 * h / w))), interpolation=cv2.INTER_AREA))
    cy_frame = H * 0.435          # lifted so the picture stays clear of the subtitle zone
    M = np.float32([[s, 0, W / 2 - s * w / 2 + dx * 20], [0, s, cy_frame - s * h / 2 + dy * 20]])
    out = _bg_cache["bg"].copy()
    cv2.warpAffine(img, M, (W, H), dst=out, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
    return out


class VideoReader:
    """Streams frames of [t_in, t_in + dur] scaled for the frame. If the clean footage before the next cut /
    black range is shorter than the shot, plays it slower (>= min_speed) instead of crossing the cut."""

    def __init__(self, path, t_in, dur, min_speed=0.5, cross_cuts=False):
        W, H, FPS = config.size()
        self.path = path
        av = available(path, t_in, cross_cuts)
        self.speed = 1.0 if dur <= av else max(min_speed, av / dur)
        need = dur * self.speed
        info = probe(path)
        sw, sh = info["w"], info["h"]
        vo = video_opts(path)
        cropf = ""
        if vo.get("crop"):
            cw, ch, cx, cy = vo["crop"]
            sw, sh = cw, ch
            cropf = f"crop={cw}:{ch}:{cx}:{cy},"
        self.desat = float(vo.get("desat", 0) or 0)
        self.small = sh < 360
        th = int(H * 0.70) if self.small else H
        tw = int(round(th * sw / sh / 2) * 2)
        if tw > W:
            tw, th = W, int(round(W * sh / sw / 2) * 2)
        self.tw, self.th = tw, th
        vf = f"{cropf}setpts=PTS/{self.speed},fps={FPS},scale={tw}:{th}:flags=lanczos"
        self.proc = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t_in:.3f}", "-i", path, "-t", f"{need + 0.2:.3f}",
                                      "-an", "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        self.last = None

    def read(self):
        b = self.proc.stdout.read(self.tw * self.th * 3)
        if len(b) == self.tw * self.th * 3:
            fr = np.frombuffer(b, np.uint8).reshape(self.th, self.tw, 3)
            if self.desat:
                fr = np.ascontiguousarray(fr)
                g3 = cv2.cvtColor(cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
                fr = cv2.addWeighted(fr, 1 - self.desat, g3, self.desat, 0)
            self.last = fr
        return self.last

    def close(self):
        try:
            self.proc.stdout.close()
            self.proc.kill()
            self.proc.wait(timeout=5)
        except Exception:
            pass


def video_frame(fr, rd, u):
    W, H, _ = config.size()
    if fr is None:
        return np.zeros((H, W, 3), np.uint8)
    th, tw = fr.shape[:2]
    if tw == W and th == H:
        s = 1.0 + 0.025 * u
        M = np.float32([[s, 0, W / 2 - s * W / 2], [0, s, H / 2 - s * H / 2]])
        return cv2.warpAffine(fr, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    out = blur_bg(fr)
    s = 1.0 + 0.02 * u
    lift = 20 if rd.small else 0
    M = np.float32([[s, 0, W / 2 - s * tw / 2], [0, s, H / 2 - s * th / 2 - lift]])
    cv2.warpAffine(np.ascontiguousarray(fr), M, (W, H), dst=out, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
    if rd.small:   # thin frame line around small archival footage
        x0, y0 = int(W / 2 - s * tw / 2) - 3, int(H / 2 - s * th / 2 - lift) - 3
        cv2.rectangle(out, (x0, y0), (x0 + int(s * tw) + 5, y0 + int(s * th) + 5), (120, 120, 116), 2)
    return out
