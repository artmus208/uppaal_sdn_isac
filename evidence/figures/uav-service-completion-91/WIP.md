# P7 interrupted preparation checkpoint

Issue: https://github.com/artmus208/uppaal_sdn_isac/issues/91
Owner: artmus208. Independent Reviewer/Integrator: vadimnbkg.
Branch: codex/artmus208/91-uav-figures.
Base: 452571598d4a5c1e070dace3a918ea737904e239.

The user interrupted generation and subsequently selected a different scientific
task on 2026-10-04 (Europe/Moscow). This checkpoint preserves unfinished work;
it is not a reviewable figure bundle and does not satisfy I03-I05.

Present: byte-identical frozen model copy, manuscript llncs.cls v2.24, dependency
declarations and an unvalidated XML-derived figure/label exporter. No figure PDF,
compiled preview, print-size inspection, completed placement map or independent
review has been produced. The attempted generation/TeX command was interrupted;
no successful execution is claimed. No verifier/simulation/replay was run.

Next P7 step: inspect the exporter, generate APP only, compile and visually check
its PDF at 122 mm text width, fix layout/provenance issues, then produce the other
three diagrams and complete the original Issue acceptance checklist. Native
UPPAAL tools were registered in the Windows server but absent from the chat;
the Issue permits explicitly declared XML-derived vector export as a fallback.

Only this directory is in scope. Existing UI implementation changes remain in
the separate a2d7 checkout. Production XML, generator, manuscript and manifests
have not been modified by this checkpoint.
