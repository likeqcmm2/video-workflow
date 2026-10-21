"""Colour grade + film texture, built from the film's own parameters (project.yaml design.grades).

There are no presets: the agent decides each film's grade from its genre, era and source material
(docs/07). A film may define several grades (e.g. one per era) and pick one per chapter (`### CH2 | … |
grade=archive`) or per shot (`grade=archive`); "main" is the default.

Parameters (all optional inside a grade; neutral values in brackets):
  desat     [0]     0..1 mix towards grey (negative = more saturation)
  contrast  [1]     around mid-grey
  warm      [1,1,1] per-channel gain R, G, B
  vignette  [0]     corner darkening
  grain     [0]     film grain amplitude on footage/photos
  gfx_grain [0]     grain on code-built graphics (so they sit with grainy footage)
  bottom    [1]     brightness at the bottom edge of footage/photos (< 1 helps subtitle legibility)
Technical notes: grain costs bitrate (keep crf, the encoder handles it); bottom 0.5-0.7 keeps white subtitles
readable on bright footage without a box.
"""
import cv2
import numpy as np

from . import config


class Grade:
    def __init__(self, prm):
        p = dict(config.GRADE_KEYS)
        p.update(prm or {})
        self.p = p
        W, H, _ = config.size()
        rs = np.random.RandomState(7)
        self.pos, self.neg = [], []
        amp = float(p["grain"])
        for _ in range(8):
            n = cv2.resize(rs.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
            n = np.repeat(n[..., None], 3, axis=2)
            self.pos.append(np.clip(n * amp, 0, 255).astype(np.uint8))
            self.neg.append(np.clip(-n * amp, 0, 255).astype(np.uint8))
        g = float(p["gfx_grain"]) / amp if amp else 0.0
        self.pos_g = [cv2.convertScaleAbs(x, alpha=g) for x in self.pos]
        self.neg_g = [cv2.convertScaleAbs(x, alpha=g) for x in self.neg]
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        v = np.clip(1 - float(p["vignette"]) * np.clip(r - 0.45, 0, None) ** 1.6, 0.6, 1)
        self.vig = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
        x = np.arange(256, dtype=np.float32)
        c = np.clip((x - 128) * float(p["contrast"]) + 126, 0, 255) if p["contrast"] != 1.0 else x
        wr, wg, wb = [float(v) for v in p["warm"]]
        self.lut = np.stack([np.clip(c * wr, 0, 255), np.clip(c * wg, 0, 255), np.clip(c * wb, 0, 255)],
                            axis=1).astype(np.uint8).reshape(256, 1, 3)
        gcol = np.ones((H, 1), np.float32)
        top = int(H * 0.68)
        gcol[top:, 0] = np.linspace(1.0, float(p["bottom"]), H - top) ** 1.2
        self.bottom = np.ascontiguousarray(np.repeat((np.repeat(gcol, W, axis=1) * 255).astype(np.uint8)[..., None], 3, axis=2))

    def apply(self, img, k, photo=True):
        img = np.ascontiguousarray(img)
        p = self.p
        if photo:
            ds = float(p["desat"])
            if ds:
                g3 = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
                img = cv2.addWeighted(img, 1 - ds, g3, ds, 0)
            img = cv2.LUT(img, self.lut)
            if p["vignette"]:
                img = cv2.multiply(img, self.vig, scale=1 / 255)
            if p["grain"]:
                img = cv2.add(img, self.pos[k % 8])
                img = cv2.subtract(img, self.neg[k % 8])
            if float(p["bottom"]) < 1:
                img = cv2.multiply(img, self.bottom, scale=1 / 255)
        elif p["gfx_grain"] and p["grain"]:
            img = cv2.add(img, self.pos_g[k % 8])
            img = cv2.subtract(img, self.neg_g[k % 8])
        return img


class Look:
    """All grades of the film, built lazily."""

    def __init__(self):
        self.defs = config.load()["design"]["grades"]
        if "main" not in self.defs:
            raise SystemExit("design.grades.main is not defined - decide the film's grade (docs/07)")
        self.cache = {}

    def grade(self, name=None):
        name = name or "main"
        if name not in self.defs:
            raise SystemExit(f"grade {name!r} is not defined in design.grades")
        if name not in self.cache:
            self.cache[name] = Grade(self.defs[name])
        return self.cache[name]

    def apply(self, img, k, photo=True, name=None):
        return self.grade(name).apply(img, k, photo)
