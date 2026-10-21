"""Download static TTF fonts from the Google Fonts CSS API into vendor/fonts/.

Usage:  python3 scripts/fetch_fonts.py ja            # fonts for a language (see LANG_FONTS)
        python3 scripts/fetch_fonts.py "Noto Sans KR:400,500,700"

Files are saved as <FamilyWithoutSpaces>-<weight>.ttf, e.g. NotoSansJP-500.ttf.
All fonts are SIL Open Font License (record this in sources.md).
"""
import re
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "vendor" / "fonts"

LANG_FONTS = {
    "ja": ["Noto Sans JP:400,500,700", "Noto Serif JP:500,700"],
    "zh": ["Noto Sans SC:400,500,700", "Noto Serif SC:500,700"],
    "zh-hant": ["Noto Sans TC:400,500,700", "Noto Serif TC:500,700"],
    "ko": ["Noto Sans KR:400,500,700", "Noto Serif KR:500,700"],
    "th": ["Noto Sans Thai:400,500,700", "Noto Serif Thai:500,700"],
    "latin": ["Noto Sans:400,500,700", "Noto Serif:500,700"],   # en, vi, es, fr, de, id, ru ...
}
ALWAYS = ["Noto Sans Mono:400"]


def fetch(spec: str):
    fam, _, weights = spec.partition(":")
    weights = weights or "400"
    url = f"https://fonts.googleapis.com/css2?family={fam.replace(' ', '+')}:wght@{weights.replace(',', ';')}"
    css = requests.get(url, timeout=60).text   # default python UA -> Google serves TrueType
    blocks = []
    for blk in css.split("@font-face")[1:]:
        w = re.search(r"font-weight:\s*(\d+)", blk)
        u = re.search(r"url\((\S+?)\)\s*format\('truetype'\)", blk)
        if w and u:
            blocks.append((w.group(1), u.group(1)))
    if not blocks:
        raise SystemExit(f"no truetype fonts returned for {spec!r}")
    for w, u in blocks:
        out = DEST / f"{fam.replace(' ', '')}-{w}.ttf"
        if out.exists() and out.stat().st_size > 10000:
            continue
        out.write_bytes(requests.get(u, timeout=120).content)
        print("font", out.name, out.stat().st_size)


def main(args):
    DEST.mkdir(parents=True, exist_ok=True)
    specs = list(ALWAYS)
    for a in args or ["ja"]:
        key = a.lower()
        if key in LANG_FONTS:
            specs += LANG_FONTS[key]
        elif ":" in a or a.startswith("Noto"):
            specs.append(a)
        else:
            specs += LANG_FONTS["latin"]
    for s in dict.fromkeys(specs):
        fetch(s)


if __name__ == "__main__":
    main(sys.argv[1:])
