import os
import unittest

from uppaal_mcp.paths import (
    is_windows_path,
    local_path,
    windows_to_wsl_path,
    wsl_to_windows_path,
)


class PathTests(unittest.TestCase):
    def test_windows_path_detection(self) -> None:
        self.assertTrue(is_windows_path(r"C:\Program Files\x.exe"))
        self.assertTrue(is_windows_path("D:/tools/verifyta.exe"))
        self.assertFalse(is_windows_path("/mnt/c/tools/verifyta.exe"))

    def test_windows_to_wsl_path(self) -> None:
        self.assertEqual(
            windows_to_wsl_path(r"C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe"),
            "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe",
        )

    def test_wsl_to_windows_path(self) -> None:
        self.assertEqual(
            wsl_to_windows_path("/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe"),
            r"C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe",
        )

    def test_local_path_accepts_windows_path_under_wsl(self) -> None:
        path = local_path(r"C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe")
        if os.name == "nt":
            self.assertEqual(str(path), r"C:\Program Files (x86)\UPPAAL-5.0.0\bin\verifyta.exe")
        else:
            self.assertEqual(str(path), "/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe")


if __name__ == "__main__":
    unittest.main()
