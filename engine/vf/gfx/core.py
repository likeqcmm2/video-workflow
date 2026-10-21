"""Neutral drawing primitives for a project's own graphics (custom_gfx.py). No styles live here.

All graphics draw on a 1920x1080 canvas (scaled if the project uses another size). Colours (C.<key>) and
fonts (F(<role>, size)) are whatever the film's project.yaml `design.palette` / `design.fonts` define.
Every text() call records its bounding box in BOXES so QA can verify that no text leaves the safe area,
enters the subtitle block or overlaps other text (lesson: an overflowing label was only found by eye).
A graphic may return RGBA: transparent pixels show the shot underneath when used as an overlay.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .. import config

W, H = 1920, 1080
BOXES = []          # filled during one render() call: (x0, y0, x1, y1, text, font_path)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


class _Palette:
    """C.<KEY> -> RGB tuple of design.palette[key] (any keys the film defines)."""

    def __getattr__(self, k):
        pal = config.load()["design"]["palette"]
        if k.lower() in pal:
            return _rgb(pal[k.lower()])
        raise AttributeError(f"design.palette has no {k.lower()!r} (keys: {sorted(pal)})")


C = _Palette()


@lru_cache(None)
def F(role, size):
    """Font for a role defined in design.fonts (role -> file in vendor/fonts, or an absolute path)."""
    fonts = config.load()["design"]["fonts"]
    if role not in fonts:
        raise KeyError(f"design.fonts has no role {role!r} (roles: {sorted(fonts)})")
    name = fonts[role]
    for p in (config.FONTS_DIR / name, name):
        if os.path.exists(p):
            return ImageFont.truetype(str(p), size)
    raise FileNotFoundError(f"font {name} not found in {config.FONTS_DIR} (scripts/fetch_fonts.py \"Family:wghts\")")


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
    """Draw text (fill blended towards bg by alpha a) and record its box for QA. Use it for ALL text."""
    if a <= 0.01 or not s:
        return None
    align = align or ("center" if anchor[0] == "m" else ("right" if anchor[0] == "r" else "left"))
    d.multiline_text(xy, s, font=font, fill=mix(fill, a, bg), anchor=anchor, spacing=spacing, align=align)
    bb = d.multiline_textbbox(xy, s, font=font, anchor=anchor, spacing=spacing, align=align)
    if a > 0.05:
        BOXES.append((*bb, s, getattr(font, "path", None)))
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
