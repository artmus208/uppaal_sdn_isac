# MCP installation and startup diagnostics — Issue #3

A fresh editable installation now selects a supported FastMCP SDK. Both the
normal resolution (`mcp 1.29.1`) and declared lower bound (`mcp 1.28.0`) install
and start successfully. Each environment completed all 80 unit tests without
skips and a real stdio initialize/tools-list exchange exposing 76 tools.

This is software regression evidence. No UPPAAL model checking was performed;
these results do not accept a scientific baseline, reviewer requirement, or gate.

## Scope and provenance

- Issue: <https://github.com/artmus208/uppaal_sdn_isac/issues/3>.
- Process: P0 software reliability support; atomic IDs: N/A — coordination-only.
- Owner/account-id: `carwasher`; independent review and integration are pending.
- Base ref: `origin/read`; target branch: `read`.
- Base commit: `11bd69bdca9a1209f820258b3732b3c865f79035`.
- Tested implementation commit: `7242cb1c9012a379d043933d7d8670b73026f336`.
- Branch: `codex/carwasher/3-mcp-startup`.
- Input baseline: `manifests/baselines/reviewer-r1.yaml`, SHA-256
  `89b8d6f520546c873649643b3cf90fd80f58e4458a443832369e3d1d28bf719a`;
  candidate only, unchanged.
- Original diagnosis: `D:/uppaal_mcp_healthcheck_20260906_184139/REPORT.md`,
  priority P1 fresh-install failure. Original diagnostics were not modified.
- Write scope: `pyproject.toml`, `src/uppaal_mcp/server.py`,
  `tests/test_phy_layer.py`, `tests/test_mcp_startup.py`, and this evidence folder.

The latest-resolution run started with a clean Git worktree. The lower-bound
run started at the same implementation commit with only the first run's new
evidence directory untracked. Each `run.json` records exact source file hashes,
Git status, commands, working directory, timing, Python, OS, CPU, virtual
environment, dependency request, log paths, and log hashes.

## Change and compatibility decision

`pyproject.toml` now requires `mcp>=1.28,<2`. The
[official SDK README](https://github.com/modelcontextprotocol/python-sdk)
(consulted 2026-09-06) identifies version 2 as an API rewrite and recommends a
`<2` upper bound for existing version 1 users. The
[version 1 FastMCP implementation](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/src/mcp/server/fastmcp/server.py)
provides the import, tool registration, `list_tools`, and default stdio `run`
APIs used here. The documented 1.28 lower bound is exercised by an exact 1.28.0
installation below; older SDK versions are outside the declared support range.

Startup diagnostics now distinguish a missing `mcp` root package from an
incompatible API or incomplete dependency installation. The latter reports the
installed SDK version when available and preserves the original import error
as its cause. Both diagnoses include the constrained SDK installation command.

The existing PHY registration test no longer converts every startup RuntimeError
into a skip. New mandatory tests exercise real stdio initialization and tool
registration, plus simulated missing-package, removed-module, removed-symbol,
missing-transitive-dependency, and missing-metadata import failures. Failed
required imports or server startup cause test failures/errors.

## Recorded results

| Check | Normal resolution: 1.29.1 | Lower bound: 1.28.0 |
|---|---|---|
| Isolated editable installation | exit 0 | exit 0 |
| `pip check` | exit 0 | exit 0 |
| `build_mcp()` and local tool listing | exit 0; 76 tools | exit 0; 76 tools |
| Full unit suite | 80 tests, no skips; exit 0 | 80 tests, no skips; exit 0 |
| Coordination structural check | exit 0 | exit 0 |
| Installed `uppaal-mcp` entry point over stdio | initialize + 76 tools; exit 0 | initialize + 76 tools; exit 0 |

Machine-readable command records: [latest/run.json](latest/run.json) and
[lower-bound/run.json](lower-bound/run.json). Exact resolved dependency versions
are in each `pip-freeze.stdout.txt`; these are environment observations, not
portable lockfiles. Complete initialization responses and tool schemas are in
each `stdio.stdout.txt`. Unit and server diagnostics are retained in the
corresponding `stderr.txt` files, including empty logs. The artifact index is
[artifacts.sha256](artifacts.sha256).
The scoped `.gitattributes` preserves original log/JSON bytes, including Windows
line endings, so Git normalization cannot invalidate their recorded hashes.

## Reproduction

From the repository root, with Python 3.10 or later installed, choose new output
directories so the recorded evidence is preserved:

```powershell
python evidence/healthcheck/20260906-mcp/reproduce.py --output evidence/healthcheck/20260906-mcp/reproduction-latest
python evidence/healthcheck/20260906-mcp/reproduce.py --output evidence/healthcheck/20260906-mcp/reproduction-lower --sdk 1.28.0
```

The script creates a separate virtual environment in the operating system's
temporary directory, removes inherited `PYTHONPATH`/`PYTHONHOME` for child
processes, runs installation, `pip check`, dependency listing, `build_mcp`, the
full unit suite, coordination checks, and `smoke.py`. It retains the environment
and saves each command's raw stdout/stderr and exit code. Normal resolution may
select a newer supported 1.x patch in future runs; the second command always
requests the tested lower bound.

## Acceptance and limitations

All Issue #3 implementation and diagnostic acceptance criteria have recorded
results. No failures or skipped tests occurred in either run. These checks were
performed on native Windows 11 with Python 3.14.5; Ubuntu/Python 3.12 CI and other
supported Python versions were not executed locally. The v2 and absent-package
error cases are simulated unit regressions; the original report contains the
actual v2 incompatibility diagnosis. Neither a v2 migration nor exhaustive tests
of every 1.x version are claimed.

Dependencies: none for this isolated software fix. Reviewer acceptance remains
pending. No scientific downstream workstream or gate is unlocked by these
software checks. Other report findings remain in their separately scoped Issues.
