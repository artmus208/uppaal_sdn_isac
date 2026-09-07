#!/usr/bin/env python3
"""Reproduce the P1 source inventory and demo-classifier boundary observations.

Stdlib only. Run from a repository checkout; --check compares exact artifacts.
This is source/static evidence, never an UPPAAL or empirical validation run.
"""
import argparse
import hashlib
import importlib
import json
import math
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
LAYERS = ("phy", "mac", "sdn", "application")
TEX = dict(zip(LAYERS, (
    "levels_tex/PHY_level_formalization_reviewed-2026-06-06-143000.tex",
    "levels_tex/MAC_resource_scheduling_formalization.tex",
    "levels_tex/SDN_RIC_control_plane_formalization.tex",
    "levels_tex/Application_service_layer_formalization.tex",
)))
XML = dict(zip(LAYERS, (
    ".uppaal_mcp_workspace/phy_generated/model.xml",
    ".uppaal_mcp_workspace/mac_generated/model.xml",
    ".uppaal_mcp_workspace/sdn_generated_smoke/model.xml",
    ".uppaal_mcp_workspace/Application_service_layer_uppaal.xml",
)))
PROFILES = ("default", "conservative_safety", "stress")
TIMING = re.compile(r"^(?:D_|T_|J_|tau_)")
CONST = re.compile(r"\bconst\s+(\w+)\s+([^;\n]+);")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def refs(path, token):
    return [{"path": path, "line": i} for i, s in enumerate(read(path).splitlines(), 1)
            if token in s]


def constants(text):
    for match in CONST.finditer(text):
        for item in match[2].split(","):
            m = re.fullmatch(r"\s*(\w+)\s*=\s*(-?\d+)\s*", item)
            if m:
                yield m[1], int(m[2]), match[1]


def build():
    paths = sorted(set(TEX.values()) | set(XML.values()) | {
        f"src/uppaal_mcp/{layer}/{module}.py"
        for layer in LAYERS[:3]
        for module in ("alpha", "defaults", "generator", "ir", "property_pack")
    })
    paths += ["manifests/baselines/reviewer-r1.yaml", "manifests/v1.md",
              "manifests/collaboration-v1.yaml"]
    data = {
        "source_commit": "f2f714a26d6b9d9f538ef1a16b53c3e060768a11",
        "evidence_kind": "source_inventory_and_static_probe",
        "files": {p: digest((ROOT / p).read_bytes()) for p in paths},
        "timings": [], "classes": [], "constant_occurrences": [],
        "clock_constraints": [], "bounded_integer_declarations": [],
        "profile_definitions": {}, "generated_model_hashes": {},
    }
    for layer in LAYERS:
        surfaces = [(XML[layer], read(XML[layer])), (TEX[layer], read(TEX[layer]))]
        if layer != "application":
            prefix = f"src/uppaal_mcp/{layer}"
            alpha = importlib.import_module(f"uppaal_mcp.{layer}.alpha")
            gen = importlib.import_module(f"uppaal_mcp.{layer}.generator")
            profiles = {n: alpha.default_profile(n) for n in PROFILES}
            data["profile_definitions"][layer] = profiles
            classes = alpha.list_classes()
            for n, profile in profiles.items():
                model = gen.generate_uppaal_model(profile=profile).model_xml
                surface = f"generated:{layer}:{n}:default-options"
                surfaces.append((surface, model))
                data["generated_model_hashes"][surface] = digest(model.encode())
            class_path = f"{prefix}/defaults.py"
        else:
            profiles = {}
            decl = ET.fromstring(read(XML[layer])).findtext("declaration") or ""
            classes = {}
            for name, value, typ in constants(decl):
                if typ != "int":
                    classes.setdefault(typ, []).append(name)
            class_path = XML[layer]
        for name, values in sorted(classes.items()):
            data["classes"].append({
                "id": f"{layer}.{name}", "values": values,
                "source_references": refs(class_path, name),
                "calibration": f"validation-report.md#{layer}-classes",
                "status": "finite_domain_defined_see_metric_or_policy_method",
            })
        timings = {}
        for surface, text in surfaces:
            # TeX prose is scanned for literal const declarations; XML only its declarations.
            if not surface.endswith(".tex"):
                model = ET.fromstring(text)
                for node in model.iter("label"):
                    if node.get("kind") in ("guard", "invariant"):
                        label = node.text or ""
                        if re.search(r"\b(?:c_\w+|aos_\w+|age_\w+|x)\b", label):
                            data["clock_constraints"].append({"surface": surface,
                                "kind": node.get("kind"), "expression": label})
                text = "\n".join(node.text or "" for node in model.iter("declaration"))
            for line in text.splitlines():
                if re.search(r"\bint\s*\[", line):
                    data["bounded_integer_declarations"].append({"surface": surface, "declaration": line.strip()})
            for name, value, typ in constants(text):
                is_timing = typ == "int" and bool(TIMING.match(name))
                encodings = {re.sub(r"[^A-Za-z0-9_]", "_", f"{cls}_{v}").upper()
                             for cls, vals in classes.items() for v in vals}
                if typ == "int" and not is_timing and name not in encodings:
                    if not name.startswith(("SCENARIO_", "W_")):
                        raise ValueError(f"Unclassified integer constant: {surface}: {name}")
                data["constant_occurrences"].append({"surface": surface, "name": name,
                    "value": value, "type": typ,
                    "kind": "timing" if is_timing else "finite_encoding"})
                if is_timing:
                    timings.setdefault(name, {})[surface] = value
        for name, values in sorted(timings.items()):
            source_paths = [TEX[layer], XML[layer]]
            if layer != "application":
                source_paths += [f"src/uppaal_mcp/{layer}/alpha.py", f"src/uppaal_mcp/{layer}/generator.py"]
            data["timings"].append({"id": f"{layer}.{name}", "values_by_surface": values,
                "profiles": {n: p["deadlines"][name] for n, p in profiles.items() if name in p["deadlines"]},
                "source_references": [r for p in source_paths for r in refs(p, name)],
                "unit": "abstract_clock_unit_not_physically_pinned",
                "status": "illustrative_uncalibrated",
                "calibration": "validation-report.md#timing-calibration"})
    alpha = importlib.import_module("uppaal_mcp.phy.alpha")
    probes = []
    # nextafter avoids an arbitrary epsilon. Raw observations, no patched classifier.
    cases = [("SINR_c", "SINRClass", t, bad) for t, bad in [(0., "OUTAGE"), (10., "LOW"), (25., "OK")]]
    cases += [("Pd", "PdClass", .5, "FAILED"), ("Pd", "PdClass", .9, "LOW"),
              ("Rfa", "RfaClass", .05, "HIGH"), ("Rfa", "RfaClass", .2, "CRITICAL"),
              ("AoS_CTRL", "AoSClass", 10., "EXPIRED")]
    for field, cls, boundary, worse in cases:
        values = [math.nextafter(boundary, -math.inf), boundary, math.nextafter(boundary, math.inf)]
        outputs = [alpha.classify_sample({field: value})[cls] for value in values]
        probes.append({"field": field, "class": cls, "threshold": boundary,
            "inputs_below_equal_above": values, "outputs_below_equal_above": outputs,
            "worse_adjacent_class": worse, "equality_matches_declared_worse_class": outputs[1] == worse})
    data["boundary_probe"] = {"source_references": refs("src/uppaal_mcp/phy/alpha.py", "Class\":") ,
        "cases": probes, "empty_input_output": alpha.classify_sample({}),
        "scope": "deterministic Python example only; no empirical data or model checking"}
    return data


