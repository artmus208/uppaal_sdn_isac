# MAC-Specific Layer Progress

Дата: 2026-06-08.

Статус: planned, not implemented.

Цель: реализовать MAC-specific MCP слой для
`MAC_resource_scheduling_formalization.tex` по тому же инженерному шаблону, что
PHY-specific слой, но с reusable layer framework для последующего SDN/RIC и
Application scaling.

## Уже зафиксировано

- Источник MAC слоя: `MAC_resource_scheduling_formalization.tex`.
- PHY слой используется как baseline, но MAC не должен быть тупой копией PHY.
- Reused infrastructure:
  - generic `verifyta` runner;
  - generic XML/query validation;
  - report/artifact pattern;
  - readable layout concept;
  - Graphviz/SVG diagram export concept;
  - trace explanation concept;
  - benchmark/scenario pattern.
- Target composition:
  - `A_MAC = A_SCH || A_Q || A_BUF || A_RSRC || A_MAC_AGG`;
  - `A_SYS_MAC = A_MAC || A_ENV_MAC`.
- Target automata:
  - `A_SCH`;
  - `A_Q`;
  - `A_BUF`;
  - `A_RSRC`;
  - `A_MAC_AGG`;
  - `A_ENV_MAC`.
- Target observers:
  - `ObsPhyAck`;
  - `ObsQueueCritical`;
  - `ObsSensingCritical`;
  - optional `ObsBufferOverflow`;
  - optional `ObsMacReportFreshness`.

## MAC article facts already identified

- MAC принимает finite PHY classes and SDN policy commands.
- MAC выдает PHY commands: resource allocation, beam update, sensing boost, comm priority, constrained mode.
- MAC reports SDN/RIC: queue, delay, loss, resource deficit and local contract failure reasons.
- MAC explicitly must not perform:
  - rerouting;
  - slice migration;
  - global recovery;
  - admission control.
- Core deadlines:
  - `D_collect`;
  - `D_sched`;
  - `D_phy_ack`;
  - `D_queue_crit`;
  - `D_buf_report`;
  - `D_mac_report`;
  - `D_phy_report`.
- Core classes:
  - `QueueClass`;
  - `BufferClass`;
  - `DelayClass`;
  - `DropClass`;
  - `ResourceClass`;
  - `SensingDemand`;
  - `CommDemand`;
  - `KPIFreshnessClass`;
  - `ScheduleMode`;
  - `MacReason`.
- Required broadcast reports:
  - `phy_kpi_report`;
  - `mac_report`.
- Required handshake channels:
  - `mac_tick`;
  - `sdn_policy_cmd`;
  - `service_priority`;
  - `phy_ack`;
  - `mac_schedule_cmd`;
  - `beam_update_cmd`;
  - `sensing_boost_cmd`;
  - `constrained_mode_cmd`;
  - `resource_reject`.

## Main Open Work

- Implement reusable layer framework.
- Implement MAC IR.
- Implement MAC LaTeX extractor.
- Implement `alpha_MAC`.
- Implement MAC UPPAAL generator.
- Implement MAC static validators.
- Implement MAC property pack.
- Implement MAC reports/artifacts.
- Implement MAC trace explanation.
- Implement MAC MCP tools and CLI commands.
- Implement MAC scenarios/benchmarks/tests/golden fixtures.
- Update docs and command reference.

## Verifyta Status

- MAC `verifyta` checks are not runnable yet because MAC generator does not exist.
- First useful smoke target:
  - generate closed MAC model;
  - static validate;
  - run one small reachability query;
  - run static property pack;
  - then run observer scenarios.

## Acceptance Checklist

- [ ] `mac-extract --tex MAC_resource_scheduling_formalization.tex` returns validated contract JSON.
- [ ] `mac-generate --layout readable --output-dir ...` writes model, queries, contract and maps.
- [ ] `mac-property-pack --output-dir ...` writes query metadata.
- [ ] `mac-verify-property-pack --static-only` passes.
- [ ] `mac-validate-benchmarks` passes with expected positive/broken split.
- [ ] MCP tools expose the same workflow as CLI.
- [ ] Existing PHY functionality remains green.
