# Versioned configuration and history

The executable contract is [config.schema.json](../assets/config.schema.json). JSON only; do not silently interpret YAML as JSON. Start from [default-config.json](../assets/default-config.json). Version `1.0` is accepted; reject other versions and offer an explicit migration rather than dropping unknown fields. Schemas reject unknown properties and wrong types.

Required groups:

| Field | Meaning |
|---|---|
| `profile_id`, `profile_name`, `confirmed` | Unique portable identifier, display name, actual onboarding confirmation |
| `jurisdictions` | Names, legal level (`kind`), and user-confirmed scope |
| `domains`, `focus` | Monitored legal areas and optional specific instruments/provisions |
| `sources` | Unique IDs, authority, public HTTP(S) endpoint, scope mapping, relevance verification and priority |
| `schedule` | Frequency, IANA zone, local time, weekdays/month day/custom recurrence and short-month policy |
| `report` | Language, word/change limits, detail, formats, design, optional font paths/colors, naming, analysis preferences |
| `storage` | Export/cloud/local proposal, destination and optional delivery destination; grants no access or permission |
| `organization` | Optional nonconfidential operational context; default `general` |
| `monitoring` | Calendar-day first lookback, historical comparison, retrieval overlap, verified-primary legal claims |

In manual mode use null `time`, `month_day`, `recurrence`, and empty `weekdays`. Weekly requires time and weekday(s). Monthly requires time and day 1-31; select `skip` or `last_day` for short months. Custom uses a recurrence string, null structured time/day fields; its grammar is deliberately not executed or validated by this package. The real scheduler must validate it.

Filename templates require `{profile}`, `{date}`, and `{run_id}` and no path separators. Run IDs prevent multiple reports on one date from overwriting each other. This extends a date-only filename for history safety. Slugs contain lowercase ASCII letters, digits and hyphens; schema rejects unsafe identifiers. Store multiple profiles in a registry or separate records; ensure ID uniqueness before saving. No default personal path exists.

`validate_config.py PROFILE.json` checks an editable draft. `--ready` additionally requires a confirmed profile, confirmed jurisdictions and relevance-verified sources. It cannot prove jurisdiction existence, that confirmation actually happened or that an authority is relevant. Review these during onboarding. Cloud/local destination strings remain proposals until connectors and access are checked; `export` is the default.

## Periods and checkpoints

Compute the end from current time converted to the configured zone. The first start is end minus N local calendar days (7 by default); across daylight-saving boundaries this can span 167 or 169 hours. Subsequent periods are `[last_complete_end, current_end)`, comparing actual instants with UTC offsets. The optional `--now` and `--checkpoint` flags compute this deterministically; checkpoint must be a complete canonical report for the same profile. Never choose a checkpoint solely because a file is the newest.

Use `retrieval_overlap_hours` to widen search retrieval before the start, without changing the reported period. Track late-indexed events by first observation and mark `late_publication`; explain actual publication date and why it is newly reported. Keep a ledger of stable event IDs, source versions/hashes, event dates, observed timestamps and material differences. The lightweight comparison script only compares the supplied files; the agent must consult the full ledger/history to avoid reintroducing older known events. A republished URL or cosmetic edit is not automatically a change.

If no checkpoint is reliable, explicitly disclose a lookback fallback and continuity uncertainty. Do not silently advance an incomplete period. A repeat after incomplete coverage starts from the last complete checkpoint; use the ledger to avoid duplicate findings. Save incomplete reports as history but do not promote them to checkpoints. If profile scope changes, either backfill newly added sources through the last checkpoint or start a new profile; disclose the coverage boundary.

Cloud storage is preferred when available and authorized; verify by reading saved content/metadata or file hashes. Store canonical JSON, Markdown/PDF and checkpoint/ledger outside the skill package. If upload fails, preserve outputs in the available runtime and return them; do not mark cloud storage/delivery complete. Do not collect secrets in profile JSON. Never assume locally synchronized folders are reachable by a scheduled cloud task.
