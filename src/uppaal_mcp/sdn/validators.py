from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

from .alpha import check_no_continuous_guards
from .defaults import build_default_contract
from .ir import SdnContractModel
from .layout import validate_generated_layout

REQUIRED_SDN = ["A_MON", "A_RISK", "A_POLICY", "A_RULE", "A_REC", "A_SDN_AGG"]
REQUIRED_ENV = ["A_ENV_SDN"]
REQUIRED_OBSERVERS = ["ObsRuleMiss", "ObsRecovery", "ObsAdmission", "ObsStaleTelemetry"]
REQUIRED_BROADCAST = ["mac_report", "phy_kpi_report", "service_request", "service_accept", "service_degraded", "service_reject"]
REQUIRED_HANDSHAKES = ["rule_miss", "link_failure", "node_failure", "ack", "sdn_policy_cmd", "flow_mod", "forward_cmd", "drop_report", "failure_report", "timeout_report", "rollback_cmd"]
REQUIRED_CLASSES = ["TelemetryClass", "RiskClass", "PolicyClass", "RuleClass", "RecoveryClass", "SliceClass", "ServiceImpact", "SdnReason"]


@dataclass
class SemanticReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_contract_ir(contract: SdnContractModel | None = None) -> SemanticReport:
    model = contract or build_default_contract()
    errors: list[str] = []
    automata = {item.name for item in model.automata}
    env = {item.name for item in model.env}
    classes = {item.name for item in model.classes}
    channels = {item.name: item.kind for item in model.channels}
    for name in REQUIRED_SDN:
        if name not in model.sdn_components:
            errors.append(f"Missing SDN component in composition: {name}.")
        if name not in automata:
            errors.append(f"Missing SDN automaton spec: {name}.")
    for name in REQUIRED_ENV:
        if name not in model.env_components:
            errors.append(f"Missing SDN ENV component: {name}.")
        if name not in env:
            errors.append(f"Missing SDN ENV spec: {name}.")
    for name in REQUIRED_CLASSES:
        if name not in classes:
            errors.append(f"Missing SDN class spec: {name}.")
    for name in REQUIRED_BROADCAST:
        if channels.get(name) != "broadcast":
            errors.append(f"{name} must be broadcast.")
    for name in REQUIRED_HANDSHAKES:
        if channels.get(name) != "handshake":
            errors.append(f"{name} must be handshake.")
    policies = {item.name for item in model.policies}
    for name in ("POL_REJECT", "POL_CONSTRAINED", "POL_REROUTE", "POL_SENS_BOOST", "POL_COMM_PRIO", "POL_NORMAL"):
        if name not in policies:
            errors.append(f"Missing SDN policy: {name}.")
    observers = {item.name for item in model.observers}
    for name in REQUIRED_OBSERVERS:
        if name not in observers:
            errors.append(f"Missing observer: {name}.")
    interfaces = {item.name for item in model.interfaces}
    for name in ("rule_miss", "recovery", "sensing_degradation", "service_admission"):
        if name not in interfaces:
            errors.append(f"Missing interface procedure: {name}.")
    return SemanticReport(ok=not errors, errors=errors, details={"component_count": len(model.sdn_components), "policy_count": len(model.policies), "interface_count": len(model.interfaces)})


def validate_generated_model(model_xml: str, queries: str | None = None, *, require_observers: bool = True, require_environment: bool = True, allow_optional_sec: bool = False) -> SemanticReport:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError as exc:
        return SemanticReport(ok=False, errors=[f"XML parse error: {exc}"])
    declarations = root.findtext("declaration") or ""
    system = root.findtext("system") or ""
    template_names = [_text(t.find("name")) for t in root.findall("template")]
    all_names = set(template_names) | set(_system_instances(system))
    if "A_SEC" in _system_instances(system) and not allow_optional_sec:
        errors.append("A_SEC must not be forced into the base SDN/RIC system; use mode=with_optional_sec.")
    required = list(REQUIRED_SDN)
    if require_environment:
        required.extend(REQUIRED_ENV)
    if require_observers:
        required.extend(REQUIRED_OBSERVERS)
    for name in required:
        if name not in all_names and f"Template_{name}" not in all_names:
            errors.append(f"Generated SDN model missing required template/instance: {name}.")
    for name in REQUIRED_BROADCAST:
        if not _declares_broadcast(declarations, name):
            errors.append(f"{name} must be declared as broadcast chan.")
    for name in REQUIRED_HANDSHAKES:
        if not _declares_handshake(declarations, name):
            errors.append(f"{name} must be declared as handshake chan.")
    errors.extend(check_no_continuous_guards(_without_comments(model_xml)).errors)
    errors.extend(_check_one_sync(root))
    errors.extend(_check_single_writer(root))
    errors.extend(_check_policy_helpers(declarations))
    errors.extend(_check_stale_policy(root, declarations))
    errors.extend(_check_rule_outcomes(root))
    errors.extend(_check_admission_outcomes(root))
    errors.extend(_check_recovery_outcomes(root))
    errors.extend(_check_command_timeout(root))
    if require_observers:
        errors.extend(_check_observers(root))
    errors.extend(validate_generated_layout(model_xml).errors)
    if queries is not None:
        errors.extend(_check_query_references(root, system, queries))
        if "A[] not deadlock" in queries and not require_environment:
            errors.append("Open SDN model must not use bare A[] not deadlock.")
    return SemanticReport(ok=not errors, errors=errors, warnings=warnings, details={"templates": template_names, "instances": _system_instances(system)})


