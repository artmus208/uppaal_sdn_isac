# Issue #6 governance implementation

The accepted [decision](decision.md) replaces shared run storage with disjoint
P3/P4 paths and adds an explicit baseline hash audit. The historical baseline
file is unchanged, `frozen: false`, Gate 1 pending. No replacement source commit
has been selected: accepted scientific P1/P2 inputs are still required.

## Reproduction

From an isolated checkout of this PR:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e . 'mcp>=1.28,<2' PyYAML==6.0.3
.venv/bin/python scripts/check_coordination.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/check_coordination.py --audit-hashes --commit 11bd69bdca9a1209f820258b3732b3c865f79035 --output /tmp/issue6-new-base-audit.json
.venv/bin/python scripts/check_coordination.py --audit-hashes --output /tmp/issue6-new-checkout-audit.json
```

Choose unused output paths. Structural checks require only the standard library;
explicit hash auditing requires PyYAML. Audit exit codes: 0 = all recorded hashes
match, 1 = drift or missing inputs, 2 = invocation, parsing, or output error.
A Git audit reads both manifest and input files from the resolved commit; a
checkout audit reads current exact bytes. Aggregate records preserve listed
source order and bytewise generator path order. Hash equality is not verification.

## Results and limitations

[checks/commands.json](checks/commands.json) records exact commands, exit codes,
runtimes and raw-log hashes. Python 3.12 / WSL Linux, MCP 1.29.1, PyYAML 6.0.3:

- 79 unit tests, no failures or skips, including five governance test methods.
- Structural checks, YAML parsing, pip check, FastMCP construction, example
  listing and Git whitespace check: exit 0.
- [Base Git blobs](checks/base-hashes.json) and
  [isolated checkout](checks/checkout-hashes.json): 7 of 20 file hashes differ,
  plus one generator aggregate; both audits return expected exit 1.
- `version` returns process exit 0 on this historical CLI, but its JSON reports
  `status=error`, verifier returncode 1 and the exact WSL error
  `UtilBindVsockAnyPort:309: socket failed 1`. This is a failed diagnostic,
  not verifier availability or model checking. See preserved version stdout.
- MCP is explicitly constrained for these tests because the independent startup
  dependency fix in PR #7 is not part of this Issue. This PR does not claim a
  fresh unconstrained installation works.

Tests use JSON (a YAML subset) through a fixture parser so the ordinary CI suite
needs no new dependency. Real YAML parsing and audit execution are separately
recorded above with PyYAML. Cases cover exact CRLF bytes, dirty versus committed
manifests, both aggregate ordering rules, missing inputs, unsafe paths, unknown
hash construction, existing-output preservation, and invalid storage scopes.

The remote `read` observed during handoff is
`f67177f898c1354cb53a0f2a697cf859cc705647`; its changes since the Issue base do
not touch this PR's implementation paths. The branch retains the exact Issue
base. Its newer model artifacts have not been selected as a scientific baseline.
Original checkout and supplied agent artifacts were read-only inputs.

Independent implementation review remains required. This PR does not accept
Gate 1, freeze a baseline, run model checking, or merge any healthcheck PR.
