#!/usr/bin/env python3
"""Read-only extraction of pinned N=1 XML; never invokes a verifier."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.parsers.expat

BASE = '8237e8c2bec41aa1bb943cc33be1ac9586d03759'
MANIFEST = 'manifests/baselines/uav-family-r1.yaml'
MANIFEST_HASH = '5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_with_lines(path):
    parser = xml.parsers.expat.ParserCreate()
    stack = []
    roots = []
    def start(tag, attrs):
        node = {'tag': tag, 'attrs': attrs, 'line': parser.CurrentLineNumber,
                'text': '', 'children': []}
        (stack[-1]['children'] if stack else roots).append(node)
        stack.append(node)
    def end(tag):
        stack.pop()
    def data(value):
        stack[-1]['text'] += value
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = data
    parser.Parse(path.read_bytes(), True)
    return roots[0]


def children(n, tag):
    return [c for c in n['children'] if c['tag'] == tag]


def one(n, tag):
    found = children(n, tag)
    return found[0] if found else {'text': '', 'attrs': {}, 'line': None}


def extract(root):
    manifest = root / MANIFEST
    assert sha(manifest) == MANIFEST_HASH, 'family manifest drift'
    m = json.loads(manifest.read_text())
    n1 = next(x for x in m['models'] if x['N'] == 1)
    for item in n1['files'].values():
        assert sha(root / item['path']) == item['sha256'], item['path']
    path = n1['files']['model.xml']['path']
    tree = parse_with_lines(root / path)
    templates = []
    for t in children(tree, 'template'):
        locations = []
        for loc in children(t, 'location'):
            locations.append({'id': loc['attrs']['id'], 'name': one(loc, 'name')['text'],
                'line': loc['line'], 'committed': bool(children(loc, 'committed')),
                'urgent': bool(children(loc, 'urgent')),
                'invariants': [c['text'] for c in children(loc, 'label') if c['attrs']['kind'] == 'invariant']})
        edges = []
        for i, e in enumerate(children(t, 'transition')):
            edges.append({'edge_index': i, 'line': e['line'],
                'source': one(e, 'source')['attrs']['ref'], 'target': one(e, 'target')['attrs']['ref'],
                **{c['attrs']['kind']: c['text'] for c in children(e, 'label')}})
        templates.append({'name': one(t, 'name')['text'], 'line': t['line'],
            'initial': one(t, 'init')['attrs']['ref'], 'declaration': one(t, 'declaration')['text'],
            'locations': locations, 'transitions': edges})
    assert len(templates) == n1['process_count'] == 50
    return {'evidence_kind': 'static_validation', 'property_verdict': 'not_applicable',
        'base_commit': BASE, 'manifest': MANIFEST, 'manifest_sha256': MANIFEST_HASH,
        'model': path, 'model_hash': n1['files']['model.xml']['sha256'],
        'service_query': (root / n1['files']['p4/u0-service.q']['path']).read_text().strip(),
        'service_query_hash': n1['files']['p4/u0-service.q']['sha256'],
        'n1_pins': n1, 'global_declaration': one(tree, 'declaration')['text'],
        'system': one(tree, 'system')['text'], 'templates': templates}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[3])
    p.add_argument('--check', type=Path, help='Compare existing inventory; no writes')
    args = p.parse_args()
    result = extract(args.root.resolve())
    if args.check:
        assert json.loads(args.check.read_text()) == result, 'inventory drift'
        print('Static inventory matches: 50 templates and all N=1 baseline pins; no model checking.')
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
