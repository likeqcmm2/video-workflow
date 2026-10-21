"""This film's graphics. Every function g_<name>(p, t, dur) becomes  VIS: gfx:<name> | key=value ...
Design them for THIS film (genre, era, material) - the engine ships no graphic styles (docs/07, docs/08).

  p      parameters from the VIS line / graphics.yaml spec: p.s("title"), p.i("n"), p.f("x"), p.l("items"), p.rows("rows")
  t,dur  seconds into the shot / shot length - animate with ramp(t, start, length), ease(), mix()
  return a PIL image 1920x1080: RGB, or RGBA to be used as an overlay on footage (overlay=gfx:<name>)

Technical rules (preflight checks them): draw ALL text with text() so its box is measured; keep text >= 5 % from
every edge and above the subtitle block (~y 887 at 1080p) unless the scene has subs=off / allow_low=1; every
character must exist in the font; cite data sources on screen; label reconstructions as reconstructions.
If design.chapter_card.enabled is true, define the card graphic named in design.chapter_card.gfx (p: num, title).
Preview: ../../scripts/vf gfx-preview <name> k=v t=2 dur=5
"""
from PIL import ImageDraw  # noqa: F401

from vf.gfx import kit  # noqa: F401  (shapes/Projector for maps, scale for charts, paper/place for documents)
from vf.gfx.core import C, F, H, W, canvas, ease, fit_font, mix, ramp, text  # noqa: F401
