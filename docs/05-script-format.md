# Phase 5 — script.md format, shot list and the length gate

script.md holds, in order: Style profile → Director notes → Design system → the script. The engine reads only
the script part (from `## HOOK`).

```markdown
## HOOK
#### S001
NAR: この街では、毎日多くの人が列車を利用しています。
VIS: vid:assets/footage/station.mp4 @0:05.0 | credit=映像：提供元

#### S002 | pause=1.0
NAR: 今回は、その交通網の仕組みを見ていきます。
VIS: anim:assets/anim/title.mp4 @0:00.0

## BODY
### CH1 | 第1章 | 路線のつながり
#### S101
NAR: 地図の上で、二つの地点を結んでみましょう。
VIS: anim:assets/anim/map_route.mp4 @0:00.0
```

- Scene ids: `S0xx` hook, `S1xx` chapter 1, `S2xx` chapter 2 … (stable ids = stable voice files).
- 1–2 spoken sentences per scene. Write for the ear. Numbers stay as digits in NAR (subtitles show digits; TTS
  gets words automatically). Fixed pronunciations go to `project.yaml voice.readings`.
- **One VIS line per sentence** → the cut lands in the pause between the sentences, so the picture appears
  when the narration names it (≤ 0.5 s rule). Other counts → split by weight `w=`.
- Every sentence has a fitting visual. Write the narration around the strongest shots.

## VIS sources
| Source | Meaning |
|---|---|
| `CLIP @12:34.5` | registered video `CLIP` (project.yaml `assets`), in-point m:ss.s |
| `vid:assets/x.mp4 @1:02` | any local video (needs `credit=`) |
| `img:assets/x.jpg` | any local image (needs `credit=`, or `credit=none` for own material) |
| `nasa:S86-38989` | NASA image fetched with `vf nasa fetch` |
| `cm:File title.jpg` | Wikimedia Commons file fetched with `vf commons fetch` (credit from licence metadata) |
| `gfx:<name>` | Python fallback graphic, only for a documented Remotion capability gap; or a thin adapter loading Remotion-rendered assets (docs/08) |
| `anim:assets/anim/x.mp4` | preferred: graphic/animation rendered with Remotion + SVG; other tools only for documented Remotion capability gaps — counts as graphics, not graded like footage (docs/08) |

## Shot options (`| key=value`)
| Option | Applies to | Effect |
|---|---|---|
| `kb=in/out/l/r/u/d/none` | stills | Ken Burns: zoom in/out, pan left/right/up/down (default `in`) |
| `fit=cover/contain` | stills | fill the frame / whole picture on its own blurred copy (default by aspect) |
| `focus=0.5,0.3` | stills (cover) | crop centre (x,y 0–1) — keep faces in frame |
| `stamp=…` | any | small date/place line (corner from `design.stamp.position`) |
| `lt=Name／Role` | any | lower third (name + role; look from `design.lower_third`) |
| `credit=…` / `credit=none` | any | override the automatic on-screen credit |
| `dim=0.2` | any | darken (for quiet moments) |
| `grade=<name>` | any | use another grade from `design.grades` for this shot (default: chapter's, else `main`) |
| `zoom=0.12` | stills | Ken Burns amount for this shot (default `design.motion.still_zoom`) |
| `push=0.04` | video | slow push-in amount (default `design.motion.video_push`; 0 = none) |
| `in=fade:0.5` / `in=dissolve:0.8` / `out=fade:1.0` | any | transition into / out of this shot (`cut` = none) |
| `overlay=gfx:<name>` / `overlay=anim:<file>` | any | composite an RGBA graphic or an alpha clip over the shot (`overlay_in=` seconds into the clip) |
| `class=real/graphic` | any | override how the shot counts in the real-footage share (e.g. a filmed reconstruction) |
| `w=1.5` | multi-shot scenes | relative duration when not split by sentences |
| `min_speed=0.5` | video | lowest allowed slow-down (preflight still errors < 0.6) |
| `cross_cuts=1` | video | the detected "cut" after the in-point is a flash/explosion, not an edit — verified on a dense contact sheet; black ranges are still respected |
| `alt=src;k=v;k=v` | any | fallback if the primary is missing — preflight WARNS; fix before delivery |
| `spec=<id>` | gfx | parameters from `graphics.yaml` (lists, rows) — inline options override |
| `allow_low=1` | gfx | text may enter the subtitle zone (only for scenes without subtitles) |
| `\N` | text params | line break |

Scene header options: `#### S123 | pause=1.5` (extra silence after the scene), `subs=off` (no subtitles for
this scene — e.g. when the picture already shows the same words; nothing is hidden automatically).
Chapter header options: `### CH3 | 第3章 | 交通の変化 | card=none` (no chapter card), `card_dur=4`,
`grade=<name>` (grade for every shot of the chapter).

## Length gate (hard stop before any voice work)
```bash
$VF count            # HOOK x (sample y, allowed a–b) | BODY | per chapter | TOTAL | GATE: PASS/FAIL
$VF count --stamp    # only when PASS: writes "Length check: … — PASS (time)" at the end of script.md
```
- Hook outside ±15 %: rewrite the hook to the sample's form (not to gain length).
- Total short: **only the body grows** — more real content in thin chapters (see per-chapter numbers) or a new
  chapter; go back to research if needed. Never repeat ideas, stretch sentences or over-summarise.
- Any later edit of NAR → `$VF count` again; below minimum → add to the body before voice/render.
