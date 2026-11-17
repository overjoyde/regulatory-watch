"""Shared schema checks, periods and canonical report rendering. No network I/O."""
import hashlib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    with open(path, encoding="utf-8") as stream:
        return json.load(stream)


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("Timestamp must include a UTC offset")
    return result


def schema_errors(data, name):
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise ValueError("Missing jsonschema: install scripts/requirements.txt") from exc
    validator = Draft202012Validator(read_json(ROOT / "assets" / name), format_checker=FormatChecker())
    return [f"{'/'.join(map(str, e.absolute_path)) or '$'}: {e.message}"
            for e in sorted(validator.iter_errors(data), key=lambda e: str(list(e.absolute_path)))]


def safe_url(value):
    parsed = urlsplit(value)
    return (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
            and not parsed.username and not parsed.password and not re.search(r"[\s<>]", value))


def config_errors(config, ready=False):
    errors = schema_errors(config, "config.schema.json")
    if errors:
        return errors
    try:
        ZoneInfo(config["schedule"]["timezone"])
    except (KeyError, ValueError):
        errors.append("schedule/timezone: unknown IANA time zone")
    schedule = config["schedule"]
    frequency = schedule["frequency"]
    for field, needed in (("time", frequency in {"daily", "weekly", "monthly"}),
                          ("month_day", frequency == "monthly"),
                          ("recurrence", frequency == "custom")):
        if needed != (schedule[field] is not None):
            errors.append(f"schedule/{field}: inconsistent with {frequency}")
    if (frequency == "weekly") != bool(schedule["weekdays"]):
        errors.append("schedule/weekdays: required only for weekly schedules")
    source_ids = [s["source_id"] for s in config["sources"]]
    if len(source_ids) != len(set(source_ids)):
        errors.append("sources: duplicate source_id")
    for source in config["sources"]:
        if not safe_url(source["url"]):
            errors.append(f"sources/{source['source_id']}: invalid HTTP(S) URL")
        if not set(source["jurisdictions"]) <= {j["name"] for j in config["jurisdictions"]}:
            errors.append(f"sources/{source['source_id']}: jurisdiction outside profile")
        if not set(source["domains"]) <= set(config["domains"]):
            errors.append(f"sources/{source['source_id']}: domain outside profile")
        if source["relevance_status"] == "verified" and not source["verified_at"]:
            errors.append(f"sources/{source['source_id']}: missing relevance verification timestamp")
    template = config["report"]["file_naming"]
    tokens = re.findall(r"\{([^{}]+)\}", template)
    if (not {"profile", "date", "run_id"} <= set(tokens)
            or set(tokens) - {"profile", "date", "run_id"}
            or re.search(r"[/\\]", template)
            or "{" in re.sub(r"\{[^{}]+\}", "", template)
            or "}" in re.sub(r"\{[^{}]+\}", "", template)):
        errors.append("report/file_naming: use {profile}, {date}, {run_id}; no paths or other tokens")
    style = config["report"]["style"]
    if bool(style["font_regular"]) != bool(style["font_bold"]):
        errors.append("report/style: supply both regular and bold TTF paths")
    if ready:
        if not config["confirmed"]:
            errors.append("onboarding: profile requires user confirmation")
        if not all(j["confirmed"] for j in config["jurisdictions"]):
            errors.append("onboarding: jurisdiction names/scope require confirmation")
        if not config["sources"] or any(s["relevance_status"] != "verified" for s in config["sources"]):
            errors.append("onboarding: verify source relevance before execution")
    return errors


def period_for(config, now, previous=None):
    """Half-open interval [start, end); lookback is local calendar days."""
    zone = ZoneInfo(config["schedule"]["timezone"])
    end = timestamp(now).astimezone(zone)
    notes = []
    if previous:
        if previous["profile_id"] != config["profile_id"]:
            raise ValueError("Previous report belongs to a different profile")
        if previous["coverage"] != "complete":
            raise ValueError("Use the last complete, verified checkpoint; incomplete report is not a checkpoint")
        start = timestamp(previous["period"]["end"]).astimezone(zone)
    else:
        start = end - timedelta(days=config["monitoring"]["first_run_lookback_days"])
        notes.append("No verified checkpoint supplied; lookback period used. History continuity is unverified.")
    if start.timestamp() >= end.timestamp():
        raise ValueError("Monitoring end must be later than the previous checkpoint")
    return {"start": start.isoformat(), "end": end.isoformat()}, notes


def change_fingerprint(finding):
    fields = ("status", "official_change", "substantive_difference", "affected_entities", "dates", "legal_claims")
    return hashlib.sha256(json.dumps({k: finding[k] for k in fields}, sort_keys=True,
                                    ensure_ascii=False).encode()).hexdigest()


def compare(current, previous=None):
    if not previous:
        return [{"finding_id": f["finding_id"], "result": "baseline_unknown"} for f in current["findings"]]
    if current["profile_id"] != previous["profile_id"]:
        raise ValueError("Cannot compare different profiles")
    old = {f["finding_id"]: f for f in previous["findings"]}
    return [{"finding_id": f["finding_id"], "result":
             "new" if f["finding_id"] not in old else
             "unchanged" if change_fingerprint(f) == change_fingerprint(old[f["finding_id"]])
             else "changed_requires_review"} for f in current["findings"]]


