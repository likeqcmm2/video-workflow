"""Wikimedia Commons client — the ONLY entry point for Commons Action API,
upload.wikimedia.org and thumb.php requests in this project.

Features: bot-password login with persisted cookies, fixed User-Agent,
process-wide (file-locked) rate limiter, API response cache, file cache,
retry/backoff for 429/403/5xx/connection errors, bandwidth-limited downloads,
license metadata extraction, JSONL request log, pending queue and stats.

Credentials come ONLY from environment variables (never logged, never committed):
  WIKIMEDIA_BOT_USER       e.g. "MyUser@MyBotName"   (Special:BotPasswords)
  WIKIMEDIA_BOT_PASSWORD
  WIKIMEDIA_USER_AGENT     e.g. "MyVideoBot/1.0 (https://commons.wikimedia.org/wiki/User:MyUser; bot)"
Without credentials the client runs anonymously with the slower anonymous limits.

Use standard-width thumbnails for images (download()) and transcodes for videos (video()).
Prefer these over originals when they meet the quality requirements.
"""
from __future__ import annotations

import fcntl
import hashlib
import http.cookiejar
import json
import os
import re
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

import requests

API = "https://commons.wikimedia.org/w/api.php"
BASE = Path("assets") / "commons"          # relative to the project directory (cwd)
DIRS = {k: BASE / k for k in ["250", "330", "500", "960", "1280", "1920", "3840", "original", "metadata",
                               "cache", "logs", "private", "video", "scout"]}
STD_WIDTHS = [20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840]

# internal limits (stricter than Wikimedia's published limits)
API_GAP = {True: 0.5, False: 1.0}     # logged-in / anonymous
FILE_GAP = {True: 1.0, False: 2.0}
BIG_FILE = 20 * 1024 * 1024
BIG_RATE = 2 * 1024 * 1024            # bytes/s for files > 20MB
MAX_GAP = 10.0

LOCK_FILE = DIRS["private"] / "rate.lock"
STATE_FILE = DIRS["private"] / "rate_state.json"
COOKIE_FILE = DIRS["private"] / "cookies.lwp"
LOG_FILE = DIRS["logs"] / "requests.jsonl"
STATS_FILE = DIRS["logs"] / "stats.json"
PENDING_FILE = DIRS["logs"] / "pending.json"


class WMError(Exception):
    pass


def _safe_name(title: str) -> str:
    t = title.split(":", 1)[-1] if title.lower().startswith("file:") else title
    stem, ext = os.path.splitext(t)
    h = hashlib.sha1(t.encode()).hexdigest()[:8]
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)[:80]
    return f"{stem}_{h}{ext.lower()}"


def _redact(url: str) -> str:
    return re.sub(r"(lgpassword|lgtoken|token)=[^&]*", r"\1=REDACTED", url)


def user_agent():
    ua = os.environ.get("WIKIMEDIA_USER_AGENT")
    if not ua:
        try:
            from . import config
            ua = config.load().get("wikimedia", {}).get("user_agent")
        except SystemExit:
            ua = None
    if not ua:
        raise SystemExit("Set WIKIMEDIA_USER_AGENT (a descriptive bot UA with contact info, see "
                         "docs/wikimedia.md). Browser or library-default UAs are not allowed.")
    return f"{ua} python-requests/{requests.__version__}"