def _declares_broadcast(declarations: str, name: str) -> bool:
    return bool(re.search(rf"\bbroadcast\s+chan\b[^;]*\b{name}\b", declarations))


def _declares_handshake(declarations: str, name: str) -> bool:
    return bool(re.search(rf"(?<!broadcast\s)\bchan\b[^;]*\b{name}\b", declarations))


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else element.text.strip()


def _system_instances(system: str) -> list[str]:
    return re.findall(r"^\s*([A-Za-z_]\w*)\s*=", system, flags=re.MULTILINE)


def _without_comments(text: str) -> str:
    return re.sub(r"//.*", "", text)


def _check_one_sync(root: ET.Element) -> list[str]:
    errors = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        for tr in template.findall("transition"):
            syncs = [label for label in tr.findall("label") if label.attrib.get("kind") == "synchronisation"]
            if len(syncs) > 1:
                errors.append(f"{name} has a transition with more than one sync label.")
    return errors


def _check_single_writer(root: ET.Element) -> list[str]:
    allowed = {
        "policyClass": {"Template_A_POLICY"},
        "serviceImpact": {"Template_A_POLICY", "Template_A_RULE", "Template_A_REC"},
        "sdnReason": {"Template_A_POLICY", "Template_A_RULE", "Template_A_REC", "Template_A_SDN_AGG"},
        "optimistic_reconfig": {"Template_A_MON", "Template_A_POLICY", "Template_A_RULE", "Template_A_REC", "Template_A_ENV_SDN"},
        "rule_miss_pending": {"Template_A_RULE"},
        "link_failure_pending": {"Template_A_REC"},
        "node_failure_pending": {"Template_A_REC"},
        "command_pending": {"Template_A_POLICY", "Template_A_REC", "Template_A_SDN_AGG"},
    }
    errors = []
    for template in root.findall("template"):
        name = _text(template.find("name"))
        for label in template.findall(".//label"):
            if label.attrib.get("kind") != "assignment":
                continue
            text = _text(label)
            for var, owners in allowed.items():
                if re.search(rf"\b{var}\s*=", text) and name not in owners:
                    errors.append(f"{name} writes {var}; allowed writers: {', '.join(sorted(owners))}.")
    return errors


def _check_policy_helpers(declarations: str) -> list[str]:
    errors = []
    for name in ("gPolReject", "gPolConstrained", "gPolReroute", "gPolSensingBoost", "gPolCommPrio", "reconfig_allowed"):
        if not re.search(rf"\b{name}\s*\(", declarations):
            errors.append(f"Missing SDN policy helper {name}().")
    if "select_sdn_policy()" not in declarations:
        errors.append("Missing select_sdn_policy().")
    return errors


def _check_stale_policy(root: ET.Element, declarations: str) -> list[str]:
    errors = []
    if "telemetryClass == TEL_FRESH" not in declarations or "policyClass != POL_CONSTRAINED" not in declarations:
        errors.append("reconfig_allowed() must require fresh telemetry and non-constrained/non-reject policy.")
    assignments = [_text(label) for label in root.findall(".//label") if label.attrib.get("kind") == "assignment"]
    for assignment in assignments:
        compact = " ".join(assignment.split())
        if re.search(r"telemetryClass\s*=\s*TEL_(STALE|MISSING)", compact) and re.search(r"optimistic_reconfig\s*=\s*true", compact):
            errors.append("stale/missing telemetry assignment enables optimistic_reconfig=true.")
    return errors


