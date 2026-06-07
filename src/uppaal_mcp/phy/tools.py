from __future__ import annotations

import hashlib
from pathlib import Path

from ..config import UppaalConfig
from ..paths import local_path
from ..verifyta import VerifytaRunner
from .alpha import (
    check_no_continuous_guards as alpha_check_no_continuous_guards,
    classify_sample,
    default_profile,
    list_classes,
    validate_threshold_policy,
)
from .artifacts import (
    build_run_metadata,
    export_run_artifacts as export_run_artifact_files,
)
from .benchmarks import generate_benchmark_model, list_benchmarks, validate_all_benchmarks
from .defaults import SOURCE, build_default_contract
from .extractor import analyze_latex, extract_contract_model
from .generator import generate_uppaal_model
from .ir import PhyContractModel
from .property_pack import (
    export_property_pack as export_property_pack_files,
    generate_property_pack as build_property_pack,
)
from .reports import export_report_bundle, generate_report_bundle
from .scenarios import generate_scenario_model, list_scenarios
from .trace import classify_failed_query, normalize_verifyta_output, parse_trace_text
from .validators import validate_contract_ir, validate_generated_model


def extract_contract(
    *,
    tex_text: str | None = None,
    tex_path: str | None = None,
) -> dict:
    text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    if text is not None:
        return extract_contract_model(text, source_name=_source_name(tex_path))
    contract = build_default_contract()
    data = contract.to_dict()
    data["extractor"] = {
        "ok": False,
        "mode": "fixture-without-tex",
        "source_name": SOURCE,
        "source_hash": hashlib.sha256(SOURCE.encode("utf-8")).hexdigest(),
        "diagnostics": ["No LaTeX source was provided or found; returned canonical article fixture only."],
        "note": "No source evidence is available for this extraction result.",
    }
    return data


def validate_contract(contract_json: dict | None = None) -> dict:
    contract = _contract_from_json(contract_json)
    return validate_contract_ir(contract).to_dict()


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
) -> dict:
    contract = _contract_from_json(contract_json) if contract_json else _contract_from_json(extract_contract(tex_text=tex_text, tex_path=tex_path))
    generated = generate_uppaal_model(
        contract,
        profile=profile or default_profile(),
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative_scenarios=include_negative_scenarios,
        mode=mode,
    )
    semantic = validate_generated_model(
        generated.model_xml,
        generated.queries,
        require_observers="ObsSenseReport" in generated.model_xml,
        require_environment=generated.system_mode == "closed",
    )
    data = generated.to_dict()
    data["semantic_validation"] = semantic.to_dict()
    data["alpha_validation"] = alpha_check_no_continuous_guards(generated.model_xml).to_dict()
    return data


def generate_property_pack(
    *,
    contract_json: dict | None = None,
    model_xml: str | None = None,
    profile: dict | None = None,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative: bool = False,
) -> dict:
    contract = _contract_from_json(contract_json)
    return build_property_pack(
        contract,
        model_xml=model_xml,
        profile=profile,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative=include_negative,
    )


def export_property_pack(
    *,
    output_dir: str,
    contract_json: dict | None = None,
    tex_text: str | None = None,
    tex_path: str | None = None,
    model_xml: str | None = None,
    profile: dict | None = None,
    include_observers: bool = True,
    debug_counters: bool = True,
    include_negative: bool = False,
) -> dict:
    if contract_json is None:
        contract_json = extract_contract(tex_text=tex_text, tex_path=tex_path)
    contract = _contract_from_json(contract_json)
    return export_property_pack_files(
        output_dir,
        contract,
        model_xml=model_xml,
        profile=profile,
        include_observers=include_observers,
        debug_counters=debug_counters,
        include_negative=include_negative,
    )


def check_no_continuous_guards(
    model_xml: str | None = None,
    contract_json: dict | None = None,
) -> object:
    if model_xml is None and contract_json is not None:
        contract = _contract_from_json(contract_json)
        model_xml = generate_uppaal_model(contract, include_observers=True).model_xml
    return alpha_check_no_continuous_guards(model_xml or "")


