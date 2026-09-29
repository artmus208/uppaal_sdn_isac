"""Reproduce the new manifest without changing models or the operational contract."""
from pathlib import Path
import json
import runpy
import sys
ROOT = Path(__file__).resolve().parents[3]
module = runpy.run_path(str(ROOT / 'scripts/check_family_baseline.py'))
expected = json.dumps(module['expected_manifest'](ROOT), ensure_ascii=False, indent=2) + '\n'
path = ROOT / module['MANIFEST']
if sys.argv[1:] == ['--write']:
    path.write_text(expected, encoding='utf-8')
elif sys.argv[1:]:
    raise SystemExit('Usage: materialize.py [--write]')
elif path.read_text(encoding='utf-8') != expected:
    raise SystemExit('manifest reproduction mismatch')
print('Family manifest reproduced; no activation or model-checking claim.')
