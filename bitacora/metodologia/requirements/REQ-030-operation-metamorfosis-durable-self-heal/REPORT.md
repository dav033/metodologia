# REQ-030 — Operation Metamorfosis: report

Date: 2026-10-28. Branch `metamorfosis` in the worktree `~/dev/metodologia-metamorfosis` (not merged into `main`, not
pushed). Raw requirement: [REQUEST.raw.md](REQUEST.raw.md). Baseline and map: [M0-ARCHAEOLOGY.md](M0-ARCHAEOLOGY.md).
Package documentation: `skill/scripts/bt_durable/README.md` on the branch.

## Milestones

| Milestone | State | What exists |
|---|---|---|
| M0 archaeology + baseline | done | responsibility map and matrix, baseline 244 test files (5 pre-existing failures, 1 flaky) |
| M1 contracts | done for the new runtime and the remote contract | `bt_contracts.execution/failure/owner/remote`; JSON Schema and phone TS generated and checked |
| M2 DBOS | done (one realistic flow) | run → task → agent/verify/integrate workflows, 4 load-class queues, durable owner decisions |
| M3 Linux supervisor | done | `bt_supervisor`: systemd user units on cgroup v2 + process-group fallback |
| M4 queues, isolation | done | agents/verify/integrate/runs queues; legacy resource claims; worktree per attempt; CAS integration line |
| M5 self-repair | done within one task | 10-class evidence classifier, bounded policy, re-verify repair, durable quota wait, coordinated remediation |
| M6 pre-flight | done | `bt_planner.preflight` in the approval gate and before a durable start |
| M7 remote/observability | remote findings fixed; telemetry JSONL | F4, F10, F11, F16, F17, F21, F22, F33, F39, F41 fixed; durable runs not yet in the phone panel |
| M8 migration | done, tested; not applied to a live run | inventory/diff/backup/claim/rollback; inherited work seeds the new line; reconcile re-verifies |
| M9 chaos | scenarios B, C, D, E, F, H, I, J, L, M(*), N, O executed | see below; A and G covered by unit tests; K partially |
| M10 benchmark | evidence per mechanism | `python -m bt_durable.bench`; legacy REQ-021 numbers from its own records |

## Acceptance criteria (only checked with evidence)

- [x] DBOS integrated and used by a complete realistic flow — `test_durable_e2e`: a 3-task dependent plan, real git
  worktrees, the real provider driver (fake `claude` binary), systemd units, M6 bubblewrap verification, integration.
- [x] Main contracts validated with Pydantic — execution/failure/owner/remote models; remote producers validated against
  them (`test_remote_contracts`, 14 tests). Legacy plan validation stays the planner's hand-written rules (see debt).
- [x] Agent processes supervised by a Linux runtime — `bt_supervisor`, 30 tests on both backends.
- [x] Recovery with real interruptions — engine SIGKILL mid-attempt: DBOS recovered 3 workflows, 1 agent launch;
  PostgreSQL stopped 6 s mid-attempt: run completed, 0 engine restarts needed, 1 launch.
- [x] Reconciliation of external effects — idempotent launch per attempt key (adoption after crash), integration by
  CAS with an ancestry check, one M6 verdict per verify key; exactly-once is not claimed.
- [x] Concurrency and worktrees protected — resource claims serialize overlapping paths; one worktree per attempt;
  stragglers are terminated before capture; cancellation stops every writer (heartbeat stops, no marked process).
- [x] Retries and self-repair with limits — Hypothesis: 500 failure sequences never loop past the budget.
- [x] Preventive plan verification — `bt_planner.preflight` (7 tests) in the approval gate and `bt-durable start`.
- [ ] Remote control compatible with the new runtime — the remote contract and findings are fixed, but the phone
  panel does not show durable runs yet (CLI and `summary` event only).
- [x] Migration of legacy plans tested — unit (6) + e2e (inherited not re-run, dependents build on it; reconcile
  re-verified); dry run on real pictures REQ-021: 28 inherit, 1 reconcile, 16 redo, blocked only by the live att-0094.
- [x] Safe workflow versioning — `test_durable_versioning` (real processes, SIGKILL between versions); placement rule.
- [x] Adversarial tests executed — listed below.
- [x] Existing regressions controlled — full suite on the merged branch: only the 5 pre-existing failures remain
  (plus 3 package isolation tests that pass under the system interpreter they target, fail under the uv venv).
- [x] Dependencies registered and locked — `pydantic`, `psutil`, `dbos==3.3.0` (+ dev `hypothesis`, `ruff`) in `uv.lock`.
- [x] Linux installation documented — README "Install"; `deploy/bt-durable.service`.
- [x] Recovery and rollback documented — README "Recovery and rollback", "Migration".
- [x] Comparative metrics obtained or limits reported — below; workloads differ, stated explicitly.
- [x] No new critical regressions known — see the regression note above.
- [x] No completeness claimed for unvalidated parts — "Not done / debt" below.

## Chaos and adversarial evidence (commands: `uv run python -m unittest <module>` with `PYTHONPATH=skill/scripts:skill/scripts/tests`)

