# Issue #80 handoff — R07 candidate, not P5 acceptance

Deliverable: one full-model UAV N=1 failure scenario with APP rejection and
recorded SLA violation, engine-generated XTR, independent replay, negative controls,
63-step event table and English paper/reviewer-response drafts.

Owner/account-id: vadimnbkg. Reviewer/integrator: artmus208 proposed, confirmation
and independent scientific acceptance pending. Atomic ID R07 remains open.
Task branch: codex/vadimnbkg/80-r07-service-trace. Target: read.
Base ref/commit: origin/read / 91113a1b634f030c7e895f54f5c36a0b140d66eb.
Isolated source checkout: /tmp/uppaal-r07-80. Original shared dirty checkout was
not changed, except newly created durable bundles inside the authorized scope.
Scientific execution/checkpoints are preserved as complete Git history in the
handoff bundle, including source commits listed in results.json.

Pre-publication report checkpoint: e490d73043ed9d2658602edeb9b1fc2ce6037b7b (
the exact final transport HEAD is supplied in the PR and user-facing handoff).
Working tree must be clean at final transport. No source/model/manuscript,
manifest, historical evidence or query bytes were changed. All new paths are
under evidence/scenarios/r07-uav-n1-20261002/**; scope audit is in checks/.

## Results and checks

- sim001: goal_reached, 63 transitions; replay001: replay_complete, 63.
- negative-discrete001: rejected at state 63, discrete_state_mismatch, 62 accepted.
- negative-clock001: rejected at state 63, clock_zone_disjoint, 62 accepted.
- Prefix all run IDs with r07-80-20261002-. Exact version, hashes, source commits,
  commands, hardware, stdout/stderr/trace refs: results.json and per-run provenance.
- Model hash 5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385;
  query_hash=null; property_verdict=null. No model checking performed.
- Actual engine version: UPPAAL 5.0.0 revision 714BA9DB36F49691; full response
  preserved in result.json. All four owned process trees reaped.
- 209 repository tests: exit 0, 46.259 seconds, no skipped tests.
- 3 evidence corruption controls: exit 0; simulated positive query verdict,
  censored native success and incorrect APP endpoint are rejected.
- Coordination, family baseline including history, MCP/CLI smoke, pip check,
  actual verifier version probe: exit 0. Version probe executes no query.
- Package archive/hash/run/endpoint audit and scope/whitespace checks recorded
  in checks/ and audit-result.json. Static audit is not new verification.

The simulator, replay and controls used 27.88949 seconds of native campaign
wall time including probes/cleanup. No schedule correction/retry was needed.
The task finished within the 180-minute cap and before 08:00 Moscow.

## Limitations and next step

The witness ends with **failure handled on APP**, not successful service.
Violation report is observed at elapsed zero <=3 abstract units; no physical
calibration or universal response guarantee is inferred. Shared KPI fan-out,
single service-context correlation and pending-admission behavior are explicit.
No packet identity connects queue grant to service_complete. Existing sensing
location/class mismatch is retained and disclosed in the candidate prose.
First sandbox build failed due to WSL interop; raw failed output was overwritten
before archival. build-attempts.md labels its transcript honestly. Successful
native build and all engine outputs are preserved; no engine attempt failed.

Before final P5 acceptance, Integrator must decide P5 applicability of Gate 1,
obtain accepted P3 core evidence and an accepted verification run for this exact
model/parameters/instance vector, and confirm independent reviewer assignment.
Historical Issue #39 evidence does not transfer automatically. Author does not
close R07/P5 or self-accept the package. P9a owns application of the proposed text;
levels_tex/samplepaper.tex was not edited.

Transport: authenticated GitHub branch/PR if available, plus a full verified
bundle saved under the owner's durable Windows-backed workspace:
/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/evidence/scenarios/r07-uav-n1-20261002/handoff/r07-80-final.bundle.
The bundle contains both the final transport branch and original source checkpoint
history; use it to restore execution checkpoint 239ae70 for native reproduction.
Local shell push is unavailable (HTTPS lacks credentials, SSH host verification
is not configured in the sandbox); Git-data publication or bundle transport is
used instead. Published-tree equality must be checked after fetching publication.

Next: independently review the failure scenario and disposition the open P5
dependencies; integrate accepted prose through P9a. Do not silently repair the
model to turn this failure into successful service completion.
