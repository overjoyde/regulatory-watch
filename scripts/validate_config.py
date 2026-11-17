#!/usr/bin/env python3
"""Validate structure and semantics. Does not confirm legal source relevance."""
import argparse
import json
from common import cli, config_errors, period_for, read_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config")
    parser.add_argument("--ready", action="store_true", help="Require completed onboarding")
    parser.add_argument("--now", help="Offset-aware timestamp for computing a period")
    parser.add_argument("--checkpoint", help="Last complete report JSON (verify storage/checkpoint externally)")
    args = parser.parse_args()
    config = read_json(args.config)
    errors = config_errors(config, args.ready)
    if errors:
        raise ValueError("\n".join(errors))
    result = {"valid": True, "ready_checked": args.ready, "profile_id": config["profile_id"],
              "scheduling": "configuration_only"}
    if args.checkpoint and not args.now:
        raise ValueError("--checkpoint requires --now")
    if args.now:
        previous = read_json(args.checkpoint) if args.checkpoint else None
        if previous:
            from validate_report import report_errors
            errors = report_errors(previous, config)
            if errors:
                raise ValueError("Invalid checkpoint: " + "; ".join(errors))
        result["period"], result["limitations"] = period_for(config, args.now, previous)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    cli(main)
