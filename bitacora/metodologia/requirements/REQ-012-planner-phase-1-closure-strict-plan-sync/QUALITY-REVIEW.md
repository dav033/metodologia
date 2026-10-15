# REQ-012 — Independent quality review of the three context-free plans

Reviewer: a fresh read-only agent that did not write the validator and was told not to run it: it opened 5-8 real
files per plan (trainingapp, maros-nest/maros-next, pictures), judged claims, dependency graph, classifications,
verifications that could pass while the work is wrong, and what a deterministic scheduler could be misled by.
Planners then revised their own plans from the findings (no edits by the implementer); `verify_independent.py` re-ran.

| Plan | Evidence claims | Verdict | Main defects found | Outcome after revision |
|---|---|---|---|---|
| REQ-901 duplicate project | 7 files, all TRUE | ACCEPT WITH CHANGES | T3 missing `after: T2` (shared asset-clone contract); invented `T6 after T5`; T2/T3 verified by tests that pass without the work; T9 risk understated | T3 after T2, T6 only after T4, tests created by T2/T3 with `created_by`, T9 medium + new shared resource; critical path 230 min |
| REQ-902 audit trail | 7 files, all TRUE (DTO absent but declared created) | ACCEPT WITH CHANGES | T1 research already answered by the repo and wrongly blocking; T5/T7 verification could not detect the new code; T4 explicit delete redundant with CASCADE; scope is `canSeeLeadNumber`, not a type filter | T1 removed, delete safety reworded as a manual check, tests with `created_by`, scope wording fixed; 7 tasks, 250 min |
| REQ-903 latency | 8 files, all TRUE (new files declared `created_by`) | ACCEPT WITH CHANGES | T5 `small_change` over six files in three layers; T3 decision had no verifiable artifact; T6 command said nothing about latency | T5 `large_change`, decision/baseline/after JSON files with harness checks (`decision-check`, `summary-check`, `budget-check`), live-quota dependency stated; 390 min |

What the review shows about the tooling: every defect it found was a *content* defect the schema cannot see (a missing
real dependency, an invented one, a test that proves nothing). The deterministic gate had passed all three plans. One
of them became a new lint (`shared_unordered`: unordered tasks that admit an interaction are a warning). The others
(a verification that can pass while wrong; a research task the code already answers) remain judgement calls that need
a reviewer — that is the honest boundary of a deterministic planner gate and why review stays part of the method.

## Round 2 (a different reviewer, on the revised plans)

All round-1 fixes were confirmed in the plan files. It still found content defects, again none visible to the schema:

| Plan | New defects | Outcome |
|---|---|---|
| REQ-901 | T4 under-classified (it orchestrates copy → transaction → cleanup); nobody owned the key/name rules; photo refs inside `data_json` were never rewritten by any task; T3 coupling evidence named the wrong task | T4 medium/medium, key/name generation owned by T4 and tested in T6, ref rewriting owned by T3; critical path 250 min |
| REQ-902 | T3 verification needed a non-production DB (not machine-runnable); the read path for actor names was unstated; an unobserved test count | T3 = `grep` of the SQL CASCADE (live delete optional, owner-gated), read path stated (`dataSource.getRepository`), count re-observed |
| REQ-903 | **High:** the measurement artifacts lived under a git-ignored `data/`, so isolated runs would lose them; T2 measures a live dev server while T4 edits `route.ts`; budget rule inconsistent (equal passed, objective said "below") and a flaky p95 comparison | artifacts in tracked `eval/latencia-asistente/`, T4 after T2, budget strictly below baseline p50 with an explicit tolerance; 435 min |

After revision all three pass the gate, the corruption battery and the approval → drift lifecycle (3/3) and they are
the module's `scenarios/` fixtures. Two review rounds found real defects each time, so the loop does not converge to
"no findings" by itself: a reviewer will always find something; the record shows what the deterministic gate can and
cannot see (content defects), which is why review stays part of the method.