def _check_rule_outcomes(root: ET.Element) -> list[str]:
    rule = _template(root, "A_RULE")
    if rule is None:
        return ["A_RULE not found for rule outcome check."]
    labels = _transition_labels(rule)
    errors = []
    for token in ("flow_mod!", "drop_report!", "timeout_report!"):
        if token not in labels:
            errors.append(f"A_RULE missing explicit rule miss outcome {token}.")
    for loc in ("RuleAcked", "RuleDropReason", "RuleTimeout"):
        if loc not in _locations(rule):
            errors.append(f"A_RULE missing outcome location {loc}.")
    return errors


def _check_admission_outcomes(root: ET.Element) -> list[str]:
    policy = _template(root, "A_POLICY")
    if policy is None:
        return ["A_POLICY not found for admission outcome check."]
    labels = _transition_labels(policy)
    errors = []
    for token in ("service_accept!", "service_degraded!", "service_reject!"):
        if token not in labels:
            errors.append(f"A_POLICY missing service admission outcome {token}.")
    return errors


def _check_recovery_outcomes(root: ET.Element) -> list[str]:
    rec = _template(root, "A_REC")
    if rec is None:
        return ["A_REC not found for recovery outcome check."]
    labels = _transition_labels(rec)
    errors = []
    for token in ("rollback_cmd!", "failure_report!", "ack?"):
        if token not in labels:
            errors.append(f"A_REC missing recovery outcome {token}.")
    if "failure_report_sent = true" not in labels:
        errors.append("A_REC recovery failure must set failure_report_sent=true.")
    return errors


def _check_command_timeout(root: ET.Element) -> list[str]:
    agg = _template(root, "A_SDN_AGG")
    if agg is None:
        return ["A_SDN_AGG not found for command timeout check."]
    labels = _transition_labels(agg)
    errors = []
    if "ack?" not in labels:
        errors.append("A_SDN_AGG missing ack? success path.")
    if "c_ctrl_ack == D_ctrl_ack" not in labels or "timeout_report!" not in labels:
        errors.append("A_SDN_AGG missing command timeout path.")
    return errors


def _check_observers(root: ET.Element) -> list[str]:
    errors = []
    for name in REQUIRED_OBSERVERS:
        template = _template(root, name)
        if template is None:
            errors.append(f"Missing observer template: {name}.")
            continue
        locs = _locations(template)
        if name == "ObsStaleTelemetry":
            if not {"Safe", "Violation"}.issubset(locs):
                errors.append(f"{name} must contain Safe/Violation.")
            continue
        if not {"Idle", "Wait", "Violation"}.issubset(locs):
            errors.append(f"{name} must contain Idle/Wait/Violation.")
        wait_invariants = [
            _text(label)
            for loc in template.findall("location")
            if _text(loc.find("name")) == "Wait"
            for label in loc.findall("label")
            if label.attrib.get("kind") == "invariant"
        ]
        if wait_invariants:
            errors.append(f"{name} Wait location must not carry deadline invariant; use x > D violation edge.")
    return errors


def _check_query_references(root: ET.Element, system: str, queries: str) -> list[str]:
    errors = []
    instances = set(_system_instances(system))
    instance_templates = dict(re.findall(r"^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\(", system, flags=re.MULTILINE))
    locs_by_template = {}
    for template in root.findall("template"):
        name = _text(template.find("name"))
        locs_by_template[name] = _locations(template)
    for query in [line.strip() for line in queries.splitlines() if line.strip()]:
        for inst, loc in re.findall(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b", query):
            if inst not in instances:
                errors.append(f"Query references unknown SDN instance {inst}: {query}")
                continue
            template_name = instance_templates.get(inst, inst)
            if loc not in locs_by_template.get(template_name, set()):
                errors.append(f"Query references unknown SDN location {inst}.{loc}: {query}")
    return errors


def _template(root: ET.Element, name: str) -> ET.Element | None:
    for template in root.findall("template"):
        template_name = _text(template.find("name"))
        if template_name == name or template_name == f"Template_{name}":
            return template
    return None


def _locations(template: ET.Element) -> set[str]:
    return {_text(loc.find("name")) for loc in template.findall("location")}


def _transition_labels(template: ET.Element) -> str:
    return "\n".join(_text(label) for label in template.findall(".//label"))
