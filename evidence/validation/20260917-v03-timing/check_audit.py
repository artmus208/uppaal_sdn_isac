"""Check that corrupted inputs/outputs cannot be reported as a matching audit."""
import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import audit


class AuditIntegrity(unittest.TestCase):
    def test_clean_saved_outputs(self):
        with patch("sys.argv", ["audit.py"]), contextlib.redirect_stdout(io.StringIO()):
            audit.main()

    def test_changed_model_is_rejected(self):
        read = Path.read_bytes
        target = audit.ROOT / audit.INPUTS["model"]
        def changed(path):
            original = read(path)
            return original + b"\n" if path == target else original
        with patch.object(Path, "read_bytes", changed):
            with self.assertRaisesRegex(ValueError, "Pinned input mismatch: model"):
                audit.build()

    def test_missing_integration_contract_is_rejected(self):
        read = Path.read_text
        target = audit.HERE / "contracts.json"
        def changed(path, *args, **kwargs):
            text = read(path, *args, **kwargs)
            if path == target:
                data = json.loads(text)
                del data["integration"]["D_bus"]
                return json.dumps(data)
            return text
        with patch.object(Path, "read_text", changed):
            with self.assertRaisesRegex(ValueError, "Integration parameter_set coverage differs"):
                audit.build()

    def test_stale_generated_output_is_rejected(self):
        read = Path.read_bytes
        target = audit.HERE / "timing-inventory.json"
        def changed(path):
            original = read(path)
            return original + b" " if path == target else original
        with patch.object(Path, "read_bytes", changed), patch("sys.argv", ["audit.py"]):
            with self.assertRaisesRegex(SystemExit, "STALE OR MISSING: timing-inventory.json"):
                audit.main()


if __name__ == "__main__":
    unittest.main(verbosity=2)
