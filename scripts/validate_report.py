#!/usr/bin/env python3
"""Check structural evidence links and content invariants, not legal truth or URL availability."""
import argparse
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from common import (LABELS, cli, compare, config_errors, markdown, read_json,
                    safe_url, schema_errors, timestamp, word_count)


def report_errors(report, config, previous=None):
    errors = config_errors(config, ready=True) + schema_errors(report, "report.schema.json")
    if errors:
        return errors
    expected = {"profile_id": config["profile_id"], "timezone": config["schedule"]["timezone"],
                "language": config["report"]["language"], "domains": config["domains"],
                "jurisdictions": [j["name"] for j in config["jurisdictions"]]}
    for key, value in expected.items():
        if report[key] != value:
            errors.append(f"{key}: does not match selected profile")
    start, end = timestamp(report["period"]["start"]), timestamp(report["period"]["end"])
    if start >= end:
        errors.append("period: must have start < end")
    zone = ZoneInfo(config["schedule"]["timezone"])
    if end.astimezone(zone).date().isoformat() != report["report_date"]:
        errors.append("report_date: must equal monitoring end date in configured zone")
    if report["language"].split("-")[0] not in LABELS and set(report["labels"]) != set(LABELS["en"]):
        errors.append("labels: provide every translated label for this language")
    if set(report["labels"]) - set(LABELS["en"]):
        errors.append("labels: unknown label keys")
    if len(report["findings"]) > config["report"]["max_changes"]:
        errors.append("findings: exceeds max_changes")
    count = word_count(report)
    if count > config["report"]["max_words"]:
        errors.append(f"word_count: {count} exceeds {config['report']['max_words']}")
    for key, items in (("sources", report["sources"]), ("source_checks", report["source_checks"]),
                       ("findings", report["findings"])):
        field = "finding_id" if key == "findings" else "source_id"
        ids = [item[field] for item in items]
        if len(ids) != len(set(ids)):
            errors.append(f"{key}: duplicate identifier")
    sources = {s["source_id"]: s for s in report["sources"]}
    checks = {s["source_id"]: s for s in report["source_checks"]}
    configured = {s["source_id"]: s for s in config["sources"]}
    if set(checks) != set(configured):
        errors.append("source_checks: must record every configured source exactly once")
    unread = any(s["status"] != "read" for s in checks.values())
    uncertain = any(s["access"] != "read" or s["verification"] != "verified" for s in sources.values())
    if report["coverage"] == "complete" and (unread or uncertain or not checks):
        errors.append("coverage: complete requires all configured sources read and evidence verified")
    if report["coverage"] == "unavailable" and (any(s["status"] == "read" for s in checks.values()) or report["findings"]):
        errors.append("coverage: unavailable cannot include successful checks or verified findings; use partial")
    if report["coverage"] != "complete" and not report["limitations"]:
        errors.append("limitations: disclose incomplete source coverage")
    for check in checks.values():
        if check["status"] != "read" and not check["limitations"]:
            errors.append(f"source_checks/{check['source_id']}: explain failed access")
    for source in sources.values():
        if not safe_url(source["url"]):
            errors.append(f"sources/{source['source_id']}: invalid HTTP(S) URL")
        if (source["access"] != "read" or source["verification"] != "verified") and not source["limitations"]:
            errors.append(f"sources/{source['source_id']}: disclose verification limitation")
    for finding in report["findings"]:
        for sid in finding["source_ids"]:
            source = sources.get(sid)
            if not source or not source["primary"] or source["access"] != "read" or source["verification"] != "verified":
                errors.append(f"findings/{finding['finding_id']}: {sid} is not verified primary evidence")
        for claim in finding["legal_claims"]:
            if not set(claim["source_ids"]) <= set(finding["source_ids"]):
                errors.append(f"findings/{finding['finding_id']}: legal claim lacks a finding evidence reference")
        if finding["change_type"] == "unchanged":
            errors.append("findings: unchanged material must not fill prioritised changes")
        observed = timestamp(finding["observed_at"])
        # Retrieval normally occurs after the frozen period end. Do not require the
        # observation timestamp to precede that end; publication/change is the event.
        if observed < start:
            errors.append(f"findings/{finding['finding_id']}: observation precedes the current review period")
        event = datetime.fromisoformat(finding["event_date"]).date()
        if event > observed.astimezone(zone).date():
            errors.append(f"findings/{finding['finding_id']}: publication/change event cannot follow observation")
        if event > end.astimezone(zone).date():
            errors.append(f"findings/{finding['finding_id']}: event occurs after the monitoring period")
        if event < start.astimezone(zone).date() and finding["change_type"] != "late_publication":
            errors.append(f"findings/{finding['finding_id']}: older event must be labelled late_publication")
        if not config["report"]["include_operational_impact"] and finding["operational_impact"]:
            errors.append("operational_impact: disabled by profile; use empty string")
        if not config["report"]["include_legal_review_questions"] and finding["review_actions"]:
            errors.append("review_actions: disabled by profile; use empty list")
    if previous:
        if previous["profile_id"] != report["profile_id"]:
            errors.append("previous_report: wrong profile")
        if report["previous_report"] != previous["run_id"]:
            errors.append("previous_report: must equal supplied checkpoint run_id")
        if previous["coverage"] != "complete":
            errors.append("previous_report: incomplete reports cannot advance checkpoint")
        if timestamp(previous["period"]["end"]) != start:
            errors.append("period: gap or overlap with checkpoint")
        if config["monitoring"]["compare_previous_report"]:
            if any(item["result"] == "unchanged" for item in compare(report, previous)):
                errors.append("findings: previously reported unchanged event presented as new")
    elif report["previous_report"] is not None:
        errors.append("previous_report: supply --previous to verify the referenced checkpoint")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--config", required=True)
    parser.add_argument("--previous")
    parser.add_argument("--markdown", help="Write canonical Markdown to a NEW path")
    args = parser.parse_args()
    report, config = read_json(args.report), read_json(args.config)
    previous = read_json(args.previous) if args.previous else None
    if previous:
        errors = schema_errors(previous, "report.schema.json")
        if errors:
            raise ValueError("Invalid previous report: " + "; ".join(errors))
    errors = report_errors(report, config, previous)
    if errors:
        raise ValueError("\n".join(errors))
    if args.markdown:
        with open(args.markdown, "x", encoding="utf-8") as stream:
            stream.write(markdown(report))
    print(json.dumps({"valid": True, "word_count": word_count(report),
                      "scope": "structural_checks_only; primary-source truth requires human/agent review"}))


if __name__ == "__main__":
    cli(main)
