# Wikimedia Commons — mandatory rules (condensed Appendix A)

**All** automated requests to the Commons Action API, upload.wikimedia.org and thumb.php go through
`engine/vf/wm_client.py` (via `vf commons …`). No other code may call Wikimedia. No HTML scraping.

Identity: `WIKIMEDIA_USER_AGENT` = descriptive bot UA with contact (e.g.
`MyVideoBot/1.0 (https://commons.wikimedia.org/wiki/User:Me; bot)`); the client appends the library version.
Never a browser UA or the library default. Login with a Bot Password (`WIKIMEDIA_BOT_USER` = `User@BotName`,
`WIKIMEDIA_BOT_PASSWORD`) only for API sessions; cookies stay in `assets/commons/private/` (0700, never in git,
logs or reports). Login failure → anonymous mode with slower limits; note it in PROGRESS.md.

Client behaviour (already implemented — do not bypass):
- One shared, file-locked rate limiter for every process: API ≥ 0.5 s apart logged in (1 s anonymous), files
  ≥ 1 s (2 s); 5 s after an API answer slower than 1 s; > 20 MB files at ~2 MB/s.
- 429: obey `Retry-After` (+2 s) or back off 5→10→20→40→80 s; double the gap (≤ 10 s) and relax after 20
  successes; 3 consecutive file 429s → pause all Commons traffic ≥ 5 min. 403: stop that resource, log, never
  change UA/IP. 5xx: wait ≥ 60 s, bounded retries. Max 5 tries per file → pending queue.
- API responses cached by request hash; files cached by name+width; licence metadata (extmetadata) only for
  shortlisted files, saved to `assets/commons/metadata/`.
- Logs: `assets/commons/logs/requests.jsonl` (no secrets); `vf commons stats` / `vf stats` for the report.

Production lessons:
- **Images: standard thumbnail widths only** (20 40 60 120 250 330 500 960 1280 1920 3840) via `thumburl`;
  scouting 250/330, final 1920 (3840 only for deep zooms). Files narrower than the request: the largest standard
  width below the original. From a cloud IP the ORIGINALS on upload.wikimedia.org returned 429 with
  Retry-After 600 repeatedly while thumbnails worked — do not fight it, use thumbnails.
- **Videos: transcodes** (`vf commons video <title> 720` picks the best ≤ 720p WebM/MP4 derivative).
- Verify the picture itself: titles/metadata can be wrong (a "report front page" was a Senate hearing cover).
- Read the policies once per job if anything seems to have changed: Wikimedia_APIs/Rate_limits, Robot_policy,
  Common_thumbnail_sizes, API:Imageinfo, User-Agent_policy. Official policy wins over these numbers.

Before rendering: only shot-list files downloaded large, all present and readable, licences recorded, no
pending queue (preflight checks the last three).
