# Video Workflow — instructions for the AI agent

This repository turns **a video title + a sample script** into a publish-ready documentary video
(`out/video.mp4`), plus `script.md`, `sources.md` and a short report, autonomously.

## How a job arrives
The user sends: this repo's URL, a **title**, a **sample script** (file or pasted text) and optionally
parameters (language, minimum length, copyright level, voice). Anything not given
uses the technical defaults in `templates/project.template.yaml` (language, length, rights levels, voice —
never visual style). Work end-to-end without asking, unless you are completely blocked (e.g. a required
secret is missing).

## Read this first, then only what the current phase needs
1. `WORKFLOW.md` — the phases, their outputs and their **gates**. Follow it in order.
2. Open a `docs/NN-*.md` file when you reach that phase (not all at once — context is a budget).
3. `docs/context-budget.md` — rules that keep a 30-minute production inside one session.

## Non-negotiables
- **Quality first.** Speed-ups are only acceptable when they cost (almost) nothing in quality.
- The sample script decides the **words** (voice, rhythm, hook form, endings). The title — its genre, sub-genre,
  era, place and the material that exists — decides the **pictures** (real-footage range, pace, colour grade,
  typography, graphics, animation, transitions).
- **This repo prescribes technique, not style.** It records how to do things reliably and the technical traps
  that cost time or tokens. It has no colour presets, no graphics templates, no default fonts and no default
  motion: design every film's look from scratch (docs/02, docs/07). Preflight errors until every design
  decision is written down.
- Every fact comes from research with a source; every asset has an on-screen credit and a row in sources.md.
- Hook length = sample hook ±15 % and is locked once the length gate passes; only the body grows.
- **Never weaken a QA check to get a green result.** Fix the content. If the engine is wrong, fix the engine,
  then run `bash tests/run_tests.sh`.

## Graphics and animation tool priority
- **Use Remotion + SVG first for all newly authored graphics and animation**, including maps, charts,
  timelines, diagrams, documents, title/chapter cards, lower thirds and overlays. Design for this film.
- Use Python drawing (`custom_gfx.py`, Pillow/OpenCV or Manim) **only when Remotion cannot meet a concrete
  requirement**. Record the requirement, what was tried and why Remotion cannot satisfy it in PROGRESS.md.
  Simplicity, familiarity, existing Python helpers, or Remotion not being installed are not fallback reasons;
  install the required Node/Remotion dependencies first. Other specialist tools also require a documented
  Remotion capability gap (for example, an essential 3D simulation).
- Render Remotion scenes to clips in `assets/anim/`, keep their source beside them, and use `anim:<file>` or
  `overlay=anim:<file>` (docs/08). Python engine orchestration, QA and thin adapters that load Remotion-rendered
  assets remain supported; this priority governs visual authoring, not the engine implementation language.

## Secrets (environment variables only)
`GEMINI_API_KEY` (TTS + ASR), `WIKIMEDIA_USER_AGENT`, `WIKIMEDIA_BOT_USER`, `WIKIMEDIA_BOT_PASSWORD`.
Check with `scripts/vf doctor` (prints set / not set, never values). Never echo, log, commit or write them
into any file. If `GEMINI_API_KEY` is missing, stop and ask the user to add it to the environment's
secrets/variables (in Claude Code on the web: environment settings). Wikimedia works anonymously
(slower) when its credentials are missing — note that in PROGRESS.md and continue.

## Sub-agents (use them — they keep images and raw search results out of your context)
- **Visual review** of rendered video/sheets (Phase 10): one full review, performed personally by the main
  agent. Do not delegate video review to sub-agents. Review small batches and save JSON issue lists to files.
  Fix identified issues and check only the corrected portions; no second full-video review is required.
- **Footage scouting** contact sheets (Phase 4) and **research fan-out** (Phase 3).
Sub-agent prompts: `docs/04-footage.md`, `docs/03-research.md`. Main-agent review checklist: `docs/10-qa-review.md`.
Sub-agents return compact text/JSON; they never edit project files unless told to.

## Engine quick reference (run inside the project dir: `projects/<slug>/`)
```
../../scripts/vf doctor | init | count [--stamp] | count-sample | tts | tts-report | tts-accept
                 media scan|contact|images|gif2mp4 | commons ... | nasa ... | ia ... | music fetch
                 plan | preflight | gfx-preview | render --changed | audio | final | qa | sheets | stats | sources
```
Run long jobs (`tts`, `render`, `final`) in the background and use completion notifications when supported.
If notifications are unavailable, check process status and short log tails at spaced intervals (start around
30–60 s and back off for long jobs). If background execution is unavailable, use a foreground execution
session with bounded waits. Do other independent work when possible; avoid rapid or repetitive polling.

## State survives context resets only in files
Keep `projects/<slug>/PROGRESS.md` current after every phase: what is done, decisions, the next action,
open issues. After a context reset, read PROGRESS.md and WORKFLOW.md — not old transcripts.
