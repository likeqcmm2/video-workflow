"""Generic, data-driven graphic templates.  VIS:  gfx:<name> | key=value | ...   or   gfx:<name> | spec=<id>
(spec ids are looked up in the project's graphics.yaml, which may hold lists/dicts).

Every template: f(p: P, t: float, dur: float) -> PIL.Image 1920x1080.
`step=N` re-uses one graphic across consecutive scenes (step 1 builds up, later steps start complete).
See docs/08-edit-render.md for the parameter table of every template.
"""
import math
from functools import lru_cache

from PIL import ImageDraw

from .. import config
from .core import (BOXES, C, F, H, P, W, canvas, ease, fit_font, mix, nl, paper, partial_line, photo_bg,
                   place, ramp, roman, source, text, title_line, tw)


# ------------------------------------------------------------------ cards
def g_title(p, t, dur):
    """Film title card. kicker, text, sub, sub2, bg=<image path>, bg_dark=0.88"""
    im = photo_bg(p.s("bg"), p.f("bg_dark", 0.88)).copy() if p.get("bg") else canvas()
    d = ImageDraw.Draw(im)
    a1, a2, a3 = ramp(t, 0.2, 1.0), ramp(t, 1.0, 1.0), ramp(t, 1.8, 1.0)
    text(d, (W / 2, 330), p.s("kicker"), F("sans", 30), C.MUTED, "mm", a1)
    big = fit_font("serif_bold", 104, p.s("text"), W * 0.84)
    text(d, (W / 2, 450), p.s("text"), big, C.TEXT, "mm", a2)
    lw = 520 * ease((t - 1.4) / 1.2)
    if lw > 0:
        d.line([(W / 2 - lw, 548), (W / 2 + lw, 548)], fill=mix(C.ACCENT, 0.9), width=2)
    text(d, (W / 2, 620), p.s("sub"), fit_font("serif", 44, p.s("sub"), W * 0.84), C.TEXT, "mm", a3)
    text(d, (W / 2, 690), p.s("sub2"), fit_font("sans", 32, p.s("sub2"), W * 0.84), C.MUTED, "mm", a3)
    return im


def g_chapter(p, t, dur):
    """Chapter card (used automatically for ### chapters). num, title"""
    bgc = C.CARD_BG
    im = canvas(bgc)
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.3, 0.8) * (1 - ramp(t, dur - 0.7, 0.6))
    text(d, (W / 2, 470), p.s("num"), F("sans_medium", 34), C.ACCENT, "mm", a, bgc)
    text(d, (W / 2, 560), p.s("title"), fit_font("serif", 76, p.s("title"), W * 0.8), C.TEXT, "mm", a, bgc)
    lw = 160 * ease((t - 0.5) / 1.0) * (1 - ramp(t, dur - 0.7, 0.6))
    if lw > 1:
        d.line([(W / 2 - lw, 625), (W / 2 + lw, 625)], fill=mix(C.LINE, 0.6 * a, bgc), width=1)
    return im


def g_quote(p, t, dur):
    """Quote card. text (use \\N for line breaks), attr, kind=name (big name + role instead)"""
    im = canvas()
    d = ImageDraw.Draw(im)
    a, a2 = ramp(t, 0.15, 0.7), ramp(t, 0.7, 0.7)
    body = p.s("text")
    if p.get("kind") == "name":
        text(d, (W / 2, 470), body, fit_font("serif", 64, body, W * 0.84), C.TEXT, "mm", a)
        text(d, (W / 2, 570), p.s("attr"), F("sans", 32), C.MUTED, "mm", a2)
        return im
    n = body.count("\n") + 1
    size = 58 if n <= 2 else 50
    f = fit_font("serif", size, body, W * 0.84)
    y = 470 - (n - 1) * (f.size * 0.75)
    text(d, (W / 2, y), body, f, C.TEXT, "mm", a, spacing=int(f.size * 0.55))
    if p.get("attr"):
        text(d, (W / 2, y + n * f.size * 0.85 + 60), "―― " + p.s("attr"), F("sans", 30), C.MUTED, "mm", a2)
    return im


def g_textcard(p, t, dur):
    """Plain statement card. text, sub"""
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 450), p.s("text"), fit_font("serif", 66, p.s("text"), W * 0.84), C.TEXT, "mm", ramp(t, 0.15, 0.7))
    text(d, (W / 2, 560), p.s("sub"), fit_font("sans", 34, p.s("sub"), W * 0.84), C.MUTED, "mm", ramp(t, 0.8, 0.7))
    return im


def g_term(p, t, dur):
    """Key term card. term, en (translation/original), note"""
    im = canvas()
    d = ImageDraw.Draw(im)
    term = p.s("term")
    text(d, (W / 2, 430), term, fit_font("serif", 70, term, W * 0.84), C.TEXT, "mm", ramp(t, 0.2, 0.8))
    text(d, (W / 2, 525), p.s("en"), F("serif", 34), C.SECONDARY, "mm", ramp(t, 0.9, 0.8))
    text(d, (W / 2, 610), p.s("note"), fit_font("sans", 28, p.s("note"), W * 0.84), C.MUTED, "mm", ramp(t, 1.4, 0.8))
    return im


