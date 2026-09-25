"""Conservative structural inventory, not model checking or reachability analysis."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / 'evidence/governance/20260906-baseline/gate1-20260923/model.xml'
HASH = '592678ed678ce8f70cf278f542e48bd2bb739969b53a962423d3e63f91e3e1e2'


def labels(element):
    return {x.get('kind'): (x.text or '').strip() for x in element.findall('label')}


def certificate(template, location, declaration):
    """Only no-update internal edges with invariant-free targets are eligible."""
    locs = {x.get('id'): x for x in template.findall('location')}
    eligible = []
    for i, edge in enumerate(template.findall('transition')):
        if edge.find('source').get('ref') != location.get('id'):
            continue
        fields = labels(edge)
        if any(fields.get(k) for k in ['assignment', 'select', 'synchronisation']):
            continue
        if labels(locs[edge.find('target').get('ref')]).get('invariant'):
            continue
        guard = fields.get('guard', '')
        if not guard or guard == 'true':
            return {'kind': 'unconditional_internal_no_update', 'edges': [i]}
        eligible.append((i, guard))
    for i, guard in eligible:
        match = re.fullmatch(r'(\w+)\s*<=\s*(\w+)', guard)
        if not match:
            continue
        clock, bound = match.groups()
        if clock not in {v.strip() for group in re.findall(r'\bclock\s+([\w\s,]+);', declaration) for v in group.split(',')}:
            continue
        if not re.search(r'\bconst\s+int\s+' + re.escape(bound) + r'\s*=\s*\d+\s*;', declaration):
            continue
        for j, other in eligible:
            if re.fullmatch(re.escape(clock) + r'\s*>\s*' + re.escape(bound), other):
                return {'kind': 'exhaustive_clock_partition_no_update', 'edges': [i, j], 'clock': clock, 'bound': bound}
    return None


def inventory(root):
    declaration = root.findtext('declaration', '')
    system = root.findtext('system', '')
    # The fixed model has neither process nor channel priorities.
    assert not re.search(r'\bchan\s+priority\b', declaration) and '<' not in system
    instances = re.findall(r'(\w+)\s*=\s*(\w+)\(\);', system)
    templates = {t.findtext('name'): t for t in root.findall('template')}
    assert len(instances) == len(templates) == 50
    assert sorted(t for _, t in instances) == sorted(templates)
    channel_types = {}
    for match in re.finditer(r'((?:urgent\s+)?(?:broadcast\s+)?)chan\s+([^;]+);', declaration):
        for name in match.group(2).split(','):
            channel_types[name.strip()] = ('broadcast' if 'broadcast' in match.group(1) else 'binary')
    receivers = {}
    for name, template in templates.items():
        for i, edge in enumerate(template.findall('transition')):
            sync = labels(edge).get('synchronisation', '')
            if sync.endswith('?'):
                receivers.setdefault(sync[:-1], []).append({'template': name, 'edge_index': i, 'source': edge.find('source').get('ref'), 'target': edge.find('target').get('ref'), 'guard': labels(edge).get('guard', ''), 'assignment': labels(edge).get('assignment', '')})
    records = []
    total_locations = total_edges = 0
    for name, template in templates.items():
        total_locations += len(template.findall('location'))
        total_edges += len(template.findall('transition'))
        locs = {l.get('id'): l for l in template.findall('location')}
        for location in locs.values():
            committed = location.find('committed') is not None
            urgent = location.find('urgent') is not None
            invariant = labels(location).get('invariant', '')
            if not (committed or urgent or invariant):
                continue
            outgoing = []
            for i, edge in enumerate(template.findall('transition')):
                if edge.find('source').get('ref') != location.get('id'):
                    continue
                fields = labels(edge)
                fields.pop('comments', None)
                row = {'edge_index': i, 'target': edge.find('target').get('ref'), 'target_invariant': labels(locs[edge.find('target').get('ref')]).get('invariant', ''), 'labels': fields}
                sync = fields.get('synchronisation', '')
                if sync:
                    channel = sync[:-1]
                    assert channel in channel_types, channel
                    row['channel_type'] = channel_types[channel]
                    if sync.endswith('!'):
                        row['syntactic_receivers'] = receivers.get(channel, [])
                outgoing.append(row)
            cert = certificate(template, location, declaration + '\n' + template.findtext('declaration', '')) if committed else None
            records.append({'template': name, 'location': location.findtext('name'), 'location_id': location.get('id'), 'committed': committed, 'urgent': urgent, 'invariant': invariant, 'local_escape_certificate': cert, 'outgoing': outgoing})
    counts = {'templates': len(templates), 'locations': total_locations, 'edges': total_edges, 'committed_locations': sum(x['committed'] for x in records), 'urgent_locations': sum(x['urgent'] for x in records), 'invariant_locations': sum(bool(x['invariant']) for x in records), 'certified_committed_locations': sum(x['local_escape_certificate'] is not None for x in records)}
    return {'classification': 'static structural evidence only; no verification run or global verdict', 'model_hash': HASH, 'model_path': str(MODEL.relative_to(ROOT)), 'edge_index_convention': 'zero-based transition order within template in exact XML', 'counts': counts, 'urgent_channel_declarations': re.findall(r'urgent\s+(?:broadcast\s+)?chan\s+[^;]+;', declaration), 'records': records}


def mutation_checks(root):
    name = 'phy_Template_ObsSenseReport'
    template = next(t for t in root.findall('template') if t.findtext('name') == name)
    location_id = 'phy_Template_ObsSenseReport_Observe_1'
    declaration = root.findtext('declaration', '')
    assert certificate(template, next(l for l in template.findall('location') if l.get('id') == location_id), declaration) is not None
    cases = []
    for mutation in ['remove_upper_branch', 'add_update', 'add_target_invariant', 'introduce_guard_gap']:
        t = copy.deepcopy(template)
        loc = next(l for l in t.findall('location') if l.get('id') == location_id)
        edges = [e for e in t.findall('transition') if e.find('source').get('ref') == location_id]
        if mutation == 'remove_upper_branch':
            t.remove(edges[1])
        elif mutation == 'add_update':
            ET.SubElement(edges[0], 'label', kind='assignment').text = 'phy_c_obs_sense = 0'
        elif mutation == 'add_target_invariant':
            target = next(l for l in t.findall('location') if l.get('id') == edges[0].find('target').get('ref'))
            ET.SubElement(target, 'label', kind='invariant').text = 'phy_c_obs_sense <= 0'
        else:
            edges[0].find("label[@kind='guard']").text = 'phy_c_obs_sense < phy_D_report'
        assert certificate(t, loc, declaration) is None, mutation
        cases.append(mutation)
    return cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    assert hashlib.sha256(MODEL.read_bytes()).hexdigest() == HASH
    root = ET.parse(MODEL).getroot()
    result = inventory(root)
    result['rejected_mutations'] = mutation_checks(root)
    text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        expected = Path(__file__).with_name('inventory.json').read_text()
        assert expected == text, 'saved inventory differs'
    print(json.dumps({'counts': result['counts'], 'rejected_mutations': result['rejected_mutations'], 'global_deadlock_verdict': None}, indent=2))


if __name__ == '__main__':
    main()
