# Four-size SDN/ISAC preparation package

[Issue #68](https://github.com/artmus208/uppaal_sdn_isac/issues/68), P2. One common
optional MAC queue-service opportunity per epoch couples N=1,2,3,4 private
PHY/MAC/SDN/APP contexts. The compositions have 50,99,148,197 automata. SDN
contexts are per-UAV logical agents, not a centralized-controller performance
model. [CONTRACT.md](CONTRACT.md) defines the scope and preserved limitations.

The generator and inherited query files for N=1,2 preserve the #67 XML/query
bytes. No fairness, priorities, physical calibration or observer repairs were
added. This is a candidate for review, **not a frozen baseline or completed P4**.
Old P3 evidence retains its original scope; R03/R04/C06 remain open.

From a clean checkout, Python 3.10+ and no external packages for generation:

```bash
python3 -B evidence/scalability/family-series-68/generate.py
python3 -B evidence/scalability/family-series-68/generate.py --check
python3 -B evidence/scalability/family-series-68/check.py
python3 -B evidence/scalability/family-series-68/audit_artifacts.py
```

The first command generates all XML, legacy/compact queries, parameters,
instance vectors, interface inventories and hashes. `inputs.json` pins all
read-only inputs, including #66. The generator hash covers both Python source
files involved in generation. `checks/static.json` records 62 rejected mutation
controls, 4,800 local guard cases, 4,000 allowed local updates and 200 load-class
cases. Static checks do not establish model-checking verdicts or timed equivalence.

Reproduction from a full clean Git archive, with a new output path inside scope:

```bash
python3 -B evidence/scalability/family-series-68/reproduce.py \
  --output evidence/scalability/family-series-68/.venv/reviewer-reproduction.json
```

This command uses only committed inputs and compares all 70 generated files.
The `.venv` directory here is ignored scratch space; it need not contain a Python
environment to hold the report. It leaves immutable published evidence unchanged.

## Actual diagnostic outcomes

See [RESULTS.md](RESULTS.md) for the N=1…4 matrix and direct run references,
[checks/diagnostic-001/runs.json](checks/diagnostic-001/runs.json) for exact
hashes, actual version, source commit, verdicts, commands and resource records,
and [gate-candidate.json](gate-candidate.json) for the decision package. Success
of `E<> true` means model loading only. Timeout/error has no property verdict.
The negative queue-safety outcome concerns the original C01-queue predicate in
these models, not a transferred old result or a claim of generator failure.

The Windows monitor is tested using harmless child processes before verifier
launch; `monitor-controls-002` confirms normal output, time stop, measured-memory
stop and process termination. `monitor-controls-001` preserves an earlier failed
test assertion caused by PowerShell progress output and a corrected sample-gap
measurement bug. No verifier was used by those monitor tests.

Native Windows private bytes/working set are sampled at 50 ms requested
intervals, with actual gaps/overshoot saved. The 2 GiB value is a measured stop
threshold, not a hard allocation cap. Available physical RAM is a campaign-start
snapshot. Compiler logs are losslessly compressed; stream hashes refer to raw
bytes and storage hashes to the saved files. Traces are retained where produced.

The bounded runner is reproducible from a clean committed checkout with a
licensed Windows verifier, after explicitly deciding that a new diagnostic
campaign is justified. This command is documented, not an automatic retry:

```bash
python3 -B evidence/scalability/family-series-68/run_checks.py \
  --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe' \
  --run-id diagnostic-review-UNIQUE
```

## Proposed P4 series and decisions

[PROTOCOL.md](PROTOCOL.md) and [p4-plan.json](p4-plan.json) specify all formulas,
assumptions/nonvacuity, order, search settings, repeats and stops. Primary fixed-u0
query curves, global growing predicates and the N-query coverage workload are
reported separately. Generation, compilation and verification costs are separate;
end-to-end verifier time is not mislabelled as pure search time.

Proposal: sequential DFS/exhaustive symbolic search, seed 68, compact DBM,
unchanged parameters, three fixed-order repetitions; 60 s and 2 GiB per verifier
invocation, 2 hours total. The current work executes only one short diagnostic
attempt per selected query, under 30 s behavior/10 s setup thresholds and the
1,200 s aggregate ceiling. It does not execute the proposed P4 series.

Before P4, Integrator must accept the finite family and logical-controller/shared
optional-service abstraction, dispose of the open behavioral checks listed in
RESULTS.md, accept the query/measurement protocol and then freeze the new commit,
model/query/generator hashes, parameters, vectors and tool version through a
separate Gate 1 decision. There is no arbitrary-N theorem or old-P3 transfer.

Repository verification: 200 tests, coordination structural check and MCP/CLI
smokes are recorded in `checks/validation.json`. Handoff and transport details:
[HANDOFF.md](HANDOFF.md).
