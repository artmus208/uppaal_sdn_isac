"""Load only the exact reviewed specification inputs, before importing sources."""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

BASE = 'dc7eeb05f1fd3f2a4775428b1cd250363893128d'
SOURCE = '7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb'
SPEC = 'evidence/instantiation/20260907-p2-scope'
PINS = {
    'inventory.json': 'ed6a022a2744bed0ee8b30586157f73723ae89d01568e904fb6b3baff8b7a195',
    'instance-vector.json': 'ebbaabd0603eb3dfc8b537b19e61e36f35878f84173cca398e243871eb572a45',
}
# User-authorized amendment, 2026-09-10: conservative threshold equality.
# Preserve the historical inventory; accept only the exact replacement bytes.
SOURCE_PIN_REVISIONS = {
    'src/uppaal_mcp/phy/alpha.py': (
        '7f77814e3ad6fafa15c32df5e86accfef00995d193fa6182f178802f3ac809e9',
        'cdaa6798d3e278c630a7b379b88b96b78287bf92e7a48d958489eeff851cb42e',
    ),
}
# Explicit operational context only; scientific manifests and all model inputs
# remain strict pins. Keep both historical and observed bytes in the evidence.
CONTEXT_DOCUMENTS = frozenset({'AGENTS.md'})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(root: Path):
    root = root.resolve()
    docs = {}
    provenance = {}
    context = {}
    for name, expected in PINS.items():
        path = root / SPEC / name
        raw = path.read_bytes()
        if sha(raw) != expected:
            raise ValueError(f'unsupported specification input: {name}')
        docs[name] = json.loads(raw)
        provenance[f'{SPEC}/{name}'] = expected
    inventory = docs['inventory.json']
    for name, record in inventory['sources'].items():
        raw = (root / name).read_bytes()
        if name in CONTEXT_DOCUMENTS:
            context[name] = {'pinned_sha256': record['sha256'],
                             'actual_sha256': sha(raw),
                             'role': 'operational_context_not_model_input'}
            continue
        expected = record['sha256']
        if name in SOURCE_PIN_REVISIONS:
            historical, replacement = SOURCE_PIN_REVISIONS[name]
            if expected != historical:
                raise ValueError(f'unsupported source revision origin: {name}')
            expected = replacement
        if sha(raw) != expected:
            raise ValueError(f'pinned source changed: {name}')
        provenance[name] = expected
    models, queries = {}, {}
    for layer in ('phy', 'mac', 'sdn', 'app'):
        key = 'stored:app' if layer == 'app' else f'generated:{layer}:with_observers'
        expected = inventory['models'][key]
        if layer == 'app':
            raw = (root / expected['origin']).read_bytes()
            xml = raw.decode('utf-8')
            queries[layer] = [q.findtext('formula') or '' for q in ET.fromstring(xml).findall('./queries/query')]
        else:
            mod = importlib.import_module(f'uppaal_mcp.{layer}.generator')
            module_path = f'src/uppaal_mcp/{layer}/generator.py'
            if sha(Path(mod.__file__).read_bytes()) != provenance[module_path]:
                raise ValueError(f'imported generator differs from pinned checkout: {layer}')
            generated = mod.generate_uppaal_model(mode='with_observers', layout='readable')
            xml = generated.model_xml
            raw = xml.encode('utf-8')
            if sha(generated.queries.encode()) != expected['query_hash']:
                raise ValueError(f'generated query hash mismatch: {layer}')
            queries[layer] = [s.strip() for s in generated.queries.splitlines() if s.strip() and not s.strip().startswith('//')]
        if sha(raw) != expected['model_hash']:
            raise ValueError(f'generated model hash mismatch: {layer}')
        models[layer] = ET.fromstring(xml)
    return docs['instance-vector.json'], inventory, models, queries, provenance, context
