# Phase 8 — Edit and render

## Pipeline
```bash
$VF plan                 # out/timeline.json + out/ass_<CH>.ass ; prints asset errors
$VF preflight            # every automated check (docs/10). Must end with 0 errors.
$VF render --changed     # only chapters whose inputs changed; parallel; subtitles burned in; final quality
$VF audio                # out/mix.wav
$VF final                # concat -c copy + AAC  (~1 minute, no re-encode)
$VF qa                   # container, codec, fps, size, durations, frame count, loudness, black frames
```
Why this shape: in the reference production subtitles were burned in a full-film re-encode at the end, so
fixing 1.5 s of black cost a 67-minute export, and one 30-minute film needed 39 chapter renders. Now every
chapter is encoded once at final quality (x264 crf 18, preset medium) with its subtitles; a fix re-renders
only the chapters whose hash changed (timeline items, subtitles, assets, pixel-affecting engine code,
custom_gfx.py, graphics.yaml, project.yaml).

Render runs ~6 frames/s per job on 4 cores (2 jobs × 2 threads). A 30-minute film ≈ 60–80 min for a full
render: start it in the background and keep working (sources, report, reviewing finished chapters).

## Timing rules the engine applies
- Scene = lead 0.15 s + voice + gap 0.30 s (+1.2 last scene of a chapter, + `pause=` — give quote and
  text-heavy scenes time to be read).
- Shots split at sentence pauses when VIS count = sentence count (picture appears when it is named).
- Subtitles: one event per sentence (long ones split at commas), ≤ 2 lines, line breaks only at phrase
  boundaries (BudouX for ja/zh/th, words otherwise), timed to the silences in the voice file.
- Video shots never cross a cut or enter a fade-out; too-short takes are slowed (≥ 0.5×; preflight errors < 0.6×).
- Chapter cards are your `design.chapter_card.gfx`; fades/dissolves come from `design.transitions` and shot options.

## Graphics and animation (built for this film — the engine ships no styles)
Two ways to make non-footage pictures; choose per shot by what the idea needs, not by habit:

**1. Code graphics — `custom_gfx.py`** (`gfx:<name>`; start from templates/custom_gfx.template.py).
Good for: maps, charts, timelines, documents, diagrams, cards, labels — anything data-driven or text-heavy.
- Primitives (`vf.gfx.core`): `canvas`, `text` (always — QA measures its box), `fit_font`, `ramp`/`ease`/`mix`,
  `partial_line`, `photo_bg`, `C.<palette key>`, `F(<font role>, size)`.
- Technical helpers (`vf.gfx.kit`): `shapes()` + `Projector` (Natural Earth maps: world, ISO3 list, US lower 48,
  admin-1), `scale()` for chart axes, `paper()` + `place()` for document reconstructions.
- Structured data in `graphics.yaml`, referenced with `spec=<id>`; inline options override.
- Return RGBA to use it as an overlay on footage: `VIS: TAPE @1:02 | overlay=gfx:<name>`.
- `$VF gfx-list` lists your graphics; `$VF gfx-preview <name> k=v t=3 dur=6` writes one PNG — look at it.
- Cost: frames are drawn in Python per frame; heavy per-pixel work (blurs, big numpy ops) every frame slows the
  render a lot — cache static layers with `functools.lru_cache` and only draw what moves.
- Reference for the quality bar (not a style to copy): `examples/challenger/custom_gfx.py`.

**2. Animation clips — `anim:<file>`** rendered with a dedicated tool (Manim, Remotion, Motion Canvas, Blender,
Three.js/Puppeteer capture, After Effects, Lottie → video…).
Good for: 3D, particles, camera moves, physical simulation, long continuous animated explanations.
Technical requirements (each one cost time somewhere):
- 1920×1080 (or the project size), same fps as the project (default 30; other rates are resampled — judder).
- Length ≥ the shot (clips are never looped; a short clip is slowed down and preflight errors < 0.6×).
  Render a little longer, trim with `@m:ss.s`.
- Full-frame clips: H.264 yuv420p `.mp4`. Clips with transparency for `overlay=anim:`: VP9 `.webm` with
  `-pix_fmt yuva420p` (decoded with libvpx — the native decoder drops alpha) or ProRes 4444 `.mov`. ffmpeg's
  `drawbox` does not write alpha; generate alpha in the tool or with `geq`/`alphamerge`.
- No text in the bottom subtitle block unless the scene is `subs=off`; text in a clip is NOT measured by QA —
  check the safe area yourself on a preview frame.
- Fonts used inside the clip must contain every glyph (CJK!) — render one test frame first.
- Store clips in `assets/anim/`; they count as graphics in the real-footage share and are not colour-graded
  like footage. Keep the source (scene file / project) next to the clip so a fix can be re-rendered.
- Tool not installed? Install it in the session (pip/npm); headless rendering needs no display (Blender
  `-b`, Manim `-qh`, Remotion `npx remotion render`, Puppeteer with the pre-installed Chromium).

## Transitions, grades, motion
- `design.transitions`: `film_in`, `film_out`, `after_card` (`cut`, `fade:<s>`, `dissolve:<s>`); per shot
  `in=` / `out=`. A dissolve blends from the previous shot's last frame.
- `design.grades.<name>` applied per chapter (`grade=` in the chapter header) or shot (`grade=`).
- Stills: `kb=` direction, `zoom=` amount (default `design.motion.still_zoom`); video: `push=`.

## Editing rules (from the original brief, still binding)
- Footage moves by itself — only a very gentle push. Stills never sit dead: slow zoom/pan; fast genres change
  picture every 2–4 s, slow genres may hold 5–8 s.
- Text never covers faces, logos or captions inside the footage (`focus=`, `fit=contain`, or move the stamp).
- Every asset carries its credit for its whole duration (automatic; preflight errors if missing).
- Pictures and on-screen text appear when the narration names them, never more than 0.5 s early or late.
