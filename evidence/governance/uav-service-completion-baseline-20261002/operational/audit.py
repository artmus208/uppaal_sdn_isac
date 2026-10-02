#!/usr/bin/env python3
"""Static operational scope/seal audit; never grants activation or verdicts."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
PACKAGE = ROOT / "evidence/governance/uav-service-completion-baseline-20261002"
BASE = "efb6d6c0d936c2c62fbf902e383a144e6b616a0a"
MANIFEST = "manifests/baselines/uav-service-completion-r1.yaml"
COLLAB = "manifests/collaboration-v2.yaml"
PREFIX = "evidence/governance/uav-service-completion-baseline-20261002/operational/"

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])

def audit():
    decision = json.loads((PACKAGE / "operational/independent-decision.json").read_text())
    captured = json.loads((PACKAGE / "operational/github-decision.json").read_text())
    assert decision["github_comment_id"] == captured["id"] == 5946722646
    assert decision["decision_reference"] == captured["url"]
    assert decision["recorded_at_utc"] == captured["created_at"]
    assert decision["scientific_input_pins"] == json.loads((PACKAGE / "decision-pins.json").read_text())
    assert decision["A"] == "accepted_limited_P1_P2_applicability"
    assert decision["B"] == "accepted_exact_inputs_gate_1"
    assert decision["C"] == "pending_separate_postmerge_activation_decision"
    assert decision["D"] == "open_verdicts_no_universal_P3_R07_acceptance"
    assert (decision["N"], decision["processes"]) == (1, 51)
    digest = lambda value: hashlib.sha256(value).hexdigest()
    assert digest((PACKAGE / "proposed-operational.patch").read_bytes()) == decision["approved_patch_sha256"]
    manifest = (ROOT / MANIFEST).read_bytes()
    assert manifest == (PACKAGE / "proposed-baseline.yaml").read_bytes()
    assert digest(manifest) == decision["scientific_input_pins"]["proposal_manifest"]["sha256"]
    assert (ROOT / COLLAB).read_bytes() == git("show", BASE + ":" + COLLAB) + b"\n" + (PACKAGE / "proposed-selection.yaml").read_bytes()
    sealed = json.loads((PACKAGE / "artifact-hashes.json").read_text())["files"]
    for path, expected in sealed.items():
        assert digest((PACKAGE / path).read_bytes()) == expected, path
    # Committed and working changes, plus untracked files, must stay in this scope.
    changed = set(git("diff", "--name-only", BASE).decode().splitlines())
    changed.update(git("ls-files", "--others", "--exclude-standard").decode().splitlines())
    assert all(path in (MANIFEST, COLLAB) or path.startswith(PREFIX) for path in changed), sorted(changed)
    return {"check": "operational_static_audit_ok", "gate_1": "accepted_exact_inputs_by_issue_84_decision", "activation": "pending_separate_postmerge_decision", "manifest_sha256": digest(manifest), "sealed_proposal_files": len(sealed), "new_native_runs": 0, "query_verdicts": "all_11_open", "base_commit": BASE}

if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
