# REQ-012 — Acceptance record (who verified what, and how independently)

Evidence sources: **R** = fresh reviewer agents (spec / standards / per-criterion rounds, same provider, no access to
AC-TRACE); **G** = delegated audit by Gemini 3.8 flash-high on an isolated copy (other vendor, 101 adversarial checks,
claims C1–C4); **P** = plans written by planner sessions with no context from the methodology documents alone
(`independent-evidence/REQ-901/902/903`, verified by `verify_independent.py` → `VERIFICATION.json`);
**T** = automated tests; **I** = the six implementer-authored trials (`planning-trials/`, regression guards); **Q** = independent content review of P (`QUALITY-REVIEW.md`).

| Criterion | Verdict | Independent evidence | Remaining honest limit |
|---|---|---|---|
| G1 sync: ids / titles / repos / after / verify | VERIFIED | R spec round (could not break); G C1 15 checks; P corruption battery on 3 foreign plans | — |
| G2 every launch path binds the approved revision, a launch never freezes | VERIFIED | R spec+standards+re-verification (found resume/foreground gaps, fixed); G C2 20 checks | explicit `--force` is the owner's approval (recorded `launch-forced`) |
| G3 classification justified with evidence | VERIFIED (existence), NOT semantic truth | R; G C3 53 checks; P plans' `file:`/`command:`/`precedent:` verified live | a fluent but false justification passes (P-023): no deterministic validator can judge truth |
| G4 real planning trials | VERIFIED | Q: three plans reviewed on content by a reviewer who did not write the validator (ACCEPT WITH CHANGES, planners revised, re-verified) · P: 3 foreign plans on 3 real repos (trainingapp, maros, pictures) pass the gate, corruption battery and approval→drift lifecycle; I: 6 trials 182/182 | the planner of REQ-902 fixed its own soft finding (undeclared new DTO file) after validation feedback; all three plans now pass `verify_independent.py` 3/3 |
| G5 suites, docs, plan state, criteria | VERIFIED | T (module, methodology, scheduler core); R found the stale docstring / environmental scan, fixed | — |
| AC-01 methodology preserved | PASS | R per-criterion; T legacy launch/approve/resume tests | — |
| AC-02 PLAN.json parses and passes schema | PASS | R; G; P | — |
| AC-03 complete classification, no defaults | PASS | R falsification; G C3 | — |
| AC-04 independent taxonomies | PASS | R; P (REQ-901 T7 low/isolated, T3 high/high) | — |
| AC-05 dependencies verified, cycles blocked | PASS | R | — |
| AC-06 shared resources explicit, no parallelism guarantee | PASS after fix | R round 3 said PARTIAL → text promising parallel safety is now refused (EN/ES) and `parallel*` keys are scheduling keys; G C3 covered it | prose that merely implies it cannot be detected |
| AC-07 verifiable criteria, no unexecuted success claimed | PASS | R; G; P commands/precedents verified to exist | existence of a command ≠ that it was run |
| AC-08 `full_system` decomposed or documented exception | PASS | R; T scenario TRAIN-6 | — |
| AC-09 honest uncertainty | PASS | R; P (REQ-902 T1, REQ-903 T2–T5 `confidence: low`) | — |
| AC-10 immutability / revisions | PASS | R; G C4 13 checks (1.0.0 byte stability) | — |
| AC-11 RUN.json untouched | PASS | R (`git status` no RUN.json); T | — |
| AC-12 planner ends, plan usable by a later session | PASS | P: three fresh sessions produced valid plans from the docs only | — |
| AC-13 retrospective compatibility | PASS | R (REQ-013/015/016 compat read-only) | — |
| AC-14 negative tests name task/field | PASS | R 20+ corruptions; G; P batteries | — |
| AC-15 no model/account/worker assignment | PASS after fix | R round 3 said PARTIAL (exact-match list) → token-based rejection; G C3 (`model_hint`, `assignee`, `max_parallel`, …) | free-text recommendations in prose are not keys |

Constraints: Scheduler and its modules untouched by this work; no historical RUN.json changed; nothing pushed,
published or deployed.

Final live-tree run (2026-10-15): module 200 OK, methodology 953 OK (3 skipped), scheduler core unchanged.
