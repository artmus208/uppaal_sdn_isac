# Current diagnostic entry point — Issue #78 / PR #79

User/Integrator requested correction of the stale README and failing aggregate
audit in this session on 2026-10-02. This authorizes the documentation/audit
correction within Issue #78's original scope, beyond the completed replay-only
implementation scope. Owner/account: vadimnbkg. Reviewer/Integrator: artmus208.
Process: P2; supporting R02/R05/R06, with no requirement closure or gate decision.

Deliverable: one current entry point and reproducible read-only aggregate audit.
Base ref: PR #79's codex/vadimnbkg/78-n1-service-diagnosis.
Base commit: 9e2c7a7610e40af70e89dd1991e9aff144869b0f.
Original scientific base: 8237e8c2bec41aa1bb943cc33be1ac9586d03759.
Work branch: codex/vadimnbkg/78-diagnostic-documentation. Target branch: read
through PR #79. Required accepted dependencies remain those in Issue #78;
model, query, baseline and scientific conclusions are unchanged.

Write scope for this correction, within evidence/scalability/n1-service-diagnosis-78/:

- README.md
- audit.py
- current-artifact-hashes.json
- checks/current-package-audit.json
- documentation-fix.md

The README leads with the current replay result and explicitly dates the older
search diagnosis. The aggregate audit preserves historical inventories, checks
their unchanged artifacts (and old README/audit bytes at b403fd3), checks the
replay's independent inventory, and uses new current inventory/report files.
It invokes no engine and reports no query verdict. Acceptance remains pending
independent review.

Reproduction from the repository root:

```sh
python3 -B evidence/scalability/n1-service-diagnosis-78/audit.py
python3 -B evidence/scalability/n1-service-diagnosis-78/replay-001/inspect_replay.py
python3 -B -m unittest discover -s evidence/scalability/n1-service-diagnosis-78 -p 'test_diagnostics.py' -v
python3 -B -m unittest discover -s evidence/scalability/n1-service-diagnosis-78/replay-001 -p 'test_*.py' -v
```

Validation on the correction checkpoint 12ed4bc947a9fb5ca74d40c0a926360a7fd1fb29:

- Aggregate audit: exit 0; 253 current artifact hashes, 255 scoped package paths,
  independent replay audit consistent. Both historical inventory files and all
  replay files remain byte-identical to the base commit.
- Diagnostic runner tests: 9 tests, exit 0. Replay evidence tests: 4 tests, exit 0.
- In-memory corruption probes for a diagnostic query hash and a replay result
  hash both rejected; no evidence bytes were modified by the probes.
- `python3 -B scripts/check_coordination.py`: exit 0.
- `python3 -B scripts/check_family_baseline.py`: exit 0; 106 current hashes.
- `PYTHONPATH=src /tmp/uppaal-replay-oct02/.venv/bin/python -B -c
  'from uppaal_mcp.server import build_mcp; print(type(build_mcp()).__name__)'`:
  exit 0, FastMCP.
- `PYTHONPATH=src /tmp/uppaal-replay-oct02/.venv/bin/python -B -m
  uppaal_mcp.cli list-examples`: exit 0.
- `PYTHONPATH=src /tmp/uppaal-replay-oct02/.venv/bin/python -B -m unittest
  discover -s tests -v`: first sandbox invocation exit 1, 209 tests in 80.966 s,
  one MCP stdio initialization TimeoutError at test_mcp_startup.py:96, no other
  failures. Isolated `-p test_mcp_startup.py` outside sandbox: 6 tests, exit 0.
  Full suite outside sandbox: 209 tests in 47.918 s, exit 0, no skipped tests.
- `git diff --check` for the correction: exit 0.

No new engine/search invocation or scientific verdict. The final checkpoint
changes only this handoff text and its current inventory hash; the audit is
regenerated and checked again. Repository source and tests are unchanged.

Publication uses the authenticated GitHub connector because local HTTPS Git
has no credentials. The published tree must equal the checked local tree;
exact final commit/ref and clean status are provided in the PR handoff.
Local checkpoint history is retained in the full durable
`evidence/scalability/n1-service-diagnosis-78/handoff/documentation-fix-final-20261002.bundle`
in the owner's repository. Next step: independent review of PR #79; the author
does not merge or self-accept the correction.
