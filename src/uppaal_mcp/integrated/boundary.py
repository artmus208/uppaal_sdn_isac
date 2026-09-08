"""Eight finite boundary automata for the single-session candidate.

Every timed binary offer has a deadline loss edge. Payload stages are committed
and precede handshakes, so receiver guards never depend on sender-side updates.
"""
from .xmlutil import edge, template, location

DECLARATIONS = '''
// Candidate abstract units, not physical calibration.
const int bus_D_cmd=1, bus_D_bus=1, bus_T_input=5, bus_T_mac_tick=5;
const int bus_T_demand=1, bus_T_complete=40;
clock bus_time, bus_phy_age, bus_mac_age;
bool bus_phy_valid=false, bus_mac_valid=false;
bool bus_phy_delivery_valid=false, bus_mac_delivery_valid=false;
bool bus_phy_pending=false, bus_mac_pending=false;
bool bus_phy_overwrite=false, bus_mac_overwrite=false;
bool bus_phy_loss=false, bus_mac_loss=false;
bool bus_input_missed=false, bus_tick_missed=false;
bool bus_demand_delivered=false, bus_complete_delivered=false;
bool bus_demand_dropped=false, bus_complete_dropped=false;
bool bus_fault_delivered=false, bus_fault_dropped=false;
bool bus_schedule_loss=false, bus_policy_loss=false, bus_dataplane_loss=false;
bool bus_admission_timeout=false, bus_admission_loss=false;
bool bus_unsolicited_outcome=false, bus_outcome_for_request=false;
bool bus_mac_report_consumed=false, bus_sdn_report_consumed=false;
bool bus_allow_comm=false, bus_allow_sensing=false;
bool bus_warning_recorded=false, bus_violation_recorded=false;
bool bus_reconfigure_recorded=false, bus_terminate_recorded=false, bus_degraded_recorded=false;
bool bus_termination_pending=false;
bool bus_protocol_error=false;
bool bus_schedule_open=false, bus_ctrl_open=false, bus_rec_policy_open=false;
bool bus_rule_drop_recorded=false, bus_failure_recorded=false, bus_timeout_recorded=false;
bool bus_resource_reject_recorded=false, bus_forward_recorded=false, bus_rollback_recorded=false;
int[0,2] bus_missed_detection=0;
int[0,2] bus_pd=0, bus_fa=0, bus_acc=0, bus_coverage=0, bus_miss=0, bus_share=0;
int[0,3] bus_queue=0, bus_resource=0;
bool bus_sensing_bad=false;
int[0,5] bus_policy_value=0;
int[0,6] bus_reason=0;
int[0,5] bus_request_service=0;
int[0,3] bus_request_criticality=0;
int[0,2] bus_request_demand=0;
int[0,2] bus_request_latency=0, bus_request_reliability=0;
int[0,2] bus_request_update=0, bus_request_freshness=0;
int[0,2] bus_request_pd=0, bus_request_fa=0, bus_request_miss=0;
int[0,2] bus_request_accuracy=0, bus_request_coverage=0;
chan bus_policy, bus_ctrl_request, bus_ctrl_ack;
chan bus_rec_policy_request, bus_rec_policy_ack;
chan bus_rec_flow_request, bus_rec_flow_ack, bus_rollback_request, bus_rec_rollback_ack;
chan bus_rule_ack, bus_admit_request;
broadcast chan bus_new_sample, bus_new_mac_sample;
'''


