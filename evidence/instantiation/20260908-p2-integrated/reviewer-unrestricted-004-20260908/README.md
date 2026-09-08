# Unrestricted WSL diagnostic — Issue #19

Run ID: `reviewer-unrestricted-004-20260908`. Source clean commit:
`6604af040b16c9c3c0e6ceb78b7f52df7172f185`. Runtime: WSL Linux, Python 3.12.3,
MCP 1.30.0, PyYAML 6.0.3, fresh isolated `.venv`; execution outside the sandbox.
This is not a native Windows Python run. Windows verifyta is invoked via WSL
interop. The implementation and tests are byte-identical to historical `2dc471d`;
`provenance-audit.json` records the comparison. Historical full dependency freeze
is unavailable; the three recorded versions match, while this run's complete
resolution is in `pip-freeze.txt`. Hardware is in checks.json and cpu.txt.

## Commands and outcomes

From `/tmp/issue19-native-handoff`, before adding diagnostic files:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e . PyYAML
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k IntegratedCandidateTests -v
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-unrestricted-004-20260908 --python .venv/bin/python --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/audit.py evidence/instantiation/20260908-p2-integrated/reviewer-run-003
```

Installation initially failed inside sandbox (exit 1, proxy/socket restriction);
outside sandbox pip upgrade/install exit 0. Logs retained. Focused exit 5:
zero tests, class setup rejects `pinned source changed: AGENTS.md`. Recorder exit
1: generation exit 1, full suite exit 1 (127 tests, one setup error, no skips),
compile-only exit 1 (generated/model.xml absent). All other recorded commands
exit 0. Historical regeneration audit exit 1 for the same pinned-source mismatch.
A new generated-artifact audit cannot run because generation produced no model.
No pins or implementation were changed to bypass the failure.

The real MCP stdio initialization/list-tools regression completes in this full
suite. The earlier timeout does not recur in this unrestricted environment;
this does not isolate its exact cause because clone/dependency resolution also
changed. The run still does not cover all 145 historical tests: IntegratedCandidate
class setup prevented its tests, while the recorder regression itself ran.

Windows `cmd.exe /c ver` failed inside sandbox with
`UtilBindVsockAnyPort:309: socket failed 1`, and succeeded outside sandbox with
Windows 10.0.19045.6456 (preliminary tool observations, not separate raw-log files).
New verifyta version/help outputs are saved raw and exit 0. Actual version:
`UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`. Version output includes a license
attribution, but model-checking license availability was not tested. Compile-only
did not establish syntax correctness; a native Windows invocation will also need
a Windows-readable path to an existing XML. No model checking or P3/P4 run occurred.

## Provenance and blockers

`collect_diagnostic.py` checks all pinned inputs, implementation/test equality,
historical command/focused/audit log hashes and the full diff scope. Exit 0 means
the integrity collector ran successfully, not that pin drift is acceptable.
All historical log hashes match. The only pinned mismatch is AGENTS.md:

- expected `cb2ed0d4b60678bfe9e8153c626dce28d1cd17d201154eac954c729047845c78`;
- actual `e4fde1df5f51a582d2b0f06daef9a2a98d3a96195c3201584d7d5e801d038b28`.

Integrator must decide the permitted provenance update in its owning scope.
No semantic model defect is inferred. The inherited PR diff to current read
`426cf570138231765b21d518f9d20289e2b11b63` also contains AGENTS.md and two promts
files outside #19 scope. Per the task, no branch reorganization or out-of-scope
PR is performed. These are the remaining blockers, not the earlier interop error.

`checks.json` has full recorder commands/timing/exit codes and log hashes.
`SHA256SUMS` indexes this diagnostic directory excluding itself. Historical logs
are unchanged. Reviewer next: resolve scope/provenance with Integrator, then run
all focused tests/full recorder/audit from a new clean accepted checkpoint and
new run ID. Scientific P2 acceptance and Gate 1 remain pending.
