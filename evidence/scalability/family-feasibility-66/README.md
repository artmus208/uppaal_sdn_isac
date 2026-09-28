# Two-size SDN/ISAC family candidate

Issue [#66](https://github.com/artmus208/uppaal_sdn_isac/issues/66), P2. N=1 has
50 automata; N=2 has 99. UAV contexts share one queue-service budget: at most
one abstract unit per MAC epoch across the network. This is a runnable candidate,
not an accepted family or a P4 resource result.

From the repository root, Python 3.10+ (no third-party modules for the prototype):

```bash
python3 -B evidence/scalability/family-feasibility-66/generate.py
python3 -B evidence/scalability/family-feasibility-66/generate.py --check
python3 -B evidence/scalability/family-feasibility-66/check.py
```

The first command writes both `generated/n1` and `generated/n2`: XML, candidate
queries, parameters, instance vectors and exact-byte hashes. Input files are
hash-pinned in `inputs.json`; changes fail closed. All outputs stay inside this
Issue's directory. The source is the committed frozen XML, so generation needs
neither the old generator's Python dependencies nor a UPPAAL license.

[CONTRACT.md](CONTRACT.md) defines routing, arbitration, state/clock ownership,
N=1 correspondence, every semantic difference and open decisions. Static tests
are not model checking. The future property files have no verdicts. Tool-load
checks only establish parser/type/initial-state acceptance, not C01/C02 or progress.

Before P4: accept the shared-server/per-UAV-controller abstraction, agree the
size domain and query schema, then freeze a new baseline through P0/Gate 1.
Optional service permits starvation; there is no packet/interference model or
physical calibration. Frozen observer/admission limitations remain. Old P3
results do not transfer automatically; R03/R04/C06 are not closed.

Check results and exact handoff will be added after the committed candidate is run.
