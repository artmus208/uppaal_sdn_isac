# Code-derived scenario semantics

All line references below address the immutable generated/n1/model.xml at base
91113a1b634f030c7e895f54f5c36a0b140d66eb, model hash in PROTOCOL.md.
model-map.json enumerates every location/transition in system order.

Demand: Boundary_E_SERVICE sends new_demand at bus_time=1 (5834 onward).
A_REQ builds SVC_UAV/CRIT_SAFETY, strict sensing requirements (793–812), emits
service_request, sets pending and resets c_admission (3967–3968).
B_ADMISSION captures the sole request, sends bus_admit_request within D_bus=1;
SDN A_POLICY enters Evaluate and resets c_dec/c_admission (3485–3491).
No request IDs or packets exist; single captured service context, one demand,
one outstanding admission are the correlation available in this composition.

PHY inputs start at tick=5; selected p13 is detection-probability class. Final
sampling forbids PD_FAILED with zero missed detections (4440–4442).
Channel report wakes sensing and PHY aggregate, sensing report sets degradation,
aggregate emits phy_kpi_report. Boundary_B_KPI snapshots and maps PHY classes,
then sends mac_phy_kpi_report, sdn_phy_kpi_report, service_kpi_update and a guarded
sla_violation. These are fan-out notifications, not sequential packet delivery.
The MAC scheduler consumes a report only in CollectKPI and then selects its
actual mode. SDN global mapped telemetry/sensing flags feed the policy guards
(486–495); admission Evaluate can wait for this telemetry within D_decision=5.

SDN sensing boost emits service_degraded (3527–3530). B_ADMISSION captures that
outcome only with SDN pending=true, assigns APP ADM_DEGRADED and reason, then
checks gSafetyAllowsDegraded (765–778). PD_FAILED/MISS_CRITICAL implies
gSlaViolation; safety-critical request cannot accept degraded sensing. The bridge
converts the outcome to ADM_REJECTED and sends service_reject to A_REQ.

APP A_SLA receives sla_violation, resets c_sla_violation and enters SLAViolated
(4074–4078); report goes to SLAReported, sets report_sent and the environment
records bus_violation_recorded (4110–4113, 5890/5926). Bound D_sla_violation=3
is a violation-response deadline, not a service delivery deadline. Observer
query `A[] !u0_obs_app_ObsViolation_0.Bad` concerns this response monitor;
this is a code-derived illustrative formula, not an executed or frozen query.
The selected N=1 query pack contains no APP observer query; query_hash=null.

Grant means optional shared abstract queue subtraction. PHY ACK confirms the
schedule-command boundary, not payload arrival. Neither is linked by a packet
identity to admission or service_complete. A_REQ.Completed is entered only from
Accepted/AcceptedDegraded on service_complete (4030–4041); E_SERVICE supplies
that signal at bus_time=40 or after termination (5873, final edge). Completion
therefore is an environment event, not proof that the queue's serviced item
delivered this APP request. This gap is preserved, not repaired.

The chosen endpoint is explicitly rejection plus recorded violation, not completed
successful service. Final P5 acceptance still needs an applicable Gate 1, matching
accepted P3 evidence and independent reviewer appointment/acceptance.
