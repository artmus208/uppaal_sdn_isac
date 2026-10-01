"""Read saved evidence only; never connects to an engine or declares a query verdict."""
import csv
import gzip
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
MODEL = "5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385"
TRACE = "8186e1b68324ba288abe6249abdc73fa771400d95414d4bf77d2d1f9fdfbfcf7"
VERSION = "UPPAAL version 5.0.0 (rev. 714BA9DB36F49691), June 2023"

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def validate_cell(result, monitor, steps, mode):
    require(result["model_hash"] == MODEL and result["trace_hash"] == TRACE, "input hash")
    require(result["actual_engine_version"].startswith(VERSION + " -- server."), "engine version")
    require(result["property_verdict"] is None, "replay must not claim a query verdict")
    require((result["processes"], result["variables"], result["clocks"]) == (50, 255, 70), "system shape")
    require(monitor["native_status"] == "success" and monitor["process_tree_reaped"], "native lifecycle")
    require(monitor["runtime_seconds"] < 60 and monitor["peak_tree_sample_bytes"] < 2147483648, "resource bound")
    accepted = 68 if mode == "replay" else 67
    require(result["accepted_transitions"] == accepted, "accepted step count")
    # Failure records may follow the accepted prefix; identify accepted zone records.
    accepted_steps = [s for s in steps if "reachable_zone" in s]
    require([s["state_index"] for s in accepted_steps] == list(range(accepted + 1)), "accepted prefix indices")
    for step in accepted_steps:
        zone = step["reachable_zone"]
        require(len(zone) == 70 and all(len(row) == 70 for row in zone), "zone dimensions")
        require(all(zone[i][i] == 1 for i in range(70)), "empty or noncanonical zone")
        if step["state_index"]:
            require(step["edge_matches"] >= step["discrete_matches"] >= step["reachable_frontier"] >= 1, "successor matching")
    if mode == "replay":
        require(result["status"] == "replay_complete" and monitor["exit_code"] == 0, "positive replay")
        final = accepted_steps[-1]
        require(final["reachable_zone"][1][0] == 21 and final["reachable_zone"][0][1] == -19, "final #time is not exactly 10")
        require(final["selected"]["family_grant_0"] == 1 and final["selected"]["u0_mac_queue_q"] == 0, "service endpoint")
        require(accepted_steps[-2]["selected"]["u0_mac_queue_q"] == 1, "queue before service")
        require(all(s["selected"]["u0_mac_queue_overflow_seen"] == 0 for s in accepted_steps), "overflow along path")
    else:
        reason = "discrete_state_mismatch" if mode == "negative-discrete" else "clock_zone_disjoint"
        require(result["status"] == "rejected" and monitor["exit_code"] == 1, "negative control accepted")
        require(result["first_unavailable_state_index"] == 68 and result["reason"] == reason, "negative-control reason")
        require(result["control_expected_rejection"] is True, "negative control not expected")
    return {"mode": mode, "accepted_transitions": accepted, "status": result["status"], "run_id": monitor["run_id"]}

def audit(root=ROOT):
    root = Path(root)
    inventory = json.loads((root / "artifact-hashes.json").read_text())
    actual = {str(f.relative_to(root)) for f in root.rglob("*") if f.is_file() and "__pycache__" not in f.parts and f.name not in {"artifact-hashes.json", "audit-result.json"}}
    require(actual == set(inventory), "artifact inventory mismatch")
    for name, expected in inventory.items():
        require(digest((root / name).read_bytes()) == expected, "artifact hash: " + name)
    archive = json.loads((root / "lossless-archive.json").read_text())
    unpacked = {}
    for entry in archive["entries"]:
        packed = (root / entry["path"]).read_bytes()
        require(len(packed) == entry["size"] and digest(packed) == entry["sha256"], "archive hash")
        raw = (lzma.decompress if entry["codec"] == "xz" else gzip.decompress)(packed)
        require(len(raw) == entry["original_size"] and digest(raw) == entry["original_sha256"], "lossless archive")
        unpacked[entry["original_path"]] = raw
    provenance = json.loads((root / "native-002/provenance.json").read_text())
    for old_path, expected in provenance["hashes"].items():
        if old_path.startswith("/tmp/uppaal-replay-oct02/"):
            source = REPO / old_path.removeprefix("/tmp/uppaal-replay-oct02/")
            require(digest(source.read_bytes()) == expected, "executed source/input hash")
    results = []
    for mode in ("replay", "negative-discrete", "negative-clock"):
        folder = root / "native-002" / mode
        result = json.loads((folder / "result.json").read_text())
        monitor = json.loads((folder / "monitor.json").read_text())
        steps = [json.loads(line) for line in unpacked[f"native-002/{mode}/steps.jsonl"].splitlines()]
        samples = list(csv.DictReader((folder / "memory.csv").read_text().splitlines()))
        require(samples and max(int(row["tree_sample_bytes"]) for row in samples) == monitor["peak_tree_sample_bytes"], "memory peak accounting")
        hardware = json.loads((folder / "hardware.json").read_text(encoding="utf-8-sig"))
        require(hardware["available_ram_bytes"] >= 3221225472, "native RAM headroom")
        results.append(validate_cell(result, monitor, steps, mode))
    summary = json.loads((root / "native-002/native-summary.json").read_text())
    require(summary["total_wall_seconds"] >= summary["prior_native_wall_seconds"] + sum(c["runtime_seconds"] for c in summary["cells"]), "budget accounting excludes a cell")
    require(summary["total_wall_seconds"] < 300, "native budget")
    return {"status": "saved_evidence_consistent", "property_verdict": None, "final_time": 10, "cells": results, "artifacts_checked": len(inventory)}

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
