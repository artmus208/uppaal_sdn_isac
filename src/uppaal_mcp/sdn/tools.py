from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import UppaalConfig
from ..paths import local_path
from ..verifyta import VerifytaRunner
from .alpha import default_profile, list_classes, validate_threshold_policy, check_no_continuous_guards as alpha_check_no_continuous_guards
from .benchmarks import generate_benchmark_model, list_benchmarks, validate_all_benchmarks
from .defaults import SOURCE, build_default_contract
from .extractor import analyze_latex, extract_contract_model
from .generator import generate_uppaal_model
from .ir import SdnContractModel
from .layout import generate_diagram_artifacts, generate_layout_maps, validate_generated_layout
from .property_pack import export_property_pack as export_property_pack_files, generate_property_pack as build_property_pack
from .reports import export_report_bundle, generate_report_bundle
from .scenarios import generate_scenario_model, list_scenarios
from .trace import explain_counterexample
from .validators import validate_contract_ir, validate_generated_model


def extract_contract(*, tex_text: str | None = None, tex_path: str | None = None) -> dict:
    text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    if text is not None:
        return extract_contract_model(text, source_name=_source_name(tex_path))
    contract = build_default_contract().to_dict()
    contract["extractor"] = {
        "ok": False,
        "mode": "fixture-without-tex",
        "source_name": SOURCE,
        "source_hash": hashlib.sha256(SOURCE.encode("utf-8")).hexdigest(),
        "diagnostics": ["No SDN LaTeX source was provided or found; returned canonical SDN fixture."],
    }
    return contract


def validate_contract(contract_json: dict | None = None) -> dict:
    return validate_contract_ir(_contract_from_json(contract_json)).to_dict()


def generate_uppaal_from_contract(
    *,
    contract_json: dict | None = None,
    tex_text: str | None = None,
    tex_path: str | None = None,
    profile: dict | None = None,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative_scenarios: bool = False,
    mode: str | None = None,
    layout: str | None = None,
) -> dict:
    contract = _contract_from_json(contract_json) if contract_json else _contract_from_json(extract_contract(tex_text=tex_text, tex_path=tex_path))
    generated = generate_uppaal_model(
        contract,
        profile=profile or default_profile(),
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative_scenarios=include_negative_scenarios,
        mode=mode,
        layout=layout,
    )
    semantic = validate_generated_model(
        generated.model_xml,
        generated.queries,
        require_observers="ObsRuleMiss" in generated.model_xml,
        require_environment=generated.system_mode != "open",
        allow_optional_sec=generated.generation_mode == "with_optional_sec",
    )
    data = generated.to_dict()
    data["semantic_validation"] = semantic.to_dict()
    data["alpha_validation"] = alpha_check_no_continuous_guards(generated.model_xml).to_dict()
    return data


def validate_layout(model_xml: str | None = None, contract_json: dict | None = None) -> dict:
    if model_xml is None:
        contract = _contract_from_json(contract_json)
        model_xml = generate_uppaal_model(contract).model_xml
    return validate_generated_layout(model_xml).to_dict()


def generate_diagram(*, model_xml: str | None = None, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, profile: dict | None = None, layout: str | None = None) -> dict:
    if model_xml is None:
        generated = generate_uppaal_from_contract(contract_json=contract_json, tex_text=tex_text, tex_path=tex_path, profile=profile, layout=layout)
        model_xml = generated["model_xml"]
        contract_json = generated["contract"]
    maps = generate_layout_maps(contract_json or build_default_contract().to_dict(), model_xml=model_xml, layout=layout)
    return {"layout_validation": validate_generated_layout(model_xml).to_dict(), **maps, **generate_diagram_artifacts(model_xml)}


def export_diagram(*, output_dir: str, model_xml: str | None = None, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, profile: dict | None = None, layout: str | None = None) -> dict:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    data = generate_diagram(model_xml=model_xml, contract_json=contract_json, tex_text=tex_text, tex_path=tex_path, profile=profile, layout=layout)
    files = []
    for name in ("model_map.md", "template_map.md", "channels_map.md", "policy_map.md", "interface_map.md", "model.dot", "model.svg"):
        (output / name).write_text(data[name], encoding="utf-8")
        files.append(str(output / name))
    (output / "layout_validation.json").write_text(json.dumps(data["layout_validation"], ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(output / "layout_validation.json"))
    return {"output_dir": str(output), "files": files, "layout_validation": data["layout_validation"]}


def generate_property_pack(*, contract_json: dict | None = None, model_xml: str | None = None, profile: dict | None = None, include_observers: bool = True, debug_counters: bool = True, include_negative: bool = False) -> dict:
    return build_property_pack(_contract_from_json(contract_json), model_xml=model_xml, include_observers=include_observers, debug_counters=debug_counters, include_negative=include_negative)


def export_property_pack(*, output_dir: str, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, model_xml: str | None = None, profile: dict | None = None, include_observers: bool = True, debug_counters: bool = True, include_negative: bool = False) -> dict:
    if contract_json is None:
        contract_json = extract_contract(tex_text=tex_text, tex_path=tex_path)
    return export_property_pack_files(output_dir, _contract_from_json(contract_json), model_xml=model_xml, include_observers=include_observers, debug_counters=debug_counters, include_negative=include_negative)


def generate_report(*, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, model_xml: str | None = None, queries: str | None = None, result_json: dict | None = None, trace_text: str | None = None, profile: dict | None = None) -> dict:
    prepared = _prepare_report_inputs(contract_json=contract_json, tex_text=tex_text, tex_path=tex_path, model_xml=model_xml, queries=queries, profile=profile)
    return generate_report_bundle(contract_json=prepared["contract_json"], model_xml=prepared["model_xml"], queries=prepared["queries"], result_json=result_json, trace_text=trace_text, profile=prepared["profile"])


def export_report(*, output_dir: str, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, model_xml: str | None = None, queries: str | None = None, result_json: dict | None = None, trace_text: str | None = None, profile: dict | None = None) -> dict:
    prepared = _prepare_report_inputs(contract_json=contract_json, tex_text=tex_text, tex_path=tex_path, model_xml=model_xml, queries=queries, profile=profile)
    return export_report_bundle(output_dir, contract_json=prepared["contract_json"], model_xml=prepared["model_xml"], queries=prepared["queries"], result_json=result_json, trace_text=trace_text, profile=prepared["profile"], source_text=prepared["source_text"])


def export_run_artifacts(*, output_root: str, contract_json: dict | None = None, tex_text: str | None = None, tex_path: str | None = None, model_xml: str | None = None, queries: str | None = None, result_json: dict | None = None, trace_text: str | None = None, profile: dict | None = None, verifyta_version: str | None = None, verifyta_command: list[str] | None = None, options: list[str] | None = None, force: bool = False) -> dict:
    prepared = _prepare_report_inputs(contract_json=contract_json, tex_text=tex_text, tex_path=tex_path, model_xml=model_xml, queries=queries, profile=profile)
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    cache_input = json.dumps({
        "source": prepared["source_text"],
        "contract": prepared["contract_json"],
        "model": prepared["model_xml"],
        "queries": prepared["queries"],
        "profile": prepared["profile"],
        "verifyta": verifyta_version,
        "options": options or [],
    }, sort_keys=True, ensure_ascii=False)
    run_id = hashlib.sha256(cache_input.encode("utf-8")).hexdigest()[:16]
    artifact_dir = root / "artifacts" / run_id
    if artifact_dir.exists() and not force:
        return {"cache_hit": True, "artifact_dir": str(artifact_dir), "run_id": run_id}
    artifact_dir.mkdir(parents=True, exist_ok=True)
    files = []
    _write_text(artifact_dir / "source.tex", prepared["source_text"] or "", files)
    _write_json(artifact_dir / "contract.json", prepared["contract_json"], files)
    _write_text(artifact_dir / "model.xml", prepared["model_xml"], files)
    _write_text(artifact_dir / "queries.q", prepared["queries"], files)
    _write_json(artifact_dir / "profile.json", prepared["profile"], files)
    if result_json is not None:
        _write_json(artifact_dir / "results.json", result_json, files)
    if trace_text is not None:
        _write_text(artifact_dir / "trace.txt", trace_text, files)
    metadata = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "layer_id": "sdn",
        "verifyta_version": verifyta_version or "unknown",
        "verifyta_command": verifyta_command or [],
        "cache_key": run_id,
    }
    _write_json(artifact_dir / "run_metadata.json", metadata, files)
    report = export_report(output_dir=str(artifact_dir), contract_json=prepared["contract_json"], tex_text=prepared["source_text"], model_xml=prepared["model_xml"], queries=prepared["queries"], result_json=result_json, trace_text=trace_text, profile=prepared["profile"])
    files.extend(path for path in report["files"] if path not in files)
    return {"cache_hit": False, "artifact_dir": str(artifact_dir), "run_id": run_id, "files": files, "metadata": metadata}


