from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig
import tempfile
import unittest

from uppaal_mcp.examples import get_builtin_example


class CliExitTests(unittest.TestCase):
    """Exercise process exit codes, including the module and installed script.

    Mocked responses are software fixtures, never UPPAAL verification evidence.
    The parent process does not call the exit-code helper directly.
    """

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.env = os.environ.copy()
        self.env.update(
            UPPAAL_MCP_WORKSPACE=str(self.root / "runs"),
            UPPAAL_VERIFYTA_PATH=str(self.root / "missing-verifyta"),
            PYTHONDONTWRITEBYTECODE="1",
        )
        self.model = self.root / "model.xml"
        self.queries = self.root / "queries.q"
        example = get_builtin_example("deadlock_free")
        self.model.write_text(example.model_xml, encoding="utf-8")
        self.queries.write_text(example.queries, encoding="utf-8")

    def run_cli(self, *args: str, patch: str | None = None, response=None, console=False):
        env = self.env.copy()
        if patch:
            # Patch the backend inside the child, then execute the actual module
            # entry point. A missing SystemExit(main()) must fail these tests.
            env["CLI_TEST_PATCH"] = patch
            env["CLI_TEST_RESPONSE"] = json.dumps(response)
            script = """
import json
import os
import runpy
import sys
from types import SimpleNamespace
from unittest.mock import patch
target = os.environ["CLI_TEST_PATCH"]
response = json.loads(os.environ["CLI_TEST_RESPONSE"])
if target.startswith("uppaal_mcp.verifyta."):
    response = SimpleNamespace(to_dict=lambda payload=response: payload)
sys.argv = ["uppaal-verifyta", *sys.argv[1:]]
with patch(target, return_value=response):
    runpy.run_module("uppaal_mcp.cli", run_name="__main__")
"""
            command = [sys.executable, "-c", script, *args]
        elif console:
            suffix = ".exe" if os.name == "nt" else ""
            executable = Path(sysconfig.get_path("scripts")) / f"uppaal-verifyta{suffix}"
            self.assertTrue(executable.is_file(), "Install the project before running its CLI tests.")
            command = [str(executable), *args]
        else:
            command = [sys.executable, "-m", "uppaal_mcp.cli", *args]
        completed = subprocess.run(
            command, capture_output=True, text=True, env=env, timeout=30, check=False,
        )
        self.assertEqual(completed.stderr, "", completed.stderr)
        payload = json.loads(completed.stdout)
        if patch:
            self.assertEqual(payload, response, "Exit handling must preserve the JSON response.")
        return completed.returncode, payload

    def test_missing_tool_version_module_and_console(self) -> None:
        for console in (False, True):
            with self.subTest(console=console):
                code, payload = self.run_cli("version", console=console)
                self.assertEqual(code, 2)
                self.assertEqual(payload["status"], "tool_not_found")

    def test_missing_tool_verify(self) -> None:
        code, payload = self.run_cli("verify", "--model", str(self.model), "--queries", str(self.queries))
        self.assertEqual(code, 2)
        self.assertEqual(payload["status"], "tool_not_found")

    def test_version_response_exit_codes(self) -> None:
        for status, code in (("ok", 0), ("error", 2), ("timeout", 2), ("tool_not_found", 2)):
            with self.subTest(status=status):
                actual, _ = self.run_cli(
                    "version", patch="uppaal_mcp.verifyta.VerifytaRunner.get_version",
                    response={"status": status, "stdout": "synthetic version fixture"},
                )
                self.assertEqual(actual, code)

    def test_verify_response_exit_codes(self) -> None:
        for status, code in (
            ("satisfied", 0), ("not_satisfied", 1), ("error", 2), ("timeout", 2),
            ("tool_not_found", 2), ("unknown", 2), ("inconclusive", 2),
            ("maybe", 2), ("mixed", 2), ("partial_satisfied", 2), ("oom", 2),
        ):
            with self.subTest(status=status):
                actual, _ = self.run_cli(
                    "verify", "--model", str(self.model),
                    patch="uppaal_mcp.verifyta.VerifytaRunner.verify",
                    response={"status": status, "returncode": 0},
                )
                self.assertEqual(actual, code)

    def test_nested_tool_failures_override_positive_summary(self) -> None:
        responses = [
            {"status": "satisfied", "returncode": 1},
            {"status": "satisfied", "query_results": [{"status": "inconclusive"}]},
            {"status": "satisfied", "runs": [{"status": "tool_not_found"}]},
        ]
        for response in responses:
            with self.subTest(response=response):
                code, _ = self.run_cli(
                    "verify", "--model", str(self.model),
                    patch="uppaal_mcp.verifyta.VerifytaRunner.verify", response=response,
                )
                self.assertEqual(code, 2)

    def test_layer_verification_dispatch(self) -> None:
        for layer in ("phy", "mac", "sdn"):
            for suffix, function, extra in (
                ("verify", "verify_contract", []),
                ("verify-property-pack", "verify_property_pack", ["--model", str(self.model), "--queries", str(self.queries)]),
                ("verify-scenario", f"{layer}_verify_scenario", ["synthetic"]),
                ("verify-all-scenarios", f"{layer}_verify_all_scenarios", []),
            ):
                with self.subTest(layer=layer, command=suffix):
                    response = {"ok": False, "results": [{"status": "timeout"}]}
                    code, _ = self.run_cli(
                        f"{layer}-{suffix}", *extra,
                        patch=f"uppaal_mcp.{layer}.tools.{function}", response=response,
                    )
                    self.assertEqual(code, 2)

    def test_scenario_expectations_and_aggregate_failures(self) -> None:
        negative = {
            "ok": True, "status": "not_satisfied", "expected_status": "not_satisfied",
            "result": {"status": "not_satisfied", "returncode": 0,
                       "query_results": [{"status": "not_satisfied"}, {"status": "satisfied"}]},
        }
        for layer in ("phy", "mac", "sdn"):
            for response, expected in (
                ({"ok": True, "results": [negative]}, 0),
                ({"ok": False, "results": [{"ok": False, "status": "satisfied", "expected_status": "not_satisfied"}]}, 1),
                ({"ok": True, "results": [negative, {"status": "error"}]}, 2),
                ({"ok": False, "results": []}, 1),
                ({"ok": True, "results": [{**negative, "result": {"status": "timeout"}}]}, 2),
            ):
                with self.subTest(layer=layer, response=response):
                    code, _ = self.run_cli(
                        f"{layer}-verify-all-scenarios",
                        patch=f"uppaal_mcp.{layer}.tools.{layer}_verify_all_scenarios", response=response,
                    )
                    self.assertEqual(code, expected)

    def test_static_validation_success_and_failure(self) -> None:
        for valid, expected in ((True, 0), (False, 1)):
            with self.subTest(valid=valid):
                if not valid:
                    self.model.write_text("<broken", encoding="utf-8")
                code, payload = self.run_cli("validate", "--model", str(self.model))
                self.assertEqual(code, expected)
                self.assertEqual(payload["ok"], valid)

    def test_static_only_property_packs(self) -> None:
        for layer in ("phy", "mac", "sdn"):
            with self.subTest(layer=layer):
                output = self.root / layer
                code, _ = self.run_cli(f"{layer}-generate", "--output-dir", str(output))
                self.assertEqual(code, 0)
                code, payload = self.run_cli(
                    f"{layer}-verify-property-pack", "--model", str(output / "model.xml"),
                    "--queries", str(output / "queries.q"), "--static-only",
                )
                self.assertEqual(code, 0)
                self.assertEqual(payload["status"], "validated")
                self.assertEqual(payload["result"]["query_results"], [])
                (output / "model.xml").write_text("<broken", encoding="utf-8")
                code, payload = self.run_cli(
                    f"{layer}-verify-property-pack", "--model", str(output / "model.xml"),
                    "--queries", str(output / "queries.q"), "--static-only",
                )
                self.assertEqual(code, 2)
                self.assertEqual(payload["status"], "static_error")

    def test_expected_negative_static_benchmarks(self) -> None:
        for layer in ("phy", "mac", "sdn"):
            with self.subTest(layer=layer):
                code, payload = self.run_cli(f"{layer}-validate-benchmarks")
                self.assertEqual(code, 0)
                self.assertTrue(payload["ok"])
                self.assertTrue(any(item["expected_static_ok"] is False for item in payload["results"]))
                code, payload = self.run_cli(
                    f"{layer}-benchmark", "broken_report_channel_declared_as_chan",
                )
                self.assertEqual(code, 0)
                self.assertFalse(payload["expected_static_ok"])

    def test_failed_static_benchmark_aggregate(self) -> None:
        for layer in ("phy", "mac", "sdn"):
            with self.subTest(layer=layer):
                code, _ = self.run_cli(
                    f"{layer}-validate-benchmarks",
                    patch=f"uppaal_mcp.{layer}.tools.{layer}_validate_benchmarks",
                    response={"ok": False, "results": [{"ok": False, "expected_static_ok": False,
                                                          "validation": {"ok": True}}]},
                )
                self.assertEqual(code, 1)

    def test_list_examples_module_and_console(self) -> None:
        for console in (False, True):
            with self.subTest(console=console):
                code, payload = self.run_cli("list-examples", console=console)
                self.assertEqual(code, 0)
                self.assertTrue(payload)


if __name__ == "__main__":
    unittest.main()