def check_channel_semantics(
    model_xml: str | None = None,
    contract_json: dict | None = None,
) -> dict:
    reports = []
    if contract_json is not None:
        reports.append(validate_contract_ir(_contract_from_json(contract_json)).to_dict())
    if model_xml is not None:
        reports.append(validate_generated_model(model_xml).to_dict())
    if not reports:
        generated = generate_uppaal_model(include_observers=True)
        reports.append(validate_contract_ir(PhyContractModel.from_dict(generated.contract)).to_dict())
        reports.append(validate_generated_model(generated.model_xml).to_dict())
    errors = [
        error
        for report in reports
        for error in report.get("errors", [])
        if _is_channel_semantics_error(error)
    ]
    warnings = [
        warning
        for report in reports
        for warning in report.get("warnings", [])
    ]
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "reports": reports,
    }


def generate_report(
    *,
    contract_json: dict | None = None,
    tex_text: str | None = None,
    tex_path: str | None = None,
    model_xml: str | None = None,
    queries: str | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    profile: dict | None = None,
) -> dict:
    prepared = _prepare_report_inputs(
        contract_json=contract_json,
        tex_text=tex_text,
        tex_path=tex_path,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        trace_text=trace_text,
        profile=profile,
    )
    return generate_report_bundle(
        contract_json=prepared["contract_json"],
        model_xml=prepared["model_xml"],
        queries=prepared["queries"],
        result_json=prepared["result_json"],
        trace_text=trace_text,
        profile=prepared["profile"],
    )


def export_report(
    *,
    output_dir: str,
    contract_json: dict | None = None,
    tex_text: str | None = None,
    tex_path: str | None = None,
    model_xml: str | None = None,
    queries: str | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    profile: dict | None = None,
) -> dict:
    prepared = _prepare_report_inputs(
        contract_json=contract_json,
        tex_text=tex_text,
        tex_path=tex_path,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        trace_text=trace_text,
        profile=profile,
    )
    return export_report_bundle(
        output_dir,
        contract_json=prepared["contract_json"],
        model_xml=prepared["model_xml"],
        queries=prepared["queries"],
        result_json=prepared["result_json"],
        trace_text=trace_text,
        profile=prepared["profile"],
        source_text=prepared["source_text"],
    )


def export_run_artifacts(
    *,
    output_root: str,
    contract_json: dict | None = None,
    tex_text: str | None = None,
    tex_path: str | None = None,
    model_xml: str | None = None,
    queries: str | None = None,
    result_json: dict | None = None,
    trace_text: str | None = None,
    profile: dict | None = None,
    verifyta_version: str | None = None,
    verifyta_command: list[str] | None = None,
    options: list[str] | None = None,
    force: bool = False,
) -> dict:
    prepared = _prepare_report_inputs(
        contract_json=contract_json,
        tex_text=tex_text,
        tex_path=tex_path,
        model_xml=model_xml,
        queries=queries,
        result_json=result_json,
        profile=profile,
    )
    return export_run_artifact_files(
        output_root,
        source_text=prepared["source_text"],
        contract_json=prepared["contract_json"],
        model_xml=prepared["model_xml"],
        queries=prepared["queries"],
        profile=prepared["profile"],
        result_json=result_json,
        trace_text=trace_text,
        verifyta_version=verifyta_version,
        verifyta_command=verifyta_command,
        options=options,
        force=force,
    )


