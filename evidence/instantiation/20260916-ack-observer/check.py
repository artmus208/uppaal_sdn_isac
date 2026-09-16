"""Reproduce #30 corrective diagnostics. Not Gate 1/P3 acceptance.

Run in a clean checkout with --run-id NEW. Outputs are immutable per run.
Focused XMLs retain actual scheduler/observer/bridge templates; the replacement
peer is explicitly a test environment, not the integrated network.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))
from uppaal_mcp.integrated.generator import generate
from uppaal_mcp.integrated.xmlutil import edge, template, normalize_order, label, set_label, append_update

BASE = '9f98a3138d1cc421fb2f58678cd7a6c6d94dea8d'
MODEL_PATH = 'evidence/governance/20260908-gate1-readiness/decision-documents-ru/threshold-correction/pin-update/model.xml'
SHA = lambda b: hashlib.sha256(b).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def focused(xml, kind):
    nta = ET.fromstring(xml)
    keep = {'mac_Template_A_SCH', 'mac_Template_ObsPhyAck', 'Boundary_B_PHY_MAC'}
    for t in list(nta.findall('template')):
        if t.findtext('name') not in keep:
            nta.remove(t)
    nta.find('declaration').text += '\nint[0,2] fixture_completed=0;\n'
    sch = next(t for t in nta.findall('template') if t.findtext('name') == 'mac_Template_A_SCH')
    ids = {l.get('id'): l.findtext('name') for l in sch.findall('location')}
    # A bounded, read-only witness counter: does not gate any production edge.
    for tr in sch.findall('transition'):
        if ids[tr.find('source').get('ref')] == 'WaitPHYAck' and label(tr, 'synchronisation') != 'bus_policy?':
            append_update(tr, 'fixture_completed = fixture_completed < 2 ? fixture_completed+1 : 2')
    if kind.startswith('late_'):
        # Deliberately break functional waiting bounds, leaving monitoring at 3.
        for inv in sch.findall("location/label[@kind='invariant']"):
            if 'mac_c_phy_ack' in inv.text:
                inv.text = 'mac_c_phy_ack <= 4'
        for tr in sch.findall('transition'):
            g = label(tr, 'guard').replace('mac_c_phy_ack == mac_D_phy_ack', 'mac_c_phy_ack == 4')
            g = g.replace('mac_c_phy_ack <= mac_D_phy_ack', 'mac_c_phy_ack <= 4')
            set_label(tr, 'guard', g)
        if kind == 'late_ack':
            nta.find('declaration').text = nta.findtext('declaration').replace('bus_D_cmd=1', 'bus_D_cmd=4')
            bridge = next(t for t in nta.findall('template') if t.findtext('name') == 'Boundary_B_PHY_MAC')
            for tr in bridge.findall('transition'):
                set_label(tr, 'guard', label(tr, 'guard').replace('mac_c_phy_ack <= mac_D_phy_ack', 'mac_c_phy_ack <= 4'))
    env = template('AckTestPeer', ['Ready'])
    for sync in ['mac_mac_tick!', 'mac_phy_kpi_report!', 'mac_mac_report?',
                 'phy_waveform_config?', 'phy_sensing_mode_cmd?', 'phy_power_cmd?']:
        edge(env, 'Ready', 'Ready', sync=sync)
    nta.append(env)
    for t in nta.findall('template'):
        normalize_order(t)
    nta.find('system').text = ('mac_A_SCH_0=mac_Template_A_SCH();\n'
        'obs_mac_ObsPhyAck_0=mac_Template_ObsPhyAck();\n'
        'boundary_B_PHY_MAC_0=Boundary_B_PHY_MAC();\n'
        'peer=AckTestPeer();\n'
        'system mac_A_SCH_0, obs_mac_ObsPhyAck_0, boundary_B_PHY_MAC_0, peer;')
    ET.indent(nta)
    return ET.tostring(nta, encoding='utf-8', xml_declaration=True)


def winpath(p):
    return subprocess.check_output(['wslpath', '-w', str(p)], text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--verifyta', default='/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe')
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.run_id):
        parser.error('run-id must be a simple directory name')
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if dirty:
        raise SystemExit('Run requires a clean checkout; commit/archive previous results first.')
    source_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    out = HERE / 'runs' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    c = generate(ROOT)
    dump(out/'composition.json', c.metadata)
    (out/'integrated-model.xml').write_bytes(c.model_xml.encode())
    (out/'integrated-queries.q').write_bytes(c.queries.encode())
    commands = []
    env = dict(os.environ)
    # Never silently inherit compile-only/approximate settings into verification.
    for k in list(env):
        if k.startswith('UPPAAL_'):
            del env[k]

    def execute(name, command, expected=None, **kwargs):
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        t = time.monotonic()
        try:
            r = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=60, **kwargs)
            stdout, stderr, code, status = r.stdout, r.stderr, r.returncode, 'completed'
        except subprocess.TimeoutExpired as e:
            stdout, stderr, code, status = e.stdout or b'', e.stderr or b'', None, 'timeout'
        (out/(name+'.stdout.txt')).write_bytes(stdout)
        (out/(name+'.stderr.txt')).write_bytes(stderr)
        verdicts = re.findall(r'-- Formula is (NOT satisfied|satisfied)\.', stdout.decode(errors='replace'))
        rec = {'name':name, 'command':command, 'started_at_utc':started,
               'runtime_seconds':time.monotonic()-t, 'exit_code':code, 'status':status,
               'verdicts':verdicts, 'expected':expected, 'stdout':name+'.stdout.txt', 'stderr':name+'.stderr.txt'}
        if expected is not None:
            rec['matches_expectation'] = code == 0 and verdicts == expected
            rec['status'] = 'success' if rec['matches_expectation'] else status if status == 'timeout' else 'error'
        commands.append(rec)
        dump(out/'commands.json', commands)
        print(json.dumps(rec), flush=True)
        return stdout

    version = execute('version', [args.verifyta, '--version']).decode(errors='replace')
    # Exact whole integrated XML is parsed by the real engine using an explicit
    # trivial query. This is deliberately NOT the ACK property of the whole model.
    (out/'parse-only.q').write_text('A[] true\n')
    execute('integrated-parser', [args.verifyta, '-q', winpath(out/'integrated-model.xml'), winpath(out/'parse-only.q')], ['satisfied'])
    old = subprocess.check_output(['git', 'show', BASE+':'+MODEL_PATH], cwd=ROOT)
    for kind, source in [('old', old), ('fixed', c.model_xml.encode()), ('late_timeout', c.model_xml.encode()), ('late_ack', c.model_xml.encode())]:
        model = focused(source, kind)
        (out/(kind+'.xml')).write_bytes(model)
        queries = ['A[] not obs_mac_ObsPhyAck_0.Violation',
                   'E<> fixture_completed == 2',
                   'E<> mac_A_SCH_0.Idle && fixture_completed > 0 && !mac_phy_ack_timeout',
                   'E<> mac_A_SCH_0.ScheduleFailure && mac_phy_ack_timeout']
        expected = ['satisfied' if kind == 'fixed' else 'NOT satisfied', 'satisfied', 'satisfied', 'satisfied']
        if kind.startswith('late_'):
            queries.append('E<> fixture_completed == 2 && mac_obs_ack_late && mac_obs_ack_active && mac_c_obs_ack == 0')
            expected.append('satisfied')
        if kind == 'late_ack':
            queries.append('E<> mac_A_SCH_0.Idle && mac_obs_ack_late && !mac_phy_ack_timeout')
            expected.append('satisfied')
        qb = ('\n'.join(queries)+'\n').encode()
        (out/(kind+'.q')).write_bytes(qb)
        execute(kind, [args.verifyta, '-q', '-t', '1', '-f', winpath(out/(kind+'-trace')), winpath(out/(kind+'.xml')), winpath(out/(kind+'.q'))], expected)
        commands[-1].update(model_hash=SHA(model), query_hash=SHA(qb), queries=queries,
                            scope='focused scheduler/bridge/observer with replacement test peer')
        dump(out/'commands.json', commands)
    execute('software', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])
    execute('mcp', [sys.executable, '-c', 'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'])
    execute('examples', [str(Path(sys.executable).parent/'uppaal-verifyta'), 'list-examples'])
    execute('coordination', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_coordination.py', '-v'])
    execute('diff', ['git', 'diff', '--check', BASE, '--', 'src', 'tests'])
    cpu = next((line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')), 'not_available')
    dump(out/'run.json', {'run_id':args.run_id, 'source_commit':source_commit, 'base_commit':BASE,
         'source_tree_clean_at_start':True, 'tool_version':version, 'operating_environment':platform.platform(),
         'cpu_model':cpu, 'logical_cpu_count':os.cpu_count(),
         'ram_bytes':os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES'),
         'hardware_scope':'WSL host reports; Windows executable accessed through WSL interop',
         'resource_limit':'60 seconds per command; no explicit memory cap',
         'peak_memory':'not_available', 'states_explored':'not_available',
         'parameter_set':c.metadata['parameter_set'], 'instance_vector':c.metadata['instance_vector'],
         'model_hash':SHA(c.model_xml.encode()), 'query_hash':SHA(c.queries.encode()),
         'source_hashes':c.metadata['source_hashes'], 'implementation_sources':c.metadata['implementation_sources'],
         'claim_limits':'Focused diagnostics only. Full integrated ACK query not evaluated. A[] true only checks engine parsing/execution. No Gate 1/P3 acceptance.',
         'all_expected_verdicts_match':all(x.get('matches_expectation', True) for x in commands),
         'all_commands_exit_zero':all(x['exit_code']==0 for x in commands)})
    (out/'SHA256SUMS').write_text(''.join(f'{SHA(p.read_bytes())}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file()))


if __name__ == '__main__':
    main()
