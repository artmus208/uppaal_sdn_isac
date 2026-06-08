from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import UppaalConfig
from .examples import get_builtin_example, list_builtin_examples
from .mac import tools as mac_tools
from .phy import tools as phy_tools
from .sdn import tools as sdn_tools
from .verifyta import VerifytaRunner


def main() -> None:
    parser = argparse.ArgumentParser(prog="uppaal-verifyta")
    parser.add_argument("--verifyta-path", help="Path to verifyta/verifyta.exe.")
    parser.add_argument("--workspace", help="Workspace for generated run artifacts.")
    parser.add_argument("--timeout-sec", type=float, help="verifyta timeout in seconds.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Print verifyta version as JSON.")
    subparsers.add_parser("list-examples", help="List built-in examples.")

    validate = subparsers.add_parser("validate", help="Validate a UPPAAL model statically.")
    validate.add_argument("--model", required=True)
    validate.add_argument("--queries")

    verify = subparsers.add_parser("verify", help="Run verifyta.")
    verify.add_argument("--model", required=True)
    verify.add_argument("--queries")
    verify.add_argument("--options-preset", choices=["normal", "trace_on_violation", "diagnostic"])
    verify.add_argument("verifyta_options", nargs=argparse.REMAINDER)

    example = subparsers.add_parser("example", help="Print or export a built-in example.")
    example.add_argument("name")
    example.add_argument("--output-dir")

    phy_extract = subparsers.add_parser("phy-extract", help="Extract PHY contract IR from the article.")
    phy_extract.add_argument("--tex")

    phy_generate = subparsers.add_parser("phy-generate", help="Generate PHY UPPAAL model and queries.")
    phy_generate.add_argument("--tex")
    phy_generate.add_argument("--output-dir")
    phy_generate.add_argument("--mode")
    phy_generate.add_argument("--layout", choices=["compact", "readable"], default="readable")
    phy_generate.add_argument("--no-observers", action="store_true")
    phy_generate.add_argument("--no-debug-counters", action="store_true")
    phy_generate.add_argument("--include-negative-scenarios", action="store_true")

    phy_export_diagram = subparsers.add_parser("phy-export-diagram", help="Export PHY Graphviz DOT/SVG and readable maps.")
    phy_export_diagram.add_argument("--model")
    phy_export_diagram.add_argument("--tex")
    phy_export_diagram.add_argument("--output-dir")
    phy_export_diagram.add_argument("--layout", choices=["compact", "readable"], default="readable")

    phy_property_pack = subparsers.add_parser("phy-property-pack", help="Generate PHY property pack with JSON metadata.")
    phy_property_pack.add_argument("--tex")
    phy_property_pack.add_argument("--output-dir")
    phy_property_pack.add_argument("--no-observers", action="store_true")
    phy_property_pack.add_argument("--no-debug-counters", action="store_true")
    phy_property_pack.add_argument("--include-negative", action="store_true")

    phy_report = subparsers.add_parser("phy-report", help="Generate PHY Markdown reports.")
    phy_report.add_argument("--tex")
    phy_report.add_argument("--output-dir")
    phy_report.add_argument("--result-json")
    phy_report.add_argument("--trace-text")

    phy_run_artifacts = subparsers.add_parser("phy-run-artifacts", help="Export PHY run artifacts with metadata/cache key.")
    phy_run_artifacts.add_argument("--tex")
    phy_run_artifacts.add_argument("--output-root", required=True)
    phy_run_artifacts.add_argument("--result-json")
    phy_run_artifacts.add_argument("--trace-text")
    phy_run_artifacts.add_argument("--verifyta-version")
    phy_run_artifacts.add_argument("--force", action="store_true")

    phy_verify = subparsers.add_parser("phy-verify", help="Generate and verify the PHY model.")
    phy_verify.add_argument("--tex")
    phy_verify.add_argument("--mode")
    phy_verify.add_argument("--timeout-sec", type=float)

    phy_verify_property_pack = subparsers.add_parser("phy-verify-property-pack", help="Verify a PHY property pack against a model.")
    phy_verify_property_pack.add_argument("--model", required=True)
    phy_verify_property_pack.add_argument("--queries", required=True)
    phy_verify_property_pack.add_argument("--timeout-sec", type=float)
    phy_verify_property_pack.add_argument("--no-explain", action="store_true")
    phy_verify_property_pack.add_argument("--static-only", action="store_true")

    subparsers.add_parser("phy-list-scenarios", help="List built-in PHY scenarios.")

    phy_scenario = subparsers.add_parser("phy-scenario", help="Generate one PHY scenario.")
    phy_scenario.add_argument("name")
    phy_scenario.add_argument("--output-dir")

    phy_verify_scenario = subparsers.add_parser("phy-verify-scenario", help="Verify one PHY scenario.")
    phy_verify_scenario.add_argument("name")
    phy_verify_scenario.add_argument("--timeout-sec", type=float)

    phy_verify_all_scenarios = subparsers.add_parser("phy-verify-all-scenarios", help="Verify all built-in PHY scenarios.")
    phy_verify_all_scenarios.add_argument("--timeout-sec", type=float)

    subparsers.add_parser("phy-list-benchmarks", help="List PHY benchmark scenarios.")

    phy_benchmark = subparsers.add_parser("phy-benchmark", help="Generate one PHY benchmark scenario.")
    phy_benchmark.add_argument("name")
    phy_benchmark.add_argument("--output-dir")

    subparsers.add_parser("phy-validate-benchmarks", help="Statically validate all PHY benchmark scenarios.")

    mac_extract = subparsers.add_parser("mac-extract", help="Extract MAC contract IR from the article.")
    mac_extract.add_argument("--tex")

    mac_generate = subparsers.add_parser("mac-generate", help="Generate MAC UPPAAL model and queries.")
    mac_generate.add_argument("--tex")
    mac_generate.add_argument("--output-dir")
    mac_generate.add_argument("--mode")
    mac_generate.add_argument("--layout", choices=["compact", "readable"], default="readable")
    mac_generate.add_argument("--no-observers", action="store_true")
    mac_generate.add_argument("--no-debug-counters", action="store_true")
    mac_generate.add_argument("--include-negative-scenarios", action="store_true")

    mac_export_diagram = subparsers.add_parser("mac-export-diagram", help="Export MAC Graphviz DOT/SVG and readable maps.")
    mac_export_diagram.add_argument("--model")
    mac_export_diagram.add_argument("--tex")
    mac_export_diagram.add_argument("--output-dir")
    mac_export_diagram.add_argument("--layout", choices=["compact", "readable"], default="readable")

    mac_property_pack = subparsers.add_parser("mac-property-pack", help="Generate MAC property pack with JSON metadata.")
    mac_property_pack.add_argument("--tex")
    mac_property_pack.add_argument("--output-dir")
    mac_property_pack.add_argument("--no-observers", action="store_true")
    mac_property_pack.add_argument("--no-debug-counters", action="store_true")
    mac_property_pack.add_argument("--include-negative", action="store_true")

    mac_report = subparsers.add_parser("mac-report", help="Generate MAC Markdown reports.")
    mac_report.add_argument("--tex")
    mac_report.add_argument("--output-dir")
    mac_report.add_argument("--result-json")
    mac_report.add_argument("--trace-text")

    mac_run_artifacts = subparsers.add_parser("mac-run-artifacts", help="Export MAC run artifacts with metadata/cache key.")
    mac_run_artifacts.add_argument("--tex")
    mac_run_artifacts.add_argument("--output-root", required=True)
    mac_run_artifacts.add_argument("--result-json")
    mac_run_artifacts.add_argument("--trace-text")
    mac_run_artifacts.add_argument("--verifyta-version")
    mac_run_artifacts.add_argument("--force", action="store_true")

    mac_verify = subparsers.add_parser("mac-verify", help="Generate and verify the MAC model.")
    mac_verify.add_argument("--tex")
    mac_verify.add_argument("--mode")
    mac_verify.add_argument("--timeout-sec", type=float)

    mac_verify_property_pack = subparsers.add_parser("mac-verify-property-pack", help="Verify a MAC property pack against a model.")
    mac_verify_property_pack.add_argument("--model", required=True)
    mac_verify_property_pack.add_argument("--queries", required=True)
    mac_verify_property_pack.add_argument("--timeout-sec", type=float)
    mac_verify_property_pack.add_argument("--no-explain", action="store_true")
    mac_verify_property_pack.add_argument("--static-only", action="store_true")

    subparsers.add_parser("mac-list-scenarios", help="List built-in MAC scenarios.")

    mac_scenario = subparsers.add_parser("mac-scenario", help="Generate one MAC scenario.")
    mac_scenario.add_argument("name")
    mac_scenario.add_argument("--output-dir")

    mac_verify_scenario = subparsers.add_parser("mac-verify-scenario", help="Verify one MAC scenario.")
    mac_verify_scenario.add_argument("name")
    mac_verify_scenario.add_argument("--timeout-sec", type=float)

    mac_verify_all_scenarios = subparsers.add_parser("mac-verify-all-scenarios", help="Verify all built-in MAC scenarios.")
    mac_verify_all_scenarios.add_argument("--timeout-sec", type=float)

    subparsers.add_parser("mac-list-benchmarks", help="List MAC benchmark scenarios.")

    mac_benchmark = subparsers.add_parser("mac-benchmark", help="Generate one MAC benchmark scenario.")
    mac_benchmark.add_argument("name")
    mac_benchmark.add_argument("--output-dir")

    subparsers.add_parser("mac-validate-benchmarks", help="Statically validate all MAC benchmark scenarios.")

    sdn_extract = subparsers.add_parser("sdn-extract", help="Extract SDN/RIC contract IR from the article.")
    sdn_extract.add_argument("--tex")

    sdn_generate = subparsers.add_parser("sdn-generate", help="Generate SDN/RIC UPPAAL model and queries.")
    sdn_generate.add_argument("--tex")
    sdn_generate.add_argument("--output-dir")
    sdn_generate.add_argument("--mode")
    sdn_generate.add_argument("--layout", choices=["compact", "readable"], default="readable")
    sdn_generate.add_argument("--no-observers", action="store_true")
    sdn_generate.add_argument("--no-debug-counters", action="store_true")
    sdn_generate.add_argument("--include-negative-scenarios", action="store_true")

    sdn_export_diagram = subparsers.add_parser("sdn-export-diagram", help="Export SDN/RIC Graphviz DOT/SVG and readable maps.")
    sdn_export_diagram.add_argument("--model")
    sdn_export_diagram.add_argument("--tex")
    sdn_export_diagram.add_argument("--output-dir")
    sdn_export_diagram.add_argument("--layout", choices=["compact", "readable"], default="readable")

    sdn_property_pack = subparsers.add_parser("sdn-property-pack", help="Generate SDN/RIC property pack with JSON metadata.")
    sdn_property_pack.add_argument("--tex")
    sdn_property_pack.add_argument("--output-dir")
    sdn_property_pack.add_argument("--no-observers", action="store_true")
    sdn_property_pack.add_argument("--no-debug-counters", action="store_true")
    sdn_property_pack.add_argument("--include-negative", action="store_true")

    sdn_report = subparsers.add_parser("sdn-report", help="Generate SDN/RIC Markdown reports.")
    sdn_report.add_argument("--tex")
    sdn_report.add_argument("--output-dir")
    sdn_report.add_argument("--result-json")
    sdn_report.add_argument("--trace-text")

    sdn_run_artifacts = subparsers.add_parser("sdn-run-artifacts", help="Export SDN/RIC run artifacts with metadata/cache key.")
    sdn_run_artifacts.add_argument("--tex")
    sdn_run_artifacts.add_argument("--output-root", required=True)
    sdn_run_artifacts.add_argument("--result-json")
    sdn_run_artifacts.add_argument("--trace-text")
    sdn_run_artifacts.add_argument("--verifyta-version")
    sdn_run_artifacts.add_argument("--force", action="store_true")

    sdn_verify = subparsers.add_parser("sdn-verify", help="Generate and verify the SDN/RIC model.")
    sdn_verify.add_argument("--tex")
    sdn_verify.add_argument("--mode")
    sdn_verify.add_argument("--timeout-sec", type=float)

    sdn_verify_property_pack = subparsers.add_parser("sdn-verify-property-pack", help="Verify an SDN/RIC property pack against a model.")
    sdn_verify_property_pack.add_argument("--model", required=True)
    sdn_verify_property_pack.add_argument("--queries", required=True)
    sdn_verify_property_pack.add_argument("--timeout-sec", type=float)
    sdn_verify_property_pack.add_argument("--no-explain", action="store_true")
    sdn_verify_property_pack.add_argument("--static-only", action="store_true")

    subparsers.add_parser("sdn-list-scenarios", help="List built-in SDN/RIC scenarios.")

    sdn_scenario = subparsers.add_parser("sdn-scenario", help="Generate one SDN/RIC scenario.")
    sdn_scenario.add_argument("name")
    sdn_scenario.add_argument("--output-dir")

    sdn_verify_scenario = subparsers.add_parser("sdn-verify-scenario", help="Verify one SDN/RIC scenario.")
    sdn_verify_scenario.add_argument("name")
    sdn_verify_scenario.add_argument("--timeout-sec", type=float)

    sdn_verify_all_scenarios = subparsers.add_parser("sdn-verify-all-scenarios", help="Verify all built-in SDN/RIC scenarios.")
    sdn_verify_all_scenarios.add_argument("--timeout-sec", type=float)

    subparsers.add_parser("sdn-list-benchmarks", help="List SDN/RIC benchmark scenarios.")

    sdn_benchmark = subparsers.add_parser("sdn-benchmark", help="Generate one SDN/RIC benchmark scenario.")
    sdn_benchmark.add_argument("name")
    sdn_benchmark.add_argument("--output-dir")

    subparsers.add_parser("sdn-validate-benchmarks", help="Statically validate all SDN/RIC benchmark scenarios.")

    args = parser.parse_args()
    config = UppaalConfig.from_env(
        verifyta_path=args.verifyta_path,
        workspace=args.workspace,
        timeout_sec=args.timeout_sec,
    )
    runner = VerifytaRunner(config)

    if args.command == "version":
        print_json(runner.get_version().to_dict())
    elif args.command == "list-examples":
        print_json(list_builtin_examples())
    elif args.command == "validate":
        print_json(runner.validate(model_path=args.model, query_path=args.queries))
    elif args.command == "verify":
        options = [item for item in args.verifyta_options if item != "--"]
        result = runner.verify(
            model_path=args.model,
            query_path=args.queries,
            options=options,
            options_preset=args.options_preset,
        )
        print_json(result.to_dict())
    elif args.command == "example":
        item = get_builtin_example(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(item.model_xml, encoding="utf-8")
            (output / "queries.q").write_text(item.queries, encoding="utf-8")
            print_json({"output_dir": str(output), **item.to_dict()})
        else:
            print_json(item.to_dict())
    elif args.command == "phy-extract":
        print_json(phy_tools.extract_contract(tex_path=args.tex))
    elif args.command == "phy-generate":
        generated = phy_tools.generate_uppaal_from_contract(
            tex_path=args.tex,
            include_observers=not args.no_observers,
            debug_counters=not args.no_debug_counters,
            include_negative_scenarios=args.include_negative_scenarios,
            mode=args.mode,
            layout=args.layout,
        )
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "contract.json").write_text(
                json.dumps(generated["contract"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (output / "model.xml").write_text(generated["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(generated["queries"], encoding="utf-8")
            (output / "model_map.md").write_text(generated["model_map"], encoding="utf-8")
            (output / "template_map.md").write_text(generated["template_map"], encoding="utf-8")
            (output / "channels_map.md").write_text(generated["channels_map"], encoding="utf-8")
            (output / "layout_validation.json").write_text(
                json.dumps(generated["layout_validation"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            generated = {
                "output_dir": str(output),
                "generation_mode": generated["generation_mode"],
                "layout": generated["layout"],
                "include_negative_scenarios": generated["include_negative_scenarios"],
                "semantic_validation": generated["semantic_validation"],
                "alpha_validation": generated["alpha_validation"],
                "layout_validation": generated["layout_validation"],
            }
        print_json(generated)
    elif args.command == "phy-export-diagram":
        model_xml = None
        if args.model:
            model_xml = Path(args.model).read_text(encoding="utf-8")
        if args.output_dir:
            print_json(
                phy_tools.export_diagram(
                    output_dir=args.output_dir,
                    model_xml=model_xml,
                    tex_path=args.tex,
                    layout=args.layout,
                )
            )
        else:
            print_json(
                phy_tools.generate_diagram(
                    model_xml=model_xml,
                    tex_path=args.tex,
                    layout=args.layout,
                )
            )
    elif args.command == "phy-property-pack":
        if args.output_dir:
            print_json(
                phy_tools.export_property_pack(
                    output_dir=args.output_dir,
                    tex_path=args.tex,
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
        else:
            print_json(
                phy_tools.generate_property_pack(
                    contract_json=phy_tools.extract_contract(tex_path=args.tex),
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
    elif args.command == "phy-report":
        result_json = None
        if args.result_json:
            result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8"))
        trace_text = None
        if args.trace_text:
            trace_text = Path(args.trace_text).read_text(encoding="utf-8")
        if args.output_dir:
            print_json(
                phy_tools.export_report(
                    output_dir=args.output_dir,
                    tex_path=args.tex,
                    result_json=result_json,
                    trace_text=trace_text,
                )
            )
        else:
            print_json(phy_tools.generate_report(tex_path=args.tex, result_json=result_json, trace_text=trace_text))
    elif args.command == "phy-run-artifacts":
        result_json = None
        if args.result_json:
            result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8"))
        trace_text = None
        if args.trace_text:
            trace_text = Path(args.trace_text).read_text(encoding="utf-8")
        print_json(
            phy_tools.export_run_artifacts(
                output_root=args.output_root,
                tex_path=args.tex,
                result_json=result_json,
                trace_text=trace_text,
                verifyta_version=args.verifyta_version,
                force=args.force,
            )
        )
    elif args.command == "phy-verify":
        print_json(phy_tools.verify_contract(tex_path=args.tex, mode=args.mode, timeout_sec=args.timeout_sec))
    elif args.command == "phy-verify-property-pack":
        print_json(
            phy_tools.verify_property_pack(
                model_path=args.model,
                query_path=args.queries,
                explain=not args.no_explain,
                timeout_sec=args.timeout_sec,
                static_only=args.static_only,
            )
        )
    elif args.command == "phy-list-scenarios":
        print_json(phy_tools.phy_list_scenarios())
    elif args.command == "phy-scenario":
        scenario = phy_tools.phy_get_scenario(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(scenario["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(scenario["queries"], encoding="utf-8")
            scenario = {key: value for key, value in scenario.items() if key not in {"model_xml", "queries"}}
            scenario["output_dir"] = str(output)
        print_json(scenario)
    elif args.command == "phy-verify-scenario":
        print_json(phy_tools.phy_verify_scenario(args.name, timeout_sec=args.timeout_sec))
    elif args.command == "phy-verify-all-scenarios":
        print_json(phy_tools.phy_verify_all_scenarios(timeout_sec=args.timeout_sec))
    elif args.command == "phy-list-benchmarks":
        print_json(phy_tools.phy_list_benchmarks())
    elif args.command == "phy-benchmark":
        benchmark = phy_tools.phy_get_benchmark(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(benchmark["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(benchmark["queries"], encoding="utf-8")
            benchmark = {key: value for key, value in benchmark.items() if key not in {"model_xml", "queries"}}
            benchmark["output_dir"] = str(output)
        print_json(benchmark)
    elif args.command == "phy-validate-benchmarks":
        print_json(phy_tools.phy_validate_benchmarks())
    elif args.command == "mac-extract":
        print_json(mac_tools.extract_contract(tex_path=args.tex))
    elif args.command == "mac-generate":
        generated = mac_tools.generate_uppaal_from_contract(
            tex_path=args.tex,
            include_observers=not args.no_observers,
            debug_counters=not args.no_debug_counters,
            include_negative_scenarios=args.include_negative_scenarios,
            mode=args.mode,
            layout=args.layout,
        )
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "contract.json").write_text(json.dumps(generated["contract"], ensure_ascii=False, indent=2), encoding="utf-8")
            (output / "model.xml").write_text(generated["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(generated["queries"], encoding="utf-8")
            (output / "model_map.md").write_text(generated["model_map"], encoding="utf-8")
            (output / "template_map.md").write_text(generated["template_map"], encoding="utf-8")
            (output / "channels_map.md").write_text(generated["channels_map"], encoding="utf-8")
            (output / "policy_map.md").write_text(generated["policy_map"], encoding="utf-8")
            (output / "layout_validation.json").write_text(json.dumps(generated["layout_validation"], ensure_ascii=False, indent=2), encoding="utf-8")
            generated = {
                "output_dir": str(output),
                "generation_mode": generated["generation_mode"],
                "layout": generated["layout"],
                "include_negative_scenarios": generated["include_negative_scenarios"],
                "semantic_validation": generated["semantic_validation"],
                "alpha_validation": generated["alpha_validation"],
                "layout_validation": generated["layout_validation"],
            }
        print_json(generated)
    elif args.command == "mac-export-diagram":
        model_xml = Path(args.model).read_text(encoding="utf-8") if args.model else None
        if args.output_dir:
            print_json(mac_tools.export_diagram(output_dir=args.output_dir, model_xml=model_xml, tex_path=args.tex, layout=args.layout))
        else:
            print_json(mac_tools.generate_diagram(model_xml=model_xml, tex_path=args.tex, layout=args.layout))
    elif args.command == "mac-property-pack":
        if args.output_dir:
            print_json(
                mac_tools.export_property_pack(
                    output_dir=args.output_dir,
                    tex_path=args.tex,
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
        else:
            print_json(
                mac_tools.generate_property_pack(
                    contract_json=mac_tools.extract_contract(tex_path=args.tex),
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
    elif args.command == "mac-report":
        result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8")) if args.result_json else None
        trace_text = Path(args.trace_text).read_text(encoding="utf-8") if args.trace_text else None
        if args.output_dir:
            print_json(mac_tools.export_report(output_dir=args.output_dir, tex_path=args.tex, result_json=result_json, trace_text=trace_text))
        else:
            print_json(mac_tools.generate_report(tex_path=args.tex, result_json=result_json, trace_text=trace_text))
    elif args.command == "mac-run-artifacts":
        result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8")) if args.result_json else None
        trace_text = Path(args.trace_text).read_text(encoding="utf-8") if args.trace_text else None
        print_json(
            mac_tools.export_run_artifacts(
                output_root=args.output_root,
                tex_path=args.tex,
                result_json=result_json,
                trace_text=trace_text,
                verifyta_version=args.verifyta_version,
                force=args.force,
            )
        )
    elif args.command == "mac-verify":
        print_json(mac_tools.verify_contract(tex_path=args.tex, mode=args.mode, timeout_sec=args.timeout_sec))
    elif args.command == "mac-verify-property-pack":
        print_json(
            mac_tools.verify_property_pack(
                model_path=args.model,
                query_path=args.queries,
                explain=not args.no_explain,
                timeout_sec=args.timeout_sec,
                static_only=args.static_only,
            )
        )
    elif args.command == "mac-list-scenarios":
        print_json(mac_tools.mac_list_scenarios())
    elif args.command == "mac-scenario":
        scenario = mac_tools.mac_get_scenario(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(scenario["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(scenario["queries"], encoding="utf-8")
            scenario = {key: value for key, value in scenario.items() if key not in {"model_xml", "queries"}}
            scenario["output_dir"] = str(output)
        print_json(scenario)
    elif args.command == "mac-verify-scenario":
        print_json(mac_tools.mac_verify_scenario(args.name, timeout_sec=args.timeout_sec))
    elif args.command == "mac-verify-all-scenarios":
        print_json(mac_tools.mac_verify_all_scenarios(timeout_sec=args.timeout_sec))
    elif args.command == "mac-list-benchmarks":
        print_json(mac_tools.mac_list_benchmarks())
    elif args.command == "mac-benchmark":
        benchmark = mac_tools.mac_get_benchmark(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(benchmark["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(benchmark["queries"], encoding="utf-8")
            benchmark = {key: value for key, value in benchmark.items() if key not in {"model_xml", "queries"}}
            benchmark["output_dir"] = str(output)
        print_json(benchmark)
    elif args.command == "mac-validate-benchmarks":
        print_json(mac_tools.mac_validate_benchmarks())
    elif args.command == "sdn-extract":
        print_json(sdn_tools.extract_contract(tex_path=args.tex))
    elif args.command == "sdn-generate":
        generated = sdn_tools.generate_uppaal_from_contract(
            tex_path=args.tex,
            include_observers=not args.no_observers,
            debug_counters=not args.no_debug_counters,
            include_negative_scenarios=args.include_negative_scenarios,
            mode=args.mode,
            layout=args.layout,
        )
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "contract.json").write_text(json.dumps(generated["contract"], ensure_ascii=False, indent=2), encoding="utf-8")
            (output / "model.xml").write_text(generated["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(generated["queries"], encoding="utf-8")
            (output / "model_map.md").write_text(generated["model_map"], encoding="utf-8")
            (output / "template_map.md").write_text(generated["template_map"], encoding="utf-8")
            (output / "channels_map.md").write_text(generated["channels_map"], encoding="utf-8")
            (output / "policy_map.md").write_text(generated["policy_map"], encoding="utf-8")
            (output / "interface_map.md").write_text(generated["interface_map"], encoding="utf-8")
            (output / "layout_validation.json").write_text(json.dumps(generated["layout_validation"], ensure_ascii=False, indent=2), encoding="utf-8")
            generated = {
                "output_dir": str(output),
                "generation_mode": generated["generation_mode"],
                "layout": generated["layout"],
                "system_mode": generated["system_mode"],
                "include_negative_scenarios": generated["include_negative_scenarios"],
                "semantic_validation": generated["semantic_validation"],
                "alpha_validation": generated["alpha_validation"],
                "layout_validation": generated["layout_validation"],
            }
        print_json(generated)
    elif args.command == "sdn-export-diagram":
        model_xml = Path(args.model).read_text(encoding="utf-8") if args.model else None
        if args.output_dir:
            print_json(sdn_tools.export_diagram(output_dir=args.output_dir, model_xml=model_xml, tex_path=args.tex, layout=args.layout))
        else:
            print_json(sdn_tools.generate_diagram(model_xml=model_xml, tex_path=args.tex, layout=args.layout))
    elif args.command == "sdn-property-pack":
        if args.output_dir:
            print_json(
                sdn_tools.export_property_pack(
                    output_dir=args.output_dir,
                    tex_path=args.tex,
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
        else:
            print_json(
                sdn_tools.generate_property_pack(
                    contract_json=sdn_tools.extract_contract(tex_path=args.tex),
                    include_observers=not args.no_observers,
                    debug_counters=not args.no_debug_counters,
                    include_negative=args.include_negative,
                )
            )
    elif args.command == "sdn-report":
        result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8")) if args.result_json else None
        trace_text = Path(args.trace_text).read_text(encoding="utf-8") if args.trace_text else None
        if args.output_dir:
            print_json(sdn_tools.export_report(output_dir=args.output_dir, tex_path=args.tex, result_json=result_json, trace_text=trace_text))
        else:
            print_json(sdn_tools.generate_report(tex_path=args.tex, result_json=result_json, trace_text=trace_text))
    elif args.command == "sdn-run-artifacts":
        result_json = json.loads(Path(args.result_json).read_text(encoding="utf-8")) if args.result_json else None
        trace_text = Path(args.trace_text).read_text(encoding="utf-8") if args.trace_text else None
        print_json(
            sdn_tools.export_run_artifacts(
                output_root=args.output_root,
                tex_path=args.tex,
                result_json=result_json,
                trace_text=trace_text,
                verifyta_version=args.verifyta_version,
                force=args.force,
            )
        )
    elif args.command == "sdn-verify":
        print_json(sdn_tools.verify_contract(tex_path=args.tex, mode=args.mode, timeout_sec=args.timeout_sec))
    elif args.command == "sdn-verify-property-pack":
        print_json(
            sdn_tools.verify_property_pack(
                model_path=args.model,
                query_path=args.queries,
                explain=not args.no_explain,
                timeout_sec=args.timeout_sec,
                static_only=args.static_only,
            )
        )
    elif args.command == "sdn-list-scenarios":
        print_json(sdn_tools.sdn_list_scenarios())
    elif args.command == "sdn-scenario":
        scenario = sdn_tools.sdn_get_scenario(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(scenario["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(scenario["queries"], encoding="utf-8")
            scenario = {key: value for key, value in scenario.items() if key not in {"model_xml", "queries"}}
            scenario["output_dir"] = str(output)
        print_json(scenario)
    elif args.command == "sdn-verify-scenario":
        print_json(sdn_tools.sdn_verify_scenario(args.name, timeout_sec=args.timeout_sec))
    elif args.command == "sdn-verify-all-scenarios":
        print_json(sdn_tools.sdn_verify_all_scenarios(timeout_sec=args.timeout_sec))
    elif args.command == "sdn-list-benchmarks":
        print_json(sdn_tools.sdn_list_benchmarks())
    elif args.command == "sdn-benchmark":
        benchmark = sdn_tools.sdn_get_benchmark(args.name)
        if args.output_dir:
            output = Path(args.output_dir)
            output.mkdir(parents=True, exist_ok=True)
            (output / "model.xml").write_text(benchmark["model_xml"], encoding="utf-8")
            (output / "queries.q").write_text(benchmark["queries"], encoding="utf-8")
            benchmark = {key: value for key, value in benchmark.items() if key not in {"model_xml", "queries"}}
            benchmark["output_dir"] = str(output)
        print_json(benchmark)
    elif args.command == "sdn-validate-benchmarks":
        print_json(sdn_tools.sdn_validate_benchmarks())


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
