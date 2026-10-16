---
id: REQ-022
status: ready
created: 2026-10-16
track: standard
---
# REQ-022 — Opt-in Scheduler runtime, status and recovery

## Problem & goal
M1–M6 exist as composable Scheduler modules, but the supported launcher still starts only the legacy marathon supervisor. The CLI watcher and web UI also read and control only legacy `RUN.json`. A Scheduler-owned run therefore has no complete, discoverable lifecycle from launch through status and safe recovery.

**Goal:** provide an explicit Scheduler path for an already approved, frozen `PLAN.json`; keep the current legacy path as the default; make Scheduler-owned status visible and controllable; and resume durable M1/M3 state after a process or machine restart without creating a second agent writer.

**Success looks like:**
- `bitacora.py launch REQ-NNN --mode marathon --scheduler` starts the Scheduler supervisor only after the existing approval and frozen-plan gates pass.
- `bitacora.py scheduler-run REQ-NNN --resume` reopens the same M1/M3 run identity and reconciles existing attempts before dispatching more work.
- The CLI watcher, project dashboard and requirement page show `RUN.projection.json`, its heartbeat and stale state. Controls go through M1.
- Legacy launch, `RUN.json`, run controls and existing plans keep their current behavior unless the Scheduler option is selected.

## Users / actors / stakeholders
- David starts, inspects, pauses, resumes and cancels a bounded plan run from the CLI or local web UI.
- M1 owns run state, task state, reservations and verdict acceptance.
- M2 recommends a currently eligible route; M3 launches and reconciles its process.
- M4, M5 and M6 retain their existing independent opt-in points. A `NEEDS_REVIEW` result remains an operator decision.

## Scope (in)

### US-1 (P1, Must) — Launch an explicitly Scheduler-owned run
As David, I want to choose the Scheduler when launching a marathon so that the existing legacy launcher remains available while new runs can use M1/M2/M3.

**Acceptance:**
- Given an approved requirement with a valid frozen `PLAN.json`, when I launch with `--scheduler`, then the launcher starts `scheduler-run` and M1 is the sole owner of the run.
- Given an unapproved/invalid plan, a legacy `RUN.json`, or a mismatched Scheduler plan revision, when I launch or resume, then execution fails closed before an agent starts.
- Given the option is absent, the existing `launch --mode marathon` path is unchanged.

### US-2 (P1, Must) — See liveness and recover after a crash
As David, I want the Scheduler projection to carry a fresh heartbeat and a clear resume command so that a dead supervisor is distinguishable from a slow task and can be safely restarted.

**Acceptance:**
- While the owner process is alive, `RUN.projection.json` is atomically refreshed with Scheduler authority and heartbeat information.
- If its heartbeat becomes stale, `watch` and the web page say the run may be stopped and show the exact `scheduler-run REQ-NNN --resume` command.
- Resume uses the persisted M1 database and M3 attempt ledger. Live attempts are reattached; missing or uncertain process evidence never authorizes a second writer.
- The per-user login resume entry targets the Scheduler command for Scheduler runs; `--no-autostart` suppresses it. No entry is installed during this implementation session.

### US-3 (P1, Must) — Inspect and control Scheduler runs
As David, I want CLI and web status to use the same projection and pause/resume/cancel to reach M1 so that controls cannot corrupt or overwrite legacy run state.

**Acceptance:**
- `watch`, the project dashboard and the requirement run page detect the run authority and read only its matching view.
- Pause, resume and stop map to M1 pause, resume and cancel operations for Scheduler runs.
- A control on a legacy run keeps using the existing legacy `RUN.json` implementation.

### US-4 (P2, Should) — Receive concise run notifications
As David, I want terminal and blocked Scheduler state changes to use the existing native/optional ntfy notifications so that background outcomes are visible without polling.

**Acceptance:**
- Notifications use the existing `bt_notify` configuration and remain best effort; delivery failure cannot stop or change a run.
- The runtime does not add a provider, send a message during development, or repeatedly notify for the same persisted terminal state after a restart.

