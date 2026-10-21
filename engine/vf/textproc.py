"""Narration text: display text (digits allowed, shown in subtitles) -> TTS text (numbers as words).

The script keeps numbers as digits ("1986年1月28日"), subtitles show those digits, and the TTS text
spells them out so the voice never has to guess. Fixed readings (acronyms, names the voice
gets wrong) come from project.yaml  voice.readings  and are applied first.
"""
import re

from . import config

DIG = "〇一二三四五六七八九"
YEAR_CUES = {"in", "since", "until", "till", "by", "of", "from", "to", "year", "early", "late", "mid",
             "january", "february", "march", "april", "may", "june", "july", "august", "september",
             "october", "november", "december", "summer", "winter", "spring", "autumn", "fall"}


def _under10000(n):
    out = ""
    for unit, val in (("千", 1000), ("百", 100), ("十", 10)):
        d = n // val
        if d:
            out += ("" if d == 1 else DIG[d]) + unit
        n %= val
    if n:
        out += DIG[n]
    return out


def int2kanji(n):
    if n == 0:
        return "ゼロ"
    out = ""
    for unit, val in (("兆", 10 ** 12), ("億", 10 ** 8), ("万", 10 ** 4)):
        d = n // val
        if d:
            out += _under10000(d) + unit
        n %= val
    return out + _under10000(n)


def _ja_numbers(t):
    def dec(m):
        ip, fp = m.group(1), m.group(2)
        head = "れい" if ip == "0" else int2kanji(int(ip))
        return head + "点" + "".join(DIG[int(c)] for c in fp)
    t = re.sub(r"(\d+)\.(\d+)", dec, t)
    t = re.sub(r"\d{1,3}(,\d{3})+", lambda m: m.group(0).replace(",", ""), t)
    return re.sub(r"\d+", lambda m: int2kanji(int(m.group(0))), t)


def _other_numbers(t, lang):
    try:
        from num2words import num2words
    except ImportError:
        return t
    code = {"zh": "zh", "vi": "vi", "en": "en", "ko": "ko"}.get(lang, lang)
    t = re.sub(r"(\d),(\d{3})", r"\1\2", t)

    def rep(m):
        s = m.group(0)
        try:
            if "." in s:
                return num2words(float(s), lang=code)
            n = int(s)
            prev = re.findall(r"(\w+)\W*$", m.string[:m.start()])
            if lang == "en" and 1100 <= n <= 2099 and prev and prev[0].lower() in YEAR_CUES:
                return num2words(n, lang="en", to="year")
            return num2words(n, lang=code)
        except NotImplementedError:
            return s
    return re.sub(r"\d+(?:\.\d+)?", rep, t)


def to_tts(text, lang=None, readings=None):
    cfg = config.load()
    lang = lang or cfg["language"]
    readings = cfg["voice"]["readings"] if readings is None else readings
    t = text
    for a in sorted(readings, key=len, reverse=True):     # longest first: "NASA本部" before "NASA"
        t = t.replace(a, readings[a])
    if lang == "ja":
        t = t.replace("%", "パーセント")
        return _ja_numbers(t)
    return _other_numbers(t, lang)


def count(text, unit=None):
    unit = unit or config.load()["length"]["unit"]
    if unit == "words":
        return len(re.findall(r"\w+", text))
    return len(re.sub(r"\s", "", text))


def sentences(text, lang=None):
    """Split narration into sentences (keeps closing quotes with their sentence)."""
    lang = lang or config.load()["language"]
    if config.is_cjk(lang):
        parts = re.findall(r"[^。？！]*[。？！]」?。?|[^。？！]+$", text)
    else:
        parts = re.findall(r".+?[.?!][\"”’)]*(?=\s|$)|.+$", text)
    out = []
    for p in (x.strip() for x in parts):
        if not p:
            continue
        if out and re.fullmatch(r"[」。\"”’)]+", p):
            out[-1] += p
        else:
            out.append(p)
    return out


def normalize_for_compare(s, lang=None):
    """Make TTS text and an ASR transcript comparable (numbers -> words, punctuation removed)."""
    lang = lang or config.load()["language"]
    s = to_tts(s, lang)
    if config.is_cjk(lang):
        return re.sub(r"[\s、。「」『』！？!?,.・ー\-（）()…：:“”\"']", "", s)
    return re.sub(r"[^\w]+", " ", s.lower()).strip()
