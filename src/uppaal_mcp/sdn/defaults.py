from __future__ import annotations

from .ir import (
    AutomatonSpec,
    ChannelSpec,
    ClassSpec,
    ClockSpec,
    ContractSpec,
    EnvSpec,
    InterfaceProcedureSpec,
    LocationSpec,
    ObserverSpec,
    PolicySpec,
    PropertySpec,
    Provenance,
    SdnContractModel,
    VariableSpec,
)

SOURCE = "SDN_RIC_control_plane_formalization.tex"


def p(section: str, line: int | None = None) -> Provenance:
    return Provenance(source=SOURCE, section=section, line=line)


def build_default_contract() -> SdnContractModel:
    classes = [
        ClassSpec("TelemetryClass", ["TEL_FRESH", "TEL_STALE", "TEL_MISSING"], p("Discrete abstraction", 117)),
        ClassSpec("RiskClass", ["RISK_LOW", "RISK_MED", "RISK_HIGH", "RISK_CRIT"], p("Discrete abstraction", 118)),
        ClassSpec("PolicyClass", ["POL_NORMAL", "POL_SENS_BOOST", "POL_COMM_PRIO", "POL_CONSTRAINED", "POL_REROUTE", "POL_REJECT"], p("Discrete abstraction", 119)),
        ClassSpec("RuleClass", ["RULE_OK", "RULE_MISS", "RULE_PENDING", "RULE_ACKED", "RULE_TIMEOUT", "RULE_DROP"], p("Discrete abstraction", 120)),
        ClassSpec("RecoveryClass", ["REC_STABLE", "REC_STANDBY", "REC_REEMBED", "REC_ROLLBACK", "REC_FAILED"], p("Discrete abstraction", 121)),
        ClassSpec("SliceClass", ["SLICE_OK", "SLICE_WARN", "SLICE_VIOLATED"], p("Discrete abstraction", 122)),
        ClassSpec("ServiceImpact", ["IMPACT_NONE", "IMPACT_DEGRADED", "IMPACT_REJECTED", "IMPACT_FAILED"], p("Declarations", 295)),
        ClassSpec("SdnReason", ["SDN_NONE", "SDN_STALE_TELEMETRY", "SDN_RULE_TIMEOUT", "SDN_RECOVERY_FAILED", "SDN_RESOURCE_LIMITED", "SDN_SENSING_FAILURE", "SDN_POLICY_REJECT"], p("Declarations", 299)),
    ]
    clocks = [
        ClockSpec("c_mon", "Telemetry collection age.", "reset on report collection", p("Clocks and invariants", 174)),
        ClockSpec("c_dec", "Policy decision age.", "reset on Evaluate", p("Clocks and invariants", 175)),
        ClockSpec("c_rule", "Rule miss handling age.", "reset on rule_miss", p("Clocks and invariants", 176)),
        ClockSpec("c_ctrl_ack", "Lower-plane command acknowledgement age.", "reset on command send", p("Clocks and invariants", 177)),
        ClockSpec("c_rec", "Recovery age after link/node failure.", "reset on failure detection", p("Clocks and invariants", 178)),
        ClockSpec("c_rollback", "Rollback age.", "reset on rollback", p("Clocks and invariants", 179)),
        ClockSpec("c_admission", "Service admission response age.", "reset on service_request", p("Clocks and invariants", 180)),
        ClockSpec("c_sec_ack", "Optional security acknowledgement age.", "optional A_SEC only", p("Optional extension", 605)),
    ]
    variables = [
        VariableSpec("telemetryClass", "TelemetryClass_t", "TEL_FRESH", "alpha_SDN class"),
        VariableSpec("riskClass", "RiskClass_t", "RISK_LOW", "risk classifier output"),
        VariableSpec("policyClass", "PolicyClass_t", "POL_NORMAL", "SDN policy decision"),
        VariableSpec("ruleClass", "RuleClass_t", "RULE_OK", "flow rule state"),
        VariableSpec("recoveryClass", "RecoveryClass_t", "REC_STABLE", "recovery state"),
        VariableSpec("sliceClass", "SliceClass_t", "SLICE_OK", "slice status"),
        VariableSpec("serviceImpact", "ServiceImpact_t", "IMPACT_NONE", "service-layer response payload"),
        VariableSpec("sdnReason", "SdnReason_t", "SDN_NONE", "explicit reason payload"),
        VariableSpec("rule_miss_pending", "bool", "false", "observer trigger"),
        VariableSpec("link_failure_pending", "bool", "false", "observer trigger"),
        VariableSpec("node_failure_pending", "bool", "false", "observer trigger"),
        VariableSpec("sensing_degradation_pending", "bool", "false", "policy input flag"),
        VariableSpec("service_request_pending", "bool", "false", "admission observer trigger"),
        VariableSpec("command_pending", "bool", "false", "command ack observer trigger"),
        VariableSpec("optimistic_reconfig", "bool", "false", "safety flag"),
        VariableSpec("standby_available", "bool", "false", "finite recovery option"),
        VariableSpec("alternative_config_exists", "bool", "false", "finite recovery option"),
        VariableSpec("lower_ack_received", "bool", "false", "ack payload replacement"),
        VariableSpec("failure_report_sent", "bool", "false", "explicit recovery failure output"),
    ]
    channels = [
        ChannelSpec("mac_report", "broadcast", "MAC-to-SDN finite report", p("Channels", 197)),
        ChannelSpec("phy_kpi_report", "broadcast", "PHY-to-SDN finite KPI report", p("Channels", 197)),
        ChannelSpec("service_request", "broadcast", "Service-to-SDN finite request", p("Channels", 197)),
        ChannelSpec("service_accept", "broadcast", "SDN accepts service", p("Channels", 204)),
        ChannelSpec("service_degraded", "broadcast", "SDN admits degraded service", p("Channels", 204)),
        ChannelSpec("service_reject", "broadcast", "SDN rejects service with reason", p("Channels", 204)),
        ChannelSpec("rule_miss", "handshake", "Data plane rule miss", p("Channels", 197)),
        ChannelSpec("link_failure", "handshake", "Link failure event", p("Channels", 197)),
        ChannelSpec("node_failure", "handshake", "Node failure event", p("Channels", 197)),
        ChannelSpec("ack", "handshake", "Lower-plane acknowledgement", p("Channels", 197)),
        ChannelSpec("sdn_policy_cmd", "handshake", "Policy command to MAC/lower plane", p("Channels", 204)),
        ChannelSpec("flow_mod", "handshake", "Install flow rule", p("Channels", 204)),
        ChannelSpec("forward_cmd", "handshake", "Forward command", p("Channels", 204)),
        ChannelSpec("drop_report", "handshake", "Explicit drop report", p("Channels", 204)),
        ChannelSpec("failure_report", "handshake", "Explicit recovery failure report", p("Channels", 204)),
        ChannelSpec("timeout_report", "handshake", "Explicit timeout report", p("Channels", 204)),
        ChannelSpec("rollback_cmd", "handshake", "Rollback command", p("Channels", 204)),
    ]
    automata = [
        AutomatonSpec(
            "A_MON",
            "MonitorIdle",
            [
                LocationSpec("MonitorIdle"),
                LocationSpec("CollectReports", "c_mon <= D_mon"),
                LocationSpec("TelemetryFresh"),
                LocationSpec("TelemetryStale"),
                LocationSpec("TelemetryMissing"),
            ],
            guarantees=["MAC/PHY reports update TelemetryClass by D_mon"],
            provenance=p("UPPAAL templates", 428),
        ),
        AutomatonSpec(
            "A_RISK",
            "RiskLow",
            [LocationSpec("RiskLow"), LocationSpec("RiskMedium"), LocationSpec("RiskHigh"), LocationSpec("RiskCritical")],
            guarantees=["riskClass follows telemetry/rule/recovery/slice classes"],
            provenance=p("UPPAAL templates", 428),
        ),
        AutomatonSpec(
            "A_POLICY",
            "PolicyIdle",
            [
                LocationSpec("PolicyIdle"),
                LocationSpec("Evaluate", "c_dec <= D_decision"),
                LocationSpec("NormalMode"),
                LocationSpec("SensingBoostMode"),
                LocationSpec("CommPriorityMode"),
                LocationSpec("ConstrainedMode"),
                LocationSpec("RejectByPolicy"),
            ],
            guarantees=["policy decision is selected by D_decision", "stale telemetry cannot trigger optimistic reconfiguration"],
            provenance=p("UPPAAL templates", 428),
        ),
        AutomatonSpec(
            "A_RULE",
            "RuleStable",
            [
                LocationSpec("RuleStable"),
                LocationSpec("RuleMiss"),
                LocationSpec("RuleInstallPending", "c_rule <= D_rule_install"),
                LocationSpec("RuleInstalled"),
                LocationSpec("RuleAcked"),
                LocationSpec("RuleTimeout"),
                LocationSpec("RuleDropReason"),
            ],
            guarantees=["rule miss ends with install+ack, drop reason, or timeout report"],
            provenance=p("UPPAAL templates", 428),
        ),
        AutomatonSpec(
            "A_REC",
            "StableConfig",
            [
                LocationSpec("StableConfig"),
                LocationSpec("FailureDetected"),
                LocationSpec("StandbySwitch", "c_rec <= D_recovery"),
                LocationSpec("ReactiveReembedding", "c_rec <= D_recovery"),
                LocationSpec("Rollback", "c_rollback <= D_rollback"),
                LocationSpec("RecoveryFailed"),
            ],
            guarantees=["link/node failure ends with stable config, rollback, or explicit failure"],
            provenance=p("UPPAAL templates", 428),
        ),
        AutomatonSpec(
            "A_SDN_AGG",
            "CommandBuild",
            [
                LocationSpec("CommandBuild"),
                LocationSpec("CommandSent"),
                LocationSpec("AwaitAck", "c_ctrl_ack <= D_ctrl_ack"),
                LocationSpec("Acked"),
                LocationSpec("CommandTimeout"),
            ],
            guarantees=["lower-plane command is acknowledged or timed out by D_ctrl_ack"],
            provenance=p("UPPAAL templates", 428),
        ),
    ]
    env = [
        EnvSpec(
            "A_ENV_SDN",
            "EnvIdle",
            [LocationSpec("EnvIdle")],
            assumptions=[
                "reports and requests are finite-class payloads written before sync",
                "rule/link/node events are bounded by local environment projection",
                "lower-plane ack either arrives or timeout path is enabled",
                "finite recovery alternatives are represented by booleans",
            ],
            provenance=p("Architectural position", 83),
        )
    ]
    observers = [
        ObserverSpec("ObsRuleMiss", "rule_miss_pending", ["RULE_ACKED", "RULE_DROP", "RULE_TIMEOUT"], "D_rule_install", "A[] not ObsRuleMiss.Violation", p("Observers", 477)),
        ObserverSpec("ObsRecovery", "link_failure_pending || node_failure_pending", ["REC_STABLE", "REC_FAILED"], "D_recovery + D_rollback", "A[] not ObsRecovery.Violation", p("Observers", 489)),
        ObserverSpec("ObsAdmission", "service_request_pending", ["IMPACT_NONE", "IMPACT_DEGRADED", "IMPACT_REJECTED"], "D_admission", "A[] not ObsAdmission.Violation", p("Observers", 502)),
        ObserverSpec("ObsStaleTelemetry", "telemetryClass == TEL_STALE || telemetryClass == TEL_MISSING", ["!optimistic_reconfig"], "0", "A[] not ObsStaleTelemetry.Violation", p("Observers", 514)),
        ObserverSpec("ObsCommandAck", "command_pending", ["!command_pending"], "D_ctrl_ack", "A[] not ObsCommandAck.Violation", p("Observers", 474)),
        ObserverSpec("ObsSensingDecision", "sensing_degradation_pending", ["POL_SENS_BOOST", "POL_CONSTRAINED", "POL_REJECT"], "D_decision", "A[] not ObsSensingDecision.Violation", p("Interface table", 227)),
    ]
    policies = [
        PolicySpec("POL_REJECT", "riskClass == RISK_CRIT || sliceClass == SLICE_VIOLATED || recoveryClass == REC_FAILED", "RejectByPolicy", "service_reject/drop_report with reason", p("Policy guards", 355)),
        PolicySpec("POL_CONSTRAINED", "telemetryClass == TEL_STALE || telemetryClass == TEL_MISSING || riskClass == RISK_HIGH || sliceClass == SLICE_WARN", "ConstrainedMode", "conservative command or degraded service", p("Policy guards", 355)),
        PolicySpec("POL_REROUTE", "(ruleClass == RULE_MISS || link_failure_pending || node_failure_pending) && finite alternative && fresh telemetry", "NormalMode/Reroute", "flow_mod or standby command", p("Policy guards", 355)),
        PolicySpec("POL_SENS_BOOST", "sensing_degradation_pending && fresh telemetry && riskClass != RISK_CRIT", "SensingBoostMode", "sdn_policy_cmd and service_degraded", p("Policy guards", 355)),
        PolicySpec("POL_COMM_PRIO", "service_request_pending && sliceClass != SLICE_VIOLATED && fresh telemetry", "CommPriorityMode", "service_accept and policy command", p("Policy guards", 355)),
        PolicySpec("POL_NORMAL", "fallback when no higher-priority guard holds", "NormalMode", "maintain current rules/slices", p("Policy guards", 355)),
    ]
    interfaces = [
        InterfaceProcedureSpec("rule_miss", "rule_miss?", ["FlowId", "SliceClass", "ServiceId", "RuleClass"], ["RuleStable", "RuleMiss", "RuleInstallPending|RuleDropReason"], ["flow_mod!", "forward_cmd!", "drop_report!", "timeout_report!"], "D_rule_install", p("Interface table", 226)),
        InterfaceProcedureSpec("recovery", "link_failure? | node_failure?", ["FaultId", "AffectedSlice", "AffectedService", "RecoveryClass"], ["StableConfig", "FailureDetected", "StandbySwitch|ReactiveReembedding", "Rollback|StableConfig"], ["sdn_policy_cmd!", "flow_mod!", "rollback_cmd!", "failure_report!"], "D_recovery + D_rollback", p("Interface table", 227)),
        InterfaceProcedureSpec("sensing_degradation", "mac_report? | phy_kpi_report?", ["SensingState", "FreshnessClass", "ResourceClass", "ConflictReason"], ["NormalMode", "Evaluate", "SensingBoostMode|ConstrainedMode|RejectByPolicy"], ["sdn_policy_cmd!", "service_degraded!", "service_reject!"], "D_decision", p("Interface table", 228)),
        InterfaceProcedureSpec("service_admission", "service_request?", ["ServiceClass", "CriticalityClass", "DemandClass", "SLAClass"], ["PolicyIdle", "Evaluate", "NormalMode|ConstrainedMode|RejectByPolicy"], ["service_accept!", "service_degraded!", "service_reject!"], "D_admission", p("Interface table", 229)),
    ]
    properties = [
        PropertySpec("deadlock_free", "A[] not deadlock", "safety", "closed SDN/RIC model has no deadlocks", p("Verification properties", 623)),
        PropertySpec("rule_invariant", "A[] (A_RULE.RuleInstallPending imply c_rule <= D_rule_install)", "timing", "rule install pending respects deadline invariant", p("Verification properties", 624)),
        PropertySpec("stale_no_optimistic", "A[] (telemetryClass == TEL_STALE imply !optimistic_reconfig)", "safety", "stale telemetry blocks optimistic reconfiguration", p("Verification properties", 626)),
        PropertySpec("missing_no_optimistic", "A[] (telemetryClass == TEL_MISSING imply !optimistic_reconfig)", "safety", "missing telemetry blocks optimistic reconfiguration", p("Verification properties", 626)),
        PropertySpec("recovery_failure_report", "A[] (recoveryClass == REC_FAILED imply failure_report_sent)", "safety", "recovery failure is explicit", p("Verification properties", 628)),
        PropertySpec("ObsRuleMiss", "A[] not ObsRuleMiss.Violation", "observer", "rule miss has bounded explicit outcome", p("Observers", 477)),
        PropertySpec("ObsRecovery", "A[] not ObsRecovery.Violation", "observer", "recovery has bounded explicit outcome", p("Observers", 489)),
        PropertySpec("ObsAdmission", "A[] not ObsAdmission.Violation", "observer", "admission has bounded service outcome", p("Observers", 502)),
        PropertySpec("ObsStaleTelemetry", "A[] not ObsStaleTelemetry.Violation", "observer", "stale/missing telemetry never enables optimistic reconfiguration", p("Observers", 514)),
        PropertySpec("reach_policy_evaluate", "E<> A_POLICY.Evaluate", "reachability", "policy evaluation is reachable", p("Verification properties", 619)),
        PropertySpec("reach_rule_timeout", "E<> A_RULE.RuleTimeout", "reachability", "rule timeout path is reachable", p("Verification properties", 619)),
        PropertySpec("reach_recovery_failed", "E<> A_REC.RecoveryFailed", "reachability", "recovery failure path is reachable", p("Verification properties", 619)),
    ]
    contracts = [
        ContractSpec(
            "C_SDN",
            [
                "MAC/PHY reports contain finite classes",
                "service request is finite-class payload",
                "policy/rule/recovery configuration spaces are finite",
                "ack either arrives or timeout remains enabled",
            ],
            [
                "rule miss gets install/drop/timeout outcome",
                "stale telemetry forbids optimistic reconfiguration",
                "service admission gets accept/degraded/reject outcome",
                "recovery gets stable/rollback/failure outcome",
                "lower command is acked or reaches CommandTimeout",
            ],
            p("SDN contract", 533),
        )
    ]
    return SdnContractModel(
        source_name=SOURCE,
        layer_id="sdn",
        sdn_components=["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"],
        env_components=["A_ENV_SDN"],
        classes=classes,
        clocks=clocks,
        variables=variables,
        channels=channels,
        automata=automata,
        env=env,
        observers=observers,
        policies=policies,
        interfaces=interfaces,
        properties=properties,
        contracts=contracts,
        mappings={
            "policy_priority": ["POL_REJECT", "POL_CONSTRAINED", "POL_REROUTE", "POL_SENS_BOOST", "POL_COMM_PRIO", "POL_NORMAL"],
            "closed_system": "A_SYS_SDN = A_SDN || A_ENV_SDN",
            "optional_extension": "A_SEC is excluded from base A_SDN",
        },
        limitations=[
            "SDN/RIC timed automata do not learn policies.",
            "SDN/RIC timed automata do not compute PHY metrics.",
            "Recovery probability, expected cost and optimization scores require external/priced/probabilistic models.",
            "A_SEC is optional and outside the base composition.",
        ],
    )
