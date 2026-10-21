from PIL import ImageDraw

from vf.gfx.core import C, F, W, H, canvas, mix, ramp, source, text, title_line


def g_ring(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    title_line(d, p.s("title", "カスタム図"), t)
    r = 160 + 40 * ramp(t, 0.2, 1.0)
    d.ellipse([W / 2 - r, 470 - r, W / 2 + r, 470 + r], outline=mix(C.SECONDARY, 0.9), width=6)
    text(d, (W / 2, 470), "Oリング", F("serif", 48), C.TEXT, "mm", ramp(t, 0.4, 0.6))
    source(d, "模式図")
    return im
