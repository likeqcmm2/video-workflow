# Phase 7 — Design system (define once, use everywhere)

Write a "Design system" section in script.md and the matching `project.yaml design` values:

| Item | Where | Notes |
|---|---|---|
| Look (grade + texture) | `design.look` | presets in `engine/vf/look.py`: documentary_dark (reference film), history_warm, mystery_dark, science_clean, business_clean, vivid; tune with `design.look_params` (desat, contrast, warm, vignette, grain, gfx_grain, bottom) |
| Palette | `design.palette` | bg, text, muted, accent (one strong accent), secondary (1 support colour), paper/ink (documents), line, card_bg |
| Fonts (≤ 2 families) | `design.fonts`, `design.subtitle.font` | Noto Serif (headlines, quotes) + Noto Sans (labels, subtitles). Per language defaults in config.py; download with `scripts/setup.sh <lang>` |
| Subtitles | `design.subtitle` | size 50 @1080p (ja), max_chars/line 24 (+4 slack); latin ~42; 2 lines max; outline + shadow |
| Title card, chapter card | `gfx:title`, automatic chapter cards | `design.chapter_card` (enabled, duration 3.6 s) — fades through black |
| Lower third | `lt=Name／Role` | blurred dark plate bottom-left, serif name + sans role |
| Credits | automatic | small, top-right, whole shot duration: 写真：/映像：… or Photo:/Footage: … |
| Date/place stamp | `stamp=` | small, top-left |
| Footage treatment | look + `assets.<ID>.crop/desat` | 4:3 or small footage centred on its own blurred copy, small (<360p) in a thin frame; crop burned-in black borders |
| Motion | `design.kenburns`, `kb=` | stills zoom ≤ 10 %; fast genres change picture every 2–4 s, slow genres hold 5–8 s with slow motion |
| Safe area | `design.safe_margin` 5 % | preflight checks every graphic's text boxes, and that no graphic text enters the subtitle block |

Keep it consistent across all chapters (colour, fonts, motion). Check with `vf gfx-preview` before rendering.
