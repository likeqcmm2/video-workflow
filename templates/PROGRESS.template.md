# PROGRESS  (state file - update after every phase; it is what survives a context reset)

## Status
- Phase: 0
- Next action:

## Decisions
-

## Data notes (formats, ids, paths that the next session must know)
- out/timeline.json: chapters[{id,start,end}], timeline[type=card|shot|vo|end]; vo entries have subs, not t1.

## Graphics / animation authoring
- Default: Remotion + SVG.
- Render host: available CPU / affinity or quota / available RAM / current load / output-disk capacity.
- Clip rendering: parallel jobs J / per-job concurrency C / measured throughput and memory / tuning decisions.
- Clip batch: completed outputs / failed jobs / next queued clips.
- Fallbacks (if any): requirement → attempted Remotion approach → why Remotion cannot meet it → chosen tool.

## Open issues / pending downloads
-

## Wikimedia
- Login status / test results / 429s / pending queue:
