from __future__ import annotations

import csv
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from .alpha import check_no_continuous_guards, default_profile
from .defaults import build_default_contract
from .ir import MacContractModel
from .layout import generate_layout_maps
from .validators import validate_contract_ir, validate_generated_model


def generate_report_bundle(*, contract_json: dict, model_xml: str | None = None, queries: str | None = None, result_json: dict | None = None, trace_text: str | None = None, profile: dict | None = None) -> dict:
    profile = profile or default_profile()
    contract = _contract_from_json(contract_json)
    reports = {
        "report.md": _report(contract, queries=queries, result_json=result_json),
        "traceability_matrix.md": _traceability(contract),
        "model_summary.md": _model_summary(contract, model_xml=model_xml, queries=queries),
        "alpha_profile_report.md": _alpha_report(profile, model_xml=model_xml),
        "coverage_report.md": _coverage(contract_json),
        "policy_report.md": _policy_report(contract),
        "properties.csv": _properties_csv(contract, result_json=result_json),
    }
    if model_xml is not None:
        reports.update(generate_layout_maps(contract_json, model_xml=model_xml))
    if result_json:
        reports["violations.md"] = _violations(result_json)
    if trace_text:
        reports["trace_explanation.md"] = _trace_explanation(trace_text, result_json=result_json)
    return {"summary": {"report_count": len(reports), "property_count": len(contract.properties), "automata_count": len(contract.automata), "has_model": model_xml is not None}, "reports": reports}


def export_report_bundle(output_dir: str | Path, *, contract_json: dict, model_xml: str | None = None, queries: str | None = None, result_json: dict | None = None, trace_text: str | None = None, profile: dict | None = None, source_text: str | None = None) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    bundle = generate_report_bundle(contract_json=contract_json, model_xml=model_xml, queries=queries, result_json=result_json, trace_text=trace_text, profile=profile)
    files = []
    _write_json(output / "contract.json", contract_json, files)
    if model_xml is not None:
        _write_text(output / "model.xml", model_xml, files)
    if queries is not None:
        _write_text(output / "queries.q", queries, files)
    if source_text is not None:
        _write_text(output / "source.tex", source_text, files)
    if profile is not None:
        _write_json(output / "profile.json", profile, files)
    if result_json is not None:
        _write_json(output / "results.json", result_json, files)
    if trace_text is not None:
        _write_text(output / "trace.txt", trace_text, files)
    for name, text in bundle["reports"].items():
        _write_text(output / name, text, files)
    return {"output_dir": str(output), "files": files, "summary": bundle["summary"]}


def _report(contract: MacContractModel, *, queries: str | None, result_json: dict | None) -> str:
    result_by_query = {item.get("formula"): item.get("status") for item in (result_json or {}).get("query_results", [])}
    lines = ["# MAC Property Report", "", "| Property | Category | Query | Result | Interpretation |", "|---|---|---|---|---|"]
    for item in contract.properties:
        lines.append(f"| `{item.name}` | `{item.category}` | `{item.query}` | {result_by_query.get(item.query, 'not_run')} | {item.interpretation} |")
    if queries:
        lines.append("")
        lines.append(f"Generated query lines: {len([line for line in queries.splitlines() if line.strip()])}.")
    return "\n".join(lines) + "\n"


def _traceability(contract: MacContractModel) -> str:
    lines = ["# MAC Traceability Matrix", "", "| Claim | IR | UPPAAL artifact |", "|---|---|---|"]
    lines.append("| `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG` | composition | `system A_SCH, A_Q, A_BUF, A_RSRC, A_MAC_AGG` |")
    lines.append("| `A_SYS_MAC = A_MAC || A_ENV_MAC` | closed system | `A_ENV_MAC` |")
    for item in contract.automata:
        lines.append(f"| MAC automaton `{item.name}` | locations/guarantees | template `{item.name}` |")
    for item in contract.observers:
        lines.append(f"| bounded response `{item.name}` | observer | `{item.violation_query}` |")
    return "\n".join(lines) + "\n"