def g_ranking(p, t, dur):
    """Top-N item card. rank, title, sub, bg=<image path> (fast/bright genres)"""
    im = photo_bg(p.s("bg"), 0.55, 4).copy() if p.get("bg") else canvas()
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.05, 0.35)
    text(d, (200, 540), p.s("rank"), F("serif_bold", 320), C.ACCENT, "lm", a)
    x = 200 + tw(p.s("rank"), F("serif_bold", 320)) + 60
    text(d, (x, 500), p.s("title"), fit_font("serif_bold", 84, p.s("title"), W - x - 120), C.TEXT, "lm", ramp(t, 0.2, 0.35))
    text(d, (x, 600), p.s("sub"), fit_font("sans", 36, p.s("sub"), W - x - 120), C.MUTED, "lm", ramp(t, 0.4, 0.35))
    return im


def g_counter(p, t, dur):
    """Animated number. value, prefix, suffix, label, decimals, sub"""
    im = canvas()
    d = ImageDraw.Draw(im)
    v = p.f("value") * ease((t - 0.2) / max(0.8, min(2.0, dur * 0.4)))
    dec = p.i("decimals", 0)
    num = f"{v:,.{dec}f}"
    s = p.s("prefix") + num + p.s("suffix")
    text(d, (W / 2, 470), s, fit_font("serif_bold", 150, s, W * 0.84), C.TEXT, "mm", ramp(t, 0.1, 0.4))
    text(d, (W / 2, 600), p.s("label"), F("sans_medium", 38), C.SECONDARY, "mm", ramp(t, 0.6, 0.6))
    text(d, (W / 2, 660), p.s("sub"), F("sans", 28), C.MUTED, "mm", ramp(t, 0.9, 0.6))
    source(d, p.s("source"))
    return im


