"""Explicit semantic adaptations applied to copies of the pinned layer XMLs."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from .xmlutil import append_update, edge, label, loc_id, location, set_label, source_name


def remove_assignment(tr, expression):
    parts = [p.strip() for p in label(tr, 'assignment').split(',')]
    set_label(tr, 'assignment', ', '.join(p for p in parts if p != expression))


def adapt_layer(layer, declaration, templates):
    if layer == 'mac':
        declaration = declaration.replace('mac_kpiFreshnessClass = mac_KPI_FRESH', 'mac_kpiFreshnessClass = mac_KPI_MISSING')
    if layer == 'sdn':
        declaration = declaration.replace('sdn_telemetryClass = sdn_TEL_FRESH', 'sdn_telemetryClass = sdn_TEL_MISSING')
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
                    append_update(tr, 'mac_c_phy_ack = 0, bus_schedule_open = true')
                if source_name(t, tr) == 'WaitPHYAck':
                    append_update(tr, 'bus_schedule_open = false')
                if sync == 'mac_phy_kpi_report?':
                    # CollectKPI invariant already bounds c_sched; broadcast input
                    # cannot legally contain a clock guard in UPPAAL.
                    set_label(tr, 'guard', '')
                    append_update(tr, 'bus_mac_report_consumed = true')
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
