## Coordination

- Closes issue: <!-- #123 -->
- Workstream: <!-- P0-P7, P9a, P8, or P9b -->
- Atomic review-comment IDs: <!-- C01-C06, R01-R07, V01-V05, I01-I06, D01; or N/A — coordination-only -->
- Baseline manifest/ID/SHA-256: <!-- path; baseline_id; manifest sha256 -->
- Baseline commit SHA: <!-- full 40-character SHA -->
- Head commit SHA: <!-- full 40-character SHA -->
- Source branch: <!-- dedicated workstream branch; `read` only for final integration -->
- Target branch: <!-- `read` for workstreams; `main` only for final `read` -> `main` PR -->
- Owner: <!-- @account -->
- Reviewer: <!-- @account -->

## Scope

Declared exclusive write scope:

<!-- Copy the exact paths/globs from the workstream issue. -->

Changed paths and reason:

<!-- List intentional changes. Explain any deviation from the declared scope. -->

Out of scope:

<!-- State what this PR deliberately does not attempt to solve. -->

## Tests and acceptance

Commands run and results:

```text
command -> result
```

Acceptance criteria satisfied:

<!-- Map each criterion from the workstream issue to a result. -->

## Evidence

- Evidence class: <!-- machine / document-source / editorial-coordination / none -->
- Evidence artifacts: <!-- paths, URLs, run IDs, logs, traces, measurements, citations -->
- Model/source hashes: <!-- if applicable -->
- Licensed UPPAAL execution: <!-- performed / required later / not applicable -->

Do not describe unit-test success as model checking. If UPPAAL verification was
not run, state that directly and leave the scientific claim unverified.

## Handoff

- Output artifacts:
- Downstream workstreams unblocked:
- Integration instructions:
- Known limitations or unresolved conflicts:

## Checklist

- [ ] The linked workstream issue is complete and names one owner and one reviewer.
- [ ] This PR is based on the declared baseline SHA, or the deviation is documented.
- [ ] Every changed path is inside the declared write scope.
- [ ] Atomic review-comment IDs are preserved without silently merging requirements.
- [ ] Dependencies and gates from the issue are satisfied.
- [ ] A P5 handoff is not marked accepted before its P3 evidence dependency is accepted.
- [ ] Relevant automated and manual acceptance checks are reported above.
- [ ] Generated evidence records its producer, inputs, hashes, and reproducible command.
- [ ] Verification claims, if any, reference actual licensed run evidence and run IDs.
- [ ] This workstream PR targets `read`; if it targets `main`, it is the final PR whose source is `read`.
- [ ] Unified manuscript edits are owned by P9a/P9b or explicitly handed off.
- [ ] Manifest-governance edits have an explicitly declared coordination owner.
- [ ] The handoff section is sufficient for another account to continue without chat history.