def environments():
    result = {}
    phy = template('Boundary_E_PHY_INPUT', [('Wait', 'tick <= bus_T_input'), ('Publish', '', True), ('Target', '', True)], 'clock tick; bool target_due=false;')
    # Hold the raw sample while its existing classifier/report pipeline is busy.
    # A skipped sample preserves the old age; it never resets freshness.
    free = '!phy_channel_report_pending && !phy_signal_report_pending && !phy_sensing_report_pending && !phy_phy_kpi_report_pending'
    fields = [('SINRClass',3),('BLERClass',2),('CQIClass',2),('IClass',2),('DopplerClass',1),
              ('DelaySpreadClass',1),('PowerClass',2),('DRTClass',1),('PilotDensityClass',2),
              ('PayloadSenseClass',2),('PRSClass',2),('BeamErrorClass',2),('BlockageClass',2),
              ('PdClass',2),('RfaClass',2),('AccClass',2),('CRBClass',2),('AoSClass',2),
              ('CapClass',2),('CoverageClass',2),('ResourceShareClass',2),('MisClass',2),('BMOverheadClass',2)]
    for i in range(len(fields)+1):
        location(phy, f'Sample{i}', committed=True)
    phy.find('declaration').text += '\n' + '\n'.join(f'int[0,{high}] p{i}=0;' for i,(_,high) in enumerate(fields))
    edge(phy, 'Wait', 'Sample0', guard=f'tick == bus_T_input && {free}', update='tick=0')
    for i,(name,high) in enumerate(fields):
        edge(phy,f'Sample{i}',f'Sample{i+1}',select=f'value:int[0,{high}]',update=f'p{i}=value')
    edge(phy,f'Sample{len(fields)}','Publish',
         guard='!(p13 == phy_PDCLASS_OK && miss == 2) && !(p13 == phy_PDCLASS_FAILED && miss == 0)',
         select='miss:int[0,2], scenario:int[0,3]',
         update=', '.join(f'phy_{name}=p{i}' for i,(name,_) in enumerate(fields)) + ', bus_missed_detection=miss, phy_env_scenario=scenario, phy_input_changed=true, bus_phy_age=0, bus_phy_valid=true')
    edge(phy, 'Wait', 'Wait', guard='tick == bus_T_input', update='tick=0, bus_input_missed=true')
    edge(phy, 'Publish', 'Target', sync='bus_new_sample!', update='phy_target_seen=true, target_due=true')
    edge(phy, 'Target', 'Wait', sync='phy_measure_tick!')
    edge(phy, 'Target', 'Wait', update='bus_input_missed=true, bus_phy_valid=false')
    # Independent target broadcast only after the context update; measurement
    # offer and target event use separate transitions.
    edge(phy, 'Wait', 'Wait', guard='target_due', sync='phy_target_detected!', update='target_due=false')
    result['E_PHY_INPUT'] = phy

    mac = template('Boundary_E_MAC_LOAD', [('Wait','tick <= bus_T_mac_tick'),('Publish','',True),('Offer','',True)], 'clock tick;')
    fields = [('queueClass',4),('bufferClass',2),('delayClass',3),('dropClass',2),('resourceClass',3),('sensingDemand',2),('commDemand',2)]
    edge(mac,'Wait','Publish',guard='tick == bus_T_mac_tick',
         select=', '.join(f'm{i}:int[0,{n}]' for i,(_,n) in enumerate(fields)),
         update=', '.join(f'mac_{s}=m{i}' for i,(s,_) in enumerate(fields)) + ', tick=0, bus_mac_age=0, bus_mac_valid=true')
    edge(mac,'Publish','Offer',sync='bus_new_mac_sample!')
    edge(mac,'Offer','Wait',sync='mac_mac_tick!')
    edge(mac,'Offer','Wait',update='bus_tick_missed=true')
    result['E_MAC_LOAD'] = mac

    service = template('Boundary_E_SERVICE', [('Demand','bus_time <= bus_T_demand'),('DemandCheck','',True),
        ('Run','bus_time <= bus_T_complete'),('CompleteCheck','',True),'Done',('Terminate','',True)])
    edge(service,'Demand','DemandCheck',guard='bus_time == bus_T_demand',sync='app_new_demand!')
    edge(service,'DemandCheck','Run',update='bus_demand_dropped = !bus_demand_delivered')
    edge(service,'Run','CompleteCheck',guard='bus_time == bus_T_complete',sync='app_service_complete!')
    edge(service,'CompleteCheck','Done',update='bus_complete_dropped = !bus_complete_delivered')
    for state in ('Demand','Run','Done'):
        for channel,flag in [('sla_warning_report','warning'),('sla_violation_report','violation'),('service_reconfigure','reconfigure'),('degraded_accept_report','degraded')]:
            edge(service,state,state,sync='app_'+channel+'?',update=f'bus_{flag}_recorded=true')
        edge(service,state,state,sync='app_service_terminate?',update='bus_terminate_recorded=true, bus_termination_pending=true')
        edge(service,state,'Terminate',guard='bus_termination_pending',update='bus_termination_pending=false')
    edge(service,'Terminate','Done',sync='app_service_complete!')
    result['E_SERVICE'] = service
    return result


