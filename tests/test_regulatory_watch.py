"""Offline, synthetic acceptance and regression tests. No network or scheduler calls."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from common import (blocks, compare, config_errors, markdown, period_for, read_json,
                    schema_errors, timestamp, word_count)
from generate_pdf import generate, verify_pdf
from validate_report import report_errors


class RegulatoryWatchTests(unittest.TestCase):
    def setUp(self):
        self.config = read_json(ROOT / "examples/synthetic-config.json")
        self.report = read_json(ROOT / "examples/synthetic-report.json")

    def test_draft_then_confirmed_onboarding(self):
        draft = read_json(ROOT / "assets/default-config.json")
        self.assertEqual(config_errors(draft), [])
        self.assertTrue(config_errors(draft, ready=True))
        self.assertEqual(config_errors(self.config, ready=True), [])

    def test_profile_reload_and_update_preserve_scope(self):
        reloaded = json.loads(json.dumps(self.config))
        original_scope = copy.deepcopy(reloaded["jurisdictions"])
        reloaded["report"]["max_words"] = 900
        self.assertEqual(config_errors(reloaded, True), [])
        self.assertEqual(reloaded["jurisdictions"], original_scope)
        self.assertEqual(self.config["report"]["max_words"], 600)

    def test_multiple_jurisdictions_domains_examples_are_drafts(self):
        config = read_json(ROOT / "examples/sweden-eu-aml.json")
        config["domains"].append("Consumer protection")
        self.assertEqual(len(config["jurisdictions"]), 2)
        self.assertEqual(config_errors(config), [])
        self.assertTrue(config_errors(config, True))
        self.assertEqual(config_errors(read_json(ROOT / "examples/uk-privacy.json")), [])

    def test_invalid_config_semantics(self):
        for mutate in [lambda c: c["schedule"].update(timezone="Mars/Olympus"),
                       lambda c: c["schedule"].update(frequency="weekly"),
                       lambda c: c["sources"][0].update(url="file:///secret"),
                       lambda c: c["sources"][0].update(jurisdictions=["Different place"]),
                       lambda c: c["report"].update(file_naming="../{profile}_{date}_{run_id}"),
                       lambda c: c.update(schema_version="2.0"),
                       lambda c: c["report"].update(formats=["docx"]),
                       lambda c: c["report"].update(max_words=True)]:
            with self.subTest(mutation=mutate):
                config = copy.deepcopy(self.config)
                mutate(config)
                self.assertTrue(config_errors(config))

    def test_weekly_monthly_custom_schedules_are_configuration_only(self):
        for fields in [{"frequency": "weekly", "time": "09:00", "weekdays": ["friday"]},
                       {"frequency": "monthly", "time": "09:00", "month_day": 31},
                       {"frequency": "custom", "recurrence": "scheduler-specific proposal"}]:
            config = copy.deepcopy(self.config)
            config["schedule"].update(fields)
            self.assertEqual(config_errors(config, True), [])
        result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_config.py"),
                                 str(ROOT / "examples/synthetic-config.json"), "--ready"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["scheduling"], "configuration_only")

    def test_first_period_and_missing_history(self):
        period, notes = period_for(self.config, "2026-10-08T09:00:00+00:00")
        self.assertEqual(period, self.report["period"])
        self.assertTrue(notes)

    def test_calendar_lookback_across_both_dst_boundaries(self):
        config = copy.deepcopy(self.config)
        config["schedule"]["timezone"] = "Europe/London"
        for end, hours in [("2026-03-30T09:00:00+01:00", 167), ("2026-10-26T09:00:00+00:00", 169)]:
            period, _ = period_for(config, end)
            duration = timestamp(period["end"]).timestamp() - timestamp(period["start"]).timestamp()
            self.assertEqual(duration / 3600, hours)
            self.assertEqual(timestamp(period["start"]).hour, 9)

    def test_checkpoint_continuity_and_rejection_of_incomplete(self):
        period, notes = period_for(self.config, "2026-10-15T09:00:00+00:00", self.report)
        self.assertEqual(period["start"], self.report["period"]["end"])
        self.assertEqual(notes, [])
        partial = copy.deepcopy(self.report)
        partial["coverage"] = "partial"
        with self.assertRaises(ValueError):
            period_for(self.config, "2026-10-15T09:00:00+00:00", partial)
        with self.assertRaises(ValueError):
            period_for(self.config, "2026-10-08T09:00:00+00:00", self.report)

    def test_historical_changes_ignore_commentary_and_cosmetic_metadata(self):
        current = copy.deepcopy(self.report)
        current["findings"][0]["interpretation"] = "Different analysis, same public event."
        current["sources"][0]["retrieved_at"] = "2026-10-08T08:45:00+00:00"
        self.assertEqual(compare(current, self.report)[0]["result"], "unchanged")
        current["findings"][0]["substantive_difference"] = "Another possible substantive difference requires review."
        self.assertEqual(compare(current, self.report)[0]["result"], "changed_requires_review")
        current["findings"][0]["dates"]["application"] = "2027-01-01"
        self.assertEqual(compare(current, self.report)[0]["result"], "changed_requires_review")
        self.assertEqual(compare(current)[0]["result"], "baseline_unknown")
        current["findings"][0]["finding_id"] = "different-event"
        self.assertEqual(compare(current, self.report)[0]["result"], "new")

    def test_no_change_vs_unavailable_sources(self):
        empty = read_json(ROOT / "examples/synthetic-no-change.json")
        unavailable = read_json(ROOT / "examples/synthetic-incomplete.json")
        self.assertEqual(report_errors(empty, self.config), [])
        self.assertEqual(report_errors(unavailable, self.config), [])
        self.assertIn("No material change identified", markdown(empty))
        self.assertNotIn("No material change identified", markdown(unavailable))
        self.assertIn("Assessment incomplete", markdown(unavailable))
        unavailable["coverage"] = "complete"
        self.assertTrue(report_errors(unavailable, self.config))

    def test_missing_and_conflicting_evidence_cannot_verify_claim(self):
        for mutate in [lambda r: r["sources"][0].update(access="unavailable"),
                       lambda r: r["sources"][0].update(verification="conflicting"),
                       lambda r: r["sources"][0].update(primary=False),
                       lambda r: r["findings"][0]["legal_claims"][0].update(source_ids=["absent"]),
                       lambda r: r.update(source_checks=[]),
                       lambda r: r["findings"].append(copy.deepcopy(r["findings"][0]))]:
            report = copy.deepcopy(self.report)
            mutate(report)
            self.assertTrue(report_errors(report, self.config))

    def test_old_events_require_late_publication(self):
        self.report["findings"][0]["event_date"] = "2026-09-20"
        self.assertTrue(report_errors(self.report, self.config))
        self.report["findings"][0]["change_type"] = "late_publication"
        self.report["findings"][0]["substantive_difference"] = "Previously unavailable event first observed during this review."
        self.assertEqual(report_errors(self.report, self.config), [])

    def test_report_limits_and_sources_last(self):
        self.assertEqual(report_errors(self.report, self.config), [])
        count = word_count(self.report)
        self.config["report"]["max_words"] = count
        self.assertEqual(report_errors(self.report, self.config), [])
        self.config["report"]["max_words"] = count - 1
        self.assertTrue(report_errors(self.report, self.config))
        headings = [text for kind, text in blocks(self.report) if kind == "h2"]
        self.assertEqual(headings[-1], "Sources and verification")
        self.assertIn("example-authority: read", markdown(self.report))
        self.config["report"]["max_words"] = 20000
        self.config["report"]["max_changes"] = 1
        second = copy.deepcopy(self.report["findings"][0])
        second["finding_id"] = "second-event"
        self.report["findings"].append(second)
        self.assertTrue(report_errors(self.report, self.config))

    def test_preference_disabling_and_translations(self):
        self.config["report"].update(include_operational_impact=False, include_legal_review_questions=False)
        self.assertTrue(report_errors(self.report, self.config))
        self.report["findings"][0].update(operational_impact="", review_actions=[])
        self.assertEqual(report_errors(self.report, self.config), [])
        self.report["language"] = self.config["report"]["language"] = "sv"
        self.assertIn("Källor och verifiering", markdown(self.report))
        self.report["language"] = self.config["report"]["language"] = "de"
        self.assertTrue(report_errors(self.report, self.config))

    def test_gap_overlap_and_duplicate_old_event_rejected(self):
        old = copy.deepcopy(self.report)
        old["period"] = {"start": "2026-09-24T09:00:00+00:00", "end": self.report["period"]["start"]}
        self.report["previous_report"] = old["run_id"]
        self.assertTrue(any("unchanged" in e for e in report_errors(self.report, self.config, old)))
        self.report["findings"] = []
        self.assertEqual(report_errors(self.report, self.config, old), [])
        old["period"]["end"] = "2026-10-01T10:00:00+00:00"
        self.assertTrue(any("gap or overlap" in e for e in report_errors(self.report, self.config, old)))

    def test_checkpoint_reference_binds_to_supplied_run(self):
        old = copy.deepcopy(self.report)
        old["run_id"] = "actual-previous"
        old["period"]["end"] = self.report["period"]["start"]
        self.report.update(findings=[], previous_report="wrong-previous")
        self.assertTrue(any("must equal" in e for e in report_errors(self.report, self.config, old)))
        self.assertTrue(any("supply --previous" in e for e in report_errors(self.report, self.config)))
        self.report["previous_report"] = old["run_id"]
        self.assertEqual(report_errors(self.report, self.config, old), [])

    def test_observation_after_period_end_is_valid(self):
        self.report["findings"][0]["observed_at"] = "2026-10-08T09:30:00+00:00"
        self.assertEqual(report_errors(self.report, self.config), [])

    def test_dst_fold_uses_actual_instants(self):
        self.config["schedule"]["timezone"] = "Europe/London"
        self.report["period"]["end"] = "2026-10-25T01:30:00+01:00"
        period, _ = period_for(self.config, "2026-10-25T01:15:00+00:00", self.report)
        self.assertEqual(timestamp(period["end"]).timestamp() - timestamp(period["start"]).timestamp(), 2700)

    def test_markdown_only_and_output_preservation(self):
        self.config["report"]["formats"] = ["markdown"]
        with tempfile.TemporaryDirectory() as directory:
            result = generate(self.report, self.config, directory)
            self.assertEqual(set(result["files"]), {"json", "md"})
            self.assertIn("cloud_storage_and_delivery_not_performed", result["storage"])
            before = Path(result["files"]["md"]).read_bytes()
            with self.assertRaises(ValueError):
                generate(self.report, self.config, directory)
            self.assertEqual(Path(result["files"]["md"]).read_bytes(), before)

    def test_pdf_parity_links_embedding_neutral_presets_and_fallback(self):
        for design in ("default_light", "minimal_gray", "custom"):
            with self.subTest(design=design), tempfile.TemporaryDirectory() as directory:
                config = copy.deepcopy(self.config)
                config["report"]["design"] = design
                if design == "custom":
                    config["report"]["style"].update(font_regular="missing-regular.ttf", font_bold="missing-bold.ttf")
                result = generate(self.report, config, directory)
                final = read_json(result["files"]["json"])
                self.assertGreaterEqual(verify_pdf(result["files"]["pdf"], final), 1)
                self.assertEqual(Path(result["files"]["md"]).read_text(), markdown(final))
                self.assertEqual(bool(result["font_substitutions"]), design == "custom")
                if design == "custom":
                    self.assertIn("Bitstream Vera substituted", Path(result["files"]["md"]).read_text())

    def test_multipage_unicode_and_long_url(self):
        self.config["report"]["max_words"] = 20000
        self.report["summary"] += " Ränta, åtgärd, naïve, Prüfung. " * 120
        self.report["sources"][0]["url"] += "?long=" + "abcdef" * 40
        with tempfile.TemporaryDirectory() as directory:
            result = generate(self.report, self.config, directory)
            self.assertGreater(result["pages"], 1)

    def test_font_disclosure_cannot_escape_word_budget(self):
        self.config["report"]["max_words"] = word_count(self.report)
        self.config["report"]["style"].update(font_regular="missing.ttf", font_bold="missing-bold.ttf")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                generate(self.report, self.config, directory)
            self.assertFalse(list(Path(directory).iterdir()))

    def test_unsupported_glyph_fails_transparently(self):
        self.report["summary"] += " 漢字"
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "glyphs"):
                generate(self.report, self.config, directory)
            self.assertFalse(list(Path(directory).iterdir()))

    def test_invalid_output_path_reports_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "file"
            file.write_text("occupied")
            with self.assertRaises(OSError):
                generate(self.report, self.config, file)

    def test_cli_exit_failure_and_comparison(self):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_config.py"),
                                 str(ROOT / "examples/uk-privacy.json"), "--ready"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("confirmation", result.stderr)
        result = subprocess.run([sys.executable, str(ROOT / "scripts/compare_reports.py"),
                                 str(ROOT / "examples/synthetic-report.json")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["comparison"][0]["result"], "baseline_unknown")


if __name__ == "__main__":
    unittest.main()
