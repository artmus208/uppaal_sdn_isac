from __future__ import annotations

import copy
import csv
import io
import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from uppaal_mcp.mac import reports as mac_reports
from uppaal_mcp.mac.defaults import build_default_contract as mac_contract
from uppaal_mcp.sdn import reports as sdn_reports
from uppaal_mcp.sdn.defaults import build_default_contract as sdn_contract
from uppaal_mcp.verifyta import parse_verifyta_outcomes, summarize_status


LAYERS = (("MAC", mac_reports, mac_contract), ("SDN", sdn_reports, sdn_contract))


class MacSdnReportStatusTests(unittest.TestCase):
    def reports(self, module, contract, result):
        return module.generate_report_bundle(
            contract_json=contract.to_dict(), result_json=result
        )["reports"]

    def property_results(self, report):
        return [
            line.split(" | ")[3]
            for line in report.splitlines()
            if line.startswith("| `")
        ]

    def test_runner_error_does_not_become_a_positive_property_result(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer):
                contract = build()
                formulas = [item.query for item in contract.properties]
                stdout = "Verifying formula 1\n -- Formula is satisfied.\n"
                outcomes = parse_verifyta_outcomes(stdout, formulas)
                result = {
                    "status": summarize_status(
                        1, outcomes, stdout, "Error: aborted",
                        expected_query_count=len(formulas),
                    ),
                    "query_results": [asdict(item) for item in outcomes],
                    "stdout": stdout,
                    "stderr": "Error: aborted",
                }
                self.assertEqual(result["status"], "error")
                reports = self.reports(module, contract, result)
                self.assertEqual(set(self.property_results(reports["report.md"])), {"not_verified"})
                self.assertIn("Overall status: `error`", reports["report.md"])
                self.assertIn("diagnostic only", reports["violations.md"])
                self.assertIn("satisfied", reports["violations.md"])
                self.assertNotIn("No failed query", reports["violations.md"])

    def test_unsuccessful_runs_with_partial_verdicts_are_diagnostic_only(self):
        for layer, module, build in LAYERS:
            contract = build()
            for status in ("error", "timeout", "oom", "tool_not_found", "static_error", "validated", "unknown", "mixed", "success", "ok", None):
                with self.subTest(layer=layer, status=status):
                    result = {"query_results": [
                        {"formula": contract.properties[0].query, "status": "satisfied"},
                        {"formula": contract.properties[1].query, "status": "not_satisfied"},
                    ]}
                    if status is not None:
                        result["status"] = status
                    reports = self.reports(module, contract, result)
                    self.assertEqual(set(self.property_results(reports["report.md"])), {"not_verified"})
                    self.assertIn("No property verdicts established", reports["violations.md"])
                    self.assertIn("diagnostic only", reports["violations.md"])
                    self.assertIn("not_satisfied", reports["violations.md"])

    def test_absent_input_is_not_run(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer):
                reports = self.reports(module, build(), None)
                self.assertEqual(set(self.property_results(reports["report.md"])), {"not_run"})
                self.assertNotIn("violations.md", reports)

    def test_empty_or_static_result_does_not_imply_no_violations(self):
        for layer, module, build in LAYERS:
            for result in ({}, {"status": "error"}, {"status": "validated", "query_results": []}):
                with self.subTest(layer=layer, result=result):
                    reports = self.reports(module, build(), result)
                    self.assertEqual(set(self.property_results(reports["report.md"])), {"not_verified"})
                    self.assertIn("No property verdicts established", reports["violations.md"])
                    self.assertNotIn("No failed query", reports["violations.md"])

    def test_complete_mixed_results_keep_positive_negative_and_uncertain_outcomes(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer):
                contract = build()
                statuses = ["satisfied", "not_satisfied", "maybe", "inconclusive"]
                result = {"status": "not_satisfied", "query_results": [
                    {"formula": prop.query, "status": statuses[i % len(statuses)]}
                    for i, prop in enumerate(contract.properties)
                ]}
                reports = self.reports(module, contract, result)
                self.assertEqual(self.property_results(reports["report.md"]), [row["status"] for row in result["query_results"]])
                violations = reports["violations.md"]
                self.assertIn("Violated properties", violations)
                self.assertIn("Queries without a decisive verdict", violations)
                self.assertNotIn("diagnostic only", violations)

    def test_inconclusive_run_is_not_a_property_violation(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer):
                contract = build()
                result = {"status": "inconclusive", "query_results": [
                    {"formula": prop.query, "status": "maybe"} for prop in contract.properties
                ]}
                reports = self.reports(module, contract, result)
                self.assertEqual(set(self.property_results(reports["report.md"])), {"maybe"})
                self.assertIn("Queries without a decisive verdict", reports["violations.md"])
                self.assertNotIn("No violated property", reports["violations.md"])
                self.assertNotIn("Violated properties", reports["violations.md"])

    def test_complete_positive_run_is_preserved(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer):
                contract = build()
                result = {"status": "satisfied", "query_results": [
                    {"formula": prop.query, "status": "satisfied"} for prop in contract.properties
                ]}
                reports = self.reports(module, contract, result)
                self.assertEqual(set(self.property_results(reports["report.md"])), {"satisfied"})
                self.assertIn("No violated property was reported among returned query results", reports["violations.md"])

    def test_missing_results_are_not_invented_for_a_completed_run(self):
        for layer, module, build in LAYERS:
            for rows in ([], [{"formula": build().properties[0].query}]):
                with self.subTest(layer=layer, rows=rows):
                    reports = self.reports(module, build(), {"status": "satisfied", "query_results": rows})
                    statuses = self.property_results(reports["report.md"])
                    self.assertEqual(statuses[0], "not_verified" if rows else "not_run")
                    self.assertEqual(set(statuses[1:]), {"not_run"})
                    self.assertNotIn("No violated property", reports["violations.md"])

    def test_export_preserves_raw_results_input_and_csv_schema(self):
        for layer, module, build in LAYERS:
            with self.subTest(layer=layer), tempfile.TemporaryDirectory() as directory:
                contract = build()
                result = {"status": "timeout", "stdout": "partial output", "query_results": [
                    {"formula": contract.properties[0].query, "status": "satisfied"}
                ]}
                original = copy.deepcopy(result)
                exported = module.export_report_bundle(
                    directory, contract_json=contract.to_dict(), result_json=result
                )
                self.assertEqual(result, original)
                self.assertEqual(json.loads((Path(directory) / "results.json").read_text(encoding="utf-8")), original)
                reports = self.reports(module, contract, result)
                self.assertEqual((Path(directory) / "report.md").read_text(encoding="utf-8"), reports["report.md"])
                self.assertEqual(next(csv.reader(io.StringIO(reports["properties.csv"]))), ["name", "category", "query", "interpretation"])
                self.assertEqual(exported["summary"]["report_count"], len(reports))


if __name__ == "__main__":
    unittest.main()