def schedule_bridge():
    t = template('Boundary_B_PHY_MAC', ['Idle',('First','x <= bus_D_cmd'),('Second','x <= bus_D_cmd'),
                 ('Ack','x <= bus_D_cmd'),'Drain'], 'clock x; int[0,4] mode=0;')
    edge(t,'Idle','First',sync='mac_mac_schedule_cmd?',update='mode=mac_scheduleMode, x=0')
    edge(t,'First','Ack',guard='mode == mac_SCH_COMM',sync='phy_waveform_config!')
    edge(t,'First','Ack',guard='mode == mac_SCH_SENS',sync='phy_sensing_mode_cmd!')
    edge(t,'First','Second',guard='mode == mac_SCH_JOINT',sync='phy_waveform_config!')
    edge(t,'Second','Ack',sync='phy_sensing_mode_cmd!')
    edge(t,'First','Ack',guard='mode == mac_SCH_CONSTRAINED',sync='phy_power_cmd!')
    edge(t,'First','Drain',guard='mode == mac_SCH_IDLE',update='bus_schedule_loss=true')
    edge(t,'Ack','Drain',guard='mac_phy_command_pending && mac_c_phy_ack <= mac_D_phy_ack',sync='mac_phy_ack!')
    for s in ('First','Second','Ack'):
        edge(t,s,'Drain',guard='x == bus_D_cmd',update='bus_schedule_loss=true')
        edge(t,s,s,sync='mac_mac_schedule_cmd?',update='bus_protocol_error=true')
    edge(t,'Drain','Idle',guard='!bus_schedule_open')
    return t


def policy_bridge():
    t = template('Boundary_B_POLICY', ['Idle',('Stage','',True),('Offer','x <= bus_D_bus'),('Ack','x <= bus_D_bus'),'Drain'],
                 'clock x; bool recovery=false;')
    edge(t,'Idle','Stage',sync='bus_ctrl_request?',update='bus_policy_value=sdn_policyClass, recovery=false, x=0')
    edge(t,'Idle','Stage',sync='bus_rec_policy_request?',update='bus_policy_value=sdn_policyClass, recovery=true, x=0')
    edge(t,'Stage','Offer',update='bus_allow_comm=(bus_policy_value == sdn_POL_COMM_PRIO || bus_policy_value == sdn_POL_NORMAL || bus_policy_value == sdn_POL_REROUTE), bus_allow_sensing=(bus_policy_value == sdn_POL_SENS_BOOST || bus_policy_value == sdn_POL_NORMAL || bus_policy_value == sdn_POL_REROUTE)')
    edge(t,'Offer','Ack',sync='bus_policy!')
    edge(t,'Ack','Drain',guard='!recovery && sdn_command_pending && sdn_c_ctrl_ack <= sdn_D_ctrl_ack',sync='bus_ctrl_ack!')
    edge(t,'Ack','Drain',guard='recovery && sdn_c_rec <= sdn_D_recovery',sync='bus_rec_policy_ack!')
    for s in ('Offer','Ack'):
        edge(t,s,'Drain',guard='x == bus_D_bus',update='bus_policy_loss=true')
    edge(t,'Drain','Idle',guard='(!recovery && !bus_ctrl_open) || (recovery && !bus_rec_policy_open)')
    return t


