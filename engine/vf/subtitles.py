"""Subtitle segmentation + ASS styles.

Line breaks only happen at phrase boundaries:
  - ja / zh / zh-hant / th : BudouX phrase segmentation (never splits a word: no "か|らな", "アメリカ|人")
  - other languages       : word boundaries
Among the allowed boundaries the break that best balances the two lines wins, with a bonus after
commas and a penalty inside quotes. Each subtitle event is at most two lines.
"""
import re
from functools import lru_cache

from . import config

PARTICLE_END = set("のはがをにでとへもやかね")
NO_LINE_START = set("、。，．・：；？！ー）」』】〕…ぁぃぅぇぉっゃゅょゎァィゥェォッャュョヮヵヶ々")


@lru_cache(None)
def _parser(lang):
    import budoux
    if lang == "ja":
        return budoux.load_default_japanese_parser()
    if lang == "zh":
        return budoux.load_default_simplified_chinese_parser()
    if lang == "zh-hant":
        return budoux.load_default_traditional_chinese_parser()
    if lang == "th":
        return budoux.load_default_thai_parser()
    return None


GLUE_AFTER_TO = ("して", "いう", "いった", "いわれ", "なる", "なっ", "なり", "いえ")
SUFFIX_UNITS = "市町村県州区郡島線号人系"


def _glue(prev, ph):
    """Phrase pairs BudouX sometimes splits but a subtitle line must keep together."""
    if prev.endswith("と") and ph.startswith(GLUE_AFTER_TO):
        return True
    if prev[-1] in "かヶヵケ" and ph.startswith("月"):          # 8か月
        return True
    if ph[0] in SUFFIX_UNITS and re.match(r"[ぁ-ゖァ-ヶー一-龯A-Za-z0-9]", prev[-1]) and len(ph) <= 3:
        return True
    return False


def phrases(text, lang=None):
    lang = lang or config.load()["language"]
    p = _parser(lang) if lang in ("ja", "zh", "zh-hant", "th") else None
    if p:
        out = p.parse(text)
        # glue phrases that would start a line with a forbidden character
        merged = []
        for ph in out:
            if merged and (ph[0] in NO_LINE_START or _glue(merged[-1], ph)):
                merged[-1] += ph
            else:
                merged.append(ph)
        return merged
    return re.findall(r"\S+\s*", text)


def _cost(a, b, maxc, slack):
    la, lb = len(a.strip()), len(b.strip())
    if la > maxc + slack or lb > maxc + slack:
        return None
    c = abs(la - lb) * 0.5
    if a.rstrip()[-1:] in "、，,;；:：":
        c -= 12            # a comma is the natural break (accepted look of the reference film) ...
    elif a.rstrip()[-1:] in PARTICLE_END:
        c -= 6             # ... then the end of a particle phrase
    if min(la, lb) < 0.25 * (la + lb):
        c += 8             # never a stub line like 「今回は、」
    if a.count("「") > a.count("」") or a.count("“") > a.count("”") or a.count('"') % 2:
        c += 20            # never break inside a quotation
    if a.rstrip()[-1:] in "「『“(（":
        c += 30
    return c


def wrap(text, maxc, slack, lang=None):
    """Split text into lines (list) at phrase boundaries, each <= maxc (+slack)."""
    t = text.strip()
    if len(t) <= maxc:
        return [t]
    ph = phrases(t, lang)
    best, bc = None, None
    for i in range(1, len(ph)):
        a, b = "".join(ph[:i]), "".join(ph[i:])
        c = _cost(a, b, maxc, slack)
        if c is not None and (bc is None or c < bc):
            best, bc = i, c
    if best is None:   # no 2-line solution: greedy fill, then recurse
        lines, cur = [], ""
        for p in ph:
            if cur and len((cur + p).strip()) > maxc:
                lines.append(cur.strip())
                cur = p
            else:
                cur += p
        lines.append(cur.strip())
        # hard-split any single phrase longer than the line
        out = []
        for ln in lines:
            while len(ln) > maxc + slack:
                out.append(ln[:maxc])
                ln = ln[maxc:]
            out.append(ln)
        return out
    return ["".join(ph[:best]).strip(), "".join(ph[best:]).strip()]