def verify_contract(*, tex_text: str | None = None, tex_path: str | None = None, contract_json: dict | None = None, profile: dict | None = None, mode: str | None = None, include_observers: bool = True, timeout_sec: float | None = None, artifact_root: str | None = None, force: bool = False) -> dict:
    source_text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    generated = generate_uppaal_from_contract(contract_json=contract_json, tex_text=source_text if contract_json is None else None, profile=profile, include_observers=include_observers, mode=mode)
    runner = VerifytaRunner(UppaalConfig.from_env())
    result = runner.verify(model_xml=generated["model_xml"], queries=generated["queries"], timeout_sec=timeout_sec, keep_artifacts=True).to_dict()
    explanation = explain_counterexample(result, contract_json=generated["contract"])
    artifacts = export_run_artifacts(output_root=artifact_root or str(runner.config.workspace / "sdn_runs"), contract_json=generated["contract"], tex_text=source_text, model_xml=generated["model_xml"], queries=generated["queries"], result_json=result, profile=generated["profile"], force=force)
    return {"status": result["status"], "result": result, "explanation": explanation, "semantic_validation": generated["semantic_validation"], "alpha_validation": generated["alpha_validation"], "profile": generated["profile"], "artifacts": artifacts}


def verify_property_pack(*, model_xml: str | None = None, model_path: str | None = None, queries: str | None = None, query_path: str | None = None, explain: bool = True, timeout_sec: float | None = None, static_only: bool = False) -> dict:
    runner = VerifytaRunner(UppaalConfig.from_env())
    static_validation = runner.validate(model_xml=model_xml, model_path=model_path, queries=queries, query_path=query_path)
    if not static_validation.get("ok"):
        result = {"status": "static_error", "query_results": [], "validation": static_validation}
        return {"status": "static_error", "static_validation": static_validation, "result": result, "explanation": explain_counterexample(result) if explain else None}
    if static_only:
        result = {"status": "validated", "query_results": [], "validation": static_validation}
        return {"status": "validated", "static_validation": static_validation, "result": result, "explanation": None}
    result = runner.verify(model_xml=model_xml, model_path=model_path, queries=queries, query_path=query_path, timeout_sec=timeout_sec, keep_artifacts=True).to_dict()
    return {"status": result["status"], "static_validation": static_validation, "result": result, "explanation": explain_counterexample(result) if explain else None}


def check_alpha_profile(profile_json: dict | None = None) -> dict:
    return validate_threshold_policy(profile_json or default_profile()).to_dict()


def check_channel_semantics(model_xml: str | None = None, contract_json: dict | None = None) -> dict:
    reports = []
    if contract_json is not None:
        reports.append(validate_contract_ir(_contract_from_json(contract_json)).to_dict())
    if model_xml is not None:
        reports.append(validate_generated_model(model_xml).to_dict())
    if not reports:
        generated = generate_uppaal_model()
        reports.append(validate_generated_model(generated.model_xml, generated.queries).to_dict())
    errors = [error for report in reports for error in report.get("errors", []) if "broadcast" in error or "handshake" in error or "chan" in error]
    return {"ok": not errors, "errors": errors, "reports": reports}


