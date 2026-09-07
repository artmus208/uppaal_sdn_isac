# Combined read checks after PRs #7–#12

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/13
Owner/account-id: `artmus208`. Process: P0 software diagnostics.
Atomic IDs: N/A — coordination-only. Target: `read`.
Source commit: `f2f714a26d6b9d9f538ef1a16b53c3e060768a11`.
Branch: `codex/artmus208/13-postmerge-checks`.
Write scope: `evidence/healthcheck/20260907-postmerge/**` only.

The combined source installs without manually constraining MCP, and all 126
unit tests pass without failures or skips. The installed MCP server initializes,
lists 76 tools and completes four read-only calls. Verifier version diagnostics
work from its Windows installation directory but time out from this clone's WSL
`/tmp` directory. The historical baseline remains candidate/unfrozen.

## Results

| Check | Result | Evidence |
|---|---|---|
| Fresh editable installation | exit 0; project resolves MCP 1.30.0 | run-001/install.*, packages.stdout.txt |
| pip check | exit 0 | run-001/pip-check.* |
| Complete unit suite | 126 tests, no skips/failures | run-001/unit.* |
| Structural coordination / YAML parsing | exit 0 / exit 0 | run-001/structural.*, yaml.* |
| FastMCP construction / example listing | exit 0 / exit 0 | run-001/build-mcp.*, examples.* |
| Installed MCP stdio session | 76 unique tools; four read-only calls, no protocol errors | run-001/stdio.* |
| Historical baseline audit at source commit | expected exit 1: 9/20 file hashes and generator aggregate differ | run-001/baseline-hashes.json |
| CLI version from clone in WSL `/tmp` | exit 2, JSON status=timeout, 15-second limit | run-001/version.* |
| Independent Windows `cmd.exe /d /c ver` | exit 0; stderr notes UNC cwd fallback | verifier-unrestricted/ |
| Direct verifyta version from Windows installation cwd | exit 0, 0.124 seconds | verifier-windows-cwd/ |
| Direct verifyta version recheck from original WSL cwd | timeout after 20 seconds, same executable hash | verifier-wsl-cwd-recheck/ |
| Installed CLI version from Windows installation cwd | exit 0, JSON status=ok | verifier-cli-windows-cwd/ |

The stdio calls were `uppaal_list_examples`, `phy_validate_contract`,
`mac_validate_contract` and `sdn_validate_contract`. All three contract results
contain `ok: true`; these are static checks, not verification of network properties.

The exact emitted version is `UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023`.
Its raw banner and binary SHA-256 are preserved. The banner also prints license
attribution, but license acquisition for an actual verification run was not
exercised. No model checking was performed; no verification run ID or scientific
claim is produced here.

The controlled cwd comparison demonstrates an environment-dependent version
startup problem for the same binary. It does not establish its internal cause
or guarantee that changing cwd suffices for model checking. A subsequent runner
Issue should address or document working-directory handling while preserving
absolute model/query paths; implementation changes are outside this report's scope.

## Reproduce

Use a separate clean checkout of the pinned source with these diagnostic scripts,
or this evidence PR. Create a new environment and unused output directories:

```sh
python3 -m venv .venv
.venv/bin/python evidence/healthcheck/20260907-postmerge/reproduce.py --output evidence/healthcheck/20260907-postmerge/reviewer-new --environment-label reviewer-environment
.venv/bin/python evidence/healthcheck/20260907-postmerge/probe_interop.py --output evidence/healthcheck/20260907-postmerge/reviewer-interop-new
.venv/bin/python evidence/healthcheck/20260907-postmerge/probe_verifyta_cwd.py --output evidence/healthcheck/20260907-postmerge/reviewer-windows-new
.venv/bin/python evidence/healthcheck/20260907-postmerge/probe_verifyta_cwd.py --cwd /tmp/uppaal-read-postmerge-20260907 --output evidence/healthcheck/20260907-postmerge/reviewer-wsl-new
.venv/bin/python evidence/healthcheck/20260907-postmerge/probe_verifyta_cwd.py --cli --output evidence/healthcheck/20260907-postmerge/reviewer-cli-new
```

The main capture script installs the project using its own dependency declaration,
then installs PyYAML 6.0.3 for explicit hash auditing. Its exit 1 preserves the
expected baseline drift and the failed version diagnostic; inspect each command
in `run-001/results.json`. Windows probes are intentionally environment-specific;
adjust `--cwd` to the source clone path. These runs used WSL Linux/Python 3.12
outside the Codex sandbox with network and Windows interop available. They are
not a native Windows Python test run. Ordinary project source and manifests were
unchanged throughout. Each run reserves its own workspace, and outputs never
replace an existing directory.

Raw logs preserve original bytes, including Windows CP866 stderr and CRLF.
`integrity.json` indexes every artifact except itself. `source.json` pins the
combined source, source file hashes, baseline hash and merged dependencies.
The original dirty checkout and artifacts supplied by the other agent were not
modified. This report requires independent review.

## Remaining scientific work

P1 must provide parameter sources/calibration and validation decisions (V01–V05).
P2 must provide the instance specification, composition/interface contract and
integrated model (R01/R02/R05/R06). Each needs its own assigned Issue and chat.
Their accepted inputs permit candidate supersession and independent Gate 1 review;
software-test success does not freeze the baseline or start P3/P4.
