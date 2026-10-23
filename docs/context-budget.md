# Context budget — operating rules

Read only the files needed for the current phase. Keep durable state and raw results on disk.

1. **Main-agent video review; delegate scouting when available.** Both video-review rounds and follow-up
   passes belong to the main agent; do not delegate them. Open review sheets in small batches (for example
   1–2 at a time), save JSON findings and progress to files, and keep a compact summary in context.
   Contact sheets/scouting grids may go to sub-agents; if unavailable or failing, inspect small batches
   yourself and save findings. Complete all required coverage.
2. **Never print raw data.** Commands print short summaries; full data goes to files (`assets/*/scout/*.json`,
   `out/qa/*.json`). If you need more, `rg`/`head` the file. Never `cat` a large JSON or HTML.
3. **Avoid repetitive polling.** Prefer background jobs with completion notifications. Without notifications,
   check status and short log tails at spaced intervals (start around 30–60 s, then back off). Without
   background support, use a foreground execution session with bounded waits. Do not skip completion checks.
4. **Prefer saved summaries and targeted reads.** After Phase 1, use the style profile; for engine APIs use
   `vf --help`, `vf gfx-list`, docs/05 and docs/08 first. If a summary is incomplete, an error needs debugging
   or docs disagree with code, re-read only the relevant sample passage, documentation or source function
   and update the saved notes. Avoid repeatedly loading whole files.
5. **Edit, don't rewrite.** Change files with small edits; do not re-emit whole scripts/graphics files.
6. **Batch shell work** into one command with a compact final print; avoid many tiny tool calls.
7. **Write state to PROGRESS.md** after every phase (decisions, data formats, next action). After a compaction,
   recover from PROGRESS.md + WORKFLOW.md, not from memory.
8. **Research fan-out** to sub-agents (docs/03); you keep only research/facts.md.
9. Prefer the automated checks to visual inspection; look only where a check cannot.
10. Shell hygiene: `pkill -f` patterns must not match your own shell (anchor them:
    `pkill -f '^python3 -m vf render'`); use a `sed` delimiter not present in the text, or Python for edits;
    know the JSON schema before indexing (timeline `vo` entries have no `t1`).
