"""Graphics registry: the project's own custom_gfx.py. There is no built-in style library on purpose -
every film designs its graphics, cards and animation for its genre, era and material (docs/08).

    # custom_gfx.py (next to project.yaml)
    from PIL import ImageDraw
    from vf.gfx.core import C, F, W, H, canvas, text, ramp, ease, mix     # neutral primitives
    from vf.gfx import kit                                                # maps, scales, paper
    def g_chapter(p, t, dur):          # becomes  gfx:chapter  (also used for chapter cards)
        im = canvas(); d = ImageDraw.Draw(im); ...; return im           # RGB, or RGBA for overlays

graphics.yaml (optional) holds structured parameters referenced from VIS lines with  spec=<id>;
inline VIS options override spec values. Complex motion (3D, particles, long animations) is better
rendered with a dedicated tool into a clip and used as  anim:<file>  (docs/08).
"""
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

import yaml
from PIL import Image

from . import core
from .core import BOXES, P


@lru_cache(None)
def _custom():
    p = Path("custom_gfx.py")
    if not p.exists():
        return {}
    spec = importlib.util.spec_from_file_location("custom_gfx", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["custom_gfx"] = mod
    spec.loader.exec_module(mod)
    return {k[2:]: v for k, v in vars(mod).items() if k.startswith("g_") and callable(v)}


@lru_cache(None)
def _specs():
    p = Path("graphics.yaml")
    return (yaml.safe_load(p.read_text()) or {}) if p.exists() else {}


def registry():
    return dict(_custom())


def params(opts):
    base = {}
    if opts.get("spec"):
        sp = _specs().get(opts["spec"])
        if sp is None:
            raise KeyError(f"graphics.yaml has no spec {opts['spec']!r}")
        base.update(sp)
    base.update({k: v for k, v in opts.items() if k != "spec"})
    return P(base)


def render(name, opts, t, dur, track=False, rgba=False):
    reg = registry()
    if name not in reg:
        raise KeyError(f"graphic {name!r} is not defined in custom_gfx.py (defined: {sorted(reg)})")
    BOXES.clear()
    im = reg[name](params(opts), t, dur)
    from .. import config
    W, H, _ = config.size()
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    if rgba:
        im = im.convert("RGBA")
    elif im.mode != "RGB":
        im = im.convert("RGB")
    return (im, list(BOXES)) if track else im