# ------------------------------------------------------------------ lists / structures
def g_list(p, t, dur):
    """Numbered list. title, items (a;b;c), highlight (1-based, comma), numbering=roman|arabic|circled|none,
    columns=1|2, step=k (reveal: k-th build), source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    items = p.l("items")
    hl = {int(x) for x in str(p.get("highlight", "")).split(",") if x.strip().isdigit()}
    numbering = p.get("numbering", "circled")
    cols = p.i("columns", 1 if len(items) <= 5 else 2)
    if p.get("title"):
        title_line(d, p.s("title"), t)
    per_col = math.ceil(len(items) / cols)
    x0s = [160, 1000] if cols == 2 else [380]
    y0 = 300 if len(items) <= 4 else 220
    gap = 88 if per_col <= 5 else 70
    for i, it in enumerate(items):
        c, r = divmod(i, per_col)
        x, y = x0s[min(c, len(x0s) - 1)], y0 + r * gap
        a = ramp(t, 0.3 + 0.35 * i, 0.5)
        col = C.ACCENT if (i + 1) in hl else C.TEXT
        mark = {"roman": roman(i + 1), "arabic": f"{i + 1}.", "circled": "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"[i] if i < 12 else str(i + 1),
                "none": ""}.get(numbering, "")
        if mark:
            text(d, (x, y), mark, F("serif", 40), col if (i + 1) in hl else C.MUTED, "la", a)
        size = 40 if cols == 1 else 34
        text(d, (x + (70 if mark else 0), y), it, fit_font("serif", size, it, (760 if cols == 2 else 1300)), col, "la", a)
    if p.get("conclusion"):
        text(d, (x0s[0], y0 + per_col * gap + 40), p.s("conclusion"), F("serif", 40), C.ACCENT, "la",
             ramp(t, 0.5 + 0.35 * len(items), 0.6))
    source(d, p.s("source"))
    return im


def g_hierarchy(p, t, dur):
    """Stacked levels with a break. title, levels (top first ;), break_after (1-based index), break_label, source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    levels = p.l("levels")
    n = len(levels)
    if p.get("title"):
        title_line(d, p.s("title"), t)
    brk = p.i("break_after", 0)
    bw0, bw1 = 440, 1480
    h, gap = 100, 50
    top = max(170, 540 - (n * (h + gap)) // 2)
    for i, lv in enumerate(levels):
        y = top + i * (h + gap)
        a = ramp(t, 0.2 + 0.25 * (n - 1 - i), 0.5)
        d.rectangle([bw0, y, bw1, y + h], outline=mix(C.LINE, 0.6 * a), width=2)
        head, _, rest = lv.partition("|")
        if rest:
            text(d, (bw0 + 40, y + h / 2), head, F("sans_medium", 32), C.SECONDARY, "lm", a)
            text(d, (bw0 + 200, y + h / 2), rest, fit_font("sans", 32, rest, bw1 - bw0 - 240), C.TEXT, "lm", a)
        else:
            text(d, ((bw0 + bw1) / 2, y + h / 2), head, fit_font("sans", 32, head, bw1 - bw0 - 80), C.TEXT, "mm", a)
    for i in range(n - 1):
        y = top + i * (h + gap) + h
        a = ramp(t, 1.4, 0.5)
        is_brk = (i + 1) == brk
        d.line([(W / 2, y + 4), (W / 2, y + gap - 4)], fill=mix(C.ACCENT if is_brk else C.LINE, a if is_brk else 0.5 * a), width=3)
        if is_brk and p.get("break_label"):
            text(d, (W / 2 + 30, y + gap / 2), "×　" + p.s("break_label"), F("sans_medium", 30), C.ACCENT, "lm",
                 ramp(t, 2.0, 0.5))
    source(d, p.s("source"))
    return im


def g_boxes(p, t, dur):
    """Row of boxes (people / options). title, items ("name|role";...), note, verdict, source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    rows = p.rows("items")
    n = max(1, len(rows))
    if p.get("title"):
        text(d, (W / 2, 250), p.s("title"), F("sans_medium", 32), C.TEXT, "mm", ramp(t, 0.1, 0.5))
    bw = min(370, (W - 2 * 140 - (n - 1) * 30) // n)
    x0 = (W - (n * bw + (n - 1) * 30)) / 2
    for i, r in enumerate(rows):
        x = x0 + i * (bw + 30)
        a = ramp(t, 0.3 + 0.2 * i, 0.5)
        d.rectangle([x, 330, x + bw, 460], outline=mix(C.LINE, 0.6 * a), width=2)
        text(d, (x + bw / 2, 380), r[0], fit_font("sans_medium", 30, r[0], bw - 30), C.TEXT, "mm", a)
        if len(r) > 1:
            text(d, (x + bw / 2, 425), r[1], fit_font("sans", 24, r[1], bw - 30), C.MUTED, "mm", a)
    text(d, (W / 2, 540), p.s("note"), fit_font("sans", 28, p.s("note"), W * 0.8), C.MUTED, "mm", ramp(t, 1.0, 0.6))
    text(d, (W / 2, 650), p.s("verdict"), F("serif_bold", 48), C.ACCENT, "mm", ramp(t, 1.6, 0.6))
    source(d, p.s("source"))
    return im


def g_names(p, t, dur):
    """Several names side by side. caption, names (;), sub, step"""
    step = p.i("step", 1)
    im = canvas()
    d = ImageDraw.Draw(im)
    names = p.l("names")
    text(d, (W / 2, 250), p.s("caption"), F("sans", 32), C.MUTED, "mm", ramp(t, 0.1, 0.6) if step == 1 else 1)
    n = max(1, len(names))
    span = min(440, (W - 300) / n)
    for i, nm in enumerate(names):
        a = ramp(t, 0.5 + 0.4 * i, 0.6) if step == 1 else 1
        text(d, (W / 2 + (i - (n - 1) / 2) * span, 430), nm, fit_font("serif", 72, nm, span - 30), C.TEXT, "mm", a)
    if step >= 2 or p.get("sub_now"):
        text(d, (W / 2, 590), p.s("sub"), F("sans_medium", 40), C.SECONDARY, "mm", ramp(t, 0.3, 0.7))
    return im


# ------------------------------------------------------------------ charts
def g_bars(p, t, dur):
    """Bar chart. title, labels (;), values (;), unit, highlight (1-based idx -> accent outline),
    ghost (idx -> dashed target bar), tags ("idx|text";..) small text above bars, step (1 axes+ghost,
    2 animate bars, 3 all + highlight), source"""
    step = p.i("step", 3)
    im = canvas()
    d = ImageDraw.Draw(im)
    labels, vals = p.l("labels"), [float(v) for v in p.l("values")]
    unit = p.s("unit")
    hl = {int(x) for x in str(p.get("highlight", "")).split(",") if x.strip().isdigit()}
    ghost = {int(x) for x in str(p.get("ghost", "")).split(",") if x.strip().isdigit()}
    tags = {int(r[0]): r[1] for r in p.rows("tags") if len(r) > 1}
    x0, x1, ybase, ytop = 300, 1620, 760, 220
    vmax = max(vals) if vals else 1
    scale = (ybase - ytop) / vmax
    n = max(1, len(vals))
    gap = (x1 - x0) / n
    bw = min(110, gap * 0.6)
    d.line([(x0 - 30, ybase), (x1, ybase)], fill=mix(C.LINE, 0.6), width=2)
    if p.get("title"):
        title_line(d, p.s("title"), t)
    for i, (lb, v) in enumerate(zip(labels, vals)):
        k = i + 1
        cx = x0 + gap * (i + 0.5)
        text(d, (cx, ybase + 22), lb, fit_font("sans", 28, lb, gap - 10), C.MUTED, "ma")
        hgt = v * scale
        val = f"{v:g}{unit}"
        if k in ghost:
            a = ramp(t, 0.4, 0.8) if step == 1 else 1
            for yy in range(int(ybase - hgt), ybase, 16):
                d.line([(cx - bw / 2, yy), (cx - bw / 2, yy + 8)], fill=mix(C.TEXT, a * 0.8), width=2)
                d.line([(cx + bw / 2, yy), (cx + bw / 2, yy + 8)], fill=mix(C.TEXT, a * 0.8), width=2)
            d.line([(cx - bw / 2, ybase - hgt), (cx + bw / 2, ybase - hgt)], fill=mix(C.TEXT, a * 0.8), width=2)
            text(d, (cx, ybase - hgt - 60), val, F("serif", 40), C.TEXT, "ma", a)
            if k in tags:
                text(d, (cx, ybase - hgt - 100), tags[k], F("sans", 26), C.MUTED, "ma", a)
            continue
        if k in hl:
            if step < 3:
                continue
            a = ramp(t, 0.3, 0.8)
            d.rectangle([cx - bw / 2, ybase - hgt, cx + bw / 2, ybase], outline=mix(C.ACCENT, a), width=3)
            text(d, (cx, ybase - hgt - 56), val, F("serif", 40), C.ACCENT, "ma", a)
            if k in tags:
                text(d, (cx, ybase - hgt - 96), tags[k], F("sans", 26), C.MUTED, "ma", a)
            continue
        if step == 1:
            continue
        g = ease((t - 0.2 - 0.25 * i) / 0.8) if step == 2 else 1
        if hgt * g > 0:
            d.rectangle([cx - bw / 2, ybase - hgt * g, cx + bw / 2, ybase], fill=mix(C.SECONDARY, 0.75))
            text(d, (cx, ybase - hgt * g - 50), val, F("serif", 36), C.TEXT, "ma", g)
            if k in tags:
                text(d, (cx, ybase - hgt * g - 90), tags[k], F("sans", 26), C.MUTED, "ma", g)
    source(d, p.s("source"))
    return im


def _axes(d, box, xr, yr, xticks, yticks, xlab, ylab, dimf=1.0, xfmt="{:g}", yfmt="{:g}"):
    x0, yt, x1, yb = box
    X = lambda v: x0 + (v - xr[0]) / (xr[1] - xr[0]) * (x1 - x0)
    Y = lambda v: yb - (v - yr[0]) / (yr[1] - yr[0]) * (yb - yt)
    d.line([(x0, yb), (x1, yb)], fill=mix(C.LINE, 0.6 * dimf), width=2)
    d.line([(x0, yb), (x0, yt - 20)], fill=mix(C.LINE, 0.6 * dimf), width=2)
    for v in xticks:
        text(d, (X(v), yb + 18), xfmt.format(v), F("sans", 24), C.MUTED, "ma", dimf)
    for v in yticks:
        text(d, (x0 - 20, Y(v)), yfmt.format(v), F("sans", 24), C.MUTED, "rm", dimf)
    text(d, (x0 - 20, yt - 70), ylab, F("sans", 24), C.MUTED, "la", dimf)
    text(d, ((x0 + x1) / 2, yb + 62), xlab, F("sans", 24), C.MUTED, "ma", dimf)
    return X, Y


def g_scatter(p, t, dur):
    """Scatter plot. title, x_label, y_label, x_range "a,b", y_range "a,b", x_ticks, y_ticks (comma lists),
    x_fmt (e.g. "{:g}°F"), points ("x|y|style";...) style: hit (accent filled) | miss (outline) ,
    reveal=hit|miss|all (which points animate in), band "x0|x1|label", vline "x|label", note "x|y|text",
    dim=1 (whole chart dimmed), source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    dimf = 0.55 if p.get("dim") else 1.0
    xr = [float(v) for v in str(p.get("x_range", "0,100")).split(",")]
    yr = [float(v) for v in str(p.get("y_range", "0,10")).split(",")]
    xt = [float(v) for v in str(p.get("x_ticks", "")).split(",") if v.strip()]
    yt_ = [float(v) for v in str(p.get("y_ticks", "")).split(",") if v.strip()]
    box = (330, 230, 1650, 720)
    X, Y = _axes(d, box, xr, yr, xt, yt_, p.s("x_label"), p.s("y_label"), dimf, p.get("x_fmt", "{:g}"), p.get("y_fmt", "{:g}"))
    if p.get("title"):
        text(d, (96, 96), p.s("title"), F("sans_medium", 32), C.TEXT, "la", ramp(t, 0.2, 0.6) * dimf)
    band = p.rows("band")
    if band:
        b = band[0]
        a = ramp(t, 0.6, 0.7)
        d.rectangle([max(box[0] + 2, X(float(b[0]))), box[1] - 20, X(float(b[1])), box[3] - 2], fill=mix((60, 30, 26), a * 0.8))
        d.line([(X(float(b[1])), box[1] - 20), (X(float(b[1])), box[3])], fill=mix(C.ACCENT, a), width=3)
        if len(b) > 2:
            text(d, (X(float(b[1])) - 12, box[1]), b[2], F("sans_medium", 26), C.ACCENT, "ra", a)
    seen = {}
    reveal = p.get("reveal", "all")
    for k, r in enumerate(p.rows("points")):
        x, y = float(r[0]), float(r[1])
        style = r[2] if len(r) > 2 else "hit"
        key = (x, y)
        seen[key] = seen.get(key, 0) + 1
        off = (seen[key] - 1) * 16
        a = ramp(t, 0.6 + 0.06 * k, 0.4) if reveal in (style, "all") else 1.0
        cx, cy = X(x), Y(y) - off
        if style == "hit":
            d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=mix(C.ACCENT, a * dimf))
        else:
            d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], outline=mix(C.SECONDARY, a * dimf), width=3)
    for r in p.rows("vline"):
        a = ramp(t, 2.0, 0.8) * dimf
        d.line([(X(float(r[0])), box[1] - 20), (X(float(r[0])), box[3])], fill=mix(C.SECONDARY, a), width=2)
        if len(r) > 1:
            text(d, (X(float(r[0])) + 12, box[1] - 10), r[1], F("sans", 24), C.SECONDARY, "la", a)
    for r in p.rows("note"):
        text(d, (X(float(r[0])), Y(float(r[1]))), r[2], F("sans", 26), C.SECONDARY, "ma", ramp(t, 1.8, 0.6) * dimf)
    source(d, p.s("source"), dimf)
    return im


