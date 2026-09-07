# Primary sources for P1

Accessed 2026-09-07. These are versioned methodological references, not evidence
that the repository's illustrative constants were obtained from them. No external
simulation or measurement dataset has been imported into this evidence package.

| ID | Primary source and locator | Applicable claim and limit |
|---|---|---|
| S1 | [3GPP TS 38.214 V17.5.0, Release 17, April 2023](https://www.etsi.org/deliver/etsi_ts/138200_138299/138214/17.05.00_60/ts_138214v170500p.pdf), §5.2.2.1, printed p. 88, CQI tables 5.2.2.1-2/3/4 | CQI selection uses a transport-block error probability target dependent on the configured table: 0.1 for table1/table2, 0.00001 for table3. This is a configuration-specific communication criterion; it supplies neither universal SINR boundaries nor sensing-detection thresholds. |
| S2 | [3GPP TS 23.501 V18.5.0, Release 18, May 2024](https://www.etsi.org/deliver/etsi_TS/123500_123599/123501/18.05.00_60/ts_123501v180500p.pdf), §5.7.3.4 p. 190, §5.7.4 table 5.7.4-1 pp. 191–197 | Packet delay budget has UE-to-UPF/N6 endpoints. 5QI 82 illustrates a 10 ms delay-critical GBR budget, packet error rate 10^-4, maximum data burst volume 255 bytes and 2000 ms averaging window (p. 195). Applicability depends on the selected QoS flow and its conditions. This is not a controller response deadline or the entire sensing-to-actuation SLA. |
| S3 | [Lagén et al., New Radio Physical Layer Abstraction for System-Level Simulations of 5G Networks, arXiv:2001.10309v2, 19 April 2021](https://arxiv.org/abs/2001.10309v2), abstract | NR link-level simulation calibrates EESM and SINR–BLER lookup tables for different configurations. This supports the proposed configuration-dependent calibration route. It does not calibrate this repository's 0/10/25 boundaries or establish sensing accuracy. |
| S4 | [ns-3 Model Library, release 3.30, LTE Design Documentation](https://www.nsnam.org/docs/release/3.30/models/html/lte-design.html), “Data PHY Error Model”, “MIESM” | The LTE error abstraction combines per-resource-block information and calibrated link-level error curves. Use as an example of separation between link and system models. LTE is not a validated 6G ISAC simulator; its channel/control assumptions must not silently become assumptions about sensing or the proposed deployment. |
| S5 | [OMNeT++ Simulation Manual, version 5.6.1](https://doc.omnetpp.org/omnetpp5/manual/index.html), §4.15, chapter 12, §27.1 | Signal-based statistics, vectors/scalars and result-file run attributes support the proposed trace-export interface. Vectors preserve time-series observations; scalar aggregates alone cannot reconstruct event order. These documented facilities are not an implemented adapter or an executed experiment in this repository. |

The source versions above are pinned for review, not presented as the newest
releases. A future runner must record the actual simulator version, radio-model
module revision and all deviations from these reference models.

No inspected primary source supplies one universal GOOD/WEAK/OUTAGE or
FRESH/STALE threshold for every waveform, application and topology. P1 therefore
specifies explicit calibration methods instead of attaching an unrelated citation
to a convenient number. Physical safety limits and application freshness bounds
still require a named deployment/service specification or measured model.
