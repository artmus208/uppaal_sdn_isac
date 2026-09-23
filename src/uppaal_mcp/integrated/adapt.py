"""Explicit semantic adaptations applied to copies of the pinned layer XMLs."""
from __future__ import annotations

import re
from copy import deepcopy
import xml.etree.ElementTree as ET
from .xmlutil import append_update, edge, label, loc_id, location, set_label, source_name


def remove_assignment(tr, expression):
    parts = [p.strip() for p in label(tr, 'assignment').split(',')]
    set_label(tr, 'assignment', ', '.join(p for p in parts if p != expression))


RECOVERY_RECORDING = '''
// Passive episode recording: only A_REC writes these variables.
bool sdn_obs_rec_active = false, sdn_obs_rec_late = false;
bool sdn_obs_rec_protocol_error = false;
void sdn_obs_rec_start() {
    if (sdn_obs_rec_active) sdn_obs_rec_protocol_error = true;
    else { sdn_obs_rec_active = true; sdn_c_obs_rec = 0; }
}
void sdn_obs_rec_finish() {
    if (!sdn_obs_rec_active) sdn_obs_rec_protocol_error = true;
    sdn_obs_rec_active = false;
}
'''

RECOVERY_ATTEMPTS = '''
// Passive #45 dispatch counters; saturating violation witnesses never gate edges.
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


def record_attempts(t):
    """Append total, nonblocking updates after the accepted recovery recorder."""
    for tr in t.findall('transition'):
        update = label(tr, 'assignment')
        if 'sdn_obs_rec_start()' in update:
            append_update(tr, 'sdn_attempt_start()')
        sync = label(tr, 'synchronisation')
        if sync in ('bus_rec_policy_request!', 'bus_rec_flow_request!'):
            append_update(tr, 'sdn_attempt_dispatch(false)')
        elif sync == 'bus_rollback_request!':
            append_update(tr, 'sdn_attempt_dispatch(true)')
        if 'sdn_obs_rec_finish()' in update:
            append_update(tr, 'sdn_attempt_finish()')


RECOVERY_OUTCOME = '''
// Local failure is distinct from later report delivery.
// 0: no failure, 1: dispatch/recovery-stage timeout, 2: rollback timeout.
int[0,2] sdn_recovery_failure_kind = 0;
bool sdn_recovery_report_pending = false;
'''


def record_recovery(t):
    """Record actual events after typed-channel and optional policy adaptation.

    End edges are binary receives or local edges, never broadcast receives.
    The exhaustive guard partition preserves functional choices and updates.
    """
    for tr in list(t.findall('transition')):
        if label(tr, 'synchronisation') in ('sdn_link_failure?', 'sdn_node_failure?'):
            append_update(tr, 'sdn_obs_rec_start()')
        target = tr.find('target').get('ref')
        if source_name(t, tr) not in ('StableConfig', 'RecoveryFailed') and target in (
                loc_id(t, 'StableConfig'), loc_id(t, 'RecoveryFailed')):
            guard = label(tr, 'guard') or 'true'
            append_update(tr, 'sdn_obs_rec_finish()')
            late = deepcopy(tr)
            deadline = '(sdn_D_recovery + sdn_D_rollback)'
            set_label(tr, 'guard', f'({guard}) && sdn_c_obs_rec <= {deadline}')
            set_label(late, 'guard', f'({guard}) && sdn_c_obs_rec > {deadline}')
            append_update(late, 'sdn_obs_rec_late = true')
            t.append(late)


def recovery_policy(t):
    """Apply the accepted functional 20/10 policy independently of recording."""
    detected = next(l for l in t.findall('location') if l.findtext('name') == 'FailureDetected')
    ET.SubElement(detected, 'label', kind='invariant').text = 'sdn_c_rec <= sdn_D_recovery'
    failed = ('sdn_recoveryClass = sdn_REC_FAILED, sdn_sdnReason = sdn_SDN_RECOVERY_FAILED, '
              'sdn_serviceImpact = sdn_IMPACT_FAILED, sdn_link_failure_pending = false, '
              'sdn_node_failure_pending = false, sdn_optimistic_reconfig = false, '
              'bus_rec_policy_open = false, sdn_failure_report_sent = false, '
              'sdn_recovery_report_pending = true')
    for tr in t.findall('transition'):
        if label(tr, 'synchronisation') in ('sdn_link_failure?', 'sdn_node_failure?'):
            append_update(tr, 'sdn_recovery_failure_kind = 0')
        if tr.find('target').get('ref') == loc_id(t, 'RecoveryFailed'):
            # Record the local outcome even when the binary report receiver is absent.
            set_label(tr, 'synchronisation', '')
            set_label(tr, 'assignment', failed + ', sdn_recovery_failure_kind = 2')
    for phase in ('FailureDetected', 'StandbySwitch', 'ReactiveReembedding'):
        edge(t, phase, 'RecoveryFailed', guard='sdn_c_rec == sdn_D_recovery',
             update=failed + ', sdn_recovery_failure_kind = 1')
    edge(t, 'RecoveryFailed', 'RecoveryFailed', guard='sdn_recovery_report_pending',
         sync='sdn_failure_report!',
         update='sdn_recovery_report_pending = false, sdn_failure_report_sent = true')


def recovery_observer(t):
    """Read-only witness; the direct bad predicate does not need an observer step."""
    for node in list(t):
        if node.tag == 'transition' or (node.tag == 'location' and node.findtext('name') == 'Wait'):
            t.remove(node)
    edge(t, 'Idle', 'Violation', guard='sdn_obs_rec_late || sdn_obs_rec_protocol_error')
    edge(t, 'Idle', 'Violation',
         guard='sdn_obs_rec_active && sdn_c_obs_rec > sdn_D_recovery + sdn_D_rollback')


def adapt_layer(layer, declaration, templates):
    if layer == 'mac':
        declaration = declaration.replace('mac_kpiFreshnessClass = mac_KPI_FRESH', 'mac_kpiFreshnessClass = mac_KPI_MISSING')
        declaration += ('\n// Passive ACK instrumentation, written only by the scheduler.\n'
                        'bool mac_obs_ack_active = false;\n'
                        'bool mac_obs_ack_late = false;\n')
    if layer == 'sdn':
        declaration = declaration.replace('sdn_telemetryClass = sdn_TEL_FRESH', 'sdn_telemetryClass = sdn_TEL_MISSING')
        declaration += RECOVERY_RECORDING + RECOVERY_OUTCOME + RECOVERY_ATTEMPTS
    if layer == 'app':
        # Producer-owned monitoring latches preserve the oldest outstanding event.
        # Observers clear only these monitoring variables on an observed response.
        for name in re.findall(r'int (app_\w+_seq) = 0;', declaration):
            declaration = declaration.replace(f'int {name} = 0;',
                f'bool {name} = false;\nclock {name}_age;\n'
                f'void raise_{name}() {{ if (!{name}) {{ {name} = true; {name}_age = 0; }} }}')
            declaration = re.sub(rf'{name}\s*=\s*{name}\s*\+\s*1', f'raise_{name}()', declaration)
        # The request builder must not fabricate current good sensing measurements.
        start = declaration.index('void app_build_uav_service_request()')
        end = declaration.index('\n}', start) + 2
        builder = declaration[start:end]
        fields = ['detectionFreshnessClass', 'updatePeriodClass', 'falseAlarmClass',
                  'missedDetectionClass', 'pdClass', 'accuracyClass', 'coverageClass']
        for field in fields:
            builder = re.sub(rf'\s*app_{field}\s*=\s*\w+;', '', builder)
        declaration = declaration[:start] + builder + declaration[end:]
        declaration = declaration.replace('app_DetectionFreshnessClass_t app_detectionFreshnessClass;',
                                          'app_DetectionFreshnessClass_t app_detectionFreshnessClass = app_DET_EXPIRED;')
        declaration = declaration.replace('app_UpdatePeriodClass_t app_updatePeriodClass;',
                                          'app_UpdatePeriodClass_t app_updatePeriodClass = app_UPD_VIOLATED;')
    for process, t in templates.items():
        prefix = f'obs_{layer}_' if process.startswith(f'obs_{layer}_') else f'{layer}_'
        original = process.removeprefix(prefix).removesuffix('_0')
        if layer == 'sdn' and original == 'ObsRecovery':
            recovery_observer(t)
        if layer == 'mac' and original == 'ObsPhyAck':
            # No polling/reset/clear transition: a completed late transaction
            # stays recorded even if the observer runs after the next command.
            for node in list(t):
                if node.tag == 'transition' or (node.tag == 'location' and node.findtext('name') == 'Wait'):
                    t.remove(node)
            edge(t, 'Idle', 'Violation', guard='mac_obs_ack_late')
            edge(t, 'Idle', 'Violation',
                 guard='mac_obs_ack_active && mac_c_obs_ack > mac_D_phy_ack')
        if layer == 'app' and original.startswith('Obs'):
            trigger = next(tr for tr in t.findall('transition') if '_seq >' in label(tr, 'guard'))
            event_name = re.search(r'app_\w+_seq', label(trigger, 'guard'))[0]
            set_label(trigger, 'guard', event_name)
            set_label(trigger, 'assignment', '')
            t.find('declaration').text = ''
            for tr in t.findall('transition'):
                set_label(tr, 'guard', re.sub(r'\bapp_x\b', event_name + '_age', label(tr, 'guard')))
                if tr.find('target').get('ref') == loc_id(t, 'Idle'):
                    append_update(tr, event_name + ' = false')
                    if original == 'ObsAdmission':
                        set_label(tr, 'guard', '!app_service_request_pending && (' + label(tr, 'guard') + ')')
        for tr in t.findall('transition'):
            sync = label(tr, 'synchronisation')
            if layer == 'app':
                set_label(tr, 'assignment', re.sub(r'(app_\w+_seq)\s*=\s*\1\s*\+\s*1', r'raise_\1()', label(tr, 'assignment')))
                remove_assignment(tr, 'app_age_sensing = 0')
                if sync == 'app_new_demand?':
                    append_update(tr, 'bus_demand_delivered = true')
                if sync == 'app_service_complete?':
                    append_update(tr, 'bus_complete_delivered = true')
            if layer == 'sdn':
                if original == 'A_MON' and sync in ('sdn_mac_report?', 'sdn_phy_kpi_report?'):
                    remove_assignment(tr, 'sdn_telemetryClass = sdn_TEL_FRESH')
                    append_update(tr, 'bus_sdn_report_consumed = true')
                if original == 'A_POLICY':
                    if sync == 'sdn_mac_report?':
                        remove_assignment(tr, 'sdn_sensing_degradation_pending = true')
                    if sync == 'sdn_service_request?':
                        set_label(tr, 'synchronisation', 'bus_admit_request?')
                    if sync in ('sdn_service_accept!', 'sdn_service_degraded!', 'sdn_service_reject!'):
                        # Publish the request tag; spontaneous policy evaluations are untagged.
                        old = label(tr, 'assignment')
                        set_label(tr, 'assignment', 'bus_outcome_for_request = sdn_service_request_pending, ' + old)
                        if 'sdn_service_request_pending = false' not in old:
                            append_update(tr, 'sdn_service_request_pending = false')
                if original == 'A_RULE' and sync == 'sdn_ack?':
                    set_label(tr, 'synchronisation', 'bus_rule_ack?')
                if original == 'A_SDN_AGG':
                    if sync == 'sdn_sdn_policy_cmd!':
                        set_label(tr, 'synchronisation', 'bus_ctrl_request!')
                        append_update(tr, 'bus_ctrl_open = true')
                    if sync == 'sdn_ack?':
                        set_label(tr, 'synchronisation', 'bus_ctrl_ack?')
                        append_update(tr, 'bus_ctrl_open = false')
                    if sync == 'sdn_timeout_report!':
                        append_update(tr, 'bus_ctrl_open = false')
                if original == 'A_REC':
                    typed = {'sdn_sdn_policy_cmd!': 'bus_rec_policy_request!',
                             'sdn_flow_mod!': 'bus_rec_flow_request!', 'sdn_rollback_cmd!': 'bus_rollback_request!'}
                    if sync in typed:
                        set_label(tr, 'synchronisation', typed[sync])
                    if sync == 'sdn_sdn_policy_cmd!':
                        append_update(tr, 'bus_rec_policy_open = true')
                    if source_name(t, tr) == 'StandbySwitch':
                        append_update(tr, 'bus_rec_policy_open = false')
                    if sync == 'sdn_ack?':
                        suffix = {'StandbySwitch': 'policy', 'ReactiveReembedding': 'flow', 'Rollback': 'rollback'}[source_name(t, tr)]
                        set_label(tr, 'synchronisation', f'bus_rec_{suffix}_ack?')
                    remove_assignment(tr, 'sdn_command_pending = true')
            if layer == 'mac' and original == 'A_SCH':
                if sync == 'mac_mac_schedule_cmd!':
                    append_update(tr, 'mac_c_phy_ack = 0, bus_schedule_open = true, '
                                  'mac_c_obs_ack = 0, mac_obs_ack_active = true')
                if source_name(t, tr) == 'WaitPHYAck':
                    # Partition the original completion edge into exhaustive,
                    # disjoint clock regions. No added delay, sync or invariant.
                    # Clock comparisons belong in guards, not bool assignments.
                    old_guard = label(tr, 'guard')
                    append_update(tr, 'bus_schedule_open = false, mac_obs_ack_active = false')
                    late = deepcopy(tr)
                    set_label(tr, 'guard', f'({old_guard}) && mac_c_obs_ack <= mac_D_phy_ack')
                    set_label(late, 'guard', f'({old_guard}) && mac_c_obs_ack > mac_D_phy_ack')
                    append_update(late, 'mac_obs_ack_late = true')
                    t.append(late)
                if sync == 'mac_phy_kpi_report?':
                    # CollectKPI invariant already bounds c_sched; broadcast input
                    # cannot legally contain a clock guard in UPPAAL.
                    set_label(tr, 'guard', '')
                    append_update(tr, 'bus_mac_report_consumed = true')
        if layer == 'sdn' and original == 'A_REC':
            recovery_policy(t)
            record_recovery(t)
            record_attempts(t)
        if layer == 'mac' and original == 'A_SCH':
            for loc in t.findall('location'):
                name = loc.findtext('name')
                edge(t, name, name, sync='bus_policy?', update='mac_sdn_comm_priority_allowed = bus_allow_comm, mac_sdn_sensing_priority_allowed = bus_allow_sensing')
        if layer == 'app' and original == 'Req':
            for loc in t.findall('location'):
                for inv in list(loc.findall("label[@kind='invariant']")):
                    if 'app_age_sensing' in (inv.text or ''):
                        loc.remove(inv)
            edge(t, 'RequestPending', 'Rejected', guard='app_c_admission == app_D_admission',
                 update='app_admissionClass = app_ADM_REJECTED, app_service_request_pending = false, bus_admission_timeout = true')
        if layer == 'app' and original == 'Sla':
            # Reports do not end monitoring of the one service. Allow new bad KPI
            # notifications to start a fresh reporting deadline after a report.
            edge(t, 'SLAReported', 'SLAViolated', guard='app_gSlaViolation()', sync='app_sla_violation?',
                 update='app_c_sla_violation = 0, app_note_sla_violation_event(), app_sla_violation_report_sent = false, app_violation_report_sent = false')
            edge(t, 'SLAReported', 'SLAWarning', guard='app_gSlaWarning()', sync='app_sla_warn?',
                 update='app_c_sla_warn = 0, app_note_sla_warning_event(), app_sla_warning_report_sent = false')
        if layer == 'phy' and original.startswith('Obs'):
            # Observe every broadcast, then classify its timing in a committed
            # state. Late responses record a violation without blocking the sender.
            for i, tr in enumerate(list(t.findall('transition'))):
                guard = label(tr, 'guard')
                if not label(tr, 'synchronisation').endswith('?') or 'phy_c_obs_' not in guard:
                    continue
                parts = guard.split('&&', 1)
                clock_part = parts[0].strip()
                boolean_part = parts[1].strip() if len(parts) == 2 else ''
                set_label(tr, 'guard', boolean_part)
                old_target = tr.find('target').get('ref')
                stage = 'Observe_' + str(i)
                tr.find('target').set('ref', location(t, stage, committed=True))
                target_name = next(x.findtext('name') for x in t.findall('location') if x.get('id') == old_target)
                edge(t, stage, target_name, guard=clock_part)
                edge(t, stage, 'Violation', guard=clock_part.replace('<=', '>'))
    return declaration
