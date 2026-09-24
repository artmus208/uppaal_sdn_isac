"""Pinned, property-specific C02 abstraction; not a replacement Gate 1 model."""
import argparse, hashlib, json, re
from pathlib import Path
import xml.etree.ElementTree as ET
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923/model.xml'
SOURCE_SHA = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'
KEEP = {'mac_c_phy_ack', 'mac_c_obs_ack', 'mac_obs_ack_active', 'mac_obs_ack_late'}
QUERY = 'A[] (!mac_obs_ack_late && (mac_obs_ack_active imply mac_c_obs_ack <= mac_D_phy_ack))\n'
def generate():
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA, 'Unreviewed baseline: stop'
    source = ET.fromstring(raw)
    sch = next(t for t in source.findall('template') if t.findtext('name') == 'mac_Template_A_SCH')
    names = {l.get('id'): l.findtext('name') for l in sch.findall('location')}
    assert names[sch.find('init').get('ref')] == 'Idle'
    wait = next(l for l in sch.findall('location') if l.findtext('name') == 'WaitPHYAck')
    invariant = wait.findtext("label[@kind='invariant']")
    assert invariant == 'mac_c_phy_ack <= mac_D_phy_ack'
    # All occurrences are exposed for review, including declaration/function text.
    refs = [{'line': n, 'text': line.strip()} for n, line in enumerate(raw.decode().splitlines(), 1)
            if any(re.search(r'\b' + v + r'\b', line) for v in KEEP)]
    nta = ET.Element('nta')
    ET.SubElement(nta, 'declaration').text = ('const int mac_D_phy_ack = 3;\n'
        'clock mac_c_phy_ack, mac_c_obs_ack;\n'
        'bool mac_obs_ack_active = false, mac_obs_ack_late = false;')
    t = ET.SubElement(nta, 'template'); ET.SubElement(t, 'name').text = 'C02Ack'
    for ident, name, x in [('idle', 'Inactive', '0'), ('wait', 'WaitPHYAck', '400')]:
        loc = ET.SubElement(t, 'location', id=ident, x=x, y='0')
        ET.SubElement(loc, 'name', x=x, y='-30').text = name
        if ident == 'wait': ET.SubElement(loc, 'label', kind='invariant', x=x, y='30').text = invariant
    ET.SubElement(t, 'init', ref='idle')
    mapping = []
    def edge(a, b, guard='', assignment='', comment=''):
        e = ET.SubElement(t, 'transition'); ET.SubElement(e, 'source', ref=a); ET.SubElement(e, 'target', ref=b)
        for kind, text in [('guard', guard), ('assignment', assignment), ('comments', comment)]:
            if text: ET.SubElement(e, 'label', kind=kind).text = text
    for n, e in enumerate(sch.findall('transition')):
        a, b = names[e.find('source').get('ref')], names[e.find('target').get('ref')]
        if (a == 'WaitPHYAck') == (b == 'WaitPHYAck'): continue
        updates = []
        for part in (e.findtext("label[@kind='assignment']") or '').split(','):
            if part.strip().split('=')[0].strip() in KEEP: updates.append(part.strip())
        guard = e.findtext("label[@kind='guard']") or ''
        assert a == 'WaitPHYAck' or not guard
        edge('wait' if a == 'WaitPHYAck' else 'idle', 'wait' if b == 'WaitPHYAck' else 'idle', guard, ', '.join(updates), f'scheduler edge {n}: {a} -> {b}; synchronization hidden')
        mapping.append({'scheduler_edge_index': n, 'source': a, 'target': b, 'guard': guard, 'retained_updates': updates})
    assert len(mapping) == 5
    for loc in ['idle', 'wait']: edge(loc, loc, comment='Hidden concrete actions may stutter; no fairness imposed')
    ET.SubElement(nta, 'system').text = 'Ack = C02Ack();\nsystem Ack;'
    ET.indent(nta)
    encode = lambda tree: ET.tostring(tree, encoding='utf-8', xml_declaration=True) + b'\n'
    normal = encode(nta)
    t.find("location[@id='wait']").remove(t.find("location[@id='wait']/label[@kind='invariant']"))
    control = encode(nta)
    report = {'kind': 'static source audit, not model checking', 'source_path': str(SOURCE.relative_to(ROOT)), 'source_hash': SOURCE_SHA,
              'retained_variables': sorted(KEEP), 'reference_inventory': refs, 'transition_mapping': mapping,
              'model_hash': hashlib.sha256(normal).hexdigest(), 'negative_control_hash': hashlib.sha256(control).hexdigest(),
              'query_hash': hashlib.sha256(QUERY.encode()).hexdigest()}
    assert report['query_hash'] == 'cec919bc6e2d960160976799d3d52ff4f25eea9f136f7b0231c02cec13f162db'
    return {'model.xml': normal, 'negative-control.xml': control, 'C02.q': QUERY.encode(),
            'active.q': b'E<> mac_obs_ack_active\n', 'deadline.q': b'E<> mac_obs_ack_active && mac_c_obs_ack == mac_D_phy_ack\n',
            'source-audit.json': (json.dumps(report, indent=2) + '\n').encode()}
if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--check', action='store_true'); args = p.parse_args()
    for name, data in generate().items():
        if args.check: assert (HERE / name).read_bytes() == data, name
        else: (HERE / name).write_bytes(data)
    print('Pinned-source generation and query identity OK (static only)')
