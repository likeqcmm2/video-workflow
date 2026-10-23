"""Resolve a VIS source to (kind, path, credit, meta). Missing media is an ERROR, never a silent
placeholder.

Sources
  gfx:<name>             code-built graphic from the project's custom_gfx.py
  anim:<path> [@m:ss.s]  animation/motion-graphics clip rendered with any tool (Manim, Remotion, Blender…);
                         counts as GRAPHICS in the real/graphics ratio; credit optional
  <ASSET_ID> @m:ss.s     registered video in project.yaml assets (path, credit, crop, desat, scan)
  vid:<path> @m:ss.s     local video file (credit=... required)
  img:<path>             local image (credit=... required; credit=none for own material)
  nasa:<id>              NASA Image Library still saved by `vf nasa fetch` -> assets/nasa/<id>.jpg
  cm:<File title>        Wikimedia Commons file fetched by `vf commons fetch` (credit from metadata)
"""
import glob
import json
import os
import re
from pathlib import Path

from . import config

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp")
VID_EXT = (".mp4", ".mov", ".webm", ".mkv", ".ogv", ".avi", ".m4v", ".mpg", ".ts")


class AssetError(Exception):
    pass


def _labels():
    return config.load()["labels"]


def credit_join(kind_label, *parts, paren=None):
    L = _labels()
    body = L["sep"].join(p for p in parts if p)
    if paren:
        body += L["paren"][0] + paren + L["paren"][1]
    return kind_label + body


def commons_path(title):
    from .wm_client import _safe_name
    stem = os.path.splitext(_safe_name("File:" + title))[0]
    for sub in ("1920", "1280", "960", "3840", "500", "original", "330", "250"):
        c = [x for x in glob.glob(f"assets/commons/{sub}/{glob.escape(stem)}.*") if not x.endswith((".ok", ".part"))]
        if c:
            return c[0]
    c = [x for x in glob.glob(f"assets/commons/video/{glob.escape(stem)}.*") if not x.endswith((".ok", ".part"))]
    return c[0] if c else None


def commons_meta(title):
    from .wm_client import _safe_name
    p = Path(f"assets/commons/metadata/{_safe_name('File:' + title)}.json")
    return json.loads(p.read_text()) if p.exists() else None


def commons_credit(title, kind="image"):
    L = _labels()
    lab = L["photo"] if kind == "image" else L["video"]
    m = commons_meta(title)
    if not m:
        return None
    lic = m.get("license", "")
    art = re.sub(r"\s+", " ", m.get("artist", "") or "").strip()
    if "unknown" in art.lower() or "not provided" in art.lower():
        art = ""
    if "public domain" in lic.lower() or lic.upper().startswith(("PD", "CC0")):
        who = "NASA" if "nasa" in (art + m.get("credit", "")).lower() else art[:40]
        return credit_join(lab, who, L["commons"], paren=L["public_domain"] if not lic.upper().startswith("CC0") else "CC0")
    return credit_join(lab, art[:40], lic, paren=L["commons"])


def registered(src):
    return config.load()["assets"].get(src)


def parse_alt(alt):
    parts = alt.split(";")
    opts = {}
    for kv in parts[1:]:
        if "=" not in kv:
            raise AssetError(f"bad alt option {kv!r} (use alt=src;key=value;key=value)")
        k, v = kv.split("=", 1)
        opts[k] = v
    head = parts[0]
    m = re.match(r"^(\S+)\s+@(\S+)$", head)
    from .scriptfmt import ts
    return {"src": m.group(1) if m else head, "in": ts(m.group(2)) if m else None, "opts": opts}


def resolve(shot, allow_alt=True):
    """Return dict(kind, path, credit, cls, used_alt). cls = real | graphic (for the ratio check)."""
    src, opts = shot["src"], shot["opts"]
    try:
        r = _resolve(src, opts)
        r["used_alt"] = False
    except AssetError:
        if allow_alt and opts.get("alt"):
            alt = parse_alt(opts["alt"])
            r = _resolve(alt["src"], alt["opts"])
            r["used_alt"] = True
            r["alt_shot"] = alt
        else:
            raise
    if opts.get("credit"):
        r["credit"] = None if opts["credit"] == "none" else opts["credit"]
    r.setdefault("cls", "graphic" if r["kind"] == "gfx" else "real")
    if opts.get("class") in ("real", "graphic"):
        r["cls"] = opts["class"]
    return r


def _resolve(src, opts):
    L = _labels()
    if src.startswith("gfx:"):
        return {"kind": "gfx", "path": src[4:], "credit": None, "cls": "graphic"}
    if src.startswith("anim:"):
        p = src[5:]
        if not os.path.exists(p):
            raise AssetError(f"animation clip missing: {p}")
        return {"kind": "video", "path": p, "credit": opts.get("credit"), "cls": "graphic", "anim": True}
    reg = registered(src)
    if reg:
        p = reg["path"]
        if not os.path.exists(p):
            raise AssetError(f"registered asset {src}: file missing {p}")
        return {"kind": "video", "path": p, "credit": reg.get("credit"), "asset": src,
                "cls": reg.get("class", "real")}
    if src.startswith("vid:"):
        p = src[4:]
        if not os.path.exists(p):
            raise AssetError(f"video missing: {p}")
        return {"kind": "video", "path": p, "credit": opts.get("credit")}
    if src.startswith("img:"):
        p = src[4:]
        if not os.path.exists(p):
            raise AssetError(f"image missing: {p}")
        if p.lower().endswith(".gif"):
            raise AssetError(f"{p}: GIF is not a still - convert with `vf media gif2mp4` and use vid:")
        return {"kind": "image", "path": p, "credit": opts.get("credit")}
    if src.startswith("nasa:"):
        nid = src[5:]
        c = [x for x in glob.glob(f"assets/nasa/{glob.escape(nid)}.*") if x.lower().endswith(IMG_EXT)]
        if not c:
            raise AssetError(f"NASA image missing: {nid} (vf nasa fetch {nid})")
        return {"kind": "image", "path": c[0], "credit": L["photo"] + "NASA"}
    if src.startswith("cm:"):
        title = src[3:]
        p = commons_path(title)
        if p is None:
            raise AssetError(f"Commons file not downloaded: {title} (vf commons fetch)")
        if p.lower().endswith(".gif"):
            raise AssetError(f"{title}: GIF - convert with `vf media gif2mp4 {p}` and reference it as vid:")
        kind = "video" if p.lower().endswith(VID_EXT) else "image"
        return {"kind": kind, "path": p, "credit": commons_credit(title, kind)}
    raise AssetError(f"unknown source {src!r}")


def video_opts(path):
    """crop / desat / cut-scan settings for a video path (from a registered asset, if any)."""
    for k, v in config.load()["assets"].items():
        if v.get("path") == path:
            return v
    return {}
