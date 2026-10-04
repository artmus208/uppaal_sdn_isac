# Shared-capacity projection and Glonina applicability (#101)

Work in progress. One P4 scientific deliverable; independent acceptance pending.

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/101
Owner: vadimnbkg. Base: `read` / `f0fcd770e3e6b93f99868b9116e4f0929f60d0fa`.
Branch: `codex/vadimnbkg/101-r04-compositional-proof`.
Write scope: this directory only.

Research question: establish the accepted finite UAV family's shared-capacity
invariant by a justified projection, and assess the precise applicability of
Glonina's scalable component-verification method to the present network.

Selected input: `uav-family-r1-20260929`, N=1,2,3,4; manifest SHA256
`5480bef5b00020735259f10eb43bdd9bc79ebc364a3bbcacad34c78fd0552cbf`.
Family activation: PR #75, comment 5891123461. Operational v2 activation: #64,
comment 5878071165. Existing #76 runs and all models are read-only.

Planned package: explicit mathematical argument, conservative proof-premise
checker with mutation controls and certificates, primary-source comparison,
historical-run index, integration-ready English text and R04 response, checks
and handoff. Mathematical argument, static checking and native model checking
remain separate evidence kinds. No new verifier run or baseline modification.