def g_line(p, t, dur):
    """Line / trajectory. title, x_label, y_label, x_range, y_range, x_ticks, y_ticks, y_fmt,
    points ("x|y";...), marks ("x|y|label|color";...) color: accent|secondary|text, draw=seconds, source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    xr = [float(v) for v in str(p.get("x_range", "0,1")).split(",")]
    yr = [float(v) for v in str(p.get("y_range", "0,1")).split(",")]
    xt = [float(v) for v in str(p.get("x_ticks", "")).split(",") if v.strip()]
    yt_ = [float(v) for v in str(p.get("y_ticks", "")).split(",") if v.strip()]
    box = (240, 200, 1640, 720)
    X, Y = _axes(d, box, xr, yr, xt, yt_, p.s("x_label"), p.s("y_label"), 1.0, p.get("x_fmt", "{:g}"), p.get("y_fmt", "{:g}"))
    if p.get("title"):
        title_line(d, p.s("title"), t)
    pts = [(X(float(r[0])), Y(float(r[1]))) for r in p.rows("points")]
    frac = ease((t - 0.4) / p.f("draw", 2.2))
    m = max(1, int(len(pts) * frac))
    if len(pts) > 1 and frac > 0:
        d.line(pts[:m], fill=mix(C.TEXT, 0.85), width=3, joint="curve")
    for i, r in enumerate(p.rows("marks")):
        col = {"accent": C.ACCENT, "secondary": C.SECONDARY}.get(r[3] if len(r) > 3 else "text", C.TEXT)
        x, y = X(float(r[0])), Y(float(r[1]))
        a = ramp(t, 0.3 + 1.2 * i, 0.5)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=mix(col, a))
        right = x > W * 0.72                       # keep labels near the right edge inside the safe area
        text(d, (x - 16 if right else x + 16, y - 40), r[2], F("sans_medium", 26), col, "ra" if right else "la", a)
    source(d, p.s("source"))
    return im


def g_timeline(p, t, dur):
    """Horizontal timeline. title, start, end (numbers e.g. years as floats), ticks ("1981|1981年";...),
    dots ("pos|hit" ;...) hit dots in accent, events ("pos|label|sub|side|stage";...) side up|up2|down,
    stage = step at which it appears, step, legend, footer (shown at last step), source"""
    step = p.i("step", 99)
    im = canvas()
    d = ImageDraw.Draw(im)
    x0, x1, y = 200, 1720, 520
    a0, a1 = p.f("start"), p.f("end")
    X = lambda v: x0 + (v - a0) / (a1 - a0) * (x1 - x0)
    d.line([(x0, y), (x1, y)], fill=mix(C.LINE, 0.6), width=2)
    for r in p.rows("ticks"):
        d.line([(X(float(r[0])), y - 8), (X(float(r[0])), y + 8)], fill=mix(C.LINE, 0.6), width=2)
        text(d, (X(float(r[0])), y + 24), r[1] if len(r) > 1 else r[0], F("sans", 26), C.MUTED, "ma")
    if p.get("title"):
        text(d, (96, 96), p.s("title"), F("sans_medium", 32), C.TEXT, "la")
    limit = p.f("show_until", 1e9) if step < 99 else 1e9
    for r in p.rows("dots"):
        pos = float(r[0])
        if pos > limit:
            continue
        hit = len(r) > 1 and r[1] in ("hit", "1", "accent")
        col = C.ACCENT if hit else mix(C.LINE, 0.55)
        rr = 9 if hit else 6
        d.ellipse([X(pos) - rr, y - rr, X(pos) + rr, y + rr], fill=col)
    for k, r in enumerate(p.rows("events")):
        pos, label = float(r[0]), r[1]
        sub = r[2] if len(r) > 2 else ""
        side = r[3] if len(r) > 3 else "up"
        stage = int(r[4]) if len(r) > 4 and r[4] else 1
        if stage > step:
            continue
        a = ramp(t, 0.3 + 0.5 * k, 0.6) if stage == step or step == 99 else 1.0
        yy = {"up": y - 200, "up2": y - 300, "down": y + 90}.get(side, y - 200)
        if side.startswith("up"):
            d.line([(X(pos), y - 12), (X(pos), yy + 110)], fill=mix(C.MUTED, a), width=1)
        else:
            d.line([(X(pos), y + 58), (X(pos), yy)], fill=mix(C.MUTED, a), width=1)
        right = X(pos) > 1400
        tx, an = (X(pos) - 10, "ra") if right else (X(pos) + 10, "la")
        text(d, (tx, yy), label, F("sans_medium", 28), C.TEXT, an, a)
        text(d, (tx, yy + 40), sub, F("sans", 26), C.MUTED, an, a)
    if p.get("legend"):
        text(d, (x0, 690), "● " + p.s("legend"), F("sans", 22), C.ACCENT, "la", 1)
    if p.get("footer") and step >= p.i("footer_step", 99 if step == 99 else step):
        text(d, (W / 2, 760), p.s("footer"), fit_font("sans_medium", 32, p.s("footer"), W * 0.84), C.ACCENT, "mm",
             ramp(t, 2.6, 0.8))
    source(d, p.s("source"))
    return im


def g_compare(p, t, dur):
    """Two numbers side by side. title, left_label, left_value, right_label, right_value, right_note,
    grid=100 (draw a 10x10 grid with one accent cell under the left value), source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    if p.get("title"):
        title_line(d, p.s("title"), t)
    text(d, (560, 330), p.s("left_label"), F("sans", 30), C.MUTED, "mm", ramp(t, 0.2, 0.5))
    text(d, (560, 410), p.s("left_value"), F("serif_bold", 72), C.TEXT, "mm", ramp(t, 0.3, 0.6))
    if p.get("grid"):
        a = ramp(t, 0.8, 0.6)
        for i in range(100):
            r, c = divmod(i, 10)
            x, y = 488 + c * 15, 480 + r * 15
            d.rectangle([x, y, x + 11, y + 11], fill=mix(C.ACCENT if i == 99 else C.DIM, a))
    text(d, (1360, 330), p.s("right_label"), F("sans", 30), C.MUTED, "mm", ramp(t, 1.2, 0.5))
    text(d, (1360, 410), p.s("right_value"), F("serif_bold", 72), C.ACCENT, "mm", ramp(t, 1.3, 0.6))
    text(d, (1360, 520), p.s("right_note"), F("serif", 34), C.TEXT, "mm", ramp(t, 2.0, 0.6))
    source(d, p.s("source"))
    return im


