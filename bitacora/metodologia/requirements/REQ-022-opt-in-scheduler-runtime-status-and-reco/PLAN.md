---
req: REQ-022
status: done
created: 2026-10-16
---
# Plan — REQ-022 — Opt-in Scheduler runtime, status and recovery

## Approach
Keep the existing launcher and supervisor as the default. Add an explicit Scheduler opt-in that composes the existing M1/M2/M3 modules behind one durable owner process, writes an atomic heartbeat projection, and reuses the current notification and per-user recovery mechanisms. Make CLI and web readers authority-aware and route Scheduler controls through M1; preserve all legacy controls and the existing human review boundary.

## Global constraints
- Require an approved, frozen `PLAN.json` revision; no force bypass and no automatic conversion of legacy plans.
- A requirement has one authority: Scheduler database or legacy `RUN.json`; never write the projection as legacy state.
- M1 owns run/task state, reservations and accepted verdicts; M2 chooses eligible routes; M3 owns agent processes and restart reconciliation.
- Do not implicitly enable M4/M5/M6, auto-approve `NEEDS_REVIEW`, or launch a real provider during implementation.
- Preserve the shared dirty worktree and concurrent REQ-020/REQ-021 changes; no commit, push or merge.
- Run regression checks only after approval of this plan; use temporary repos and fake providers.

## Tasks
- [x] T1 — Add the Scheduler owner process, `scheduler-run` CLI and durable M2/M3 composition · files: `skill/scripts/bitacora.py`, `skill/scripts/bt_cli_scheduler_run.py`, `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_adapter.py`, `skill/scripts/bt_runentry.py`, `skill/scripts/bt_notify.py`, `skill/scripts/bt_autostart.py`, `skill/scripts/tests/test_scheduler_runtime.py` · verify: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_runtime.py'` · covers: R2, R3, R4, R5, R6, R8, R9, R10, US-1, US-2, US-4
- [x] T2 — Add the explicit launch option and preserve legacy launch behavior · after: T1 · files: `skill/scripts/bitacora.py`, `skill/scripts/bt_cli_launch.py`, `skill/scripts/bt_launch.py`, `skill/scripts/tests/test_scheduler_launch.py`, `pyproject.toml` · verify: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_launch.py'` · covers: R1, R2, R3, US-1
- [x] T3 — Make CLI watcher, dashboard and web run controls authority-aware · after: T1, T2 · files: `skill/scripts/bitacora.py`, `skill/scripts/bt_cli_run_control.py`, `skill/scripts/bt_watch.py`, `skill/scripts/bt_page_run.py`, `skill/scripts/bt_page_req.py`, `skill/scripts/bt_pages.py`, `skill/scripts/bt_server.py`, `skill/scripts/bt_scheduler_adapter.py`, `skill/scripts/tests/test_scheduler_run_views.py`, `skill/scripts/tests/test_scheduler_run_controls.py`, `tests/migration/test_package_install.py`, `pyproject.toml` · verify: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_run_*.py'` · covers: R5, R6, R7, R8, US-2, US-3
- [x] T4 — Reconcile the P-026 resume evidence, document the supported lifecycle and update P-001 without losing its separate Maros E2E follow-up · after: T1, T2, T3 · files: `skill/references/modules.md`, `bitacora/metodologia/ARCHITECTURE.md`, `bitacora/metodologia/PENDING.md`, `bitacora/metodologia/DECISIONS.md`, `bitacora/metodologia/SUMMARY.md`, `bitacora/metodologia/2026-10/W3/2026-10-16.md`, `bitacora/metodologia/2026-10/W3/WEEK.md`, `bitacora/metodologia/requirements/REQ-022-opt-in-scheduler-runtime-status-and-reco/REPORT.md` · verify: `python skill/scripts/bitacora.py --project metodologia trace --node REQ-022` · covers: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, US-1, US-2, US-3, US-4

## Verification
- Focused new regression tests for CLI dispatch, old/new authority isolation, atomic projection/heartbeat, stale run reporting, M1 controls, notification deduplication and M1/M3 crash-resume safety.
- Existing `test_plan_launch_paths.py` stale-revision case and the reported scratch reproduction compared on the current implementation; close that P-026 sub-item only if the regression confirms `PLAN_REF_STALE`.
- Scoped Ruff and compile checks for modified Python modules, plus `git diff --check` and `bitacora.py trace --node REQ-022`.
- No live provider, network request, actual launch, autostart installation or workspace task execution.

