# WORKFLOW — title + sample script → publish-ready video

Phases run in order. Each ends with a **gate**: do not start the next phase until the gate is met.
`$VF` = `../../scripts/vf` run from `projects/<slug>/`. Times are for a ~30-minute film on 4 cores.

| # | Phase | Output | Gate | Detail |
|---|---|---|---|---|
| 0 | Setup | project skeleton, env OK | `vf doctor` clean, PROGRESS.md started | below |
| 1 | Style profile | profile at top of script.md, `length.sample_hook` | profile has hook analysis + must/never rules | docs/01 |
| 2 | Director notes | genre/era/material, real % range, visual direction | notes written before any script text | docs/02 |
| 3 | Research | research/facts.md, chapter outline | enough verified material for the minimum length | docs/03 |
| 4 | Footage scouting | research/shotlist.md, assets/, `vf media scan` | every chapter has the visuals planned for it (or a written gap) | docs/04 |
| 5 | Script + shot list | script.md (HOOK/BODY/CH/S, NAR/VIS) | `vf count --stamp` → GATE: PASS | docs/05 |
| 6 | Voice | out/vo/*.wav | all scenes ≥ 0.93 similarity or reviewed+accepted | docs/06 |
| 7 | Design system | design section in script.md, project.yaml design, custom_gfx.py / anim clips | every design decision filled, graphics previewed | docs/07, 08 |
| 8 | Edit + render | out/ch_*.mp4 | `vf preflight` 0 errors before rendering | docs/08 |
| 9 | Audio | out/mix.wav | music per chapter, voice clearly on top | docs/09 |
| 10 | Review ×1 | issue list, fixes | one full review completed, fixes checked, `vf qa` 0 errors | docs/10 |
| 11 | Deliver | video.mp4, script.md, sources.md, REPORT.md | report sent to the user | docs/11 |

---

## Phase 0 — Setup (10 min)
```bash
bash scripts/setup.sh <lang>                       # ffmpeg check, python deps, fonts, Natural Earth
scripts/vf doctor                                   # tools + env secrets (set / not set)
scripts/vf init projects/<slug> --title "<title>" --lang <lang>
cd projects/<slug>
```
- Put the user's sample script in `research/sample.txt`. Fill `project.yaml` from the user's parameters
  (language, `length.min`, `copyright_level`, voice). Unknown → template defaults.
- If `WIKIMEDIA_*` are set: `$VF commons test` (login, UA, search, cache, one 330 px thumbnail). Record the
  result in PROGRESS.md. Read `docs/wikimedia.md` before any bulk Commons work.
- Gate: doctor shows no MISSING tool; `GEMINI_API_KEY` set (else ask the user — nothing else blocks).

## Phase 1 — Style profile (first, before anything else)
- Read the sample once, completely. `$VF count-sample research/sample.txt` then
  `$VF count-sample research/sample.txt "<last words of the hook>"` → set `length.sample_hook`.
- Write the profile at the top of script.md (docs/01): structure with % per part, hook anatomy sentence by
  sentence, narrator voice, sentence stats, signature phrases, retention devices, pacing, 5–8 must-keep rules,
  3–5 never-do rules.
- Use the profile as the reference. Re-read a relevant sample passage when needed to resolve a gap or
  verify a detail, then update the profile; avoid reloading the full sample (context budget).

## Phase 2 — Director notes (before writing narration)
- From the title: genre AND sub-genre, era, place, the material that exists, the emotion. docs/02's table is
  a starting point to reason from — decide for THIS film: real-footage range for the whole film
  (`director.real_pct: {min, max}`; single chapters may be all archive or all animation), pace, transitions,
  text behaviour, colour, sound, three don'ts, how a long film stays varied across chapters.

## Phase 3 — Research (sub-agents)
- Fan out 2–4 research sub-agents (by language / by period / by people) with the template in docs/03.
  They write `research/notes_<topic>.md`; you merge into `research/facts.md` (fact → source URL → date).
- Draft the chapter outline. Estimate length per chapter; research more where the minimum cannot be met
  with real content. Never pad.

## Phase 4 — Footage scouting (before the script is final)
- Per chapter: what must be seen. Search wide (docs/04 list); make a small initial check, diagnose failures
  and try bounded legitimate fixes before abandoning a source. When YouTube has relevant material, actually
  search/test it with `yt-dlp` in the current environment; do not assume it is blocked. Use Commons thumbnails.
- Every downloaded video: `$VF media scan <file>` (cuts + black/fade ranges) and a contact sheet
  (`$VF media contact`). Prefer **scouting sub-agents** to return shot lists (time ranges, content, people,
  burned-in text, quality). If unavailable or failing, inspect small batches yourself and save the same
  findings to `research/shotlist.md`.
- Register reusable videos in project.yaml `assets` (path, credit, link, license, rights_check, crop, desat).
- Rights groups A/B/C and the `copyright_level` rules: docs/04.
- Gate: every chapter has the pictures the director planned for it (archive, graphics or animation — by
  purpose), the whole film can reach the planned real-footage range, and real gaps are written down for the
  report.

## Phase 5 — Script + shot list
- Write script.md exactly in the format of docs/05 (HOOK / BODY / `### CHn | num | title` / `#### Sxxx` / NAR / VIS).
  Write the words around the strongest shots. One VIS line per sentence lets the cut land exactly when the
  narration names the thing.
- `$VF count` until **GATE: PASS** (hook within ±15 % of the sample hook; total ≥ minimum), then
  `$VF count --stamp`. Hook is now locked. Every later script edit → `$VF count` again.
- Self-check three random passages against the profile's must/never rules; no long sentence copied.

## Phase 6 — Voice
- `$VF tts` (prefer background; execution fallback: CLAUDE.md). Then `$VF tts-report`.
  For each scene under 0.93: read text vs asr in
  `out/vo/<id>.json`; fix with `voice.readings` (katakana/hiragana) or `tts_overrides.yaml`, `$VF tts <ids>`;
  if the take is right and only the transcription differs (kanji vs kana), `$VF tts-accept <id>`.
- Record the total voice duration in PROGRESS.md.

## Phase 7 — Design system
- Design the look for THIS film (docs/07) — there are no presets or templates: colour grade(s), palette,
  fonts, title/chapter/lower-third/credit styles, footage treatment, motion, transitions. Write it into
  script.md and project.yaml `design`; `$VF preflight` lists any decision still missing.
- Author graphics and animation with **Remotion + SVG first** (docs/08), render clips to `assets/anim/`,
  and reference them with `anim:` / `overlay=anim:`. This includes simple maps, charts and cards.
- Before rendering those clips, inspect the actual render server's available CPU/RAM, workload and resource
  limits. Run independent clips in parallel when resources allow, tuning job count and per-job concurrency
  to maximize useful CPU throughput without memory pressure (docs/08); save the allocation in PROGRESS.md.
- Python drawing (`custom_gfx.py` / Pillow / Manim) is allowed only for a documented requirement Remotion
  cannot meet. Record the gap and attempted approach in PROGRESS.md; missing dependencies are not a reason.
- Preview representative frames of every clip, including text bounds, glyphs and the subtitle safe area.
  For an approved Python fallback, also use `$VF gfx-preview <name> k=v`.

## Phase 8 — Edit + render
```bash
$VF plan                 # timeline + subtitles; prints asset errors
$VF preflight            # MUST be 0 errors. Warnings: read each, fix or consciously accept (note why)
$VF render --changed     # prefer background; execution fallback: CLAUDE.md; parallel chapters, subtitles burned in
```
- While chapters render: write `sources_facts.md`, prepare the report, start reviewing finished chapters.

## Phase 9 — Audio
- Music per chapter (docs/09), voice levelled, ducking, loudness −16 LUFS: `$VF audio`.

## Phase 10 — One review (docs/10)
- `$VF final && $VF qa` → `$VF sheets all --every 3`. The main agent personally reviews all sheets in
  small batches and saves JSON issue lists; do not delegate video review to sub-agents.
- Fix identified issues → `$VF plan && $VF preflight && $VF render --changed` as needed → `$VF final && $VF qa`.
  The main agent checks only corrected portions for visual fixes. No second full-video review or 6 s
  whole-film skim is required. Resolve identified issues before delivery and record accepted low-severity notes.
- Style comes first: does it fit this genre, era and story; does anything look generic; is the real/graphics
  share of the whole film inside the range (chapters are free; preflight shows them for information)?

## Phase 11 — Deliver (docs/11)
```bash
$VF final && $VF qa && $VF stats && $VF sources
```
- `REPORT.md` from `templates/REPORT.template.md`; reply to the user (their language) with the summary:
  duration, narration length, genre + visual direction, real/graphics ratio, what was learned from the
  sample, what review fixed, and what they must check (rights, audio, approximate matches).
