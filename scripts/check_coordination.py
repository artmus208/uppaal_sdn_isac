"""Dependency-free structural checks for GitHub coordination artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERRORS: list[str] = []


def read_required(path: Path, root: Path = ROOT) -> str:
    if not path.is_file():
        ERRORS.append(f"missing required file: {path.relative_to(root)}")
        return ""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        ERRORS.append(f"empty required file: {path.relative_to(root)}")
    if "\t" in text:
        ERRORS.append(f"tab indentation is not allowed: {path.relative_to(root)}")
    return text


def require_tokens(label: str, text: str, tokens: list[str]) -> None:
    for token in tokens:
        if token not in text:
            ERRORS.append(f"{label}: missing {token!r}")


def check_run_storage(text: str) -> list[str]:
    """Check the canonical mapping and its containment without a YAML dependency."""
    errors = []
    expected = {"P3": "evidence/verification/runs/<run_id>/",
                "P4": "evidence/scalability/runs/<run_id>/"}
    contract = re.search(r"(?ms)^run_evidence_contract:\n(.*?)(?=^\S|\Z)", text)
    block = contract.group(1) if contract else ""
    mapping = re.search(r"(?ms)^  storage_pattern_by_workstream:\n((?:    .*\n)+)", block)
    if not mapping:
        return ["run storage: missing storage_pattern_by_workstream"]
    entries = re.findall(r'^    (P[0-9]+): "([^"\n]+)"$', mapping.group(1), re.M)
    if len(entries) != 2 or dict(entries) != expected:
        errors.append("run storage: require exactly the disjoint canonical P3/P4 patterns")
    if re.search(r"(?m)^  storage_pattern:", block):
        errors.append("run storage: obsolete shared storage_pattern is forbidden")
    for stream, pattern in expected.items():
        match = re.search(rf"(?ms)^  {stream}:\n(.*?)(?=^  \S|^\S|\Z)", text)
        section = match.group(1) if match else ""
        scope = re.search(r"(?ms)^    write_scope:\n((?:      - .*\n)+)", section)
        root = pattern.split("runs/")[0]
        if not scope or f"      - {root}**\n" not in scope.group(1):
            errors.append(f"run storage: {stream} pattern is outside its write scope")
    return errors


def check_baseline_state(text: str) -> list[str]:
    """Reject inconsistent freeze flags without claiming a hash audit."""
    def section(name):
        match = re.search(rf"(?ms)^{name}:\n(.*?)(?=^\S|\Z)", text)
        return match.group(1) if match else ""
    def field(block, name):
        match = re.search(rf"(?m)^  {name}: ([^\n]+)$", block)
        return match.group(1) if match else None
    meta, gate = section("metadata"), section("gate_1")
    state = (field(meta, "status"), field(meta, "frozen"),
             field(gate, "status"), field(gate, "passed"))
    if state not in (("candidate", "false", "pending", "false"),
                     ("frozen", "true", "accepted", "true")):
        return ["baseline: inconsistent candidate/frozen and Gate 1 flags"]
    if field(meta, "id") != "reviewer-r1-candidate":
        repo = section("repository")
        if field(repo, "worktree_dirty_at_capture") != "false" or field(repo, "commit_is_exact_snapshot") != "true":
            return ["baseline: supersession requires exact clean committed inputs"]
        if field(gate, "P1_accepted") != "true" or field(gate, "P2_accepted") != "true":
            return ["baseline: supersession requires accepted P1/P2"]
    return []


def yaml_block(text: str, name: str, indent: int = 0) -> str:
    """Extract one block from the repository's deliberately simple YAML layout."""
    match = re.search(
        rf"(?ms)^{' ' * indent}{re.escape(name)}:\n(.*?)(?=^ {{0,{indent}}}\S|\Z)", text
    )
    return match.group(1) if match else ""


def inline_ids(block: str, field: str, indent: int) -> list[str]:
    match = re.search(rf"(?m)^{' ' * indent}{re.escape(field)}: \[([^\]\n]*)\]$", block)
    return [v.strip() for v in match.group(1).split(",") if v.strip()] if match else []


def local_document(root: Path, value: object) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError(f"expected repository-relative document path: {value!r}")
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"missing or outside-repository document: {value!r}")
    return path


