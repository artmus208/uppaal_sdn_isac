from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .alpha import check_no_continuous_guards, default_profile
from .ir import PhyContractModel, Provenance
from .trace import parse_trace_text
from .validators import validate_contract_ir, validate_generated_model


def generate_report_bundle(
    *,
    contract_json: dict,
    model_xml: str | None = None,
    queries: str | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    profile: dict | None = None,
) -> dict:
    contract = _contract_from_json(contract_json)
    profile = profile or default_profile()
    reports = {
        "report.md": _property_report(contract, queries=queries, result_json=result_json),
        "traceability_matrix.md": _traceability_matrix(contract),
        "model_summary.md": _model_summary(contract, model_xml=model_xml, queries=queries),
        "assume_guarantee_report.md": _assume_guarantee_report(contract),
        "alpha_profile_report.md": _alpha_profile_report(profile, model_xml=model_xml, contract=contract),
        "coverage_report.md": _coverage_report(contract_json),
        "publication_tables.md": _publication_tables(contract),
        "properties.csv": _properties_csv(contract, result_json=result_json),
    }
    if result_json:
        reports["violations.md"] = _violations_report(result_json)
    if trace_text:
        reports["trace_explanation.md"] = _trace_explanation_report(trace_text, result_json=result_json)
    return {
        "summary": {
            "report_count": len(reports),
            "property_count": len(contract.properties),
            "automata_count": len(contract.automata),
            "observer_count": len(contract.observers),
            "has_model": model_xml is not None,
            "has_result": result_json is not None,
            "has_trace": trace_text is not None,
        },
        "reports": reports,
    }


def export_report_bundle(
    output_dir: str | Path,
    *,
    contract_json: dict,
    model_xml: str | None = None,
    queries: str | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    profile: dict | None = None,
    source_text: str | None = None,
) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    bundle = generate_report_bundle(
        contract_json=contract_json,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        trace_text=trace_text,
        profile=profile,
    )
    written: list[str] = []
    _write_json(output / "contract.json", contract_json, written)
    if model_xml is not None:
        _write_text(output / "model.xml", model_xml, written)
    if queries is not None:
        _write_text(output / "queries.q", queries, written)
    if result_json is not None:
        _write_json(output / "results.json", result_json, written)
    if trace_text is not None:
        _write_text(output / "trace.txt", trace_text, written)
    if profile is not None:
        _write_json(output / "profile.json", profile, written)
    if source_text is not None:
        _write_text(output / "source.tex", source_text, written)
    for name, text in bundle["reports"].items():
        _write_text(output / name, text, written)
    return {
        "output_dir": str(output),
        "files": written,
        "summary": bundle["summary"],
    }


def _property_report(
    contract: PhyContractModel,
    *,
    queries: str | None,
    result_json: dict | None,
) -> str:
    result_by_query = _result_by_query(result_json)
    lines = [
        "# PHY Property Report",
        "",
        "| Property | Category | Query | Result | Interpretation | Source |",
        "|---|---|---|---|---|---|",
    ]
    for item in contract.properties:
        result = result_by_query.get(item.query, "not_run")
        lines.append(
            "| "
            + " | ".join([
                _cell(item.name),
                _cell(item.category),
                _code_cell(item.query),
                _cell(result),
                _cell(item.interpretation),
                _cell(_source(item.provenance)),
            ])
            + " |"
        )
    if queries is not None:
        generated = [line.strip() for line in queries.splitlines() if line.strip()]
        lines.extend([
            "",
            f"Generated query lines: {len(generated)}.",
        ])
    return "\n".join(lines) + "\n"


def _traceability_matrix(contract: PhyContractModel) -> str:
    lines = [
        "# PHY Traceability Matrix",
        "",
        "| Article claim | IR entity | UPPAAL artifact | Source |",
        "|---|---|---|---|",
    ]
    lines.append("| `A_PHY = A_CH || A_SIG || A_BM || A_SQ || A_PH` | composition | `system ... A_PH ...` | invariants |")
    lines.append("| `A_SYS = A_PHY || A_ENV` | closed system | `ENV_CH, ENV_TARGET, ENV_MAC, ENV_NET` | invariants |")
    for item in contract.automata:
        lines.append(
            "| "
            + " | ".join([
                _cell(f"PHY automaton {item.name}"),
                _cell(item.name),
                _cell(f"Template_{item.name} / instance {item.name}"),
                _cell(_source(item.provenance)),
            ])
            + " |"
        )
    for item in contract.observers:
        lines.append(
            "| "
            + " | ".join([
                _cell(f"Bounded response {item.name}"),
                _cell(item.name),
                _cell(item.violation_query),
                _cell(_source(item.provenance)),
            ])
            + " |"
        )
    for item in contract.contracts:
        lines.append(
            "| "
            + " | ".join([
                _cell(f"Assume-guarantee for {item.automaton}"),
                _cell(item.automaton),
                _cell(f"{item.assumptions[0]} imply not {item.violation_location}"),
                _cell(_source(item.provenance)),
            ])
            + " |"
        )
    return "\n".join(lines) + "\n"


