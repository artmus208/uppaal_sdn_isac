# Issue #26 — publication contract

https://github.com/artmus208/uppaal_sdn_isac/issues/26

Process: P1 — report revision publication (supporting correction).
Deliverable: Publish the user-reviewed local PHY/parameter revision of validation-report.md as a separate, traceable review package and draft PR to read.
Atomic IDs: V01, V02, V03, V04, V05 — supporting clarification only; primary ownership remains #15. No independent closure.
Owner account: carwasher (account-id: carwasher).
Reviewer / Integrator: independent reviewer pending assignment; author does not accept own result.
Base ref: read
Base commit: 4480f1087b93f48541a925590ae82ca86fa4b808
Target branch: read
Input manifests: manifests/v1.md (SHA256 f0290fdb65df369a42dbbdb5e8b86a3c4753f029446444281101c4b7bbbd8075); manifests/collaboration-v1.yaml (31ab816470827d81bc73944487b11897beb2d0ddc80c5f3f4f878facf93417c0); manifests/baselines/reviewer-r1.yaml (89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a), candidate, not frozen.
Dependencies: P0 candidate and merged P1/P2 packages already present at the pinned read commit. These are publication/source-audit inputs; scientific acceptance is not presumed. Open PR #24 is referenced as an unmerged proposal only.
Required gate: none for publishing a revision proposal. P1/P2 acceptance and Gate 1 remain separate decisions.
Write scope:
- evidence/validation/20260910-phy-revision/**
Read-only inputs: D:/ПЗ психология/validation-report.md, its original backup/patch/revision record, historical P1/P2 packages, code, TeX and manifests.
Out of scope: model/generator changes, manuscript, manifests, historical P1 artifacts, threshold correction PR #24, empirical data collection, verification, Gate 1 acceptance.
Acceptance criteria:
- Preserve the exact revised local report (SHA256 cabda2a06ef942f7d572a1bf8db8396f522ca2c86f60440d0357f678f2403b8b), original backup, reproducible patch and original revision record.
- Make the package readable on GitHub with working local report links and explicit local-origin/publication provenance.
- Explain corrections to physical quantities, CFAR, accuracy/CRB, sensing capacity, timing/resource assumptions, missing data and source age; distinguish proposed definitions from implemented decisions.
- Recheck content hashes, patch reproduction and unchanged historical/model/manuscript inputs; record relevant CONTRIBUTING checks and all failures.
- Publish an isolated named branch and draft PR to read with reproducible handoff.
Expected artifacts: report, backup, patch, local revision record, README, issue contract/provenance and check logs inside scope.
Verification required: no. Software/static checks do not establish physical validity or model checking.
Status: claimed
Authorization: user explicitly requested “1 Опубликуй” after the proposal to publish the revised P1 report as a separate revision and draft PR.
Scope audit: open Issues inspected on 2026-09-10; no existing write scope claims this new directory. #15 and #25 retain their own scopes and ownership.

Task branch: codex/carwasher/26-phy-report-revision
Isolated clone: /tmp/uppaal_sdn_isac-carwasher-26
