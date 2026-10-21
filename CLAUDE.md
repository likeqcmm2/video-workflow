# Video Workflow — instructions for the AI agent

This repository turns **a video title + a sample script** into a publish-ready documentary video
(`out/video.mp4`), plus `script.md`, `sources.md` and a short report, autonomously.
The quality bar is the reference production in `examples/challenger/` (32-minute Japanese documentary);
every rule here exists because that production paid for it in time or tokens (`docs/lessons-learned.md`).

## How a job arrives
The user sends: this repo's URL, a **title**, a **sample script** (file or pasted text) and optionally
parameters (language, minimum length, copyright level, graphic-content level, voice). Anything not given
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
  motion: you design every film's look from scratch (docs/02, docs/07). The Challenger example shows the
  quality bar, not a look to copy. Preflight errors until every design decision is written down.
- Every fact comes from research with a source; every asset has an on-screen credit and a row in sources.md.
- Hook length = sample hook ±15 % and is locked once the length gate passes; only the body grows.
- No gore, bodies, injured victims, child victims. Reconstructions are labelled as reconstructions.
- **Never weaken a QA check to get a green result.** Fix the content. If the engine is wrong, fix the engine,
  then run `bash tests/run_tests.sh`.

## Secrets (environment variables only)
`GEMINI_API_KEY` (TTS + ASR), `WIKIMEDIA_USER_AGENT`, `WIKIMEDIA_BOT_USER`, `WIKIMEDIA_BOT_PASSWORD`.
Check with `scripts/vf doctor` (prints set / not set, never values). Never echo, log, commit or write them
into any file. If `GEMINI_API_KEY` is missing, stop and ask the user to add it to the environment's
secrets/variables (in Claude Code on the web: environment settings). Wikimedia works anonymously
(slower) when its credentials are missing — note that in PROGRESS.md and continue.

## Sub-agents (use them — they keep images and raw search results out of your context)
- **Visual review** of rendered sheets (Phase 10) — always delegated, never read review sheets yourself.
- **Footage scouting** contact sheets (Phase 4) and **research fan-out** (Phase 3).
Prompt templates: `docs/10-qa-review.md`, `docs/04-footage.md`, `docs/03-research.md`.
Sub-agents return compact text/JSON; they never edit project files unless told to.

## Engine quick reference (run inside the project dir: `projects/<slug>/`)
```
../../scripts/vf doctor | init | count [--stamp] | count-sample | tts | tts-report | tts-accept
                 media scan|contact|images|gif2mp4 | commons ... | nasa ... | ia ... | music fetch
                 plan | preflight | gfx-preview | render --changed | audio | final | qa | sheets | stats | sources
```
Long jobs (`tts`, `render`, `final`) run in the background (`run_in_background`); you get notified when they
finish — do not poll, do other work meanwhile (writing sources/facts, reviewing finished chapters).

## State survives context resets only in files
Keep `projects/<slug>/PROGRESS.md` current after every phase: what is done, decisions, the next action,
open issues. After a context reset, read PROGRESS.md and WORKFLOW.md — not old transcripts.
