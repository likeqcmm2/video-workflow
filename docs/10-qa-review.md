# Phase 10 — QA and review (machines first, then eyes — eyes belong to sub-agents)

## Automated checks
`vf preflight` (before rendering) — must end with **0 errors**:

| Check | Catches | Why it exists |
|---|---|---|
| design | any design decision missing (grade, palette, fonts, card, motion, real % range) | no film renders on an assumed style |
| fonts, libass | font family of subtitles/credits/stamps not installed; **glyphs missing** in a graphic's font | libass substitutes silently; decorative fonts lack kanji/diacritics |
| length gate | hook ±15 %, total ≥ min, stamp line | hard rule of the brief |
| voice | missing, placeholder, **narration edited after TTS**, similarity < 0.80 (error) / < 0.93 (warn) | stale or misread voice |
| assets | missing files, unknown sources, GIF as still, **alt fallback in use** (warn) | a silent fallback once rendered an empty card |
| credits | any photo/footage without on-screen credit | every asset must be credited |
| video in-points | beyond file end, **on a cut or black range**, too-short takes (< 0.6× = error), **black frames inside the used segment** | two shots ran into a tape's fade-to-black |
| stills | unreadable, too small for full-frame (`fit=contain`), static too long, same still > 3 times | soft or repetitive pictures |
| graphics | render errors, **text outside the 5 % safe area**, **text in the subtitle block**, overlapping text | an overflowing label was found only by eye |
| subtitles | > 2 lines, over-long lines, a line starting with 、。」ー or small kana, events < 0.6 s | broken Japanese line breaks needed six rounds of fixes |
| ratio | real-footage share of the WHOLE film outside `director.real_pct` (each chapter's share is printed as INFO only — chapters may be all archive or all animation) | genre drift of the film as a whole |
| timing | scenes split by weight (sync to check by eye) | picture ≠ word |
| Wikimedia | pending downloads | missing pictures |

`vf qa` (after `vf final`): size, fps, H.264 yuv420p, AAC, video = audio = timeline duration, exact frame count,
loudness (−16 LUFS ±1, true peak), black frames during photo/footage shots.

## Visual review (two rounds minimum)
```bash
$VF sheets CH1 CH2 CH3 --every 3      # 4x5 tiles per sheet, each labelled "m:ss  S123"; manifest JSON beside them
```
Spawn review sub-agents in parallel, **≤ 2 chapters each** (≈ 4–8 sheets per agent). You never open the
sheets yourself — you read their issue lists. Prompt template:

> You are a demanding viewer reviewing a <GENRE> documentary for <AUDIENCE>. Director notes: <3–5 lines from
> script.md: genre, era, visual direction, pace, real-footage range, don'ts>. Look at every tile of these review sheets:
> <paths>. Tiles are labelled with film time and scene id; `<manifest.json>` gives each tile's source and type,
> and the narration of each scene is in `<script.md>` (NAR lines).
> Check, in this order:
> 1. Style: does it fit this genre, era and story? Anything generic that could belong to any other video?
>    Do graphics, animation and footage feel like one film?
> 2. Text: overlapping text, text over faces/logos/captions in the footage, cut-off or overflowing text,
>    typos, low contrast, subtitle line breaks inside words.
> 3. Picture: distortion, unintended black/blank frames, watermarks, stretched low-res images.
> 4. Match: picture does not show what the narration of that scene says (or arrives late/early).
> 5. Edit: a shot showing a different scene at its start/end (wrong cut), the same picture repeated too often,
>    static or empty stretches, jerky rhythm, inconsistent style between chapters.
> 6. Sensitive images (<graphic_content rule>).
> 7. Boring, confusing or awkward passages.
> Reply ONLY with JSON: `[{"scene": "S123", "t": "4:12", "severity": "high|medium|low", "type": "<check>",
> "issue": "<what is wrong>", "fix": "<concrete suggestion>"}]` — `[]` if nothing. Be literal; do not invent.

Then: fix (script VIS / options / assets / custom graphics) → `vf plan && vf preflight && vf render --changed`.

**Round 2**: `vf final && vf qa` (0 errors) + sheets at 3 s for every chapter re-rendered since round 1 + a
6 s skim of the whole film (`vf sheets all --every 6`) by a FRESH sub-agent (fresh eyes catch what the first
missed). Repeat until a round returns nothing above low severity. Re-read the final script against the style
profile and re-run `vf count` (still ≥ minimum after edits?).

## Accepting a warning
Some warnings are judgement calls (e.g. slowed smoke footage at 0.7×, a 500 px portrait used contained).
Accept consciously and list the accepted ones in PROGRESS.md and the report's "to check" section.
