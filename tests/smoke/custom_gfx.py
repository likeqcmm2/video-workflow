"""Graphics of the smoke-test film. They exist to exercise the engine (cards, charts, maps, documents,
RGBA overlays) - they are not a style to copy."""
from PIL import Image, ImageDraw

from vf.gfx import kit
from vf.gfx.core import C, F, H, W, canvas, ease, fit_font, mix, ramp, text


def g_chapter(p, t, dur):
    """Chapter card. num, title"""
    im = canvas()
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.2, 0.6) * (1 - ramp(t, dur - 0.6, 0.5))
    text(d, (W / 2, 470), p.s("num"), F("text_medium", 34), C.ACCENT, "mm", a)
    text(d, (W / 2, 560), p.s("title"), F("display", 76), C.TEXT, "mm", a)
    return im


def g_quote(p, t, dur):
    """Quote. text, attr"""
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 440), p.s("text"), fit_font("display", 60, p.s("text"), W * 0.8), C.TEXT, "mm", ramp(t, 0.2, 0.6))
    text(d, (W / 2, 540), "―― " + p.s("attr"), F("text", 30), C.MUTED, "mm", ramp(t, 0.7, 0.6))
    return im


def g_bars(p, t, dur):
    """Bars. title, labels, values"""
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (96, 96), p.s("title"), F("text_medium", 32), C.TEXT)
    vals = [float(v) for v in p.l("values")]
    Y = kit.scale(0, max(vals), 760, 260)
    for i, (lb, v) in enumerate(zip(p.l("labels"), vals)):
        cx = 400 + i * 320
        g = ease((t - 0.2 - 0.2 * i) / 0.8)
        d.rectangle([cx - 50, Y(v * g), cx + 50, 760], fill=mix(C.SECONDARY, 0.8))
        text(d, (cx, 780), lb, F("text", 28), C.MUTED, "ma")
        text(d, (cx, Y(v * g) - 50), f"{v:g}回", F("display", 34), C.TEXT, "ma", g)
    return im


def g_map(p, t, dur):
    """US map with three linked points (kit.shapes / kit.Projector)."""
    rows = kit.shapes("us48")
    pr = kit.Projector(rows)
    im = canvas()
    d = ImageDraw.Draw(im)
    hl = {"Utah", "Alabama", "Florida"}
    for name, polys in rows:
        for poly in polys:
            d.polygon(pr.polygon(poly), fill=mix(C.SECONDARY, 0.22) if name in hl else None, outline=mix(C.LINE, 0.35))
    pts = {"ut": (-112.2, 41.6, "ユタ州"), "al": (-86.6, 34.6, "アラバマ州"), "fl": (-80.6, 28.5, "フロリダ州")}
    xy = {k: pr(v[0], v[1]) for k, v in pts.items()}
    for i, (k, (_, _, lab)) in enumerate(pts.items()):
        x, y = xy[k]
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=C.TEXT)
        text(d, (x + 24, y - 20), lab, F("text_medium", 30), C.TEXT, "la", ramp(t, 0.3 * i, 0.5))
    text(d, (96, 96), "3か所を結んだ電話会議", F("text_medium", 32), C.TEXT)
    text(d, (W - 96, 820), "地図：Natural Earth", F("text", 22), C.MUTED, "ra")
    return im


def g_document(p, t, dur):
    """Reconstructed memo on paper (kit.paper / kit.place)."""
    im = canvas().convert("RGBA")
    pap = kit.paper(900, 600, C.PAPER)
    dd = ImageDraw.Draw(pap)
    for i, line in enumerate(["MORTON THIOKOL, INC.", "", "31 July 1985", "", "SUBJECT: O-Ring Erosion"]):
        dd.text((60, 50 + i * 38), line, font=F("mono", 24), fill=C.INK)
    kit.place(im, pap, ramp(t, 0.1, 0.6), 600, 460, -1.5)
    d = ImageDraw.Draw(im)
    text(d, (1110, 330), "技術者のメモ", F("text_medium", 32), C.TEXT, "la", ramp(t, 0.6, 0.6))
    text(d, (1110, 390), "文面の一部を再現", F("text", 26), C.MUTED, "la", ramp(t, 0.9, 0.6))
    return im.convert("RGB")


def g_label(p, t, dur):
    """RGBA overlay: a caption box over footage (transparent elsewhere)."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.3, 0.5)
    d.rectangle([96, 140, 760, 220], fill=(0, 0, 0, int(150 * a)))
    text(d, (120, 180), p.s("label", "オーバーレイのテスト"), F("text_medium", 34), C.TEXT, "lm", a, bg=(0, 0, 0))
    return im