def sdn_list_profiles() -> list[dict]:
    return [default_profile("default"), default_profile("conservative_safety"), default_profile("stress")]


def sdn_get_profile(name: str) -> dict:
    return default_profile(name)


def sdn_list_scenarios() -> list[dict]:
    return list_scenarios()


def sdn_get_scenario(name: str, profile: dict | None = None) -> dict:
    return generate_scenario_model(name, profile=profile)


def sdn_verify_scenario(name: str, profile: dict | None = None, timeout_sec: float | None = None) -> dict:
    scenario = generate_scenario_model(name, profile=profile)
    runner = VerifytaRunner(UppaalConfig.from_env())
    result = runner.verify(model_xml=scenario["model_xml"], queries=scenario["queries"], timeout_sec=timeout_sec if timeout_sec is not None else scenario["timeout_sec"], keep_artifacts=True).to_dict()
    return {"name": name, "expected_status": scenario["expected_status"], "status": result["status"], "ok": result["status"] == scenario["expected_status"], "result": result, "explanation": explain_counterexample(result)}


def sdn_verify_all_scenarios(profile: dict | None = None, timeout_sec: float | None = None) -> dict:
    results = [sdn_verify_scenario(item["name"], profile=profile, timeout_sec=timeout_sec) for item in list_scenarios()]
    return {"ok": all(item["ok"] for item in results), "results": results}


def sdn_list_benchmarks() -> list[dict]:
    return list_benchmarks()


def sdn_get_benchmark(name: str, profile: dict | None = None) -> dict:
    return generate_benchmark_model(name, profile=profile)


def sdn_validate_benchmarks(profile: dict | None = None) -> dict:
    return validate_all_benchmarks(profile=profile)


def sdn_list_classes() -> dict[str, list[str]]:
    return list_classes()


def _contract_from_json(contract_json: dict | None) -> SdnContractModel:
    if not contract_json:
        return build_default_contract()
    cleaned = dict(contract_json)
    cleaned.pop("extractor", None)
    return SdnContractModel.from_dict(cleaned)


def _load_tex(*, tex_text: str | None, tex_path: str | None) -> str | None:
    if tex_text is not None and tex_path is not None:
        raise ValueError("Pass either tex_text or tex_path, not both.")
    if tex_text is not None:
        return tex_text
    if tex_path is not None:
        return local_path(tex_path).read_text(encoding="utf-8")
    default_path = Path.cwd() / SOURCE
    if default_path.exists():
        return default_path.read_text(encoding="utf-8")
    return None


def _source_name(tex_path: str | None) -> str:
    return SOURCE if tex_path is None else local_path(tex_path).name


def _prepare_report_inputs(*, contract_json: dict | None, tex_text: str | None, tex_path: str | None, model_xml: str | None, queries: str | None, profile: dict | None) -> dict:
    source_text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    if contract_json is None:
        if source_text is not None:
            contract_json = extract_contract_model(source_text, source_name=_source_name(tex_path))
        else:
            contract_json = extract_contract()
    elif source_text is not None and "extractor" not in contract_json:
        contract_json = dict(contract_json)
        contract_json["extractor"] = analyze_latex(source_text, source_name=_source_name(tex_path)).to_dict()
    profile = profile or default_profile()
    if model_xml is None or queries is None:
        generated = generate_uppaal_from_contract(contract_json=contract_json, profile=profile)
        model_xml = model_xml or generated["model_xml"]
        queries = queries or generated["queries"]
    return {"source_text": source_text, "contract_json": contract_json, "model_xml": model_xml, "queries": queries, "profile": profile}


def _write_text(path: Path, text: str, files: list[str]) -> None:
    path.write_text(text, encoding="utf-8")
    files.append(str(path))


def _write_json(path: Path, data: object, files: list[str]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    files.append(str(path))
