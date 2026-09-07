"""P2 exact-source inventory. Stdlib only; never invokes a verifier.

--write creates inventory.json and inventory.md once. --check recomputes both.
This deliberately supports the explicit, zero-argument process declarations in
the pinned source surfaces; unsupported syntax fails instead of being guessed.
"""
import argparse
import hashlib
import importlib
import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BASE = "7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb"
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
XML_PATHS = {
    "phy": ".uppaal_mcp_workspace/phy_generated/model.xml",
    "mac": ".uppaal_mcp_workspace/mac_generated/model.xml",
    "sdn": ".uppaal_mcp_workspace/sdn_generated_smoke/model.xml",
    "app": ".uppaal_mcp_workspace/Application_service_layer_uppaal.xml",
}
TEX_PATHS = [
    "levels_tex/PHY_level_formalization_reviewed-2026-06-06-143000.tex",
    "levels_tex/MAC_resource_scheduling_formalization.tex",
    "levels_tex/SDN_RIC_control_plane_formalization.tex",
    "levels_tex/Application_service_layer_formalization.tex",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clean_comments(text):
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)


def model_record(data, origin, detailed=False, queries=None):
    root = ET.fromstring(data)
    templates = {}
    for t in root.findall("template"):
        name = t.findtext("name")
        if name in templates:
            raise ValueError(f"duplicate template: {origin}: {name}")
        locs = {loc.get("id"): {
            "name": loc.findtext("name") or loc.get("id"),
            "invariants": [l.text for l in loc.findall("label") if l.get("kind") == "invariant"],
            "urgent": loc.find("urgent") is not None,
            "committed": loc.find("committed") is not None,
        } for loc in t.findall("location")}
        edges = []
        for n, e in enumerate(t.findall("transition"), 1):
            edges.append({"edge": n, "source": locs[e.find("source").get("ref")]["name"],
                          "target": locs[e.find("target").get("ref")]["name"],
                          **{l.get("kind"): l.text or "" for l in e.findall("label")
                             if l.get("kind") != "comments"}})
        initial = t.find("init")
        templates[name] = {
            "parameters": t.findtext("parameter") or "",
            "declarations": t.findtext("declaration") or "",
            "initial": locs[initial.get("ref")]["name"] if initial is not None else None,
            "location_count": len(locs), "transition_count": len(edges),
            "locations": list(locs.values()), "edges": edges,
        }
    system = clean_comments(root.findtext("system") or "")
    instances = {}
    for statement in filter(None, (s.strip() for s in system.split(";"))):
        if statement.startswith("system "):
            active = [s.strip() for s in statement[7:].split(",")]
        else:
            m = re.fullmatch(r"(\w+)\s*=\s*(\w+)\(\s*\)", statement)
            if not m:
                raise ValueError(f"unsupported instantiation: {origin}: {statement}")
            if m[1] in instances:
                raise ValueError(f"duplicate process: {m[1]}")
            instances[m[1]] = m[2]
    if set(active) != set(instances) or len(active) != len(set(active)):
        raise ValueError(f"incomplete system definition: {origin}")
    for template in instances.values():
        if template not in templates or templates[template]["parameters"]:
            raise ValueError(f"unsupported template binding: {origin}: {template}")
    declaration = root.findtext("declaration") or ""
    channels = {}
    for m in re.finditer(r"\b(?:(urgent)\s+)?(?:(broadcast)\s+)?chan\s+([^;]+);", clean_comments(declaration)):
        for channel in m[3].split(","):
            channel = channel.strip()
            if not re.fullmatch(r"\w+", channel) or channel in channels:
                raise ValueError(f"unsupported or duplicate channel: {origin}: {channel}")
            channels[channel] = {"kind": "broadcast" if m[2] else "binary", "urgent": bool(m[1]),
                                 "senders": [], "receivers": []}
    for instance, template in instances.items():
        for edge in templates[template]["edges"]:
            sync = edge.get("synchronisation", "").strip()
            if sync:
                m = re.fullmatch(r"(\w+)([!?])", sync)
                if not m or m[1] not in channels:
                    raise ValueError(f"undeclared/unsupported synchronization: {origin}: {sync}")
                channels[m[1]]["senders" if m[2] == "!" else "receivers"].append(
                    {"process": instance, "edge": edge["edge"], "source": edge["source"], "target": edge["target"]})
    clocks = {}
    for scope, decl in [("global", declaration)] + [(n, t["declarations"]) for n, t in templates.items()]:
        clocks[scope] = [name.strip() for m in re.finditer(r"\bclock\s+([^;]+);", clean_comments(decl))
                         for name in m[1].split(",")]
    record = {"origin": origin, "model_hash": sha(data), "instances": instances,
              "system_order": active, "process_count": len(active),
              "location_count": sum(templates[t]["location_count"] for t in instances.values()),
              "transition_count": sum(templates[t]["transition_count"] for t in instances.values()),
              "global_declarations": declaration, "clocks": clocks, "channels": channels,
              "templates": templates}
    if queries is not None:
        record["query_hash"] = sha(queries.encode("utf-8"))
    if not detailed:
        record["templates"] = {n: {k: v for k, v in t.items() if k not in ("edges", "locations")}
                               for n, t in templates.items()}
    return record


