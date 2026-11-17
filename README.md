# Regulatory Watch

**A configurable AI-agent skill for evidence-linked regulatory monitoring.**

Define the jurisdictions, regulatory domains and reporting preferences that matter
to you. The skill guides an agent through primary-source research, comparison
with earlier reporting periods and a clear assessment of material changes. It
produces Markdown and PDF from the same canonical report, keeping evidence,
dates and findings consistent across formats.

Version **1.0.0** · Python **3.10+** for bundled scripts · **25 offline tests**

## What it does

| Capability | How it works |
|---|---|
| Interactive setup | Confirms scope, source mapping, time zone and report preferences before the first review. |
| Multiple profiles | Keeps independent, versioned profiles for different jurisdictions, domains or functions. |
| Primary-source research | Requires original publications, provisions, status, scope and relevant dates for material legal claims. |
| Change detection | Compares stable event IDs and substantive fields; unchanged publications do not fill the report. |
| Clear analysis boundaries | Separates official facts, interpretation, potential operational impact and organization-specific applicability. |
| Explicit source coverage | Distinguishes a complete review with no material changes from a review with inaccessible or unverified sources. |
| Consistent reports | Renders Markdown and PDF from one JSON model, with configurable word/change limits and source links. |
| Configurable presentation | Neutral light and grayscale designs, plus custom colors and licensed TTF fonts. |
| Schedule planning | Captures manual, daily, weekly, monthly or custom recurrence without activating a task automatically. |

No organization, jurisdiction, industry, storage provider or scheduler is assumed.
Monitor one country, multiple countries, supranational rules, national
implementation, or another supported legal framework within a profile.

## Choose your starting point

- **Use the skill with an agent:** install the folder and ask the agent to configure a profile.
- **Try the deterministic tools:** run the offline demonstration below, without browsing or real regulatory data.
- **Adapt the workflow:** start with the profile examples and the configuration/report schemas.

The instructions guide research through the host agent. The Python scripts
validate and render supplied data; they are not a standalone regulatory crawler
or a background monitoring service.

## Install the skill

Clone or download this repository. The repository root is the skill folder:
it contains `SKILL.md`, `agents/`, `references/`, `scripts/` and `assets/`.

For a standard Codex user installation, clone directly into its skill directory:

```sh
git clone https://github.com/overjoyde/regulatory-watch.git ~/.codex/skills/regulatory-watch
```

If that folder exists, update the existing installation rather than cloning over
it. Refresh skill discovery or restart the host if required. Other agents can
use the folder when they support this skill format; installation and ZIP-upload
support depend on the host.

Installing the skill does not install Python packages, create a monitoring
profile, run a review or activate a schedule.

## First use

Ask your agent:

> Use $regulatory-watch to configure a weekly regulatory watch for the United
> Kingdom, focused on data protection and privacy. Walk me through the required
> settings and keep scheduling inactive.

The agent gathers and confirms:

1. Jurisdictions and regulatory domains, including any specific laws or provisions.
2. Relevant official sources and their current remit.
3. Manual or recurring schedule settings, local time and IANA time zone.
4. Report language, word/change limits, detail level, formats and visual design.
5. Available storage/delivery capabilities and optional nonconfidential operational context.

After confirming a valid profile, ask:

> Use $regulatory-watch with this confirmed profile to review changes since the
> last complete report. Explain any source limitations and produce the requested
> report formats.

Update individual settings without repeating the entire onboarding:

> Change this profile's report language to Swedish and its word limit to 800.
> Keep its existing scope and leave scheduling inactive.

The starter proposes English, 600 words, up to three changes, standard detail,
Markdown and PDF, neutral light design, manual execution and export. These are
editable starting values, not inferred user preferences.

## Run the offline demonstration

