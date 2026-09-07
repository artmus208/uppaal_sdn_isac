import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uppaal_mcp.config import UppaalConfig
from uppaal_mcp.verifyta import VerifytaRunner, parse_verifyta_outcomes, resolve_verifyta_options, summarize_status


MODEL_XML = """<nta>
<template><name>P</name><location id="id0"/><init ref="id0"/></template>
<system>p = P(); system p;</system>
<queries><query><formula>A[] not deadlock</formula></query>
<query><formula>E&lt;&gt; true</formula></query></queries>
</nta>"""
QUERIES = "A[] not deadlock\nE<> true\n"
FIRST_SUCCESS = "Verifying formula 1 at queries.q:1\n-- Formula is satisfied.\n"
COMPLETE_SUCCESS = FIRST_SUCCESS + "Verifying formula 2 at queries.q:2\n-- Formula is satisfied.\n"


class VerifytaParserTests(unittest.TestCase):
    def test_parse_satisfied_and_not_satisfied(self) -> None:
        stdout = """
        Verifying formula 1 at /nta/queries/query[1]/formula
        -- Formula is satisfied.
        Verifying formula 2 at /nta/queries/query[2]/formula
        -- Formula is NOT satisfied.
        """
        outcomes = parse_verifyta_outcomes(stdout, ["A[] not deadlock", "E<> Bad"])
        self.assertEqual([item.status for item in outcomes], ["satisfied", "not_satisfied"])
        self.assertEqual(outcomes[0].formula, "A[] not deadlock")
        self.assertEqual(summarize_status(0, outcomes, stdout, ""), "not_satisfied")

    def test_summarize_all_satisfied(self) -> None:
        stdout = "-- Formula is satisfied."
        outcomes = parse_verifyta_outcomes(stdout, ["A[] not deadlock"])
        self.assertEqual(summarize_status(0, outcomes, stdout, ""), "satisfied")

    def test_summarize_error_without_outcomes(self) -> None:
        self.assertEqual(summarize_status(1, [], "", "syntax error"), "error")

    def test_reported_indices_bind_results_to_the_correct_formula(self) -> None:
        stdout = "Verifying formula 2 at queries.q:2\n-- Formula is NOT satisfied.\n"
        outcomes = parse_verifyta_outcomes(stdout, QUERIES.splitlines())
        self.assertEqual(outcomes[0].index, 2)
        self.assertEqual(outcomes[0].formula, "E<> true")

    def test_ansi_output_and_uncertain_verdicts(self) -> None:
        for verdict in ("may be satisfied", "is maybe satisfied", "is inconclusive"):
            with self.subTest(verdict=verdict):
                stdout = "\x1b[2KVerifying formula 1\n\x1b[2K -- Formula " + verdict + ".\n"
                outcomes = parse_verifyta_outcomes(stdout, ["A[] not deadlock"])
                self.assertEqual(len(outcomes), 1)
                self.assertEqual(
                    summarize_status(0, outcomes, stdout, "", expected_query_count=1),
                    "inconclusive",
                )

    def test_only_result_lines_are_parsed(self) -> None:
        stdout = 'Warning: model comment says "Formula is satisfied."\n'
        self.assertEqual(parse_verifyta_outcomes(stdout, ["A[] not deadlock"]), [])

    def test_resolve_verifyta_options_presets(self) -> None:
        self.assertEqual(resolve_verifyta_options(options_preset="normal"), [])
        self.assertEqual(resolve_verifyta_options(options_preset="trace_on_violation"), ["-t0"])
        self.assertEqual(resolve_verifyta_options(options=["-u"], options_preset="diagnostic"), ["-t0", "-u"])
        with self.assertRaises(ValueError):
            resolve_verifyta_options(options_preset="wild")


class VerifytaRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.runner = VerifytaRunner(UppaalConfig("mock-verifyta", Path(workspace.name)))

    def run_completed(self, stdout: str, *, returncode: int = 0, stderr: str = "", **inputs):
        if not inputs:
            inputs = {"model_xml": MODEL_XML, "queries": QUERIES}
        completed = subprocess.CompletedProcess(["mock-verifyta"], returncode, stdout, stderr)
        with patch("uppaal_mcp.verifyta.subprocess.run", return_value=completed) as run:
            result = self.runner.verify(**inputs)
        run.assert_called_once()
        self.assertEqual(result.returncode, returncode)
        self.assertEqual(result.stdout, stdout)
        self.assertEqual(result.stderr, stderr)
        return result

    def test_report_complete_success_control(self) -> None:
        result = self.run_completed(COMPLETE_SUCCESS)
        self.assertEqual(result.status, "satisfied")
        self.assertEqual([item.index for item in result.query_results], [1, 2])

    def test_report_error_after_first_success(self) -> None:
        result = self.run_completed(
            FIRST_SUCCESS + "Verifying formula 2 at queries.q:2\n",
            returncode=1,
            stderr="syntax error in second query\n",
        )
        self.assertEqual(result.status, "error")
        self.assertEqual(len(result.query_results), 1)
        self.assertEqual(result.query_results[0].status, "satisfied")

    def test_report_incomplete_output_returncode_zero(self) -> None:
        result = self.run_completed(FIRST_SUCCESS)
        self.assertEqual(result.status, "error")
        self.assertEqual(len(result.query_results), 1)

    def test_report_error_after_success_returncode_zero(self) -> None:
        result = self.run_completed(FIRST_SUCCESS, stderr="error: second query failed\n")
        self.assertEqual(result.status, "error")

    def test_report_error_without_outcomes_control(self) -> None:
        result = self.run_completed("", returncode=2, stderr="syntax error\n")
        self.assertEqual(result.status, "error")
        self.assertEqual(result.query_results, [])

    def test_report_timeout_after_first_success_control(self) -> None:
        timeout = subprocess.TimeoutExpired(
            ["mock-verifyta"], 1, output=FIRST_SUCCESS.encode(), stderr=b"synthetic timeout\n"
        )
        with patch("uppaal_mcp.verifyta.subprocess.run", side_effect=timeout):
            result = self.runner.verify(model_xml=MODEL_XML, queries=QUERIES)
        self.assertEqual(result.status, "timeout")
        self.assertIsNone(result.returncode)
        self.assertEqual(result.stdout, FIRST_SUCCESS)
        self.assertEqual(result.stderr, "synthetic timeout\n")
        self.assertEqual(result.query_results, [])

    def test_report_missing_tool_control(self) -> None:
        with patch("uppaal_mcp.verifyta.subprocess.run", side_effect=FileNotFoundError("synthetic missing verifier")):
            result = self.runner.verify(model_xml=MODEL_XML, queries=QUERIES)
        self.assertEqual(result.status, "tool_not_found")
        self.assertIsNone(result.returncode)
        self.assertIn("synthetic missing verifier", result.stderr)

    def test_process_errors_override_complete_verdicts(self) -> None:
        for returncode, stdout, stderr in (
            (1, COMPLETE_SUCCESS, ""),
            (1, COMPLETE_SUCCESS.replace("satisfied", "NOT satisfied"), ""),
            (0, COMPLETE_SUCCESS, "syntax error in second query"),
            (0, COMPLETE_SUCCESS, "queries.q:2: error: invalid expression"),
            (0, COMPLETE_SUCCESS, "Error loading model"),
            (0, COMPLETE_SUCCESS, "Fatal error during verification"),
            (0, COMPLETE_SUCCESS + "Error: cannot finish verification\n", ""),
            (0, COMPLETE_SUCCESS, "out of memory"),
        ):
            with self.subTest(returncode=returncode, stdout=stdout, stderr=stderr):
                self.assertEqual(self.run_completed(stdout, returncode=returncode, stderr=stderr).status, "error")

    def test_missing_duplicate_and_extra_results_fail_closed(self) -> None:
        for stdout in (
            "",
            FIRST_SUCCESS.replace("satisfied", "NOT satisfied"),
            FIRST_SUCCESS.replace("is satisfied", "is inconclusive"),
            FIRST_SUCCESS + FIRST_SUCCESS,
            FIRST_SUCCESS + "-- Formula is satisfied.\n",
            COMPLETE_SUCCESS + "-- Formula is satisfied.\n",
            COMPLETE_SUCCESS.replace("formula 2", "formula 3"),
            COMPLETE_SUCCESS.replace("formula 1", "formula 0"),
            COMPLETE_SUCCESS + "Verifying formula 3\n",
            "Verifying formula 1\n" + COMPLETE_SUCCESS,
            "-- Formula is satisfied.\n" + FIRST_SUCCESS.replace("formula 1", "formula 2"),
        ):
            with self.subTest(stdout=stdout):
                self.assertEqual(self.run_completed(stdout).status, "error")

    def test_complete_negative_results_remain_not_satisfied(self) -> None:
        stdout = COMPLETE_SUCCESS.replace("-- Formula is satisfied.", "-- Formula is NOT satisfied.", 1)
        self.assertEqual(self.run_completed(stdout).status, "not_satisfied")

    def test_headerless_output_still_requires_complete_coverage(self) -> None:
        line = "-- Formula is satisfied.\n"
        self.assertEqual(self.run_completed(line * 2).status, "satisfied")
        self.assertEqual(self.run_completed(line).status, "error")
        self.assertEqual(self.run_completed(line * 3).status, "error")

    def test_error_names_in_paths_traces_and_warnings_are_not_diagnostics(self) -> None:
        stdout = COMPLETE_SUCCESS.replace("queries.q", "D:/error/models/queries.q")
        stdout += "State:\n( P.Error )\nerror_count=0\nerror = 0\n"
        result = self.run_completed(stdout, stderr="Warning: error bounds are approximate\nNo errors.\n")
        self.assertEqual(result.status, "satisfied")

    def test_counts_ignore_query_comments_and_blank_lines(self) -> None:
        queries = "// first query\nA[] not deadlock\n\n/* second query follows */\nE<> true\n"
        result = self.run_completed(COMPLETE_SUCCESS, model_xml=MODEL_XML, queries=queries)
        self.assertEqual(result.status, "satisfied")
        self.assertEqual([item.formula for item in result.query_results], QUERIES.splitlines())

    def test_repeated_formula_text_is_not_deduplicated(self) -> None:
        queries = "A[] not deadlock\nA[] not deadlock\n"
        result = self.run_completed(COMPLETE_SUCCESS, model_xml=MODEL_XML, queries=queries)
        self.assertEqual(result.status, "satisfied")
        self.assertEqual(len(result.query_results), 2)

    def test_embedded_queries_and_query_paths_enforce_coverage(self) -> None:
        query_path = self.runner.config.workspace / "input.q"
        query_path.write_text(QUERIES, encoding="utf-8")
        for inputs in ({"model_xml": MODEL_XML}, {"model_xml": MODEL_XML, "query_path": query_path}):
            with self.subTest(inputs=inputs):
                self.assertEqual(self.run_completed(FIRST_SUCCESS, **inputs).status, "error")
                self.assertEqual(self.run_completed(COMPLETE_SUCCESS, **inputs).status, "satisfied")


if __name__ == "__main__":
    unittest.main()
