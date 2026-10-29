# REQ-030 M0 — Architectural archaeology and baseline

Date: 2026-10-28. Source tree: branch `metamorfosis` at `a42224c3b` (HEAD `1827f80fa` + the uncommitted Codex
scheduler fixes of 2026-10-28, captured as a snapshot commit without touching the main working tree).
Raw requirement: [REQUEST.raw.md](REQUEST.raw.md). Execution mode chosen by the owner: direct work in one
session with subagents; the legacy Scheduler/handoff/planning flow is NOT used to build this (it is the thing being
replaced).

## 1. Baseline

- Test suite: 244 `skill/scripts/tests/test_*.py` files, each run in isolation (`BITACORA_ROOT` in a scratch dir,
  6 in parallel). 238 pass.
- Pre-existing deterministic failures (also fail on pristine HEAD `1827f80fa`):
  `test_plan_boundary` (bt_review_policy imports the planner directly), `test_plan_schema_13_compat` (frozen plans
  in the live bitácora use schema-13 names), `test_real_designer_kit`, `test_recovery_views` (server route shape),
  `test_remote_panel` (`components` route has no production counterpart).
- Flaky under load: `test_platform.test_kill_tree_ends_a_group_that_ignores_sigterm_and_its_children` (fails with 6
  parallel runners, passes 3/3 alone).
- Live state at start: one run, pictures REQ-021 r15, put on hold by the operator (owner stopped); attempt att-0094
  (T3.11) left to finish in its worktree; T2.6 blocked after 24 attempts (decision T2.6:24 open).

## 2. Where things really live (verified paths, `skill/scripts/`)

| Concern | Location | Notes |
|---|---|---|
| State machine (M1) | `bt_scheduler_core/states.py`, `transitions.py`, `events.py`, `recovery.py`, `reservation.py`, `operations.py` | task 7 states, attempt 9 states, run status derived |
| Run persistence | `bt_scheduler_core/sqlite_repository.py` | whole run = ONE JSON doc rewritten per transaction; WAL, `synchronous=NORMAL`; append-only `audit` |
| Second state machine | `bt_scheduler_executor/ledger.py`, `model.py` (M3 ledger.db) | queued→preparing→running→settling→terminal; lossy mapping to M1 (`core_port.py`) |
| Dispatch boundary | `bt_scheduler_core/dispatch.py` (outbox) → `bt_scheduler_executor/core_port.py` → `executor.py` → `spawn.py` → `shim.py` | git integration base computed inline in delivery |
| Process isolation | `bt_scheduler_executor/shim.py`, `procinfo.py` | setsid + pgid; /proc scan every 100 ms; agents unconfined (no cgroup/rlimit); only the M6 verifier is sandboxed (bubblewrap) |
| Retries | ≥17 mechanisms (M1 budget, M1 outbox, M5 advice, M6 outbox + 3 retry kinds, healing ×4, watch ×3, remediation, REQ-029 cycle, ready-monitor) | overlapping counters; refused starts burn budget |
| Locks / owners | owner flock, watch flock, hold FILE (no staleness), executor flock, workspace flock, integration O_EXCL lock, `bt_lock.central_lock` (breaks live holders after 60 s) | owner liveness found by /proc cmdline match; `stop_owner` kills by pid without identity |
| Contracts | hand-written dict/isinstance validators; JSON Schemas exist but are never executed | 4× `PLAN_SCHEMA_CAPABILITIES`, 5 quota shapes, 4 cursor dialects |
| Quota control | `bt_scheduler_quota_preflight.py` (inline, blocking network poll), M2 `bt_scheduler_decision/` | waits = `hold_until`; owner exits "stalled" when no route |
| Security controls | M6 sandbox policy, verifier env redaction, owner decisions, attestation keys | must be preserved |
| Audit → remediation | `bt_audit_gate`, `bitacora_platform/quality_delivery.py`, `bt_remediation.py`, watch `_remediate` | revise path cancels EVERY live attempt (`scheduler_ops_apply.py:84-85`) |
| Plan migration / rebase | `bt_scheduler_core/rebase.py`, `bt_scheduler_plan_compat.py`, `bt_planner/schema_13.py`, M1 doc upgrade 1–9, SQLite `user_version` migrations | sound, versioned |
| Crash recovery | `bt_scheduler_executor/recovery.py` + M1 `needs_reconcile` + `apply_observation` | shim adoption by pid+boot_id:starttime |

## 3. Responsibility matrix

