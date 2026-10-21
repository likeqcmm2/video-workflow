# Context budget — how one session survives a 30-minute production

The reference production processed ~347 M input tokens over 977 turns and hit a 783 k-token context before it
was compacted. Most of it was avoidable. Rules:

1. **Images go to sub-agents.** Review sheets, contact sheets, scouting grids: a sub-agent reads them and returns
   text/JSON. The main agent opens at most a handful of images itself (a custom graphic preview, one spot check).
   (Reference: 119 images ≈ 180–200 k tokens stayed in the main context.)
2. **Never print raw data.** Commands print short summaries; full data goes to files (`assets/*/scout/*.json`,
   `out/qa/*.json`). If you need more, `grep`/`head` the file. Never `cat` a large JSON or HTML.
3. **No polling.** Long jobs (`tts`, `render`, `final`) run in the background; you are notified when they end.
   Each "is it done yet?" turn re-reads the whole context. (Reference: 46 polling turns.)
4. **Do not re-read** the sample script after Phase 1, or engine source files to learn their API — use
   `vf --help`, `vf gfx-list`, docs/05 and docs/08.
5. **Edit, don't rewrite.** Change files with small edits; do not re-emit whole scripts/graphics files.
6. **Batch shell work** into one command with a compact final print; avoid many tiny tool calls.
7. **Write state to PROGRESS.md** after every phase (decisions, data formats, next action). After a compaction,
   recover from PROGRESS.md + WORKFLOW.md, not from memory.
8. **Research fan-out** to sub-agents (docs/03); you keep only research/facts.md.
9. Prefer the automated checks to visual inspection; look only where a check cannot.
10. Shell hygiene that cost retries: `pkill -f` patterns must not match your own shell (anchor them:
    `pkill -f '^python3 -m vf render'`); use a `sed` delimiter not present in the text, or Python for edits;
    know the JSON schema before indexing (timeline `vo` entries have no `t1`).
