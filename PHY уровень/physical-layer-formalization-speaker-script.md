# Speaker script

Target duration: about 4-6 minutes.

## 1. Title
This talk presents the physical layer formalization for an SDN-enabled 6G ISAC network. The focus is resource orchestration and resilience, not a full radio-physics simulator. Timed automata do not calculate SINR, detection probability or CRB directly. These values are estimated outside the automata. Then they are mapped to finite classes. These classes become the inputs for contract timed automata, which can be checked by UPPAAL-style verification.

## 2. Objective and outline
The objective is practical: to define a physical layer abstraction that can be used inside a model checker. The layer must report communication and sensing degradation to MAC and SDN within bounded time. The talk follows five points. First, I show the position of PHY in the hierarchy. Then I explain the abstraction function, the automata, the sensing capability metrics, and finally the verification logic with observer automata.

## 3. Methods
The method has three steps. First, the estimator layer computes physical values, such as SINR, BLER, probability of detection, false alarm rate, beam error, and age of sensing. Second, the abstraction function maps these values to finite classes. Third, these classes become guards, updates, and report events in timed automata. This design keeps the model finite, avoids an unrealistic state space, and still preserves the information needed by upper control layers.

## 4. PHY position
The physical layer is the lower measured part of the hierarchy. The service layer defines SLA requirements. SDN selects global policies and recovery actions. MAC implements radio-resource scheduling, such as pilot density, PRS resources, power, MCS, and beam commands. PHY receives these commands, observes the environment through estimators, classifies the current state, and reports degradation. This makes PHY a measurement and reporting layer for orchestration, not the global decision maker.

## 5. Discrete abstraction
The key bridge is alpha PHY. It maps measured values and configuration values to a discrete set. Continuous values are not used directly in guards. For example, SINR is converted into OUTAGE, LOW, OK, or HIGH. Similar classes are used for channel, signal, beam and sensing quality. The abstraction is conservative. If a value is close to a boundary or has uncertainty, it is mapped to the worse neighboring class. This reduces false safety in verification.

## 6. Contract automata
The PHY layer is decomposed into four child automata and one aggregate automaton. A CH tracks the channel class. A SIG tracks the signal configuration, for example pilot-based or payload-assisted sensing. A BM tracks beam search, tracking, misalignment and recovery. A SQ evaluates sensing quality. Their reports are broadcast, because more than one consumer may need the same event. A PH combines the reports and publishes one global PHY state.

## 7. Results
The result is a working formal PHY abstraction. First, radio estimators are separated from the automata core, so the model does not pretend to calculate physics internally. Second, communication degradation and sensing degradation are explicit states. This is important because a communication problem and a sensing problem are not always the same. Third, reports, recovery actions and deadline requirements can be checked with observer automata and clocks.

## 8. Conclusion and future implementation
To conclude, the PHY layer is a finite and conservative contract layer. It does not claim that timed automata calculate detection probability, false alarm rate, or CRB. SensCAP-type metrics are used at the estimator or SDN-score side, then converted to classes such as ProbabilityLimited, FreshnessLimited, or CapacityLimited. The next implementation step is to calibrate thresholds with simulation or field traces, connect PHY reports to MAC and SDN policies, and check bounded response observers in UPPAAL XML or XTA.

## 9. Thank you
This completes the presentation. I am ready to discuss abstraction thresholds, automata interfaces, and the UPPAAL implementation details.
