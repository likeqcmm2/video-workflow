# Phase 9 — Audio

- Voice: levelled per scene (RMS), always clearly on top.
- Music: free licence (Incompetech / Kevin MacLeod CC BY 4.0 is reliable: `vf music fetch "Dark Times"`;
  Free Music Archive with a compatible licence). Match the genre's emotion; long films change track per chapter
  (`music.chapters`), with fades. Use `offset` to choose the music in-point and `cut_from_scene` to
  fade music to silence from a selected scene. Example: `{file: assets/music/B.mp3, offset: 30, cut_from_scene: S103}`.
- Ducking: music 0.22 between sentences → 0.09 under narration (`level_between`, `level_under_voice`).
- Silence is a tool: cut the music at the climax of a disaster film.
- Sound effects by genre: true crime/history almost none; top 10/entertainment more.
- Original footage audio: only if certain it has no commentary from the source; otherwise muted (default) and
  say so in the report.
- Loudness: −16 LUFS integrated, true peak ≤ −1.5 dBTP (`vf audio`; `vf qa` measures the final file).
- Music credit text goes to `music.credit` → sources.md and the video description.
