import os
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from uppaal_mcp import config


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()
        self.which = patch.object(config.shutil, "which", return_value=None).start()
        self.is_file = patch.object(Path, "is_file", return_value=False).start()

    def platform(self, name: str) -> None:
        # Replace this module's os reference, not global os.name: pathlib must
        # still instantiate the host's concrete Path class on every test host.
        patch.object(config, "os", SimpleNamespace(name=name, getenv=os.getenv)).start()

    def test_explicit_path_has_precedence_over_environment_and_discovery(self) -> None:
        os.environ.update(UPPAAL_VERIFYTA_PATH="preferred", VERIFYTA_PATH="legacy")
        self.which.return_value = "from-path"
        self.assertEqual(config.UppaalConfig.from_env(verifyta_path="explicit").verifyta_path, "explicit")
        self.which.assert_not_called()
        self.is_file.assert_not_called()

    def test_preferred_environment_path_has_precedence(self) -> None:
        os.environ.update(UPPAAL_VERIFYTA_PATH="preferred", VERIFYTA_PATH="legacy")
        self.assertEqual(config.UppaalConfig.from_env().verifyta_path, "preferred")
        self.which.assert_not_called()

    def test_legacy_environment_path_is_supported(self) -> None:
        os.environ["VERIFYTA_PATH"] = "legacy"
        self.assertEqual(config.UppaalConfig.from_env().verifyta_path, "legacy")
        self.which.assert_not_called()

    def test_path_precedes_existing_install_locations_on_both_platforms(self) -> None:
        for platform_name in ("nt", "posix"):
            with self.subTest(platform=platform_name):
                self.platform(platform_name)
                self.which.return_value = "selected-by-path"
                self.is_file.return_value = True
                self.assertEqual(config.resolve_verifyta_path(), "selected-by-path")
        self.is_file.assert_not_called()

    def test_path_exe_name_is_tried_after_verifyta(self) -> None:
        self.which.side_effect = [None, "selected-verifyta.exe"]
        self.assertEqual(config.resolve_verifyta_path(), "selected-verifyta.exe")
        self.assertEqual([call.args[0] for call in self.which.call_args_list], ["verifyta", "verifyta.exe"])

    def test_native_windows_install_discovery(self) -> None:
        self.platform("nt")
        for selected in config.NATIVE_WINDOWS_VERIFYTA_PATHS:
            with self.subTest(path=selected):
                # Use the host's concrete Path on both sides while simulating
                # Windows selection, without touching the real filesystem.
                with patch.object(Path, "is_file", new=lambda path: path == Path(selected)):
                    self.assertEqual(config.resolve_verifyta_path(), selected)

    def test_windows_discovery_does_not_choose_a_wsl_location(self) -> None:
        self.platform("nt")
        with patch.object(Path, "is_file", new=lambda path: path == Path(config.DEFAULT_WSL_VERIFYTA)):
            self.assertEqual(config.resolve_verifyta_path(), config.DEFAULT_WINDOWS_VERIFYTA)

    def test_wsl_legacy_install_discovery(self) -> None:
        self.platform("posix")
        with patch.object(Path, "is_file", new=lambda path: path == Path(config.DEFAULT_WSL_VERIFYTA)):
            self.assertEqual(config.resolve_verifyta_path(), config.DEFAULT_WSL_VERIFYTA)

    def test_missing_executable_keeps_legacy_fallback_for_runner_diagnostic(self) -> None:
        for platform_name, expected in (("nt", config.DEFAULT_WINDOWS_VERIFYTA), ("posix", config.DEFAULT_WSL_VERIFYTA)):
            with self.subTest(platform=platform_name):
                self.platform(platform_name)
                self.assertEqual(config.resolve_verifyta_path(), expected)

    def test_explicit_windows_path_normalization(self) -> None:
        for platform_name, expected in (("nt", r"D:\UPPAAL\app\bin\verifyta.exe"), ("posix", "/mnt/d/UPPAAL/app/bin/verifyta.exe")):
            with self.subTest(platform=platform_name):
                self.platform(platform_name)
                self.assertEqual(config.resolve_verifyta_path('  "D:\\UPPAAL\\app\\bin\\verifyta.exe"  '), expected)

    def test_workspace_and_timeout_environment_and_explicit_overrides(self) -> None:
        os.environ.update(UPPAAL_MCP_WORKSPACE="env-workspace", UPPAAL_TIMEOUT_SEC="12.5")
        self.assertEqual(config.UppaalConfig.from_env(verifyta_path="verifier").workspace, Path("env-workspace"))
        self.assertEqual(config.UppaalConfig.from_env(verifyta_path="verifier").timeout_sec, 12.5)
        explicit = config.UppaalConfig.from_env(verifyta_path="verifier", workspace="own-workspace", timeout_sec=0)
        self.assertEqual(explicit.workspace, Path("own-workspace"))
        self.assertEqual(explicit.timeout_sec, 0)


if __name__ == "__main__":
    unittest.main()
