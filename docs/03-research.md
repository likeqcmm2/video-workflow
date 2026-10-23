# Phase 3 — Research

Research deep enough to fill the minimum length with real content: several periods, several people, concrete
details, sourced anecdotes, consequences, comparisons. Search in the narration language, in English, and in
the language of the country/people involved. Draft the chapter outline now so you see what is missing.

## Fan out to sub-agents (keeps ~100k characters of search results out of your context)
Spawn 2–4 sub-agents in parallel, each with one angle (e.g. "the technical cause", "the night before",
"aftermath and people", "Japanese-language coverage"). Prompt template:

> Research <TOPIC — ANGLE> for a documentary narrated in <LANGUAGE>. Use web search/fetch in <LANGUAGES>.
> Write `projects/<slug>/research/notes_<angle>.md` containing ONLY verified facts, one per line:
> `- <fact with exact numbers/dates/names> — <source title>, <publisher>, <date>, <URL>`
> Prefer primary sources (official reports, court records, the people involved, contemporary newspapers),
> then reputable secondary sources. Include quotable lines with the speaker and where they said it.
> Do not write narration. Reply with: number of facts, the 5 strongest anecdotes, gaps you could not fill.

## Your part
- Merge into `research/facts.md` (dedupe, resolve contradictions, keep the strongest source per fact).
- Outline chapters with estimated length each; send another sub-agent where a chapter is thin.
- The fact → source table later becomes `sources_facts.md` (Phase 11), keyed by scene ids.