## Rulings
- Launch surface: add `--scheduler` under the existing `--mode marathon` rather than repurpose `--mode marathon`; cost if wrong: low, because this keeps current CLI meaning and compatibility.
- Recovery: resume only against the exact frozen M1 plan identity; M3 reattaches by process identity and M1 keeps uncertain attempts reserved; cost if wrong: high, so no automatic retry on uncertainty.
- Optional modules: M4/M5/M6 remain off unless separately supplied; M6 `NEEDS_REVIEW` remains visible and operator-owned; cost if wrong: medium, but this preserves D-043 and ARCHITECTURE.md.
- Startup recovery: mirror the existing per-user login entry for a selected Scheduler run, with `--no-autostart`; do not create an entry during this change; cost if wrong: low and reversible by the existing remove path.
- Ownership race: both supervisors use the same local non-blocking lock; legacy holds it through RUN.json initialization and Scheduler holds it for the run lifetime, so the authority check and first state creation cannot interleave — cost if wrong: medium; process exit releases the lock and no historical RUN.json is rewritten.
- Notification dedupe: key a notification to the latest non-process-resume M1 audit sequence, persist the claim before best-effort delivery, and skip delivery when local dedupe state is unreadable or unwritable — cost if wrong: low; a message may be missed rather than duplicated or allowed to stop execution.

## Progress log
- 2026-10-16: inspected current P-001/P-026 records, launcher, watcher, web controls, M1/M2/M3 contracts, existing notification/autostart paths and resume guard. Drafted SPEC/PLAN; no source code or tests changed/run.
- 2026-10-16 06:50 review comments (terminal): Owner approved in chat on 2026-10-16.
- 2026-10-16 06:50 plan APPROVED (terminal)
- 2026-10-16 06:50 launched marathon supervisor (pool auto, haiku) from HQ in `/`
- 2026-10-16: stopped the generated supervisor before source edits because its prompt required a commit contrary to the approved no-commit constraint; continued T1 in-session with an explicit no-commit brief. The supervisor left two local RUN.json-only bookkeeping commits; neither is pushed.
- 2026-10-16: T1 implemented and verified: runtime 11/11, existing Scheduler integration 28/28, installed-wheel `scheduler-run --help` 1/1, scoped Ruff and compile checks passed, `git diff --check` passed. Full wheel suite is 17/18: the only failure is the concurrent un-packaged `bt_scheduler_decision_benchmark` from REQ-020, not a T1 module. Independent spec and standards reviews approved after fixes.
- 2026-10-16: T2 implemented and verified: Scheduler launch 8/8; independent spec and standards re-reviews approved the frozen `PLAN.json` guard, including refusal of legacy plans without a frozen revision even with `--force`. Scoped Ruff on the new CLI and launch tests and compile checks passed; `bt_launch.py` retains pre-existing lint findings also present at HEAD.
- 2026-10-16: Follow-up for T1 adds `require_ready(rdir)` under the shared owner lock before authority checks/composition. Runtime 12/12, Scheduler integration 28/28, scoped Ruff, compile, and `git diff --check` passed; independent spec and standards reviews approved this R2 correction.
- 2026-10-16: T3 implementation now covers Scheduler projections in `watch`, dashboard and requirement views; CLI/web pause, resume and stop route to M1, with stop mapped to cancel. Missing/corrupt projections offer resume guidance without legacy fallback. Review found and fixed acceptance of empty `plan_ref`; the final focused T3 suite passed 15/15, scoped Ruff and compile checks passed, and fresh spec/standards reviews approved. Legacy web control 1/1 and installed `scheduler-run`/control helper tests 2/2 passed. The package module-list audit still fails only because concurrent REQ-020's untracked `bt_scheduler_decision_benchmark.py` is absent from `py-modules`; it remains outside this plan's scope.
- 2026-10-16: T4 reconciled the old P-026 observation against `PLAN_REF_STALE` regression plus an independent temporary reproduction, closed P-026, and retained P-001 only for the separate Maros and Relay follow-ups. Updated lifecycle/module docs, architecture, D-051, SUMMARY, WEEK and REPORT. `trace --node REQ-022` passed; targeted trace lint reports no uncovered, unknown-ref or dangling item for REQ-022. The repository-wide trace still reports historical warnings/errors in unrelated requirements and pending references. REQ-022 is complete; no live run, web server, autostart installation, source commit or push was performed.
