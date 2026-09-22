"""Read-only source provenance/symbol audit; not verification or a query parser."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
BASE = 'aeeb62d4893db7f4bfd7d4243932860c50132f66'
FILES = [
    'manifests/v1.md', 'manifests/collaboration-v1.yaml',
    'levels_tex/MAC_resource_scheduling_formalization.tex',
    'src/uppaal_mcp/mac/alpha.py', 'src/uppaal_mcp/mac/generator.py',
    'src/uppaal_mcp/integrated/adapt.py',
    'src/uppaal_mcp/integrated/boundary.py',
    'src/uppaal_mcp/integrated/generator.py',
    'src/uppaal_mcp/sdn/generator.py',
]
hashes = {}
for name in FILES:
    actual = (ROOT / name).read_bytes()
    expected = subprocess.check_output(['git', 'show', f'{BASE}:{name}'], cwd=ROOT)
    if actual != expected:
        raise SystemExit(f'Source drift: {name}')
    hashes[name] = hashlib.sha256(actual).hexdigest()
adapt = (ROOT / FILES[5]).read_text()
mac = (ROOT / FILES[4]).read_text()
for symbol in ['mac_obs_ack_late', 'mac_obs_ack_active', 'mac_c_obs_ack', 'mac_D_phy_ack']:
    if symbol not in adapt:
        raise SystemExit(f'Missing ACK symbol: {symbol}')
if 'phy_ack_timeout' not in mac:
    raise SystemExit('Missing timeout symbol')
print(json.dumps({'status': 'static_source_audit_only', 'base': BASE,
                  'verification': 'not_run', 'sha256': hashes}, indent=2))
