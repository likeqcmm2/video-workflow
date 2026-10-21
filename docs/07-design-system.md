# Phase 7 — Design system (designed for THIS film — the engine assumes no style)

Nothing visual has a default. Design the look from the director notes: genre and sub-genre, era, place,
the material you actually found, the emotion. A 1940s newsreel story, a 1986 TV-archive disaster and a
2020s tech story need different colour, texture, typography and motion, even inside one genre. Write the
design into script.md ("Design system" section) and into `project.yaml design`. Preflight errors on any
missing decision.

## Decisions → where they live
| Decision | project.yaml | Notes |
|---|---|---|
| Colour grade(s) | `design.grades.main` (+ any named grades) | parameters below; several grades for several eras/sources; pick per chapter (`### CH2 \| … \| grade=archive`) or per shot (`grade=…`) |
| Palette | `design.palette` | any keys your graphics use (`C.<key>` in custom_gfx.py); `text` is required (lower-third name) |
| Fonts | `design.fonts` (role → file) | roles are your names (`display`, `text`, `mono`…); download any Google Fonts family: `python3 scripts/fetch_fonts.py "Family Name:400,700"` |
| Subtitle, credit, stamp, lower-third fonts | `design.subtitle.font`, `credit.font`, `stamp.font`, `lower_third.name_font/role_font` | family names as fontconfig sees them (`fc-scan --format "%{fullname}\n" vendor/fonts/X.ttf`) |
| Chapter cards | `design.chapter_card {enabled, duration, gfx}` | the card is YOUR graphic (`gfx: chapter` → `g_chapter` in custom_gfx.py) |
| Transitions | `design.transitions {film_in, film_out, after_card}`, shot `in=` / `out=` | `cut`, `fade:<s>`, `dissolve:<s>` |
| Motion | `design.motion {still_zoom, video_push}`, shot `kb=`, `zoom=`, `push=` | 0 = static |
| Title card, lower-third look, overlays, all graphics | custom_gfx.py / animation clips | docs/08 |

## Grade parameters (`design.grades.<name>`)
| Key | Neutral | Effect |
|---|---|---|
| `desat` | 0 | mix towards grey (1 = black & white, negative = more saturation) |
| `contrast` | 1 | around mid-grey |
| `warm` | [1, 1, 1] | per-channel gain R, G, B (warm: R up / B down; cold: the reverse) |
| `vignette` | 0 | corner darkening (0.1 subtle … 0.4 heavy) |
| `grain` | 0 | film grain on footage/photos (0 clean … ~9 heavy) |
| `gfx_grain` | 0 | grain on code graphics so they sit with grainy footage (needs grain > 0) |
| `bottom` | 1 | darkens the lower third of footage/photos; 0.5–0.7 keeps white subtitles readable on bright footage |
Animation clips (`anim:`) are not graded like footage. Test a grade on 3–4 representative frames with
`vf gfx-preview` / a short render before committing to it.

## Technical constraints (these ARE fixed — they are about legibility and safety, not style)
- Safe area: all text ≥ 5 % from every edge; graphics text stays above the two-line subtitle block
  (≈ y 887 at 1080p with the default subtitle size). Preflight measures every text box.
- Every character must exist in its font (preflight checks glyph coverage — decorative fonts often lack
  kanji/diacritics and render boxes).
- Font family names used by subtitles/credits must be installed in vendor/fonts, otherwise libass silently
  substitutes another font (preflight checks).
- Subtitles: line length `design.subtitle.max_chars` (ja 24, zh 22, ko 20, latin 42) and ≤ 2 lines are
  readability limits; size 48–54 px at 1080p. Their colour/outline may change, their legibility may not.
- Credits are always on screen for the whole shot (style is yours, presence is not).
- Contrast of text vs background: check the darkest and brightest frames each text sits on.
