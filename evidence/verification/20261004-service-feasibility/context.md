# Inputs, project context and scientific claim map

The user requested a substantial autonomous scientific task after accepting all
prior MRs. On 2026-10-04 this chat inspected all seven other accessible Codex chats
of this project and the saved repository chat history inventory. No archived Codex
chat belonged to this project. This is a focused synthesis, not a copy of private
chat logs and not evidence of scientific acceptance.

| Chat, exact title | Relevant outcome and implication |
|---|---|
| Спланировать проект и научную работу | #89 continuation reported Q4/Q6 false, Q2/Q3/Q5 timeout, local raw artifacts; the unresolved need is operating/progress assumptions. |
| Научная новизна | Main theoretical opportunity is a concrete interaction failure/condition; combining UPPAAL, hierarchy and deadlines alone is not a new method. |
| Найди задачу в проекте | #95 extensions and #100/#105 portability/report status completed; do not repeat them. |
| Исследовать агентный UI UPPAAL | Existing UI operation research; GUI availability is not model-checking evidence. |
| Найти работу с AGENTS.md | #99/#104 fixture/cache corrections complete. |
| Найти новую задачу | #101 shared-capacity proof complete; fairness, delivery and SLA explicitly excluded. |
| Проверь доступ к операциям | #108 truthful completion proof and P7 work; terminal receipt safety differs from progress. |

Live canonical read was fetched into a clean isolated clone. Base commit is
e5c299d0b426e57652cb8a78f37ae770949b53b1. It contains accepted/merged #97/#98,
#102/#103/#106/#107/#109/#110/#90/#112/#114. The original Desktop checkout is
dirty and was read only. GitHub Issues still show several old in-review snapshots;
the user explicitly supplied acceptance of all previous MRs, and live PR #110
metadata confirmed its actual merge at 82ed885dcd04eb55593f258445fa385488400e65.
No inference that all scientific requirements/gates are closed is made.

Selected scientific source commit: 61386aa358805082b705dcd00c8cbfde5fb98248.
Baseline: manifests/baselines/uav-service-completion-r1.yaml;
SHA256 4b4bf71f55767123cc5934074024179289fa5ad3355fa4c0e37385e8261ef98d.

Authority and scope:

- [Candidate acceptance #83](https://github.com/artmus208/uppaal_sdn_isac/pull/83#pullrequestreview-5388261528).
- [Exact limited A/B and Gate 1 #84](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5946722646).
- [Post-merge activation #84](https://github.com/artmus208/uppaal_sdn_isac/issues/84#issuecomment-5947256320), actual operational merge 46bf268c66d6ec2c106ae4ce8e8d5f893315ad91, decision 2026-10-02T07:18:22Z.
- [Scientific v2 activation #64](https://github.com/artmus208/uppaal_sdn_isac/issues/64#issuecomment-5878071165).
- [Accepted causal/safety dependency #110](https://github.com/artmus208/uppaal_sdn_isac/pull/110); its source and premises are exact pinned read-only dependencies of the new checker. Its run-status claims remain as originally recorded.
- [This scoped deliverable #115](https://github.com/artmus208/uppaal_sdn_isac/issues/115).
- [Primary UPPAAL timed-system semantics](https://docs.uppaal.org/language-reference/system-description/semantics/), read on 2026-10-04; paraphrased for the proof's discrete/delay convention.

| Claim ID | Statement | Evidence and permitted interpretation |
|---|---|---|
| SF1 | Exact age accounting for a dispatched/received FIFO token | Lemma 1/Theorem 1, certificate writer/epoch facts; mathematical argument conditional on actual events. |
| SF2 | Initial rank >=2 precludes success in M | Corollaries 1/2; implication over finite histories, no assertion that ranks are reachable. |
| SF3 | Time-divergent emitted executions enter an APP terminal by age 40 | Theorem 2, bounded graph and reset closure; excludes nondivergent/maximal finite executions, success not implied. |
| SF4 | Explicit successful-service contract | Last proof section; undischarged environmental/scheduler/timing conditions are labelled assumptions. |

All four are mathematical claims pending independent scientific acceptance, with
static-validation certificates and no machine model-checking verdict. This package
supports C02/C03/C04/C05 discussion; primary owners and requirement closure remain
unchanged. New verification evidence run_id/tool_version: not_applicable.
