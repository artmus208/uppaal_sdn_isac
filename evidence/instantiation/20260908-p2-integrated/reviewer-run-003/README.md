# Sandbox software/static diagnostics — reviewer-run-003

Source: clean commit `2dc471d` on `codex/carwasher/19-integrated-evidence`.
The user authorized repair of the previous regression harness and continuation.
The repaired mock is local to the recorder; `os.path.abspath` preserves the venv
symlink while normalizing relative paths. During that repair, one intermediate
test run raised NameError because SimpleNamespace was imported in the wrong test;
the import was corrected before the committed run. The final recorder regression
and all 19 focused Integrated tests exited 0 (no skips). `focused.json` and logs
record the focused run from the same committed source.

```sh
.venv/bin/python -B evidence/instantiation/20260908-p2-integrated/checks.py --output evidence/instantiation/20260908-p2-integrated/reviewer-run-003 --python .venv/bin/python --verifyta '/mnt/c/Program Files (x86)/UPPAAL-5.0.0/bin/verifyta.exe'
```

Recorder exit: 1. Full suite: 145 tests, one error, no skips. The failing
`McpStdioStartupTests.test_server_initializes_and_lists_registered_tools` timed
out at session initialization. This matches the previously recorded sandbox MCP
stdio limitation in merged PR #16; it is not a newly diagnosed model defect.
Pip consistency, versions, generation, coordination, YAML, MCP construction,
installed examples and diff check exited 0. The interpreter/CLI stayed in venv.

Version/help/compile-only each exited 1 with a WSL interop socket error:

```text
ERROR: UtilBindVsockAnyPort:309: socket failed 1
```

No tool version or license availability was established. No compile success or
property verdict is claimed. `checks.json` preserves exact per-command output,
hashes, environment, hardware, timing and exit codes. Generated artifacts carry
input/implementation hashes, parameters, instance vector and query mapping.
`audit.json` and its logs record the successful byte-reproduction/static audit.

Next: preserve this diagnostic run, then repeat the same checks outside the
sandbox on unchanged implementation/test bytes in a fresh directory. This is an
environment comparison, not a relaxation of tests. Scientific acceptance,
baseline supersession and Gate 1 remain pending.
