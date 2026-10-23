# Phase 4 — Footage scouting (know what you can show before you write)

A 30-minute film needs a lot of material. Make a shot need list per chapter; every chapter needs its own
pictures; do not repeat one still many times.

## Where to look (check access, diagnose failures, then choose sources)
| Source | Notes from production |
|---|---|
| NASA Image & Video Library (`vf nasa search/fetch`) | public domain, excellent originals; no endorsement implied |
| Internet Archive (`vf ia search/files/fetch`) | great for government films; CHECK the licence field and watermarks — some scans carry stock-house watermarks + timecode (unusable) |
| Wikimedia Commons (`vf commons …`) | only through `engine/vf/wm_client.py`; images as standard thumbnails, videos as transcodes (docs/wikimedia.md) |
| US National Archives, Library of Congress, .gov (NOAA, USGS…), ESA/ESO, EU AV Service | public domain or open; check each item |
| Museums open access (Met, AIC, Cleveland, Smithsonian, Rijksmuseum) | art, artefacts |
| National archives of the country concerned (e.g. Japan Search, ColBase, NDL, GSI, kantei.go.jp) | local material |
| YouTube / Vimeo (yt-dlp) | news, reports and CC-licensed clips: when relevant, actually search/test with `yt-dlp` in the current environment. Do not infer access from another machine or a single failed video. Never use cookies, proxies or other IPs to bypass blocking. |
| Newspapers / official sites | screenshot headline + photo + masthead + date (group B) |
| Free stock (Pexels, Mixkit, Coverr, Pakutaso) | generic background only, never as a substitute for the real thing |

## Access checks and bounded recovery
- Select sources by relevance to the shot need, not by which source has a built-in helper. For relevant
  YouTube material, run an actual `yt-dlp` search/metadata check before ruling it out; for example:
  `yt-dlp --skip-download --dump-single-json "ytsearch3:<topic keywords>" > research/youtube_candidates.json`.
  Inspect a compact summary, then test selected URLs; metadata success alone does not confirm media download.
- Start with a small check. On failure, inspect the error and distinguish an unavailable/private item,
  outdated tool or missing dependency, transient network failure and actual access denial.
- Apply legitimate fixes that fit the error: update `yt-dlp` when outdated, install reported dependencies,
  retry a transient failure with backoff, or test a different relevant public URL. Use a bounded recovery
  budget (up to three diagnostic/recovery attempts per source pass); stop retrying an explicitly denied
  resource. Do not treat one failed item as proof the whole service is unusable.
- Preserve existing source-specific rate limits and Retry-After requirements. Do not use cookies, proxies
  or IP changes to bypass blocking. If access still fails, log the commands, concise errors and fixes tried
  in PROGRESS.md/shotlist, switch to another relevant source and continue the project.

## Video scouting
```bash
$VF media scan assets/ia/film.mp4          # cuts + black/fade ranges -> assets/scenes/film.json (ALWAYS)
$VF media contact assets/ia/film.mp4 8     # one tile every 8 s -> assets/contact/film_NN.jpg
$VF media contact assets/ia/film.mp4 2 300 420   # dense sheet for a promising range
```
The renderer never crosses a cut or plays into a fade-to-black; if a take is too short it slows it down,
and preflight errors below 0.6×. Choose in-points inside clean ranges.

### Scouting review (prefer sub-agents; use small batches yourself if unavailable)
> You are scouting footage for a documentary about <TOPIC>. Look at these contact sheets (each tile is labelled
> with its time in the source): <paths>. Source file: <path>, cut/black data: assets/scenes/<stem>.json.
> Return a markdown table: `| start–end (s) | what is visible | people (only if certain) | burned-in text/logos
> | quality 1–5 | usable for (chapter/topic) |`. Be literal: describe only what you see. Flag watermarks,
> stock-house logos and timecodes. No commentary beyond the table and a 3-line summary.
Merge their tables into `research/shotlist.md`. If sub-agents are unavailable or fail, use the same
checklist yourself on small batches and save the table; do not skip scouting.

## Rights groups
- **A** open archives, free use (public domain, CC0, CC BY/BY-SA with attribution).
- **B** screenshots of articles/official posts — keep masthead and date visible.
- **C** copyrighted material (broadcasts, reportage, films) — only as `copyright_level` allows:
  `safe` = never; `balanced` = short excerpts when nothing else can show it; `max` = prefer real footage
  (the user checks rights). Each C excerpt ≤ ~15 s, on-screen source for its whole duration, and
  `rights_check: true` → "CẦN KIỂM TRA QUYỀN" in sources.md.

## Standards
- Real people: verify identity (homonyms!) and period; unsure → do not use. Photos from another year get a
  stamp like 「写真は2012年」 / "photo taken 2012".
- Prefer video over stills when both exist. 1–3 candidates per scene, pick the best.
- Watermarks of stock sites, aggregator channels or ads: never. The original broadcaster's logo: keep, note it.
- Low resolution is fine for irreplaceable archive: the engine contains it on a blurred background
  (`fit=contain`) or frames small footage; never stretch.
- Verify what each file shows before scripting it; titles and metadata are not enough.
- GIFs: `$VF media gif2mp4 file.gif 0.4 2` (slow, loop) and use it as `vid:`; label slow motion on screen.

After scouting compare with the director's ratio. Short of real material → search again with other keywords
and sources before filling with graphics; still short → write it down for the report.
