The integrated candidate previously rejected an updated AGENTS.md before generation, and its inherited branch included three paths outside #19 scope. This branch starts from current read, contains only the assigned paths, and records AGENTS.md as operational context while preserving strict model/specification/manifest pins. Model and query bytes remain identical to historical run-003.

## Handoff
- Issue: #19, keep open for independent review. Process P2; IDs R01/R02/R05/R06.
- Owner: artmus208, user-authorized ownership and scoped continuation recorded in #19.
- Branch: codex/artmus208/19-scoped-candidate; target: read.
- Base commit: 426cf570138231765b21d518f9d20289e2b11b63 (origin/read); historical base dc7eeb05f1fd3f2a4775428b1cd250363893128d.
- Tested local implementation: 6f88b49a99d74dd1a5a1d96005d9838b1579c6be; published equivalent: 87d1b1055e2ff320715c8792ce468f4b42775d0f. Identical tree b10e31df888520089f86a7b9eaeb5e841db05181; API commit metadata differs.
- Final head: see final #19 handoff comment and this PR head ref.
- Write scope / changed paths: src/uppaal_mcp/integrated/**, tests/test_sdn_layer.py, evidence/instantiation/20260908-p2-integrated/** only. No AGENTS.md, promts, manifest or standalone generator edits.
- Baseline: manifests/baselines/reviewer-r1.yaml; reviewer-r1-candidate; SHA256 89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a; frozen:false.
- Dependencies: P0 candidate, merged PR #16 and #18; no scientific acceptance inferred.
- Artifacts: evidence/instantiation/20260908-p2-integrated/reviewer-scoped-005-20260908/{checks.json,summary.json,SHA256SUMS,generated/,raw logs}; README criterion mapping and decisions.md.
- Model hash: 2b6928bda92bfb9bad5c74e91cf78c0b15beb4e7300bea401de8b4dc2cf592a4.
- Query hash: af9bbd8e73b1bc73eb7e957a89b826d24e04f1c2f1eed2f1b1e5bb4a55cd25b9.

## Validation and reproduction
Fresh isolated venv on unrestricted WSL, Python 3.12.3 / MCP 1.30.0 / PyYAML 6.0.3. 21 focused tests and all 147 suite tests exit 0, without skips/errors/failures. Recorder exit 0: generation, pip consistency, versions, coordination, YAML, MCP construction, examples, diff check, real verifier version/help/compile-only. Static audit exit 0.

Actual verifier: UPPAAL 5.0.0 rev. 714BA9DB36F49691 (June 2023), Windows executable via WSL. Recorder now translates paths and explicitly forwards UPPAAL_COMPILE_ONLY through WSLENV. Transport regression checks prevent losing that flag. No model-checking query or model-checking license probe was run.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k Integrated -v
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-new --python .venv/bin/python --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/audit.py evidence/instantiation/20260908-p2-integrated/reviewer-new
```

Use a clean committed checkout and new output directory. Save focused logs outside checkout until recording begins. Native Windows uses its own python/verifier paths. Exact commands, overrides, timestamps and log hashes are in checks.json; complete dependency freeze and hardware are saved.

## Acceptance checklist and limits
- [x] Deterministic 20 core + 8 boundary + 22 observer composition and historical XML/query byte equality.
- [x] Namespace/stub removal and explicit adaptation records.
- [x] Typed ACK, staged payload, transport loss/deadline and source-age regressions.
- [x] Explicit abstract bounds, placeholders and observer limitations.
- [x] Instance/parameter/query/provenance maps and strict unsupported-input rejection; operational AGENTS.md hashes separately retained.
- [x] Full software/static checks and separate real compile-only diagnostics.
- [x] Scoped draft handoff; historical evidence unchanged.
- [ ] Independent scientific acceptance of P2; reviewer/integrator decision and Gate 1 remain pending.

Verification status: not_run. Compile-only is not model checking. Replay tests do not prove timed properties. Uncalibrated abstract bounds, finite sample envelope, APP Crit/Agg placeholders, coalesced observer events and unimplemented application reconfiguration remain. No scientific downstream workstream is unblocked. Prior scope/provenance blockers are resolved for draft review; no merge or gate self-acceptance requested.
