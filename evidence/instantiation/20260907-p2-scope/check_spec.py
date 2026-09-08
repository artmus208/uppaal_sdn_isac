"""Check P2 vector/source partition and regenerate the scheduler edge table.

These checks establish consistency of this specification's references and counts,
not correctness of the proposed adapters or formal model verification.
"""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def table(model):
    template = model["templates"][model["instances"]["A_SCH"]]
    lines = ["# Existing A_SCH edge table", "", "Generated from the pinned default MAC XML inventory. Static inspection only.", "",
             "| Edge | Source | Target | Guard | Synchronization | Update |",
             "|---:|---|---|---|---|---|"]
    def cell(text):
        return str(text).replace("|", "&#124;").replace("\n", " ") or "—"
    for edge in template["edges"]:
        lines.append("| " + " | ".join(cell(edge.get(k, "")) for k in
                     ("edge", "source", "target", "guard", "synchronisation", "assignment")) + " |")
    return "\n".join(lines) + "\n"


def check(vector, inv):
    if vector["source_commit"] != inv["source_commit"]:
        raise ValueError("vector/inventory source mismatch")
    consumed = {}
    names = set()
    counts = {"core": 0, "boundary": 0, "observers": 0}
    for group in vector["groups_in_system_order"]:
        key = "boundary" if group["group"] == "boundary" else "observers" if group["group"].startswith("obs_") else "core"
        counts[key] += len(group["retain"])
        for name in group["retain"]:
            qualified = f"{group['group']}_{name}_0"
            if qualified in names:
                raise ValueError(f"duplicate qualified process: {qualified}")
            names.add(qualified)
            if group["source"] != "new_templates_required":
                if name not in inv["models"][group["source"]]["instances"]:
                    raise ValueError(f"unknown process: {name}")
                retained = consumed.setdefault(group["source"], set())
                if name in retained:
                    raise ValueError(f"source process reused across groups: {name}")
                retained.add(name)
    for source, retained in consumed.items():
        removed = vector["remove"][source]
        original = set(inv["models"][source]["instances"])
        if len(removed) != len(set(removed)) or retained.intersection(removed) or retained.union(removed) != original:
            raise ValueError(f"retained/removed partition mismatch: {source}")
    counts["total"] = sum(counts.values())
    if counts != vector["expected_process_counts"]:
        raise ValueError(f"process count mismatch: {counts}")
    if vector["entities"]["uav_devices_subset"] > vector["entities"]["devices_total"]:
        raise ValueError("UAVs exceed total device count")
    if vector["bindings"]["device_0"]["serving_bs"] >= vector["entities"]["base_stations"]:
        raise ValueError("BS binding out of range")
    for field in ("D_cmd", "D_bus", "T_input", "T_mac_tick", "T_demand", "T_complete"):
        if not isinstance(vector["parameter_policy"][field], int) or vector["parameter_policy"][field] <= 0:
            raise ValueError(f"invalid abstract timing: {field}")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-table", action="store_true")
    args = parser.parse_args()
    inv = json.loads((HERE / "inventory.json").read_text(encoding="utf-8"))
    vector = json.loads((HERE / "instance-vector.json").read_text(encoding="utf-8"))
    counts = check(vector, inv)
    rendered = table(inv["models"]["generated:mac:with_observers"]).encode("utf-8")
    path = HERE / "scheduler-edges.md"
    if args.write_table:
        with path.open("xb") as stream:
            stream.write(rendered)
    elif path.read_bytes() != rendered:
        raise ValueError("scheduler edge table differs from inventory")
    # Adversarial mutations check that key contract errors cannot pass silently.
    import copy
    bad = copy.deepcopy(vector)
    bad["groups_in_system_order"][0]["retain"].append("missing_process")
    bad_count = copy.deepcopy(vector)
    bad_count["expected_process_counts"]["total"] += 1
    bad_partition = copy.deepcopy(vector)
    bad_partition["remove"]["stored:app"].append("Req")
    for invalid in (bad, bad_count, bad_partition):
        try:
            check(invalid, inv)
        except ValueError:
            continue
        raise AssertionError("invalid vector was accepted")
    print(f"Candidate vector: {counts}; source partitions and scheduler table consistent; "
          "three invalid-vector probes rejected. No integrated model or verification checked.")


if __name__ == "__main__":
    main()