From the repository root, create a local environment and install dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r scripts/requirements.txt
```

On Windows PowerShell, activate with `.venv/Scripts/Activate.ps1` instead.
Systems without an IANA time-zone database may also need `python -m pip install tzdata`.

Validate a fictional profile and report, compare findings, then generate files:

```sh
python scripts/validate_config.py examples/synthetic-config.json --ready
python scripts/validate_report.py examples/synthetic-report.json --config examples/synthetic-config.json
python scripts/compare_reports.py examples/synthetic-report.json
python scripts/generate_pdf.py examples/synthetic-report.json --config examples/synthetic-config.json --output-dir demo-output
```

The demonstration creates canonical JSON, Markdown and a PDF under `demo-output/`.
It uses fictional publications and simulated verification flags. It performs no
network research, uploads, messaging or scheduling. Comparison returns
`baseline_unknown` because no prior report was supplied.

On another run, choose a new output directory or a unique `run_id`; existing
report files are never overwritten. To generate Markdown only, set
`report.formats` to `["markdown"]` in a working profile copy. The generator name
does not force PDF output.

## Configure a real profile

| Starting file | Intended use |
|---|---|
| [assets/default-config.json](assets/default-config.json) | Neutral, unconfirmed starter for onboarding. |
| [examples/sweden-eu-aml.json](examples/sweden-eu-aml.json) | Combined national/supranational AML scope example. |
| [examples/uk-privacy.json](examples/uk-privacy.json) | Unrelated jurisdiction and privacy-domain example. |
| [assets/config.schema.json](assets/config.schema.json) | Versioned profile contract. |
| [assets/report.schema.json](assets/report.schema.json) | Canonical report contract. |

Geographic examples are **unconfirmed templates** with source relevance pending.
Verify jurisdiction, issuing authority, current remit and endpoint before use.
They do not establish current legal requirements.

Draft validation checks structure and settings. Execution readiness also requires
completed onboarding:

```sh
python scripts/validate_config.py PROFILE.json
python scripts/validate_config.py PROFILE.json --ready
```

`PROFILE.json` and `REPORT.json` in these commands stand for your working files.
Keep actual profiles, reports, history, credentials and operational data outside
the installed skill and version-controlled repository.

## History and change detection

The first review uses a seven-day local-calendar lookback by default. Subsequent
periods start at the last complete, source-verified and successfully saved
checkpoint. Periods use explicit UTC offsets and `[start, end)` boundaries.
Incomplete coverage does not advance the checkpoint.

```sh
python scripts/validate_config.py PROFILE.json --ready --now 2026-10-15T09:00:00+00:00 --checkpoint PREVIOUS.json
python scripts/compare_reports.py REPORT.json --previous PREVIOUS.json
python scripts/validate_report.py REPORT.json --config PROFILE.json --previous PREVIOUS.json
python scripts/generate_pdf.py REPORT.json --config PROFILE.json --previous PREVIOUS.json --output-dir reports
```

When a checkpoint is supplied, `previous_report` must match its `run_id` and
periods must be continuous. Comparison distinguishes new candidates, unchanged
material, possible substantive changes and missing baselines. It does not infer
repeal from an absent finding or prove that a text edit is a legal change.

Full-history deduplication requires an external ledger of stable event IDs and
prior versions. Retrieval overlap helps find late-indexed publications; newly
discovered older events must be identified and explained as late publications.

## Reports and PDF checks

Reports include the exact period, scope, executive summary, prioritized findings
and a final sources/verification section. Each finding separates official facts,
status, scope/dates, interpretation, potential operational impact and internal
applicability questions. Unverified dates remain explicitly unknown.

All requested formats use the same ordered content. The generator checks word
budgets, PDF text parity, clickable source-link annotations and font embedding.
Missing requested fonts fall back to available embedded Bitstream Vera, with the
substitution disclosed in every output. Custom fonts need appropriate rights and
glyph coverage; complex-script shaping depends on the renderer.

Render and inspect every PDF page. With Poppler installed:

```sh
pdftoppm -scale-to 1400 -png demo-output/Regulatory_Watch_synthetic-demo_2026-10-08_demo-01.pdf demo-output/page
```

Text/annotation checks do not establish visual quality, source reachability or
legal correctness. Word count includes headings, metadata, limitations, sources
and visible URLs.

## Scheduling, persistence and delivery

This repository does not contain a scheduler or storage connector. The host must
provide browsing, code execution, persistence and any scheduling/delivery tools
that a particular workflow needs.

A saved frequency is a proposal until an authorized scheduling action succeeds.
Future cloud runs need access to the profile, history and output destination;
local files or conversation memory cannot be assumed to transfer. When a
capability is unavailable, the skill explains the limitation and offers export
or complete inline output where possible.

## Tests and verification limits

Run the offline suite from the repository root:

```sh
python -m unittest discover -s tests -v
```

The 25 tests cover draft/readiness checks, profile updates, multiple scopes,
schedule consistency, initial and checkpoint periods, both daylight-saving
transitions and the repeated-hour boundary, change detection, no-change versus
unavailable-source results, evidence links, limits, translations, output
preservation, PDF parity, links, fonts, fallback and transparent failures.

The initial package also passed skill-frontmatter validation, strict operational
validation, an identity-content scan, extracted-ZIP tests and visual inspection
of final demonstration PDFs. An independent offline forward test exercised
first-time and returning-user behavior.

These checks use synthetic data. Real primary-source accuracy, legal
applicability, exhaustive discovery, authenticated access, cloud persistence,
scheduler behavior and delivery require verification in the target environment.
Date-only publication fields require an additional source check at exact
intraday period boundaries.

## Repository guide

```text
regulatory-watch/
├── SKILL.md                 Agent entry point and workflow invariants
├── agents/openai.yaml       Skill discovery/display metadata
├── assets/                  Default profile and versioned JSON schemas
├── examples/                Unconfirmed scope templates and synthetic fixtures
├── references/              Onboarding, source policy, analysis and reporting guides
├── scripts/                 Validation, comparison and report generation
└── tests/                   Offline synthetic regression suite
```

Read the detailed [onboarding guide](references/onboarding.md),
[configuration and history rules](references/configuration.md),
[source policy](references/source-policy.md),
[analysis guide](references/regulatory-analysis.md),
[report contract](references/report-template.md),
[design guide](references/report-design.md),
[scheduling guide](references/scheduling.md), and
[acceptance scenarios](references/acceptance-tests.md) as needed.
