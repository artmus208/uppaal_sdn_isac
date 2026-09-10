"""The amendment changes one exact pin; it never disables source validation."""
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
from uppaal_mcp.integrated.inputs import load, SOURCE_PIN_REVISIONS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'src/uppaal_mcp/phy/alpha.py'

class PinRevisionTests(unittest.TestCase):
    def test_corrected_source_is_recorded_in_provenance(self):
        *_, provenance, context = load(ROOT)
        self.assertEqual(provenance[SOURCE], hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest())
        self.assertEqual(provenance[SOURCE], SOURCE_PIN_REVISIONS[SOURCE][1])

    def test_old_and_unreviewed_sources_are_rejected(self):
        # Keep this regression runnable in shallow CI checkouts, without Git history.
        old = (ROOT / 'evidence/governance/20260908-gate1-readiness/'
               'decision-documents-ru/threshold-correction/ci-fix/phy-alpha-before.txt').read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(), SOURCE_PIN_REVISIONS[SOURCE][0])
        read = Path.read_bytes
        for raw in (old, (ROOT / SOURCE).read_bytes() + b'\n# unreviewed edit\n'):
            with self.subTest(hash=hashlib.sha256(raw).hexdigest()):
                def read_override(path):
                    return raw if path == ROOT / SOURCE else read(path)
                with patch.object(Path, 'read_bytes', read_override):
                    with self.assertRaisesRegex(ValueError, 'pinned source changed: src/uppaal_mcp/phy/alpha.py'):
                        load(ROOT)
