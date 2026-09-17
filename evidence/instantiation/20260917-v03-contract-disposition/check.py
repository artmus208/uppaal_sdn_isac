"""Read-only byte provenance, XML anchors and complete 43/14 coverage check."""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def git_bytes(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    provenance = json.loads((HERE / "inputs.json").read_text())
    for record in provenance["inputs"]:
        data = git_bytes(record["commit"], record["path"])
        require(hashlib.sha256(data).hexdigest() == record["sha256"], record["path"])
        if record["commit"] == provenance["base_commit"]:
            require((ROOT / record["path"]).read_bytes() == data,
                    "Working input drift: " + record["path"])
    inventory = json.loads(git_bytes(provenance["supplement_commit"],
        "evidence/validation/20260917-v03-timing/timing-inventory.json"))
    coverage = json.loads((HERE / "coverage.json").read_text())
    for key, count in (("source_timings", 43), ("integration", 14)):
        actual = coverage[key]
        expected = {row["parameter"]: row for row in inventory[key]}
        require(len(actual) == count == len(expected), "Wrong coverage count: " + key)
        require({row["parameter"] for row in actual} == set(expected),
                "Missing/duplicate coverage: " + key)
        for row in actual:
            original = expected[row["parameter"]]
            require(row["value"] == original["value"], "Changed parameter value")
            require(bool(row["reason"]) and bool(row["disposition"]), "Empty disposition")
            if key == "source_timings":
                require(row["usage"] == original["usage"], "Changed usage")
                require(row["source_refs"] == original["direct_refs"], "Changed references")
    xml_path = next(r["path"] for r in provenance["inputs"] if r["path"].endswith(".xml"))
    tree = ET.fromstring(git_bytes(provenance["base_commit"], xml_path))
    templates = {t.findtext("name"): t for t in tree.findall("template")}
    anchors = json.loads((HERE / "source-anchors.json").read_text())
    require(len(anchors) == 9, "Wrong anchor template count")
    for saved in anchors:
        name = saved["template"]
        t = templates[name]
        names = {l.get("id"): l.findtext("name") for l in t.findall("location")}
        locations = [{"name": l.findtext("name"),
                      "invariant": l.findtext("label[@kind='invariant']", "")}
                     for l in t.findall("location")]
        edges = [{"id": f"{name}:edge:{i}",
                  "from": names[tr.find("source").get("ref")],
                  "to": names[tr.find("target").get("ref")],
                  **{l.get("kind"): l.text for l in tr.findall("label")}}
                 for i, tr in enumerate(t.findall("transition"))]
        require(locations == saved["locations"] and edges == saved["edges"],
                "Source anchors differ: " + name)
    print("Static check: pinned bytes/hashes, 9 XML templates, 43/14 coverage match.")
    print("Contract correctness, reachability and UPPAAL results are not checked.")


if __name__ == "__main__":
    main()
