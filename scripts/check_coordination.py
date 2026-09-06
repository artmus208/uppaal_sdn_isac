"""Dependency-free structural checks for GitHub coordination artifacts."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ISSUE_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "workstream.yml"
PR_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"
CODEOWNERS = ROOT / ".github" / "CODEOWNERS"
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
AGENT_RULES = ROOT / "AGENTS.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
SCIENTIFIC_PLAN = ROOT / "manifests" / "v1.md"
COLLABORATION = ROOT / "manifests" / "collaboration-v1.yaml"
BASELINE = ROOT / "manifests" / "baselines" / "reviewer-r1.yaml"

ERRORS: list[str] = []


def read_required(path: Path) -> str:
    if not path.is_file():
        ERRORS.append(f"missing required file: {path.relative_to(ROOT)}")
        return ""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        ERRORS.append(f"empty required file: {path.relative_to(ROOT)}")
    if "\t" in text:
        ERRORS.append(f"tab indentation is not allowed: {path.relative_to(ROOT)}")
    return text


def require_tokens(label: str, text: str, tokens: list[str]) -> None:
    for token in tokens:
        if token not in text:
            ERRORS.append(f"{label}: missing {token!r}")


issue = read_required(ISSUE_FORM)
pr = read_required(PR_TEMPLATE)
owners = read_required(CODEOWNERS)
workflow = read_required(WORKFLOW)
agent_rules = read_required(AGENT_RULES)
contributing = read_required(CONTRIBUTING)
scientific_plan = read_required(SCIENTIFIC_PLAN)
collaboration = read_required(COLLABORATION)
baseline = read_required(BASELINE)

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
        "manifests/collaboration-v1.yaml",
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
    "scientific plan",
    scientific_plan,
    [
        *[f"`C{i:02d}`" for i in range(1, 7)],
        *[f"`R{i:02d}`" for i in range(1, 8)],
        *[f"`V{i:02d}`" for i in range(1, 6)],
        *[f"`I{i:02d}`" for i in range(1, 7)],
        "`D01`",
        "P9a Integration draft",
        "P9b Final assembly",
        "hardware_description",
        "query_hash",
    ],
)
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
require_tokens(
    "baseline manifest",
    baseline,
    [
        "status: candidate",
        "frozen: false",
        "worktree_dirty_at_capture: true",
        "integrated_model:",
        "status: blocked",
        "policy: record_hardware_per_run",
        "status: pending",
    ],
)

plan_hash_match = re.search(
    r"(?m)^  scientific_plan:\n    path: manifests/v1\.md\n    sha256: ([0-9a-f]{64})$",
    baseline,
)
if not plan_hash_match:
    ERRORS.append("baseline manifest: missing scientific-plan SHA-256")
else:
    actual_plan_hash = hashlib.sha256(SCIENTIFIC_PLAN.read_bytes()).hexdigest()
    if plan_hash_match.group(1) != actual_plan_hash:
        ERRORS.append(
            "baseline manifest: manifests/v1.md SHA-256 is stale "
            f"({plan_hash_match.group(1)} != {actual_plan_hash})"
        )

if ERRORS:
    for error in ERRORS:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)

print("Coordination artifacts are structurally consistent.")
