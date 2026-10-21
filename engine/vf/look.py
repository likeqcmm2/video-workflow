"""Colour grade + film texture per genre ("look"). Chosen in project.yaml design.look, tweakable with
design.look_params. documentary_dark is exactly the grade of the reference (Challenger) video.

  desat      0..1 mix towards grey (negative = saturation boost)
  contrast   around mid-grey
  warm       per-channel gain (R, G, B)
  vignette   corner darkening strength
  grain      film grain amplitude on footage/photos (0 = clean)
  gfx_grain  grain on code-built graphics (keeps them from looking "digital" next to film)
  bottom     brightness at the bottom edge of footage (darkens under subtitles; 1 = none)
"""
import cv2
import numpy as np

from . import config

PRESETS = {
    "documentary_dark": dict(desat=0.28, contrast=1.06, warm=(1.025, 1.0, 0.965), vignette=0.28, grain=7.0,
                             gfx_grain=3.5, bottom=0.5),
    "history_warm": dict(desat=0.15, contrast=1.04, warm=(1.06, 1.0, 0.90), vignette=0.30, grain=6.0,
                         gfx_grain=3.0, bottom=0.55),
    "mystery_dark": dict(desat=0.40, contrast=1.08, warm=(0.97, 1.0, 1.05), vignette=0.38, grain=8.0,
                         gfx_grain=4.0, bottom=0.45),
    "science_clean": dict(desat=0.0, contrast=1.03, warm=(1.0, 1.0, 1.0), vignette=0.12, grain=0.0,
                          gfx_grain=0.0, bottom=0.6),
    "business_clean": dict(desat=0.05, contrast=1.03, warm=(1.0, 1.0, 1.0), vignette=0.08, grain=0.0,
                           gfx_grain=0.0, bottom=0.6),
    "vivid": dict(desat=-0.10, contrast=1.05, warm=(1.0, 1.0, 1.0), vignette=0.10, grain=0.0, gfx_grain=0.0,
                  bottom=0.6),
}


class Look:
    def __init__(self):
        cfg = config.load()["design"]
        prm = dict(PRESETS.get(cfg["look"], PRESETS["documentary_dark"]))
        prm.update(cfg.get("look_params") or {})
        self.p = prm
        W, H, _ = config.size()
        self.W, self.H = W, H
        rs = np.random.RandomState(7)
        self.pos, self.neg = [], []
        for _ in range(8):
            n = cv2.resize(rs.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
            n = np.repeat(n[..., None], 3, axis=2)
            self.pos.append(np.clip(n * prm["grain"], 0, 255).astype(np.uint8))
            self.neg.append(np.clip(-n * prm["grain"], 0, 255).astype(np.uint8))
            self._gpos = None
        g = prm["gfx_grain"] / max(prm["grain"], 1e-6) if prm["grain"] else 0
        self.pos_g = [cv2.convertScaleAbs(x, alpha=g) for x in self.pos]
        self.neg_g = [cv2.convertScaleAbs(x, alpha=g) for x in self.neg]
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        v = np.clip(1 - prm["vignette"] * np.clip(r - 0.45, 0, None) ** 1.6, 0.6, 1)
        self.vig = np.repeat((v * 255).astype(np.uint8)[..., None], 3, axis=2)
        x = np.arange(256, dtype=np.float32)
        c = np.clip((x - 128) * prm["contrast"] + 126, 0, 255)
        wr, wg, wb = prm["warm"]
        self.lut = np.stack([np.clip(c * wr, 0, 255), np.clip(c * wg, 0, 255), np.clip(c * wb, 0, 255)],
                            axis=1).astype(np.uint8).reshape(256, 1, 3)
        gcol = np.ones((H, 1), np.float32)
        top = int(H * 0.68)
        gcol[top:, 0] = np.linspace(1.0, prm["bottom"], H - top) ** 1.2
        self.bottom = np.ascontiguousarray(np.repeat((np.repeat(gcol, W, axis=1) * 255).astype(np.uint8)[..., None], 3, axis=2))

    def apply(self, img, k, photo=True):
        img = np.ascontiguousarray(img)
        p = self.p
        if photo:
            if p["desat"]:
                g3 = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
                img = cv2.addWeighted(img, 1 - p["desat"], g3, p["desat"], 0)
            img = cv2.LUT(img, self.lut)
            img = cv2.multiply(img, self.vig, scale=1 / 255)
            if p["grain"]:
                img = cv2.add(img, self.pos[k % 8])
                img = cv2.subtract(img, self.neg[k % 8])
            if p["bottom"] < 1:
                img = cv2.multiply(img, self.bottom, scale=1 / 255)
        elif p["gfx_grain"] and p["grain"]:
            img = cv2.add(img, self.pos_g[k % 8])
            img = cv2.subtract(img, self.neg_g[k % 8])
        return img
