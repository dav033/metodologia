# REQ-018 v2 — isolated M1/M2 simulation

PASS: 8 tasks, two account orders, 16 simulated executions/verdicts. Routing was invariant under reversed account enumeration.

Real components: SchedulerCore (M1), DecisionAssignmentPort and policy/router (M2), SQLite ledgers. Synthetic boundary: two accounts, fresh used quota Claude 20% / Codex 60%, executor and verifier. Sockets and subprocess launch forbidden during both runs.

| Tasks | Role | Model / effort |
| --- | --- | --- |
| T1–T6 | Implementer | Claude Sonnet / medium |
| T7 | Runner | Claude Sonnet / low |
| T8 | Reviewer | Codex GPT-6.1 Sol / high |

Implementer keeps quota-based preferences regardless of explicit difficulty (D-072). Runner selected the lower-used family. High-complexity Reviewer prioritizes its first configured option (Sol high) before quota. These are policy-conformance results, not comparative model-quality evidence.

Assertions passed: frozen SHA matches manifest; source and frozen JSON are semantically identical; complete-DAG recommendations have resolvable route IDs; dispatch only after dependencies complete; concurrency never exceeds two; one execution/verdict per task; completed terminal state; identical routes in both orders; canonical source hash unchanged and PLAN.md remains draft.

The approved/frozen copy is simulation-only. No Pictures implementation, actual command execution, browser test, real-provider call or product/manual acceptance. Scripted positive verdicts do not establish the planned acceptance criteria. No policy changes or new production-code checks were needed. No mutation workflow CLI or manual Git action was invoked; pre-existing global hook/VCS issue P-118 remains unresolved.