def g_gauge(p, t, dur):
    """Vertical gauge / thermometer. min, max, tick (scale step), unit, value, label, sub, ref "value|label",
    color=accent|secondary, source"""
    im = canvas()
    d = ImageDraw.Draw(im)
    lo, hi, unit = p.f("min", -20), p.f("max", 30), p.s("unit")
    x, ytop, ybot = 560, 170, 800
    Y = lambda c: ybot - (c - lo) / (hi - lo) * (ybot - ytop)
    d.line([(x, ytop), (x, ybot)], fill=mix(C.LINE, 0.6), width=3)
    tick = p.f("tick", (hi - lo) / 5)
    v = lo
    while v <= hi + 1e-6:
        d.line([(x - 14, Y(v)), (x + 14, Y(v))], fill=mix(C.LINE, 0.6), width=2)
        text(d, (x - 30, Y(v)), f"{v:g}{unit}", F("sans", 26), C.MUTED, "rm")
        v += tick
    if lo < 0 < hi:
        d.line([(x - 40, Y(0)), (x + 40, Y(0))], fill=mix(C.SECONDARY, 0.8), width=2)
    for r in p.rows("ref"):
        rv = float(r[0])
        d.line([(x - 26, Y(rv)), (x + 26, Y(rv))], fill=C.MUTED, width=3)
        text(d, (x + 50, Y(rv)), r[1] if len(r) > 1 else "", F("sans", 26), C.MUTED, "lm")
    col = C.ACCENT if p.get("color", "secondary") == "accent" else C.SECONDARY
    val = p.f("value")
    start = hi - (hi - lo) * 0.1
    cur = start + (val - start) * ease((t - 0.3) / 1.4)
    d.rectangle([x - 8, Y(cur), x + 8, ybot], fill=mix(col, 0.9))
    d.ellipse([x - 16, Y(cur) - 16, x + 16, Y(cur) + 16], fill=mix(col, ramp(t, 0.3, 0.8)))
    text(d, (1000, 420), p.s("label"), fit_font("serif", 50, p.s("label"), 820), C.TEXT, "lm", ramp(t, 1.2, 0.6))
    text(d, (1000, 500), p.s("sub"), fit_font("sans", 30, p.s("sub"), 820), C.MUTED, "lm", ramp(t, 1.6, 0.6))
    source(d, p.s("source"))
    return im