class WMClient:
    def __init__(self, login: bool = True):
        for d in DIRS.values():
            d.mkdir(parents=True, exist_ok=True)
        os.chmod(DIRS["private"], 0o700)
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": user_agent()})
        self.s.cookies = http.cookiejar.LWPCookieJar(str(COOKIE_FILE))
        if COOKIE_FILE.exists():
            try:
                self.s.cookies.load(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass
        self.logged_in = False
        self.user = None
        self.stats = self._load_stats()
        self.ok_streak = 0
        self.consec_429_files = 0
        if login:
            self.ensure_login()

    # ---------------- stats / log ----------------
    def _load_stats(self):
        if STATS_FILE.exists():
            return json.loads(STATS_FILE.read_text())
        return {k: 0 for k in ["requests_sent", "api_requests", "file_requests", "cache_hits",
                               "http_429", "http_403", "http_5xx", "retries", "files_ok",
                               "files_failed", "bytes_downloaded"]}

    def _save_stats(self):
        self.stats["login_status"] = "logged_in" if self.logged_in else "anonymous"
        STATS_FILE.write_text(json.dumps(self.stats, indent=1))

    def _log(self, **kw):
        kw["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        kw["logged_in"] = self.logged_in
        if "url" in kw:
            kw["url"] = _redact(kw["url"])
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(kw, ensure_ascii=False) + "\n")

    # ---------------- rate limiter (shared across processes) ----------------
    @contextmanager
    def _slot(self, kind: str):
        """Serialize all Wikimedia requests (API and files) through one lock."""
        with open(LOCK_FILE, "a+") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                st = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
                mult = st.get("mult", 1.0)
                base = (API_GAP if kind == "api" else FILE_GAP)[self.logged_in]
                gap = min(MAX_GAP, base * mult)
                gap = max(gap, st.get("extra_wait", 0))
                pause_until = st.get("pause_until", 0)
                now = time.time()
                wait = max(st.get("last", 0) + gap - now, pause_until - now, 0)
                if wait > 0:
                    time.sleep(wait)
                t0 = time.time()
                info = {}
                yield info
                st = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
                st["last"] = time.time()
                # slow API responses -> wait 5s before next
                st["extra_wait"] = 5.0 if (kind == "api" and info.get("elapsed", 0) > 1.0) else 0
                if info.get("status") == 429:
                    st["mult"] = min(MAX_GAP / base, st.get("mult", 1.0) * 2)
                    self.ok_streak = 0
                elif info.get("status") == 200:
                    self.ok_streak += 1
                    if self.ok_streak >= 20 and st.get("mult", 1.0) > 1.0:
                        st["mult"] = max(1.0, st["mult"] / 2)
                        self.ok_streak = 0
                if info.get("pause_until"):
                    st["pause_until"] = info["pause_until"]
                STATE_FILE.write_text(json.dumps(st))
            finally:
                fcntl.flock(lf, fcntl.LOCK_UN)

    # ---------------- core request with retry ----------------
    def _request(self, kind, method, url, params=None, data=None, stream=False, label=""):
        backoff = [5, 10, 20, 40, 80]
        attempt = 0
        while True:
            attempt += 1
            with self._slot("api" if kind != "file" else "file") as info:
                t0 = time.time()
                err = None
                r = None
                try:
                    headers = {"Accept-Encoding": "gzip"} if kind != "file" else {}
                    r = self.s.request(method, url, params=params, data=data, stream=stream,
                                       timeout=(20, 120), headers=headers)
                    status = r.status_code
                except requests.RequestException as e:
                    status, err = 0, type(e).__name__
                info["elapsed"] = time.time() - t0
                info["status"] = status
                self.stats["requests_sent"] += 1
                self.stats["api_requests" if kind != "file" else "file_requests"] += 1
                if status == 429:
                    self.stats["http_429"] += 1
                elif status == 403:
                    self.stats["http_403"] += 1
                elif status >= 500:
                    self.stats["http_5xx"] += 1
                body = None
                if r is not None and status >= 400:
                    try:
                        body = r.text[:3000]
                    except Exception:
                        body = None
                self._log(type=label or kind, url=r.url if r is not None else url, status=status,
                          attempt=attempt, elapsed=round(info["elapsed"], 3), cache="miss",
                          error=err, body=body,
                          retry_after=(r.headers.get("Retry-After") if r is not None else None))
                wait = None
                if status == 429:
                    ra = r.headers.get("Retry-After")
                    wait = (float(ra) + 2) if ra and ra.isdigit() else backoff[min(attempt - 1, 4)]
                elif status >= 500:
                    ra = r.headers.get("Retry-After")
                    wait = max(60, float(ra) if ra and ra.isdigit() else 0)
                elif status == 0:
                    wait = backoff[min(attempt - 1, 4)]
                if wait:
                    info["pause_until"] = time.time() + wait
            if status == 200:
                self._save_stats()
                return r
            if status == 403:
                self._save_stats()
                raise WMError(f"403 Forbidden for {_redact(url)}: {r.text[:200]}")
            if status == 404:
                self._save_stats()
                raise WMError(f"404 for {_redact(url)}")
            if attempt >= 5 or wait is None:
                self._save_stats()
                raise WMError(f"failed status={status} after {attempt} attempts: {_redact(url)}")
            self.stats["retries"] += 1
            self._log(type="retry", url=url, status=status, attempt=attempt, wait=wait)

    # ---------------- login ----------------
    def _userinfo(self):
        r = self._request("api", "GET", API, params={"action": "query", "meta": "userinfo",
                                                     "format": "json"}, label="login")
        return r.json()["query"]["userinfo"]

    def ensure_login(self):
        try:
            ui = self._userinfo()
            if "anon" not in ui:
                self.logged_in, self.user = True, ui["name"]
                self._log(type="login", url=API, status=200, note="reused saved session")
                return True
            cred = {"username": os.environ.get("WIKIMEDIA_BOT_USER"),
                    "password": os.environ.get("WIKIMEDIA_BOT_PASSWORD")}
            if not cred["username"] or not cred["password"]:
                self._log(type="login", url=API, status=0, note="no credentials; anonymous mode")
                return False
            r = self._request("api", "GET", API, params={"action": "query", "meta": "tokens",
                                                         "type": "login", "format": "json"},
                              label="login")
            token = r.json()["query"]["tokens"]["logintoken"]
            r = self._request("api", "POST", API, data={"action": "login", "lgname": cred["username"],
                                                        "lgpassword": cred["password"],
                                                        "lgtoken": token, "format": "json"},
                              label="login")
            res = r.json().get("login", {})
            if res.get("result") != "Success":
                self._log(type="login", url=API, status=200,
                          note=f"login failed: {res.get('result')} {res.get('reason', '')}"[:200])
                return False
            ui = self._userinfo()
            self.logged_in = "anon" not in ui
            self.user = ui.get("name")
            if self.logged_in:
                self.s.cookies.save(ignore_discard=True, ignore_expires=True)
                os.chmod(COOKIE_FILE, 0o600)
            return self.logged_in
        except WMError as e:
            self._log(type="login", url=API, status=0, note=f"login error: {str(e)[:150]}")
            return False
        finally:
            self._save_stats()

    # ---------------- API with cache ----------------
    def api(self, params: dict, label="api", refresh=False) -> dict:
        p = dict(params)
        p.setdefault("format", "json")
        key = hashlib.sha256((API + json.dumps(p, sort_keys=True)).encode()).hexdigest()
        cf = DIRS["cache"] / f"{key}.json"
        if cf.exists() and not refresh:
            self.stats["cache_hits"] += 1
            self._log(type=label, url=API + "?" + "&".join(f"{k}={v}" for k, v in p.items()),
                      status=200, attempt=0, cache="hit")
            self._save_stats()
            return json.loads(cf.read_text())
        r = self._request("api", "GET", API, params=p, label=label)
        j = r.json()
        if "error" in j:
            raise WMError(f"API error: {j['error']}")
        cf.write_text(json.dumps(j, ensure_ascii=False))
        return j

    def _paged(self, params, label, max_pages=4):
        out = {}
        cont = {}
        for _ in range(max_pages):
            j = self.api({**params, **cont}, label=label)
            for pg in j.get("query", {}).get("pages", {}).values():
                out[pg["title"]] = pg
            if "continue" not in j:
                break
            cont = j["continue"]
        return out

    def search(self, query, limit=50, width=330, max_pages=1):
        return self._paged({"action": "query", "generator": "search", "gsrsearch": query,
                            "gsrnamespace": 6, "gsrlimit": limit, "prop": "imageinfo",
                            "iiprop": "url|size|mime", "iiurlwidth": width}, "search", max_pages)

    def category(self, cat, limit=50, width=330, max_pages=4):
        return self._paged({"action": "query", "generator": "categorymembers",
                            "gcmtitle": f"Category:{cat}", "gcmtype": "file", "gcmlimit": limit,
                            "prop": "imageinfo", "iiprop": "url|size|mime", "iiurlwidth": width},
                           "category", max_pages)

    def info(self, titles, width=1920, ext=False):
        """Batch lookup of known files (<=50 per request)."""
        out = {}
        titles = [t if t.startswith("File:") else "File:" + t for t in titles]
        for i in range(0, len(titles), 50 if not ext else 20):
            chunk = titles[i:i + (50 if not ext else 20)]
            prop = "url|size|mime" + ("|extmetadata" if ext else "")
            p = {"action": "query", "titles": "|".join(chunk), "prop": "imageinfo",
                 "iiprop": prop, "iiurlwidth": width}
            if ext:
                p["iiextmetadatafilter"] = "LicenseShortName|Artist|Credit|UsageTerms|ImageDescription|DateTimeOriginal|LicenseUrl"
            j = self.api(p, label="metadata" if ext else "info")
            norm = {n["to"]: n["from"] for n in j.get("query", {}).get("normalized", [])}
            for pg in j.get("query", {}).get("pages", {}).values():
                out[norm.get(pg["title"], pg["title"])] = pg
        return out

    def video_derivatives(self, title):
        j = self.api({"action": "query", "titles": title, "prop": "videoinfo",
                      "viprop": "url|size|mime|derivatives"}, label="metadata")
        pg = next(iter(j["query"]["pages"].values()))
        return pg.get("videoinfo", [{}])[0]

    # ---------------- license metadata ----------------
    def license(self, titles):
        res = {}
        for t, pg in self.info(titles, width=1920, ext=True).items():
            if "imageinfo" not in pg:
                res[t] = {"missing": True}
                continue
            ii = pg["imageinfo"][0]
            em = ii.get("extmetadata", {})
            g = lambda k: re.sub(r"<[^>]+>", "", em.get(k, {}).get("value", "")).strip()
            meta = {"title": t, "page": ii.get("descriptionurl"), "url": ii.get("url"),
                    "width": ii.get("width"), "height": ii.get("height"), "mime": ii.get("mime"),
                    "size": ii.get("size"), "license": g("LicenseShortName"), "artist": g("Artist"),
                    "credit": g("Credit"), "usage_terms": g("UsageTerms"),
                    "license_url": g("LicenseUrl"), "description": g("ImageDescription")[:500],
                    "date": g("DateTimeOriginal")}
            lic = meta["license"].lower()
            meta["flag"] = not any(x in lic for x in ["public domain", "cc0", "cc by", "cc-by", "pd"])
            (DIRS["metadata"] / (_safe_name(t) + ".json")).write_text(
                json.dumps(meta, ensure_ascii=False, indent=1))
            res[t] = meta
        return res

    # ---------------- file download ----------------
    def download(self, title, width=1920):
        """Download standard-width thumbnail (or original if smaller) via thumburl."""
        assert width in STD_WIDTHS or width == "original"
        pg = self.info([title], width=1920 if width == "original" else width).get(
            title if title.startswith("File:") else "File:" + title)
        if not pg or "imageinfo" not in pg:
            self._add_pending(title, "missing on Commons")
            raise WMError(f"missing {title}")
        ii = pg["imageinfo"][0]
        if width != "original" and ii.get("width", 0) <= width:
            # file smaller than requested: take the largest STANDARD thumbnail below the
            # original width (originals on upload.wikimedia.org are rate-limited for us)
            smaller = [w for w in STD_WIDTHS if w < ii.get("width", 0)]
            if smaller and smaller[-1] >= 250:
                width = smaller[-1]
                pg = self.info([title], width=width).get(
                    title if title.startswith("File:") else "File:" + title)
                ii = pg["imageinfo"][0]
        if width == "original":
            url, sub = ii["url"], "original"
        else:
            url = ii.get("thumburl") or ii["url"]
            sub = str(width) if str(width) in DIRS else "1920"
            if "/thumb/" not in url:
                sub = "original"
        DIRS.setdefault(sub, BASE / sub).mkdir(parents=True, exist_ok=True)
        dest = DIRS[sub] / _safe_name(title)
        if url.split("?")[0].lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            dest = dest.with_suffix(os.path.splitext(urlparse(url).path)[1].lower())
        done = dest.with_suffix(dest.suffix + ".ok")
        if dest.exists() and done.exists():
            self.stats["cache_hits"] += 1
            self._log(type="file", url=url, status=200, attempt=0, cache="hit")
            self._save_stats()
            return dest
        tmp = dest.with_suffix(dest.suffix + ".part")
        try:
            r = self._request("file", "GET", url, stream=True,
                              label="thumbnail" if sub != "original" else "file")
            total = int(r.headers.get("Content-Length", 0))
            n, t0 = 0, time.time()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
                    n += len(chunk)
                    if total > BIG_FILE:
                        ideal = n / BIG_RATE
                        el = time.time() - t0
                        if ideal > el:
                            time.sleep(ideal - el)
            if total and n != total:
                raise WMError(f"incomplete download {n}/{total}")
            tmp.rename(dest)
            done.write_text(str(n))
            self.stats["files_ok"] += 1
            self.stats["bytes_downloaded"] += n
            self._remove_pending(title)
            self.consec_429_files = 0
            return dest
        except WMError as e:
            self.stats["files_failed"] += 1
            if "429" in str(e) or "status=429" in str(e):
                self.consec_429_files += 1
                if self.consec_429_files >= 3:
                    with self._slot("file") as info:
                        info["pause_until"] = time.time() + 300
            self._add_pending(title, str(e)[:200])
            if tmp.exists():
                tmp.unlink()
            raise
        finally:
            self._save_stats()

    def download_url(self, url, dest: Path, label="file"):
        """Download a Commons media URL (e.g. video transcode) obtained from the API."""
        assert urlparse(url).netloc.endswith("wikimedia.org")
        done = dest.with_suffix(dest.suffix + ".ok")
        if dest.exists() and done.exists():
            self.stats["cache_hits"] += 1
            self._save_stats()
            return dest
        r = self._request("file", "GET", url, stream=True, label=label)
        total = int(r.headers.get("Content-Length", 0))
        n, t0 = 0, time.time()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(65536):
                f.write(chunk)
                n += len(chunk)
                if total > BIG_FILE:
                    ideal = n / BIG_RATE
                    el = time.time() - t0
                    if ideal > el:
                        time.sleep(ideal - el)
        done.write_text(str(n))
        self.stats["files_ok"] += 1
        self.stats["bytes_downloaded"] += n
        self._save_stats()
        return dest

    # ---------------- pending queue ----------------
    def _pending(self):
        return json.loads(PENDING_FILE.read_text()) if PENDING_FILE.exists() else {}

    def _add_pending(self, title, reason):
        p = self._pending()
        p[title] = reason
        PENDING_FILE.write_text(json.dumps(p, ensure_ascii=False, indent=1))

    def _remove_pending(self, title):
        p = self._pending()
        if title in p:
            del p[title]
            PENDING_FILE.write_text(json.dumps(p, ensure_ascii=False, indent=1))

    def report(self):
        s = dict(self.stats)
        s["pending"] = self._pending()
        s["login_status"] = "logged_in as " + str(self.user) if self.logged_in else "anonymous"
        return s

    # ---------------- video transcodes ----------------
    def video(self, title, max_height=720):
        """Download the best WebM/MP4 transcode <= max_height (originals are often rate-limited)."""
        title = title if title.startswith("File:") else "File:" + title
        vi = self.video_derivatives(title)
        ders = [d for d in vi.get("derivatives", []) if d.get("height") and d["height"] <= max_height
                and d.get("transcodekey", "").endswith(("webm", "mp4"))]
        if not ders:
            raise WMError(f"no transcode <= {max_height}p for {title}")
        best = max(ders, key=lambda d: (d["height"], d.get("bandwidth", 0)))
        ext = os.path.splitext(urlparse(best["src"]).path)[1] or ".webm"
        dest = DIRS["video"] / (os.path.splitext(_safe_name(title))[0] + ext)
        self.download_url(best["src"], dest, label="file")
        self.license([title])
        return dest, best

    # ---------------- convenience for scouting ----------------
    def scout(self, query, limit=50, width=330, category=False):
        """Search (or category) -> compact rows saved to assets/commons/scout/<slug>.json."""
        res = self.category(query, limit, width) if category else self.search(query, limit, width)
        rows = []
        for t, pg in res.items():
            ii = (pg.get("imageinfo") or [{}])[0]
            rows.append({"title": t, "w": ii.get("width"), "h": ii.get("height"), "mime": ii.get("mime"),
                         "thumb": ii.get("thumburl"), "page": ii.get("descriptionurl")})
        slug = re.sub(r"[^A-Za-z0-9]+", "_", query)[:60]
        (DIRS["scout"] / f"{'cat_' if category else ''}{slug}.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1))
        return rows
