"""Audit retained machine evidence and archives; never launch UPPAAL."""
import csv
import gzip
import hashlib
import json
import lzma
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODEL_HASH = '5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def raw(p):
    if p.exists():
        return p.read_bytes()
    if p.with_name(p.name + '.gz').exists():
        return gzip.decompress(p.with_name(p.name + '.gz').read_bytes())
    return lzma.decompress(p.with_name(p.name + '.xz').read_bytes())


def load(p):
    return json.loads(raw(p))


def steps(p):
    return [json.loads(line) for line in raw(p).splitlines()]


def decode_bound(bound):
    return {'value': bound // 2, 'strict': bound % 2 == 0}


def interval(zone, clock):
    lo, hi = decode_bound(zone[0][clock]), decode_bound(zone[clock][0])
    return f"{'(' if lo['strict'] else '['}{-lo['value']},{hi['value']}{')' if hi['strict'] else ']'}"


def goal(snapshot, names):
    v = dict(zip(names, snapshot['values']))
    return (snapshot['locations'][16] == 'Rejected' and v['u0_app_service_request_pending'] == 0
            and v['u0_app_admissionClass'] == 2 and v['u0_app_pdClass'] == 2
            and v['u0_app_missedDetectionClass'] == 2 and v['u0_bus_violation_recorded'] == 1
            and v['u0_app_sla_violation_report_sent'] == 1 and v['u0_bus_outcome_for_request'] == 1
            and v['u0_bus_mac_report_consumed'] == 1 and v['u0_sdn_policyClass'] == 1)


def validate_cell(folder):
    result, monitor = load(folder / 'result.json'), load(folder / 'monitor.json')
    require(result['model_hash'] == MODEL_HASH, 'model hash')
    require(result['property_verdict'] is None and result['query_hash'] is None, 'simulation verdict')
    require(result['tool_version'].startswith('UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023 -- server.'), 'actual tool version')
    require(monitor['native_status'] == 'success' and monitor['process_tree_reaped'], 'native lifecycle')
    require(monitor['runtime_seconds'] < 60 and monitor['peak_tree_sample_bytes'] < 2147483648, 'native limits')
    require(load(folder / 'hardware.json')['available_ram_bytes'] >= 3221225472, 'native RAM headroom')
    rows = list(csv.DictReader(raw(folder / 'memory.csv').decode().splitlines()))
    require(rows and max(int(r['tree_sample_bytes']) for r in rows) == monitor['peak_tree_sample_bytes'], 'memory samples')
    records = steps(folder / 'steps.jsonl')
    negative = result['mode'].startswith('negative-')
    require(result['accepted_transitions'] == (62 if negative else 63), 'step count')
    if negative:
        reason = 'clock_zone_disjoint' if result['mode'] == 'negative-clock' else 'discrete_state_mismatch'
        require(result['status'] == 'rejected' and result['reason'] == reason and result['control_expected_rejection'], 'negative control')
        require(result['first_unavailable_state_index'] == 63 and monitor['exit_code'] == 1, 'negative endpoint')
    else:
        require(result['status'] == ('goal_reached' if result['mode'] == 'simulate' else 'replay_complete'), 'positive status')
        require(monitor['exit_code'] == 0, 'positive native exit')
        require(goal(records[-1]['snapshot'], result['variable_names']), 'APP endpoint')
    expected = list(range(63 if negative else 64))
    indices = [s.get('state_index', s.get('waypoint')) for s in records]
    require(indices == expected, 'prefix indices')
    for s in records:
        z = s['snapshot']['zone']
        require(len(z) == 70 and all(len(row) == 70 for row in z), 'zone dimensions')
        require(all(z[i][i] == 1 for i in range(70)), 'DBM consistency')
    provenance = load(folder / 'provenance.json')
    require(provenance['wrapper_status'] == 'complete' and provenance['wrapper_exit'] == 0, 'wrapper outcome')
    for name, expected_hash in provenance['hashes'].items():
        path = Path(name)
        if '/tmp/uppaal-r07-80/' in name:
            path = ROOT / name.split('/tmp/uppaal-r07-80/', 1)[1]
        if '/tmp/uppaal-r07-80/' in name or path.exists():
            require(digest(raw(path)) == expected_hash, 'executed source/input hash: ' + name)
    return result, records


def audit():
    inventory = load(HERE / 'inventory.json')
    actual = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file()
              and '__pycache__' not in p.parts and p.name not in {'inventory.json', 'audit-result.json'}}
    require(actual == set(inventory), 'inventory coverage')
    for name, h in inventory.items():
        require(digest((HERE / name).read_bytes()) == h, 'inventory hash: ' + name)
    for entry in load(HERE / 'lossless-archive.json'):
        packed = (HERE / entry['path']).read_bytes()
        require(digest(packed) == entry['sha256'], 'archive hash')
        unpacked = (gzip.decompress if entry['codec'] == 'gzip' else lzma.decompress)(packed)
        require(digest(unpacked) == entry['original_sha256'] and len(unpacked) == entry['original_size'], 'lossless bytes')
        original = HERE / entry['original_path']
        if original.exists():
            require(original.read_bytes() == unpacked.replace(b'\r\n', b'\n'), 'normalized native JSON')
    cells = []
    for folder in sorted((HERE / 'runs').iterdir()):
        result, records = validate_cell(folder)
        cells.append({'run_id': load(folder / 'provenance.json')['run_id'], 'status': result['status'],
                      'accepted_transitions': result['accepted_transitions']})
    r, ss = validate_cell(HERE / 'runs/replay001')
    clock = r['clock_names'].index('u0_app_c_sla_violation')
    require(interval(ss[54]['snapshot']['zone'], 1) == '[5,5]', 'PHY/SLA time')
    require(interval(ss[62]['snapshot']['zone'], clock) == '[0,0]', 'pre-report elapsed deadline')
    require(interval(ss[63]['snapshot']['zone'], 1) == '[5,5]', 'APP result time')
    summary = load(HERE / 'results.json')
    require(summary['property_verdict'] is None and summary['query_hash'] is None, 'summary verdict')
    require(summary['accepted_verification_run_id'] is None and summary['acceptance_status'] == 'candidate_pending_independent_review', 'acceptance honesty')
    require(summary['total_native_wall_seconds'] < 600 and len(cells) == 4, 'campaign cap')
    return {'status': 'saved_evidence_consistent', 'property_verdict': None, 'artifacts': len(inventory),
            'cells': cells, 'APP_result': 'Rejected', 'report_time': 5, 'report_elapsed': 0}


if __name__ == '__main__':
    print(json.dumps(audit(), indent=2))