def g_calendar(p, t, dur):
    """Row of day cells. title, cells (;), top (small label above every cell), marks
    ("idx|label|style|sub|stage";...) style: x (struck out) | box (accent frame) | ring (secondary frame),
    note "text|stage", step, source"""
    step = p.i("step", 99)
    im = canvas()
    d = ImageDraw.Draw(im)
    cells = p.l("cells")
    n = max(1, len(cells))
    bw = min(190, (W - 400) // n)
    x0, y0 = (W - n * bw + 20) / 2, 380
    if p.get("title"):
        text(d, (96, 96), p.s("title"), F("sans_medium", 32), C.TEXT, "la")
    for i, c in enumerate(cells):
        x = x0 + i * bw
        a = 1 if step > 1 else ramp(t, 0.1 + 0.08 * i, 0.4)
        d.rectangle([x, y0, x + bw - 20, y0 + 170], outline=mix(C.LINE, 0.5 * a), width=2)
        text(d, (x + (bw - 20) / 2, y0 + 85), c, F("serif", 64), C.TEXT, "mm", a)
        text(d, (x + (bw - 20) / 2, y0 - 30), p.s("top"), F("sans", 24), C.MUTED, "mm", a)
    for k, r in enumerate(p.rows("marks")):
        idx = int(r[0]) - 1
        style = r[2] if len(r) > 2 else "x"
        stage = int(r[4]) if len(r) > 4 and r[4] else 1
        if stage > step:
            continue
        a = ramp(t, 0.3 + 0.4 * k, 0.4) if stage == step or step == 99 else 1
        x = x0 + idx * bw
        col = {"x": C.MUTED, "box": C.ACCENT, "ring": C.SECONDARY, "xa": C.ACCENT}.get(style, C.MUTED)
        if style in ("x", "xa"):
            d.line([(x + 15, y0 + 15), (x + bw - 35, y0 + 155)], fill=mix(col, a), width=4)
        else:
            d.rectangle([x - 4, y0 - 4, x + bw - 16, y0 + 174], outline=mix(col, a), width=4)
        text(d, (x + (bw - 20) / 2, y0 + 205), r[1] if len(r) > 1 else "", F("sans", 26), col, "ma", a)
        if len(r) > 3 and r[3]:
            text(d, (x + (bw - 20) / 2, y0 + 245), r[3], F("sans", 24), C.MUTED, "ma", a)
    for r in p.rows("note"):
        if (int(r[1]) if len(r) > 1 else 1) <= step:
            text(d, (W / 2, 720), r[0], F("sans_medium", 30), C.TEXT, "mm", ramp(t, 1.8, 0.6))
    source(d, p.s("source"))
    return im


def g_clocks(p, t, dur):
    """One or two analog clocks. clocks ("label|sub|HH:MM";...) - second clock fades in later"""
    im = canvas()
    d = ImageDraw.Draw(im)
    rows = p.rows("clocks")
    n = len(rows)
    for i, r in enumerate(rows):
        cx = W / 2 if n == 1 else (640 if i == 0 else 1280)
        a = ramp(t, 0.2 + 1.2 * i, 0.6)
        hh, mm = [int(x) for x in r[2].split(":")]
        rr, cy = 150, 420
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=mix(C.LINE, a), width=3)
        for k in range(12):
            ang = k / 12 * 2 * math.pi
            d.line([(cx + (rr - 18) * math.sin(ang), cy - (rr - 18) * math.cos(ang)),
                    (cx + rr * math.sin(ang), cy - rr * math.cos(ang))], fill=mix(C.LINE, a), width=3)
        ah, am = ((hh % 12) + mm / 60) / 12 * 2 * math.pi, mm / 60 * 2 * math.pi
        d.line([(cx, cy), (cx + 80 * math.sin(ah), cy - 80 * math.cos(ah))], fill=mix(C.TEXT, a), width=7)
        d.line([(cx, cy), (cx + 120 * math.sin(am), cy - 120 * math.cos(am))], fill=mix(C.TEXT, a), width=4)
        text(d, (cx, cy + rr + 40), r[0], F("sans_medium", 32), C.TEXT, "ma", a)
        text(d, (cx, cy + rr + 90), r[1] if len(r) > 1 else "", F("sans", 28), C.MUTED, "ma", a)
    return im


