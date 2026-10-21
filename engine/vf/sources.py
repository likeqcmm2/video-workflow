"""Scouting helpers for open archives. Every command prints a SHORT table and writes full results
to a JSON file under assets/ - never dump raw API JSON into the conversation.

  NASA Image and Video Library  (public domain; https://images.nasa.gov)
  Internet Archive              (check each item's licence/rights field!)
"""
import json
import re
import time
from pathlib import Path

import requests

UA = {"User-Agent": "video-workflow/1.0 (documentary production; python-requests)"}


def _get(url, **kw):
    for a in range(4):
        try:
            r = requests.get(url, headers=UA, timeout=60, **kw)
            if r.status_code == 429:
                time.sleep(int(r.headers.get("Retry-After", "30")) + 2)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException:
            if a == 3:
                raise
            time.sleep(5 * (a + 1))


# ---------------------------------------------------------------- NASA
def nasa_search(q, media="image", pages=1, year_start=None, year_end=None):
    out = []
    for page in range(1, pages + 1):
        params = {"q": q, "media_type": media, "page": page}
        if year_start:
            params["year_start"] = year_start
        if year_end:
            params["year_end"] = year_end
        j = _get("https://images-api.nasa.gov/search", params=params).json()
        for it in j["collection"]["items"]:
            d = it["data"][0]
            out.append({"id": d["nasa_id"], "title": d.get("title", "")[:90], "date": d.get("date_created", "")[:10],
                        "center": d.get("center"), "desc": re.sub(r"\s+", " ", d.get("description", ""))[:300],
                        "preview": (it.get("links") or [{}])[0].get("href")})
        if len(j["collection"]["items"]) < 100:
            break
    Path("assets/nasa/scout").mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", q)[:60]
    Path(f"assets/nasa/scout/{slug}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    for r in out[:40]:
        print(f"{r['id']:28s} {r['date']}  {r['title']}")
    print(f"({len(out)} results -> assets/nasa/scout/{slug}.json)")
    return out


def nasa_fetch(ids, prefer=("~orig", "~large")):
    Path("assets/nasa/meta").mkdir(parents=True, exist_ok=True)
    for nid in ids:
        dest = Path(f"assets/nasa/{nid}.jpg")
        if dest.exists() and dest.stat().st_size > 1000:
            continue
        files = _get(f"https://images-api.nasa.gov/asset/{nid}").json()["collection"]["items"]
        hrefs = [f["href"] for f in files]
        url = None
        for p in prefer:
            url = next((h for h in hrefs if p in h and h.lower().endswith((".jpg", ".jpeg", ".png", ".tif"))), None)
            if url:
                break
        if not url:
            print("no image file for", nid)
            continue
        data = _get(url.replace("http://", "https://")).content
        if url.lower().endswith((".tif", ".png")):
            from io import BytesIO
            from PIL import Image
            im = Image.open(BytesIO(data)).convert("RGB")
            im.thumbnail((4000, 4000))
            im.save(dest, quality=92)
        else:
            dest.write_bytes(data)
        try:
            meta = _get(f"https://images-api.nasa.gov/search", params={"nasa_id": nid}).json()
            d = meta["collection"]["items"][0]["data"][0]
            Path(f"assets/nasa/meta/{nid}.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
        except Exception:
            pass
        print("nasa", nid, dest.stat().st_size)


# ---------------------------------------------------------------- Internet Archive
def ia_search(q, rows=50, mediatype="movies"):
    params = {"q": f"({q}) AND mediatype:{mediatype}", "fl[]": ["identifier", "title", "year", "licenseurl", "rights"],
              "rows": rows, "output": "json"}
    j = _get("https://archive.org/advancedsearch.php", params=params).json()
    docs = j["response"]["docs"]
    Path("assets/ia/scout").mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^A-Za-z0-9]+", "_", q)[:60]
    Path(f"assets/ia/scout/{slug}.json").write_text(json.dumps(docs, ensure_ascii=False, indent=1))
    for d in docs[:40]:
        lic = "lic" if d.get("licenseurl") else ""
        print(f"{d['identifier'][:45]:45s} {str(d.get('year', ''))[:4]:4s} {lic:3s} {str(d.get('title'))[:70]}")
    print(f"({len(docs)} results -> assets/ia/scout/{slug}.json)")
    return docs


def ia_files(identifier):
    j = _get(f"https://archive.org/metadata/{identifier}").json()
    md = j.get("metadata", {})
    files = [f for f in j.get("files", []) if f.get("format") and any(
        x in f["format"].lower() for x in ("mpeg4", "h.264", "ogg video", "matroska", "webm", "jpeg", "png"))]
    print(f"{identifier}: {md.get('title')} | licence: {md.get('licenseurl') or md.get('rights') or 'NOT STATED'}")
    for f in files[:30]:
        print(f"  {f['name'][:70]:70s} {f.get('format')} {int(f.get('size', 0)) // 1_000_000}MB {f.get('height', '')}")
    return files


def ia_fetch(identifier, name, dest=None):
    dest = Path(dest or f"assets/ia/{name.replace('/', '_')}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 1000:
        print("exists", dest)
        return dest
    url = f"https://archive.org/download/{identifier}/{requests.utils.quote(name)}"
    with requests.get(url, headers=UA, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    print("ia", dest, dest.stat().st_size)
    return dest


# ---------------------------------------------------------------- music (Incompetech, CC BY 4.0)
def music_fetch(titles):
    Path("assets/music").mkdir(parents=True, exist_ok=True)
    for t in titles:
        dest = Path("assets/music") / (t.replace(" ", "_") + ".mp3")
        if dest.exists():
            continue
        url = "https://incompetech.com/music/royalty-free/mp3-royaltyfree/" + requests.utils.quote(t) + ".mp3"
        dest.write_bytes(_get(url).content)
        print("music", dest, dest.stat().st_size)
