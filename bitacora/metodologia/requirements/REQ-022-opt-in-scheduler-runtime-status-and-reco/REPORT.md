# REQ-022 — Opt-in Scheduler runtime, status and recovery

Date: 2026-10-16  
Authority: David approved the SPEC/PLAN in chat on 2026-10-16.

## Built

- Added the explicit `launch --mode marathon --scheduler` path. The existing launch default remains legacy; Scheduler launch requires the requirements readiness gate and an existing approved, frozen `PLAN.json`. `--force` cannot bypass the Scheduler plan gate.
- Added `bt_scheduler_run.py` and `scheduler-run` to compose one durable M1 owner with the existing M2 route decision and M3 executor. A runtime binding pins plan id, revision and hash; resume rejects a different approved plan and reuses the existing run identity.
- Added the shared owner lock across legacy run initialization and Scheduler startup, preventing a second writer from racing the authority check.
- Added an atomic `RUN.projection.json` with Scheduler authority, complete frozen plan identity, task state and a five-second heartbeat cadence. Scheduler readers require an existing M1 database, validate the projection and never fall back to `RUN.json`.
- Updated `watch`, dashboard and requirement run views to show stale/missing/corrupt projection state and the exact recovery command. Active status is stale after two minutes. CLI/web pause and resume use M1; stop maps to M1 cancel. Legacy controls remain intact.
- Added best-effort terminal notifications deduplicated against M1's latest state-changing audit sequence. Scheduler launch installs its matching per-user login-resume entry unless `--no-autostart` is passed.
- Kept M4/M5/M6 separately opt-in and `NEEDS_REVIEW` operator-owned. Updated module and architecture documentation and reconciled P-001/P-026.

## Verification evidence

- M1/M2/M3 owner runtime: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_runtime.py'` — 12/12 passed.
- Existing Scheduler integration: focused `test_scheduler_integration.py` — 28/28 passed.
- Explicit launch contract: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_launch.py'` — 8/8 passed.
- Authority-aware views/controls: `PYTHONPATH=skill/scripts python -m unittest discover -s skill/scripts/tests -p 'test_scheduler_run_*.py'` — 15/15 passed after adding a regression for an empty `plan_ref`.
- Legacy web control regression — 1/1 passed. Installed-wheel Scheduler launch/control helper import checks — 2/2 passed.
- Legacy frozen-plan resume guard: `test_plan_launch_paths.py` — 23/23 passed; `test_a_run_started_under_r1_does_not_resume_when_r2_is_approved` returns `PLAN_REF_STALE`. A separate temporary reproduction of the reported r1→r2 scenario returned the same refusal. The old scratch receipt named by P-026 was not present in the workspace, `.local/share` or `/tmp`.
- `ruff check skill/scripts/bt_scheduler_adapter.py skill/scripts/tests/test_scheduler_run_views.py`, scoped `compileall`, and `git diff --check` passed. T1/T2 scoped lint and compile checks are recorded in PLAN. A broader Ruff pass showed 11 findings (RUF100, BLE001 and ISC004) that were also present on HEAD; no new finding was introduced by this work.
- `python skill/scripts/bitacora.py --project metodologia trace --node REQ-022` returned the requirement neighborhood. Targeted `bt_trace.lint()` reports no uncovered, unknown-ref, dangling or open-task finding under REQ-022. A repository-wide trace still reports older uncovered requirements and dangling P-IDs outside this request; they were not changed here.
- The package module-completeness audit fails because concurrent REQ-020 has an untracked `skill/scripts/bt_scheduler_decision_benchmark.py` not listed in `pyproject.toml`. This file is outside REQ-022 and was left untouched. An earlier package suite was 17/18 for the same issue.
- No real provider, task, live Scheduler run, local web server, notification delivery, or per-user autostart installation was performed. No source commit or push was made. Two pre-existing local supervisor bookkeeping commits contain only `RUN.json` state and were left untouched.

## Rulings

- D-051 keeps Scheduler execution behind explicit opt-in, with M1 as the sole run authority and the legacy supervisor as the default.
- A missing or malformed status projection is unavailable state, never permission to read or write legacy `RUN.json`. A stale active heartbeat (>2 minutes) is displayed with the exact resume command.
- Notification dedupe state is persisted before best-effort delivery; if that local state is unreadable or unwritable, delivery is skipped so notification failure cannot interrupt the owner.
- A `scheduler-run` invocation may install the matching per-user login-resume entry; `--no-autostart` suppresses/removes it. No entry was installed by this implementation session.
- P-026's old scratch observation is retained as historical evidence, but the current exact-revision test and an independent temporary reproduction now refuse resume with `PLAN_REF_STALE`.

## Needs your eyes

- Before a real provider run, review the opt-in boundary and runtime ownership in `skill/scripts/bt_launch.py`, `skill/scripts/bt_scheduler_run.py`, `skill/scripts/bt_scheduler_adapter.py` and `skill/scripts/bt_server.py`. The implementation used fake providers and no live server.
- The independent T1/T2/T3 spec and standards reviews approved. T3's spec review found acceptance of an empty `plan_ref`; the adapter now validates nonempty plan id, positive integer revision and lowercase 64-character SHA-256, with a regression test, and both re-reviews approved the correction.

## Proposals

- None.

## Pending

- P-026 is closed. P-001 remains open only for the separate Maros REQ-005 E2E audit (M3–M5) and Relay F-23 helper-start success-path/broader behavior tests. They remain outside REQ-022.
- No live provider smoke was authorized by this plan. Use a separate bounded operational plan if real execution evidence is later wanted.

## Walkthrough

1. Approve and freeze the requirement plan, then explicitly call `bitacora.py --project <project> launch <REQ> --mode marathon --scheduler`.
2. The normal readiness gate runs; the shared lock chooses one authority and M1 binds the exact frozen plan identity.
3. The owner composes M2's eligible route and M3's isolated agent process under the durable M1 run.
4. M1 remains authoritative in its SQLite database; the owner atomically updates `RUN.projection.json` and its heartbeat.
5. `watch`, dashboard and the requirement page read the projection only for Scheduler-owned requirements; pause/resume/stop go through M1.
6. If the owner stops, resume with `bitacora.py --project <project> scheduler-run <REQ> --resume`; M3 reconciles process identity before new dispatch. A stale view shows this exact command.
7. M4/M5/M6 remain separately configured; `NEEDS_REVIEW` still waits for an operator, and the ordinary launcher still uses legacy mode by default.

## Independent review

- T1 and its readiness-gate correction: independent spec and standards reviews approved.
- T2's launch and frozen-plan guards: independent spec and standards re-reviews approved.
- T3's authority-aware view/control implementation and the complete-plan-identity correction: independent spec and standards reviews approved.
