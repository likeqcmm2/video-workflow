"""Project configuration (project.yaml) with defaults.

A project is a directory containing project.yaml + script.md. All engine commands run with
the project directory as the working directory; every relative path in project.yaml is
relative to it.
"""
import copy
import os
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]          # repo root
VENDOR = REPO / "vendor"
FONTS_DIR = VENDOR / "fonts"
GEO_DIR = VENDOR / "geo"

DEFAULTS = {
    "title": "",
    "language": "ja",                      # narration + on-screen text language
    "video": {"width": 1920, "height": 1080, "fps": 30},
    "length": {"unit": "chars", "min": 10000, "sample_hook": None, "hook_tolerance": 0.15},
    "copyright_level": "balanced",          # safe | balanced | max
    "graphic_content": "none",              # none | limited  (never child victims)
    "voice": {
        "tts_model": "gemini-3.8-flash-tts",
        "voice": "Arlo",
        "asr_models": ["gemini-3.8-flash", "gemini-3.5-flash"],
        "min_similarity": 0.93,
        "attempts": 3,
        "workers": 4,
        "readings": {},                      # display text -> what TTS should read
    },
    "director": {"genre": "", "target_real_pct": 70},
    "design": {
        "look": "documentary_dark",
        "palette": {"bg": "#0d1014", "text": "#e8e2d6", "muted": "#8f8a80", "dim": "#46484c",
                    "accent": "#c8553d", "secondary": "#9fb7c9", "paper": "#e9e4d8", "ink": "#22201c",
                    "line": "#beb8ac", "card_bg": "#080a0d"},
        "fonts": {"serif": "NotoSerifJP-500.ttf", "serif_bold": "NotoSerifJP-700.ttf",
                  "sans": "NotoSansJP-400.ttf", "sans_medium": "NotoSansJP-500.ttf",
                  "sans_bold": "NotoSansJP-700.ttf", "mono": "NotoSansMono-400.ttf"},
        "subtitle": {"font": "Noto Sans JP Medium", "size": 50, "max_chars": 24, "slack": 4,
                     "margin_v": 62, "outline": 2.6, "shadow": 1.2, "spacing": 1},
        "credit": {"font": "Noto Sans JP", "size": 22},
        "stamp": {"font": "Noto Sans JP Medium", "size": 28},
        "lower_third": {"name_font": "Noto Serif JP Medium", "name_size": 44,
                        "role_font": "Noto Sans JP", "role_size": 28},
        "chapter_card": {"enabled": True, "duration": 3.6},
        "safe_margin": 0.05,                 # fraction of width/height kept clear of text
        "subtitle_zone_top": None,           # gfx text must stay above this y; None = derived from subtitle style
        "kenburns": 0.10,                    # max zoom for still images
        "fade_in_start": 0.6,                # fade from black at the start of the film
        "fade_out_end": 1.5,                 # fade to black before the end
    },
    "labels": {"photo": "写真：", "video": "映像：", "map": "地図：", "source": "出典：",
               "public_domain": "パブリックドメイン", "commons": "Wikimedia Commons",
               "reenactment": "再現", "photo_year": "写真は{year}年", "sep": "／", "paren": ["（", "）"]},
    "timing": {"lead": 0.15, "gap": 0.30, "quote_extra": 0.5, "chapter_end_extra": 1.2,
               "end_black": 3.0, "max_still": 8.0},
    "assets": {},                            # registered video sources: ID -> {path, credit, crop, desat}
    "music": {"chapters": {}, "default": None, "level_between": 0.22, "level_under_voice": 0.09,
              "fade_in": 2.0, "fade_out": 2.5},
    "loudness": {"integrated": -16.0, "true_peak": -1.5, "lra": 11},
    "encode": {"crf": 18, "preset": "medium", "audio_bitrate": "192k", "jobs": 0},
    "review": {"every": 3.0, "skim_every": 6.0},
    "wikimedia": {"user_agent": None},       # falls back to env WIKIMEDIA_USER_AGENT
}