def verify_contract(
    *,
    tex_text: str | None = None,
    tex_path: str | None = None,
    contract_json: dict | None = None,
    profile: dict | None = None,
    mode: str | None = None,
    include_observers: bool = True,
    timeout_sec: float | None = None,
    artifact_root: str | None = None,
    force: bool = False,
) -> dict:
    source_text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    include_observers = _include_observers_from_mode(mode, include_observers)
    generator_mode = _generator_mode_from_verify_mode(mode)
    generated = generate_uppaal_from_contract(
        contract_json=contract_json,
        tex_text=source_text if contract_json is None else None,
        tex_path=None,
        profile=profile,
        include_observers=include_observers,
        mode=generator_mode,
    )
    runner = VerifytaRunner(UppaalConfig.from_env())
    version = _verifyta_version_banner(runner)
    if include_observers:
        base_model = generate_uppaal_from_contract(
            contract_json=generated["contract"],
            profile=generated["profile"],
            include_observers=False,
            mode=generator_mode,
        )
        base_queries = [
            query
            for query in generated["queries"].splitlines()
            if query.strip() and "Obs" not in query
        ]
        observer_queries = [
            query
            for query in generated["queries"].splitlines()
            if query.strip() and "Obs" in query
        ]
        runs = _verify_queries_one_by_one(
            runner,
            model_xml=base_model["model_xml"],
            queries=base_queries,
            timeout_sec=timeout_sec,
        )
        result = _combine_results(runs)
        if observer_queries:
            scenario_results = phy_verify_all_scenarios(
                profile=generated["profile"],
                timeout_sec=timeout_sec,
            )
            result["observer_verification_mode"] = "compact_scenarios"
            result["observer_queries"] = observer_queries
            result["observer_scenario_results"] = scenario_results
            if result["status"] == "satisfied" and not scenario_results["ok"]:
                result["status"] = "not_satisfied"
    else:
        runs = _verify_queries_one_by_one(
            runner,
            model_xml=generated["model_xml"],
            queries=[query for query in generated["queries"].splitlines() if query.strip()],
            timeout_sec=timeout_sec,
        )
        result = _combine_results(runs)
    explanation = explain_counterexample(result_json=result, contract_json=generated["contract"])
    run_metadata = build_run_metadata(
        source_text=source_text,
        contract_json=generated["contract"],
        model_xml=generated["model_xml"],
        queries=generated["queries"],
        profile=generated["profile"],
        result_json=result,
        verifyta_version=version,
        verifyta_command=_representative_command(result),
    )
    artifacts = export_run_artifacts(
        output_root=artifact_root or str(runner.config.workspace / "phy_runs"),
        contract_json=generated["contract"],
        tex_text=source_text,
        model_xml=generated["model_xml"],
        queries=generated["queries"],
        result_json=result,
        profile=generated["profile"],
        verifyta_version=version,
        verifyta_command=_representative_command(result),
        force=force,
    )
    return {
        "status": result["status"],
        "result": result,
        "explanation": explanation,
        "semantic_validation": generated["semantic_validation"],
        "alpha_validation": generated["alpha_validation"],
        "profile": generated["profile"],
        "run_metadata": run_metadata,
        "artifacts": artifacts,
    }


def verify_property_pack(
    *,
    model_xml: str | None = None,
    model_path: str | None = None,
    queries: str | None = None,
    query_path: str | None = None,
    explain: bool = True,
    timeout_sec: float | None = None,
    static_only: bool = False,
) -> dict:
    runner = VerifytaRunner(UppaalConfig.from_env())
    static_validation = runner.validate(
        model_xml=model_xml,
        model_path=model_path,
        queries=queries,
        query_path=query_path,
    )
    if not static_validation.get("ok"):
        result = {
            "status": "static_error",
            "query_results": [],
            "validation": static_validation,
        }
        return {
            "status": "static_error",
            "static_validation": static_validation,
            "result": result,
            "explanation": explain_counterexample(result_json=result) if explain else None,
        }
    if static_only:
        result = {
            "status": "validated",
            "query_results": [],
            "validation": static_validation,
        }
        return {
            "status": "validated",
            "static_validation": static_validation,
            "result": result,
            "explanation": None,
        }
    result = runner.verify(
        model_xml=model_xml,
        model_path=model_path,
        queries=queries,
        query_path=query_path,
        timeout_sec=timeout_sec,
        keep_artifacts=True,
    ).to_dict()
    return {
        "status": result["status"],
        "static_validation": static_validation,
        "result": result,
        "explanation": explain_counterexample(result_json=result) if explain else None,
    }


def explain_counterexample(
    *,
    result_json: dict,
    trace_text: str | None = None,
    contract_json: dict | None = None,
) -> dict:
    status = result_json.get("status", "unknown")
    failed = [
        item
        for item in result_json.get("query_results", [])
        if item.get("status") != "satisfied"
    ]
    if status in {"satisfied", "partial_satisfied"}:
        return {
            "status": status,
            "summary": "All executed PHY contract properties parsed from verifyta output were satisfied.",
            "counterexample_type": None,
            "counterexample_classification": None,
            "failed_queries": [],
            "observer_verification_mode": result_json.get("observer_verification_mode"),
            "observer_scenario_results": result_json.get("observer_scenario_results"),
        }
    classification = "unknown"
    domain_classification = "unknown"
    reasons: list[str] = []
    classified_failures = []
    for item in failed:
        formula = item.get("formula") or ""
        query_classification = classify_failed_query(formula)
        classified_failures.append({**item, **query_classification})
        if domain_classification == "unknown":
            domain_classification = query_classification.get("counterexample_classification", "unknown")
        if "Obs" in formula and "Violation" in formula:
            classification = "deadline_violation"
            reasons.append(f"Observer violation candidate: {formula}")
        elif "deadlock" in formula:
            classification = "modeling_error"
            reasons.append("Deadlock freedom failed in closed A_SYS.")
        elif "ContractViolation" in formula:
            classification = "environment_assumption_violation"
            reasons.append(f"Contract violation query failed: {formula}")
    parsed_trace = parse_trace_text(trace_text) if trace_text else None
    if parsed_trace:
        reasons.extend(parsed_trace.get("root_cause_candidates", []))
        trace_classification = parsed_trace.get("classification")
        if trace_classification and trace_classification != "unknown":
            domain_classification = trace_classification
    return {
        "status": status,
        "summary": "At least one generated PHY contract property was not satisfied or was not classified as satisfied.",
        "counterexample_type": classification,
        "counterexample_classification": domain_classification,
        "failed_queries": classified_failures,
        "reasons": reasons,
        "artifact_dir": result_json.get("artifact_dir"),
        "normalized_output": normalize_verifyta_output(result_json),
        "parsed_trace": parsed_trace,
    }