LABELS = {
    "en": {"title": "Regulatory Watch", "metadata": "Report details", "summary": "Executive summary",
           "changes": "Prioritised regulatory changes", "sources": "Sources and verification",
           "none": "No material change identified", "incomplete": "Assessment incomplete",
           "date": "Report date", "zone": "Time zone", "jurisdictions": "Jurisdictions",
           "domains": "Regulatory domains", "period": "Monitoring period [start, end)",
           "previous": "Previous report", "coverage": "Source coverage", "limitations": "Limitations",
           "status": "Regulatory status", "official": "Official regulation / publication",
           "entities": "Affected entities", "dates": "Dates", "interpretation": "Interpretation",
           "impact": "Potential operational impact", "internal": "Internal applicability assessment",
           "actions": "Recommended review actions", "evidence": "Evidence", "change": "Change type",
           "diff": "Substantive difference", "font": "Font substitution", "legal": "Legal claims",
           "retrieved": "Retrieved", "verified": "Verified", "provision": "Provision"},
    "sv": {"title": "Regulatorisk bevakning", "metadata": "Rapportuppgifter", "summary": "Sammanfattning",
           "changes": "Prioriterade regelverksförändringar", "sources": "Källor och verifiering",
           "none": "Ingen väsentlig förändring", "incomplete": "Ofullständig bedömning",
           "date": "Rapportdatum", "zone": "Tidszon", "jurisdictions": "Jurisdiktioner",
           "domains": "Regelområden", "period": "Granskad period [start, slut)",
           "previous": "Föregående rapport", "coverage": "Källtäckning", "limitations": "Begränsningar",
           "status": "Regulatorisk status", "official": "Offentlig reglering / publikation",
           "entities": "Berörda aktörer", "dates": "Datum", "interpretation": "Tolkning",
           "impact": "Möjlig operativ påverkan", "internal": "Intern tillämplighetsbedömning",
           "actions": "Rekommenderade granskningsåtgärder", "evidence": "Underlag", "change": "Förändringstyp",
           "diff": "Saklig skillnad", "font": "Typsnittsersättning", "legal": "Rättsliga påståenden",
           "retrieved": "Hämtad", "verified": "Verifierad", "provision": "Bestämmelse"},
}


def blocks(report):
    """One ordered representation consumed by both Markdown and PDF."""
    labels = dict(LABELS.get(report["language"].split("-")[0], LABELS["en"]))
    labels.update(report["labels"])
    result = [("h1", labels["title"]), ("h2", labels["metadata"])]
    for key, value in (("date", report["report_date"]), ("zone", report["timezone"]),
                       ("jurisdictions", ", ".join(report["jurisdictions"])),
                       ("domains", ", ".join(report["domains"])),
                       ("period", f"{report['period']['start']} - {report['period']['end']}"),
                       ("previous", report["previous_report"] or "unavailable"),
                       ("coverage", report["coverage"])):
        result.append(("p", f"{labels[key]}: {value}"))
    result.extend([("h2", labels["summary"]), ("p", report["summary"])])
    if not report["findings"]:
        result.append(("p", labels["none"] if report["coverage"] == "complete" else labels["incomplete"]))
    result.append(("h2", labels["changes"]))
    for i, finding in enumerate(report["findings"], 1):
        result.append(("h3", f"{i}. {finding['title']}"))
        for key, value in (("change", finding["change_type"]), ("status", finding["status"]),
                           ("official", finding["official_change"]), ("diff", finding["substantive_difference"]),
                           ("entities", finding["affected_entities"]),
                           ("dates", f"event: {finding['event_date']}; observed: {finding['observed_at']}; " +
                            "; ".join(f"{k}: {v or 'unknown'}" for k, v in finding["dates"].items())),
                           ("interpretation", finding["interpretation"]), ("impact", finding["operational_impact"]),
                           ("internal", finding["internal_applicability"]),
                           ("actions", "; ".join(finding["review_actions"]))):
            if value:
                result.append(("p", f"{labels[key]}: {value}"))
        for claim in finding["legal_claims"]:
            result.append(("p", f"{labels['legal']}: {claim['text']} [{', '.join(claim['source_ids'])}]"))
        result.append(("p", f"{labels['evidence']}: {', '.join(finding['source_ids'])}"))
    # This section is always last, including limits and font disclosures.
    result.append(("h2", labels["sources"]))
    for limit in report["limitations"]:
        result.append(("p", f"{labels['limitations']}: {limit}"))
    for check in report["source_checks"]:
        result.append(("p", f"{check['source_id']}: {check['status']}. {check['limitations']}"))
    for source in report["sources"]:
        result.append(("p", f"[{source['source_id']}] {source['title']}. {source['authority']}. "
                       f"Published: {source['publication_date'] or 'unknown'}. "
                       f"{labels['provision']}: {source['provision']}. "
                       f"Access: {source['access']}; {labels['verified']}: {source['verification']}; "
                       f"{labels['retrieved']}: {source['retrieved_at']}. "
                       f"Limitations: {source['limitations'] or 'none'}."))
        result.append(("url", source["url"]))
    return result


def markdown(report):
    prefixes = {"h1": "# ", "h2": "## ", "h3": "### "}
    # Escape syntax so source-supplied content remains literal text.
    def literal(value):
        return re.sub(r"([\\`*_{}\[\]<>#!|])", r"\\\1", value)
    return "\n\n".join(prefixes.get(kind, "") +
                        (f"<{value}>" if kind == "url" else literal(value))
                        for kind, value in blocks(report)) + "\n"


def word_count(report):
    # Whitespace-delimited visible tokens, INCLUDING headings, metadata, sources and URLs.
    return sum(len(value.split()) for _, value in blocks(report))


def output_stem(config, report):
    return config["report"]["file_naming"].format(profile=config["profile_id"],
                                                  date=report["report_date"], run_id=report["run_id"])


def cli(main):
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, ImportError) as exc:
        import sys
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
