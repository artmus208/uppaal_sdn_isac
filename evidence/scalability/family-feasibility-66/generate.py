#!/usr/bin/env python3
"""Finite candidate family. Stdlib only; frozen XML is a read-only compiler input."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
FROZEN = 'evidence/governance/20260906-baseline/gate1-20260923/'
BASE = '05ac107789532b6d2eac9914433a4b8408835057'
WORD = re.compile(r'\b[A-Za-z_]\w*\b')
SCOPED = re.compile(r'^(?:(?:phy|mac|sdn|app|bus|obs|boundary)_|raise_app_|Boundary_)')
LOAD = 'Boundary_E_MAC_LOAD'
LOAD_PROCESS = 'boundary_E_MAC_LOAD_0'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def inputs():
    pins = json.loads((HERE / 'inputs.json').read_text())
    for path, digest in pins['files'].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError(f'Pinned input changed: {path}')
    return pins


def rename(text, i, extra=None):
    extra = extra or {}
    return WORD.sub(lambda m: extra.get(m[0], f'u{i}_{m[0]}' if SCOPED.match(m[0]) else m[0]), text)


def renamed(element, i):
    element = copy.deepcopy(element)
    for e in element.iter():
        if e.text:
            e.text = rename(e.text, i)
        for key in ('id', 'ref'):
            if key in e.attrib:
                e.set(key, rename(e.get(key), i))
    return element


def label(element, kind, text):
    ET.SubElement(element, 'label', kind=kind).text = text


def edge(t, source, target, guard=None, sync=None, update=None, select=None):
    e = ET.SubElement(t, 'transition')
    ET.SubElement(e, 'source', ref=source)
    ET.SubElement(e, 'target', ref=target)
    for kind, value in [('select', select), ('guard', guard), ('synchronisation', sync), ('assignment', update)]:
        if value:
            label(e, kind, value)
    return e


def shared_load(source, n):
    """One atomic service/arrival epoch, then bounded zero-time indexed delivery."""
    old = next(t for t in source.findall('template') if t.findtext('name') == LOAD)
    sample = old.findall('transition')[0]
    old_select = sample.findtext("label[@kind='select']")
    old_update = sample.findtext("label[@kind='assignment']")
    t = ET.Element('template')
    ET.SubElement(t, 'name').text = 'SharedLoad'
    local = ['clock tick;']
    for i in range(n):
        for name,hi in [('arrival',1),('m1',2),('m2',3),('m3',2),('m4',3),('m5',2),('m6',2)]:
            local.append(f'int[0,{hi}] {name}_{i}=0;')
    ET.SubElement(t, 'declaration').text = '\n'.join(local)
    wait = ET.SubElement(t, 'location', id='shared_Wait', x='0', y='0')
    ET.SubElement(wait, 'name').text = 'Wait'
    label(wait, 'invariant', 'tick <= u0_bus_T_mac_tick')
    for i in range(n):
        for k, name in enumerate(('Publish', 'Offer')):
            loc = ET.SubElement(t, 'location', id=f'shared_{name}_{i}', x=str(240*(2*i+k+1)), y='0')
            ET.SubElement(loc, 'name').text = f'{name}_{i}'
            ET.SubElement(loc, 'committed')
    for i in range(1,n+1):
        loc=ET.SubElement(t, 'location', id=f'shared_Sample_{i}', x=str(240*i), y='180')
        ET.SubElement(loc, 'name').text=f'Sample_{i}'
        ET.SubElement(loc, 'committed')
    ET.SubElement(t, 'init', ref='shared_Wait')
    for i in range(n):
        sel=old_select.replace(', service:int[0,1]', '')
        extras={name:f'pick_{name}' for name in ['arrival']+[f'm{k}' for k in range(1,7)]}
        assignments=', '.join(f'{name}_{i}=pick_{name}' for name in extras)
        edge(t, 'shared_Wait' if i==0 else f'shared_Sample_{i}', f'shared_Sample_{i+1}',
             guard='tick == u0_bus_T_mac_tick' if i==0 else None,
             select=rename(sel, i, extras), update=assignments)
    selects = ['server:int[-1,' + str(n-1) + ']']
    guards = ['tick == u0_bus_T_mac_tick']
    updates = []
    for i in range(n):
        # A single server choice replaces independent 0/1 service selectors.
        extras = {'arrival': f'arrival_{i}', **{f'm{k}': f'm{k}_{i}' for k in range(1, 7)}}
        # Inputs were staged per entity to avoid a Cartesian selector expansion.
        extras['service'] = f'(server == {i} ? 1 : 0)'
        guards.append(f'(server != {i} || (u{i}_mac_queue_q > 0 && (u{i}_mac_scheduleMode == u{i}_mac_SCH_COMM || u{i}_mac_scheduleMode == u{i}_mac_SCH_JOINT)))')
        updates.append(rename(old_update.replace(', tick=0', ''), i, extras))
        updates.append(f'family_grant_{i}=(server == {i})')
    updates += ['family_last_server=server', 'tick=0']
    edge(t, f'shared_Sample_{n}', 'shared_Publish_0', guard=' && '.join(guards), select=', '.join(selects), update=', '.join(updates))
    for i in range(n):
        p, o = f'shared_Publish_{i}', f'shared_Offer_{i}'
        target = f'shared_Publish_{i+1}' if i+1 < n else 'shared_Wait'
        edge(t, p, o, sync=f'u{i}_bus_new_mac_sample!')
        edge(t, o, target, sync=f'u{i}_mac_mac_tick!')
        edge(t, o, target, update=f'u{i}_bus_tick_missed=true')
    return t


def build(n):
    if type(n) is not int or n not in (1, 2):
        raise ValueError('Candidate domain is exactly N=1,2; extension requires review')
    source = ET.parse(ROOT / FROZEN / 'model.xml').getroot()
    result = ET.Element('nta')
    ET.SubElement(result, 'declaration').text = '\n'.join(
        [f'const int FAMILY_N={n};', f'int[-1,{n-1}] family_last_server=-1;'] +
        [f'bool family_grant_{i}=false;' for i in range(n)] +
        [rename(source.findtext('declaration'), i) for i in range(n)])
    for i in range(n):
        for t in source.findall('template'):
            if t.findtext('name') != LOAD:
                result.append(renamed(t, i))
    result.append(shared_load(source, n))
    old_bindings, old_system = source.findtext('system').split('system ')
    bindings, order = [], []
    for i in range(n):
        bindings.extend(rename(line, i) for line in old_bindings.splitlines() if line.strip() and not line.startswith(LOAD_PROCESS + ' ='))
        for name in old_system.strip().rstrip(';').split(', '):
            if name == LOAD_PROCESS:
                if i == 0:
                    order.append('shared_load')
            else:
                order.append(rename(name, i))
    bindings.append('shared_load = SharedLoad();')
    ET.SubElement(result, 'system').text = '\n'.join(bindings) + '\nsystem ' + ', '.join(order) + ';'
    ET.SubElement(result, 'queries')  # Queries are explicit external inputs, never hidden GUI defaults.
    ET.indent(result, space='  ')
    return result


def queries(n):
    old = json.loads((ROOT / FROZEN / 'selected-queries.json').read_text())
    rows = []
    for row in old:
        for i in range(1 if row['id'] == 'C01-deadlock' else n):
            rows.append({'id': row['id'] if row['id'] == 'C01-deadlock' else f"u{i}-{row['id']}",
                         'query': rename(row['query'], i), 'role': row['role'], 'verdict': None,
                         'source': 'frozen schema; candidate semantics; no transferred verdict'})
    rows.append({'id': 'shared-capacity', 'role': 'candidate-structural', 'verdict': None,
                 'query': 'A[] (' + ' + '.join(f'(family_grant_{i} ? 1 : 0)' for i in range(n)) + ' <= 1)'})
    for i in range(n):
        rows.append({'id': f'u{i}-service-choice', 'role': 'candidate-nonvacuity', 'verdict': None,
                     'query': f'E<> family_grant_{i}'})
    if n == 2:
        rows.append({'id': 'joint-backlog', 'role': 'candidate-nonvacuity', 'verdict': None,
                     'query': 'E<> u0_mac_queue_q > 0 && u1_mac_queue_q > 0'})
    return rows


def vector(n, model):
    return {'configuration_id': f'p2-family-66-n{n}-candidate', 'candidate_not_accepted': True,
            'growth_dimension': 'UAV contexts sharing one abstract BS service budget',
            'entities': {'base_stations': 1, 'uav_devices': n, 'radio_links': n, 'sensing_targets': n,
                         'service_sessions': n, 'sdn_control_contexts': n, 'mac_contexts': n,
                         'abstract_queues': n, 'shared_queue_servers': 1, 'explicit_packets': 0},
            'bindings': [{'uav': i, 'bs': 0, 'link': i, 'target': i, 'service': i, 'sdn_context': i} for i in range(n)],
            'process_counts': {'core': 20*n, 'boundary_private': 7*n, 'boundary_shared': 1, 'observers': 22*n, 'total': 49*n+1},
            'system_order': model.findtext('system').split('system ')[1].rstrip(';').split(', '),
            'storage': 'compile-time indexed namespaces u0_ and u1_; local clocks remain instance local',
            'shared_service': {'capacity_per_epoch': 1, 'period': 5, 'optional': True, 'fairness': False},
            'time_unit': 'abstract_model_unit', 'physical_time_scale_seconds': None}


def artifacts(n, pins):
    root = build(n)
    # UPPAAL 5.0.0 rejects a self-closing queries element (Unexpected end).
    xml = ET.tostring(root, encoding='utf-8', xml_declaration=True).replace(b'<queries />', b'<queries></queries>') + b'\n'
    rows = queries(n)
    q = ''.join(f"// {r['id']} | {r['role']} | no verdict\n{r['query']}\n" for r in rows).encode()
    pars = {'per_uav_frozen_parameters': json.loads((ROOT / FROZEN / 'parameters.json').read_text()),
            'family': {'N': n, 'shared_service_capacity': 1, 'synchronous_period': 5, 'fairness': False}}
    result = {'model.xml': xml, 'queries.q': q, 'queries.json': encoded(rows),
              'parameters.json': encoded(pars), 'instance-vector.json': encoded(vector(n, root)),
              'load.q': b'E<> true\n'}
    result['metadata.json'] = encoded({'base_commit': BASE, 'source_hash': pins['source_hash'],
        'generator_hash': sha(Path(__file__).read_bytes()), 'source_input_model_hash': pins['files'][FROZEN+'model.xml'],
        'hash_algorithm': 'sha256 exact bytes', 'files': {k: sha(v) for k,v in result.items()},
        'N': n, 'acceptance_status': 'candidate', 'scientific_queries_executed': False,
        'reproduce': 'python3 -B evidence/scalability/family-feasibility-66/generate.py'})
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check', action='store_true', help='Compare both sizes with committed artifacts, without writing')
    ap.add_argument('--output', type=Path, default=HERE/'generated')
    args = ap.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(HERE):
        ap.error('Output must remain in the Issue #66 write scope')
    pins = inputs()
    for n in (1,2):
        for name, data in artifacts(n, pins).items():
            path = output / f'n{n}' / name
            if args.check:
                if not path.is_file() or path.read_bytes() != data:
                    raise ValueError(f'Reproduction mismatch: {path}')
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        print(f'N={n}: {49*n+1} processes; ' + ('exact artifact reproduction' if args.check else 'generated'))


if __name__ == '__main__':
    main()
