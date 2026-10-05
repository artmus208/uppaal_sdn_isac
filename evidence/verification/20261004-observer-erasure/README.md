# Observer-erasure proof package

One P3 research deliverable for Issue #116: determine exactly what deleting the explicit
observers preserves in the activated fixed N=1 UAV completion model. Author:
vadimnbkg; intended independent reviewer/integrator: artmus208. Supporting
C01/C03/C04/C05 evidence only; primary ownership and acceptance stay unchanged.

Results are mathematical arguments and static validation, **not native UPPAAL
verdicts**. Acceptance is pending. The original 51-process input is unchanged.
The scoped diagnostic XML has 29 processes; 22 observer instances are removed.

| Claim | Evidence |
|---|---|
| T1: equal retained finite timed traces up to stuttering; safety/reachability transfer | proof.md sections 2–6; check.py; certificate.json |
| T2: full deadlock implies projected reduced deadlock; no general converse | proof.md section 6; SemanticControls |
| T3: retained divergent-path observations correspond under the stated convention | proof.md section 6; explicit normalization argument |
| Observer nonrestriction does not establish error detection completeness | proof.md section 7; exact observer edges; polling controls |
| Input/transformation binding | premises.json; input hashes and reduced hash in certificate.json |

Reproduce from this package's directory, supplying the source checkout root:

```powershell
python check.py --repo C:\path\to\research-work --output reproduced-certificate.json --reduced reproduced-model.xml
python tests.py --repo C:\path\to\research-work -v
```

For a later integration under
`evidence/verification/20261004-observer-erasure/`, `--repo` defaults to the
repository root. `premises.json` binds declaration/types/initialization, helper
signatures, local scopes and process order; it is an extracted source capsule,
not a behavioral oracle. Mutation controls bypass the outer XML hash to test
retained writes, hidden enabling dependencies, helper effects, binary/urgent
receives, missing committed exits, cycles, priorities and invalid query classes.
Toy semantic controls distinguish failure of a general transfer from a
reachable counterexample in this particular full network.

Scientific input: `uav-service-completion-r1-20261002`, source commit
`61386aa358805082b705dcd00c8cbfde5fb98248`, baseline model SHA256
`b8ab50e112b71491f8242789cc7906497baf8440c473d7a5a4d5214840187e02`,
manifest SHA256 `4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d`.
Analysis base `read` at `e5c299d0b426e57652cb8a78f37ae770949b53b1`.

Accepted selection/activation sources:
[v2 activation #64](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165),
[candidate #83](https://github.com/artmus208/uppaal_sdn_isac/pull/83),
[A/B input Gate1](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646),
[operational activation](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320).
Issue #115's FIFO/termination task and #108's completion-safety proof are
separate read-only work; neither is assumed by this reduction theorem.

Publication is authorized under [Issue #116](https://github.com/artmus208/uppaal_sdn_isac/issues/116).
Branch: `codex/vadimnbkg/116-observer-erasure`; target: `read`.
The bounded native campaign is specified in assignment.md and native/protocol.json.
Each exact accepted query receives one 600-second/2048-MiB attempt on the
diagnostic XML. Native results, when present, are separate from the mathematical
argument; full-model transfer still requires independent acceptance.

The campaign ran on UPPAAL 5.0.0 (rev. 714BA9DB36F49691). Completion safety
hit its 600-second limit; success stopped on a Windows status-file update error.
Neither query has a decisive native verdict. See native-summary.md and
native-results.json; raw evidence is preserved and no retry was performed.
Draft PR: https://github.com/artmus208/uppaal_sdn_isac/pull/118.

## User-authorized 30-minute rerun, 2026-10-05

The user extended timeout to 1800 seconds per formula and authorized a
conditional repair/rerun if the status-write error recurred. The scientific
inputs and 2048-MiB sampled memory stop were unchanged. Both runs ended on
memory_limit, with no native verdict: safety after 971.813 seconds, success
after 1064.141 seconds. The status-write error did not recur; no repair or
suffix-03 run was activated. Raw logs, exact bindings and integrity validation
are in native-30min/. Historical native/ evidence remains byte-for-byte intact.
Published branch remains codex/vadimnbkg/116-observer-erasure, draft PR #118;
independent acceptance remains pending. No active native worker remains.
