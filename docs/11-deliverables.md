# Phase 11 — Deliverables and the report

```bash
$VF final && $VF qa && $VF stats && $VF sources
```
| File | Content |
|---|---|
| `out/video.mp4` | H.264 + AAC, project size/fps, faststart |
| `script.md` | style profile + director notes + design system + final script (NAR + VIS per scene) + `Length check … PASS` line |
| `sources.md` | `sources_assets.md` (generated: every asset on screen, licence, link, scenes, **CẦN KIỂM TRA QUYỀN** flags) + `sources_facts.md` (yours: fact → source per scene, and "handled with care") |
| `REPORT.md` | from `templates/REPORT.template.md`, numbers from `out/stats.json` |
| `out/credits_for_description.txt` | attribution lines for CC BY / BY-SA assets and music, ready for the video description |

Final message to the user (their language), short: duration; narration length; genre and visual direction;
real-footage vs graphics ratio (`real_pct`); what was learned from the sample and applied; what the review
rounds fixed; what the user must check before publishing — rights (C group, uncertain PD), audio (you cannot
listen), weak or single sources, approximate picture/word matches, places that differ from the sample's style.
If asked to upload (e.g. rclone to Drive), verify size + MD5 after upload.
