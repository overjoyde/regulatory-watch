# Canonical report and delivery

Use [report.schema.json](../assets/report.schema.json). [synthetic-report.json](../examples/synthetic-report.json) shows the complete shape; its legal content and verification flags are fictional. Replace all synthetic values before real use. `schema_version` is `1.0`.

Required metadata: profile/run ID, report date, language, IANA zone, jurisdictions/domains, explicit offset-aware half-open period, previous-report run ID or null, coverage, summary, findings, sources, checks for every configured source and limitations. Period end must produce the given report date in the profile zone. A run ID is unique within the profile. `previous_report` must equal the supplied checkpoint's `run_id`; supply `--previous` whenever this is non-null.

Each finding has a stable `finding_id`, title, change type, verified status, actual event date, first observation timestamp, official change, substantive difference, affected entities, date fields, interpretation, potential operational impact, internal applicability, review actions, source IDs and individually linked legal claims. The publication/change event must belong to the monitoring period; retrieval/observation can occur later during the review. Old newly found events require `late_publication` and an explanation. The date-only event field cannot resolve exact intraday boundaries: check the original publication's timestamp/version where available and explain date-only uncertainty, particularly for boundary dates. Never claim that structural checks prove exact event inclusion. Unknown legal dates are JSON null; render as unknown. Transition text can contain verified dates/terms or null. `operational_impact` is empty when disabled; `review_actions` is empty when disabled.

Source records contain direct URL, title, authority, publication date or null, provision, primary-source flag, access and verification state, retrieval timestamp and limitations. A legal claim must cite verified, read primary evidence. For conflicting/unavailable evidence, disclose limitations and withhold unsupported legal conclusions. Source IDs used in the finding resolve to these records; links appear in the last section. Human/agent review must verify that the source actually supports every official fact, status, date and scope statement. The structural validator cannot establish that.

## Rendered order

1. Regulatory Watch (localized title)
2. Report details: date, zone, jurisdictions, domains, exact period, previous report, coverage
3. Executive summary, including no-change/incomplete result as appropriate
4. Prioritized regulatory changes, each with status, official facts, substantive difference, scope/dates, interpretation, operational impact (if enabled), internal applicability, review actions (if enabled), claims and evidence IDs
5. **Sources and verification — always last**, including all limitations, source check results, direct links and font disclosures

Built-in heading labels support English and Swedish. Other languages are supported through a complete translated `labels` map with the keys in `scripts/common.py:LABELS`; provide all labels and translate authored content. Fixed technical enum/date metadata may remain machine-readable. Labels must not conceal or misrepresent mandatory evidence categories. The generator checks font glyph coverage and will reject unsupported scripts instead of silently producing missing characters. Complex script shaping/RTL is environment-dependent; verify visually and use a capable renderer if necessary.

All content is plain text, not Markdown/HTML in JSON fields. URLs must be HTTP(S) without credentials. The renderer escapes untrusted text. Markdown uses standard headings, paragraphs and autolinks. PDF uses the same ordered text blocks with clickable source URLs. `word_count` counts whitespace-delimited visible tokens across headings, metadata, body, source information and full URLs. This is a reproducible budget rule, not a linguistic tokenizer; for unsegmented languages agree an additional character budget with the user.

## Commands

```sh
python scripts/validate_report.py REPORT.json --config PROFILE.json --previous CHECKPOINT.json
python scripts/compare_reports.py REPORT.json --previous PREVIOUS_REPORT.json
python scripts/generate_pdf.py REPORT.json --config PROFILE.json --previous CHECKPOINT.json --output-dir OUTPUT_DIRECTORY
```

Omit `--previous` for the first report, not to bypass known history. For Markdown only, set `report.formats` to `["markdown"]`; the generator name does not force PDF output. It always writes canonical JSON alongside requested formats. `validate_report.py --markdown NEW_FILE.md` is a simple Markdown-only export after validation. If a font substitution occurs during PDF generation, the generator adds it to a copy of the canonical model, revalidates the word limit and writes that identical final model into JSON/Markdown/PDF.

Files default to `Regulatory_Watch_{profile}_{date}_{run_id}.md/.pdf/.json`. The directory is an explicit execution/output parameter, not an assumed storage integration. The generator never uploads, delivers messages, schedules a task or updates a checkpoint. It returns file hashes and results; inspect actual files, upload with available authorized connectors and verify persistence separately. Do not claim `storage.mode: cloud` has been fulfilled merely because local runtime files exist.

When validation exceeds word/change limits, edit the canonical content and regenerate all formats; do not silently truncate citations or limitations. If PDF generation fails, disclose the failed format, export valid Markdown separately if possible and provide the full report in the conversation. If no runtime exists, author equivalent inline Markdown and state that deterministic scripts were not run. Report source-verification status independently of file validation.

Final execution status: profile; `[start, end)` with zone; material changes count; complete/partial/unavailable research and main gaps; requested/created/failed formats; saved/delivery destination with verified or failed status; actual output links. Never report file links or external persistence without observing successful creation.
