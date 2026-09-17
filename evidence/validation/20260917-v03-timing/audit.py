#!/usr/bin/env python3
"""Read-only by default: reproduce a lexical timing audit, not model checking."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = "49b33764b27b343b9354b234e4b4523430201872"
RUN = "evidence/instantiation/20260916-ack-observer/runs/ack-review-003-20260917/"
INPUTS = {
    "model": RUN + "integrated-model.xml",
    "queries": RUN + "integrated-queries.q",
    "candidate": "evidence/governance/20260910-p1-p2-review/candidate-inputs.json",
    "adaptation": "src/uppaal_mcp/integrated/adapt.py",
    "boundary": "src/uppaal_mcp/integrated/boundary.py",
    "manifest": "manifests/v1.md",
    "collaboration": "manifests/collaboration-v1.yaml",
    "baseline": "manifests/baselines/reviewer-r1.yaml",
}


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def words(text):
    # Comments cannot establish use of a declaration.
    text = re.sub(r"/\*.*?\*/|//[^\n]*", "", text or "", flags=re.S)
    return set(re.findall(r"\b[A-Za-z_]\w*\b", text))


def build():
    raw = {k: (ROOT / p).read_bytes() for k, p in INPUTS.items()}
    pinned = json.loads((HERE / "input-hashes.json").read_text())
    for k, data in raw.items():
        digest = hashlib.sha256(data).hexdigest()
        if digest != pinned[k]["sha256"] or INPUTS[k] != pinned[k]["path"]:
            raise ValueError(f"Pinned input mismatch: {k}")
    root = ET.fromstring(raw["model"])
    candidate = json.loads(raw["candidate"])
    contracts = json.loads((HERE / "contracts.json").read_text())
    records = []
    global_decl = root.findtext("declaration", "")
    clocks = set()
    for declaration in root.iter("declaration"):
        for match in re.finditer(r"\bclock\s+([^;]+);", declaration.text or ""):
            clocks.update(words(match.group(1)))
    # Function bodies include helper-owned resets (notably APP raise_* latches).
    for match in re.finditer(r"\b(?:void|bool|int)\s+(\w+)\s*\([^)]*\)\s*\{", global_decl):
        start, pos, depth = match.start(), match.end(), 1
        while depth:
            if global_decl[pos] == "{": depth += 1
            if global_decl[pos] == "}": depth -= 1
            pos += 1
        records.append({"id": "function:" + match.group(1), "kind": "function", "text": global_decl[start:pos]})
    # Include non-function global expressions, excluding const declaration lines.
    remainder = global_decl
    for record in records:
        remainder = remainder.replace(record["text"], "")
    remainder = re.sub(r"\bconst\s+int\s+[^;]+;", "", remainder)
    records.append({"id": "global:other", "kind": "declaration", "text": remainder})
    declarations = {}
    for block in re.findall(r"\bconst\s+int\s+([^;]+);", global_decl):
        declarations.update(re.findall(r"\b(\w+)\s*=\s*(\d+)\b", block))
    for template in root.findall("template"):
        name = template.findtext("name")
        locations = {loc.get("id"): loc.findtext("name") for loc in template.findall("location")}
        decl = template.findtext("declaration", "")
        if decl:
            records.append({"id": name + ":declaration", "kind": "declaration", "template": name, "text": decl})
        for loc in template.findall("location"):
            invariant = " && ".join(x.text or "" for x in loc.findall("label[@kind='invariant']"))
            records.append({"id": name + ":location:" + locations[loc.get("id")], "kind": "location",
                            "template": name, "location": locations[loc.get("id")], "invariant": invariant,
                            "committed": loc.find("committed") is not None, "urgent": loc.find("urgent") is not None})
        for i, edge in enumerate(template.findall("transition")):
            record = {"id": name + ":edge:" + str(i), "kind": "edge", "template": name,
                      "source": locations[edge.find("source").get("ref")], "target": locations[edge.find("target").get("ref")]}
            record.update({x.get("kind"): x.text or "" for x in edge.findall("label") if x.get("kind") != "comments"})
            records.append(record)
    records.append({"id": "queries", "kind": "query", "text": raw["queries"].decode()})
    lexical = {r["id"]: words(" ".join(str(v) for k, v in r.items()
                                if k in ("text", "guard", "invariant", "assignment", "synchronisation", "select"))) for r in records}
    rows = []
    for layer, values in candidate["source_parameters"].items():
        for name, value in values.items():
            if not re.match(r"^(D_|T_|J_|tau_)", name): continue
            symbol = layer + "_" + name
            if declarations.get(symbol) != value:
                raise ValueError(f"Declaration mismatch: {symbol}")
            refs = [r["id"] for r in records if symbol in lexical[r["id"]]]
            related_clocks = sorted(set().union(*(lexical[x] & clocks for x in refs)))
            # Qualified global names are unique. Local clock refs carry template scope;
            # a shared local name is conservatively included, never treated as one clock.
            clock_refs = [r["id"] for r in records if set(related_clocks) & lexical[r["id"]]]
            core = any("Obs" not in x and x != "queries" for x in refs)
            use = "core_or_boundary" if core else "observer_only" if refs else "declaration_only"
            rows.append({"parameter": layer + "." + name, "symbol": symbol, "value": int(value),
                         "unit": "abstract_model_unit", "usage": use, "direct_refs": refs,
                         "clock_names": related_clocks, "clock_refs": clock_refs,
                         "xml_lines": [i for i, line in enumerate(raw["model"].decode().splitlines(), 1) if symbol in words(line)],
                         **contracts["source"][layer + "." + name]})
    if len(rows) != 43 or {r["parameter"] for r in rows} != set(contracts["source"]):
        raise ValueError("Source timing coverage is not exactly 43")
    model_timings = {name for name in declarations if re.match(r"^(phy|mac|sdn|app)_(D_|T_|J_|tau_)", name)}
    if model_timings != {r["symbol"] for r in rows}:
        raise ValueError("Uninventoried or missing model timing declaration")
    if set(candidate["parameter_set"]) != set(contracts["integration"]):
        raise ValueError("Integration parameter_set coverage differs")
    for key in ("D_cmd", "D_bus", "T_input", "T_mac_tick", "T_demand", "T_complete"):
        if declarations.get("bus_" + key) != str(candidate["parameter_set"][key]):
            raise ValueError(f"Boundary constant mismatch: {key}")
    integration = [{"parameter": key, "value": val, **contracts["integration"][key]}
                   for key, val in candidate["parameter_set"].items()]
    inventory = {"evidence_class": "static_validation_not_model_checking", "inspected_commit": BASE,
                 "inputs": pinned, "historical_candidate_model_hash": candidate["model_hash"],
                 "time_scale_seconds": None, "source_timing_count": len(rows),
                 "integration_entry_count": len(integration), "source_timings": rows,
                 "integration": integration,
                 "method_limits": "Lexical references, not reachability or data-flow proof. Function refs retained; clock_refs conservatively include similarly named local clocks with explicit template scope. Declaration-only means no lexical use outside const declarations in selected XML/queries; no claim about other profiles."}
    lines = ["# Полный указатель временных параметров", "", "Сгенерировано audit.py из закреплённого XML; это статический разбор, не verification.", "", "| Параметр | Значение | Использование | Интервал / роль | Ограничение |", "|---|---:|---|---|---|"]
    for row in rows:
        cells = [row["parameter"], str(row["value"]), row["usage"], row["interval"], row["limit"]]
        lines.append("| " + " | ".join(c.replace("|", " / ").replace("\n", " ") for c in cells) + " |")
    lines += ["", "## Параметры интеграции", "", "| Поле | Значение | Роль / интервал | Ограничение |", "|---|---|---|---|"]
    for row in integration:
        cells = [row["parameter"], json.dumps(row["value"], ensure_ascii=False), row["interval"], row["limit"]]
        lines.append("| " + " | ".join(c.replace("|", " / ") for c in cells) + " |")
    output = {"timing-inventory.json": encoded(inventory),
              "parameter-table.md": ("\n".join(lines) + "\n").encode()}
    for group in ("phy", "mac", "sdn", "app", "Boundary", "global"):
        selected = [r for r in records if
                    (r.get("template", "").startswith(group + "_") if group != "global"
                     else "template" not in r)]
        output["model-index-" + group.lower() + ".json"] = encoded({
            "input_model_sha256": pinned["model"]["sha256"], "records": selected})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write only generated files in this evidence directory")
    args = parser.parse_args()
    output = build()
    for name, data in output.items():
        path = HERE / name
        if args.write:
            path.write_bytes(data)
        elif not path.exists() or path.read_bytes() != data:
            raise SystemExit(f"STALE OR MISSING: {name}")
    print("Static audit: 43 source timing rows; complete integration key coverage; pinned input hashes and generated bytes match. No UPPAAL execution.")


if __name__ == "__main__":
    main()
