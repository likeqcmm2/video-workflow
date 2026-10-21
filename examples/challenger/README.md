# Reference production — チャレンジャー号爆発事故の真相

Title: 打ち上げ73秒後に空中爆発。前夜から技術者が「飛ばすな」と警告していたチャレンジャー号爆発事故の真相
Japanese, 32:35.8, 10,351 narration characters (hook 465 vs sample 421), 229 scenes, voice 29:55 (Gemini TTS,
voice Arlo, mean back-transcription similarity 0.990), real footage/photos 60 % / graphics 40 % of shot time.
The client rated the result very good in every respect. This folder is the quality bar — not a look to copy: its dark, desaturated, grainy grade and serif typography
were chosen for a 1986 TV-archive disaster story. Another title, era or genre needs its own design.

| File | What it shows |
|---|---|
| `project.yaml` | registered footage with crop/desaturation, chapter music, readings, real-footage range with two declared chapter exceptions, and the design THIS film chose (grade, palette, fonts) |
| `script.md` | style profile (Vietnamese notes) + director notes + design system + the full script with VIS lines |
| `custom_gfx.py` | 30 project-specific graphics: mechanism diagrams (field joint, O-ring, booster), datasets (Dalal 1989 temperature/damage), reconstructed documents labelled 再現, maps, cards |
| `research_facts.md` | research fact sheet with sources |
| `sources_facts.md` | fact → source table per scene + "handled with care" notes |
| `REPORT.md` | the final report delivered to the client (Vietnamese) |
| `credits_for_description.txt` | attribution lines for the video description |

Media (≈ 2.2 GB) is not in git. To rebuild, fetch the assets listed in `sources_facts.md`/`REPORT.md`
(NASA ids via `vf nasa fetch`, Commons titles via `vf commons fetch`, the Internet Archive films via `vf ia fetch`,
music via `vf music fetch`), then `vf media scan` each video and follow WORKFLOW.md from Phase 6.

## Engine parity check
The current engine re-rendered HOOK and chapter 2 from the same script, assets and voice files:
HOOK PSNR 40.2 dB against the delivered video (visually identical); chapter 2 pictures identical, the only
differences being subtitle line breaks (216 of 229 scenes break exactly as delivered; the other 13 break at
phrase boundaries that are equally or more natural). Final export is now a stream copy instead of a re-encode,
so picture quality is one encode generation better than the delivered file.

## What the new automated QA finds in this delivered film
The reference passed two visual review rounds. `vf preflight` on it still reports:
- **8 shots where the take is shorter than the scene** (S109, S126, S204, S401, S427, S702, S713, S818): the old
  renderer slowed them to 0.5× and ran across the next cut. Verified for S427: in-point 15:06.5, real cut at
  15:07.04 — the first half-second shows the previous shot. Fix: in-point after the cut, or two VIS lines.
- **S410** temperature card: the right end of the label enters the 5 % safe margin (x = 1885 > 1824).
- Warnings: 500 px Commons photos shown full-frame (S327, S414, S603, S703, S706 → `fit=contain` or a larger
  file), several takes slowed 0.65–0.8× (acceptable for smoke and launch footage), five low-similarity voice
  takes that were checked by hand (kanji/kana spelling only).
These are exactly the defects machines see better than eyes; new productions get them before rendering.

## Real-footage share
Director range 50–80 % real. Preflight reports real 60 % / graphics 40 % for the film. CH2 (the field-joint
mechanism) and CH3 (the night-before teleconference, never filmed: 21 % real) are declared in
`director.chapter_exceptions` with their reasons; every other chapter is inside the range ± 15.
