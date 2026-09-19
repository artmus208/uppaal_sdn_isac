"""Targeted #35 harnesses: actual A_REC/observer plus an explicit replacement peer.

These are finite diagnostic compositions, not the integrated network. Mutations
are named in each case. Original input bytes are read from the pinned Git base.
"""
from copy import deepcopy
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from uppaal_mcp.integrated.adapt import RECOVERY_RECORDING, record_recovery, recovery_observer
from uppaal_mcp.integrated.xmlutil import edge, template, normalize_order, label, set_label, append_update, loc_id, source_name

BASE = '44ff0e336c7bfc88e3ebe3da3d05699c2acef62f'
BASE_MODEL = 'evidence/instantiation/20260916-ack-observer/runs/ack-review-003-20260917/integrated-model.xml'
REC = 'sdn_Template_A_REC'
OBS = 'sdn_Template_ObsRecovery'
BAD = '(sdn_obs_rec_late || (sdn_obs_rec_active && sdn_c_obs_rec > 30))'
SAFE = 'A[] !' + BAD
WITNESS = '''
clock fx_age, fx_since_end, fx_first;
int[0,2] fx_started=0, fx_done=0;
bool fx_late=false, fx_failed=false;
void fx_start() {
    if (fx_started == 0) fx_first=0;
    fx_started = fx_started < 2 ? fx_started+1 : 2;
    fx_age=0;
}
void fx_end() {
    fx_done = fx_done < 2 ? fx_done+1 : 2;
    fx_since_end=0;
}
'''


def original_xml():
    return subprocess.check_output(['git', 'show', BASE + ':' + BASE_MODEL], cwd=ROOT)


def recorder_only(xml):
    nta = ET.fromstring(xml)
    nta.find('declaration').text += RECOVERY_RECORDING
    record_recovery(next(t for t in nta.findall('template') if t.findtext('name') == REC))
    recovery_observer(next(t for t in nta.findall('template') if t.findtext('name') == OBS))
    return ET.tostring(nta)


