from __future__ import annotations

from typing import Any

from .config import UppaalConfig
from .examples import get_builtin_example, list_builtin_examples
from .phy import tools as phy_tools
from .verifyta import VerifytaRunner


def _runner() -> VerifytaRunner:
    return VerifytaRunner(UppaalConfig.from_env())


def build_mcp() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError(
            "The 'mcp' Python package is not installed. Install with: pip install -e ."
        ) from exc

    mcp = FastMCP("uppaal-mcp")

    @mcp.tool()
    def uppaal_version() -> dict:
        """Return verifyta version and license banner."""
        return _runner().get_version().to_dict()

    @mcp.tool()
    def uppaal_validate_model(
        model_xml: str | None = None,
        model_path: str | None = None,
        queries: str | None = None,
        query_path: str | None = None,
    ) -> dict:
        """Statically validate a UPPAAL XML model and optional query file."""
        return _runner().validate(
            model_xml=model_xml,
            model_path=model_path,
            queries=queries,
            query_path=query_path,
        )

    @mcp.tool()
    def uppaal_verify(
        model_xml: str | None = None,
        model_path: str | None = None,
        queries: str | None = None,
        query_path: str | None = None,
        options: list[str] | None = None,
        options_preset: str | None = None,
        timeout_sec: float | None = None,
        keep_artifacts: bool = True,
    ) -> dict:
        """Run UPPAAL verifyta on model/query text or paths."""
        return _runner().verify(
            model_xml=model_xml,
            model_path=model_path,
            queries=queries,
            query_path=query_path,
            options=options,
            options_preset=options_preset,
            timeout_sec=timeout_sec,
            keep_artifacts=keep_artifacts,
        ).to_dict()

    @mcp.tool()
    def uppaal_verify_batch(
        items: list[dict],
        options_preset: str | None = None,
        timeout_sec: float | None = None,
    ) -> list[dict]:
        """Run several UPPAAL verification jobs sequentially."""
        return _runner().verify_batch(items, options_preset=options_preset, timeout_sec=timeout_sec)

    @mcp.tool()
    def uppaal_list_examples() -> list[dict]:
        """List built-in UPPAAL example models."""
        return list_builtin_examples()

    @mcp.tool()
    def uppaal_get_example(name: str) -> dict:
        """Return a built-in example with model_xml and queries text."""
        return get_builtin_example(name).to_dict()

    @mcp.tool()
    def uppaal_explain_result(result: dict) -> dict:
        """Create a compact human-readable explanation from a verifyta result dict."""
        return explain_result(result)

    @mcp.tool()
    def phy_extract_contract(
        tex_text: str | None = None,
        tex_path: str | None = None,
    ) -> dict:
        """Extract the PHY contract IR from the article LaTeX source."""
        return phy_tools.extract_contract(tex_text=tex_text, tex_path=tex_path)

    @mcp.tool()
    def phy_validate_contract(contract_json: dict | None = None) -> dict:
        """Validate the PHY contract IR against article invariants."""
        return phy_tools.validate_contract(contract_json)

    @mcp.tool()
    def phy_generate_uppaal_model(
        contract_json: dict | None = None,
        tex_text: str | None = None,
        tex_path: str | None = None,
        profile: dict | None = None,
        include_observers: bool = True,
        debug_counters: bool = True,
        include_negative_scenarios: bool = False,
        mode: str | None = None,
    ) -> dict:
        """Generate a closed UPPAAL A_SYS model from the PHY contract."""
        return phy_tools.generate_uppaal_from_contract(
            contract_json=contract_json,
            tex_text=tex_text,
            tex_path=tex_path,
            profile=profile,
            include_observers=include_observers,
            debug_counters=debug_counters,
            include_negative_scenarios=include_negative_scenarios,
            mode=mode,
        )

    @mcp.tool()
    def phy_generate_property_pack(
        contract_json: dict | None = None,
        model_xml: str | None = None,
        profile: dict | None = None,
        include_observers: bool = True,
        debug_counters: bool = True,
        include_negative: bool = False,
    ) -> dict:
        """Generate the PHY-specific query pack from the contract IR."""
        return phy_tools.generate_property_pack(
            contract_json=contract_json,
            model_xml=model_xml,
            profile=profile,
            include_observers=include_observers,
            debug_counters=debug_counters,
            include_negative=include_negative,
        )

    @mcp.tool()
    def phy_export_property_pack(
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
        """Write PHY queries.q plus JSON metadata/provenance files."""
        return phy_tools.export_property_pack(
            output_dir=output_dir,
            contract_json=contract_json,
            tex_text=tex_text,
            tex_path=tex_path,
            model_xml=model_xml,
            profile=profile,
            include_observers=include_observers,
            debug_counters=debug_counters,
            include_negative=include_negative,
        )

    @mcp.tool()
    def phy_generate_report(
        contract_json: dict | None = None,
        tex_text: str | None = None,
        tex_path: str | None = None,
        model_xml: str | None = None,
        queries: str | None = None,
        result_json: dict | None = None,
        trace_text: str | None = None,
        profile: dict | None = None,
    ) -> dict:
        """Generate PHY Markdown reports and traceability artifacts in-memory."""
        return phy_tools.generate_report(
            contract_json=contract_json,
            tex_text=tex_text,
            tex_path=tex_path,
            model_xml=model_xml,
            queries=queries,
            result_json=result_json,
            trace_text=trace_text,
            profile=profile,
        )

    @mcp.tool()
    def phy_export_report(
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
        """Write PHY reports plus contract/model/query artifacts to a directory."""
        return phy_tools.export_report(
            output_dir=output_dir,
            contract_json=contract_json,
            tex_text=tex_text,
            tex_path=tex_path,
            model_xml=model_xml,
            queries=queries,
            result_json=result_json,
            trace_text=trace_text,
            profile=profile,
        )

    @mcp.tool()
    def phy_export_run_artifacts(
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
        """Write a PHY run artifact layout with metadata and cache key."""
        return phy_tools.export_run_artifacts(
            output_root=output_root,
            contract_json=contract_json,
            tex_text=tex_text,
            tex_path=tex_path,
            model_xml=model_xml,
            queries=queries,
            result_json=result_json,
            trace_text=trace_text,
            profile=profile,
            verifyta_version=verifyta_version,
            verifyta_command=verifyta_command,
            options=options,
            force=force,
        )

    @mcp.tool()
    def phy_verify_contract(
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
        """Generate and verify the closed PHY A_SYS model with verifyta."""
        return phy_tools.verify_contract(
            tex_text=tex_text,
            tex_path=tex_path,
            contract_json=contract_json,
            profile=profile,
            mode=mode,
            include_observers=include_observers,
            timeout_sec=timeout_sec,
            artifact_root=artifact_root,
            force=force,
        )

    @mcp.tool()
    def phy_verify_property_pack(
        model_xml: str | None = None,
        model_path: str | None = None,
        queries: str | None = None,
        query_path: str | None = None,
        explain: bool = True,
        timeout_sec: float | None = None,
        static_only: bool = False,
    ) -> dict:
        """Verify a PHY property pack against a model, optionally returning PHY explanation."""
        return phy_tools.verify_property_pack(
            model_xml=model_xml,
            model_path=model_path,
            queries=queries,
            query_path=query_path,
            explain=explain,
            timeout_sec=timeout_sec,
            static_only=static_only,
        )

    @mcp.tool()
    def phy_check_no_continuous_guards(
        model_xml: str | None = None,
        contract_json: dict | None = None,
    ) -> dict:
        """Check that generated automata do not use continuous PHY values in guards."""
        return phy_tools.check_no_continuous_guards(
            model_xml=model_xml,
            contract_json=contract_json,
        ).to_dict()

    @mcp.tool()
    def phy_check_channel_semantics(
        model_xml: str | None = None,
        contract_json: dict | None = None,
    ) -> dict:
        """Check report/event broadcast and command handshake channel semantics."""
        return phy_tools.check_channel_semantics(
            model_xml=model_xml,
            contract_json=contract_json,
        )

    @mcp.tool()
    def phy_check_alpha_profile(profile_json: dict | None = None) -> dict:
        """Validate an alpha_PHY threshold/profile policy."""
        return phy_tools.check_alpha_profile(profile_json)

    @mcp.tool()
    def phy_explain_counterexample(
        result_json: dict,
        trace_text: str | None = None,
        contract_json: dict | None = None,
    ) -> dict:
        """Explain a verifyta violation in PHY/SDN/ISAC terms."""
        return phy_tools.explain_counterexample(
            result_json=result_json,
            trace_text=trace_text,
            contract_json=contract_json,
        )

    @mcp.tool()
    def phy_list_profiles() -> list[dict]:
        """List built-in alpha/deadline profiles."""
        return phy_tools.list_profiles()

    @mcp.tool()
    def phy_get_profile(name: str) -> dict:
        """Return one built-in alpha/deadline profile."""
        return phy_tools.get_profile(name)

    @mcp.tool()
    def phy_list_scenarios() -> list[dict]:
        """List built-in PHY verification scenarios."""
        return phy_tools.phy_list_scenarios()

    @mcp.tool()
    def phy_get_scenario(name: str, profile: dict | None = None) -> dict:
        """Generate one compact PHY scenario model."""
        return phy_tools.phy_get_scenario(name, profile=profile)

    @mcp.tool()
    def phy_verify_scenario(
        name: str,
        profile: dict | None = None,
        timeout_sec: float | None = None,
    ) -> dict:
        """Verify one compact PHY scenario with verifyta."""
        return phy_tools.phy_verify_scenario(name, profile=profile, timeout_sec=timeout_sec)

    @mcp.tool()
    def phy_verify_all_scenarios(
        profile: dict | None = None,
        timeout_sec: float | None = None,
    ) -> dict:
        """Verify all built-in compact PHY scenarios with verifyta."""
        return phy_tools.phy_verify_all_scenarios(profile=profile, timeout_sec=timeout_sec)

    @mcp.tool()
    def phy_list_benchmarks() -> list[dict]:
        """List PHY benchmark and intentionally broken static scenarios."""
        return phy_tools.phy_list_benchmarks()

    @mcp.tool()
    def phy_get_benchmark(name: str, profile: dict | None = None) -> dict:
        """Generate one PHY benchmark scenario model."""
        return phy_tools.phy_get_benchmark(name, profile=profile)

    @mcp.tool()
    def phy_validate_benchmarks(profile: dict | None = None) -> dict:
        """Generate and statically validate all PHY benchmark scenarios."""
        return phy_tools.phy_validate_benchmarks(profile=profile)

    return mcp


def explain_result(result: dict) -> dict:
    status = result.get("status", "unknown")
    query_results = result.get("query_results") or []
    failed = [
        item
        for item in query_results
        if item.get("status") in {"not_satisfied", "inconclusive", "maybe"}
    ]
    if status == "satisfied":
        summary = "All parsed UPPAAL formulas were satisfied."
    elif status == "not_satisfied":
        summary = "At least one UPPAAL formula was not satisfied."
    elif status == "timeout":
        summary = "verifyta timed out before finishing."
    elif status == "tool_not_found":
        summary = "verifyta was not found at the configured path."
    elif status == "error":
        summary = "verifyta returned an error. Check stderr/stdout and model syntax."
    else:
        summary = "The result could not be classified from verifyta output."

    return {
        "status": status,
        "summary": summary,
        "failed_queries": failed,
        "artifact_dir": result.get("artifact_dir"),
        "stderr_tail": _tail(result.get("stderr") or ""),
        "stdout_tail": _tail(result.get("stdout") or ""),
    }


def _tail(text: str, max_lines: int = 20) -> str:
    lines = text.splitlines()
    return "\n".join(lines[-max_lines:])


def main() -> None:
    build_mcp().run()


if __name__ == "__main__":
    main()
