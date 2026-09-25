"""Pinned syntactic premises and finite induction obligations; NOT UPPAAL verification."""
import copy
import hashlib
import itertools
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923/model.xml'
MODEL_HASH = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
NAME = 'sdn_Template_A_REC'
TOKEN = re.compile(r'\bsdn_attempt_\w+\b')
BLOCK = '''
bool sdn_attempt_active=false, sdn_attempt_bad=false, sdn_attempt_protocol_error=false;
int[0,2] sdn_attempt_primary=0, sdn_attempt_rollback=0;
int[0,3] sdn_attempt_total=0;
void sdn_attempt_start() {
    if (sdn_attempt_active) sdn_attempt_protocol_error=true;
    else {
        sdn_attempt_active=true;
        sdn_attempt_primary=0; sdn_attempt_rollback=0; sdn_attempt_total=0;
    }
}
void sdn_attempt_dispatch(bool rollback) {
    if (!sdn_attempt_active) sdn_attempt_protocol_error=true;
    if (rollback) sdn_attempt_rollback=sdn_attempt_rollback<2 ? sdn_attempt_rollback+1 : 2;
    else sdn_attempt_primary=sdn_attempt_primary<2 ? sdn_attempt_primary+1 : 2;
    sdn_attempt_total=sdn_attempt_total<3 ? sdn_attempt_total+1 : 3;
    sdn_attempt_bad=sdn_attempt_bad || sdn_attempt_primary>1 || sdn_attempt_rollback>1 || sdn_attempt_total>2;
}
void sdn_attempt_finish() {
    if (!sdn_attempt_active) sdn_attempt_protocol_error=true;
    sdn_attempt_active=false;
}
'''
CALLS = {'start': 'sdn_attempt_start()', 'primary': 'sdn_attempt_dispatch(false)',
         'rollback': 'sdn_attempt_dispatch(true)', 'finish': 'sdn_attempt_finish()'}
# Complete pinned topology, including duplicated late-outcome edges.
EXPECTED = [
    ('StableConfig', 'FailureDetected', 'start'),
    ('StableConfig', 'FailureDetected', 'start'),
    ('FailureDetected', 'StandbySwitch', 'primary'),
    ('FailureDetected', 'ReactiveReembedding', 'primary'),
    ('FailureDetected', 'Rollback', 'rollback'),
    ('StandbySwitch', 'StableConfig', 'finish'),
    ('ReactiveReembedding', 'StableConfig', 'finish'),
    ('StandbySwitch', 'Rollback', 'rollback'),
    ('ReactiveReembedding', 'Rollback', 'rollback'),
    ('Rollback', 'StableConfig', 'finish'),
    ('Rollback', 'RecoveryFailed', 'finish'),
    ('FailureDetected', 'RecoveryFailed', 'finish'),
    ('StandbySwitch', 'RecoveryFailed', 'finish'),
    ('ReactiveReembedding', 'RecoveryFailed', 'finish'),
    ('RecoveryFailed', 'RecoveryFailed', 'none'),
    ('StandbySwitch', 'StableConfig', 'finish'),
    ('ReactiveReembedding', 'StableConfig', 'finish'),
    ('Rollback', 'StableConfig', 'finish'),
    ('Rollback', 'RecoveryFailed', 'finish'),
    ('FailureDetected', 'RecoveryFailed', 'finish'),
    ('StandbySwitch', 'RecoveryFailed', 'finish'),
    ('ReactiveReembedding', 'RecoveryFailed', 'finish'),
]


def norm(s):
    return re.sub(r'\s+', '', s or '')


