# Acceptance scenarios and actual verification boundaries

Run `python -m unittest discover -s tests -v` with package dependencies installed. Fixtures are fictional; no live source, cloud upload, delivery or scheduling is tested by these scripts.

| Scenario | Deterministic coverage | Behavioral/target-host check |
|---|---|---|
| New user onboarding | Unconfirmed draft rejected for execution; confirmed fixture accepted | Ask grouped scope/source/report questions; wait for confirmation |
| Existing user | JSON round-trip and readiness validation | Find authorized saved profile; select correct ID |
| Profile update | Settings change preserves original scope | Reconfirm material change; no full onboarding repeat |
| Multiple jurisdictions/domains | Combined scope and unrelated example profiles | Verify actual territorial/legal relevance |
| First 7-day report | Exact local-calendar lookback | Disclose no checkpoint/history continuity |
| Subsequent/history comparison | Stable IDs; substance versus commentary; checkpoint continuity | Read full ledger, original versions and prior reports |
| No material change | Complete empty report accepted | Do not pad findings |
| Primary source unavailable | Unavailable report accepted, false complete rejected | Explain gaps; no blanket no-change claim |
| Missing prior report | Lookback plus explicit continuity notice | Retrieve earlier checkpoint if available |
| Markdown/PDF parity | Shared blocks, exact PDF text, Markdown serialization | Visually inspect delivered PDF pages |
| DST | 167/169-hour local 7-day periods | Scheduler's ambiguous/nonexistent time handling |
| Word/change limits | Boundary and over-budget rejection | Summarize content without dropping evidence |
| Neutral light/grayscale/custom design | All presets generate; embedded fonts and links checked | Page-by-page visual inspection |
| Missing font | Fallback embedded; disclosure in both formats and counted | Verify license for custom fonts |
| Unsupported scheduler | CLI returns `configuration_only`; no scheduler code | Explain manual use and no task activation |
| No persistence | Explicit output-directory results distinguish cloud persistence | Export profile; do not promise cross-session memory |
| Conflicting/unverifiable evidence | Nonverified evidence cannot support verified claims | Describe conflict, unknown dates and legal review questions |

Additional checks cover invalid time zones, malformed schedules/URLs/filenames, unsupported schemas/formats, duplicate IDs, missing checks, late events, historical overlap/gaps, Markdown-only output, failed writes, overwrite protection, long multipage content, Unicode glyph coverage, and disabled impact/review-question preferences.

The tests establish executable contracts only. They do not prove primary-source authority, legal correctness, valid user consent, exhaustive geographic validity or real integration availability. Forward-test agent behavior with synthetic requests when changing workflows; record findings separately from the distributable examples. Do not convert simulated fixture verification flags into claims that real research passed.
