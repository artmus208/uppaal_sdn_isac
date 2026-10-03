# Preparation report — no machine verdict

Issue #89 has a reproducible proposed Hnom restriction patch, six fixed queries,
native Windows controller/Job Object watchdog, reserved-slot plan and offline controls. All
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

No witness, counterexample or native verifier version observation is
available for #89 yet. Windows PE inspection confirmed the user-supplied executable
SHA256 without invoking it. Prior #87's eleven timeout/null attempts remain scoped to
their original campaign, and the reported 7.477845500001 s overrun remains an
unresolved disposition in the retrieved records. Merge #88 does not accept it.

The user corrected the Runner environment to Windows Python + Windows verifyta.
Original Linux preparation 9e4743bf remains in history. Native host/Python and PE
bytes/hash were inspected; the persistent checkout and exact new checkpoint still
need artmus208's decision. Historical expected UPPAAL version is compared only
after authorized preflight. Commands and decision text are in `RUNNER.md` and
`proposed-decision.md`; Windows implementation details are in `WINDOWS.md`.

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

Windows revision validation: all 26 scoped tests completed on native Windows
Python with zero failures/errors/skips (`checks/windows-004/record.json`). The
first 16 process controls had passed, while three generic tests exposed system
codepage decoding. Explicit UTF-8 restored the exact old model/query products.
Two subsequent sets exposed transient console-host teardown; probes identified
owned conhost.exe, and a 250 ms natural-exit grace bounded by the existing
attempt deadline fixed the fast-exit regression. All failed logs/probes remain
under checks/windows-001, checks/windows-final and checks/windows-003.

The observed Windows verifier PE is AMD64 PE32+, 6,730,240 bytes, matching the
user's SHA256. This is byte inspection, not execution or version evidence.