def _model_summary(contract: MacContractModel, *, model_xml: str | None, queries: str | None) -> str:
    lines = ["# MAC Model Summary", "", f"- components: {', '.join(contract.mac_components)}", f"- env: {', '.join(contract.env_components)}", f"- classes: {len(contract.classes)}", f"- policies: {len(contract.policies)}", f"- properties: {len(contract.properties)}"]
    if model_xml:
        validation = validate_generated_model(model_xml, queries)
        lines.append(f"- generated validation: {'ok' if validation.ok else 'failed'}")
        if validation.errors:
            lines.append("- errors: " + "; ".join(validation.errors))
        lines.append("- templates: " + ", ".join(_template_names(model_xml)))
    return "\n".join(lines) + "\n"


def _alpha_report(profile: dict, *, model_xml: str | None) -> str:
    alpha = check_no_continuous_guards(model_xml or "").to_dict() if model_xml else {"ok": None, "errors": []}
    return "\n".join([
        "# Alpha MAC Profile Report",
        "",
        f"- profile: {profile.get('name', 'custom')}",
        f"- boundary policy: {profile.get('boundary_policy', 'unknown')}",
        f"- no continuous guards: {alpha.get('ok')}",
        f"- errors: {'; '.join(alpha.get('errors', [])) if alpha.get('errors') else 'none'}",
        "",
    ])


def _coverage(contract_json: dict) -> str:
    extractor = contract_json.get("extractor", {})
    return "\n".join([
        "# MAC Coverage Report",
        "",
        f"- extractor ok: {extractor.get('ok')}",
        f"- sections: {len(extractor.get('sections', []))}",
        f"- diagnostics: {'; '.join(extractor.get('diagnostics', [])) if extractor.get('diagnostics') else 'none'}",
        "",
    ])


def _policy_report(contract: MacContractModel) -> str:
    lines = ["# MAC Policy Report", "", "| Policy | Guard | Mode | Outcome |", "|---|---|---|---|"]
    for item in contract.policies:
        lines.append(f"| `{item.name}` | `{item.guard}` | `{item.mode}` | {item.outcome} |")
    validation = validate_contract_ir(contract)
    lines.append("")
    lines.append(f"Contract validation: {'ok' if validation.ok else 'failed'}.")
    return "\n".join(lines) + "\n"


def _properties_csv(contract: MacContractModel, *, result_json: dict | None) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["name", "category", "query", "interpretation"])
    for item in contract.properties:
        writer.writerow([item.name, item.category, item.query, item.interpretation])
    return out.getvalue()


def _violations(result_json: dict) -> str:
    failed = [item for item in result_json.get("query_results", []) if item.get("status") != "satisfied"]
    lines = ["# MAC Violations", ""]
    if not failed:
        lines.append("No failed query was parsed.")
    for item in failed:
        lines.append(f"- `{item.get('formula')}`: {item.get('status')}")
    return "\n".join(lines) + "\n"


def _trace_explanation(trace_text: str, *, result_json: dict | None) -> str:
    causes = []
    lower = trace_text.lower()
    if "waitphyack" in lower or "phy_ack" in lower:
        causes.append("missed or late PHY acknowledgement")
    if "queuecritical" in lower or "q_crit" in lower:
        causes.append("queue critical timeout")
    if "bufferoverflow" in lower or "b_overflow" in lower:
        causes.append("buffer overflow report path")
    if "resourceexhausted" in lower or "res_exhausted" in lower:
        causes.append("resource exhaustion path")
    if not causes:
        causes.append("unknown MAC trace cause")
    return "# MAC Trace Explanation\n\n" + "\n".join(f"- {item}" for item in causes) + "\n"


def _contract_from_json(contract_json: dict | None) -> MacContractModel:
    if not contract_json:
        return build_default_contract()
    cleaned = dict(contract_json)
    cleaned.pop("extractor", None)
    return MacContractModel.from_dict(cleaned)


def _template_names(model_xml: str) -> list[str]:
    root = ET.fromstring(model_xml)
    return [template.findtext("name") or "<unnamed>" for template in root.findall("template")]


def _write_text(path: Path, text: str, files: list[str]) -> None:
    path.write_text(text, encoding="utf-8")
    files.append(str(path))


def _write_json(path: Path, data: object, files: list[str]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(path))

