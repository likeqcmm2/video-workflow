"""Custom graphics of the reference (Challenger) production - ported 1:1 from the original build.

They show the quality bar for project-specific graphics: mechanism diagrams (g_joint, g_oring, g_srb, g_stack),
data graphics built from a documented dataset (g_incidents, g_chart from Dalal et al. 1989), reconstructed
documents labelled as reconstructions (g_doc, g_memo), and small explanatory cards.
They are this film's design (1986 archive disaster: dark paper, serif, restrained red). New films design their own
graphics for their genre and era; reuse techniques from here, not the look.
"""
import math
import os
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from vf.config import FONTS_DIR, GEO_DIR
from vf.gfx.core import C, H, W, canvas as _canvas, ease, mix as _mix, partial_line, ramp, text, tw  # noqa: F401

# legacy colour names used throughout this file
BG, TXT, MUTED, DIM = C.BG, C.TEXT, C.MUTED, C.DIM
RED, ICE, PAPER, INK, LINE = C.ACCENT, C.SECONDARY, C.PAPER, C.INK, C.LINE


@lru_cache(None)
def F(kind, size):
    path = {"serif": "NotoSerifJP-500.ttf", "serifb": "NotoSerifJP-700.ttf", "sans": "NotoSansJP-400.ttf",
            "sansm": "NotoSansJP-500.ttf", "sansb": "NotoSansJP-700.ttf"}.get(kind)
    if kind == "mono":
        lib = "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"
        return ImageFont.truetype(lib if os.path.exists(lib) else str(FONTS_DIR / "NotoSansMono-400.ttf"), size)
    return ImageFont.truetype(str(FONTS_DIR / path), size)


def mix(c, a, bg=BG):
    return _mix(c, a, bg)


def canvas(bg=BG):
    return _canvas(bg)


def source(d, s, a=1.0):
    text(d, (W - 96, 820), s, F("sans", 22), MUTED, anchor="ra", a=a)


def wrap_lines(s):
    return s.replace("\\N", "\n")


@lru_cache(None)
def photo_bg(name, darkness=0.85):
    p = os.path.join("assets", "nasa", name)
    im = Image.open(p).convert("RGB")
    im = im.resize((W, int(W * im.height / im.width)))
    top = max(0, (im.height - H) // 2)
    im = im.crop((0, top, W, top + H)).filter(ImageFilter.GaussianBlur(6))
    im = Image.blend(im.convert("L").convert("RGB"), Image.new("RGB", (W, H), BG), darkness)
    return im


# ------------------------------------------------------------------ text cards
def g_title(p, t, dur):
    im = photo_bg("S86-38989.jpg", 0.88).copy()
    d = ImageDraw.Draw(im)
    bgc = BG
    a1, a2, a3 = ramp(t, 0.2, 1.0), ramp(t, 1.0, 1.0), ramp(t, 1.8, 1.0)
    text(d, (W / 2, 330), "1 9 8 6 . 1 . 2 8", F("sans", 30), MUTED, "mm", a1, bgc)
    text(d, (W / 2, 450), "チャレンジャー号爆発事故", F("serifb", 104), TXT, "mm", a2, bgc)
    lw = 520 * ease((t - 1.4) / 1.2)
    if lw > 0:
        d.line([(W / 2 - lw, 548), (W / 2 + lw, 548)], fill=mix(RED, 0.9, bgc), width=2)
    text(d, (W / 2, 620), "打ち上げ73秒後の空中分解", F("serif", 44), TXT, "mm", a3, bgc)
    text(d, (W / 2, 690), "前夜「飛ばすな」と警告した技術者たちの声は、なぜ届かなかったのか", F("sans", 32), MUTED, "mm", a3, bgc)
    return im


def g_chapter(p, t, dur):
    im = canvas((8, 10, 13))
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.3, 0.8) * (1 - ramp(t, dur - 0.7, 0.6))
    bgc = (8, 10, 13)
    num, title = p["num"], p["title"]
    text(d, (W / 2, 470), num, F("sansm", 34), RED, "mm", a, bgc)
    text(d, (W / 2, 560), title, F("serif", 76), TXT, "mm", a, bgc)
    lw = 160 * ease((t - 0.5) / 1.0) * (1 - ramp(t, dur - 0.7, 0.6))
    if lw > 1:
        d.line([(W / 2 - lw, 625), (W / 2 + lw, 625)], fill=mix(LINE, 0.6 * a, bgc), width=1)
    return im





def g_quote(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.15, 0.7)
    a2 = ramp(t, 0.7, 0.7)
    body = wrap_lines(p.get("text", ""))
    if p.get("kind") == "name":
        text(d, (W / 2, 470), body, F("serif", 64), TXT, "mm", a)
        text(d, (W / 2, 570), p.get("attr", ""), F("sans", 32), MUTED, "mm", a2)
        return im
    n = body.count("\n") + 1
    size = 58 if n <= 2 else 50
    y = 470 - (n - 1) * (size * 0.75)
    text(d, (W / 2, y), body, F("serif", size), TXT, "mm", a, spacing=int(size * 0.55))
    yb = y + n * size * 0.85 + 60
    text(d, (W / 2, yb), "―― " + p.get("attr", ""), F("sans", 30), MUTED, "mm", a2)
    return im


def g_textcard(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 450), wrap_lines(p.get("text", "")), F("serif", 66), TXT, "mm", ramp(t, 0.15, 0.7))
    text(d, (W / 2, 560), wrap_lines(p.get("sub", "")), F("sans", 34), MUTED, "mm", ramp(t, 0.8, 0.7))
    return im


