from __future__ import annotations

from .ir import (
    AutomatonSpec,
    ChannelSpec,
    ClassSpec,
    ClockSpec,
    ContractSpec,
    EnvSpec,
    LocationSpec,
    MacContractModel,
    ObserverSpec,
    PolicySpec,
    PropertySpec,
    Provenance,
    VariableSpec,
)

SOURCE = "MAC_resource_scheduling_formalization.tex"


def p(section: str, line: int | None = None) -> Provenance:
    return Provenance(source=SOURCE, section=section, line=line)


def build_default_contract() -> MacContractModel:
    classes = [
        ClassSpec("QueueClass", ["Q_EMPTY", "Q_LOW", "Q_MED", "Q_HIGH", "Q_CRIT"], p("Discrete abstraction")),
        ClassSpec("BufferClass", ["B_SAFE", "B_WARN", "B_OVERFLOW"], p("Discrete abstraction")),
        ClassSpec("DelayClass", ["D_OK", "D_WARN", "D_DEADLINE_RISK", "D_VIOLATED"], p("Discrete abstraction")),
        ClassSpec("DropClass", ["DROP_NONE", "DROP_LOW", "DROP_HIGH"], p("Discrete abstraction")),
        ClassSpec("ResourceClass", ["RES_FREE", "RES_BALANCED", "RES_TIGHT", "RES_EXHAUSTED"], p("Discrete abstraction")),
        ClassSpec("SensingDemand", ["SENS_NOMINAL", "SENS_BOOST_REQ", "SENS_CRITICAL"], p("Discrete abstraction")),
        ClassSpec("CommDemand", ["COMM_NOMINAL", "COMM_HIGH", "COMM_CRITICAL"], p("Discrete abstraction")),
        ClassSpec("KPIFreshnessClass", ["KPI_FRESH", "KPI_STALE", "KPI_MISSING"], p("Discrete abstraction")),
        ClassSpec("ScheduleMode", ["SCH_IDLE", "SCH_COMM", "SCH_SENS", "SCH_JOINT", "SCH_CONSTRAINED"], p("Declarations")),
        ClassSpec(
            "MacReason",
            [
                "REASON_NONE",
                "REASON_RESOURCE_EXHAUSTED",
                "REASON_PHY_ACK_TIMEOUT",
                "REASON_QUEUE_CRITICAL",
                "REASON_SENS_COMM_CONFLICT",
                "REASON_STALE_PHY_KPI",
                "REASON_BUFFER_OVERFLOW",
            ],
            p("Declarations"),
        ),
    ]
    clocks = [
        ClockSpec("c_sched", "Scheduling window age.", "reset on mac_tick/selection", p("Operational semantics")),
        ClockSpec("c_phy_ack", "PHY command acknowledgement age.", "reset before waiting for phy_ack", p("Operational semantics")),
        ClockSpec("c_queue", "Queue critical age.", "reset on entering QueueCritical", p("Operational semantics")),
        ClockSpec("c_buf", "Buffer overflow age.", "reset on entering BufferOverflow", p("Operational semantics")),
        ClockSpec("c_report", "MAC report build age.", "reset on ReportBuild", p("Operational semantics")),
    ]
    variables = [
        VariableSpec("queueClass", "QueueClass_t", "Q_EMPTY", "alpha_MAC class"),
        VariableSpec("bufferClass", "BufferClass_t", "B_SAFE", "alpha_MAC class"),
        VariableSpec("delayClass", "DelayClass_t", "D_OK", "alpha_MAC class"),
        VariableSpec("dropClass", "DropClass_t", "DROP_NONE", "alpha_MAC class"),
        VariableSpec("resourceClass", "ResourceClass_t", "RES_FREE", "alpha_MAC class"),
        VariableSpec("mappedResourceClass", "ResourceClass_t", "RES_FREE", "mu_PHY_to_MAC result"),
        VariableSpec("sensingDemand", "SensingDemand_t", "SENS_NOMINAL", "policy input class"),
        VariableSpec("commDemand", "CommDemand_t", "COMM_NOMINAL", "policy input class"),
        VariableSpec("kpiFreshnessClass", "KPIFreshnessClass_t", "KPI_FRESH", "freshness input class"),
        VariableSpec("scheduleMode", "ScheduleMode_t", "SCH_IDLE", "MAC decision"),
        VariableSpec("macReason", "MacReason_t", "REASON_NONE", "report payload"),
        VariableSpec("mac_report_pending", "bool", "false", "report flag"),
        VariableSpec("mac_report_sent", "bool", "false", "report flag"),
        VariableSpec("silent_accept", "bool", "false", "safety flag"),
        VariableSpec("phy_ack_timeout", "bool", "false", "failure flag"),
        VariableSpec("phy_command_pending", "bool", "false", "ack observer flag"),
        VariableSpec("sdn_sensing_priority_allowed", "bool", "false", "policy flag"),
        VariableSpec("sdn_comm_priority_allowed", "bool", "false", "policy flag"),
    ]
    channels = [
        ChannelSpec("phy_kpi_report", "broadcast", "PHY-to-MAC finite KPI report", p("Declarations")),
        ChannelSpec("mac_report", "broadcast", "MAC-to-SDN/RIC report", p("Declarations")),
        ChannelSpec("mac_tick", "handshake", "scheduling window tick", p("Declarations")),
        ChannelSpec("sdn_policy_cmd", "handshake", "finite SDN/RIC policy command", p("Declarations")),
        ChannelSpec("service_priority", "handshake", "service priority update", p("Declarations")),
        ChannelSpec("phy_ack", "handshake", "PHY command acknowledgement", p("Declarations")),
        ChannelSpec("mac_schedule_cmd", "handshake", "PHY scheduling command", p("Declarations")),
        ChannelSpec("beam_update_cmd", "handshake", "PHY beam update command", p("Declarations")),
        ChannelSpec("sensing_boost_cmd", "handshake", "PHY sensing boost command", p("Declarations")),
        ChannelSpec("constrained_mode_cmd", "handshake", "PHY constrained mode command", p("Declarations")),
        ChannelSpec("resource_reject", "handshake", "explicit resource rejection", p("Declarations")),
    ]
    automata = [
        AutomatonSpec(
            "A_SCH",
            "Idle",
            [
                LocationSpec("Idle"),
                LocationSpec("CollectKPI", "c_sched <= D_collect"),
                LocationSpec("SelectMode", "c_sched <= D_sched"),
                LocationSpec("ApplySchedule"),
                LocationSpec("WaitPHYAck", "c_phy_ack <= D_phy_ack"),
                LocationSpec("ScheduleFailure"),
            ],
            guarantees=["fresh KPI/policy selection finishes by D_sched", "PHY command is acknowledged or reported by D_phy_ack"],
            provenance=p("Automaton scheduler"),
        ),
        AutomatonSpec(
            "A_Q",
            "QueueNormal",
            [LocationSpec("QueueNormal"), LocationSpec("QueueWarning"), LocationSpec("QueueCritical", "c_queue <= D_queue_crit"), LocationSpec("QueueDraining")],
            guarantees=["Q_CRIT triggers drain, reject or report by D_queue_crit"],
            provenance=p("Queue and buffer automata"),
        ),
        AutomatonSpec(
            "A_BUF",
            "BufferSafe",
            [LocationSpec("BufferSafe"), LocationSpec("BufferWarning"), LocationSpec("BufferOverflow", "c_buf <= D_buf_report")],
            guarantees=["B_OVERFLOW triggers mac_report by D_buf_report"],
            provenance=p("Queue and buffer automata"),
        ),
        AutomatonSpec(
            "A_RSRC",
            "ResourceAvailable",
            [LocationSpec("ResourceAvailable"), LocationSpec("ResourceTight"), LocationSpec("ResourceConflict"), LocationSpec("ResourceExhausted")],
            guarantees=["RES_EXHAUSTED cannot be silently accepted"],
            provenance=p("Resource automaton"),
        ),
        AutomatonSpec(
            "A_MAC_AGG",
            "ReportIdle",
            [LocationSpec("ReportIdle"), LocationSpec("ReportBuild", "c_report <= D_mac_report"), LocationSpec("ReportSent"), LocationSpec("ReportStale")],
            guarantees=["pending report is emitted by D_mac_report"],
            provenance=p("Report interface"),
        ),
    ]
    env = [
        EnvSpec(
            "A_ENV_MAC",
            "EnvIdle",
            [LocationSpec("EnvIdle")],
            assumptions=[
                "mac_tick is bounded",
                "PHY reports are finite and fresh or explicitly stale",
                "SDN/RIC commands are finite admissible policies",
                "mutually exclusive classes are not forced simultaneously",
            ],
            provenance=p("Local environment"),
        )
    ]
    observers = [
        ObserverSpec("ObsPhyAck", "phy_command_pending", ["!phy_command_pending"], "D_phy_ack", "A[] not ObsPhyAck.Violation", p("Observers")),
        ObserverSpec("ObsQueueCritical", "queueClass == Q_CRIT", ["QueueDraining", "mac_report_sent", "SCH_COMM", "SCH_CONSTRAINED"], "D_queue_crit", "A[] not ObsQueueCritical.Violation", p("Observers")),
        ObserverSpec("ObsSensingCritical", "sensingDemand == SENS_CRITICAL", ["SCH_SENS", "SCH_JOINT", "SCH_CONSTRAINED", "mac_report_sent"], "D_sched", "A[] not ObsSensingCritical.Violation", p("Observers")),
        ObserverSpec("ObsBufferOverflow", "bufferClass == B_OVERFLOW", ["mac_report_sent"], "D_buf_report", "A[] not ObsBufferOverflow.Violation", p("Observers")),
        ObserverSpec("ObsMacReportFreshness", "mac_report_pending", ["mac_report_sent"], "D_mac_report", "A[] not ObsMacReportFreshness.Violation", p("Observers")),
    ]
    policies = [
        PolicySpec("P0", "resourceClass == RES_EXHAUSTED || mappedResourceClass == RES_EXHAUSTED", "SCH_CONSTRAINED", "resource_reject! or mac_report! by D_sched", p("MAC policies")),
        PolicySpec("P1", "bufferClass == B_OVERFLOW || delayClass == D_VIOLATED", "SCH_COMM", "protect communication and report SDN/RIC", p("MAC policies")),
        PolicySpec("P2", "queueClass == Q_CRIT && commDemand == COMM_CRITICAL", "SCH_COMM", "mac_schedule_cmd! or mac_report!", p("MAC policies")),
        PolicySpec("P3", "sensingDemand == SENS_CRITICAL && SDN allows sensing priority", "SCH_SENS or SCH_JOINT", "sensing_boost_cmd! or constrained_mode_cmd!", p("MAC policies")),
        PolicySpec("P4", "resourceClass == RES_TIGHT and both demands active", "SCH_JOINT or SCH_CONSTRAINED", "joint scheduling or deficit report", p("MAC policies")),
        PolicySpec("P5", "KPIFreshnessClass stale or missing", "SCH_CONSTRAINED", "avoid aggressive reconfiguration", p("MAC policies")),
        PolicySpec("P6", "ResourceClass free or balanced", "SCH_JOINT", "ordinary ISAC schedule", p("MAC policies")),
        PolicySpec("P7", "fallback", "SCH_CONSTRAINED", "safe fallback", p("MAC policies")),
    ]
    properties = [
        PropertySpec("deadlock_free", "A[] not deadlock", "safety", "closed MAC model has no deadlocks", p("Verification properties")),
        PropertySpec("no_silent_accept", "A[] (resourceClass == RES_EXHAUSTED imply !silent_accept)", "safety", "exhausted resource is never silently accepted", p("Verification properties")),
        PropertySpec("ack_invariant", "A[] (A_SCH.WaitPHYAck imply c_phy_ack <= D_phy_ack)", "timing", "wait-for-PHY-ack state respects its deadline", p("Verification properties")),
        PropertySpec("ObsPhyAck", "A[] not ObsPhyAck.Violation", "observer", "PHY command is acked or failed by deadline", p("Observers")),
        PropertySpec("ObsQueueCritical", "A[] not ObsQueueCritical.Violation", "observer", "critical queue gets bounded response", p("Observers")),
        PropertySpec("ObsSensingCritical", "A[] not ObsSensingCritical.Violation", "observer", "critical sensing demand gets bounded response", p("Observers")),
        PropertySpec("reach_schedule", "E<> A_SCH.SelectMode", "reachability", "scheduler can reach policy selection", p("Verification properties")),
        PropertySpec("reach_report", "E<> A_MAC_AGG.ReportSent", "reachability", "MAC can emit report", p("Verification properties")),
    ]
    contracts = [
        ContractSpec(
            "C_MAC",
            [
                "PHY report contains finite classes",
                "SDN/RIC command belongs to finite admissible policy set",
                "service priority is already admitted by upper layers",
                "alpha_MAC classes have bounded domains",
            ],
            [
                "critical queue or deadline risk gets bounded local response",
                "critical sensing demand gets bounded command/report",
                "resource exhaustion is explicit reject/constrained/report",
                "PHY command is acknowledged or failed by D_phy_ack",
            ],
            p("MAC contract"),
        )
    ]
    mappings = {
        "mu_PHY_to_MAC": [
            {"phy": "PHYState=PHY_FAILURE or ChannelClass=OUTAGE", "mac": "ResourceClass=RES_EXHAUSTED"},
            {"phy": "PHYCommunicationDegraded or ChannelClass=MOBILITY_LIMITED/MULTIPATH_LIMITED", "mac": "ResourceClass=RES_TIGHT, CommDemand=COMM_HIGH"},
            {"phy": "SensingState=ProbabilityLimited/AccuracyLimited/FreshnessLimited", "mac": "SensingDemand=SENS_BOOST_REQ"},
            {"phy": "nominal PHY classes", "mac": "ResourceClass=RES_BALANCED"},
        ],
        "strictest_priority": ["RES_EXHAUSTED", "RES_TIGHT", "RES_BALANCED", "RES_FREE"],
    }
    return MacContractModel(
        source_name=SOURCE,
        layer_id="mac",
        mac_components=["A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG"],
        env_components=["A_ENV_MAC"],
        classes=classes,
        clocks=clocks,
        variables=variables,
        channels=channels,
        automata=automata,
        env=env,
        observers=observers,
        policies=policies,
        properties=properties,
        contracts=contracts,
        mappings=mappings,
        limitations=[
            "MAC timed automata do not optimize throughput.",
            "MAC timed automata do not simulate stochastic queues.",
            "MAC does not perform SDN/RIC global recovery or admission control.",
            "Raw MAC measurements are external to alpha_MAC.",
        ],
    )

