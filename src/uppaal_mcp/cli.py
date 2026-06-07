from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import UppaalConfig
from .examples import get_builtin_example, list_builtin_examples
from .phy import tools as phy_tools
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
    phy_generate.add_argument("--no-observers", action="store_true")
    phy_generate.add_argument("--no-debug-counters", action="store_true")
    phy_generate.add_argument("--include-negative-scenarios", action="store_true")

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
            generated = {
                "output_dir": str(output),
                "generation_mode": generated["generation_mode"],
                "include_negative_scenarios": generated["include_negative_scenarios"],
                "semantic_validation": generated["semantic_validation"],
                "alpha_validation": generated["alpha_validation"],
            }
        print_json(generated)
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


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
