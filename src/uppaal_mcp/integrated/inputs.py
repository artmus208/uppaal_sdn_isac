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


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(root: Path):
    root = root.resolve()
    docs = {}
    provenance = {}
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
        if sha(raw) != record['sha256']:
            raise ValueError(f'pinned source changed: {name}')
        provenance[name] = record['sha256']
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
    return docs['instance-vector.json'], inventory, models, queries, provenance