def list_profiles() -> list[dict]:
    return [default_profile("default"), default_profile("conservative_safety"), default_profile("stress")]


def get_profile(name: str) -> dict:
    return default_profile(name)


def check_alpha_profile(profile_json: dict | None = None) -> dict:
    return validate_threshold_policy(profile_json or default_profile()).to_dict()


def alpha_classify_sample(meas: dict, cfg: dict | None = None, profile: dict | None = None) -> dict:
    return classify_sample(meas, cfg, profile)


def alpha_list_classes() -> dict[str, list[str]]:
    return list_classes()


def phy_list_scenarios() -> list[dict]:
    return list_scenarios()


def phy_get_scenario(name: str, profile: dict | None = None) -> dict:
    return generate_scenario_model(name, profile=profile)


def phy_verify_scenario(name: str, profile: dict | None = None, timeout_sec: float | None = None) -> dict:
    scenario = generate_scenario_model(name, profile=profile)
    runner = VerifytaRunner(UppaalConfig.from_env())
    result = runner.verify(
        model_xml=scenario["model_xml"],
        queries=scenario["queries"],
        timeout_sec=timeout_sec if timeout_sec is not None else scenario.get("timeout_sec"),
        keep_artifacts=True,
    ).to_dict()
    return {
        "name": name,
        "expected_status": scenario["expected_status"],
        "status": result["status"],
        "ok": result["status"] == scenario["expected_status"],
        "result": result,
        "explanation": explain_counterexample(result_json=result),
    }


def phy_verify_all_scenarios(profile: dict | None = None, timeout_sec: float | None = None) -> dict:
    results = [
        phy_verify_scenario(item["name"], profile=profile, timeout_sec=timeout_sec)
        for item in list_scenarios()
    ]
    return {
        "ok": all(item["ok"] for item in results),
        "results": results,
    }


def phy_list_benchmarks() -> list[dict]:
    return list_benchmarks()


def phy_get_benchmark(name: str, profile: dict | None = None) -> dict:
    return generate_benchmark_model(name, profile=profile)


def phy_validate_benchmarks(profile: dict | None = None) -> dict:
    return validate_all_benchmarks(profile=profile)


def _contract_from_json(contract_json: dict | None) -> PhyContractModel:
    if not contract_json:
        return build_default_contract()
    cleaned = dict(contract_json)
    cleaned.pop("extractor", None)
    return PhyContractModel.from_dict(cleaned)


def _queries_without(queries: str, excluded: set[str]) -> str:
    lines = [line for line in queries.splitlines() if line.strip() and line.strip() not in excluded]
    return "\n".join(lines) + "\n"


def _combine_results(results: list[dict]) -> dict:
    if not results:
        return {"status": "unknown", "query_results": [], "runs": []}
    statuses = [item.get("status", "unknown") for item in results]
    if any(status == "error" for status in statuses):
        status = "error"
    elif any(status == "timeout" for status in statuses):
        status = "timeout"
    elif any(status == "not_satisfied" for status in statuses):
        status = "not_satisfied"
    elif statuses and all(status == "satisfied" for status in statuses):
        status = "satisfied"
    else:
        status = "mixed"
    combined = dict(results[-1])
    combined["status"] = status
    combined["runs"] = results
    combined["query_results"] = [
        query
        for item in results
        for query in item.get("query_results", [])
    ]
    combined["stdout"] = "\n".join(item.get("stdout", "") for item in results)
    combined["stderr"] = "\n".join(item.get("stderr", "") for item in results if item.get("stderr"))
    combined["artifact_dir"] = ";".join(
        item.get("artifact_dir", "") for item in results if item.get("artifact_dir")
    )
    return combined