def g_term(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    kind = p.get("kind", "deviance")
    if kind == "deviance":
        a, b, c = "「逸脱の常態化」", "Normalization of Deviance", "社会学者 ダイアン・ヴォーン『チャレンジャー号打ち上げの決定』（1996年）"
    elif kind == "rooted":
        a, b, c = "「歴史に根ざした事故」", "An Accident Rooted in History", "大統領事故調査委員会報告書　第6章の題"
    else:
        a, b, c = "異常　→　無事に帰還　→　「許容できるリスク」", "", "コロンビア号の断熱材落下も、チャレンジャー号のOリングと同じ道をたどった"
    text(d, (W / 2, 430), a, F("serif", 70 if kind != "deviance2" else 52), TXT, "mm", ramp(t, 0.2, 0.8))
    if b:
        text(d, (W / 2, 525), b, F("serif", 34), ICE, "mm", ramp(t, 0.9, 0.8))
    text(d, (W / 2, 610), c, F("sans", 28), MUTED, "mm", ramp(t, 1.4, 0.8))
    return im


# ------------------------------------------------------------------ map
@lru_cache(None)
def _states():
    import shapefile
    r = shapefile.Reader(str(GEO_DIR / "ne_50m_admin_1_states_provinces_lakes"))
    out = []
    fields = [f[0] for f in r.fields[1:]]
    for sr in r.shapeRecords():
        rec = dict(zip(fields, sr.record))
        if rec.get("admin") != "United States of America" or rec.get("name") in ("Alaska", "Hawaii"):
            continue
        pts = sr.shape.points
        parts = list(sr.shape.parts) + [len(pts)]
        polys = [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]
        out.append((rec.get("name"), polys))
    return out


def _proj(lon, lat):
    # simple equal-area-ish projection for the lower 48, fitted to the frame
    x = (lon + 96.0) * math.cos(math.radians(38)) * 30.5 + 960
    y = (38.5 - lat) * 30.5 + 470
    return x, y


SITES = {
    "utah": (-112.2, 41.6, "ユタ州", "モートン・サイオコール社", (-330, 30)),
    "alabama": (-86.65, 34.65, "アラバマ州", "NASA マーシャル宇宙飛行センター", (40, -95)),
    "florida": (-80.65, 28.55, "フロリダ州", "NASA ケネディ宇宙センター", (40, 40)),
}


@lru_cache(None)
def _map_base(hl):
    im = canvas()
    d = ImageDraw.Draw(im)
    for name, polys in _states():
        key = name.lower()
        fill = None
        if key in hl:
            fill = mix(RED if key == hl[-1] and len(hl) == 1 and hl[0] == "alabama" else ICE, 0.22)
        for poly in polys:
            xy = [_proj(*pt) for pt in poly]
            if len(xy) > 2:
                d.polygon(xy, fill=fill, outline=mix(LINE, 0.35))
    return im


def g_map3(p, t, dur):
    mode = p.get("mode", "connect")
    hl = {"utah": ("utah",), "utah_dark": ("utah",), "alabama": ("alabama",)}.get(mode, ("utah", "alabama", "florida"))
    im = _map_base(hl).copy()
    d = ImageDraw.Draw(im)
    pts = {k: _proj(v[0], v[1]) for k, v in SITES.items()}
    order = ["utah", "alabama", "florida"]
    for i, k in enumerate(order):
        a = ramp(t, 0.2 + 0.3 * i, 0.5)
        if mode in ("utah", "utah_dark") and k != "utah":
            a *= 0.35
        if mode == "alabama" and k != "alabama":
            a *= 0.35
        x, y = pts[k]
        col = RED if (mode == "alabama" and k == "alabama") else TXT
        r = 9
        d.ellipse([x - r, y - r, x + r, y + r], fill=mix(col, a))
        ox, oy = SITES[k][4]
        text(d, (x + ox, y + oy), SITES[k][2], F("sansm", 30), col, "la", a)
        text(d, (x + ox, y + oy + 40), SITES[k][3], F("sans", 24), MUTED, "la", a)
    if mode in ("connect", "connect2", "hook"):
        pairs = [("utah", "alabama"), ("alabama", "florida"), ("utah", "florida")]
        for i, (a_, b_) in enumerate(pairs):
            frac = ease((t - 1.0 - 0.4 * i) / 1.2)
            col = RED if (mode == "hook" and t > 3.0) else ICE
            partial_line(d, pts[a_], pts[b_], frac, mix(col, 0.85), 3)
        cap = {"connect": "3か所を結んだ電話会議", "connect2": "電話会議の再開　―　サイオコール社「打ち上げを推奨」",
               "hook": "1986年1月27日夜　電話会議"}[mode]
        text(d, (96, 96), cap, F("sansm", 32), TXT, "la", ramp(t, 0.6, 0.6))
    if mode == "utah_dark":
        text(d, (96, 96), "サイオコール社、電話会議を中断して社内検討", F("sansm", 32), TXT, "la", ramp(t, 0.4, 0.6))
    source(d, "地図：Natural Earth")
    return im


# ------------------------------------------------------------------ bar chart: flight rate
def g_flightrate(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    x0, y0, x1, ybase = 300, 150, 1620, 760
    scale = 22.0  # px per flight
    years = ["1981", "1982", "1983", "1984", "1985", "1986", "1990"]
    vals = [2, 3, 4, 5, 9, 15, 24]
    bw = 110
    gap = (x1 - x0) / len(years)
    d.line([(x0 - 30, ybase), (x1, ybase)], fill=mix(LINE, 0.6), width=2)
    text(d, (96, 96), "スペースシャトルの年間打ち上げ回数", F("sansm", 34), TXT, "la", ramp(t, 0.1, 0.5))
    for i, (yr, v) in enumerate(zip(years, vals)):
        cx = x0 + gap * (i + 0.5)
        text(d, (cx, ybase + 22), yr + ("年" if i < 6 else "年"), F("sans", 28), MUTED, "ma")
        if i == 6:  # goal
            a = ramp(t, 0.4, 0.8) if step == 1 else 1
            hgt = v * scale
            for yy in range(int(ybase - hgt), ybase, 16):
                d.line([(cx - bw / 2, yy), (cx - bw / 2, yy + 8)], fill=mix(TXT, a * 0.8), width=2)
                d.line([(cx + bw / 2, yy), (cx + bw / 2, yy + 8)], fill=mix(TXT, a * 0.8), width=2)
            d.line([(cx - bw / 2, ybase - hgt), (cx + bw / 2, ybase - hgt)], fill=mix(TXT, a * 0.8), width=2)
            text(d, (cx, ybase - hgt - 60), "24回", F("serif", 40), TXT, "ma", a)
            text(d, (cx, ybase - hgt - 100), "目標", F("sans", 26), MUTED, "ma", a)
            continue
        if i == 5:  # planned 1986
            if step < 3:
                continue
            a = ramp(t, 0.3, 0.8)
            hgt = v * scale
            d.rectangle([cx - bw / 2, ybase - hgt, cx + bw / 2, ybase], outline=mix(RED, a), width=3)
            text(d, (cx, ybase - hgt - 56), "15回", F("serif", 40), RED, "ma", a)
            text(d, (cx, ybase - hgt - 96), "予定", F("sans", 26), MUTED, "ma", a)
            continue
        if step == 1:
            continue
        g = ease((t - 0.2 - 0.25 * i) / 0.8) if step == 2 else 1
        hgt = v * scale * g
        if hgt > 0:
            d.rectangle([cx - bw / 2, ybase - hgt, cx + bw / 2, ybase], fill=mix(ICE, 0.75))
            text(d, (cx, ybase - hgt - 50), f"{v}回", F("serif", 36), TXT, "ma", g)
    source(d, "出典：大統領事故調査委員会報告書 第8章／NASA")
    return im


# ------------------------------------------------------------------ names (Japanese astronauts)
def g_names(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 250), "1985年8月7日　初の日本人宇宙飛行士候補に選ばれた3人", F("sans", 32), MUTED, "mm", ramp(t, 0.1, 0.6) if step == 1 else 1)
    for i, n in enumerate(["毛利 衛", "向井 千秋", "土井 隆雄"]):
        a = ramp(t, 0.5 + 0.4 * i, 0.6) if step == 1 else 1
        text(d, (W / 2 + (i - 1) * 440, 430), n, F("serif", 72), TXT, "mm", a)
    if step >= 2:
        a = ramp(t, 0.3, 0.7)
        text(d, (W / 2, 590), "スペースシャトル搭乗予定：1988年", F("sansm", 40), ICE, "mm", a)
    return im


# ------------------------------------------------------------------ shuttle stack diagram
def _ogive(d, x, top, w, h_nose, bottom, outline, fill=None, width=3):
    left, right = [], []
    for k in range(21):
        u = k / 20
        hw = w / 2 * math.sqrt(u)
        left.append((x - hw, top + h_nose * u))
        right.append((x + hw, top + h_nose * u))
    shape = left[::-1][::-1]
    shape = list(reversed(left)) if False else None
    shape = [(x - w / 2, bottom)] + list(reversed(left)) + right + [(x + w / 2, bottom)]
    d.polygon(shape, outline=outline, fill=fill)
    if width > 1:
        d.line(shape + [shape[0]], fill=outline, width=width)


def g_stack(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    cx, top, bot = 900, 130, 800
    a_et, a_srb, a_orb = ramp(t, 0.2, 0.8), ramp(t, 1.2, 0.8), ramp(t, 2.2, 0.8)
    if a_et > 0:
        _ogive(d, cx, top, 150, 130, bot - 10, mix((196, 120, 70), a_et), fill=mix((90, 55, 35), a_et))
    if a_srb > 0:
        for dx in (-125, 125):
            _ogive(d, cx + dx, top + 90, 66, 70, bot + 20, mix(TXT, a_srb), fill=mix((60, 62, 66), a_srb))
            d.polygon([(cx + dx - 33, bot + 20), (cx + dx + 33, bot + 20), (cx + dx + 45, bot + 60), (cx + dx - 45, bot + 60)],
                      outline=mix(TXT, a_srb), fill=mix((60, 62, 66), a_srb))
    if a_orb > 0:
        col = mix(TXT, a_orb)
        body = [(cx - 40, 330), (cx + 40, 330), (cx + 46, 720), (cx + 270, 760), (cx + 270, 790), (cx - 270, 790), (cx - 270, 760), (cx - 46, 720)]
        d.polygon(body, outline=col, fill=mix((205, 205, 200), a_orb * 0.9))
        d.polygon([(cx - 30, 330), (cx, 270), (cx + 30, 330)], outline=col, fill=mix((40, 40, 44), a_orb))
        d.polygon([(cx - 12, 560), (cx + 12, 560), (cx + 8, 330), (cx - 8, 330)], fill=mix((120, 120, 120), a_orb))
    labels = [(a_orb, (cx + 270, 775), (1300, 700), "オービター", "乗組員が乗る翼のついた機体"),
              (a_et, (cx + 40, 230), (1300, 230), "外部燃料タンク", "液体水素と液体酸素"),
              (a_srb, (cx + 158, 470), (1300, 470), "固体ロケットブースター（2本）", "打ち上げの推力の大部分")]
    for a, (px, py), (lx, ly), s1, s2 in labels:
        if a <= 0:
            continue
        d.line([(px, py), (lx - 20, ly + 20)], fill=mix(MUTED, a), width=2)
        text(d, (lx, ly), s1, F("sansm", 36), TXT, "la", a)
        text(d, (lx, ly + 48), s2, F("sans", 26), MUTED, "la", a)
    text(d, (96, 96), "スペースシャトルの構成（正面から見た模式図）", F("sans", 28), MUTED, "la", ramp(t, 0.1, 0.5))
    return im


def g_srb(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    y, x0, x1 = 430, 280, 1640
    a = ramp(t, 0.1, 0.8)
    # horizontal booster: nose (right), 4 motor segments, aft skirt (left)
    d.polygon([(x0, y - 60), (x0 + 60, y - 50), (x0 + 60, y + 50), (x0, y + 60)], outline=mix(TXT, a), fill=mix((55, 57, 60), a))
    segs = [x0 + 60, 520, 790, 1060, 1330]
    for i in range(4):
        d.rectangle([segs[i], y - 50, segs[i + 1], y + 50], outline=mix(TXT, a), fill=mix((70, 72, 76), a), width=2)
    pts = [(1330, y - 50)] + [(1330 + 310 * (k / 20), y - 50 * (1 - (k / 20) ** 2)) for k in range(21)] + [(1330 + 310 * (k / 20), y + 50 * (1 - (k / 20) ** 2)) for k in range(20, -1, -1)] + [(1330, y + 50)]
    d.polygon(pts, outline=mix(TXT, a), fill=mix((70, 72, 76), a))
    text(d, (W / 2, 250), "固体ロケットブースター（全長 約45m）", F("sansm", 34), TXT, "mm", a)
    joints = [520, 790, 1060]
    for i, jx in enumerate(joints):
        aj = ramp(t, 1.0 + 0.3 * i, 0.5)
        col = RED if jx == 520 else ICE
        d.line([(jx, y - 80), (jx, y + 80)], fill=mix(col, aj), width=4)
    ah = ramp(t, 2.2, 0.6)
    if ah > 0:
        r = 70 + 6 * math.sin(t * 3)
        d.ellipse([520 - r, y - r, 520 + r, y + r], outline=mix(RED, ah), width=3)
        text(d, (520, y + 130), "フィールド・ジョイント（接合部）", F("sansm", 32), RED, "ma", ah)
        text(d, (520, y + 180), "事故の起点：右ブースターの最下部の接合部", F("sans", 26), MUTED, "ma", ah)
    text(d, (790, y + 130), "", F("sans", 26), MUTED, "ma", 0)
    text(d, (300, y - 140), "← 下（ノズル側）", F("sans", 24), MUTED, "la", a)
    text(d, (1640, y - 140), "上（先端）→", F("sans", 24), MUTED, "ra", a)
    return im


# ------------------------------------------------------------------ joint cross-section
def g_joint(p, t, dur):
    mode = p.get("mode", "intro")
    im = canvas()
    d = ImageDraw.Draw(im)
    metal = (128, 132, 138)
    edge = (200, 200, 196)
    gx = 905  # inner face of tang (gap side)
    gap = 4.0
    if mode in ("rotation",):
        gap = 4 + 18 * ease((t - 1.0) / 2.0)
    if mode in ("cold", "leak", "blowby", "blowby_photo", "plug", "reopen"):
        gap = 16
    if mode == "rotation" or mode == "cold":
        pass
    # hot gas region (inside, left)
    hot = mode not in ("oring_only",)
    if hot:
        flick = 0.8 + 0.2 * math.sin(t * 7) * math.sin(t * 3.1)
        for k in range(12):
            c = mix((210, 110, 40), (0.10 + 0.03 * k) * flick)
            d.rectangle([150 + k * 40, 120, 190 + k * 40, 840], fill=c)
    # propellant/insulation strip
    d.rectangle([640, 120, 850, 840], fill=(52, 46, 40))
    # lower segment: clevis (U)  inner leg x 850-gx-gap, outer leg 960-1020, base y 640-700
    inner_r = gx - gap
    d.rectangle([850, 330, inner_r, 700], fill=metal, outline=edge)
    d.rectangle([958, 330, 1020, 700], fill=metal, outline=edge)
    d.rectangle([850, 640, 1020, 840], fill=metal, outline=edge)
    # upper segment with tang
    tang_x0, tang_x1 = gx, 954
    d.rectangle([850, 120, 1020, 300], fill=metal, outline=edge)
    d.rectangle([tang_x0, 300, tang_x1, 630], fill=(150, 154, 160), outline=edge)
    # putty gap between segments (inside) at y 300-330
    d.rectangle([850, 300, inner_r, 330], fill=(95, 85, 70))
    # pin
    d.ellipse([920, 560, 944, 584], fill=(90, 92, 96), outline=edge)
    # O-rings
    ring_col = (30, 30, 32)
    if mode in ("cold", "leak", "plug", "reopen"):
        ring_col = (70, 95, 115)
    rings = [(inner_r - 2, 410), (inner_r - 2, 480)]
    if mode == "redesign":
        rings.append((inner_r - 2, 360))
    seal_shift = 0
    if mode in ("seal", "double"):
        seal_shift = 6 * ease((t - 0.8) / 1.0)
    if mode == "cold":
        seal_shift = 6 * ease((t - 2.5) / 3.0)
    for i, (rx, ry) in enumerate(rings):
        r = 13
        hl = mode in ("orings", "double") or (mode == "redesign" and i == 2)
        oc = ICE if hl else edge
        sx = seal_shift if i == 0 else 0
        d.ellipse([rx - r + sx, ry - r, rx + r + sx, ry + r], fill=ring_col, outline=oc, width=3 if hl else 2)
    # gas path / blow-by drawings
    def arrow(pts, col, w=5):
        d.line(pts, fill=col, width=w, joint="curve")
        (x1, y1), (x2, y2) = pts[-2], pts[-1]
        ang = math.atan2(y2 - y1, x2 - x1)
        for s in (-1, 1):
            d.line([(x2, y2), (x2 - 18 * math.cos(ang + s * 0.5), y2 - 18 * math.sin(ang + s * 0.5))], fill=col, width=w)
    gasc = (235, 140, 50)
    if mode in ("intro", "seal", "double", "rotation"):
        a = ramp(t, 0.6, 0.6)
        arrow([(600, 315), (inner_r + 6, 315), (inner_r + 6, 380)], mix(gasc, a))
    if mode in ("blowby", "blowby_photo", "leak", "reopen"):
        a = ramp(t, 0.4, 0.8)
        frac = ease((t - 0.4) / 1.6)
        path = [(600, 315), (inner_r + 6, 315), (inner_r + 6, 300 + 160 * frac)]
        arrow(path, mix(gasc, a))
        # soot between rings
        sa = ramp(t, 1.6, 0.8)
        d.rectangle([inner_r - 1, 425, gx + 6, 465], fill=mix((15, 12, 10), sa, metal))
    if mode == "leak":
        a = ramp(t, 1.6, 0.8)
        arrow([(inner_r + 8, 470), (inner_r + 8, 640), (1100, 640), (1250, 560)], mix((150, 150, 150), a), 6)
    if mode == "plug":
        a = ramp(t, 0.5, 1.0)
        for k in range(60):
            yy = 330 + (k * 37) % 140
            xx = inner_r + (k * 13) % max(4, int(gap))
            d.ellipse([xx - 3, yy - 3, xx + 3, yy + 3], fill=mix((210, 210, 200), a, (40, 40, 40)))
    if mode == "reopen":
        a = ramp(t, 1.8, 0.8)
        arrow([(inner_r + 8, 470), (inner_r + 8, 640), (1100, 640), (1250, 520)], mix((250, 120, 40), a), 9)
    if mode == "redesign":
        a = ramp(t, 1.0, 0.8)
        d.rectangle([1020, 360, 1060, 640], fill=mix(RED, a * 0.8))
    # labels
    L = []
    if mode == "intro":
        L = [((300, 180), "内側：燃焼ガス（3000℃超）", (235, 140, 50)), ((1080, 180), "外側", MUTED),
             ((1080, 600), "上下の筒をつなぐ接合部（断面の模式図）", TXT)]
    elif mode == "orings":
        L = [((1080, 395), "1本目のOリング（プライマリー）", ICE), ((1080, 465), "2本目のOリング（セカンダリー）", ICE)]
    elif mode == "seal":
        L = [((1080, 395), "圧力でゴムが隙間に押しつけられ", TXT), ((1080, 445), "ガスを封じ込める", TXT)]
    elif mode == "double":
        L = [((1080, 395), "1本目が破られても", TXT), ((1080, 465), "2本目がある　＝　二重の安全装置", ICE)]
    elif mode == "rotation":
        L = [((1080, 395), "点火の圧力で筒が膨らむと", TXT), ((1080, 445), "隙間が閉じず、逆に開く", RED),
             ((1080, 495), "（ジョイント・ローテーション）", MUTED)]
    elif mode in ("blowby", "blowby_photo"):
        L = [((1080, 395), "ガスが1本目を突き抜け", RED), ((1080, 445), "奥に黒いすすが残る（ブローバイ）", TXT)]
        if mode == "blowby_photo":
            L.append(((1080, 520), "1985年1月 STS-51C の接合部（模式図）", MUTED))
    elif mode == "cold":
        L = [((1080, 395), "低温でゴムが硬くなると", ICE), ((1080, 445), "開いた隙間に追いつけない", TXT)]
    elif mode == "leak":
        L = [((1080, 395), "冷えたOリングが隙間をふさげず", ICE), ((1080, 445), "灰色の煙が外へ", TXT)]
    elif mode == "plug":
        L = [((1080, 395), "燃焼で生じた酸化アルミニウムのかすが", TXT), ((1080, 445), "一時的に隙間を詰まらせた", TXT)]
    elif mode == "reopen":
        L = [((1080, 395), "上空の風の乱れで揺さぶられ", TXT), ((1080, 445), "詰まりが外れ、炎が噴き出す", RED)]
    elif mode == "redesign":
        L = [((1080, 330), "3本目のOリングを追加", ICE), ((1080, 395), "接合部を温めるヒーター", RED),
             ((1080, 460), "（再設計後の模式図）", MUTED)]
    for i, ((x, y), s, c) in enumerate(L):
        text(d, (x + 30, y), s, F("sansm", 32), c, "la", ramp(t, 0.5 + 0.35 * i, 0.6))
    text(d, (96, 880 - 820), "", F("sans", 20), MUTED, "la", 0)
    source(d, "模式図（大統領事故調査委員会報告書をもとに作成）")
    return im


def g_oring(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    a = ramp(t, 0.2, 0.8)
    cx, cy, R = 700, 470, 300
    d.ellipse([cx - R, cy - R * 0.32, cx + R, cy + R * 0.32], outline=mix((40, 40, 42), a, BG), width=12)
    d.ellipse([cx - R, cy - R * 0.32, cx + R, cy + R * 0.32], outline=mix(LINE, a * 0.6), width=2)
    aw = ramp(t, 0.9, 0.7)
    d.line([(cx - R, cy + 150), (cx + R, cy + 150)], fill=mix(MUTED, aw), width=2)
    text(d, (cx, cy + 175), "輪の直径　約3.7m", F("sansm", 34), TXT, "ma", aw)
    ai = ramp(t, 1.6, 0.7)
    ix, iy = 1400, 450
    d.ellipse([ix - 90, iy - 90, ix + 90, iy + 90], fill=mix((35, 35, 37), ai), outline=mix(ICE, ai), width=3)
    d.line([(cx + R - 10, cy), (ix - 100, iy)], fill=mix(MUTED, ai * 0.7), width=1)
    text(d, (ix, iy + 120), "断面の太さ　約7mm", F("sansm", 34), TXT, "ma", ai)
    text(d, (ix, iy + 170), "（拡大）", F("sans", 26), MUTED, "ma", ai)
    text(d, (96, 96), "Oリング：断面が丸いゴム製のパッキン", F("sansm", 32), TXT, "la", a)
    return im


# ------------------------------------------------------------------ documents
def _paper(w, h, angle=0.0):
    im = Image.new("RGBA", (w, h), PAPER + (255,))
    noise = (np.random.RandomState(3).rand(h, w) * 16).astype(np.uint8)
    arr = np.array(im)
    arr[..., :3] = np.clip(arr[..., :3].astype(int) - noise[..., None], 0, 255)
    return Image.fromarray(arr)


def _place_paper(im, paper, a, cx, cy, angle):
    pp = paper.rotate(angle, expand=True, resample=Image.BICUBIC)
    alpha = pp.split()[3].point(lambda v: int(v * a))
    shadow = Image.new("RGBA", pp.size, (0, 0, 0, 140))
    im.paste(shadow, (int(cx - pp.width / 2 + 14), int(cy - pp.height / 2 + 16)), alpha.point(lambda v: int(v * 0.6)))
    im.paste(pp, (int(cx - pp.width / 2), int(cy - pp.height / 2)), alpha)


@lru_cache(None)
def _memo_paper(kind):
    pw, ph = 980, 700
    pap = _paper(pw, ph)
    d = ImageDraw.Draw(pap)
    m = F("mono", 24)
    if kind == "memo":
        lines = ["MORTON THIOKOL, INC.", "Wasatch Division", "", "31 July 1985", "", "TO:      R. K. Lund",
                 "         VP, Engineering", "FROM:    R. M. Boisjoly", "         Applied Mechanics",
                 "SUBJECT: SRM O-Ring Erosion/Potential", "         Failure Criticality", "", "  ...",
                 "  The result would be a catastrophe of", "  the highest order - loss of human life.", "  ..."]
    elif kind == "fax":
        lines = ["MTI ASSESSMENT OF TEMPERATURE CONCERN", "ON SRM-25 (51L) LAUNCH", "", "  o CALCULATIONS SHOW THAT SRM-25",
                 "    O-RINGS WILL BE 20 DEG COLDER", "    THAN SRM-15 O-RINGS", "  o TEMPERATURE DATA NOT CONCLUSIVE",
                 "    ON PREDICTING PRIMARY O-RING", "    BLOW-BY", "  ...", "", "  o MTI RECOMMENDS STS-51L LAUNCH",
                 "    PROCEED ON 28 JANUARY 1986", "", "        J. C. KILMINSTER, VICE PRESIDENT", "        SPACE BOOSTER PROGRAMS"]
    elif kind == "marshall":
        lines = ["NASA MARSHALL SPACE FLIGHT CENTER", "", "21 Oct 1977  (L. Ray)", "  ... the present design",
                 "  is unacceptable ...", "", "9 Jan 1978  (J. Q. Miller)", "  ... no valid reason for not",
                 "  designing to accepted standards ...", "", "19 Jan 1979  (J. Q. Miller)",
                 "  ... Thiokol's position ... is", "  completely unacceptable ..."]
    else:  # ride
        lines = ["NASA  INTERNAL", "", "O-RING RESILIENCY vs TEMPERATURE", "", "  TEMP (F)        RESILIENCY",
                 "  ------          ----------", "  ......          ......", "  ......          ......", "  ......          ......",
                 "  ......          ......", "  ......          ......"]
    for i, s in enumerate(lines):
        d.text((60, 50 + i * 38), s, font=m, fill=INK)
    return pap, lines


def g_doc(p, t, dur):
    kind = p.get("kind", "fax")
    im = canvas().convert("RGBA")
    pap, lines = _memo_paper(kind)
    a = ramp(t, 0.1, 0.8)
    zoom = 1.0 + 0.04 * t / max(dur, 1)
    pp = pap.resize((int(pap.width * zoom * 0.9), int(pap.height * zoom * 0.9)))
    _place_paper(im, pp, a, 600, 460, -1.5)
    d = ImageDraw.Draw(im)
    cap = {"fax": ("サイオコール社の打ち上げ推奨文書", "1月27日 午後11時45分ごろ送信　／　文面の一部を再現"),
           "marshall": ("マーシャル宇宙飛行センターの技術者の文書", "1977〜79年　接合部の設計は「受け入れられない」　／　要旨の再現"),
           "ride": ("低温とOリングの弾力を示すNASAの内部資料", "イメージ（実際の数値は省略）")}[kind]
    capx = 1110
    text(d, (capx, 330), cap[0], F("sansm", 32), TXT, "la", ramp(t, 0.8, 0.6))
    for i, line in enumerate(cap[1].split("　／　")):
        text(d, (capx, 390 + i * 44), line, F("sans", 26), MUTED, "la", ramp(t, 1.1, 0.6))
    if kind == "fax":
        text(d, (capx, 520), "「MTIは、STS-51Lの打ち上げを\n1986年1月28日に実施する\nことを推奨する」", F("serif", 32), RED, "la", ramp(t, 1.8, 0.6))
    return im.convert("RGB")


def g_memo(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas().convert("RGBA")
    pap, lines = _memo_paper("memo")
    a = 1.0 if step > 1 else ramp(t, 0.1, 0.8)
    if step == 3:
        a = 0.35
    pp = pap.resize((int(pap.width * 0.9), int(pap.height * 0.9)))
    _place_paper(im, pp, a, 600, 460, 1.2)
    d = ImageDraw.Draw(im)
    if step == 1:
        text(d, (1110, 330), "ボイジョリーのメモ", F("sansm", 36), TXT, "la", ramp(t, 0.8, 0.6))
        text(d, (1110, 390), "1985年7月31日　技術担当副社長あて", F("sans", 28), MUTED, "la", ramp(t, 1.1, 0.6))
        text(d, (1110, 434), "件名：Oリングの侵食と\n潜在的な破損の重大性", F("sans", 28), MUTED, "la", ramp(t, 1.3, 0.6))
    elif step == 2:
        hy = 460 - 0.9 * 700 / 2 + 0.9 * (50 + 13 * 38) - 6
        hl = ramp(t, 0.2, 0.8)
        d.rectangle([600 - 0.9 * 980 / 2 + 40, hy, 600 + 0.9 * 980 / 2 - 40, hy + 0.9 * 80], outline=mix(RED, hl), width=3)
        text(d, (1110, 360), "「接合部が破られれば、", F("serif", 40), TXT, "la", ramp(t, 0.5, 0.7))
        text(d, (1110, 420), "結果は最高レベルの大惨事、", F("serif", 40), TXT, "la", ramp(t, 0.9, 0.7))
        text(d, (1110, 480), "すなわち人命の喪失となるだろう」", F("serif", 40), RED, "la", ramp(t, 1.3, 0.7))
    else:
        text(d, (1110, 400), "ロジャー・ボイジョリー", F("serif", 48), TXT, "la", ramp(t, 0.3, 0.7))
        text(d, (1110, 470), "2012年1月6日死去　73歳", F("sans", 30), MUTED, "la", ramp(t, 0.8, 0.7))
    source(d, "出典：Online Ethics Center／大統領事故調査委員会報告書（文面の一部を再現）")
    return im.convert("RGB")


# ------------------------------------------------------------------ incident timeline
FLIGHTS = [("STS-1", 1981.28, 66, 0), ("STS-2", 1981.87, 70, 1), ("STS-3", 1982.22, 69, 0), ("STS-5", 1982.86, 68, 0),
           ("STS-6", 1983.26, 67, 0), ("STS-7", 1983.46, 72, 0), ("STS-8", 1983.66, 73, 0), ("STS-9", 1983.91, 70, 0),
           ("41-B", 1984.09, 57, 1), ("41-C", 1984.26, 63, 1), ("41-D", 1984.66, 70, 1), ("41-G", 1984.76, 78, 0),
           ("51-A", 1984.86, 67, 0), ("51-C", 1985.07, 53, 2), ("51-D", 1985.28, 67, 0), ("51-B", 1985.33, 75, 0),
           ("51-G", 1985.46, 70, 0), ("51-F", 1985.58, 81, 0), ("51-I", 1985.66, 76, 0), ("51-J", 1985.76, 79, 0),
           ("61-A", 1985.83, 75, 2), ("61-B", 1985.91, 76, 0), ("61-C", 1986.03, 58, 1)]


def g_incidents(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    x0, x1, y = 200, 1720, 520
    X = lambda yr: x0 + (yr - 1981.0) / 5.2 * (x1 - x0)
    d.line([(x0, y), (x1, y)], fill=mix(LINE, 0.6), width=2)
    for yr in range(1981, 1987):
        d.line([(X(yr), y - 8), (X(yr), y + 8)], fill=mix(LINE, 0.6), width=2)
        text(d, (X(yr), y + 24), f"{yr}年", F("sans", 26), MUTED, "ma")
    text(d, (96, 96), "接合部のOリングをめぐる記録（1981〜1986年）", F("sansm", 32), TXT, "la")
    shown = {1: ["STS-2"], 2: ["STS-2"], 3: ["STS-2", "41-B", "41-C", "41-D"], 4: [f[0] for f in FLIGHTS]}[step]
    for i, (nm, yr, temp, dmg) in enumerate(FLIGHTS):
        if step < 4 and yr > {1: 1982.0, 2: 1983.3, 3: 1985.0}[step]:
            continue
        a = 1.0
        if step == 4 and yr > 1985.0:
            a = ramp(t, 0.2 + (yr - 1985.0) * 2.0, 0.4)
        col = RED if dmg else mix(LINE, 0.55)
        r = 9 if dmg else 6
        d.ellipse([X(yr) - r, y - r, X(yr) + r, y + r], fill=mix(col, a))
    notes = [(1981.87, "1981年11月 STS-2", "Oリングの侵食を初めて確認", 1, -1),
             (1982.96, "1982年12月", "「クリティカリティ1」に分類", 2, 1),
             (1983.24, "1983年3月", "特例として飛行を承認", 3, -1),
             (1985.07, "1985年1月 STS-51C", "過去最低の温度でブローバイ", 4, 1),
             (1985.55, "1985年7月", "打ち上げ制約を設定 → 毎回特例で解除", 4, -2)]
    for k, (yr, a1, a2, st, side) in enumerate(notes):
        if st > step:
            continue
        a = ramp(t, 0.3 + (0.6 * k if st == step else 0), 0.6) if st == step else 1.0
        yy = (y - 200 if side == -1 else y - 300) if side < 0 else y + 90
        d.line([(X(yr), y + (-12 if side < 0 else 58)), (X(yr), yy + (110 if side < 0 else 0))], fill=mix(MUTED, a), width=1)
        right = X(yr) > 1400
        tx, an = (X(yr) - 10, "ra") if right else (X(yr) + 10, "la")
        text(d, (tx, yy), a1, F("sansm", 28), TXT, an, a)
        text(d, (tx, yy + 40), a2, F("sans", 26), MUTED if st != 4 or k != 3 else RED, an, a)
    if step == 4:
        a = ramp(t, 2.6, 0.8)
        text(d, (W / 2, 760), "損傷が見つかっても機体は帰還　→　「許容できるリスク」として飛行継続", F("sansm", 32), RED, "mm", a)
    text(d, (x0, 690), "● 接合部のOリングに損傷があった飛行", F("sans", 22), RED, "la", 1)
    source(d, "出典：大統領事故調査委員会報告書 第6章")
    return im


# ------------------------------------------------------------------ temperature card
def g_temp(p, t, dur):
    mode = p.get("mode", "launch")
    im = canvas()
    d = ImageDraw.Draw(im)
    # vertical thermometer scale from -20C to 30C
    x, ytop, ybot = 560, 170, 800
    Y = lambda c: ybot - (c + 20) / 50 * (ybot - ytop)
    d.line([(x, ytop), (x, ybot)], fill=mix(LINE, 0.6), width=3)
    for c in range(-20, 31, 10):
        d.line([(x - 14, Y(c)), (x + 14, Y(c))], fill=mix(LINE, 0.6), width=2)
        text(d, (x - 30, Y(c)), f"{c}℃", F("sans", 26), MUTED, "rm")
    d.line([(x - 40, Y(0)), (x + 40, Y(0))], fill=mix(ICE, 0.8), width=2)
    vals = {"51c": (11.7, "Oリングの温度 約12℃（華氏53度）", "1985年1月24日　STS-51C　それまでの最低", ICE),
            "forecast": (-5.5, "1月28日朝の予報　氷点下5度前後", "（華氏22度前後）", ICE),
            "launch": (2.2, "打ち上げ時の気温　約2℃（華氏36度）", "それまでのどの打ち上げよりも華氏で15度低い", RED)}
    c, s1, s2, col = vals[mode]
    if mode == "launch":
        cc = 11.7
        d.line([(x - 26, Y(cc)), (x + 26, Y(cc))], fill=mix(MUTED, 1), width=3)
        text(d, (x + 50, Y(cc)), "これまでの最低（STS-51C）", F("sans", 26), MUTED, "lm")
    a = ramp(t, 0.3, 0.8)
    cur = 25 + (c - 25) * ease((t - 0.3) / 1.4)
    d.rectangle([x - 8, Y(cur), x + 8, ybot], fill=mix(col, 0.9))
    d.ellipse([x - 16, Y(cur) - 16, x + 16, Y(cur) + 16], fill=mix(col, a))
    text(d, (1000, 420), s1, F("serif", 50), TXT, "lm", ramp(t, 1.2, 0.6))
    text(d, (1000, 500), s2, F("sans", 30), MUTED, "lm", ramp(t, 1.6, 0.6))
    source(d, "出典：大統領事故調査委員会報告書")
    return im


# ------------------------------------------------------------------ calendar of delays
def g_calendar(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    days = list(range(22, 29))
    x0, y0, bw = 300, 380, 190
    text(d, (96, 96), "1986年1月　打ち上げ日程", F("sansm", 32), TXT, "la")
    for i, dd in enumerate(days):
        x = x0 + i * bw
        a = 1 if step > 1 else ramp(t, 0.1 + 0.08 * i, 0.4)
        col = TXT
        d.rectangle([x, y0, x + bw - 20, y0 + 170], outline=mix(LINE, 0.5 * a), width=2)
        text(d, (x + (bw - 20) / 2, y0 + 85), f"{dd}", F("serif", 64), col, "mm", a)
        text(d, (x + (bw - 20) / 2, y0 - 30), "1月", F("sans", 24), MUTED, "mm", a)
    def mark(i, label, col, a):
        x = x0 + i * bw
        d.line([(x + 15, y0 + 15), (x + bw - 35, y0 + 155)], fill=mix(col, a), width=4)
        text(d, (x + (bw - 20) / 2, y0 + 205), label, F("sans", 26), col, "ma", a)
    if step == 1:
        a = ramp(t, 1.0, 0.6)
        d.rectangle([x0 - 4, y0 - 4, x0 + bw - 16, y0 + 174], outline=mix(ICE, a), width=4)
        text(d, (x0 + (bw - 20) / 2, y0 + 205), "当初の予定", F("sans", 26), ICE, "ma", a)
    if step >= 2:
        for k, i in enumerate([0, 1, 3, 4]):
            a = ramp(t, 0.3 + 0.4 * k, 0.4) if step == 2 else 1
            mark(i, "延期", MUTED, a)
        text(d, (W / 2, 720), "前のミッションの遅れ・天候不良で3度の延期", F("sansm", 30), TXT, "mm", ramp(t, 1.8, 0.6) if step == 2 else 1)
    if step >= 3:
        a = ramp(t, 0.3, 0.5)
        mark(5, "中止", RED, a)
        text(d, (x0 + 5 * bw + (bw - 20) / 2, y0 + 245), "ハッチ・横風", F("sans", 24), MUTED, "ma", a)
        a2 = ramp(t, 1.4, 0.5)
        x = x0 + 6 * bw
        d.rectangle([x - 4, y0 - 4, x + bw - 16, y0 + 174], outline=mix(RED, a2), width=4)
        text(d, (x + (bw - 20) / 2, y0 + 205), "打ち上げ", F("sansm", 26), RED, "ma", a2)
    source(d, "出典：大統領事故調査委員会報告書 第2章")
    return im


# ------------------------------------------------------------------ temperature vs O-ring distress chart
def g_chart(p, t, dur):
    mode = p.get("mode", "distress")
    im = canvas()
    d = ImageDraw.Draw(im)
    x0, x1, yb, yt = 330, 1650, 720, 230
    X = lambda f: x0 + (f - 25) / 60 * (x1 - x0)
    Y = lambda n: yb - n / 3 * (yb - yt)
    dimf = 0.55 if mode == "all_dim" else 1.0
    d.line([(x0, yb), (x1, yb)], fill=mix(LINE, 0.6 * dimf), width=2)
    d.line([(x0, yb), (x0, yt - 20)], fill=mix(LINE, 0.6 * dimf), width=2)
    for f in range(30, 86, 10):
        text(d, (X(f), yb + 18), f"{f}°F", F("sans", 24), MUTED, "ma", dimf)
    for n in range(0, 4):
        text(d, (x0 - 20, Y(n)), str(n), F("sans", 24), MUTED, "rm", dimf)
    text(d, (x0 - 20, yt - 70), "損傷があった接合部の数", F("sans", 24), MUTED, "la", dimf)
    text(d, ((x0 + x1) / 2, yb + 62), "接合部の温度（華氏）", F("sans", 24), MUTED, "ma", dimf)
    title = {"distress": "前夜に検討されたのは「損傷があった7回」の飛行だけだった",
             "line53": "サイオコール社の結論：華氏53度（約12℃）未満では打ち上げを推奨しない",
             "distress_only": "この7回だけを見ると、温度との関係ははっきりしない",
             "all": "損傷がなかった16回を加えると　――　低温ほど損傷が起きていた",
             "all_dim": ""}[mode]
    text(d, (96, 96), title, F("sansm", 32), TXT if mode != "all" else TXT, "la", ramp(t, 0.2, 0.6) * dimf)
    fl = [f for f in FLIGHTS if f[0] != "STS-1" or True]
    # jitter for overlapping points
    seen = {}
    for k, (nm, yr, temp, dmg) in enumerate(FLIGHTS):
        if dmg == 0 and mode not in ("all", "all_dim"):
            continue
        key = (temp, dmg)
        seen[key] = seen.get(key, 0) + 1
        off = (seen[key] - 1) * 16
        a = 1.0
        if dmg == 0 and mode == "all":
            a = ramp(t, 0.8 + 0.06 * k, 0.4)
        if dmg > 0 and mode == "distress":
            a = ramp(t, 0.6 + 0.12 * k, 0.4)
        cx, cy = X(temp), Y(dmg) - off
        col = RED if dmg else ICE
        if dmg:
            d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=mix(col, a * dimf))
        else:
            d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], outline=mix(col, a * dimf), width=3)
    if mode in ("line53",):
        a = ramp(t, 0.6, 0.7)
        d.rectangle([x0 + 2, yt - 20, X(53), yb - 2], fill=mix((60, 30, 26), a * 0.8))
        d.line([(X(53), yt - 20), (X(53), yb)], fill=mix(RED, a), width=3)
        text(d, (X(53) - 12, yt), "華氏53度", F("sansm", 26), RED, "ra", a)
        # re-draw points on top
        for nm, yr, temp, dmg in FLIGHTS:
            if dmg:
                d.ellipse([X(temp) - 11, Y(dmg) - 11, X(temp) + 11, Y(dmg) + 11], fill=RED)
    if mode in ("all", "all_dim"):
        a = ramp(t, 2.6, 0.8) * dimf
        d.line([(X(36), yt - 20), (X(36), yb)], fill=mix(ICE, a), width=2)
        text(d, (X(36) + 12, yt - 10), "1986年1月28日\n打ち上げ時の気温 華氏36度", F("sans", 24), ICE, "la", a)
        if mode == "all":
            text(d, (X(73), Y(0) - 70), "損傷なし：すべて華氏66度以上", F("sans", 26), ICE, "ma", ramp(t, 1.8, 0.6))
    source(d, "出典：大統領事故調査委員会報告書／Dalal ほか（1989）のデータより作成", dimf)
    return im


# ------------------------------------------------------------------ small text diagrams
def g_proof(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    a1 = ramp(t, 0.2, 0.7) if step == 1 else 0.45
    text(d, (W / 2, 380), "通常の安全審査", F("sans", 30), MUTED, "mm", a1)
    text(d, (W / 2, 450), "「安全であること」を証明できなければ　→　打ち上げ中止", F("serif", 46), TXT, "mm", a1)
    if step == 2:
        a2 = ramp(t, 0.3, 0.7)
        text(d, (W / 2, 590), "1月27日の夜", F("sans", 30), RED, "mm", a2)
        text(d, (W / 2, 660), "「危険であること」を証明できなければ　→　打ち上げ", F("serif", 46), RED, "mm", a2)
    return im


def g_vote(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    names = [("ジェラルド・メイソン", "上級副社長"), ("カルビン・ウィギンズ", "副社長"),
             ("ジョー・キルミンスター", "副社長"), ("ボブ・ランド", "技術担当副社長")]
    text(d, (W / 2, 160), "サイオコール社　最終判断に加わった4人の幹部", F("sansm", 32), TXT, "mm", ramp(t, 0.1, 0.6) if step == 1 else 1)
    for i, (n, r) in enumerate(names):
        x = 180 + i * 400
        a = ramp(t, 0.4 + 0.25 * i, 0.5) if step == 1 else 1
        d.rectangle([x, 270, x + 370, 430], outline=mix(LINE, 0.6 * a), width=2)
        text(d, (x + 185, 330), n, F("serif", 30), TXT, "mm", a)
        text(d, (x + 185, 385), r, F("sans", 24), MUTED, "mm", a)
    a = ramp(t, 1.6, 0.6) if step == 1 else 1
    text(d, (W / 2, 560), "技術者たち（ボイジョリー、トンプソンほか）は投票から外された", F("sans", 30), MUTED, "mm", a)
    if step == 2:
        a = ramp(t, 0.2, 0.6)
        text(d, (W / 2, 700), "結論：打ち上げに賛成", F("serifb", 54), RED, "mm", a)
    source(d, "出典：大統領事故調査委員会報告書 第5章")
    return im


def g_reasons(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (96, 96), "アラン・マクドナルドが挙げた延期の理由", F("sansm", 32), TXT, "la")
    items = ["①　記録的な寒さとOリング", "②　発射台の氷", "③　ブースターを回収する海域の荒天"]
    for i, s in enumerate(items):
        text(d, (360, 300 + i * 110), s, F("serif", 50), TXT, "la", ramp(t, 0.4 + 0.6 * i, 0.6))
    text(d, (360, 680), "→　「参考として伝えておく」", F("serif", 44), RED, "la", ramp(t, 2.8, 0.6))
    source(d, "出典：大統領事故調査委員会報告書 第5章")
    return im


def g_levels(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    rows = [("レベルⅠ", "NASA本部　打ち上げの最終判断"), ("レベルⅡ", "シャトル計画の管理部門"),
            ("レベルⅢ", "マーシャル宇宙飛行センター（ブースター計画）"), ("レベルⅣ", "サイオコール社（製造元）")]
    text(d, (96, 96), "NASAの打ち上げ審査の階層", F("sansm", 32), TXT, "la")
    for i, (lv, s) in enumerate(rows):
        y = 200 + i * 150
        a = ramp(t, 0.2 + 0.25 * (3 - i), 0.5)
        d.rectangle([440, y, 1480, y + 100], outline=mix(LINE, 0.6 * a), width=2)
        text(d, (480, y + 50), lv, F("sansm", 32), ICE, "lm", a)
        text(d, (640, y + 50), s, F("sans", 32), TXT, "lm", a)
    for i in range(3):
        y = 200 + i * 150 + 100
        a = ramp(t, 1.4, 0.5)
        col = RED if i == 1 else LINE
        if i == 1:
            d.line([(960, y + 4), (960, y + 46)], fill=mix(col, a), width=3)
            text(d, (990, y + 25), "×　ここから上には伝わらず", F("sansm", 30), RED, "lm", ramp(t, 2.0, 0.5))
        else:
            d.line([(960, y + 4), (960, y + 46)], fill=mix(col, 0.5 * a), width=3)
    source(d, "出典：大統領事故調査委員会報告書 第5章")
    return im


def g_clock(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    def clock(cx, cy, hh, mm, label1, label2, a):
        r = 150
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=mix(LINE, a), width=3)
        for k in range(12):
            ang = k / 12 * 2 * math.pi
            d.line([(cx + (r - 18) * math.sin(ang), cy - (r - 18) * math.cos(ang)), (cx + r * math.sin(ang), cy - r * math.cos(ang))], fill=mix(LINE, a), width=3)
        ah = ((hh % 12) + mm / 60) / 12 * 2 * math.pi
        am = mm / 60 * 2 * math.pi
        d.line([(cx, cy), (cx + 80 * math.sin(ah), cy - 80 * math.cos(ah))], fill=mix(TXT, a), width=7)
        d.line([(cx, cy), (cx + 120 * math.sin(am), cy - 120 * math.cos(am))], fill=mix(TXT, a), width=4)
        text(d, (cx, cy + r + 40), label1, F("sansm", 32), TXT, "ma", a)
        text(d, (cx, cy + r + 90), label2, F("sans", 28), MUTED, "ma", a)
    clock(640, 420, 11, 38, "フロリダ", "1月28日　午前11時38分", ramp(t, 0.2, 0.6))
    clock(1280, 420, 1, 38, "日本", "1月29日　午前1時38分", ramp(t, 0.9, 0.6))
    return im


def g_trajectory(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    x0, x1, yb, yt = 300, 1600, 760, 200
    X = lambda s: x0 + s / 260 * (x1 - x0)
    Y = lambda km: yb - km / 22 * (yb - yt)
    d.line([(x0, yb), (x1, yb)], fill=mix(LINE, 0.6), width=2)
    d.line([(x0, yb), (x0, yt)], fill=mix(LINE, 0.6), width=2)
    for km in (0, 5, 10, 15, 20):
        text(d, (x0 - 16, Y(km)), f"{km}km", F("sans", 24), MUTED, "rm")
    text(d, ((x0 + x1) / 2, yb + 30), "打ち上げからの時間", F("sans", 24), MUTED, "ma")
    pts = []
    for k in range(0, 101):
        s = 73 + k / 100 * 165  # 73s -> 238s
        if s <= 98:
            km = 14 + (19.8 - 14) * math.sin((s - 73) / 25 * math.pi / 2)
        else:
            u = (s - 98) / 140
            km = 19.8 * (1 - u ** 1.6)
        pts.append((X(s), Y(max(km, 0))))
    n = int(len(pts) * ease((t - 0.6) / 3.0))
    if n > 1:
        d.line(pts[:n], fill=mix(ICE, 0.9), width=4)
    a = ramp(t, 0.3, 0.6)
    d.ellipse([X(73) - 9, Y(14) - 9, X(73) + 9, Y(14) + 9], fill=mix(RED, a))
    text(d, (X(73) - 20, Y(14) + 20), "73秒　分解（約14km）", F("sans", 26), RED, "ra", a)
    a2 = ramp(t, 1.6, 0.6)
    text(d, (X(98), Y(19.8) - 50), "約20kmまで上昇", F("sans", 26), TXT, "ma", a2)
    a3 = ramp(t, 3.4, 0.6)
    text(d, (X(238), Y(0) - 60), "約2分45秒後　海面へ", F("sansm", 28), TXT, "ra", a3)
    source(d, "出典：NASA（1986年7月28日 カーウィン報告）")
    return im


def g_icewater(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    gx, gy = 760, 560
    # glass
    a = 1 if step > 1 else ramp(t, 0.2, 0.7)
    d.polygon([(gx - 150, gy - 260), (gx + 150, gy - 260), (gx + 120, gy + 160), (gx - 120, gy + 160)], outline=mix(LINE, a), fill=None)
    d.line([(gx - 150, gy - 260), (gx - 120, gy + 160), (gx + 120, gy + 160), (gx + 150, gy - 260)], fill=mix(LINE, a), width=3)
    d.polygon([(gx - 140, gy - 160), (gx + 140, gy - 160), (gx + 120, gy + 156), (gx - 120, gy + 156)], fill=mix((60, 85, 105), a))
    for k, (ix, iy) in enumerate([(-80, -150), (20, -140), (70, -90), (-40, -60)]):
        d.rectangle([gx + ix - 30, gy + iy - 30, gx + ix + 30, gy + iy + 30], outline=mix(ICE, a), fill=mix((150, 180, 200), a * 0.6))
    # clamp + rubber
    if step == 1:
        cy = gy - 420
    elif step == 2:
        cy = gy - 420 + 360 * ease((t - 0.6) / 1.6)
    else:
        cy = gy - 420
    cx = gx + 330 if step == 3 else gx
    rubber_h = 18 if step >= 2 else 40
    if step == 3:
        rubber_h = 18
    ca = 1 if step >= 2 else ramp(t, 1.0, 0.6)
    d.rectangle([cx - 60, cy - rubber_h / 2, cx + 60, cy + rubber_h / 2], fill=mix((25, 25, 27), ca), outline=mix(LINE, ca))
    if step == 2 or (step == 3 and t < 0.8):
        # C-clamp
        d.line([(cx - 30, cy - 90), (cx - 30, cy - rubber_h / 2), ], fill=mix((170, 170, 170), ca), width=8)
        d.line([(cx - 30, cy - 90), (cx + 90, cy - 90), (cx + 90, cy + 90), (cx - 30, cy + 90), (cx - 30, cy + rubber_h / 2)], fill=mix((170, 170, 170), ca), width=8)
    if step == 3:
        a3 = ramp(t, 1.0, 0.6)
        for k in range(0, 120, 12):
            d.line([(cx - 60 + k, cy - 20), (cx - 54 + k, cy - 20)], fill=mix(MUTED, a3), width=2)
            d.line([(cx - 60 + k, cy + 20), (cx - 54 + k, cy + 20)], fill=mix(MUTED, a3), width=2)
        text(d, (cx + 100, cy - 30), "潰れたまま戻らない", F("sansm", 32), RED, "la", a3)
        text(d, (cx + 100, cy + 20), "（点線は本来の形）", F("sans", 24), MUTED, "la", a3)
    cap = {1: "公聴会で用意された氷水（0℃前後）", 2: "Oリングの素材を締め具で挟み、氷水へ", 3: "取り出して締め具を外すと…"}[step]
    text(d, (96, 96), cap, F("sansm", 32), TXT, "la", ramp(t, 0.2, 0.6))
    text(d, (96, 140), "1986年2月　ファインマンの実験（再現イラスト）", F("sans", 24), MUTED, "la", ramp(t, 0.2, 0.6))
    return im


def g_recs(p, t, dur):
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (96, 96), "委員会の9項目の勧告", F("sansm", 32), TXT, "la")
    items = ["Ⅰ　固体ロケットブースターの設計見直し", "Ⅱ　シャトル計画の管理体制の見直し", "Ⅲ　重要部品の再審査と危険の分析",
             "Ⅳ　独立した安全監督部門の設置", "Ⅴ　情報伝達の改善", "Ⅵ　着陸の安全性向上",
             "Ⅶ　打ち上げ中止と乗員脱出の手段", "Ⅷ　資源に見合った飛行回数", "Ⅸ　整備の安全確保"]
    for i, s in enumerate(items):
        col = 0 if i < 5 else 1
        x = 200 + col * 820
        y = 220 + (i if i < 5 else i - 5) * 105
        hl = i in (0, 3)
        text(d, (x, y), s, F("serif", 38), RED if hl else TXT, "la", ramp(t, 0.3 + 0.18 * i, 0.5))
    source(d, "出典：大統領事故調査委員会報告書　勧告")
    return im


def g_prob(p, t, dur):
    step = int(p.get("step", 1))
    im = canvas()
    d = ImageDraw.Draw(im)
    text(d, (96, 96), "シャトルが失われる確率の見積もり（ファインマンの所見より）", F("sansm", 32), TXT, "la")
    a1 = 1 if step > 1 else ramp(t, 0.3, 0.6)
    text(d, (520, 330), "現場の技術者", F("sans", 34), MUTED, "mm", a1)
    text(d, (520, 450), "約 1/100", F("serifb", 92), TXT, "mm", a1)
    # grid 10x10
    for k in range(100):
        gx, gy = 370 + (k % 10) * 30, 540 + (k // 10) * 30
        col = RED if k == 99 else (60, 64, 70)
        d.rectangle([gx, gy, gx + 22, gy + 22], fill=mix(col, a1))
    if step >= 2:
        a2 = 1 if step > 2 else ramp(t, 0.3, 0.6)
        text(d, (1400, 330), "管理職", F("sans", 34), MUTED, "mm", a2)
        text(d, (1400, 450), "1/100,000", F("serifb", 92), RED, "mm", a2)
    if step >= 3:
        a3 = ramp(t, 0.4, 0.7)
        text(d, (1400, 600), "毎日1回打ち上げても", F("sans", 32), TXT, "mm", a3)
        text(d, (1400, 660), "事故は約300年に1度", F("serif", 46), TXT, "mm", a3)
    source(d, "出典：大統領事故調査委員会報告書 付録F（R. P. ファインマン）")
    return im
