# Phase 5 — script.md format, shot list and the length gate

script.md holds, in order: Style profile → Director notes → Design system → the script. The engine reads only
the script part (from `## HOOK`).

```markdown
## HOOK
#### S001
NAR: 1986年1月28日午前11時38分、アメリカ・フロリダ州の青空に、白い煙の柱がまっすぐに伸びていきました。
VIS: TAPE @5:19.0 | stamp=1986年1月28日　午前11時38分（米東部時間）　フロリダ州

#### S012 | pause=3.0
NAR: 今回は、チャレンジャー号爆発事故の真相を解き明かしていきます。
VIS: gfx:title | text=チャレンジャー号爆発事故 | kicker=1 9 8 6 . 1 . 2 8 | sub=打ち上げ73秒後の空中分解

## BODY
### CH1 | 第1章 | 夢の宇宙船
#### S101
NAR: まず、チャレンジャー号が飛び立つまでの時代背景から見ていきましょう。1981年4月、…
VIS: nasa:S81-30498 | kb=in
VIS: nasa:S81-30505 | stamp=1981年4月12日　コロンビア号（STS-1）
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
| `TAPE @12:34.5` | registered video `TAPE` (project.yaml `assets`), in-point m:ss.s |
| `vid:assets/x.mp4 @1:02` | any local video (needs `credit=`) |
| `img:assets/x.jpg` | any local image (needs `credit=`, or `credit=none` for own material) |
| `nasa:S86-38989` | NASA image fetched with `vf nasa fetch` |
| `cm:File title.jpg` | Wikimedia Commons file fetched with `vf commons fetch` (credit from licence metadata) |
| `gfx:<template>` | library graphic (docs/08) or `custom_gfx.py` function |

## Shot options (`| key=value`)
| Option | Applies to | Effect |
|---|---|---|
| `kb=in/out/l/r/u/d/none` | stills | Ken Burns: zoom in/out, pan left/right/up/down (default `in`) |
| `fit=cover/contain` | stills | fill the frame / whole picture on its own blurred copy (default by aspect) |
| `focus=0.5,0.3` | stills (cover) | crop centre (x,y 0–1) — keep faces in frame |
| `stamp=…` | any | small date/place line, top-left |
| `lt=Name／Role` | any | lower third (name + role) |
| `credit=…` / `credit=none` | any | override the automatic on-screen credit |
| `dim=0.2` | any | darken (for quiet moments) |
| `w=1.5` | multi-shot scenes | relative duration when not split by sentences |
| `min_speed=0.5` | video | lowest allowed slow-down (preflight still errors < 0.6) |
| `cross_cuts=1` | video | the detected "cut" after the in-point is a flash/explosion, not an edit — verified on a dense contact sheet; black ranges are still respected |
| `alt=src;k=v;k=v` | any | fallback if the primary is missing — preflight WARNS; fix before delivery |
| `spec=<id>` | gfx | parameters from `graphics.yaml` (lists, rows) — inline options override |
| `allow_low=1` | gfx | text may enter the subtitle zone (only for scenes without subtitles) |
| `\N` | text params | line break |

Scene header options: `#### S123 | pause=1.5` (extra silence after the scene), `subs=off/on` (force
subtitles off/on; default off only for quote cards that show the same words).
Chapter header options: `### CH3 | 第3章 | 運命の前夜 | card=none` (no chapter card), `card_dur=4`.

## Length gate (hard stop before any voice work)
```bash
$VF count            # HOOK x (sample y, allowed a–b) | BODY | per chapter | TOTAL | GATE: PASS/FAIL
$VF count --stamp    # only when PASS: writes "Length check: … — PASS (time)" at the end of script.md
```
- Hook outside ±15 %: rewrite the hook to the sample's form (not to gain length).
- Total short: **only the body grows** — more real content in thin chapters (see per-chapter numbers) or a new
  chapter; go back to research if needed. Never repeat ideas, stretch sentences or over-summarise.
- Any later edit of NAR → `$VF count` again; below minimum → add to the body before voice/render.