def focused(xml, *, route='standby', dispatch=0, ack=20, rollback_ack=True,
            report=False, repeat=False, no_end=False, stopped=False, duplicate=False,
            rollback_transport=True):
    nta = ET.fromstring(xml)
    for t in list(nta.findall('template')):
        if t.findtext('name') not in (REC, OBS):
            nta.remove(t)
    nta.find('declaration').text += WITNESS
    core = next(t for t in nta.findall('template') if t.findtext('name') == REC)
    for tr in list(core.findall('transition')):
        if label(tr, 'synchronisation') in ('sdn_link_failure?', 'sdn_node_failure?'):
            append_update(tr, 'fx_start()')
        source = source_name(core, tr)
        if source not in ('StableConfig', 'RecoveryFailed') and tr.find('target').get('ref') in (loc_id(core, 'StableConfig'), loc_id(core, 'RecoveryFailed')):
            append_update(tr, 'fx_end()')
            if tr.find('target').get('ref') == loc_id(core, 'RecoveryFailed'):
                append_update(tr, 'fx_failed=true')
    if no_end:
        # Negative control: remove all exits after start, allow elapsed >30.
        for tr in list(core.findall('transition')):
            if source_name(core, tr) != 'StableConfig':
                core.remove(tr)
        for inv in list(core.findall("location/label[@kind='invariant']")):
            for loc in core.findall('location'):
                if inv in list(loc):
                    loc.remove(inv)
    if duplicate:
        # Synthetic protocol misuse, not a second production failure receiver.
        edge(core, 'FailureDetected', 'FailureDetected', guard='fx_age == 5 && !sdn_obs_rec_protocol_error',
             update='sdn_obs_rec_start()')
    peer = template('RecoveryPeer', [('Init', '', True), ('Offer', '', True),
                    ('Dispatch', '' if no_end else ('fx_age <= 0' if stopped else f'fx_age <= {dispatch}')), 'Live'],
                    'int[0,3] mode=0; clock rb;')
    edge(peer, 'Init', 'Offer', update='sdn_telemetryClass=sdn_TEL_FRESH, sdn_policyClass=sdn_POL_NORMAL, '
         f'sdn_standby_available={str(route == "standby").lower()}, sdn_alternative_config_exists={str(route == "reembed").lower()}')
    for ch in ('sdn_link_failure!', 'sdn_node_failure!'):
        edge(peer, 'Offer', 'Dispatch', sync=ch)
    if stopped:
        edge(peer, 'Dispatch', 'Dispatch')
    # Local terminal behavior allows time-divergent idling after the outcome.
    # It does not repair core deadlocks while an episode is active.
    edge(peer, 'Dispatch', 'Live', guard='fx_done > 0')
    edge(peer, 'Live', 'Live', guard='fx_done > 0')
    if repeat:
        edge(peer, 'Live', 'Offer', guard='fx_done == 1 && fx_started == 1 && !fx_failed')
    for request, mode in [('bus_rec_policy_request?', 1), ('bus_rec_flow_request?', 2), ('bus_rollback_request?', 3)]:
        edge(peer, 'Dispatch', 'Live', guard=f'fx_age >= {dispatch} && mode == 0',
             sync=request, update=f'mode={mode}, rb=0')
        if mode == 3 and rollback_transport:
            edge(peer, 'Live', 'Live', guard='mode == 1 || mode == 2',
                 sync=request, update='mode=3, rb=0')
    for response, mode in [('bus_rec_policy_ack!', 1), ('bus_rec_flow_ack!', 2), ('bus_rec_rollback_ack!', 3)]:
        if ack is None or (mode == 3 and not rollback_ack):
            continue
        timing = f'rb == {ack}' if route == 'direct' else (f'rb == 10' if mode == 3 else f'fx_age == {ack}')
        if repeat:
            # Separate edges: UPPAAL does not permit this disjunction of clock zones.
            edge(peer, 'Live', 'Live', guard=f'mode == {mode} && fx_started == 1 && {timing}', sync=response, update='mode=0')
            edge(peer, 'Live', 'Live', guard=f'mode == {mode} && fx_started == 2 && rb == 0', sync=response, update='mode=0')
        else:
            edge(peer, 'Live', 'Live', guard=f'mode == {mode} && {timing}', sync=response, update='mode=0')
    # Wrong typed ACK cannot synchronize with this phase; no extra core receiver.
    edge(peer, 'Live', 'Live', guard='mode == 1', sync='bus_rec_flow_ack!')
    # A duplicate after the only completed production episode has no receiver.
    for response in ('bus_rec_policy_ack!', 'bus_rec_flow_ack!', 'bus_rec_rollback_ack!'):
        edge(peer, 'Live', 'Live', guard='fx_done == 1 && fx_started == 1 && mode == 0', sync=response)
    if report:
        edge(peer, 'Live', 'Live', sync='sdn_failure_report?')
    for t in (core, peer):
        normalize_order(t)
    nta.insert(list(nta).index(nta.find('system')), peer)
    nta.find('system').text = 'rec=sdn_Template_A_REC(); obs=sdn_Template_ObsRecovery(); peer=RecoveryPeer(); system rec, obs, peer;'
    ET.indent(nta)
    return ET.tostring(nta, encoding='utf-8', xml_declaration=True, short_empty_elements=False) + b'\n'


