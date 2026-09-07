# Native Windows configuration diagnostics — Issue #5

Classification: software configuration, version, MCP transport, and static
diagnostics only. No model checking, scientific verification claim, or gate
acceptance is made here.

Source commit: `6aa30316d36fd5ce9948263c6f0edf5b5fee7664`.
Base: `origin/read`, `11bd69bdca9a1209f820258b3732b3c865f79035`.
Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/5>.
Owner account: `carwasher`. Target branch: `read`.

The original healthcheck at
`D:/uppaal_mcp_healthcheck_20260906_184139/REPORT.md` is a read-only input.
The active baseline remains a candidate; its model/generator hash discrepancies
and pending Gate 1 are outside this deliverable.

## Results

The run [run-20260907-native-01](run-20260907-native-01/) completed on Windows 11,
Python 3.14.5. Exact commands, return codes, source paths, source hashes, OS/CPU,
manifest hashes, and stdout/stderr hashes are stored in its JSON records.

| Check | Result |
| --- | --- |
| Isolated editable install with `mcp>=1.28,<2` | MCP 1.29.1 installed; `pip check` exit 0 |
| Unit suite | 85 tests, all successful, no skips; 11 new configuration tests |
| Coordination check | Exit 0; structural consistency only |
| `build_mcp()` and list-examples | Exit 0; FastMCP constructed and examples returned |
| Changed resolver with both verifier environment overrides absent | Finds `D:/UPPAAL/app/bin/verifyta.exe`; version command exit 0 |
| Real stdio using exact `mcp_conf.conf` command/cwd/env | Initialized, listed 76 tools, completed 4 read-only calls, closed |
| Real stdio using changed worktree and supported SDK | Same checks completed, with verifier path discovered automatically |

[Raw native version stdout](run-20260907-native-01/version-native-raw.stdout.txt)
reports `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`; the exact banner and
empty stderr are preserved. This is an actual `--version` process result, not a
model checking run.

The two stdio checks intentionally record different source environments:

- [Configured original environment](run-20260907-native-01/configured-original-environment/launch.json):
  `D:/uppaal_mcp/.venv/Scripts/python.exe`, existing MCP 1.27.2, imports original
  `D:/uppaal_mcp/src/uppaal_mcp/config.py`. This proves the updated configuration
  starts the existing installation. It does not test the changed resolver or
  establish compatibility with the new supported SDK range.
- [Changed worktree environment](run-20260907-native-01/changed-worktree-environment/launch.json):
  this task's own `.venv`, MCP 1.29.1, imports this task's changed resolver.
  The server has no explicit verifier path override; it discovers the native
  installation. This exercises the implementation with a supported SDK.

Both call only `uppaal_version`, `uppaal_list_examples`, `uppaal_get_example`, and
`uppaal_validate_model`. They do not run model checking or write model artifacts.
The original environment was not installed into or upgraded. Its checkout status
is identical before and after the diagnostics; bytecode writes were disabled in
child processes. No global Codex configuration, environment variables, license
settings, or original diagnostic files were changed.

## Reproduction

Use a clean checkout of the source commit and an isolated environment. Adjust
`mcp_conf.conf` paths for another machine before testing its configured server.
The diagnostic driver requires Python 3.11+ for `tomllib`; package runtime
requirements are unchanged by this workstream.

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -e . 'mcp>=1.28,<2'
& ./.venv/Scripts/python.exe -B evidence/healthcheck/20260906-config/diagnose.py --repo D:/uppaal_sdn_isac-carwasher-5 --out D:/new-native-config-diagnostic
```

Always choose a new `--out` directory: the driver refuses to overwrite a run.
The original install stdout/stderr are in `install.*.txt`; `installation.json`
records the commands and their byte hashes. Run-level `SHA256.json` records every
diagnostic file hash. The scoped `.gitattributes` prevents Git line-ending
conversion of raw `.txt` and `.json` evidence. The raw version stdout has a
file-specific whitespace exception because verifyta itself emits a trailing
space on its `Compiled using` line; those bytes remain unchanged.

These runs do not reproduce Linux/WSL execution or the CI Python 3.12 environment.
Unit path cases simulate Windows and POSIX selection independently of the host
filesystem and PATH. Scientific baseline/governance work remains outside #5;
dependency pinning is supplied separately by #3. Independent PR review is pending.
