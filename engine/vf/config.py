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
    "voice": {
        "tts_model": "gemini-3.8-flash-tts",
        "voice": "Arlo",
        "asr_models": ["gemini-3.8-flash", "gemini-3.5-flash"],
        "min_similarity": 0.93,
        "attempts": 3,
        "workers": 4,
        "readings": {},                      # display text -> what TTS should read
    },
    "director": {
        "genre": "",
        "real_pct": {"min": None, "max": None},   # REQUIRED range of real footage/photos over the WHOLE film (Phase 2);
                                                   # single chapters are free (all archive / all animation is fine)
    },
    # design: NO style defaults. Every film decides its own look (docs/07). Only technical values have defaults.
    "design": {
        "grades": {},           # REQUIRED: {main: {desat, contrast, warm, vignette, grain, gfx_grain, bottom}, <other>: {...}}
        "palette": {},          # REQUIRED: colours your graphics use (any keys -> C.<key> in custom_gfx.py)
        "fonts": {},            # REQUIRED: role -> font file in vendor/fonts (roles are yours: e.g. display, text, mono)
        # On-screen text layers burned in by libass. None = REQUIRED decision of the film (docs/07).
        # Sizes/outlines have legible 1080p starting values; change them freely.
        # Colours "#rrggbb"; opacity 0..1. Positions: top-left | top-right | bottom-left | bottom-right
        # (bottom positions sit just above the subtitle block); lower_third.position: left | right.
        "subtitle": {"font": None, "colour": None, "outline_colour": "#101010", "size": 50, "max_chars": 24,
                     "slack": 4, "margin_v": 62, "outline": 2.6, "shadow": 1.2, "shadow_opacity": 0.41, "spacing": 1},
        "credit": {"font": None, "colour": None, "opacity": 1.0, "position": None, "size": 22, "outline": 1.2},
        "stamp": {"font": None, "colour": None, "opacity": 1.0, "position": None, "size": 28, "outline": 1.6,
                  "spacing": 1},
        "lower_third": {"name_font": None, "name_colour": None, "name_size": 44, "role_font": None,
                        "role_colour": None, "role_opacity": 1.0, "role_size": 28, "position": None,
                        "plate": None, "plate_colour": "#000000", "plate_opacity": 0.7},
        "chapter_card": {"enabled": None, "duration": None, "gfx": "chapter"},    # enabled REQUIRED; duration if enabled
        "transitions": {"film_in": None, "film_out": None, "after_card": None},  # REQUIRED: cut | fade:<s> | dissolve:<s>
        "motion": {"still_zoom": None, "video_push": None},                      # REQUIRED (0 = static)
        "safe_margin": 0.05,                 # technical: fraction of width/height kept clear of text
        "subtitle_zone_top": None,           # gfx text must stay above this y; None = derived from subtitle style
    },
    "labels": {"photo": "写真：", "video": "映像：", "map": "地図：", "source": "出典：",
               "public_domain": "パブリックドメイン", "commons": "Wikimedia Commons",
               "reenactment": "再現", "photo_year": "写真は{year}年", "sep": "／", "paren": ["（", "）"]},
    "timing": {"lead": 0.15, "gap": 0.30, "chapter_end_extra": 1.2,
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
    # language -> linguistic/technical defaults only (credit labels, subtitle line length, length unit). Fonts are
    # a design decision of each film (docs/07); `scripts/fetch_fonts.py` downloads any Google Fonts family.
    "ja": {},
    "zh": {"design": {"subtitle": {"max_chars": 22}},
           "labels": {"photo": "图片：", "video": "视频：", "map": "地图：", "source": "来源：",
                      "public_domain": "公有领域", "reenactment": "再现", "photo_year": "摄于{year}年"}},
    "ko": {"design": {"subtitle": {"max_chars": 20}},
           "labels": {"photo": "사진: ", "video": "영상: ", "map": "지도: ", "source": "출처: ",
                      "public_domain": "퍼블릭 도메인", "reenactment": "재현", "photo_year": "{year}년 촬영"}},
    "_latin": {"design": {"subtitle": {"size": 48, "max_chars": 42, "slack": 6}},
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


GRADE_KEYS = {"desat": 0.0, "contrast": 1.0, "warm": [1.0, 1.0, 1.0], "vignette": 0.0, "grain": 0.0,
              "gfx_grain": 0.0, "bottom": 1.0}


def design_missing():
    """Design decisions that must be made in Phase 7 before rendering (no style is assumed)."""
    d = load()["design"]
    miss = []
    if not d.get("grades", {}).get("main"):
        miss.append("design.grades.main (colour grade of this film)")
    for name, g in (d.get("grades") or {}).items():
        unknown = set(g) - set(GRADE_KEYS)
        if unknown:
            miss.append(f"design.grades.{name}: unknown keys {sorted(unknown)} (allowed: {sorted(GRADE_KEYS)})")
    if not d.get("palette"):
        miss.append("design.palette (the colours of this film's graphics)")
    if not d.get("fonts"):
        miss.append("design.fonts (role -> font file)")
    corners = ("top-left", "top-right", "bottom-left", "bottom-right")
    req = [("subtitle.font", d["subtitle"]["font"], None), ("subtitle.colour", d["subtitle"]["colour"], None),
           ("credit.font", d["credit"]["font"], None), ("credit.colour", d["credit"]["colour"], None),
           ("credit.position", d["credit"]["position"], corners),
           ("stamp.font", d["stamp"]["font"], None), ("stamp.colour", d["stamp"]["colour"], None),
           ("stamp.position", d["stamp"]["position"], corners),
           ("lower_third.name_font", d["lower_third"]["name_font"], None),
           ("lower_third.name_colour", d["lower_third"]["name_colour"], None),
           ("lower_third.role_font", d["lower_third"]["role_font"], None),
           ("lower_third.role_colour", d["lower_third"]["role_colour"], None),
           ("lower_third.position", d["lower_third"]["position"], ("left", "right")),
           ("lower_third.plate", d["lower_third"]["plate"], (True, False)),
           ("chapter_card.enabled", d["chapter_card"]["enabled"], (True, False)),
           ("motion.still_zoom", d["motion"]["still_zoom"], None),
           ("motion.video_push", d["motion"]["video_push"], None)]
    req += [(f"transitions.{k}", d["transitions"].get(k), None) for k in ("film_in", "film_out", "after_card")]
    if d["chapter_card"]["enabled"]:
        req.append(("chapter_card.duration", d["chapter_card"]["duration"], None))
    for k, v, allowed in req:
        if v is None or v == "":
            miss.append(f"design.{k}" + (f" (one of {list(allowed)})" if allowed else ""))
        elif allowed and v not in allowed:
            miss.append(f"design.{k}: {v!r} is not one of {list(allowed)}")
    for k, v in d["transitions"].items():
        if v and v != "cut" and str(v).partition(":")[0] not in ("fade", "dissolve"):
            miss.append(f"design.transitions.{k}: {v!r} (cut | fade:<s> | dissolve:<s>)")
    if d["credit"]["position"] and d["credit"]["position"] == d["stamp"]["position"]:
        miss.append("design.credit.position and design.stamp.position are the same corner (they would overlap)")
    lt = d["lower_third"]["position"]
    for k in ("credit", "stamp"):
        if lt and d[k]["position"] == f"bottom-{lt}":
            miss.append(f"design.{k}.position bottom-{lt} collides with the lower third ({lt})")
    r = load()["director"]["real_pct"]
    if r.get("min") is None or r.get("max") is None:
        miss.append("director.real_pct {min, max} (Phase 2)")
    return miss
