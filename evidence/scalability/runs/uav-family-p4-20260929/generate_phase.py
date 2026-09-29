"""Measure the pinned generator with writes confined to this Issue's directory."""
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = ROOT / 'evidence/scalability/family-series-68'
sys.path.insert(0, str(SOURCE))
import generate
out = Path(sys.argv[1]).resolve()
if not out.is_relative_to(HERE) or out.exists():
    raise SystemExit('Fresh output inside Issue scope required')
pins = generate.inputs()
written = {}
for n in generate.SIZES:
    for name, data in generate.artifacts(n, pins).items():
        if data != (SOURCE / f'generated/n{n}' / name).read_bytes():
            raise SystemExit('Generation differs from frozen bytes')
        path = out / f'n{n}' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        written[str(path.relative_to(out))] = generate.sha(data)
print(json.dumps({'files': written, 'count': len(written)}))