def build():
    paths = set(XML_PATHS.values()) | set(TEX_PATHS)
    paths.update(["AGENTS.md", "CONTRIBUTING.md", "manifests/v1.md", "manifests/collaboration-v1.yaml",
                  "manifests/baselines/reviewer-r1.yaml", "src/uppaal_mcp/layers.py", "src/uppaal_mcp/layout_core.py",
                  "evidence/validation/20260907-p1/validation-report.md",
                  "evidence/validation/20260907-p1/inventory.json"])
    for layer in ("phy", "mac", "sdn"):
        for module in ("__init__", "defaults", "alpha", "ir", "generator", "layout", "property_pack"):
            paths.add(f"src/uppaal_mcp/{layer}/{module}.py")
    sources = {}
    for p in sorted(paths):
        data = (ROOT / p).read_bytes()
        committed = subprocess.check_output(["git", "show", f"{BASE}:{p}"], cwd=ROOT)
        if data != committed:
            raise ValueError(f"source bytes differ from pinned commit: {p}")
        sources[p] = {"sha256": sha(data), "git_blob_sha": subprocess.check_output(
            ["git", "rev-parse", f"{BASE}:{p}"], cwd=ROOT, text=True).strip()}
    models = {}
    for layer in ("phy", "mac", "sdn"):
        generator = importlib.import_module(f"uppaal_mcp.{layer}.generator")
        modes = ["with_observers", "minimal"]
        if layer in ("phy", "sdn"):
            modes += ["open_system", "with_extended_observers" if layer == "phy" else "with_optional_sec"]
        for mode in modes:
            kwargs = {"mode": mode, "layout": "readable"}
            model = generator.generate_uppaal_model(**kwargs)
            key = f"generated:{layer}:{mode}"
            models[key] = model_record(model.model_xml.encode("utf-8"), key,
                                       detailed=mode == "with_observers", queries=model.queries)
            models[key]["generation"] = {"module": generator.__name__, "kwargs": kwargs,
                                         "profile": model.profile, "system_mode": model.system_mode}
    for layer, p in XML_PATHS.items():
        models[f"stored:{layer}"] = model_record((ROOT / p).read_bytes(), p, detailed=layer == "app")
    cross = {}
    for layer in ("phy", "mac", "sdn", "app"):
        key = "stored:app" if layer == "app" else f"generated:{layer}:with_observers"
        for name, channel in models[key]["channels"].items():
            cross.setdefault(name, {})[layer] = {
                "kind": channel["kind"],
                "senders": sorted({e["process"] for e in channel["senders"]}),
                "receivers": sorted({e["process"] for e in channel["receivers"]})}
    cross = {n: v for n, v in sorted(cross.items()) if len(v) > 1}
    return {"schema_version": 1, "issue": 17, "source_commit": BASE,
            "evidence_class": "source_audit_and_static_xml_inventory_not_verification",
            "coverage": "four stored XMLs and ten explicitly selected default-profile generator modes; no custom profiles or TeX parser",
            "sources": sources, "models": models, "same_name_cross_layer_channels": cross,
            "channel_kind_conflicts": [n for n, v in cross.items() if len({s["kind"] for s in v.values()}) > 1]}


def render(data):
    lines = ["# Reproducible P2 source inventory", "", f"Source commit: `{BASE}`. Issue #17.", "",
             "Counts below are XML syntax counts, not reachable states or verification results.", "",
             "| Surface | Processes | Locations | Transitions |", "|---|---:|---:|---:|"]
    for key, model in data["models"].items():
        lines.append(f"| {key} | {model['process_count']} | {model['location_count']} | {model['transition_count']} |")
    lines += ["", "## Instantiated templates", ""]
    for key in ("generated:phy:with_observers", "generated:mac:with_observers", "generated:sdn:with_observers", "stored:app"):
        m = data["models"][key]
        lines += [f"### {key}", "", "| Process | Template | Initial | Locations | Transitions |",
                  "|---|---|---|---:|---:|"]
        for name in m["system_order"]:
            t = m["templates"][m["instances"][name]]
            lines.append(f"| {name} | {m['instances'][name]} | {t['initial']} | {t['location_count']} | {t['transition_count']} |")
        lines.append("")
    lines += ["## Same-name cross-layer channels", "", "Endpoint presence is syntactic; no enabledness or compatibility is inferred.", "",
              "| Channel | Layer | Kind | Senders | Receivers |", "|---|---|---|---|---|"]
    for name, layers in data["same_name_cross_layer_channels"].items():
        for layer, entry in layers.items():
            lines.append(f"| {name} | {layer} | {entry['kind']} | {', '.join(entry['senders']) or 'none'} | {', '.join(entry['receivers']) or 'none'} |")
    lines += ["", "Channel-kind conflicts: " + ", ".join(f"`{n}`" for n in data["channel_kind_conflicts"]) + ".", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = build()
    artifacts = {"inventory.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n", "inventory.md": render(data)}
    if args.write:
        if any((HERE / name).exists() for name in artifacts):
            raise FileExistsError("inventory outputs already exist; refusing overwrite")
        for name, content in artifacts.items():
            (HERE / name).write_bytes(content.encode("utf-8"))
    else:
        for name, content in artifacts.items():
            if (HERE / name).read_bytes() != content.encode("utf-8"):
                raise ValueError(f"reproduction mismatch: {name}")
    print(f"{len(data['sources'])} pinned source files; {len(data['models'])} XML surfaces; "
          f"{len(data['channel_kind_conflicts'])} cross-layer channel-kind conflicts. Static evidence only.")


if __name__ == "__main__":
    main()