def cases(original, fixed):
    recorded = recorder_only(original)
    good = [('elapsed safety', SAFE, True), ('protocol', 'A[] !sdn_obs_rec_protocol_error', True),
            ('no deadlock in this harness', 'A[] not deadlock', True)]
    start = ('accepted failure reachable', 'E<> fx_started == 1 && rec.FailureDetected', True)
    result = []
    def add(name, source, options, queries, scope):
        result.append((name, focused(source, **options), queries, scope))
    # Same functional composition, old observer versus passive recorder.
    q = [start, ('timely success', 'E<> fx_done == 1 && !fx_failed && fx_age == 20', True),
         ('old delayed polling can falsely report violation', 'E<> obs.Violation && fx_done == 1 && !fx_failed', True)]
    add('original-timely', original, {}, q, 'Original core/observer; replacement peer accepts standby, ACK at age20.')
    add('recorder-timely', recorded, {}, good + [start, q[1]], 'Original functional core plus recorder; same peer; delayed observer is unrestricted.')
    for route in ('standby', 'reembed'):
        for d in (0, 19, 20):
            add(f'fixed-{route}-{d}', fixed, dict(route=route, dispatch=d), good + [start,
                ('ACK at exact stage deadline', 'E<> fx_done == 1 && !fx_failed && fx_age == 20', True),
                ('rollback outcome at total30', 'E<> fx_done == 1 && fx_age == 30', True),
                ('local failure independent of report', 'E<> rec.RecoveryFailed && sdn_recovery_report_pending && !sdn_failure_report_sent', True)],
                'Actual fixed core; one accepted link/node failure; replacement transport/typed ACK peer, no report receiver.')
    for d in (0, 5, 19, 20):
        add(f'fixed-direct-{d}', fixed, dict(route='direct', dispatch=d, ack=10), good + [start,
            ('direct rollback dispatch age', f'E<> rec.Rollback && fx_age == {d}', True),
            ('direct rollback ACK at b10', f'E<> fx_done == 1 && !fx_failed && fx_age == {d+10}', True),
            ('rollback timeout at b10', f'E<> sdn_recovery_failure_kind == 2 && fx_age == {d+10}', True)],
            'Direct rollback with controlled dispatch and ACK at local age10; timeout equally permitted.')
    add('fixed-unavailable', fixed, dict(dispatch=99, ack=None), good + [start,
        ('local dispatch failure at20', 'E<> rec.RecoveryFailed && fx_age == 20 && sdn_recovery_failure_kind == 1', True),
        ('failure no later than20', 'A[] (fx_started == 1 && fx_age > 20) imply fx_done == 1', True)],
        'Peer refuses all dispatch until99 and never receives failure_report; local outcome must remain possible at20.')
    for route in ('standby', 'reembed'):
        add('fixed-blocked-rollback-' + route, fixed,
            dict(route=route, ack=None, rollback_transport=False), good + [start,
            ('blocked rollback dispatch ends locally at20', 'E<> rec.RecoveryFailed && fx_age == 20 && sdn_recovery_failure_kind == 1', True),
            ('wrong typed ACK cannot close the episode', 'A[] fx_done > 0 imply fx_failed', True)],
            'Initial command delivered; no matching ACK, rollback receiver or report receiver. Wrong typed ACK offered, without receiver.')
    add('fixed-report', fixed, dict(route='direct', ack=None, report=True), good + [
        ('local failure before report', 'E<> rec.RecoveryFailed && !sdn_failure_report_sent', True),
        ('separate report delivery', 'E<> rec.RecoveryFailed && sdn_failure_report_sent && !sdn_recovery_report_pending', True)],
        'Rollback timeout and optional report receiver; distinct local outcome and report transitions.')
    add('original-late-dispatch', original, dict(route='direct', dispatch=31, ack=0), [start,
        ('original permits unbounded wait', 'E<> rec.FailureDetected && fx_age == 31', True),
        ('original late success', 'E<> fx_done == 1 && fx_age == 31', True)],
        'Original actual core; synthetic transport delays direct rollback beyond20; not a full-model counterexample.')
    add('recorder-late-repeat', recorded, dict(route='direct', dispatch=31, ack=0, repeat=True), [start,
        ('late completion retained', 'E<> fx_done == 1 && sdn_obs_rec_late && !sdn_obs_rec_active', True),
        ('late retained across next start with no observer step', 'E<> fx_started == 2 && fx_done == 1 && sdn_obs_rec_late && sdn_obs_rec_active && fx_since_end == 0 && obs.Idle', True),
        ('negative elapsed safety', SAFE, False)],
        'Original unbounded dispatch plus recorder, two synthetic consecutive episodes (production allows one).')
    add('fixed-rapid', fixed, dict(ack=0, repeat=True), good + [
        ('two distinct zero-time completions', 'E<> fx_started == 2 && fx_done == 2 && fx_first == 0 && obs.Idle', True),
        ('completion then immediate next start', 'E<> fx_started == 2 && fx_done == 1 && fx_since_end == 0', True)],
        'Synthetic sequential two-episode extension; actual recorder/core unchanged.')
    add('no-completion', fixed, dict(no_end=True, ack=None), [start,
        ('missing completion exceeds30', 'E<> fx_done == 0 && sdn_obs_rec_active && sdn_c_obs_rec > 30', True),
        ('negative elapsed safety', SAFE, False)],
        'Negative mutant removes all core exits after failure and all core invariants; never production input.')
    add('time-stopped', fixed, dict(stopped=True, dispatch=99, ack=None), [start,
        ('elapsed remains zero', 'A[] fx_age == 0', True),
        ('no completion', 'A[] fx_done == 0', True),
        ('elapsed safety is insufficient', SAFE, True),
        ('enabled zero-time loop is not deadlock', 'A[] not deadlock', True)],
        'Synthetic peer Live invariant fx_age<=0 and local self-loop: a time-stopped execution, not a completion proof.')
    add('duplicate-start', fixed, dict(duplicate=True, dispatch=99, ack=None), [
        ('duplicate records error without resetting oldest age', 'E<> sdn_obs_rec_protocol_error && sdn_c_obs_rec == 5', True),
        ('oldest age still counts', 'A[] fx_started == 1 imply sdn_c_obs_rec == fx_age', True)],
        'Synthetic misuse invokes recorder start while active at5; not an extra production failure transition.')
    return result