| Scenario | Test | Result |
|---|---|---|
| B agent running when the engine dies | `test_engine_sigkill_mid_attempt_recovers_without_a_duplicate_launch` | 1 launch, run completed |
| C work done, checkpoint missing | supervisor `launch` adoption tests + B | adopts the unit, no second process |
| D step recorded, then crash | B (DBOS replays recorded steps) | step 1 not re-run (DBOS probe, 1 execution) |
| E duplicate concurrent commands | `test_duplicate_concurrent_answers_start_one_attempt` | 4 answers → 1 attempt; stale ids refused |
| F cancel while writing | `test_cancelling_a_run_stops_every_writer` | writer stops, no marked process |
| H database outage | `test_durable_postgres` | completed, 1 launch |
| I workflow version change | `test_durable_versioning` | past-patch workflows keep v1 steps |
| J repeated migration | `test_claim_is_idempotent…`, `inventory…stable…` | no-op, legacy stores untouched |
| L quota exhausted | `test_no_capacity_waits_durably_for_the_reset_then_runs` | durable wait, then 1 retry |
| M worktree reused by another attempt | `GitWorkspaces` manifest check (kept) | refuses (`WORKSPACE_ERROR`) |
| N permission | classifier/policy tests | always escalated, never retried |
| O infra vs code | `test_an_environment_failure_is_repaired_without_a_new_agent_attempt` vs `…retried_from_its_snapshot…` | re-verify (1 launch) vs retry with decisive lines (2 launches) |
| A, G | frontier tests (Hypothesis) | ready tasks never conflict; nothing restarts a known task |
| K | `test_repeated_failure_escalates…` | retry → one remediation → owner; legacy audit remediation not ported |

## Benchmark (no invented numbers)

Legacy, pictures REQ-021 (`python -m bt_durable.bench legacy ~/bitacora pictures REQ-021`): 71 attempts, 34 verify
failures (47.9 %), 198,088,200 tokens reported, T2.6 alone 24 attempts, 9 owner decisions + 20 manual interventions,
296 minutes lost recorded.

Durable lab (`python -m bt_durable.bench durable …` over every lab run): 0 duplicate launches in all runs; owner
decisions only where the budget or design requires them (repeated failure, stop).

Mechanism-level comparison (same failure, both runtimes):
- verifier Node heap OOM: legacy att-0088 consumed a full agent attempt; durable re-verifies the same snapshot with a
  bounded larger heap — 0 extra agent attempts.
- decisive failure line: legacy notes dropped it (24 T2.6 attempts); the shared digest now keeps it (both runtimes).
- engine crash mid-attempt: legacy relies on the watchdog and shim adoption; durable recovery proven with 0 duplicates.

These are not a throughput benchmark on identical workloads; the first real plan on the durable runtime is the next
measurement.

## Live state at the end

Owner approval on 2026-10-28 ("sí a todo", and migrate REQ-021 to the new contracts and runtime):

- `main` fast-forwarded to the branch (`003b7d6fc`, then ops commits) and pushed; the uncommitted Codex scheduler
  fixes are kept in branch `backup/main-wip-20261028`.
- Remote deployed: laptop remote API pinned at `~/.local/share/bitacora-remote/003b7d6fc…` (drop-in backup
  `exec.conf.bak.20261028-a5854d5f`); gateway on advin `current → releases/003b7d6fc…`, `previous → ee62d2e8…`
  (`/healthz` reports the new SHA; live smoke identical to before); phone built by Vercel from `main`
  (rollback target `flow-remote-cja7mw2iw-dav033s-projects.vercel.app`). Local web dashboard restarted.
- Durable runtime: PostgreSQL `metodologia-dbos-pg` (127.0.0.1:5435, volume `metodologia-dbos-pg`, password only in
  `~/.config/bitacora/durable*.env`, 0600); `bt-durable.service` enabled with the legacy launcher's PATH and root;
  routes codex-luis / codex-1 / codex-2 (gpt-6-luna high), then claude-luis (sonnet medium), live quota as capacity.
- pictures REQ-021 migrated: att-0094 was settled by the legacy owner under pause (T3.11 rejected → ready), then
  the run was held, its watchdog and monitor services stopped and disabled, and `migrate --apply` moved ownership
  (`RUN.owner.json` backend dbos, backup `.state/durable/migrations/pictures-REQ-021-r15-8e0f865109bd`).
  Inventory: 28 inherited (all 28 integrated into `refs/bt/line/pictures/REQ-021/r15/pictures` without a conflict),
  3 reconciled (T2.6 from att-0095, T3.11 from att-0094, T3.2 re-verified), 14 to run.

## Not done / remaining debt

- Plan/subplan contracts are still the planner's hand-written validators; only the runtime contracts are Pydantic.
- The durable router is a static ordered route list; the M2 decision engine and live quota signals are not wired in.
- Milestone audits and audit-driven plan revisions are not ported; remediation is a per-task coordinated attempt.
- Durable runs are not shown in the web UI / phone panel.
- The legacy runtime still has its 17 retry mechanisms; nothing was removed (ELIMINAR waits for equivalence on real plans).
- `file_guard.py` still does not see shell writes (no reliable interception was added).
- No real Claude/Codex session was run under the durable runtime.
