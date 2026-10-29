# REQ-030 iteration 2 — status (2026-10-28 22:35, closed)

All ten items of CONTINUE.md meet their criteria (item 9 as a proposal, D-144, by design: nothing is removed without
the owner's decision). Integrated in `main` `3519eec09` after a full regression, deployed 22:12 with a DBOS backup
first and a smoke after. pictures REQ-021 r15 runs on the durable runtime with subplans, the owner's notes in its
briefs, attestations (T3.2 completed by re-verification) and milestone audits armed for its five audit tasks; the web
dashboard and the remote snapshot show it. Details, evidence and the exact state of both runtimes: [REPORT.md](REPORT.md).

The session that shared this iteration (metodologia-b1) ended at ~21:25 before the final merge; session
metodologia-6d reviewed its integrated branch (`evidence/iter2/review-3cdace8f4.md`), fixed what the review found
(`a6a2706c9`), ran the regression, deployed and resumed REQ-021.

After the first deploy REQ-021 exposed two defects of the durable verifier, both fixed with tests, a full regression and a
third deploy (23:34, `bc7425690`): the engine-owned ledger check of every audit, and the operator's session variables
(`VK_DRIVER_FILES`, the engine's DB URL) leaking into checks. T2.6, T3.2 and T3.11 are accepted; T2.7 (visual audit)
was judged live three times and is held blocked at its round limit: it needs an owner decision (a test-database
credential for visual-audit agents, or the owner's own review). T3.12 runs; every gate depends on T2.7/T2.8.

Update 01:35: two more live findings fixed and deployed (subplan members accepted in their own lines, `ae9665a76`;
an owner's retry reopens a run that ended blocked, `f0df69300`). SP-3 complete (T3.15 audit passed). REQ-021 ended
`blocked` on T2.7; `retry-task` now reopens it (checked live on a throwaway fork of its real history).

Update 2026-10-29 11:30 (session 7db4552d): REQ-021 runs by stages on the durable runtime. The owner's «Ejecutar SP-4»
joined the new stage into the running run (D-149, r16); T94 and T92 completed; T4.1's check, which the sandbox could
never run, was replaced with the owner's approval (r17, D-152) and the task completed. Methodology integrated today:
D-146, D-147, D-149, D-150, D-151; D-152 waits for its full regression. Details in [REPORT.md](REPORT.md).