# ------------------------------------------------------------------ documents
@lru_cache(16)
def _doc_paper(lines, pw=980, ph=700):
    pap = paper(pw, ph)
    d = ImageDraw.Draw(pap)
    m = F("mono", 24)
    for i, s in enumerate(lines):
        d.text((60, 50 + i * 38), s, font=m, fill=C.INK)
    return pap


def g_document(p, t, dur):
    """Typed document on paper (a RECONSTRUCTION - say so in `note`). lines (list or \\N-separated),
    caption, sub (" ／ "-separated lines), quote (accent text on the right), highlight "from-to"
    (1-based line range boxed in accent), angle, dim=1 (paper faded), name/sub2 (big name instead of
    caption), source"""
    lines = p.l("lines") if isinstance(p.get("lines"), list) else p.s("lines").split("\n")
    im = canvas().convert("RGBA")
    pap = _doc_paper(tuple(lines))
    a = 0.35 if p.get("dim") else ramp(t, 0.1, 0.8)
    zoom = 0.9 * (1.0 + 0.04 * t / max(dur, 1))
    pp = pap.resize((int(pap.width * zoom), int(pap.height * zoom)))
    bx = place(im, pp, a, 600, 460, p.f("angle", -1.5))
    d = ImageDraw.Draw(im)
    capx = 1110
    if p.get("highlight"):
        f0, f1 = [int(x) for x in str(p["highlight"]).split("-")]
        top = 460 - zoom * 700 / 2 + zoom * (50 + (f0 - 1) * 38) - 6
        hl = ramp(t, 0.2, 0.8)
        d.rectangle([600 - zoom * 980 / 2 + 40, top, 600 + zoom * 980 / 2 - 40, top + zoom * 38 * (f1 - f0 + 1) + 4],
                    outline=mix(C.ACCENT, hl), width=3)
    if p.get("name"):
        text(d, (capx, 400), p.s("name"), F("serif", 48), C.TEXT, "la", ramp(t, 0.3, 0.7))
        text(d, (capx, 470), p.s("sub2"), F("sans", 30), C.MUTED, "la", ramp(t, 0.8, 0.7))
    else:
        text(d, (capx, 330), p.s("caption"), fit_font("sans_medium", 32, p.s("caption"), W - capx - 100), C.TEXT, "la",
             ramp(t, 0.8, 0.6))
        for i, ln in enumerate(s for s in p.s("sub").split(" ／ ") if s):
            text(d, (capx, 390 + i * 44), ln, fit_font("sans", 26, ln, W - capx - 100), C.MUTED, "la", ramp(t, 1.1, 0.6))
    if p.get("quote"):
        q = p.s("quote")
        text(d, (capx, 520 if not p.get("highlight") else 360), q, fit_font("serif", 34, q, W - capx - 100), C.ACCENT,
             "la", ramp(t, 1.4, 0.6), spacing=14)
    source(d, p.s("source"))
    return im.convert("RGB")


