from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field

from .alpha import check_no_continuous_guards
from .defaults import build_default_contract
from .ir import MacContractModel
from .layout import validate_generated_layout

REQUIRED_MAC = ["A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG"]
REQUIRED_ENV = ["A_ENV_MAC"]
REQUIRED_OBSERVERS = ["ObsPhyAck", "ObsQueueCritical", "ObsSensingCritical"]
REQUIRED_BROADCAST = ["phy_kpi_report", "mac_report"]
REQUIRED_HANDSHAKES = ["mac_tick", "sdn_policy_cmd", "service_priority", "phy_ack", "mac_schedule_cmd", "beam_update_cmd", "sensing_boost_cmd", "constrained_mode_cmd", "resource_reject"]


@dataclass
class SemanticReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def validate_contract_ir(contract: MacContractModel | None = None) -> SemanticReport:
    model = contract or build_default_contract()
    errors: list[str] = []
    automata = {item.name for item in model.automata}
    env = {item.name for item in model.env}
    classes = {item.name for item in model.classes}
    channels = {item.name: item.kind for item in model.channels}
    for name in REQUIRED_MAC:
        if name not in model.mac_components:
            errors.append(f"Missing MAC component in composition: {name}.")
        if name not in automata:
            errors.append(f"Missing MAC automaton spec: {name}.")
    for name in REQUIRED_ENV:
        if name not in model.env_components:
            errors.append(f"Missing MAC ENV component: {name}.")
        if name not in env:
            errors.append(f"Missing MAC ENV spec: {name}.")
    for name in ("QueueClass", "BufferClass", "DelayClass", "ResourceClass", "SensingDemand", "CommDemand", "KPIFreshnessClass", "ScheduleMode", "MacReason"):
        if name not in classes:
            errors.append(f"Missing MAC class spec: {name}.")
    for name in REQUIRED_BROADCAST:
        if channels.get(name) != "broadcast":
            errors.append(f"{name} must be broadcast.")
    for name in REQUIRED_HANDSHAKES:
        if channels.get(name) != "handshake":
            errors.append(f"{name} must be handshake.")
    policies = {item.name for item in model.policies}
    for index in range(8):
        if f"P{index}" not in policies:
            errors.append(f"Missing MAC policy P{index}.")
    observers = {item.name for item in model.observers}
    for name in REQUIRED_OBSERVERS:
        if name not in observers:
            errors.append(f"Missing observer: {name}.")
    return SemanticReport(ok=not errors, errors=errors, details={"component_count": len(model.mac_components), "policy_count": len(model.policies), "class_count": len(model.classes)})


def validate_generated_model(model_xml: str, queries: str | None = None, *, require_observers: bool = True, require_environment: bool = True) -> SemanticReport:
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
    required = list(REQUIRED_MAC)
    if require_environment:
        required.extend(REQUIRED_ENV)
    if require_observers:
        required.extend(REQUIRED_OBSERVERS)
    for name in required:
        if name not in all_names:
            errors.append(f"Generated MAC model missing required template/instance: {name}.")
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
    errors.extend(_check_no_silent_accept(root))
    errors.extend(_check_ack_timeout_path(root))
    if require_observers:
        errors.extend(_check_observers(root))
    errors.extend(validate_generated_layout(model_xml).errors)
    if queries is not None:
        errors.extend(_check_query_references(root, system, queries))
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
        "scheduleMode": {"A_SCH", "Template_A_SCH"},
        "macReason": {"A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG", "Template_A_SCH", "Template_A_Q", "Template_A_BUF", "Template_A_RSRC", "Template_A_MAC_AGG"},
        "mac_report_pending": {"A_SCH", "A_Q", "A_BUF", "A_RSRC", "A_MAC_AGG", "Template_A_SCH", "Template_A_Q", "Template_A_BUF", "Template_A_RSRC", "Template_A_MAC_AGG"},
        "silent_accept": {"A_SCH", "A_RSRC", "Template_A_SCH", "Template_A_RSRC"},
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
    for index in range(8):
        if not re.search(rf"\bgP{index}\s*\(", declarations):
            errors.append(f"Missing MAC policy guard helper gP{index}().")
    if "select_mac_policy()" not in declarations:
        errors.append("Missing select_mac_policy().")
    return errors


