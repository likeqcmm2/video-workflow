# Lessons learned — reference production post-mortem → rules in this repo

Reference: "チャレンジャー号爆発事故の真相", 32:36, 10,351 characters, 229 scenes, built in one session
(6 h 50 min wall clock, 977 turns, 502 tool calls, ~347 M input tokens, peak context 783 k → compacted).
The result was good; the path was expensive. Each row below is a measured cost and the fix now built in.

| What happened | Cost | Root cause | Now |
|---|---|---|---|
| 39 chapter renders for 9 chapters; two 67-min final exports, the second to fix 1.5 s of black | ~3 h | subtitles burned only in a full-film final re-encode; no change tracking | per-chapter render with subtitles burned in, one final-quality encode, `concat -c copy` final (~1 min); `render --changed` via input hashes (`render.py`) |
| Black frames at S615/S435 (tape faded to black) | 2 re-renders + 1 export | scene file had cuts only, no fades | `media scan` stores cuts AND black ranges with fade-onset detection; reader never enters them; preflight runs blackdetect on every used segment (`media.py`, `qa.py`) |
| Empty card at S809 | 1 re-render | alt fallback for a GIF dropped its parameters silently | missing media is an error; alt fallback warned; GIF → `media gif2mp4` (`assets.py`) |
| Text overflow in one graphic | 1 re-render | no bounds check | every text box recorded; preflight checks safe area, subtitle block, overlaps (`gfx/core.py`, `qa.py`) |
| Wrong Commons document, wrong date/place stamps | rework late | asset chosen by title/metadata | rule: look at the file; scouting agents describe only what they see (docs/04) |
| Japanese subtitle breaks inside words, ~6 rounds | many turns + images | hand-made scoring rules | BudouX phrase segmentation; preflight checks line starts (`subtitles.py`) |
| Commons originals 429 / Retry-After 600 | hours of waiting | requested originals from a cloud IP | standard thumbnails for images, transcodes for video, from the start (docs/wikimedia.md) |
| YouTube blocked; watermarked IA scans | wasted searches/downloads | no early probe | probe each source with one request; check watermarks on the contact sheet before downloading more |
| TTS style prompt read aloud → 229 scenes regenerated | 2× TTS cost | instructions inside the TTS text | send only narration (docs/06) |
| ASR refused 3 scenes | manual fallback | single ASR model | automatic fallback list `voice.asr_models` |
| API key blocked on the command line | retries | secret in a command / in the prompt file | secrets only as environment variables; never in prompts, files or commands |
| `pkill -f` killed its own shell ×3, sed delimiter error, KeyError on timeline | small retries | shell hygiene, schema forgotten after compaction | docs/context-budget.md §10; schema notes in PROGRESS.md |
| 119 images, 46 polling turns, raw JSON dumps; 783 k context | most of the token bill | everything in one context | sub-agents for images and research; background jobs without polling; compact command output (docs/context-budget.md) |
| Footage slowed to 0.5× crossing a cut (S427 etc.), 500 px photos full-frame, a label in the 5 % margin | not noticed by eye | no machine check | preflight errors < 0.6× and checks still resolution and safe area — the new QA finds these in the reference itself (examples/challenger/README.md) |

What worked and is kept unchanged: the style-profile-first method, the hard length gate with a locked hook,
scouting before writing, one TTS call per scene with back-transcription, sentence-aligned cuts and subtitles,
a colour grade designed for the film's era and material (its parameters are now generic grade controls, its
values belong to that film only), contained archival footage on blurred backgrounds, on-screen credits,
chapter music with ducking, two review rounds.

Second lesson (after the first version of this repo): built-in colour presets and a graphics template library
pulled every film towards the same look — one "documentary" preset cannot fit a 1940s war film, a 1986 TV-era
disaster and a modern tech story. The repo now keeps only technique and technical traps; every film designs its
own grade, typography, graphics and animation, and preflight refuses to render until those decisions exist.
