# gate-recompose — state at emergency shutdown (2026-10-31)

Branch `gate-recompose` (from `built-subplan-versions` a5c468cea, now merged to main as e74c6ea8b).

## Done (committed, tests red before / green after)
- Gap 1, D-245 (a8bc62230, f529cc022): a passed composition gate that no later gate supersedes is composed again
  when a member's line takes work its gate task was not verified with; its gate task runs a new round on the new
  candidate. Patch `bt-run-fresh-gates` (latched right before `bt.sync_lines`), step `bt.gate_freshness`
  (`CompositionComposer.stale_members`), pure `subplans.fresh_targets`/`superseded`, events `gate_stale` /
  `gate_freshness_failed` (flow panel + solver brief). Tests: tests/test_durable_fresh_gates.py (2 e2e DBOS + 2 pure).
- Gap 2, D-246 (478557ac2): «Probar» folds the current line tips of the subplans a subplan builds on into its offered
  version (`bt_verification_tree.py`, composer settle rules, `refs/bt/try/...`, stable per tree); panel names the
  included predecessor versions or says which one could not be combined. Tests: tests/test_durable_verification.py
  (LaterSubplanTree). Dry run on a scratch copy of pictures r29: SP-14/SP-3/SP-4 gain a version with SP-2 v2;
  SP-5, SP-7..9, SP-11, SP-12 conflict with SP-2's r27 repairs (8 files).
- Suites run green: test_durable_fresh_gates, test_durable_verification, test_verification, test_stdlib_boundary,
  test_verify_servers, test_stage_queue, test_subplan_flow, test_package_modules, test_durable_solver.

## Left
- Full regression NOT run (selection untrusted: 177/311 suites; integrations were running back to back).
  In particular not yet run here: test_durable_subplans, test_compose_conflicts, test_durable_compose_upgrade,
  test_durable_upgrade, test_durable_audits(_upgrade).
- Decision entries D-245/D-246 (reserved) not written to DECISIONS.md; texts are in the commit messages.
- Not integrated, not pushed.

## Resume
1. Check nothing integrates: `cat ~/bitacora/.state/integrate.lock; pgrep -af bt_regress`.
2. `python3 skill/scripts/bt_regress.py <this worktree> <scratch> <results.txt> --base main`, launched with
   SIGTTIN/SIGTTOU/SIGTSTP at default (scratchpad/dfl.py wrapper).
3. If green: rebase/merge onto main and integrate per the usual flow; paste D-245/D-246.