def _check_no_silent_accept(root: ET.Element) -> list[str]:
    declarations = root.findtext("declaration") or ""
    if re.search(r"\bsilent_accept\s*=\s*true\b", declarations):
        return ["Generated MAC model sets silent_accept=true."]
    assignments = "\n".join(_text(label) for label in root.findall(".//label") if label.attrib.get("kind") == "assignment")
    if re.search(r"\bsilent_accept\s*=\s*true\b", assignments):
        return ["Generated MAC model sets silent_accept=true."]
    if "REASON_RESOURCE_EXHAUSTED" not in assignments:
        return ["Generated MAC model has no explicit resource exhaustion report/reject path."]
    return []


def _check_ack_timeout_path(root: ET.Element) -> list[str]:
    sch = _template(root, "A_SCH")
    if sch is None:
        return ["A_SCH not found for ack timeout check."]
    found_timeout = False
    found_ack = False
    for tr in sch.findall("transition"):
        labels = "\n".join(_text(label) for label in tr.findall("label"))
        source_el = tr.find("source")
        target_el = tr.find("target")
        src = _loc_name(sch, source_el.attrib.get("ref", "") if source_el is not None else "")
        target = _loc_name(sch, target_el.attrib.get("ref", "") if target_el is not None else "")
        if src == "WaitPHYAck" and "phy_ack?" in labels and "c_phy_ack <= D_phy_ack" in labels:
            found_ack = True
        if src == "WaitPHYAck" and target == "ScheduleFailure" and "c_phy_ack == D_phy_ack" in labels and "REASON_PHY_ACK_TIMEOUT" in labels:
            found_timeout = True
    errors = []
    if not found_ack:
        errors.append("A_SCH missing PHY ack success path with c_phy_ack <= D_phy_ack.")
    if not found_timeout:
        errors.append("A_SCH missing PHY ack timeout path to ScheduleFailure/mac_report.")
    return errors


def _check_observers(root: ET.Element) -> list[str]:
    errors = []
    for name in REQUIRED_OBSERVERS:
        template = _template(root, name)
        if template is None:
            errors.append(f"Missing observer template: {name}.")
            continue
        locs = {_text(loc.find("name")) for loc in template.findall("location")}
        if not {"Idle", "Wait", "Violation"}.issubset(locs):
            errors.append(f"{name} must contain Idle/Wait/Violation.")
    return errors


def _check_query_references(root: ET.Element, system: str, queries: str) -> list[str]:
    errors = []
    instances = set(_system_instances(system))
    instance_templates = dict(re.findall(r"^\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)\s*\(", system, flags=re.MULTILINE))
    locs_by_template = {}
    for template in root.findall("template"):
        name = _text(template.find("name"))
        locs_by_template[name] = {_text(loc.find("name")) for loc in template.findall("location")}
    for query in [line.strip() for line in queries.splitlines() if line.strip()]:
        for inst, loc in re.findall(r"\b([A-Za-z_]\w*)\.([A-Za-z_]\w*)\b", query):
            if inst not in instances:
                errors.append(f"Query references unknown MAC instance {inst}: {query}")
                continue
            template_name = instance_templates.get(inst, inst)
            if loc not in locs_by_template.get(template_name, set()):
                errors.append(f"Query references unknown MAC location {inst}.{loc}: {query}")
    return errors


def _template(root: ET.Element, name: str) -> ET.Element | None:
    for template in root.findall("template"):
        template_name = _text(template.find("name"))
        if template_name == name or template_name == f"Template_{name}":
            return template
    return None


def _loc_name(template: ET.Element, loc_id: str) -> str:
    for loc in template.findall("location"):
        if loc.attrib.get("id") == loc_id:
            return _text(loc.find("name"))
    return ""