def current_configuration(root: Path) -> dict:
    """Resolve the configured contract. Never infer activation or fall back to v1."""
    data = json.loads((root / "manifests/current.json").read_text(encoding="utf-8"))
    required = {"schema_version", "scientific_plan", "collaboration_manifest",
                "baseline_manifest", "migration_map", "activation_issue", "contributing_guide"}
    if not isinstance(data, dict) or set(data) != required or type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("current pointer has unsupported schema or fields")
    for key in required - {"schema_version", "activation_issue"}:
        local_document(root, data[key])
    if not isinstance(data["activation_issue"], str) or not re.fullmatch(
        r"https://github\.com/artmus208/uppaal_sdn_isac/issues/[1-9][0-9]*", data["activation_issue"]
    ):
        raise ValueError("current pointer requires an activation Issue reference")
    return data


def check_contract(root: Path, config: dict, collaboration: str, migration: str) -> list[str]:
    errors = []
    meta = yaml_block(collaboration, "metadata")
    for key, expected in (("scientific_plan", config["scientific_plan"]),
                          ("baseline_manifest", config["baseline_manifest"]),
                          ("contributing_guide", config["contributing_guide"]),
                          ("coordination_pointer", "manifests/current.json")):
        if not re.search(rf"(?m)^  {key}: {re.escape(expected)}$", meta):
            errors.append(f"current contract: metadata {key} disagrees with pointer")
    if f"  issue: {config['activation_issue']}\n" not in yaml_block(collaboration, "activation"):
        errors.append("current contract: activation Issue disagrees with pointer")

    expected = {
        **{f"C{i:02}": "P3" for i in range(1, 7)},
        **{f"R{i:02}": "P2" for i in (1, 2, 5, 6)},
        "R03": "P4", "R04": "P4", "R07": "P5",
        **{f"V{i:02}": "P1" for i in range(1, 6)},
        "I01": "P6", "I02": "P6", "I03": "P7", "I04": "P7", "I05": "P7", "I06": "P8",
        "D01": "P9b",
    }
    workstreams = yaml_block(collaboration, "workstreams")
    actual = []
    for owner in re.findall(r"(?m)^  (P[0-9]+[ab]?):$", workstreams):
        block = yaml_block(workstreams, owner, 2)
        actual.extend((ident, owner) for ident in inline_ids(block, "atomic_comment_ids", 4))
        actual.extend((ident, owner) for ident in inline_ids(block, "conditional_comment_ids", 4))
    if len(actual) != len(expected) or dict(actual) != expected:
        errors.append("current contract: stable IDs or primary ownership changed")
    rows = re.findall(r"(?m)^\| ([CRVID][0-9]{2}) \| (P[0-9]+[ab]?)(?: \(условно\))? \|", migration)
    if len(rows) != len(expected) or dict(rows) != expected:
        errors.append("migration map: stable IDs or primary ownership changed")
    if "| D01 | P9b (условно) |" not in migration:
        errors.append("migration map: D01 must remain conditional")
    conditional = yaml_block(yaml_block(collaboration, "review_comment_ids"), "deferred_conditional_ownership", 2)
    if "default_status: deferred" not in conditional or "owner_when_activated: P9b" not in conditional:
        errors.append("current contract: D01 conditional ownership is missing")

    p3 = yaml_block(workstreams, "P3", 2)
    milestones = yaml_block(p3, "milestones", 4)
    core = yaml_block(milestones, "P3_core_evidence_accepted", 6)
    complete = yaml_block(milestones, "P3_complete", 6)
    if (inline_ids(core, "covers", 8) != [f"C{i:02}" for i in range(1, 6)]
            or inline_ids(core, "accept_after", 8) != ["gate_1"]
            or inline_ids(core, "unlocks", 8) != ["P5_final_acceptance"]
            or inline_ids(complete, "covers", 8) != [f"C{i:02}" for i in range(1, 7)]
            or inline_ids(complete, "accept_after", 8) != ["P4"]):
        errors.append("current contract: P3 core/complete milestone dependency changed")
    for owner, field, expected_dependencies in (
        ("P5", "accept_after", ["P3_core_evidence_accepted", "gate_1"]),
        ("P9a", "start_after", [f"P{i}" for i in range(1, 8)]),
        ("P9b", "start_after", ["P8", "gate_2"]),
        ("P4", "series_requires", ["accepted_configuration_family", "gate_1"]),
    ):
        if inline_ids(yaml_block(workstreams, owner, 2), field, 4) != expected_dependencies:
            errors.append(f"current contract: {owner} {field} dependency changed")

    historical = yaml_block(collaboration, "historical_inputs")
    for key, relative in (("scientific_plan", "manifests/v1.md"),
                          ("collaboration_contract", "manifests/collaboration-v1.yaml"),
                          ("baseline_manifest", "manifests/baselines/reviewer-r1.yaml"),
                          ("contributing_guide", "CONTRIBUTING.md")):
        block = yaml_block(historical, key, 2)
        match = re.search(r"(?m)^    sha256: ([0-9a-f]{64})$", block)
        if f"    path: {relative}\n" not in block or not match:
            errors.append(f"historical inputs: missing exact pin for {key}")
            continue
        try:
            observed = hashlib.sha256(local_document(root, relative).read_bytes()).hexdigest()
            if observed != match.group(1):
                errors.append(f"historical inputs: hash mismatch for {relative}")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def structural_checks(root: Path = ROOT) -> int:
    ERRORS.clear()
    try:
        config = current_configuration(root)
    except (OSError, ValueError) as exc:
        print(f"ERROR: current coordination pointer: {exc}", file=sys.stderr)
        return 1
    issue = read_required(root / ".github/ISSUE_TEMPLATE/workstream.yml", root)
    pr = read_required(root / ".github/PULL_REQUEST_TEMPLATE.md", root)
    owners = read_required(root / ".github/CODEOWNERS", root)
    workflow = read_required(root / ".github/workflows/ci.yml", root)
    agent_rules = read_required(root / "AGENTS.md", root)
    contributing = read_required(root / "CONTRIBUTING.md", root)
    current_guide = read_required(root / config["contributing_guide"], root)
    scientific_plan = read_required(root / config["scientific_plan"], root)
    collaboration = read_required(root / config["collaboration_manifest"], root)
    baseline = read_required(root / config["baseline_manifest"], root)
    migration = read_required(root / config["migration_map"], root)
    ERRORS.extend(check_contract(root, config, collaboration, migration))

    expected_ids = [
        "workstream",
        "problem",
        "atomic_comment_ids",
        "baseline_manifest",
        "baseline_sha",
        "inputs",
        "write_scope",
        "outputs",
        "dependencies",
        "acceptance",
        "owner",
        "reviewer",
        "evidence_class",
        "evidence_requirements",
    ]
    found_ids = re.findall(r"(?m)^    id: ([a-z0-9_-]+)$", issue)
    if len(found_ids) != len(set(found_ids)):
        ERRORS.append("issue form: component IDs must be unique")
    for component_id in expected_ids:
        if component_id not in found_ids:
            ERRORS.append(f"issue form: missing component id {component_id!r}")
        block_match = re.search(
            rf"(?ms)^  - type: [a-z]+\n    id: {re.escape(component_id)}\n(.*?)(?=^  - type: |\Z)",
            issue,
        )
        if block_match and not re.search(
            r"(?m)^    validations:\n      required: true$", block_match.group(0)
        ):
            ERRORS.append(f"issue form: {component_id!r} must be required")

    workstreams = [
        "P0 — Baseline (candidate → frozen)",
        "P1 — Validation",
        "P2 — Instantiation and abstraction",
        "P3 — Verification",
        "P4 — Scalability",
        "P5 — End-to-end scenarios (RELATED; accept after P3)",
        "P6 — Literature",
        "P7 — Figures",
        "P9a — Draft integration",
        "P8 — Language and terminology",
        "P9b — Final integration and closure",
    ]
    require_tokens("issue form", issue, [f"- {item}" for item in workstreams])
    require_tokens(
        "issue form",
        issue,
        [
            "C01-C06",
            "R01-R07",
            "V01-V05",
            "I01-I06",
            "D01",
            "N/A",
            "P5 acceptance must depend on accepted P3 evidence",
            "Every workstream PR targets `read`",
        ],
    )

    require_tokens(
        "pull request template",
        pr,
        [
            "## Coordination",
            "Atomic review-comment IDs",
            "Baseline manifest/ID/SHA-256",
            "Baseline commit SHA",
            "Head commit SHA",
            "Source branch",
            "Target branch",
            "## Scope",
            "## Tests and acceptance",
            "## Evidence",
            "## Handoff",
            "## Checklist",
        ],
    )

    active_owner_lines = [
        line.strip() for line in owners.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]
    if "* @artmus208" not in active_owner_lines:
        ERRORS.append("CODEOWNERS: missing repository-wide @artmus208 ownership")
    handles = set(re.findall(r"@[A-Za-z0-9-]+", "\n".join(active_owner_lines)))
    unexpected_handles = sorted(handles - {"@artmus208"})
    if unexpected_handles:
        ERRORS.append(f"CODEOWNERS: unknown handles: {', '.join(unexpected_handles)}")

    require_tokens(
        "CI workflow",
        workflow,
        [
            'python-version: "3.12"',
            "python scripts/check_coordination.py",
            "python -m pip install .",
            "python -m unittest discover -s tests -v",
            "contents: read",
        ],
    )

    require_tokens(
        "agent rules",
        agent_rules,
        [
            "manifests/current.json",
            config["collaboration_manifest"],
            "codex/<account-id>/<issue-number>-<deliverable-slug>",
            "P9a Integration draft",
            "P8 Language",
            "P9b Final assembly",
            "N/A — coordination-only",
        ],
    )
    require_tokens(
        "contributing guide",
        contributing,
        [
            "https://learn.chatgpt.com/docs/projects",
            "https://learn.chatgpt.com/docs/environments/git-worktrees",
            "Target branch: read",
            "integration PR: `read` → `main`",
            "source_hash",
            "generator_hash",
        ],
    )
    require_tokens(
        "scientific plan", scientific_plan,
        ["P9a Integration draft", "P9b Final assembly", "P3_core_evidence_accepted",
         "P3_complete", "query_hash", "claim_scope", "direct_model_checking",
         "mathematical_argument", "reduction_with_transfer", "simulation",
         "external_validation", "static_validation", "Решения при неполной информации"],
    )
    require_tokens("issue form", issue, ["manifests/current.json"])
    require_tokens("pull request template", pr, ["manifests/current.json"])
    require_tokens("current contributing guide", current_guide, ["manifests/current.json", config["scientific_plan"]])
    require_tokens("collaboration v2", collaboration,
                   ['schema_version: "2.0"', "status: configured", "configured_is_not_activated: true",
                    "uncertainty_policy:", "claim_evidence_contract:", "family_feasibility:",
                    "mandatory_dependency_change: requires_explicit_reviewer_integrator_disposition"])
    require_tokens(
        "collaboration manifest",
        collaboration,
        [
            "system: github_issues",
            "name: main",
            "name: read",
            "class: RELATED",
            "P3_core_evidence_accepted",
            "P3_complete",
            "accept_after: [P4]",
            "manuscript_merge_rule: Only P9a and P9b",
            "coordination-only",
            "status/accepted",
        ],
    )
    require_tokens("baseline manifest", baseline,
                   ["integrated_model:", "policy: record_hardware_per_run"])
    ERRORS.extend(check_baseline_state(baseline))

    # Baseline identity belongs to the historical plan pinned by that baseline,
    # independently of the plan selected by the operational pointer.
    plan_hash_match = re.search(
        r"(?m)^  scientific_plan:\n    path: ([^\n]+)\n    sha256: ([0-9a-f]{64})$", baseline
    )
    if not plan_hash_match:
        ERRORS.append("baseline manifest: missing historical scientific-plan SHA-256")
    else:
        try:
            historical_plan = local_document(root, plan_hash_match.group(1))
            actual_plan_hash = hashlib.sha256(historical_plan.read_bytes()).hexdigest()
            if plan_hash_match.group(2) != actual_plan_hash:
                ERRORS.append("baseline manifest: historical scientific-plan SHA-256 is stale")
        except ValueError as exc:
            ERRORS.append(str(exc))
    ERRORS.extend(check_run_storage(collaboration))
    if ERRORS:
        for error in ERRORS:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Configured coordination: {config['scientific_plan']} / {config['collaboration_manifest']}; historical pins match. "
          "Structural validation only; not activation approval, full baseline audit or verification.")
    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-hashes", action="store_true",
                        help="Audit exact baseline bytes separately; requires PyYAML")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--commit", help="Read manifest and inputs from this exact Git commit")
    parser.add_argument("--output", type=Path, help="New JSON evidence path (never overwritten)")
    args = parser.parse_args()
    if args.audit_hashes:
        if args.output is None:
            parser.error("--audit-hashes requires --output")
        import runpy
        auditor = runpy.run_path(str(ROOT / "evidence/governance/20260906-baseline/audit_hashes.py"))
        return auditor["run"](args.repo, args.commit, args.output)
    if args.commit or args.output or args.repo != ROOT:
        parser.error("--repo, --commit and --output require --audit-hashes")
    return structural_checks()


if __name__ == "__main__":
    raise SystemExit(main())
