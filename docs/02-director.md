# Phase 2 — Director notes (the GENRE decides the PICTURES)

Work like a director, not a template filler. Test 1: mute any 10 seconds — a viewer must guess the genre.
Test 2: listen to any 30 seconds — someone who knows the channel must recognise its voice (Phase 1).
Code-built graphics are a tool, not a default: when real footage of the thing being said exists, it wins.

Write into script.md (after the profile), before any narration:
- genre AND sub-genre, period/era, place, the nature of the available material (TV archive, newsreel,
  paintings, satellite imagery, smartphone video…), and the main emotion (fear, curiosity, awe, grief…)
- the planned share of real footage/photos over the WHOLE film as a RANGE → `project.yaml
  director.real_pct: {min, max}`. Preflight errors only when the film as a whole is outside it.
  Chapters are free: one chapter may be all archive, another all graphics or animation (a mechanism nobody
  filmed, a reconstruction, a data-heavy passage). What matters is that every picture fits its narration and
  the arrangement has a purpose — you are the director. Preflight prints each chapter's share as information.
- pace (cut rhythm, how long stills hold), transitions, how on-screen text behaves, colour and texture,
  sound — all specific to THIS film (they become the design system in Phase 7)
- three things NOT to do in this film
- long films (>15 min): how visuals stay varied per chapter (chapter cards or not, a different dominant
  source per chapter, a recurring graphic that evolves, different grades per era…)

The table is a **starting point to reason from, not a template**. Two documentaries of the same genre can look
completely different (a 1940s war story vs. a 2010s cyber-crime; a Top 10 of ancient wonders vs. of
smartphones). Decide from the specific title, era and material.

| Genre | Typical real share | Dominant picture | Graphics are for | Pace & motion tendencies | Avoid |
|---|---|---|---|---|---|
| True crime, disaster, news | 70–90 % | scene, broadcasts, court, people, documents, newspapers | only where no footage exists: maps, law text, sentences, simple timelines | slow, heavy; hard cuts; restrained text; very few SFX | slamming text, counters, people icons, colourful charts, pounding music |
| History, biography | 60–80 % | archival photos/film, paintings, old maps, artefacts, old newspapers | animated maps (territory, routes), timelines, family trees | medium; slow moves on stills; treatment that fits each period | wrong-period images, modern illustrations posing as archive, anachronistic typography |
| Geography, travel, countries, nature | 50–70 % | real scenery, aerials, satellite | maps as the backbone: zooms, borders, area comparisons, statistics | medium, airy | wrong-scale maps or borders, footage from the wrong place |
| Science, technology, how it works | 30–50 % | experiments, equipment, NASA, microscopy | 50–70 %: diagrams, simulations, 3D, charts — graphics lead | clear, step by step; motion explains | effects that explain nothing, scientifically wrong diagrams |
| Top 10, ranking, comparison | each item has real pictures of itself | — | rank numbers, info cards, comparison bars, summary table | fast, high energy; strong motion graphics fit | every item in the same visual, items without real pictures |
| Business, finance, companies | 50–70 % | products, HQ, people, launches, articles | revenue/stock charts, money flows, logos, timelines | medium–fast | charts without a data source |
| Mystery, legend, the unexplained | 50–70 % | places, documents, artefacts | maps, suggestive reconstructions (shadows, blur) | slow, pauses | stating the unconfirmed as fact |
| Sports, entertainment, celebrities | 70–90 % | footage/photos of the event and people | scores, stats, records | fast, energetic | wrong match, season or person |

Mixed titles: pick the main genre and borrow from the second. Unlisted genre: reason the same way — what do
viewers of this genre expect, what makes them trust and stay. Animation clips made with external tools
(`anim:`) and code graphics both count as graphics; footage and photos count as real.

Reference: Challenger (1986 disaster, TV-era archive) planned 50–80 % real and landed at 60 %; its chapter
on the unfilmed teleconference is mostly maps, documents and charts (21 % real) because that is what the
story needed there — see examples/challenger.
