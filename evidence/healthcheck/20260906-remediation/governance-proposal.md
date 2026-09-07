# Decision required for issue #6

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/6

This is a reviewable proposal, not an accepted decision or a manifest edit.
The candidate remains `reviewer-r1-candidate`, `frozen: false`, Gate 1 pending.
All software fixes are independent of scientific P3 acceptance.

## Baseline provenance

The recorded baseline explicitly describes an old dirty working tree rather
than an exact commit. The fresh read-only audit finds 6 of 20 file hashes differ
in the original checkout, plus the generator aggregate. Exact blobs at commit
`11bd69bdca9a1209f820258b3732b3c865f79035` differ in 7 of 20 records, plus the
generator aggregate. `current-checkout-hashes.json` and `base-commit-hashes.json`
record every expected/current pair, the manifest hash, commands and environment.
These are different input sets; checkout bytes must not be described as commit
bytes. The scientific-source aggregate matches in both modes.

The existing structural checker does not audit these model/generator hashes.
`audit_baseline.py` now provides a separate fail-on-drift diagnostic without
rewriting the baseline. It returns exit 1 for the recorded mismatches. A matching
hash would establish input identity only, not model adequacy or verification.

Approve the following replacement procedure:

1. Preserve the historical capture. Select an exact clean source commit after
   the intended model/generator changes have been accepted. Record an explicit
   candidate supersession; do not silently refresh the old snapshot's hashes.
2. Pin all new model, generator, source and query hashes to that commit. Record
   per-configuration model/query hashes separately from shared source hashes.
3. Keep the replacement candidate unfrozen until accepted P1/P2 results supply
   the integrated model, interface contract, parameters, instances and queries.
4. Record native Windows verifier availability as a dated, environment-specific
   diagnostic. Preserve the historical WSL license failure as historical context.
5. Let an independent integrator accept Gate 1 only after its full checklist is
   supported by accepted artifacts. No hash refresh substitutes for that gate.

## Run storage and write scopes

The current common path `evidence/runs/<run_id>/` is outside both typical P3 and
P4 write scopes. Prefer the following exact mapping in a dedicated governance PR:

```yaml
run_evidence_contract:
  storage_pattern_by_workstream:
    P3: "evidence/verification/runs/<run_id>/"
    P4: "evidence/scalability/runs/<run_id>/"
  manifest_filename: run.yaml
```

Replace the single `storage_pattern` entry with this mapping, leaving the other
run contract fields unchanged. Each Issue must reserve its unique run IDs under
the appropriate workstream root. This fits the existing disjoint P3/P4 scopes.
The governance checker should test the mapping and containment, and expose hash
checking separately from historical candidate structural checks. No shared
generated evidence should be moved or overwritten as part of this change.

## Exact approval requested

Integrator approval in issue #6 is needed for the replacement procedure and
storage mapping above, an owner assignment, and the inactive proposed manifest
write scope in that Issue. No scientific Gate 1 approval is requested here.

Authority: `AGENTS.md`, “Ownership и write scope”: “Любой файл в `manifests/`
меняется только в отдельном governance Issue с manifest-specific write scope и
принятым решением Integrator.” `CONTRIBUTING.md` section 8 repeats that rule.
The separate Issue exists; the accepted Integrator decision remains outstanding.