LANG_DEFAULTS = {
    # language -> overrides applied before project.yaml (fonts, subtitle sizes, labels)
    "ja": {},
    "zh": {"design": {"fonts": {"serif": "NotoSerifSC-500.ttf", "serif_bold": "NotoSerifSC-700.ttf",
                                "sans": "NotoSansSC-400.ttf", "sans_medium": "NotoSansSC-500.ttf",
                                "sans_bold": "NotoSansSC-700.ttf"},
                      "subtitle": {"font": "Noto Sans SC Medium", "max_chars": 22},
                      "credit": {"font": "Noto Sans SC"}, "stamp": {"font": "Noto Sans SC Medium"},
                      "lower_third": {"name_font": "Noto Serif SC Medium", "role_font": "Noto Sans SC"}},
           "labels": {"photo": "图片：", "video": "视频：", "map": "地图：", "source": "来源：",
                      "public_domain": "公有领域", "reenactment": "再现", "photo_year": "摄于{year}年"}},
    "ko": {"design": {"fonts": {"serif": "NotoSerifKR-500.ttf", "serif_bold": "NotoSerifKR-700.ttf",
                                "sans": "NotoSansKR-400.ttf", "sans_medium": "NotoSansKR-500.ttf",
                                "sans_bold": "NotoSansKR-700.ttf"},
                      "subtitle": {"font": "Noto Sans KR Medium", "max_chars": 20},
                      "credit": {"font": "Noto Sans KR"}, "stamp": {"font": "Noto Sans KR Medium"},
                      "lower_third": {"name_font": "Noto Serif KR Medium", "role_font": "Noto Sans KR"}},
           "labels": {"photo": "사진: ", "video": "영상: ", "map": "지도: ", "source": "출처: ",
                      "public_domain": "퍼블릭 도메인", "reenactment": "재현", "photo_year": "{year}년 촬영"}},
    "_latin": {"design": {"fonts": {"serif": "NotoSerif-500.ttf", "serif_bold": "NotoSerif-700.ttf",
                                    "sans": "NotoSans-400.ttf", "sans_medium": "NotoSans-500.ttf",
                                    "sans_bold": "NotoSans-700.ttf"},
                          "subtitle": {"font": "Noto Sans Medium", "size": 48, "max_chars": 42, "slack": 6},
                          "credit": {"font": "Noto Sans"}, "stamp": {"font": "Noto Sans Medium"},
                          "lower_third": {"name_font": "Noto Serif Medium", "role_font": "Noto Sans"}},
               "length": {"unit": "words"},
               "labels": {"photo": "Photo: ", "video": "Footage: ", "map": "Map: ", "source": "Source: ",
                          "public_domain": "public domain", "reenactment": "Reconstruction",
                          "photo_year": "photo taken {year}", "sep": " / ", "paren": [" (", ")"]}},
}
CJK = {"ja", "zh", "zh-hant", "ko", "th"}


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def find_project(argv):
    """Strip '--project DIR' from argv and chdir into the project directory."""
    if len(argv) > 1 and argv[0] == "--project":
        os.chdir(argv[1])
        argv = argv[2:]
    return argv


_cfg = None


def load(path="project.yaml"):
    global _cfg
    if _cfg is not None:
        return _cfg
    if not Path(path).exists():
        raise SystemExit(f"project.yaml not found in {os.getcwd()} - run inside a project directory "
                         f"or create one with:  vf init <dir>")
    user = yaml.safe_load(Path(path).read_text()) or {}
    lang = (user.get("language") or "ja").lower()
    cfg = DEFAULTS
    cfg = deep_merge(cfg, LANG_DEFAULTS.get(lang, LANG_DEFAULTS["_latin"] if lang not in CJK else {}))
    cfg = deep_merge(cfg, user)
    cfg["language"] = lang
    _cfg = cfg
    return cfg


def size():
    c = load()["video"]
    return c["width"], c["height"], c["fps"]


def is_cjk(lang=None):
    lang = lang or load()["language"]
    return lang in CJK


def subtitle_zone_top():
    """Top edge (px) of a two-line subtitle block - graphics text must stay above it."""
    d = load()["design"]
    if d.get("subtitle_zone_top"):
        return d["subtitle_zone_top"] * size()[1] / 1080
    st = d["subtitle"]
    return size()[1] - st["margin_v"] - 2 * st["size"] * 1.25 - 6