## Out of scope
- Enabling Scheduler mode by default or migrating historical `RUN.json` runs.
- Automatically activating M4, M5 or M6 globally, bypassing M1 ownership, or treating `NEEDS_REVIEW` as success.
- Starting a real task or provider during implementation/verification; tests use temporary repositories and fake providers.
- Cloud scheduling, remote workers, unattended approval of new plans, or unbounded/continuous project polling.
- Reworking the legacy supervisor's plan-resume guard. The current `PLAN_REF_STALE` guard and its existing regression case will be retained and included in verification; the old P-026 scratch observation will be reconciled against that evidence.

## Requirements
- R1. Scheduler use shall require an explicit launch option and shall not change the legacy default.
- R2. Scheduler launch shall require the existing requirements gate, an approved plan and the frozen `PLAN.json` revision; `--force` shall not bypass these gates.
- R3. A requirement shall have exactly one run authority. Scheduler launch/resume shall refuse a legacy `RUN.json`; the legacy supervisor shall continue refusing a Scheduler-owned database.
- R4. The Scheduler runtime shall compose the existing M1/M2/M3 ports using deterministic, project-scoped local stores and existing route/quota/profile policies.
- R5. Runtime status shall be written atomically to `RUN.projection.json`, never to `RUN.json`, and include a UTC heartbeat, Scheduler authority, plan identity and task summary.
- R6. Resume shall bind to the same approved plan id, revision and hash; M3 shall reconcile durable process identity before any retry. An uncertain attempt shall retain its reservation and shall not be relaunched automatically.
- R7. CLI and web status shall detect Scheduler authority, render stale heartbeats, and provide the correct resume command. Web controls shall use M1 operations for Scheduler runs.
- R8. Per-user login recovery shall use the correct supervisor command and remain disableable with `--no-autostart`.
- R9. Status notifications shall be best effort, bounded, deduplicated across a clean restart, and use only the existing local/optional ntfy channel.
- R10. M4/M5/M6 and operator-owned review states shall preserve their existing activation and decision boundaries.

## Edge cases & errors
- Missing, corrupt or stale projection: report unavailable/stale status and preserve the M1 database; never fall back to editing `RUN.json`.
- Another legacy or Scheduler owner is active: refuse duplicate launch and leave the existing run untouched.
- Frozen plan changes or a different revision is approved: refuse resume with a stable plan-binding error.
- M2 has no eligible route, quota is stale/exhausted, or a profile is denied: show the blocked/waiting cause; do not invent a route or bypass policy.
- M3 process identity cannot be verified: retain uncertainty and reservation; do not start a replacement writer.
- M6 is absent or returns `NEEDS_REVIEW`: keep the task awaiting operator action; do not report completion.
- Notification backend is unavailable: log the failure and continue the run.

## Constraints
- Preserve one-way dependency boundaries and the single core importer (`bt_scheduler_adapter.py`).
- Keep local Scheduler, M2 and M3 stores outside versioned requirement files; create no cross-run/shared M2 ledger.
- Keep state-changing controls behind the local web token/CLI boundary and route them through M1.
- Do not commit, push, merge, activate a real run, or install an autostart entry during implementation.
- User-facing web copy stays in Spanish; follow the existing project styling and accessibility patterns.

## Priorities & phases
- Must: scheduler-owned launch/resume, heartbeat/projection, authority-aware CLI/web read and controls, crash-safety regressions.
- Should: terminal/blocked notifications through existing channels.
- Later: separately authorized M4/M5/M6 activation/configuration or remote scheduling.

## Timeline & dependencies
- One implementation sequence in the current methodology repository, after owner approval of the plan.
- Depends on the existing frozen planner, M1, M2, M3, local notification and web-control contracts.

## Assumptions
- `--scheduler` is the explicit opt-in under the existing `--mode marathon`; the default remains the current legacy supervisor.
- M2 continues using the deterministic production policy and configured local account/quota evidence; Laya remains gated by its existing evidence allowlist.
- Starting a Scheduler run may install the same per-user login-resume entry as a legacy marathon; `--no-autostart` disables it. This behavior is only activated when David launches that mode.
- M4, M5 and M6 are not implicitly enabled by this adoption. A run without an independent verifier may wait for operator action, by design.
- The existing `PLAN_REF_STALE` resume behavior is already implemented; verify it against the old scratch reproduction before closing P-026.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- 2026-10-16: scope inferred from David's explicit instruction to fix the identified P-001/P-026 autonomy gaps. Existing defaults, M1 ownership and separately opt-in verification/recovery modules remain protected.
