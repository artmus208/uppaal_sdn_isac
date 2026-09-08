# Issue #19: blocked recorder run on WSL

This is failed software diagnostic evidence, not a completed implementation
evidence bundle. No model checking or compile-only run was attempted.

Source commit: `635c3ba6cd0c5acb3f010e2df949dd89265db9ac`.
Base commit: `dc7eeb05f1fd3f2a4775428b1cd250363893128d`.
Owner: `carwasher`. Continuation branch: `codex/carwasher/19-integrated-evidence`.
Clean isolated clone: `/tmp/uppaal-carwasher-19-evidence-20260908`.
The original dirty checkout and its task branch were preserved.

## Results

Python 3.12.3; the isolated environment installed mcp 1.30.0 and PyYAML 6.0.3.
The initial dependency installation was blocked by sandbox proxy permissions;
the permitted network retry installed the dependencies successfully. That initial
installation console output is not part of the raw recorder logs.

The direct focused command exited 0: 18 tests, no failures or skips:

```sh
.venv/bin/python -B -m unittest discover -s tests -p test_sdn_layer.py -k IntegratedCandidateTests -v
```

`focused.stdout.log` and `focused.stderr.log` preserve that command's output.
The command ran before the recorder from the same clean source commit.

The recorder command exited 1:

```sh
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-run-002 --python .venv/bin/python
```

`checks.json` contains exact child commands, timestamps, environment, hardware,
exit codes and raw-log hashes. Coordination, YAML parsing and diff checks exited
0. Its pip-check also exited 0, but checked the system interpreter, so it does
not establish consistency of the intended virtual environment.

Versions, generation, full unittest discovery and MCP construction exited 1.
Examples could not start. Unittest reported 14 tests and 9 import errors; this
is not an execution of the complete software suite.

## Confirmed cause

`checks.py` uses `python=str(args.python.resolve())`. On this Unix venv,
`.venv/bin/python` is a symlink: resolving it yields `/usr/bin/python3.12`,
discarding the virtual environment. Its CLI lookup then becomes
`/usr/bin/uppaal-verifyta`, which does not exist. Logs record
`ModuleNotFoundError: No module named 'uppaal_mcp'` and missing mcp metadata.
The successful focused run used the venv path directly.

Under the task prompt's explicit stop-on-test-failure rule, implementation and
further checks stopped here. No source files were changed, no complete bundle
was audited, and no PR was opened. `audit.py` requires generated output, which
this failed recorder run did not produce. The existing top-level README's
`checks-native-01` reference is not evidence supplied by this checkout.

## Next action

Fix recorder interpreter handling within Issue #19 scope: make the supplied
Python path absolute without dereferencing the executable symlink, keeping CLI
lookup relative to that venv. Add a focused regression that exercises a symlinked
venv. Commit the recorder fix before running it from a clean tree. Use a fresh
output directory (for example `reviewer-run-003`); never overwrite this run.
Then finish the full suite, deterministic generation, actual tool availability
diagnostics, static audit and scoped draft PR to `read`.

P1/P2 independent scientific acceptance, baseline supersession and Gate 1 remain
pending. Tool version and license availability were not established in this run.
No generated model/query hashes or property verdicts are available from it.