def _model_summary(
    contract: PhyContractModel,
    *,
    model_xml: str | None,
    queries: str | None,
) -> str:
    lines = [
        "# PHY Model Summary",
        "",
        "## IR",
        "",
        f"- PHY components: {', '.join(contract.phy_components)}",
        f"- ENV components: {', '.join(contract.env_components)}",
        f"- classes: {len(contract.classes)}",
        f"- clocks: {len(contract.clocks)}",
        f"- variables: {len(contract.variables)}",
        f"- channels: {len(contract.channels)}",
        f"- env specs: {len(contract.env)}",
        f"- observers: {len(contract.observers)}",
        f"- properties: {len(contract.properties)}",
        "",
        "## Generated UPPAAL",
        "",
    ]
    if model_xml:
        templates = _template_names(model_xml)
        validation = validate_generated_model(model_xml)
        lines.extend([
            f"- templates: {', '.join(templates)}",
            f"- generated model static validation: {'ok' if validation.ok else 'failed'}",
        ])
        if validation.errors:
            lines.append(f"- validation errors: {'; '.join(validation.errors)}")
    else:
        lines.append("- model XML: not provided")
    if queries is not None:
        query_lines = [line for line in queries.splitlines() if line.strip()]
        lines.append(f"- query lines: {len(query_lines)}")
    return "\n".join(lines) + "\n"


def _assume_guarantee_report(contract: PhyContractModel) -> str:
    lines = [
        "# Assume-Guarantee Report",
        "",
        "| Automaton | Assumptions | Guarantees | Violation | Source |",
        "|---|---|---|---|---|",
    ]
    for item in contract.contracts:
        lines.append(
            "| "
            + " | ".join([
                _cell(item.automaton),
                _cell(", ".join(item.assumptions)),
                _cell(", ".join(item.guarantees)),
                _cell(item.violation_location),
                _cell(_source(item.provenance)),
            ])
            + " |"
        )
    validation = validate_contract_ir(contract)
    lines.extend([
        "",
        f"Contract IR validation: {'ok' if validation.ok else 'failed'}.",
    ])
    if validation.errors:
        lines.append("Errors: " + "; ".join(validation.errors))
    return "\n".join(lines) + "\n"


def _alpha_profile_report(profile: dict, *, model_xml: str | None, contract: PhyContractModel) -> str:
    alpha_status = check_no_continuous_guards(model_xml).to_dict() if model_xml else {"ok": None, "errors": []}
    lines = [
        "# Alpha PHY Profile Report",
        "",
        f"- profile: {profile.get('name', 'custom')}",
        f"- boundary policy: {profile.get('boundary_policy', 'unknown')}",
        f"- class count: {len(contract.classes)}",
        f"- no continuous guards: {alpha_status.get('ok')}",
        "",
        "| Deadline | Value |",
        "|---|---|",
    ]
    for key, value in sorted((profile.get("deadlines") or {}).items()):
        lines.append(f"| `{_cell(str(key))}` | `{_cell(str(value))}` |")
    errors = alpha_status.get("errors") or []
    if errors:
        lines.extend(["", "Errors:"] + [f"- {item}" for item in errors])
    return "\n".join(lines) + "\n"


def _coverage_report(contract_json: dict) -> str:
    extractor = contract_json.get("extractor") or {}
    diagnostics = extractor.get("diagnostics") or []
    coverage = extractor.get("coverage") or {}
    found = coverage.get("found") or {}
    expected = coverage.get("expected") or {}
    lines = [
        "# Coverage Report",
        "",
        f"- extractor mode: {extractor.get('mode', 'unknown')}",
        f"- extractor ok: {extractor.get('ok')}",
        f"- source hash: {extractor.get('source_hash', 'unknown')}",
        "",
        "| Item | Found | Expected |",
        "|---|---:|---:|",
    ]
    for key in ("sections", "verbatim_blocks", "channels", "class_sets", "queries", "markers"):
        lines.append(f"| {key} | {found.get(key, 0)} | {expected.get(key, '')} |")
    if diagnostics:
        lines.extend(["", "Diagnostics:"] + [f"- {item}" for item in diagnostics])
    return "\n".join(lines) + "\n"


