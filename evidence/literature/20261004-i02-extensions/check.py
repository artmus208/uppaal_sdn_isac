"""Offline I02 artifact audit. Needs bibtexparser 1.x; never runs a verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

import bibtexparser


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    sources = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    base = sources["base_commit"]
    inputs = {
        path: git_bytes("show", f"{base}:{path}")
        for path in sources["local_inputs"]
    }
    for path, data in inputs.items():
        if (ROOT / path).read_bytes() != data:
            raise ValueError(f"Local input differs from pinned base: {path}")

    old = bibtexparser.loads(inputs[sources["existing_bibliography"]].decode("utf-8"))
    new = bibtexparser.loads((HERE / "references.bib").read_text(encoding="utf-8"))
    old_keys = {entry["ID"] for entry in old.entries}
    new_keys = {entry["ID"] for entry in new.entries}
    assert len(new.entries) == len(new_keys) == len(sources["new_bibtex_keys"])
    assert new_keys == set(sources["new_bibtex_keys"])
    assert not old_keys & new_keys, "Duplicate integration bibliography key"
    assert set(sources["reused_bibtex_keys"]) <= old_keys
    for entry in new.entries:
        source = next(s for s in sources["sources"] if s.get("bibtex_key") == entry["ID"])
        assert entry["doi"] == source["doi"]
        assert entry["year"] == str(source["year"])
        assert entry["pages"] == source["pages"]
        assert entry["author"] and entry["title"]
    snippet = (HERE / "proposed-text.tex").read_text(encoding="utf-8")
    cited = {key.strip() for group in re.findall(r"\\cite\{([^}]+)\}", snippet)
             for key in group.split(",")}
    assert cited == new_keys | set(sources["reused_bibtex_keys"])

    model_path = "evidence/instantiation/uav-service-completion-candidate/model.xml"
    assert sha256(inputs[model_path]) == "b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02"
    model = ET.fromstring(inputs[model_path])
    strict = [label.text for label in model.findall(".//label[@kind='guard']")
              if "c82_sample_age<5" in (label.text or "")]
    assert strict, "The cited strict freshness guard must exist"
    scope = HERE.relative_to(ROOT).as_posix() + "/"
    changed = git_bytes("diff", "--name-only", base, "--").decode().splitlines()
    untracked = git_bytes("ls-files", "--others", "--exclude-standard").decode().splitlines()
    assert all(path.startswith(scope) for path in changed + untracked), "Out-of-scope diff"
    print(json.dumps({
        "check_type": "static_artifact_audit_not_model_checking",
        "status": "success",
        "base_commit": base,
        "new_bibtex_keys": sorted(new_keys),
        "resolved_citation_keys": sorted(cited),
        "strict_freshness_guard_occurrences": len(strict),
        "input_sha256": {path: sha256(data) for path, data in inputs.items()},
        "artifact_sha256": {name: sha256((HERE / name).read_bytes()) for name in
                            ["README.md", "references.bib", "proposed-text.tex", "sources.json", "check.py"]},
        "scope": scope,
        "limitations": "Checks structure, hashes, citation resolution and a local XML fact; not source interpretation, typesetting or a behavioral property."
    }, indent=2))


if __name__ == "__main__":
    main()
