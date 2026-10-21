"""Project-specific graphics. Every function g_<name>(p, t, dur) becomes  VIS: gfx:<name> | key=value ...
Use these only for things the library (engine/vf/gfx/library.py) cannot show - e.g. a mechanism diagram.
Keep text inside the 5 % safe area and above the two-line subtitle block (~y 887 at 1080p); `vf preflight` checks it.
"""
from PIL import ImageDraw

from vf.gfx.core import C, F, W, H, canvas, ease, mix, ramp, source, text, title_line  # noqa: F401


# def g_example(p, t, dur):
#     im = canvas()
#     d = ImageDraw.Draw(im)
#     title_line(d, p.s("title"), t)
#     return im