def _violations_report(result_json: dict) -> str:
    lines = [
        "# Violations",
        "",
        f"Overall status: `{result_json.get('status', 'unknown')}`.",
        "",
        "| Query | Status | Suggested fix |",
        "|---|---|---|",
    ]
    for item in result_json.get("query_results", []):
        if item.get("status") == "satisfied":
            continue
        formula = item.get("formula", "")
        lines.append(
            "| "
            + " | ".join([
                _code_cell(formula),
                _cell(item.get("status", "unknown")),
                _cell(_suggest_fix(formula)),
            ])
            + " |"
        )
    if len(lines) == 6:
        lines.append("| no failed parsed query | - | - |")
    return "\n".join(lines) + "\n"


def _publication_tables(contract: PhyContractModel) -> str:
    channel_counts: dict[str, int] = {}
    for item in contract.channels:
        channel_counts[item.kind] = channel_counts.get(item.kind, 0) + 1
    property_counts: dict[str, int] = {}
    for item in contract.properties:
        property_counts[item.category] = property_counts.get(item.category, 0) + 1
    lines = [
        "# Publication Tables",
        "",
        "## Composition",
        "",
        "| Layer | Components |",
        "|---|---|",
        f"| A_PHY | `{', '.join(contract.phy_components)}` |",
        f"| A_ENV | `{', '.join(contract.env_components)}` |",
        "",
        "## Model Size",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| finite classes | {len(contract.classes)} |",
        f"| variables | {len(contract.variables)} |",
        f"| clocks | {len(contract.clocks)} |",
        f"| channels | {len(contract.channels)} |",
        f"| PHY automata | {len(contract.automata)} |",
        f"| ENV specs | {len(contract.env)} |",
        f"| observers | {len(contract.observers)} |",
        f"| properties | {len(contract.properties)} |",
        "",
        "## Channel Kinds",
        "",
        "| Kind | Count |",
        "|---|---:|",
    ]
    for kind, count in sorted(channel_counts.items()):
        lines.append(f"| {kind} | {count} |")
    lines.extend([
        "",
        "## Property Categories",
        "",
        "| Category | Count |",
        "|---|---:|",
    ])
    for category, count in sorted(property_counts.items()):
        lines.append(f"| {category} | {count} |")
    return "\n".join(lines) + "\n"


def _properties_csv(contract: PhyContractModel, *, result_json: dict | None) -> str:
    result_by_query = _result_by_query(result_json)
    lines = ["name,category,query,result,source,line"]
    for item in contract.properties:
        provenance = item.provenance
        row = [
            item.name,
            item.category,
            item.query,
            result_by_query.get(item.query, "not_run"),
            provenance.source if provenance else "",
            "" if provenance is None or provenance.line is None else str(provenance.line),
        ]
        lines.append(",".join(_csv_cell(value) for value in row))
    return "\n".join(lines) + "\n"


