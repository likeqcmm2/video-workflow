# Minimal clip integration example

Read this only when you need a short syntax example. `script.md` is an excerpt, not a complete renderable
project or a style preset. Asset paths are placeholders; no media, voice or Remotion project is bundled.

1. Initialize a project using `vf init` (WORKFLOW.md Phase 0) and choose its design and length settings.
2. Author the title and route-map animation in Remotion + SVG; keep sources in `assets/anim/<scene>/`.
3. Render `title.mp4` and `map_route.mp4` at the project size/fps as H.264 yuv420p. Each clip must cover its
   assigned shot duration, including lead/gaps. Re-render if voice timing changes.
4. Supply the station footage and its credit; replace the narration with researched content for the title.
5. Run the length gate, TTS, plan and preflight before rendering (docs/05, docs/06, docs/08).

Full-frame clip: `VIS: anim:assets/anim/map_route.mp4 @0:00.0`.
Alpha overlay: append `| overlay=anim:assets/anim/labels.webm` to a footage VIS line; use VP9 alpha or
ProRes 4444 as specified in docs/08. Check text bounds and glyphs on preview frames; clip text is not
measured by Python graphics QA. Automatic chapter cards still require a thin adapter (docs/08).
