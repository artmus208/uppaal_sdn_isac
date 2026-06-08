# PHY Model Summary

## IR

- PHY components: A_CH, A_SIG, A_BM, A_SQ, A_PH
- ENV components: ENV_CH, ENV_TARGET, ENV_MAC, ENV_NET
- classes: 28
- clocks: 9
- variables: 40
- channels: 45
- env specs: 4
- observers: 3
- properties: 17

## Generated UPPAAL

- templates: Template_A_CH, Template_A_SIG, Template_A_BM, Template_A_SQ, Template_A_PH, Template_ENV_CH, Template_ENV_TARGET, Template_ENV_MAC, Template_ENV_NET
- generated model static validation: failed
- validation errors: Generated model does not contain required template/instance: ObsSenseReport.; Generated model does not contain required template/instance: ObsFreshness.; Generated model does not contain required template/instance: ObsBeamRecovery.; Broadcast channel aos_ctrl_expired has no listener.; Broadcast channel beam_failure has no listener.; Broadcast channel beam_restored has no listener.; Broadcast channel handover_hint has no listener.; Broadcast channel phy_kpi_report has no listener.; Broadcast channel recovery_start has no listener.; Broadcast channel sensing_degraded has no listener.
- query lines: 12
