"""Drawing primitives shared by every graphic (library templates and project custom_gfx.py).

All graphics draw on a 1920x1080 RGB canvas (scaled if the project uses another size).
Colours and fonts come from project.yaml `design`. Every text() call records its bounding box in
BOXES so QA can verify that no text leaves the safe area, enters the subtitle zone or overlaps
other text (lesson: an overflowing label was only found by eye after rendering).
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .. import config

W, H = 1920, 1080
BOXES = []          # filled during one render() call: (x0, y0, x1, y1, text)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class _Palette:
    def __getattr__(self, k):
        pal = config.load()["design"]["palette"]
        if k.lower() in pal:
            return _rgb(pal[k.lower()])
        raise AttributeError(k)


C = _Palette()          # C.BG, C.TEXT, C.MUTED, C.ACCENT, C.SECONDARY, C.PAPER, C.INK, C.LINE, C.DIM, C.CARD_BG


@lru_cache(None)
def F(kind, size):
    fonts = config.load()["design"]["fonts"]
    alias = {"serifb": "serif_bold", "sansm": "sans_medium", "sansb": "sans_bold"}
    name = fonts.get(alias.get(kind, kind)) or fonts["sans"]
    for p in (config.FONTS_DIR / name, name, "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(str(p), size)
    raise FileNotFoundError(f"font {name} not found in {config.FONTS_DIR} (run scripts/setup.sh <lang>)")


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, start, length=0.6):
    return ease((t - start) / length) if length > 0 else float(t >= start)


def mix(c, a, bg=None):
    bg = bg or C.BG
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


def canvas(bg=None):
    return Image.new("RGB", (W, H), bg or C.BG)


def text(d, xy, s, font, fill, anchor="la", a=1.0, bg=None, spacing=10, align=None):
    if a <= 0.01 or not s:
        return None
    align = align or ("center" if anchor[0] == "m" else ("right" if anchor[0] == "r" else "left"))
    d.multiline_text(xy, s, font=font, fill=mix(fill, a, bg), anchor=anchor, spacing=spacing, align=align)
    bb = d.multiline_textbbox(xy, s, font=font, anchor=anchor, spacing=spacing, align=align)
    if a > 0.05:
        BOXES.append((*bb, s))
    return bb


def tw(s, font):
    return font.getlength(s)


def fit_font(kind, size, s, max_w, min_size=18):
    """Largest font size <= size whose widest line fits max_w."""
    while size > min_size and max(F(kind, size).getlength(x) for x in s.split("\n")) > max_w:
        size -= 2
    return F(kind, size)


def partial_line(d, p0, p1, frac, fill, width=3):
    if frac <= 0:
        return
    frac = min(1.0, frac)
    d.line([p0, (p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac)], fill=fill, width=width)


def source(d, s, a=1.0):
    """Small source line, bottom-right, above the subtitle zone."""
    if s:
        text(d, (W - int(W * 0.05), 820), s, F("sans", 22), C.MUTED, anchor="ra", a=a)


def title_line(d, s, t=0.0, delay=0.1):
    """Graphic heading at the top-left safe corner."""
    text(d, (96, 96), s, F("sans_medium", 32), C.TEXT, "la", ramp(t, delay, 0.5))


def nl(s):
    return (s or "").replace("\\N", "\n").replace("\\n", "\n")


@lru_cache(8)
def photo_bg(path, darkness=0.85, blur=6):
    im = Image.open(path).convert("RGB")
    im = im.resize((W, int(W * im.height / im.width)))
    if im.height < H:
        im = im.resize((int(H * im.width / im.height), H))
    left, top = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(blur))
    return Image.blend(im.convert("L").convert("RGB"), Image.new("RGB", (W, H), C.BG), darkness)


# ---------------------------------------------------------------- paper documents
def paper(w, h, seed=3):
    im = Image.new("RGBA", (w, h), C.PAPER + (255,))
    noise = (np.random.RandomState(seed).rand(h, w) * 16).astype(np.uint8)
    arr = np.array(im)
    arr[..., :3] = np.clip(arr[..., :3].astype(int) - noise[..., None], 0, 255)
    return Image.fromarray(arr)


def place(im, layer, a, cx, cy, angle=0.0, shadow=True):
    pp = layer.rotate(angle, expand=True, resample=Image.BICUBIC) if angle else layer
    alpha = pp.split()[3].point(lambda v: int(v * a))
    if shadow:
        sh = Image.new("RGBA", pp.size, (0, 0, 0, 140))
        im.paste(sh, (int(cx - pp.width / 2 + 14), int(cy - pp.height / 2 + 16)), alpha.point(lambda v: int(v * 0.6)))
    im.paste(pp, (int(cx - pp.width / 2), int(cy - pp.height / 2)), alpha)
    return (cx - pp.width / 2, cy - pp.height / 2, cx + pp.width / 2, cy + pp.height / 2)


# ---------------------------------------------------------------- param helpers
class P(dict):
    """Template parameters: strings from VIS lines or native values from graphics.yaml."""

    def s(self, k, default=""):
        v = self.get(k, default)
        return nl(v) if isinstance(v, str) else v

    def i(self, k, default=0):
        try:
            return int(float(self.get(k, default)))
        except (TypeError, ValueError):
            return default

    def f(self, k, default=0.0):
        try:
            return float(self.get(k, default))
        except (TypeError, ValueError):
            return default

    def l(self, k, sep=";"):
        v = self.get(k)
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [nl(x.strip()) for x in str(v).split(sep)]

    def rows(self, k, sep=";", fsep="|"):
        """List of rows; each row a list of fields ("a|b|c;d|e|f" or YAML list of lists/strings)."""
        out = []
        for r in self.l(k, sep):
            if isinstance(r, (list, tuple)):
                out.append([nl(str(x)) for x in r])
            elif isinstance(r, dict):
                out.append(r)
            else:
                out.append([nl(x.strip()) for x in str(r).split(fsep)])
        return out


def roman(n):
    return "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫ"[n - 1] if 1 <= n <= 12 else str(n)


def deg2rad(x):
    return math.radians(x)
