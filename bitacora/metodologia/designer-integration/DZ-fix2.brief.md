# Task DZ-fix2 — approve the contract blob the UI tasks will actually start from

Read first, binding: `/home/david/dev/.designer-wt/RULES.md`, `CONTEXT.md` (D-127). Worktree `dz/INT` at `7dfa5ee88`
(path `/home/david/dev/.designer-wt/DZ-approval`); commit on top. Fail-first tests, modules < 500 lines.

Problem (lead review): `bt_design_approval.decide`/`contract_snapshot` hash `git show HEAD:<contract>` in the design
task's repository. In a real 1.3 run the accepted design task's delta is integrated on the SUBPLAN LINE ref
`refs/m3/line/<run identity>/<role>/<SP-id>` (see `bt_integration_line.SubplanLineRouter` / `Line.ref`, wired in
`bt_scheduler_executor_wiring.py:~284-300`, identity = `api.run_identity(scheduler)`), and the UI tasks' base tree —
which the gate `check_tree(rdir, repo, base, path)` reads — is that line, not the repo's HEAD. HEAD normally does not
contain the contract until final integration, so the owner could not approve (blob absent) or would pin a different blob.
The owner E2E only passes because its fixture commits the contract to HEAD directly.

Fix: resolve the approval revision as the current run's subplan line ref for the contract's subplan in that
repository, through public APIs (the integration-line module / executor adapter — e.g. derive the run identity the same
way the wiring does, or from the newest `.state/executor/<project>-<REQ>-<identity>/` root via the adapter's
`executor_root` convention; document the rule). Fall back to HEAD only when no run exists for the requirement (plan not
launched yet). Use the SAME resolution in the web snapshot (shown bytes + digest), the CLI `show/approve`, and anything
else that pins a digest. Tests: (1) a temp repo where the contract exists only on `refs/m3/line/<id>/<role>/SP-1`
(not HEAD) — approve succeeds and pins that blob; the gate check_tree on that line returns approved; (2) another
requirement's line with the same subplan id is never chosen; (3) no run → HEAD fallback still works; (4) extend the
owner E2E or the scheduler-chain test so the contract is produced by the design task on the line (not pre-committed to
HEAD), then approved, then the ui task starts. Run focused tests, owner E2E, executor + core suites, full root suite.
