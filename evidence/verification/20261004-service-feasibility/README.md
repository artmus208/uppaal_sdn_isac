# Service feasibility and progress — Issue #115

One fixed-model mathematical package for the accepted N=1, 51-process,
one-request/one-result UAV completion baseline. Owner: vadimnbkg;
independent Reviewer/Integrator: artmus208/user-integrator.
Base: read at e5c299d0b426e57652cb8a78f37ae770949b53b1.
Branch: codex/vadimnbkg/115-service-feasibility; PR target: read.
Sole write scope: evidence/verification/20261004-service-feasibility/**.

The key result is a necessary queue constraint: a result enqueued at FIFO rank
two or greater cannot meet the strict five-unit freshness bound when consecutive
service decisions are five units apart. A second theorem bounds APP terminal
outcome by request age 40 on time-divergent executions, without asserting that
every prefix has such a continuation or that the terminal outcome is success.
See [proof.md](proof.md) for quantifiers, proof and a conditional success contract.

Evidence: mathematical_argument supported by static_validation. The scripts
audit premises and rational examples; they do not prove arbitrary UPPAAL models,
run the verifier, or produce model-checking verdicts. Existing native timeout and
negative results keep their original meanings. Independent acceptance is pending.

From repository root, Python >=3.10, standard library only:

```text
python -B evidence/verification/20261004-service-feasibility/check.py --check
python -B evidence/verification/20261004-service-feasibility/tests.py
python -B evidence/verification/20261004-completion-safety-proof/check.py --check
```

The third command reproduces the accepted #110 causal/safety dependency. The
first command additionally pins its source and premise bytes. Mutation tests
bypass only the outer model byte gate; the reviewed semantic capsule remains
fixed. Certificates list complete writer sites and graph/constant obligations.
Do not regenerate a capsule merely to make a changed model pass.

Read [context.md](context.md), [article-snippet.md](article-snippet.md) and the
final HANDOFF.md for scope, prior work and validation. No model, query, manifest,
shared implementation or manuscript changes belong to this deliverable.