def events(sentence, lang=None):
    """Split one sentence into subtitle events, each 1-2 lines joined with \\N."""
    st = config.load()["design"]["subtitle"]
    maxc, slack = st["max_chars"], st["slack"]
    s = sentence.strip()
    if len(s) <= 2 * maxc:            # longer sentences become several events (dense 2x28 lines read badly)
        lines = wrap(s, maxc, slack, lang)
        if len(lines) <= 2:
            return ["\\N".join(lines)]
    # long sentence: cut into pieces at commas (or phrases) that fit two lines each
    pieces = re.findall(r"[^、，,]*[、，,]\s*|[^、，,]+$", s)
    chunks, cur = [], ""
    limit = 2 * maxc - 4
    for p in pieces:
        if cur and len(cur + p) > limit:
            chunks.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        chunks.append(cur)
    out = []
    for c in chunks:
        ls = wrap(c, maxc, slack, lang)
        while len(ls) > 2:
            out.append("\\N".join(ls[:2]))
            ls = ls[2:]
        out.append("\\N".join(ls))
    return out


def _ass_color(hexrgb, opacity=1.0):
    h = str(hexrgb).lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    alpha = max(0, min(255, round((1 - float(opacity)) * 255)))
    return f"&H{alpha:02X}{b}{g}{r}".upper()


_ALIGN = {"top-left": 7, "top-right": 9, "bottom-left": 1, "bottom-right": 3, "left": 1, "right": 3}


def corner_margin_v(position):
    """Vertical margin for a corner layer: the safe margin at the top, just above the subtitle block at the bottom."""
    W, H, _ = config.size()
    my = int(H * config.load()["design"]["safe_margin"])
    return my if position.startswith("top") else int(H - config.subtitle_zone_top() + 12)


def ass_header():
    cfg = config.load()
    W, H, _ = config.size()
    d = cfg["design"]
    s, cr, stp, lt = d["subtitle"], d["credit"], d["stamp"], d["lower_third"]
    mx = int(W * d["safe_margin"])
    oc = lambda c: _ass_color(c)      # noqa: E731
    sub_out = oc(s.get("outline_colour") or "#101010")
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,{s['font']},{s['size']},{_ass_color(s['colour'])},&H000000FF,{sub_out},{_ass_color('#000000', s['shadow_opacity'])},0,0,0,0,100,100,{s['spacing']},0,1,{s['outline']},{s['shadow']},2,{mx + 64},{mx + 64},{s['margin_v']},1
Style: Credit,{cr['font']},{cr['size']},{_ass_color(cr['colour'], cr['opacity'])},&H000000FF,{sub_out},&H00000000,0,0,0,0,100,100,0,0,1,{cr['outline']},0,{_ALIGN[cr['position']]},{mx},{mx},{corner_margin_v(cr['position'])},1
Style: Stamp,{stp['font']},{stp['size']},{_ass_color(stp['colour'], stp['opacity'])},&H000000FF,{sub_out},&H00000000,0,0,0,0,100,100,{stp['spacing']},0,1,{stp['outline']},0,{_ALIGN[stp['position']]},{mx},{mx},{corner_margin_v(stp['position'])},1
Style: LTName,{lt['name_font']},{lt['name_size']},{_ass_color(lt['name_colour'])},&H000000FF,{sub_out},&H00000000,0,0,0,0,100,100,1,0,1,2,0,{_ALIGN[lt['position']]},{mx + 14},{mx + 14},{int(H * 0.215)},1
Style: LTRole,{lt['role_font']},{lt['role_size']},{_ass_color(lt['role_colour'], lt['role_opacity'])},&H000000FF,{sub_out},&H00000000,0,0,0,0,100,100,0,0,1,1.6,0,{_ALIGN[lt['position']]},{mx + 16},{mx + 16},{int(H * 0.178)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_time(x):
    x = max(0.0, x)
    cs = int(round(x * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def esc(t):
    return t.replace("{", "｛").replace("}", "｝")
