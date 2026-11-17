#!/usr/bin/env python3
"""Conservative comparison by stable publication/event identifier and substantive fields."""
import argparse
import json
from common import cli, compare, read_json, schema_errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current")
    parser.add_argument("--previous")
    args = parser.parse_args()
    current = read_json(args.current)
    previous = read_json(args.previous) if args.previous else None
    for report in (current, previous):
        if report is not None:
            errors = schema_errors(report, "report.schema.json")
            if errors:
                raise ValueError("\n".join(errors))
    print(json.dumps({"comparison": compare(current, previous),
                      "meaning": "Candidate differences require primary-source review; absence is not withdrawal."},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    cli(main)
