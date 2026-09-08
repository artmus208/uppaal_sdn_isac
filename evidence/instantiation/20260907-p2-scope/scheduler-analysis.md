# R05 — Existing MAC scheduler A_SCH

Input: `generated:mac:with_observers` in `inventory.json`, generated from the
pinned MAC default profile with mode=with_observers and layout=readable.
Implementation: `src/uppaal_mcp/mac/generator.py`, `_add_a_sch`, lines 303–313
at commit `7baa86e8d0d9eb2fc2df8d728a360c6b7cfb91bb`. The policy predicates and
selection function are at lines 287–297. This is an inspection of existing code.

## Locations and invariants

| Location | Invariant | Meaning |
|---|---|---|
| Idle (initial) | none | Wait for scheduling tick |
| CollectKPI | c_sched <= D_collect | Await a PHY report or choose stale fallback |
| SelectMode | c_sched <= D_sched | Apply the finite policy priority chain |
| ApplySchedule | none | Attempt binary command send |
| WaitPHYAck | c_phy_ack <= D_phy_ack | Await ACK or report timeout |
| ScheduleFailure | none | Publish failure report and return |

Defaults are D_collect=2, D_sched=5, D_phy_ack=3 abstract units. Neither clock is
local to the XML template: both are in the MAC global declarations. Their values
and all reset sites must be considered in the complete composition. The generated
`scheduler-edges.md` reproduces **all nine edges** without hand transcription:
source/target, guard, synchronization and update. Its check reads the raw XML
inventory and compares the exact rendered table.

## Reading the transitions

1. `mac_tick?` leaves Idle, resets c_sched and clears mac_report_sent.
2. A `phy_kpi_report?` within the collection bound enters SelectMode and resets
   c_sched again. This is a fresh scheduling window, not elapsed time from tick.
3. Nonfresh input or equality c_sched==D_collect enables the direct constrained
   fallback to ApplySchedule. It resets c_phy_ack and sets the stale-report reason.
4. In SelectMode, gP0 means either actual or mapped resource is exhausted; the
   scheduler goes to ScheduleFailure, marks a pending report and clears silent_accept.
5. Otherwise select_mac_policy runs, c_phy_ack resets and command_pending is set.
   The priority order is exhaustion, overflow/violated delay, critical queue with
   critical communication, allowed critical sensing, joint resource conflict,
   stale/missing KPI, available resource, default constrained. Raw predicates can
   overlap. policy_enabled_count counts those predicates, not executed schedules.
6. `mac_schedule_cmd!` enters WaitPHYAck and sets pending=true. **It does not reset
   c_phy_ack**. Time spent in ApplySchedule therefore consumes the ACK budget.
7. `phy_ack?` at or before D_phy_ack returns Idle and clears pending/timeout.
8. At exact equality D_phy_ack an internal timeout edge instead enters
   ScheduleFailure and records REASON_PHY_ACK_TIMEOUT, clearing pending.
9. `mac_report!` returns Idle after setting report_sent and clearing pending.

## Consequences and limitations

The clock reset on edges 3/5 means that if ApplySchedule waits beyond three
units, taking edge 6 would violate WaitPHYAck's target invariant. No invariant
on ApplySchedule itself forces earlier sending. This is a local semantic
observation, not a demonstrated reachable timelock. The current binary command
partner is A_ENV_MAC, whose command-receive loop is unguarded; that environment
also offers ACK without checking whether PHY processed a command. Thus the
closed projection cannot establish a real PHY command-to-ACK relation.

At collection deadline a report receive and fallback can compete. At ACK deadline
ACK and timeout can compete. No explicit priority chooses success or failure in
these cases. A future adapter must not remove the timeout merely because it can
also emit ACK. Similarly an enabled policy edge is not forced immediately by its
guard, and an upper-bound invariant alone does not establish every promised
response. These conclusions use the distinction between guards, invariant-valid
targets and delays in [UPPAAL semantics](https://docs.uppaal.org/language-reference/system-description/semantics/).

A_SCH has no sdn_policy_cmd receiver. The booleans read by its sensing-priority
policy are currently written by its environment, not by actual SDN delivery.
The stale fallback does not set phy_command_pending until command emission;
the normal path sets it earlier. Consequently ObsPhyAck's pending-flag trigger
can refer to different starting points on the two paths. Its Idle→Wait guard is
not a synchronization with the command; delayed observation is a review concern.

The six locations and nine edges retain only scheduling phase, finite priority
decisions, deadline clocks and failure flags. They omit packet identities,
explicit buffer capacity, detailed PHY configuration execution and distributed
controller delivery. These omissions explain the compact automaton and bound
its claims. No statement here asserts deadlock freedom, determinism of the whole
network, reachability, a satisfied query or measured state-space reduction.
