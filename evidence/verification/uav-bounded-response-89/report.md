# Preparation report — no machine verdict

Issue #89 has a reproducible proposed Hnom restriction patch, six fixed queries,
native Linux controller/watchdog, reserved-slot plan and offline controls. All
six queries are **not_executed / verdict=null**. The issue requires approval
before materializing its restricted model, and a separate explicit decision
before native execution. Neither decision is present in this preparation.

The baseline remains exact full M (N=1, 51 processes). Hnom is a proposed
nominal-input, isolated-load diagnostic region. Its prospective hash comes from
deterministic in-memory construction; no XML file or machine verification is
claimed. `query-inventory.json` and `results.json` distinguish Q1–Q5/Hnom from Q6/M.
The original production model, generator, queries and manifests are unchanged.

Static inspection identifies retained sensing failure, optional service, result
loss, cancellation, timeout and unbounded waiting. Favorable external inputs do
not establish success. A particularly direct obstruction is the retained internal
loss alternative immediately before an otherwise possible correct delivery.
This is XML reasoning, not a saved UPPAAL counterexample. No defect against an
accepted component contract has been demonstrated by this preparation.

The proposed queries distinguish existential correct success (Q3), universal
successful bounded response (Q4), and universal terminal handling including
negative outcomes (Q6). Only explicit machine results can answer them. Q1/Q2/Q3
provide separate nonvacuity and causal coverage; their timeout would leave a gap.
Q5 checks terminal-location-aware deadlock but cannot establish fairness or time
divergence. No query will be changed after a negative verdict.

No witness, counterexample, native version observation or executable hash is
available for #89 yet. Prior #87's eleven timeout/null attempts remain scoped to
their original campaign, and the reported 7.477845500001 s overrun remains an
unresolved disposition in the retrieved records. Merge #88 does not accept it.

The native Linux implementation was selected by the user. The actual Runner
hostname, persistent path and verifier path/hash still need to be supplied in
the exact checkpoint decision. The historical expected version is compared only
after authorized preflight, never substituted for an observation. The prepared
commands and decision text are in `RUNNER.md` and `proposed-decision.md`.

Software/static validation is recorded in `checks/check-results.json`. Synthetic
tests exercise owned-process cleanup, time/memory stops, watchdog death,
controller disconnect, stop and telemetry/JSON failures without invoking UPPAAL.
The initial assertion expecting two explicit service-clock resets was wrong;
inspection shows one reset at actual send. That test correction and the original
failure are retained in `checks/initial-findings.json`.

The first full repository suite ran 209 tests: 208 succeeded and the MCP stdio
startup check hit its 30-second timeout inside the sandbox. The focused six-test
MCP startup module then completed successfully outside the sandbox (1.339 s).
Both logs are retained; the failure is not relabeled. The final host-suite result
and updated source checks are recorded alongside that history.

Owner must assemble the actual results after Runner's durable handoff, retaining
execution commits, raw hashes, any failed/interrupted attempts, missing metrics,
budget deviations and trace classifications. The English text below remains
preparation-stage wording. Acceptance of this protocol is not C02/P3/Gate 2/R07
acceptance. artmus208's participation in execution will be disclosed; subsequent
producer review is not independent scientific acceptance.