# ------------------------------------------------------------------ maps (Natural Earth, public domain)
@lru_cache(4)
def _layer(name):
    import shapefile
    r = shapefile.Reader(str(config.GEO_DIR / name))
    fields = [f[0] for f in r.fields[1:]]
    out = []
    for sr in r.shapeRecords():
        rec = dict(zip(fields, sr.record))
        pts = sr.shape.points
        parts = list(sr.shape.parts) + [len(pts)]
        out.append((rec, [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]))
    return out


def _region(region):
    """region: world | us48 | ISO3[,ISO3..] (countries) | admin1:ISO3 (states/provinces of a country)"""
    if region == "us48":
        rows = [(r, p) for r, p in _layer("ne_50m_admin_1_states_provinces_lakes")
                if r.get("adm0_a3") == "USA" and r.get("name") not in ("Alaska", "Hawaii")]
        return rows, "name"
    if region.startswith("admin1:"):
        iso = region.split(":", 1)[1]
        return [(r, p) for r, p in _layer("ne_50m_admin_1_states_provinces_lakes") if r.get("adm0_a3") == iso], "name"
    rows = _layer("ne_50m_admin_0_countries")
    if region != "world":
        isos = set(region.split(","))
        rows = [(r, p) for r, p in rows if r.get("ADM0_A3") in isos or r.get("ISO_A3") in isos]
    return rows, "NAME"


@lru_cache(8)
def _map_base(region, bbox, hl, hl_accent):
    rows, key = _region(region)
    if bbox:
        lon0, lat0, lon1, lat1 = bbox
    else:
        xs = [x for _, ps in rows for poly in ps for x, _ in poly]
        ys = [y for _, ps in rows for poly in ps for _, y in poly]
        lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
    k = math.cos(math.radians((lat0 + lat1) / 2))
    box = (140, 150, 1780, 800)
    s = min((box[2] - box[0]) / ((lon1 - lon0) * k), (box[3] - box[1]) / (lat1 - lat0))
    cx, cy = (lon0 + lon1) / 2, (lat0 + lat1) / 2
    proj = (cx, cy, k, s, (box[0] + box[2]) / 2, (box[1] + box[3]) / 2)
    im = canvas()
    d = ImageDraw.Draw(im)
    for rec, polys in rows:
        name = str(rec.get(key, ""))
        fill = None
        if name.lower() in hl:
            fill = mix(C.ACCENT if name.lower() in hl_accent else C.SECONDARY, 0.22)
        for poly in polys:
            xy = [_proj(proj, *pt) for pt in poly]
            if len(xy) > 2:
                d.polygon(xy, fill=fill, outline=mix(C.LINE, 0.35))
    return im, proj


def _proj(pr, lon, lat):
    cx, cy, k, s, ox, oy = pr
    return ox + (lon - cx) * k * s, oy - (lat - cy) * s


def g_map(p, t, dur):
    """Map from Natural Earth. region (world | us48 | JPN,KOR | admin1:JPN), bbox "lon0,lat0,lon1,lat1",
    highlight (names ;), highlight_accent (names ;), points ("key|lon|lat|label|sub|dx|dy";...),
    links ("a-b";...) drawn progressively, link_color=secondary|accent, dim_others=key (fade other points),
    caption (top-left), kicker (small line above caption), source (default: Natural Earth)"""
    hl = tuple(x.lower() for x in p.l("highlight"))
    hla = tuple(x.lower() for x in p.l("highlight_accent"))
    bbox = tuple(float(v) for v in str(p["bbox"]).split(",")) if p.get("bbox") else None
    base, proj = _map_base(p.get("region", "world"), bbox, hl + hla, hla)
    im = base.copy()
    d = ImageDraw.Draw(im)
    pts = {}
    for i, r in enumerate(p.rows("points")):
        key, lon, lat = r[0], float(r[1]), float(r[2])
        x, y = _proj(proj, lon, lat)
        pts[key] = (x, y)
        a = ramp(t, 0.2 + 0.3 * i, 0.5)
        if p.get("dim_others") and key != p.get("dim_others"):
            a *= 0.35
        col = C.ACCENT if p.get("dim_others") == key else C.TEXT
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=mix(col, a))
        dx = float(r[5]) if len(r) > 5 and r[5] else 30
        dy = float(r[6]) if len(r) > 6 and r[6] else -20
        anchor = "ra" if dx < 0 else "la"
        if len(r) > 3:
            text(d, (x + dx, y + dy), r[3], F("sans_medium", 30), col, anchor, a)
        if len(r) > 4 and r[4]:
            text(d, (x + dx, y + dy + 40), r[4], F("sans", 24), C.MUTED, anchor, a)
    lc = C.ACCENT if p.get("link_color") == "accent" else C.SECONDARY
    for i, lk in enumerate(p.l("links")):
        a_, b_ = lk.split("-")
        if a_ in pts and b_ in pts:
            partial_line(d, pts[a_], pts[b_], ease((t - 1.0 - 0.4 * i) / 1.2), mix(lc, 0.85), 3)
    if p.get("kicker"):
        text(d, (96, 60), p.s("kicker"), F("sans", 24), C.MUTED, "la", ramp(t, 0.4, 0.6))
    if p.get("caption"):
        text(d, (96, 96), p.s("caption"), F("sans_medium", 32), C.TEXT, "la", ramp(t, 0.6, 0.6))
    source(d, p.s("source") or (config.load()["labels"]["map"] + "Natural Earth"))
    return im


REG = {k[2:]: v for k, v in globals().items() if k.startswith("g_")}
