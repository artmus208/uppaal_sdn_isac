# Issue #84 — operational installation

Independent Integrator decisions A/B/D and phase-2 scope are recorded in
https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646.
This package installs the exact approved patch, SHA256
`00ec9a8f4755df1a3db8285d41a959bebaf8adb5da9c6831acdebe6f1b95bd9d`.

PR #85 HEAD `6ff7f63b03c16bc3cc4b6acb861604d6fb46906a` was merged into
`read` as `efb6d6c0d936c2c62fbf902e383a144e6b616a0a`. That merge is the
operational branch base. The new manifest SHA256 is
`4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d`.

A/B accept limited P1/P2 applicability and Gate 1 for the exact Full UAV
`uav-service-completion-r1-20261002`, N=1, 51 processes, one request and
one result, with the pinned parameters, instance vector and all 11 query
formulas. These are accepted inputs; all query verdicts remain open.
D excludes universal guarantees, P3 acceptance and R07 closure.

The approved manifest and proposal pins deliberately retain the sealed
preparation snapshot wording (`proposed`, `frozen: false`, pending Gate 1).
The independent Issue decision is authoritative for A/B; installing the
snapshot does not rewrite its history. Original checker output still reports
that preparation status. `operational/audit.py` distinguishes it from the
current independent decision. Neither checker grants C or checks properties.

C remains pending until independent acceptance and operational merge into
`read`, followed by a separate explicit activation decision with actual merge
SHA and UTC time. `activation-record.template.json` is only a preparation
form. It contains no fabricated operational merge or activation timestamp.
Selection authorizes no native execution and transfers no verdicts.

Historical inputs, `manifests/current.json`, the P4 selection policy, manuscript,
generated model and existing evidence are preserved. The standalone proposal
seal remains unchanged; operational files have their own check records.

Reproduce from the operational branch/bundle:

```bash
python3 -B evidence/governance/uav-service-completion-baseline-20261002/operational/audit.py
python3 -B evidence/governance/uav-service-completion-baseline-20261002/check.py --operational --source-history
python3 scripts/check_coordination.py
python3 scripts/check_coordination.py --audit-hashes --commit HEAD --output /tmp/issue84-review-new.json
python3 scripts/check_family_baseline.py
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Full historical hash audit needs PyYAML and a previously nonexistent output.
`--source-history` needs the retained execution checkpoint ref included in the
full handoff bundle. All checks here are static/software checks, not UPPAAL
model checking. See `check-results.json` for actual commands and logs.