def premises(root):
    declaration = norm(root.findtext('declaration'))
    assert declaration.count(norm(BLOCK)) == 1, 'Recorder definitions changed'
    assert 'sdn_attempt_' not in declaration.replace(norm(BLOCK), ''), 'Other global reference/write'
    system = root.findtext('system')
    assert re.findall(r'(\w+)\s*=\s*sdn_Template_A_REC\s*\(\s*\)', system) == ['sdn_A_REC_0']
    processes = [p.strip() for p in re.search(r'\bsystem\s+([^;]+)', system).group(1).split(',')]
    assert processes.count('sdn_A_REC_0') == 1
    assert system.count(NAME) == 1, 'Additional/parameterized recovery instance'
    rec = next(t for t in root.findall('template') if t.findtext('name') == NAME)
    locations = {p.get('id'): p.findtext('name') for p in rec.findall('location')}
    assert len(locations) == 6 and len(set(locations.values())) == 6
    assert locations[rec.find('init').get('ref')] == 'StableConfig'
    edges = rec.findall('transition')
    assert len(edges) == 22
    for t in root.findall('template'):
        assert not TOKEN.search((t.findtext('declaration') or '') + (t.findtext('parameter') or ''))
        for label in t.iter('label'):
            if not TOKEN.search(label.text or ''):
                continue
            assert t is rec and label.get('kind') == 'assignment', 'External reference, writer or alias'
            parts = [norm(p) for p in (label.text or '').split(',') if TOKEN.search(p)]
            assert len(parts) == 1 and parts[0] in CALLS.values(), 'Unexpected recorder operation'
    inventory = []
    for n, (edge, expected) in enumerate(zip(edges, EXPECTED)):
        a = locations[edge.find('source').get('ref')]
        b = locations[edge.find('target').get('ref')]
        assignments = edge.findall("label[@kind='assignment']")
        assert len(assignments) == 1
        parts = [norm(p) for p in (assignments[0].text or '').split(',') if TOKEN.search(p)]
        op = next((k for k, v in CALLS.items() if parts == [v]), 'none')
        assert (a, b, op) == expected, f'Edge {n} topology/recorder mismatch'
        inventory.append(dict(edge=n, source=a, target=b, operation=op,
                              guard=edge.findtext("label[@kind='guard']"),
                              synchronization=edge.findtext("label[@kind='synchronisation']")))
    return inventory


def invariant(location, s):
    a, p, r, total, bad, error = s
    if bad or error or p > 1 or r > 1 or total != p + r:
        return False
    if location in ('StableConfig', 'RecoveryFailed'):
        return not a
    if location == 'FailureDetected':
        return a and (p, r, total) == (0, 0, 0)
    if location in ('StandbySwitch', 'ReactiveReembedding'):
        return a and (p, r, total) == (1, 0, 1)
    return location == 'Rollback' and a and r == 1 and total == p + 1


def effect(op, s):
    # Explicit transcription of the exact definitions asserted above.
    a, p, r, total, bad, error = s
    if op == 'start':
        if a:
            error = True
        else:
            a, p, r, total = True, 0, 0, 0
    elif op in ('primary', 'rollback'):
        error = error or not a
        if op == 'primary':
            p = min(p + 1, 2)
        else:
            r = min(r + 1, 2)
        total = min(total + 1, 3)
        bad = bad or p > 1 or r > 1 or total > 2
    elif op == 'finish':
        error, a = error or not a, False
    return a, p, r, total, bad, error


def induction(edges):
    assert invariant('StableConfig', (False, 0, 0, 0, False, False))
    checked = 0
    for a, b, op in edges:
        for s in itertools.product((False, True), range(3), range(3), range(4), (False, True), (False, True)):
            if invariant(a, s):
                assert invariant(b, effect(op, s)), (a, b, op, s)
                checked += 1
    return checked


def main():
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest() == MODEL_HASH
    root = ET.parse(MODEL).getroot()
    inventory = premises(root)
    checked = induction(EXPECTED)
    mutations = []
    for kind in ('missing-finish', 'external-write', 'duplicate-instance'):
        mutant = copy.deepcopy(root)
        rec = next(t for t in mutant.findall('template') if t.findtext('name') == NAME)
        if kind == 'missing-finish':
            label = rec.findall('transition')[5].find("label[@kind='assignment']")
            label.text = label.text.replace(', sdn_attempt_finish()', '')
        elif kind == 'external-write':
            ET.SubElement(mutant.find('template/transition'), 'label', kind='assignment').text = 'sdn_attempt_primary=2'
        else:
            mutant.find('system').text += '\nOther = sdn_Template_A_REC();'
        try:
            premises(mutant)
        except AssertionError:
            mutations.append(kind)
        else:
            raise AssertionError('Mutation not rejected: ' + kind)
    try:
        induction(EXPECTED + [('StandbySwitch', 'StandbySwitch', 'primary')])
    except AssertionError:
        mutations.append('repeated-primary-invariant-obligation')
    else:
        raise AssertionError('Repeated dispatch not rejected')
    print(json.dumps(dict(kind='static inductive proof support; NOT model checking',
                         model_hash=MODEL_HASH, recovery_instances=1,
                         checked_edge_valuation_obligations=checked,
                         rejected_mutations=mutations, edges=inventory), indent=2))


if __name__ == '__main__':
    main()