def fault_environment():
    # One process, two orthogonal finite components represented by explicit product
    # locations: fault schedule (before/offered/done) and dataplane transaction.
    fault_states = ['Before','Rule','Link','Node','Done']
    tx_states = ['Idle','Forward','Ack','RecFlow','Rollback']
    states = []
    for f in fault_states:
        for tx in tx_states:
            inv = []
            if f != 'Done': inv.append('bus_time <= 13')
            if tx != 'Idle': inv.append('x <= bus_D_bus')
            states.append((f+'_'+tx, ' && '.join(inv)))
    t=template('Boundary_E_FAULT',states,'clock x; bool lose=false;')
    for tx in tx_states:
        for f,channel in [('Rule','sdn_rule_miss!'),('Link','sdn_link_failure!'),('Node','sdn_node_failure!')]:
            edge(t,'Before_'+tx,f+'_'+tx,guard='bus_time >= 12 && bus_time <= 13',
                 select='standby:int[0,1], alternative:int[0,1]',update='sdn_standby_available=(standby == 1), sdn_alternative_config_exists=(alternative == 1)')
            edge(t,f+'_'+tx,'Done_'+tx,sync=channel,update='bus_fault_delivered=true')
            edge(t,f+'_'+tx,'Done_'+tx,guard='bus_time == 13',update='bus_fault_dropped=true')
        edge(t,'Before_'+tx,'Done_'+tx,guard='bus_time >= 12 && bus_time <= 13')
    for f in fault_states:
        edge(t,f+'_Idle',f+'_Forward',sync='sdn_flow_mod?',select='loss:int[0,1]',update='lose=(loss == 1), x=0')
        edge(t,f+'_Forward',f+'_Ack',sync='sdn_forward_cmd?',update='bus_forward_recorded=true')
        edge(t,f+'_Ack',f+'_Idle',guard='!lose && sdn_rule_miss_pending && sdn_c_rule <= sdn_D_rule_ack',sync='bus_rule_ack!')
        for tx,request,ack in [('RecFlow','bus_rec_flow_request?','bus_rec_flow_ack!'),('Rollback','bus_rollback_request?','bus_rec_rollback_ack!')]:
            edge(t,f+'_Idle',f+'_'+tx,sync=request,select='loss:int[0,1]',update='lose=(loss == 1), x=0' + (', bus_rollback_recorded=true' if tx=='Rollback' else ''))
            edge(t,f+'_'+tx,f+'_Idle',guard='!lose',sync=ack)
        for tx in tx_states[1:]:
            edge(t,f+'_'+tx,f+'_Idle',guard='x == bus_D_bus',update='bus_dataplane_loss=true')
        for tx in tx_states:
            for channel,flag in [('sdn_drop_report?','bus_rule_drop_recorded'),('sdn_failure_report?','bus_failure_recorded'),('sdn_timeout_report?','bus_timeout_recorded'),('mac_resource_reject?','bus_resource_reject_recorded')]:
                edge(t,f+'_'+tx,f+'_'+tx,sync=channel,update=flag+'=true')
    return t


def admission_bridge():
    t=template('Boundary_B_ADMISSION',['Idle',('StageRequest','',True),('OfferRequest','x <= bus_D_bus'),
        ('AwaitOutcome','total <= app_D_admission'),('StageOutcome','',True),('Safety','',True),
        ('OfferOutcome','x <= bus_D_bus'),'Done'],
        'clock x, total; int[0,3] outcome=0;')
    fields = {'service':'serviceClass','criticality':'criticalityClass','demand':'demandClass','latency':'latencyBoundClass',
              'reliability':'reliabilityClass','update':'sensingUpdateBoundClass','freshness':'sensingFreshnessBoundClass',
              'pd':'pdMinClass','fa':'pfaMaxClass','miss':'pmissMaxClass','accuracy':'accuracyBoundClass','coverage':'coverageBoundClass'}
    edge(t,'Idle','StageRequest',sync='app_service_request?',update=', '.join(f'bus_request_{k}=app_{v}' for k,v in fields.items())+', x=0, total=0')
    edge(t,'StageRequest','OfferRequest')
    edge(t,'OfferRequest','AwaitOutcome',sync='bus_admit_request!')
    edge(t,'OfferRequest','Done',guard='x == bus_D_bus',update='bus_admission_loss=true')
    for channel,value in [('sdn_service_accept?',1),('sdn_service_reject?',2),('sdn_service_degraded?',3)]:
        edge(t,'AwaitOutcome','StageOutcome',guard='bus_outcome_for_request',sync=channel,update=f'outcome={value}, bus_reason=sdn_sdnReason, x=0')
        # Tag is set on the emitting edge, so the receiver guard must use the
        # pre-existing request pending flag, not that same-edge publication.
        tr=t.findall('transition')[-1]
        from .xmlutil import set_label
        set_label(tr,'guard','sdn_service_request_pending')
        for state in ('Idle','OfferRequest','Done'):
            edge(t,state,state,sync=channel,update='bus_unsolicited_outcome=true')
        edge(t,'AwaitOutcome','AwaitOutcome',guard='!sdn_service_request_pending',sync=channel,update='bus_unsolicited_outcome=true')
    edge(t,'AwaitOutcome','Done',guard='total == app_D_admission',update='bus_admission_timeout=true')
    edge(t,'StageOutcome','Safety',update='app_admissionClass=outcome, app_degraded_allowed=(outcome == app_ADM_DEGRADED), app_degradedReason=(bus_reason == sdn_SDN_STALE_TELEMETRY ? app_DEG_STALE : (bus_reason == sdn_SDN_RESOURCE_LIMITED ? app_DEG_RESOURCE_LIMITED : app_DEG_COMM_LIMITED))')
    edge(t,'Safety','OfferOutcome',guard='outcome != app_ADM_DEGRADED || app_gSafetyAllowsDegraded()')
    edge(t,'Safety','OfferOutcome',guard='outcome == app_ADM_DEGRADED && !app_gSafetyAllowsDegraded()',update='outcome=app_ADM_REJECTED, app_admissionClass=app_ADM_REJECTED, app_degraded_allowed=false')
    for channel,value in [('app_service_accept!',1),('app_service_reject!',2),('app_service_degraded!',3)]:
        edge(t,'OfferOutcome','Done',guard=f'outcome == {value} && app_service_request_pending',sync=channel)
    edge(t,'OfferOutcome','Done',guard='x == bus_D_bus',update='bus_admission_loss=true')
    return t


