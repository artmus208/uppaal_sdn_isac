"""Run the unchanged memory-limit test under a chosen Python interpreter."""
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(root/'src'), str(root/'tests')]
from test_verification_manager import ManagerTests

print('interpreter:', sys.executable, flush=True)
result = unittest.TextTestRunner(verbosity=2).run(
    unittest.TestSuite([ManagerTests('test_memory_limit_measures_real_child')]))
sys.exit(0 if result.wasSuccessful() else 1)
