---
req: REQ-011
status: delivered-uncommitted
date: 2026-10-14
---
# Report — REQ-011 — Scheduler Core M1 (`bt_scheduler_core`)

## Outcome

M1 of the Scheduler (`PLAN-SCHEDULER-CORE-M1.md`, repo root) is built as an isolated, stdlib-only package
`skill/scripts/bt_scheduler_core/` with **no AI of any kind**, reached from the methodology only through
`skill/scripts/bt_scheduler_adapter.py`. Nothing is committed (not requested). M2–M5 (decision, executor, monitor,
recovery) are *not* built: only their ports and deterministic simulators exist (proposal P-020).

What the core does: loads a `PLAN.json` revision **bound to an approved sha256**; resolves the DAG; runs the
task/attempt state machine on a transactional store (SQLite WAL, or in-memory); reserves capacity and shared resources
atomically with fencing tokens; delivers orders through a write-ahead outbox (query before resend); ingests events and
independent verdicts idempotently; reconciles after a restart; keeps an append-only audit log; exposes a CLI
(`python -m bt_scheduler_core validate|simulate|status|audit`).

## Changes

| Area | Files |
|---|---|
| Module | `skill/scripts/bt_scheduler_core/` — `plan, states, model, contracts, repository, sqlite_repository, transitions, reservation, resources, events, recovery, operations, dispatch, scheduler, simulators, simulation, views, config, errors, cli`, `README.md`, `tests/` |
| Adapter | `skill/scripts/bt_scheduler_adapter.py` (only importer of the core) |
| Guard | `bt_runentry.supervise`: two lines — `refuse_legacy_run(rdir)` before the requirements gate |
| Packaging | `pyproject.toml`: package `bt_scheduler_core`, py-module `bt_scheduler_adapter`, README as package data |
| Integration tests | `skill/scripts/tests/test_scheduler_integration.py` |
| Docs | `skill/references/modules.md` §Scheduler core; `skill/SKILL.md` router row |