def kpi_bridge():
    # Three idle freshness phases enforce expiry exactly at source age 5/10.
    # Expired is unbounded; a new sample restarts Fresh with downstream validity
    # false until an actual report is captured and delivered.
    t=template('Boundary_B_KPI', [('Expired','p <= bus_D_bus && m <= bus_D_bus'),
        ('Fresh','bus_phy_age <= 5 && p <= bus_D_bus && m <= bus_D_bus'),
        ('Stale','bus_phy_age <= 10 && p <= bus_D_bus && m <= bus_D_bus'),
        ('Map','',True),('Mac','',True),('Sdn','',True),('App','',True),('Notify','',True),
        ('MacNotice','',True),('CtrlNotice','',True),('Return','',True),
        ('MacOnly','',True)],
        'clock p, m, n; int[0,2] band=2; bool publishing=false;')
    states=[loc.findtext('name') for loc in t.findall('location')]
    snapshot='bus_phy_overwrite=(bus_phy_overwrite || bus_phy_pending), bus_phy_pending=true, p=0, bus_pd=phy_PdClass, bus_fa=phy_RfaClass, bus_acc=phy_AccClass, bus_coverage=phy_CoverageClass, bus_share=phy_ResourceShareClass, bus_miss=bus_missed_detection, bus_sensing_bad=phy_sensing_degraded_flag'
    for state in states:
        edge(t,state,state,sync='phy_phy_kpi_report?',update=snapshot)
        edge(t,state,state,sync='mac_mac_report?',update='bus_mac_overwrite=(bus_mac_overwrite || bus_mac_pending), bus_mac_pending=true, m=0, bus_queue=(mac_queueClass == mac_Q_CRIT ? 3 : (mac_queueClass == mac_Q_HIGH ? 2 : 0)), bus_resource=mac_resourceClass')
        edge(t,state,state,sync='bus_new_mac_sample?',update='bus_mac_overwrite=(bus_mac_overwrite || bus_mac_pending), bus_mac_pending=false, bus_mac_delivery_valid=false')
        # Explicitly drop outstanding transport on a new raw generation. No old
        # payload receives a fresh age simply because the measurement clock resets.
        edge(t,state,'Fresh',sync='bus_new_sample?',update='bus_phy_overwrite=(bus_phy_overwrite || bus_phy_pending), bus_phy_pending=false, bus_phy_delivery_valid=false, publishing=false, band=0, mac_kpiFreshnessClass=mac_KPI_MISSING, sdn_telemetryClass=sdn_TEL_MISSING, app_detectionFreshnessClass=app_DET_EXPIRED, app_updatePeriodClass=app_UPD_VIOLATED')
    edge(t,'Fresh','Stale',guard='bus_phy_age == 5',update='band=1, mac_kpiFreshnessClass=(bus_phy_delivery_valid ? mac_KPI_STALE : mac_KPI_MISSING), sdn_telemetryClass=(bus_phy_delivery_valid ? sdn_TEL_STALE : sdn_TEL_MISSING), app_detectionFreshnessClass=(bus_phy_delivery_valid ? app_DET_STALE : app_DET_EXPIRED)')
    edge(t,'Stale','Notify',guard='bus_phy_age == 10',sync='phy_aos_ctrl_expired!',update='band=2, mac_kpiFreshnessClass=mac_KPI_MISSING, sdn_telemetryClass=sdn_TEL_MISSING, app_detectionFreshnessClass=app_DET_EXPIRED, app_updatePeriodClass=app_UPD_VIOLATED, app_note_kpi_update_event()')
    for s in ('Fresh','Stale','Expired'):
        edge(t,s,'Map',guard='bus_phy_pending && bus_phy_valid && p <= bus_D_bus',update='bus_phy_pending=false, bus_phy_delivery_valid=true, publishing=true')
        edge(t,s,s,guard='bus_phy_pending && p == bus_D_bus',update='bus_phy_pending=false, bus_phy_loss=true, p=0')
        edge(t,s,s,guard='!bus_phy_pending && p == bus_D_bus',update='p=0')
        edge(t,s,'MacOnly',guard='bus_mac_pending && bus_mac_valid && m <= bus_D_bus',update='bus_mac_pending=false, bus_mac_delivery_valid=true')
        edge(t,s,s,guard='bus_mac_pending && m == bus_D_bus',update='bus_mac_pending=false, bus_mac_loss=true, m=0')
        edge(t,s,s,guard='!bus_mac_pending && m == bus_D_bus',update='m=0')
    # Age guard partition at staging includes bridge residence time.
    for guard,age in [('bus_phy_age < 5',0),('bus_phy_age >= 5 && bus_phy_age < 10',1),('bus_phy_age >= 10',2)]:
        edge(t,'Map','Mac',guard=guard,update=f'band={age}, mac_kpiFreshnessClass={age}, sdn_telemetryClass={age}, app_detectionFreshnessClass={age}, app_updatePeriodClass=({age} == 0 ? app_UPD_OK : ({age} == 1 ? app_UPD_SLOW : app_UPD_VIOLATED)), mac_mappedResourceClass=(bus_share == phy_RESOURCESHARECLASS_STARVED ? mac_RES_EXHAUSTED : (bus_share == phy_RESOURCESHARECLASS_LIMITED ? mac_RES_TIGHT : mac_resourceClass)), app_pdClass=bus_pd, app_falseAlarmClass=bus_fa, app_accuracyClass=bus_acc, app_coverageClass=bus_coverage, app_missedDetectionClass=bus_miss, sdn_sensing_degradation_pending=bus_sensing_bad, bus_mac_report_consumed=false, bus_sdn_report_consumed=false')
    edge(t,'Mac','Sdn',sync='mac_phy_kpi_report!')
    edge(t,'Sdn','App',sync='sdn_phy_kpi_report!')
    edge(t,'App','Notify',sync='app_service_kpi_update!')
    edge(t,'Notify','MacNotice',guard='app_gSlaViolation()',sync='app_sla_violation!',update='n=0')
    edge(t,'Notify','MacNotice',guard='app_gSlaWarning() && !app_gSlaViolation()',sync='app_sla_warn!',update='n=0')
    edge(t,'Notify','MacNotice',guard='!app_gSlaWarning() && !app_gSlaViolation()',update='n=0')
    edge(t,'MacNotice','CtrlNotice',guard='publishing && bus_mac_report_consumed',sync='phy_mac_report_delivered!')
    edge(t,'MacNotice','CtrlNotice',guard='!publishing || !bus_mac_report_consumed')
    edge(t,'MacNotice','CtrlNotice',update='bus_phy_loss=true')
    edge(t,'CtrlNotice','Return',guard='publishing && bus_sdn_report_consumed',sync='phy_controller_report_delivered!')
    edge(t,'CtrlNotice','Return',guard='!publishing || !bus_sdn_report_consumed')
    edge(t,'CtrlNotice','Return',update='bus_phy_loss=true')
    edge(t,'MacOnly','Return',sync='sdn_mac_report!',update='sdn_sliceClass=(bus_resource == mac_RES_EXHAUSTED ? sdn_SLICE_VIOLATED : (bus_queue >= 2 ? sdn_SLICE_WARN : sdn_SLICE_OK))')
    edge(t,'Return','Fresh',guard='bus_phy_valid && bus_phy_age < 5',update='band=0, publishing=false')
    edge(t,'Return','Stale',guard='bus_phy_valid && bus_phy_age >= 5 && bus_phy_age < 10',update='band=1, publishing=false')
    edge(t,'Return','Expired',guard='bus_phy_age >= 10',update='band=2, publishing=false')
    edge(t,'Return','Expired',guard='!bus_phy_valid',update='band=2, publishing=false')
    return t


def build():
    result=environments()
    result.update(E_FAULT=fault_environment(), B_PHY_MAC=schedule_bridge(),
                  B_POLICY=policy_bridge(), B_ADMISSION=admission_bridge(), B_KPI=kpi_bridge())
    return result
