# Shared-capacity projection and Glonina applicability (#101)

One P4 scientific deliverable, ready for independent review; acceptance pending.

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/101
Owner: vadimnbkg. Base: `read` / `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Branch: `codex/vadimnbkg/101-r04-compositional-proof`.
Write scope: this directory only.

Research question: establish the accepted finite UAV family's shared-capacity
invariant by a justified projection, and assess the precise applicability of
Glonina's scalable component-verification method to the present network.

Selected input: `uav-family-r1-20260929`, N=1,2,3,4; manifest SHA256
`5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`.
Family activation: PR #75, comment 5891123461. Operational v2 activation: #64,
comment 5878071165. Existing #76 runs and all models are read-only.

## Result

The proposed invariant is stronger than the original capacity predicate:
`family_grant_i <-> (family_last_server == i)` holds in every reachable state
of each pinned instance under the stated UPPAAL semantics. Its inductive proof
and full-to-abstract simulation depend on explicit writer/initialization/frame
premises, which the scoped checker audits. The resulting observation graph has
N+1 reachable states. This does not establish concrete service reachability,
fairness, useful throughput, queue safety, SLA, or arbitrary-network scalability.

Glonina's source-specific component and parameter reductions are compared against
the actual family. None is silently treated as a universal UAV cutoff. All
twelve historical native capacity attempts remain timeouts with null verdicts.
No model/query was submitted to a native verifier by this scientific package.
A version-only repository smoke probe is disclosed in `HANDOFF.md`.

## Read and reproduce

| Artifact | Purpose |
|---|---|
| [PROOF.md](PROOF.md) | Precise theorem, assumptions, induction, forward simulation and transfer limits |
| [GLONINA.md](GLONINA.md) | Primary-source comparison with theorem pages and concrete model selectors |
| [integration.md](integration.md), [references.bib](references.bib) | Proposed English article text, R04 reply, claim map and candidate citations |
| [sources.json](sources.json) | Source identity, hashes, page mapping and visual-reading record |
| [check_proof.py](check_proof.py), [test_proof.py](test_proof.py) | Standard-library premise audit, abstract BFS and 27 test methods with mutation controls |
| [generated/certificate.json](generated/certificate.json) | Four pinned model/query certificates and complete reachable abstract state lists |
| [generated/historical-runs.json](generated/historical-runs.json) | Twelve original timeout records with reproducible source references |
| [checks](checks), [HANDOFF.md](HANDOFF.md) | Commands, raw test logs, base regression controls and acceptance boundaries |

From the repository root, with Python 3.11 or newer:

```text
python evidence/scalability/20261004-r04-compositional-proof/check_proof.py
python -m unittest discover -s evidence/scalability/20261004-r04-compositional-proof -p test_proof.py -v
```

The first command recomputes all checks and compares the deterministic artifacts.
Exit 0 means static premises and artifacts agree; it is not a native property
verdict or independent scientific approval. A changed pinned input or stale
artifact returns exit 1. No third-party Python package or verifier is required.

For an intentional artifact regeneration after reviewing checker/source changes:

```text
python evidence/scalability/20261004-r04-compositional-proof/check_proof.py --write
```

The output directory is fixed within this workstream. Keep exact repository
bytes (`git -c core.autocrlf=false clone ...` for a fresh Windows checkout), since
the scientific inputs and output certificates are byte-pinned. The whole
repository suite, unlike these scoped tests, requires the project dependencies.
CI runs that root suite; it does not discover tests in this evidence directory.

Frozen inputs, generator, manifests, manuscript and production code are unchanged.
Integration and reviewer-requirement closure require an independent decision.