Not touched: `PLAN.json`/`plan-revisions` (read-only), any historical `RUN.json`, `bt_run*`/`bt_runstate` behaviour,
the planner module (another session's schema 1.1.0 work is uncommitted in the same tree and is not part of this).

## Rulings made without asking (also in PLAN.md §Rulings)

1. **Approval = caller-supplied sha256** of the frozen revision; the adapter takes it from the planner's manifest. A
   valid JSON is never an approved plan (answer 5).
2. **One authority per requirement**: the run database xor legacy `RUN.json`. The database alone decides; a legacy
   run is never opened, migrated or overwritten.
3. **Projection is `RUN.projection.json`, never `RUN.json`**, so the web controls (`bt_page_run.apply_control` →
   `bt_runstate.update`) have no file to write a legacy state into.
4. **Database location**: `<bitácora root>/.state/scheduler/<project>-<REQ>.db` (local, untracked — a live SQLite file
   with `-wal/-shm` does not belong in the versioned documents); `<requirement>/SCHEDULER.db` outside that layout.
5. **State split vs plan §5.3 diagram**: task states (`pending, ready, active, recovering, completed, blocked,
   cancelled`) and attempt states (`reserved, dispatched, running, verifying, accepted, failed, rejected, cancelled,
   uncertain`) are separate; a failed attempt is not a blocked task (it goes through `recovering`).
6. **`completed_with_blockers` is run status `blocked`**: nothing can progress yet not everything is completed.
7. **Agent "finished" never completes a task**; only an independent verdict (verifier ≠ executor, non-empty evidence,
   `accepted is True`) does. A lapsed lease or old heartbeat only triggers a query, never a verdict of death.
8. **Uncertainty keeps the reservation** (no second writer); `uncertain` is resolved by reconciliation or an
   authorised operator (`resolve_attempt`).

## Plan §12 answers (against the real code; map of the supervisor in the session scratch, summarised here)

1. **Where things live.** Loop `bt_run.py` (`_open`, `_step`, parallel batch), entry `bt_runentry.supervise`, state
   `bt_runstate.py` (task parser, `RUN.json` load/save/`update`), settle `bt_runsettle.py`, sessions `bt_runsession.py`,
   router/pool `bt_agents.py`, task commands `bt_runtask.py`, worktrees `bt_worktree.py`/`bt_run_isolated.py`.
2. **Source of truth.** Kept: legacy `RUN.json` for existing runs. New runs may opt into the core's database. Never both
   (rulings 2–3; enforced in `open_scheduler` and `supervise`).
3. **Semantics of done/fail/heartbeat/audit/limits.** Not reimplemented or migrated: the legacy commands keep their
   behaviour on legacy runs. The core's equivalents are explicit events/verdicts (see README §Contracts) with the same
   rule that a claim of done is not an acceptance.
4. **Resource/isolation invariants.** The supervisor has four unrelated locking mechanisms (RUN.json lock, central
   named locks, integration lease, planner lock) and `resources:` tags are only a grouping hint for worktrees, not locks.
   The core adds none of them: its holds live inside its own transactional state and never touch those files.
5. **Plan approval.** Today: PLAN.md `status: approved` plus the frozen `plan-revisions/PLAN.r<N>.json` with a manifest
   sha256; `plan_ref` is recorded at run creation but **not enforced on resume** in the legacy supervisor. The core
   enforces it (`PLAN_MISMATCH` on another id/revision/hash; the stored run is left untouched).
6. **Blocked by dependency vs by exhaustion.** Dependency: the task stays `pending` and is reported `unreachable` with
   the blocking head; exhaustion/recovery stop: `blocked` with a `reason`; `reopen` (needs `by`) gives a fresh budget.
7. **Evidence.** Verification verdict carries `verifier`, `evidence` (≤ 2000 chars), `accepted`; a task is `completed`
   only by an accepted verdict whose verifier differs from the executor label (configurable).
8. **Public CLI/paths.** Unchanged. The only edit in an existing command path is the authority guard, which is a no-op
   unless the requirement already belongs to the scheduler.

## Reviews and what they changed

Three independent reviews ran on the finished tree: spec (APPROVE-WITH-FIXES), standards (APPROVE-WITH-FIXES),
antagonist (BLOCKING A1–A8). All findings were fixed with regression tests:

| Finding | Fix | Test (in `tests/test_hardening.py` unless noted) |
|---|---|---|
| A1 untyped verdict/event values accepted | `verdict_problem`, events re-validated on ingest | `UntrustedPortTypes` |
| refused ids poisoned later corrected retries | only applied ids remembered, bounded (`SEEN_LIMIT`), refusal window | `RefusedIsNotRemembered` |
| unbounded wait / delivery retries | `max_recovery_waits=3`, `max_deliveries=5` | `WaitCap`, `ConfigLimits` |
| A2/A3 VERIFYING wedged by `unknown`; abandoned verify order | unknown ignored while verifying unless manual; verify re-requestable by an operator; `VERIFYING→FAILED` operator-only | `VerifyingIsSettledByVerdict` |
| A4 no port burned deliveries | order kept untouched for `pending_orders()` | `NoPortKeepsOrders` |
| A5 `wait(0)` busy loop | waits hold ≥ 1 s and are not progress | `RecoveryWaitIsNotBusy` |
| A6 cancel then resend | pending start voided on cancel; start never sent after cancel; cancel ack ⇒ next step queries | `CancelNeverResends` |
| A7 adapter could be written by legacy controls | projection in its own file; DB decides authority; DB under `.state/` | `test_scheduler_integration.py` (`Authority`, `Projection`) |
| A8 slow uncertain retry; unbounded outbox | uncertain retried within `reconcile_seconds`; outbox pruned past 1000 (newest 500 + pending + live kept) | `OutboxIsBounded` |

## Verification (run on this tree, 2026-10-14)

| Suite | Command | Result |
|---|---|---|
| Module | `cd skill/scripts && PYTHONPATH=. python3 -W error::ResourceWarning -m unittest discover -s bt_scheduler_core/tests` | 234 OK |
| Integration | `python3 -W error::ResourceWarning -m unittest tests.test_scheduler_integration` | 28 OK |
| Methodology (all) | `cd skill/scripts && python3 -W error::ResourceWarning -m unittest discover -s tests` | 797 OK |
| Packaging | `python3 -m unittest tests.migration.test_package_install` (repo root) | 11 OK |

Acceptance criteria SC-AC01..20 → test names: `bt_scheduler_core/README.md` §Acceptance evidence; the table is itself
checked by `tests/test_readme.py` (every name must exist; all twenty must appear). SC-AC18 (compatibility) is
`tests/test_scheduler_integration.py` (`HistoricalRuns`: real `RUN.json` files copied, hash-checked, byte-identical).

Notes on the integration boundary test: it now skips the `bitacora/` folder of the repo (records, not methodology code);
a REQ-012 trial script there legitimately names the core's reader.

## Limitations (explicit)

- The core is driven by a caller: no real executor, verifier, assignment or recovery module exists yet (simulators
  only). `run()` returns when only `uncertain` attempts remain or after the idle timeout; an operator must resolve them.
- The legacy supervisor is unaware of the core beyond the guard; there is no automatic opt-in (`launch` still creates
  legacy runs). That is deliberate: dual operation is out of scope.
- SQLite is the only durable repository; the port allows others, none is written.
- Cross-process fencing relies on SQLite `BEGIN IMMEDIATE`; network filesystems are not supported.

## Proposals (out of scope, for the owner)

- **P-020** M2–M5 modules (decision/assignment, executor, monitor, recovery) on the existing ports.
- Opt-in switch in `launch --mode marathon` to create a scheduler-owned run, with `watch`/web reading the projection.
- Enforce `plan_ref` on resume in the legacy supervisor (gap found while answering §12.5).
