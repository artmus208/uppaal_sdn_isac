# Scoped software/static evidence — Issue #19

Run ID: reviewer-scoped-005-20260908. Source clean commit:
6f88b49a99d74dd1a5a1d96005d9838b1579c6be. Published equivalent implementation
commit: 87d1b1055e2ff320715c8792ce468f4b42775d0f. Both have identical Git tree
b10e31df888520089f86a7b9eaeb5e841db05181, parent read
426cf570138231765b21d518f9d20289e2b11b63. GitHub API publication changes commit
metadata, not file bytes; the local source is also in the durable checkpoint bundle.

Environment: fresh isolated .venv, Python 3.12.3, MCP 1.30.0, PyYAML 6.0.3,
WSL Linux outside sandbox, Windows verifyta via interop. This is not a native
Windows Python test. Full installed resolution: pip-freeze.txt; install.log;
hardware: checks.json and cpu.txt. Commands run from /tmp/issue19-scoped.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k Integrated -v
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-scoped-005-20260908 --python .venv/bin/python --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/audit.py evidence/instantiation/20260908-p2-integrated/reviewer-scoped-005-20260908
```

Focused output was stored in /tmp until recording began from the clean commit.
Reproduction must use a NEW directory, not overwrite this run. All commands
above exit 0. Focused: 21 tests; full suite: 147 tests, no skips/errors/failures.
Recorder exit 0: pip consistency, versions, generation, coordination, YAML, suite,
MCP construction, installed examples, diff-check, verifier version/help/compile-only.
Static audit exit 0. Exact recorder arrays, per-command overrides, timing,
exit codes and raw-log hashes are in checks.json; supplemental results are in
summary.json. SHA256SUMS indexes all files in this run except itself.

Actual verifyta output: UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023.
Compile-only uses Windows-readable paths and WSLENV forwarding of
UPPAAL_COMPILE_ONLY=1. The captured compiler output is diagnostic output, not
a property verdict. Model checking and its license availability were not tested.

Model hash: 2b6928bda92bfb9bad5c74e91cf78c0b15beb4e7300bea401de8b4dc2cf592a4.
Query hash: af9bbd8e73b1bc73eb7e957a89b826d24e04f1c2f1eed2f1b1e5bb4a55cd25b9.
Both are identical to run-003; generated/model.xml and queries.q are byte-identical.
Partition: 20 core + 8 boundary + 22 observers. New implementation hash reflects
the explicit provenance classification, not altered XML/query semantics.

Only AGENTS.md is operational context, with historical and actual hashes in
generated/composition.json/context_document_hashes. All other source and
specification pins remain enforced. New regressions exercise operational drift,
strict model/specification/manifest rejection and Windows compile-only transport.
The audit additionally compares actual context metadata. Historical logs/runs
remain unchanged and refer to their own source implementations.

The prior two blockers are resolved for this draft: no out-of-scope paths in the
new branch, and operational AGENTS.md drift no longer blocks generation. No
scientific baseline, parameter or gate was accepted. Independent reviewer must
assess decisions.md, semantic adaptations and the complete candidate; P1/P2
scientific acceptance and Gate 1 remain pending.
