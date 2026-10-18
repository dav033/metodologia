# REQ-018 — isolated real-plan M1/M2 simulation

Owner approval: “procede”, explicitly scoped to isolated simulation. Canonical Pictures PLAN.md remains draft; only an external copy was approved/frozen. No Pictures implementation or real task execution is authorized by this record.

Real M1, real M2, real candidate source and role router consumed the actual frozen schema1.2.0 REQ-018 (six tasks, three milestones). Synthetic profiles/quota/runtime availability/history, fake executor and verifier. Claude used20%; Codex used60%. Socket and subprocess-launch guards active during simulation.

| Task | Kind | Complexity | Selected model | Effort |
|---|---|---|---|---|
| T1 | implement | medium | sonnet | medium |
| T2 | implement | high | gpt-6-luna | high |
| T3 | implement | medium | sonnet | medium |
| T4 | implement | high | gpt-6-luna | high |
| T5 | implement | medium | sonnet | medium |
| T6 | test | medium | sonnet | low |

Result: both account-enumeration orders completed, six simulated executions and six simulated accepted verdicts per run (12 task executions total). Selections identical. Each run checked full-DAG routing, all prerequisite completion before READY assignment, capacity<=2, resolvable M2 dispatch references and exact expected route policy. Source PLAN.json remained byte-identical; frozen JSON values equal source values, with normalized serialization hash recorded in simulation-approval.json.

Audit entries: forward=80, reverse=80. Ruff on the harness passed. No full Pictures lint/types/build/new behavior tests were run: product code unchanged. Simulated accepted verdicts do not satisfy implementation acceptance or the two manual product-review criteria.

Initial freeze assertion incorrectly compared raw source serialization hash to normalized frozen hash; corrected to record both and validate semantic equality plus each actual hash. First simulated run oracle guessed task kind from title and falsely expected implementation effort for T6. Corrected harness to honor explicit schema1.2 task.kind; original failed artifacts retained externally. No M1/M2 production changes.

External runnable harness and isolated databases: /home/david/.local/tmp/pictures-req018-m1m2-dzwyqcyd/. Persisted evidence here contains no live database or approval that authorizes canonical implementation.

Separate incident: previously used round CLI and native Planner Stop hooks automatically committed and pushed methodology bitacora changes. origin/main reflog confirms update-by-push through5bc98f3 (also41344be/298da62/5eeee36/0312304/fed1200). Earlier no-commit statements were incorrect. No rollback or further Git mutation was performed during this simulation. Tracked separately as metodologia P-118.