def markdown(data):
    lines = ["# P1 parameter inventory", "", "Generated by `inventory.py`; source hashes and all occurrences are in `inventory.json`.",
             "Values are illustrative abstract clock units. Calibration methods and symbolic inputs are in `validation-report.md`.", "",
             "| Parameter | Stored XML | Profile default / conservative / stress | Method |", "|---|---:|---|---|"]
    for row in data["timings"]:
        layer = row["id"].split(".")[0]
        p = row["profiles"]
        values = " / ".join(str(p[n]) for n in PROFILES) if p else "not profile-controlled"
        lines.append(f"| `{row['id']}` | {row['values_by_surface'].get(XML[layer], 'absent')} | {values} | [timing](validation-report.md#timing-calibration) |")
    lines += ["", "## Finite domains requiring an external mapping or a policy definition", "",
              "An enum code is not a measured capacity, retry limit or physical threshold.", "",
              "| Domain | Values | Calibration / definition |", "|---|---|---|"]
    for row in data["classes"]:
        lines.append(f"| `{row['id']}` | {', '.join(row['values'])} | [method]({row['calibration']}) |")
    lines += ["", "## Reproduced equality observations", "",
              "| Input | Boundary | Below / equal / above | Declared worse class |", "|---|---:|---|---|"]
    for row in data["boundary_probe"]["cases"]:
        lines.append(f"| {row['field']} | {row['threshold']} | {' / '.join(row['outputs_below_equal_above'])} | {row['worse_adjacent_class']} |")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    outputs = {"inventory.json": json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
               "parameter-table.md": markdown(data)}
    for name, content in outputs.items():
        path = HERE / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"STALE OR MISSING: {name}; regenerate and review the source change")
        else:
            path.write_text(content, encoding="utf-8")
    print(json.dumps({"artifact_comparison": "match" if args.check else "generated",
        "timing_parameters": len(data["timings"]), "finite_domains": len(data["classes"]),
        "files_hashed": len(data["files"]),
        "boundary_policy_mismatches": sum(not c["equality_matches_declared_worse_class"] for c in data["boundary_probe"]["cases"]),
        "verification": "not_run"}, indent=2))


if __name__ == "__main__":
    main()