| Subsystem | Verdict | Target owner |
|---|---|---|
| M1 domain rules: frontier, resources, budgets, verdict independence, rework, rebase, subplans | CONSERVAR | Control Plane (pure functions) |
| M1 persistence doc + outbox + `seen_events` + dispatch redelivery | REEMPLAZAR | DBOS workflow/step checkpoints + workflow IDs |
| M1 owner loop (`scheduler.step/run`, `bt_scheduler_run`) | ADAPTAR | DBOS run workflow; composition root keeps wiring |
| M3 ledger, executor loop, recovery, outbox | REEMPLAZAR | DBOS steps + Linux supervisor reconciliation |
| M3 shim + procinfo (process identity, tree kill, timeouts) | REEMPLAZAR | systemd user units + cgroup v2 (`cgroup.kill`, `MemoryMax`, `RuntimeMaxSec`) |
| M3 brief/prompt/drivers/workspace/handoff/retention | CONSERVAR | reused as step bodies |
| M6 sandbox runner, policy, evidence, pass cache | CONSERVAR | step body |
| M6 requests/outbox redelivery | REEMPLAZAR | DBOS step result |
| M5 `policy.propose` | CONSERVAR (single retry authority) | Control Plane |
| M5 stores, leases, checkpoints | REEMPLAZAR | DBOS |
| Healing ×4, watch restarts, ready-monitor, monitor repairs (hard-coded to pictures/REQ-021) | REEMPLAZAR / ELIMINAR | typed classifier + bounded recovery workflow; systemd `Restart=` for the engine |
| 10 failure classification sites, 6 excerpt builders | ADAPTAR → one typed taxonomy + one `FailureDigest` | Evidence plane |
| M2 decision engine, quota assessment, route pins | CONSERVAR (preflight → step) | Control Plane |
| Integration line / integrator / invariant | CONSERVAR + add CAS on refs + serialize | Control Plane, single integration step |
| Hold file, `central_lock`, `stop_owner` | REEMPLAZAR | DBOS cancel/resume + workflow-ID serialization |
| Hand-written contracts / unexecuted JSON Schemas / TS inline types | ADAPTAR / REEMPLAZAR | Pydantic v2 models → generated JSON Schema → checked TS |
| Legacy `bt_worktree`, `bt_integration_lock`, dormant M2 modules, preview/rollout | ELIMINAR-candidates | only after equivalence is shown |

Estimated generic infrastructure DBOS/systemd can own: ~4–5k lines of runtime code plus tests (M1 store/outbox/
dispatch/loop ~900, M3 ledger/loop/recovery/shim/procinfo ~1,300, watch/monitors/hold/locks ~1,300, M4/M5/M6
outboxes/leases ~800).

## 4. Confirmed defects driving owner intervention (evidence: REQ-021 today)

1. Failure feedback hides the decisive error: `quality_delivery.py:116-124` keeps the last 1500 chars of
   stderr+stdout; `_ERROR_LINE` misses Playwright `Timeout … exceeded` / `locator.waitFor`. att-0095's note to the
   agent held only server JSON logs. 24 T2.6 attempts, ~1.3 M tokens each.
2. "Cannot find module" hint tells the agent to `npm ci` when a SOURCE file is missing (T3.11 att-0093).
3. Every nonzero exit is `FAIL_CODE` (`bt_scheduler_quality/evidence.py:429`): a Node heap OOM in the verifier
   sandbox (att-0088) cost a code-rework attempt.
4. Revise cancels unrelated live attempts; stale analysis keyed by task only produced duplicate repair T3.14 and
   cancelled T2.6 att-0085 mid-verification.
5. Operator `cancel-attempt` kills the shim by pid without identity and never signals the agent's own group
   (`bt_scheduler_executor_adapter.py:544-559`); a `setsid` descendant outside the worktree survives cancel.
6. Owner race → `OWNER_ACTIVE` exit 2 → the watchdog gives up permanently.
7. Remote: F4, F10, F11, F21, F33, F41 still present (see contracts map); `bt_page_flow_review.py:86` rejects
   `m6.evidence-manifest/1.1`.
8. Hard-coded project hacks in shared code (`bt_scheduler_decisions.py:339`, `bt_scheduler_monitor_repairs.py`).

## 5. Environment facts that shape the design

- Hooks, bitácora CLI and the monitor service run under `/usr/bin/python3` (no pydantic/psutil/dbos). The uv tool
  venv `~/.local/share/uv/tools/bitacora` is an editable install of the repo. ⇒ hook/bitácora import paths must
  stay stdlib-only; the new runtime is a separate package loaded only by the DBOS backend under the uv venv.
- systemd 261 user manager: `systemd-run --user` works without sudo; delegated controllers `cpu memory pids`;
  `cgroup.kill` and `cgroup.freeze` available.
- Docker 29 (user in `docker` group). Ports 5432–5434 are taken by other projects' Postgres containers.
- 16 cores, 30 GB RAM.

## 6. Integration strategy

- Feature flag `execution.backend = legacy | dbos` in `bt_config` (default `legacy`). Ownership is recorded per run
  at creation; nothing changes owner implicitly.
- New packages: `bt_contracts` (Pydantic models, schema generation), `bt_supervisor` (Linux process runtime),
  `bt_durable` (DBOS execution plane: workflows, steps, queues, migration bridge). Control-plane logic is reused
  from existing modules through narrow ports; DBOS details stay inside `bt_durable`.
- Shared defects (1–3, 5, remote findings) are fixed in place because they also hurt legacy runs.
- Each milestone lands as its own commit(s) on `metamorfosis` with targeted + regression tests; nothing is pushed.
