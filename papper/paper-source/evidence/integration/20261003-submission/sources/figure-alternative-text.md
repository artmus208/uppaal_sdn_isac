# Figure text alternatives

These descriptions accompany the article for author/typesetter accessibility work.
Full guards, updates and all omitted edges are in figures/transition-catalogue.json.

1. PHY fragment: a channel report triggers sensing evaluation. A normal-scenario report enters SensingQoSOk. An admitted job starts JobMeasuring. Acquisition at five time units can succeed or fail; an inactive job may retire separately without an equality-to-five requirement.
2. MAC fragment: a MAC tick triggers collection of PHY reports and policy selection. Stale/deadline fallback can apply a constrained schedule; insufficient resources produce failure. Applying a schedule sends a PHY command. ACK and ACK-timeout terminate this command interaction, independently of application result delivery.
3. SDN/RIC fragment: an admission request enters Evaluate. Ordered predicates select rejection, constrained mode, sensing boost, communication priority or normal mode. The figure does not show return edges or other report-triggered entries.
4. APP fragment: demand builds a request, readiness precedes emission, and admission can accept or reject it. Valid matching receipt can complete an accepted request before or at age forty. Invalid identity/quality, sensing failure, loss, queue failure, timeout and cancellation remain separate unsuccessful outcomes. Degraded-admission branches and additional transitions are catalogued separately.

The four publication panels are XML-derived illustrations. The compressed app-native-full.eps.gz is a separate, unedited native UPPAAL export of the complete APP template; it is not used as a print-size article figure.
