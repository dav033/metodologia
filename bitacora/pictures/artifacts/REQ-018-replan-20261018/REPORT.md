# Pictures REQ-018 — Planner repair and regenerated draft v2

Owner requested correcting Planner quality and generating a new plan, not implementing Pictures. Original artifacts/hashes remain in before/; reviewed regenerated draft in after/. Canonical PLAN.md remains draft and has no frozen revision.

Planner changes: one role pointer plus explicit WBS responsibility/calibration checks and adversarial checks. Classify deliverables using actual kind consumers; keep code/test-harness authoring and registration in implementation, standalone command execution in test, substantive acceptance review in audit. Preserve implementation-local tests with their producer. Justify complexity from inspected decision/state/stream/persistence/consumer/harness boundaries, considering the adjacent higher level; unknown history remains unknown, missing harnesses are work, not evidence.

| Task | Deliverable | Kind | Complexity |
|---|---|---|---|
| T1 | Strict catalogue matching | implement | medium |
| T2 | Discovery turn decisions | implement | high |
| T3 | Honest matching and empty responses | implement | high |
| T4 | Integrate category discovery into the guided API | implement | high |
| T5 | Preserve gallery identity and empty-turn selection | implement | high |
| T6 | Register category regression commands | implement | low |
| T7 | Run established verification commands | test | low |
| T8 | Review integration and product acceptance evidence | audit | high |

Three milestones, eight tasks, six preserved requirements and four interfaces. T1 remains medium; T2/T4 high. T3 and T5 are high based on streamed/final sanitation and persisted/restored empty-gallery boundaries. Old mixed T6 becomes implementation registration T6(low), established-command execution T7(low) and integration/product evidence review T8(high). Browser/harness construction remains explicitly owned by T4/T5; feasibility was inspected, no finished harness or browser acceptance fabricated.

Canonical plan check/report exit0: zero errors, nine warnings (seven future-test references; two manual criteria that cannot auto-PASS). Both fresh-context read-only reviews, spec and standards, APPROVE with no actionable findings. Their approval is review of the draft, not owner execution approval or product acceptance.

Runtime14 tests pass. Combined profile/runtime19 tests:18 pass, one pre-existing profile failure rejects model/effort metadata already present before this change; same failure reproduced after removing only the new role instruction. Check was not weakened or skipped. Offline wheel builds and contains byte-identical corrected resources; six generated Planner definitions refreshed. No other roles/models changed. Scoped Ruff/whitespace pass. No full repository suite/static type checker/browser executed for the instruction change.

One native generation: canonical Planner API, exact codex-luis/gpt-6.1-sol/high, exit0. CLI header reports requested configuration; reported usage193,984 tokens is not a subscription invoice. --disable hooks applied only to this child, verified supported via CLI features list; global hook config unchanged. No hook events observed in the requested child. During closeout the shared workspace recorded another automatic commit/push ae37a9c labelled session aa047071; origin/main reflog confirms it. Its initiating process was not conclusively attributed. No manual Git mutation was invoked by coordinator; no rollback/global config edit. P-118 remains open: the child-only mitigation does not protect the whole workspace.

Current user choices remain /asistente, full current guided catalogue, category-only discovery, optional preferences, strict matches/no padding, no designs on zero matches, existing plan/selection safeguards and source updates through normal publication/build/deploy. No new admin/hot reload or REQ-017 integration.

Remaining: owner review of new draft before any new-plan simulation/execution; pre-existing profile test debt tracked separately as metodologia P-119. Raw native logs remain outside the repo at /home/david/.local/tmp/planner-replan-req018/.
