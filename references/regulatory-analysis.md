# Analysis, change detection and prioritization

For each candidate, establish a stable instrument/event identifier (official document ID plus consultation/amendment/decision event). Keep distinct events on one instrument separate. Compare actual substance, status, scope and dates against known versions and the history ledger. The same PDF posted again, title edits, URL changes and translated copies are not new requirements.

`compare_reports.py` fingerprints official-change text, status, scope, dates and claim evidence. It returns `new`, `unchanged`, `changed_requires_review`, or `baseline_unknown`. It ignores commentary and source retrieval time so those do not alone create a regulatory change. It cannot recognize semantically equivalent paraphrases or determine legal significance; read the prior and original texts. An absent item is not evidence of repeal/withdrawal. A changed application date needs direct evidence of the change, not merely a deadline becoming closer.

Select no more than the profile maximum using legal significance, domain/activity relevance, proximity of actual application deadlines, potential operational effect, substantive materiality and confidence of organization-type relevance. Do not invent numeric legal risk scores. `executive` favors brief decisions and dates; `standard` includes the complete core analysis; `detailed` includes additional provisions and transition discussion within the same configured word budget.

For each selected event, separate:

1. **Official regulation/publication:** what the primary text actually says, substantive difference, status and provisions. Include affected entities, activities, territorial scope and explicit unknown dates. Not every official publication is a regulation.
2. **Interpretation:** reasoned analysis with assumptions and uncertainty, separate from the quoted/verified position. Explain if a source does not settle an issue.
3. **Potential operational impact:** relevance to configured processes such as complaints, fraud detection, data retention, model governance, reporting, documentation or third parties. Omit when disabled. Proposed controls are recommendations unless a cited provision establishes an obligation.
4. **Internal applicability assessment:** concrete questions about entity type, licenses, activities, exemptions, jurisdiction, processes and implementation choices. Never infer applicability solely because the user works in a related industry. Do not invent internal thresholds, policies, owners or decisions. A technology provider need not have a bank's obligations.
5. **Recommended review actions:** focused questions for appropriate Legal, Compliance or operational functions, if enabled. Suggest a role for review, without assigning an unverified internal responsibility. Do not require confidential data to use the skill.

If there is no material event after a complete review, report localized no-change text (Swedish: “Ingen väsentlig förändring”), without padding findings. After incomplete review, report “Assessment incomplete” (or equivalent), describe source gaps and avoid a universal no-change conclusion. Even a fully source-checked result means no material change identified within the documented scope and period, not an assurance that every possible publication was found.
