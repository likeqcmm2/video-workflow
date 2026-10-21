# WORKFLOW — title + sample script → publish-ready video

Phases run in order. Each ends with a **gate**: do not start the next phase until the gate is met.
`$VF` = `../../scripts/vf` run from `projects/<slug>/`. Times are for a ~30-minute film on 4 cores.

| # | Phase | Output | Gate | Detail |
|---|---|---|---|---|
| 0 | Setup | project skeleton, env OK | `vf doctor` clean, PROGRESS.md started | below |
| 1 | Style profile | profile at top of script.md, `length.sample_hook` | profile has hook analysis + must/never rules | docs/01 |
| 2 | Director notes | genre/era/material, real % range, visual direction | notes written before any script text | docs/02 |
| 3 | Research | research/facts.md, chapter outline | enough verified material for the minimum length | docs/03 |
| 4 | Footage scouting | research/shotlist.md, assets/, `vf media scan` | every chapter has its own real visuals (or a written gap) | docs/04 |
| 5 | Script + shot list | script.md (HOOK/BODY/CH/S, NAR/VIS) | `vf count --stamp` → GATE: PASS | docs/05 |
| 6 | Voice | out/vo/*.wav | all scenes ≥ 0.93 similarity or reviewed+accepted | docs/06 |
| 7 | Design system | design section in script.md, project.yaml design, custom_gfx.py / anim clips | every design decision filled, graphics previewed | docs/07, 08 |
| 8 | Edit + render | out/ch_*.mp4 | `vf preflight` 0 errors before rendering | docs/08 |
| 9 | Audio | out/mix.wav | music per chapter, voice clearly on top | docs/09 |
| 10 | Review ×2 | issue lists, fixes | round 2 clean, `vf qa` 0 errors | docs/10 |
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
  (language, `length.min`, `copyright_level`, `graphic_content`, voice). Unknown → template defaults.
- If `WIKIMEDIA_*` are set: `$VF commons test` (login, UA, search, cache, one 330 px thumbnail). Record the
  result in PROGRESS.md. Read `docs/wikimedia.md` before any bulk Commons work.
- Gate: doctor shows no MISSING tool; `GEMINI_API_KEY` set (else ask the user — nothing else blocks).

## Phase 1 — Style profile (first, before anything else)
- Read the sample once, completely. `$VF count-sample research/sample.txt` then
  `$VF count-sample research/sample.txt "<last words of the hook>"` → set `length.sample_hook`.
- Write the profile at the top of script.md (docs/01): structure with % per part, hook anatomy sentence by
  sentence, narrator voice, sentence stats, signature phrases, retention devices, pacing, 5–8 must-keep rules,
  3–5 never-do rules.
- After this the sample is not re-read; the profile is the reference (context budget).

## Phase 2 — Director notes (before writing narration)
- From the title: genre AND sub-genre, era, place, the material that exists, the emotion. docs/02's table is
  a starting point to reason from — decide for THIS film: real-footage range (`director.real_pct: {min, max}`,
  chapter exceptions with reasons), pace, transitions, text behaviour, colour, sound, three don'ts, how a long
  film stays varied per chapter.

## Phase 3 — Research (sub-agents)
- Fan out 2–4 research sub-agents (by language / by period / by people) with the template in docs/03.
  They write `research/notes_<topic>.md`; you merge into `research/facts.md` (fact → source URL → date).
- Draft the chapter outline. Estimate length per chapter; research more where the minimum cannot be met
  with real content. Never pad.

## Phase 4 — Footage scouting (before the script is final)
- Per chapter: what must be seen. Search wide (docs/04 list), probe each source with ONE small request
  before investing (cloud IPs get blocked: YouTube usually is; Commons originals may 429 — use thumbnails).
- Every downloaded video: `$VF media scan <file>` (cuts + black/fade ranges) and a contact sheet
  (`$VF media contact`). Contact sheets are read by **scouting sub-agents**, who return shot lists
  (time ranges, content, people, burned-in text, quality). You keep only `research/shotlist.md`.
- Register reusable videos in project.yaml `assets` (path, credit, link, license, rights_check, crop, desat).
- Rights groups A/B/C and the `copyright_level` rules: docs/04. Sensitive-image rules: docs/04.
- Gate: real material per chapter fits the director's range, or the gap is declared as a chapter exception
  (with the reason) and written down for the report.

## Phase 5 — Script + shot list
- Write script.md exactly in the format of docs/05 (HOOK / BODY / `### CHn | num | title` / `#### Sxxx` / NAR / VIS).
  Write the words around the strongest shots. One VIS line per sentence lets the cut land exactly when the
  narration names the thing.
- `$VF count` until **GATE: PASS** (hook within ±15 % of the sample hook; total ≥ minimum), then
  `$VF count --stamp`. Hook is now locked. Every later script edit → `$VF count` again.
- Self-check three random passages against the profile's must/never rules; no long sentence copied.

## Phase 6 — Voice
- `$VF tts` (background). Then `$VF tts-report`. For each scene under 0.93: read text vs asr in
  `out/vo/<id>.json`; fix with `voice.readings` (katakana/hiragana) or `tts_overrides.yaml`, `$VF tts <ids>`;
  if the take is right and only the transcription differs (kanji vs kana), `$VF tts-accept <id>`.
- Record the total voice duration in PROGRESS.md.

## Phase 7 — Design system
- Design the look for THIS film (docs/07) — there are no presets or templates: colour grade(s), palette,
  fonts, title/chapter/lower-third/credit styles, footage treatment, motion, transitions. Write it into
  script.md and project.yaml `design`; `$VF preflight` lists any decision still missing.
- Build every graphic for this film in `custom_gfx.py` (docs/08: primitives, kit, overlays); complex motion
  (3D, particles, long animated sequences) with an external tool rendered to a clip (`anim:`, docs/08).
  Preview each with `$VF gfx-preview <name> k=v` and look at the PNG yourself (1 image).

## Phase 8 — Edit + render
```bash
$VF plan                 # timeline + subtitles; prints asset errors
$VF preflight            # MUST be 0 errors. Warnings: read each, fix or consciously accept (note why)
$VF render --changed     # background; parallel chapters; subtitles burned in; one encode
```
- While chapters render: write `sources_facts.md`, prepare the report, start reviewing finished chapters.

## Phase 9 — Audio
- Music per chapter (docs/09), voice levelled, ducking, loudness −16 LUFS: `$VF audio`.

## Phase 10 — Review, at least two rounds (docs/10)
- Round 1: `$VF sheets <chapters> --every 3` → spawn review sub-agents (≤ 2 chapters each, template in docs/10)
  → they return JSON issue lists → fix → `$VF plan && $VF preflight && $VF render --changed`.
- Round 2: `$VF final && $VF qa` (0 errors) + sheets at 3 s for every chapter changed since round 1 + a
  6 s skim of the whole film by a fresh sub-agent. Repeat until a round finds nothing to fix.
- Style comes first: does it fit this genre, era and story; does anything look generic; is the real/graphics
  share inside the range (preflight reports it per chapter)?

## Phase 11 — Deliver (docs/11)
```bash
$VF final && $VF qa && $VF stats && $VF sources
```
- `REPORT.md` from `templates/REPORT.template.md`; reply to the user (their language) with the summary:
  duration, narration length, genre + visual direction, real/graphics ratio, what was learned from the
  sample, what review fixed, and what they must check (rights, audio, weak sources, approximate matches).
