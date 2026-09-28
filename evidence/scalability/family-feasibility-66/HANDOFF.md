# Handoff — Issue #66

- Deliverable: P2 runnable candidate UAV family N=1,2 and executable composition
  contract; shared abstract BS service capacity one per epoch.
- Owner/account-id: `vadimnbkg`. Independent review/acceptance pending.
- Branch: `codex/vadimnbkg/66-family-feasibility`; target `read`.
- Actual base: `05ac107789532b6d2eac9914433a4b8408835057`; no advance from the supplied base.
- Published source checkpoint: `a14b823de8415c6e73fd01607ce0a8343e2f2d09`.
  Tree `48a81c6430a43986b5a1bd232bb028451f2bed9a`, identical to local source
  checkpoint `1cfa2e54744587e5ae72e5cdcd3bb15bbb74d493`.
- Final artifact HEAD and PR URL: recorded in the linked GitHub Issue/PR handoff
  after publication (a commit cannot embed its own hash). The final PR includes
  the source checkpoint as its ancestor.
- Write scope: `evidence/scalability/family-feasibility-66/**` only.
- Working tree for published-source checks: clean. Final handoff tree: clean after
  committing generated evidence; runtime environments, scratch checkout and bundles ignored.
- Existing source, manifests, frozen inputs, previous evidence and manuscript unchanged.

## Reproduction and results

Run `python3 -B evidence/scalability/family-feasibility-66/generate.py` from the
checkout root. `generate.py --check` compares exact bytes; `check.py` validates
composition, 12,160 allowed queue-step cases, 80 singleton macrostep comparisons
and 11 negative controls. Those are static/local expression checks, not UPPAAL
model checking. Full isolated Git-tree reproduction is in
`checks/clean-reproduction.json`; per-file integrity in `artifacts-sha256.json`.

Repository checks: 200 tests OK, 57 baseline hashes and both aggregates unchanged,
server/CLI smoke OK. Exact commands and known limitations are in
`checks/validation.json`. No failed or skipped repository tests.

Final tool evidence: `checks/uppaal-published-005/runs.json` and its raw logs.
UPPAAL 5.0.0 (rev. 714BA9DB36F49691), June 2023, observed working license.
Both generated XML compile; both candidate query files parse. `E<> true` is the
only executed formula. Invalid XML/query controls are rejected. Scientific
queries have no verdicts and are not part of this bounded smoke.
All run identities, source/model/query hashes, tool version, environment,
commands and stdout/stderr references are in the run record. Native peak memory
and explored-state metrics are not available and are not invented.

N=1 XML SHA-256: `5234cb087e5274798926d516dedc77d1f9542ea7df59cec39f83859771ce1385`.
N=2 XML SHA-256: `e7ac599140b7beeb94acdf0e3535a727c2eccc40aa15314afa3371eb09700208`.
Other hashes and the exact vectors/parameters: `generated/n*/metadata.json`.

## Durable transport and next step

Primary transport: published GitHub branch in `artmus208/uppaal_sdn_isac`.
Direct SSH/HTTPS push was unavailable; authenticated GitHub Git-data APIs
published an exactly matching tree. The source was then fetched over HTTPS;
final successful tool checks refer to that public source SHA.

Owner-local full checkpoint bundle:
`/mnt/c/Users/musta/Desktop/pySources/mcp_uppaal/.worktrees/66-family-feasibility/evidence/scalability/family-feasibility-66/handoff/local-checkpoints.bundle`.
It preserves prepublication source commits and the redundant `uppaal-load-004`
parser checks. They are not substituted for the final public-source evidence.
A final bundle is saved beside it as `final.bundle` after publication.

Next: independent P2/P4 review of the shared service capacity, optional arbitration,
per-UAV controller contexts and property/size domain; P0 records a new Gate 1
before P4 resource measurements. N=1 correspondence is a checked local macrostep
argument, not a whole-system equivalence proof. Old P3 evidence is not transferred.
No Glonina comparison, scientific gate acceptance or R03/R04/C06 closure.
