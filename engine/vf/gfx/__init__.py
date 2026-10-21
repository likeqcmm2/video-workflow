"""Graphics registry: library templates + the project's own custom_gfx.py.

    from vf.gfx import render
    img = render("bars", {"spec": "flights"}, t=1.0, dur=6.0)

Project extension (custom_gfx.py next to project.yaml):

    from vf.gfx.core import *            # C, F, text, ramp, canvas, ...
    def g_joint(p, t, dur):               # becomes  gfx:joint
        im = canvas(); d = ImageDraw.Draw(im); ...; return im

graphics.yaml (optional) holds structured parameters:   flights: {labels: [...], values: [...]}
and is referenced from VIS lines with  spec=flights . Inline VIS options override spec values.
"""
import importlib.util
import sys
from functools import lru_cache
from pathlib import Path

import yaml
from PIL import Image

from . import core
from .core import BOXES, P
from .library import REG as LIB


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
    reg = dict(LIB)
    reg.update(_custom())
    return reg


def params(opts):
    base = {}
    if opts.get("spec"):
        sp = _specs().get(opts["spec"])
        if sp is None:
            raise KeyError(f"graphics.yaml has no spec {opts['spec']!r}")
        base.update(sp)
    base.update({k: v for k, v in opts.items() if k != "spec"})
    return P(base)


def render(name, opts, t, dur, track=False):
    reg = registry()
    if name not in reg:
        raise KeyError(f"unknown graphic {name!r}; library: {sorted(LIB)}; custom: {sorted(_custom())}")
    BOXES.clear()
    im = reg[name](params(opts), t, dur)
    from .. import config
    W, H, _ = config.size()
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    if im.mode != "RGB":
        im = im.convert("RGB")
    return (im, list(BOXES)) if track else im