def _verify_queries_one_by_one(
    runner: VerifytaRunner,
    *,
    model_xml: str,
    queries: list[str],
    timeout_sec: float | None,
) -> list[dict]:
    runs: list[dict] = []
    for query in queries:
        per_query_timeout = timeout_sec
        if query.strip() == "A[] not deadlock":
            per_query_timeout = max(float(timeout_sec or 0), 20.0)
        result = runner.verify(
            model_xml=model_xml,
            queries=query + "\n",
            timeout_sec=per_query_timeout,
            keep_artifacts=True,
        ).to_dict()
        runs.append(result)
        if result.get("status") in {"error", "timeout"}:
            # Keep going for independent properties only if the timeout was user-provided.
            # A hard verifyta syntax error usually repeats for every property.
            if result.get("status") == "error":
                break
    return runs


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
    if tex_path is None:
        return SOURCE
    return local_path(tex_path).name


def _prepare_report_inputs(
    *,
    contract_json: dict | None,
    tex_text: str | None,
    tex_path: str | None,
    model_xml: str | None,
    queries: str | None,
    result_json: dict | None,
    profile: dict | None,
    trace_text: str | None = None,
) -> dict:
    source_text = _load_tex(tex_text=tex_text, tex_path=tex_path)
    if contract_json is None:
        if source_text is not None:
            contract_json = extract_contract_model(source_text, source_name=_source_name(tex_path))
        else:
            contract_json = extract_contract()
    elif source_text is not None and "extractor" not in contract_json:
        contract_json = dict(contract_json)
        contract_json["extractor"] = analyze_latex(source_text, source_name=_source_name(tex_path)).to_dict()
    if model_xml is None or queries is None:
        generated = generate_uppaal_from_contract(
            contract_json=contract_json,
            profile=profile or default_profile(),
            include_observers=True,
        )
        model_xml = model_xml or generated["model_xml"]
        queries = queries or generated["queries"]
        profile = profile or generated["profile"]
    return {
        "contract_json": contract_json,
        "model_xml": model_xml,
        "queries": queries,
        "result_json": result_json,
        "profile": profile or default_profile(),
        "source_text": source_text,
    }


def _is_channel_semantics_error(error: str) -> bool:
    needles = (
        "broadcast",
        "handshake",
        "channel",
        "sync",
        "A_SQ does not listen",
        "A_PH does not listen",
    )
    return any(needle in error for needle in needles)


def _include_observers_from_mode(mode: str | None, include_observers: bool) -> bool:
    if mode is None:
        return include_observers
    normalized = mode.strip().lower()
    if normalized in {"closed", "with_observers", "observers"}:
        return True
    if normalized in {"open", "open_system", "open-system"}:
        return include_observers
    if normalized in {"base", "minimal", "no_observers", "without_observers"}:
        return False
    raise ValueError("Unsupported PHY verify mode. Use closed, open_system, with_observers, base, or no_observers.")


def _generator_mode_from_verify_mode(mode: str | None) -> str | None:
    if mode is None:
        return None
    normalized = mode.strip().lower()
    if normalized in {"closed", "with_observers", "observers"}:
        return None
    if normalized in {"open", "open_system", "open-system"}:
        return "open_system"
    if normalized in {"minimal"}:
        return "minimal"
    if normalized in {"base", "no_observers", "without_observers"}:
        return None
    raise ValueError("Unsupported PHY verify mode. Use closed, open_system, with_observers, minimal, base, or no_observers.")


def _verifyta_version_banner(runner: VerifytaRunner) -> str:
    result = runner.get_version().to_dict()
    if result.get("status") != "ok":
        return f"unavailable:{result.get('status', 'unknown')}"
    text = (result.get("stdout") or result.get("stderr") or result.get("status") or "unknown").strip()
    return text.splitlines()[0] if text else "unknown"


def _representative_command(result: dict) -> list[str]:
    runs = result.get("runs") or []
    if runs and isinstance(runs[0], dict):
        return list(runs[0].get("command") or [])
    return list(result.get("command") or [])