def _trace_explanation_report(trace_text: str, *, result_json: dict | None) -> str:
    parsed = parse_trace_text(trace_text)
    lines = [
        "# Trace Explanation",
        "",
        f"- classification: `{parsed.get('classification', 'unknown')}`",
        f"- parsed ok: `{parsed.get('ok')}`",
    ]
    if result_json is not None:
        lines.append(f"- result status: `{result_json.get('status', 'unknown')}`")
    deadline = parsed.get("deadline_violation")
    if deadline:
        lines.extend([
            "",
            "## Deadline Violation",
            "",
            f"- observer: `{deadline.get('observer')}`",
            f"- domain: {deadline.get('domain')}",
            f"- trigger: `{deadline.get('trigger')}`",
            f"- trigger seen: `{deadline.get('trigger_seen')}`",
            f"- deadline: `{deadline.get('deadline')}`",
            f"- expected responses: `{', '.join(deadline.get('expected_responses', []))}`",
            f"- observed responses: `{', '.join(deadline.get('observed_responses', [])) or '-'}`",
        ])
    beam = parsed.get("beam_recovery") or {}
    if beam.get("triggered") or beam.get("observed_outcomes"):
        lines.extend([
            "",
            "## Beam Recovery",
            "",
            f"- triggered: `{beam.get('triggered')}`",
            f"- outcome status: `{beam.get('outcome_status')}`",
            f"- observed outcomes: `{', '.join(beam.get('observed_outcomes', [])) or '-'}`",
            f"- outcomes after violation: `{', '.join(beam.get('outcomes_after_violation', [])) or '-'}`",
        ])
    freshness = parsed.get("freshness") or {}
    if any(freshness.get(key) is not None for key in ("AoSClass", "AoS_BS", "AoS_CTRL")):
        lines.extend([
            "",
            "## Freshness",
            "",
            f"- AoSClass: `{freshness.get('AoSClass')}`",
            f"- AoS_BS: `{freshness.get('AoS_BS')}`",
            f"- AoS_CTRL: `{freshness.get('AoS_CTRL')}`",
            f"- AoS_CTRL - AoS_BS: `{freshness.get('AoS_CTRL_minus_AoS_BS')}`",
            f"- aos_ctrl_expired seen: `{freshness.get('aos_ctrl_expired_seen')}`",
            f"- sensing_report seen: `{freshness.get('sensing_report_seen')}`",
        ])
    for title, key in (
        ("Root-Cause Candidates", "root_cause_candidates"),
        ("Replay Hints", "replay_hints"),
        ("Modeling Errors", "modeling_errors"),
        ("Diagnostics", "diagnostics"),
    ):
        values = parsed.get(key) or []
        if values:
            lines.extend(["", f"## {title}", ""])
            lines.extend(f"- {item}" for item in values)
    lines.extend([
        "",
        "## Trace Facts",
        "",
        f"- locations: `{', '.join(parsed.get('locations_seen', [])) or '-'}`",
        f"- syncs: `{', '.join(parsed.get('syncs_seen', [])) or '-'}`",
        "",
        "```json",
        json.dumps(parsed.get("class_values", {}), ensure_ascii=False, indent=2),
        "```",
    ])
    return "\n".join(lines) + "\n"


def _contract_from_json(contract_json: dict) -> PhyContractModel:
    cleaned = dict(contract_json)
    cleaned.pop("extractor", None)
    return PhyContractModel.from_dict(cleaned)


def _result_by_query(result_json: dict | None) -> dict[str, str]:
    if not result_json:
        return {}
    return {
        item.get("formula", ""): item.get("status", "unknown")
        for item in result_json.get("query_results", [])
    }


def _template_names(model_xml: str) -> list[str]:
    try:
        root = ET.fromstring(model_xml)
    except ET.ParseError:
        return []
    names = []
    for template in root.findall("template"):
        element = template.find("name")
        if element is not None and element.text:
            names.append(element.text.strip())
    return names


def _source(provenance: Provenance | None) -> str:
    if provenance is None:
        return ""
    suffix = f":{provenance.line}" if provenance.line is not None else ""
    return f"{provenance.source}:{provenance.section}{suffix}"


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _code_cell(value: Any) -> str:
    return f"`{_cell(value)}`"


def _csv_cell(value: Any) -> str:
    text = str(value)
    if any(char in text for char in [",", '"', "\n"]):
        return '"' + text.replace('"', '""') + '"'
    return text


def _write_text(path: Path, text: str, written: list[str]) -> None:
    path.write_text(text, encoding="utf-8")
    written.append(str(path))


def _write_json(path: Path, data: Any, written: list[str]) -> None:
    path.write_text(json.dumps(_jsonable(data), ensure_ascii=False, indent=2), encoding="utf-8")
    written.append(str(path))


def _jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value


def _suggest_fix(formula: str) -> str:
    if "deadlock" in formula:
        return "Inspect closed A_SYS environment stubs and blocked handshakes."
    if "ObsBeamRecovery" in formula:
        return "Check recovery_start trigger, BeamRecover deadline, and outcome broadcasts."
    if "ObsFreshness" in formula:
        return "Check aos_ctrl_expired handling and FreshnessLimited sensing_report response."
    if "ObsSenseReport" in formula:
        return "Check sensing_degraded trigger and phy_kpi_report response before D_report."
    if "ContractViolation" in formula:
        return "Inspect corresponding ass_* and gar_* predicate implementation."
    if "BeamRecover" in formula:
        return "Check c_rec invariant and timeout guard c_rec == D_BM."
    return "Inspect the referenced template, guard, sync channel, and source provenance."
