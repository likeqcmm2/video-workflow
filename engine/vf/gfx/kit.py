"""Technical helpers for custom graphics - geometry and data, no styling decisions.

  shapes(region)                    Natural Earth polygons: "world" | "us48" | "JPN,KOR" (ISO3 list) | "admin1:JPN"
  Projector(rows, box, bbox=None)   fits polygons into a pixel box (equirectangular with cos(lat) correction);
                                    pr(lon, lat) -> (x, y)
  scale(v0, v1, p0, p1)             linear value -> pixel mapping for charts (returns a function)
  paper(w, h, colour)               RGBA sheet with fibre noise (for document reconstructions)
  place(im, layer, alpha, cx, cy, angle, shadow)   paste an RGBA layer rotated, with optional drop shadow
Map data: Natural Earth 1:50m (public domain) in vendor/geo (scripts/setup.sh). Credit it on screen.
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image

from .. import config


@lru_cache(4)
def _layer(name):
    import shapefile
    r = shapefile.Reader(str(config.GEO_DIR / name))
    fields = [f[0] for f in r.fields[1:]]
    out = []
    for sr in r.shapeRecords():
        rec = dict(zip(fields, sr.record))
        pts = sr.shape.points
        parts = list(sr.shape.parts) + [len(pts)]
        out.append((rec, [pts[parts[i]:parts[i + 1]] for i in range(len(parts) - 1)]))
    return out


def shapes(region="world"):
    """[(name, [polygon, ...]), ...] for a region. Polygons are lists of (lon, lat)."""
    if region == "us48":
        rows = [(r["name"], p) for r, p in _layer("ne_50m_admin_1_states_provinces_lakes")
                if r.get("adm0_a3") == "USA" and r.get("name") not in ("Alaska", "Hawaii")]
    elif region.startswith("admin1:"):
        iso = region.split(":", 1)[1]
        rows = [(r["name"], p) for r, p in _layer("ne_50m_admin_1_states_provinces_lakes") if r.get("adm0_a3") == iso]
    else:
        rows = [(r["NAME"], p) for r, p in _layer("ne_50m_admin_0_countries")
                if region == "world" or r.get("ADM0_A3") in region.split(",") or r.get("ISO_A3") in region.split(",")]
    if not rows:
        raise ValueError(f"no shapes for region {region!r}")
    return rows


class Projector:
    def __init__(self, rows, box=(140, 150, 1780, 800), bbox=None):
        if bbox:
            lon0, lat0, lon1, lat1 = bbox
        else:
            xs = [x for _, ps in rows for poly in ps for x, _ in poly]
            ys = [y for _, ps in rows for poly in ps for _, y in poly]
            lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
        self.k = math.cos(math.radians((lat0 + lat1) / 2))
        self.s = min((box[2] - box[0]) / ((lon1 - lon0) * self.k), (box[3] - box[1]) / (lat1 - lat0))
        self.c = ((lon0 + lon1) / 2, (lat0 + lat1) / 2)
        self.o = ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

    def __call__(self, lon, lat):
        return self.o[0] + (lon - self.c[0]) * self.k * self.s, self.o[1] - (lat - self.c[1]) * self.s

    def polygon(self, poly):
        return [self(*pt) for pt in poly]


def scale(v0, v1, p0, p1):
    return lambda v: p0 + (v - v0) / (v1 - v0) * (p1 - p0)


def paper(w, h, colour, seed=3, noise=16):
    im = Image.new("RGBA", (w, h), tuple(colour) + (255,))
    nz = (np.random.RandomState(seed).rand(h, w) * noise).astype(np.uint8)
    arr = np.array(im)
    arr[..., :3] = np.clip(arr[..., :3].astype(int) - nz[..., None], 0, 255)
    return Image.fromarray(arr)


def place(im, layer, a, cx, cy, angle=0.0, shadow=True):
    pp = layer.rotate(angle, expand=True, resample=Image.BICUBIC) if angle else layer
    alpha = pp.split()[3].point(lambda v: int(v * a))
    if shadow:
        sh = Image.new("RGBA", pp.size, (0, 0, 0, 140))
        im.paste(sh, (int(cx - pp.width / 2 + 14), int(cy - pp.height / 2 + 16)), alpha.point(lambda v: int(v * 0.6)))
    im.paste(pp, (int(cx - pp.width / 2), int(cy - pp.height / 2)), alpha)
    return (cx - pp.width / 2, cy - pp.height / 2, cx + pp.width / 2, cy + pp.height / 2)
