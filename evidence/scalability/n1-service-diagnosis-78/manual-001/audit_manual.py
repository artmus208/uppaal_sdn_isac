"""Read-only discrete XTR audit. Does not validate timed edges or run UPPAAL."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MODEL = ROOT / 'evidence/scalability/family-series-68/generated/n1/model.xml'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def normalized(element):
    # Ignore drawing coordinates, XML IDs and comments; retain executable labels.
    if element.tag == 'label' and element.get('kind') == 'comments':
        return None
    attrs = {k: v for k, v in element.attrib.items()
             if k not in ('x', 'y', 'id', 'ref', 'color')}
    return [element.tag, attrs, (element.text or '').strip(),
            [n for c in element if (n := normalized(c)) is not None]]

def main():
    assert sha(MODEL) == '5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385'
    baseline = ET.parse(MODEL).getroot()
    gui = ET.parse(HERE / 'gui-saved-model.xml').getroot()
    for tag in ('declaration', 'system'):
        assert baseline.findtext(tag) == gui.findtext(tag)
    extras = []
    assert len(baseline.findall('template')) == len(gui.findall('template')) == 50
    for a, b in zip(baseline.findall('template'), gui.findall('template')):
        assert a.findtext('name') == b.findtext('name')
        for tag in ('parameter', 'declaration'):
            assert (a.findtext(tag) or '').strip() == (b.findtext(tag) or '').strip()
        al, bl = a.findall('location'), b.findall('location')
        ai = {x.get('id'): i for i, x in enumerate(al)}
        bi = {x.get('id'): i for i, x in enumerate(bl)}
        assert len(bl) >= len(al)
        assert [normalized(x) for x in al] == [normalized(x) for x in bl[:len(al)]]
        assert ai[a.find('init').get('ref')] == bi[b.find('init').get('ref')]
        at, bt = a.findall('transition'), b.findall('transition')
        assert len(at) == len(bt)
        for x, y in zip(at, bt):
            for tag in ('source', 'target'):
                assert ai[x.find(tag).get('ref')] == bi[y.find(tag).get('ref')]
            # Nails encode drawing geometry, not transitions.
            assert [normalized(c) for c in x if c.tag != 'nail'] == [normalized(c) for c in y if c.tag != 'nail']
        for loc in bl[len(al):]:
            ident = loc.get('id')
            assert b.find('init').get('ref') != ident
            assert not any(c.get('ref') == ident for t in bt for c in t if c.tag in ('source', 'target'))
            extras.append({'template': b.findtext('name'), 'id': ident, 'isolated': True})
    layout_path = ROOT / 'evidence/scalability/family-series-68/checks/diagnostic-001/n1-compile.stdout.txt.gz'
    layout = gzip.decompress(layout_path.read_bytes()).decode()
    variables = {int(n): (name, int(lo), int(hi), int(init)) for lo, hi, init, n, name in
                 re.findall(r'^\d+:var:(-?\d+):(-?\d+):(-?\d+):(\d+):([^\r\n]+)', layout, re.M)}
    assert sorted(variables) == list(range(255))
    trace = HERE / '05-service-before-overflow.xtr'
    blocks = [x.strip().splitlines() for x in re.split(r'^\.$', trace.read_text(), flags=re.M)]
    def vectors(size):
        return [[int(x) for x in b] for b in blocks if len(b) == size and all(re.fullmatch(r'-?\d+', x) for x in b)]
    values, locations = vectors(255), vectors(50)
    assert len(values) == len(locations) == 69
    assert all(values[0][i] == v[3] for i, v in variables.items())
    assert all(v[1] <= row[i] <= v[2] for row in values for i, v in variables.items())
    system = baseline.findtext('system')
    bindings = dict(re.findall(r'(\w+)\s*=\s*(\w+)\(\);', system))
    processes = re.search(r'\bsystem\s+([^;]+);', system)[1].replace(' ', '').split(',')
    templates = {t.findtext('name'): t for t in baseline.findall('template')}
    names = [[loc.findtext('name') for loc in templates[bindings[p]].findall('location')] for p in processes]
    assert len(names) == 50
    for row in locations:
        assert all(0 <= x < len(names[i]) for i, x in enumerate(row))
    decoded = [{v[0]: row[i] for i, v in variables.items()} for row in values]
    d1, d2, d3, grant = [], [], [], []
    for n, (v, loc) in enumerate(zip(decoded, locations)):
        state = {p: names[i][loc[i]] for i, p in enumerate(processes)}
        if state['u0_mac_A_SCH_0'] == 'SelectMode': d1.append(n)
        if state['shared_load'] == 'Sample_1' and 0 < v['u0_mac_queue_q'] <= 4 and v['u0_mac_scheduleMode'] in (1, 3): d2.append(n)
        if state['shared_load'] == 'Publish_0' and v['family_grant_0'] and not v['u0_mac_queue_overflow_seen']: d3.append(n)
        if v['family_grant_0']: grant.append(n)
    selected = ['family_last_server', 'family_grant_0', 'u0_mac_queue_q', 'u0_mac_queue_overflow_seen',
                'u0_mac_scheduleMode', 'u0_app_service_request_pending', 'u0_bus_admission_loss',
                'u0_bus_allow_comm', 'u0_mac_phy_command_pending', 'shared_load.arrival_0']
    history = json.loads((HERE.parent / 'history.json').read_text())
    service = [r for r in history['runs'] if r['query_text'] and r['query_text'].strip() == 'E<> family_grant_0']
    result = {
        'evidence_kind': 'static_validation_of_user_simulation_artifact',
        'model_checking_performed': False, 'timed_transition_replay_performed': False,
        'model_hash': sha(MODEL), 'trace_hash': sha(trace), 'gui_model_hash': sha(HERE / 'gui-saved-model.xml'),
        'layout_compressed_hash': sha(layout_path), 'source_checkpoint': 'f10767d75604241d9ddc07ed9c4ff94ffd0cb2f7',
        'gui_extra_locations': extras, 'existing_locations_edges_declarations_match': True,
        'state_count': len(values), 'initial_values_match': True, 'all_values_in_domain': True,
        'matching_state_indices_zero_based': {'original_grant': grant, 'D1': d1, 'D2': d2, 'D3': d3},
        'selected_final_values': {key: decoded[-1][key] for key in selected},
        'final_shared_location': names[21][locations[-1][21]],
        'penultimate_queue': decoded[-2]['u0_mac_queue_q'],
        'overflow_ever_in_stored_states': any(v['u0_mac_queue_overflow_seen'] for v in decoded),
        'time_10_source': 'User GUI screenshot; DBM constraints not independently decoded by this script',
        'historical_original_service_attempts': [{k: r[k] for k in ('run_id', 'status', 'timeout_seconds', 'command', 'model_hash', 'query_hash', 'tool_version', 'stdout_text', 'native_peak_bytes')} for r in service],
    }
    assert d1 and d2 and d3 and grant
    print(json.dumps(result, ensure_ascii=False, indent=2) )

if __name__ == '__main__':
    main()
