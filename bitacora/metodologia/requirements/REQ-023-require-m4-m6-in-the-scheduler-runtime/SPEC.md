---
id: REQ-023
status: ready
created: 2026-10-16
track: deep
---
# REQ-023 — Require M4-M6 in the Scheduler runtime

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The supported Scheduler owner runtime currently creates M1/M2/M3 only. Although an offline integration test
manually composes M4/M5/M6, ordinary Scheduler runs omit them. Even when a caller configures M4, the owner loop does
not drain M3 streams or deliver the M4 incident outbox. Monitoring, bounded recovery and independent verification
are therefore absent from the supported run lifecycle.

**Success looks like:** every supported Scheduler-owned run starts M4/M5/M6, drains and records M3 output, routes
recovery through M5 and requires a correlated M6 verdict before a task completes. A local offline end-to-end test
proves rejection, recovery and acceptance without a real provider call.

## Users / actors / stakeholders
- David operates Scheduler runs and resolves `NEEDS_REVIEW` items.
- M1 owns run/task/attempt state; M2 assigns routes; M3 owns agent processes; M4 observes execution; M5 advises
  recovery; M6 verifies approved checks.

## Scope (in)
### US-1 (P1, Must) — Make all Scheduler owner runs compose M4-M6
As David, I want every supported Scheduler launch to use M4, M5 and M6 so monitoring, recovery and quality checks
are part of the ordinary run lifecycle.

**Acceptance:**
- Given a valid frozen plan, when `scheduler-run` or `launch --scheduler` starts, then it initializes distinct
  durable M4/M5/M6 stores before dispatching tasks.
- Given an invalid or unavailable required module/store, when a new run starts, then no M3 task is dispatched and
  the CLI reports a stable failure; no optional-verifier fallback is used.

### US-2 (P1, Must) — Run M4 from the M1 owner loop
As David, I want the owner loop to drain bounded M3 streams into M4 and deliver M4's audit-only incidents through
M1 so stored monitoring evidence reflects actual executions.

**Acceptance:**
- During and after each M3 attempt, the owner drains available frames until terminal output is drained and delivers
  the durable M4 incident outbox with a stable run-scoped claim token.
- M4 cannot change task state, launch/retry work, or declare success. M4 failures stay visible and never silently
  bypass M1 ownership.

### US-3 (P1, Must) — Make M5 and M6 required ports
As David, I want M5 to advise M1 on every recovery and M6 to verify every completed attempt so failed work cannot
be accepted without an independent verdict.

**Acceptance:**
- M5 recommendations remain bounded and persisted; M1 alone applies retry/wait/block decisions and requests a new
  M2 route when a retry is approved.
- M6 verifies the exact approved M1 order against the matching M3 snapshot. Only a correlated PASS can complete the
  task; FAIL follows existing M1/M5 recovery; `NEEDS_REVIEW` remains operator-owned.

### US-4 (P1, Must) — Preserve run isolation and the existing route policy
As David, I want module state to resume with the same Scheduler run and remain separate from M1, while M2's routing
policy and legacy state files remain unchanged.

**Acceptance:**
- M4/M5/M6 stores are private, durable, separate from each other and M1, and use the same stable runtime identity
  on resume.
- M2 continues its existing deterministic route policy; this change does not activate experimental M2 routing.
- The M3→M4 FIFO bridge rejects intermediate-symlink escapes and wheel metadata covers shipped runtime modules.

## Out of scope
- Enabling Scheduler as the default for legacy `launch --mode marathon`, or migrating historical `RUN.json` state;
  scope round 1 is still open.
- Changing M1 contracts, M2 route ranking/learning policy, provider profiles, or live provider behavior.
- Automatically resolving `NEEDS_REVIEW`, running a real task/provider, installing autostart configuration, or
  starting a web server.
- Removing low-level optional port injection used for isolated module tests and explicit custom compositions.

## Requirements
- R1. When a supported Scheduler owner runtime starts a new or resumed run, it shall compose M4, M5 and M6 with
  distinct, durable stores scoped to the stable runtime identity.
- R2. Before M1 dispatches an attempt, the runtime shall initialize all required module stores and the M6 policy;
  initialization failure shall exit visibly without dispatching work or selecting a fallback verifier.
- R3. While M3 attempts are active or have undrained terminal output, the owner loop shall drain bounded stream
  batches to M4 and deliver pending M4 incidents through M1 using the existing versioned audit contract.
- R4. The runtime shall connect M5 to M1's existing `RecoveryPort`; M1 remains the sole state owner and applies only
  M5's bounded retry/wait/block recommendations.
- R5. The runtime shall connect M6 to M1's existing `VerificationPort` for every verification order. M1 shall not
  complete a task without the matching correlated PASS; `NEEDS_REVIEW` shall remain pending for operator action.
- R6. If M6 sandboxing is unavailable or a check cannot be safely executed, the runtime shall preserve the existing
  `NEEDS_REVIEW`/fail-closed behavior and shall never execute checks unsandboxed.
- R7. If the M4 stream reference contains an intermediate symlink escape, the adapter shall reject it before opening
  the FIFO.
- R8. Existing legacy `RUN.json`, explicit legacy launcher behavior, M1 contracts and deterministic M2 routing
  shall remain unchanged unless scope round 1 says otherwise.
- R9. The installed wheel audit shall include every required Scheduler runtime module and pass.
- R10. Resume shall reopen the same module stores for the same runtime identity and shall not duplicate delivered M4
  incidents or lose M6 pending-verdict reconciliation.

## Edge cases & errors
- Existing legacy `RUN.json` or conflicting M1 authority: refuse Scheduler start as today; preserve both authorities.
- Missing, corrupt, unwritable or shared module stores: fail closed before new task dispatch with a stable diagnostic.
- M4 FIFO not yet created: retry on the next bounded owner-loop poll; invalid paths/frames remain visible errors.
- M4 storage pressure or M1 incident rejection: preserve the durable outbox and retry through M4's existing lease
  semantics; M4 does not mutate task state.
- M5 state corruption or evidence mismatch: M5 blocks recovery; no raw agent/provider output is trusted as authority.
- M6 rejects a result, is interrupted during restart, or needs operator review: reconcile its durable outbox; never
  convert an admission Ack or `NEEDS_REVIEW` into PASS.
- No task verification command or missing sandbox: M6 leaves the task pending/reviewable rather than skipping
  verification or running unsandboxed.
- Resume with an existing run: reuse its per-run stores and worker identity; do not create a second M1 run.

## Constraints
- Preserve M1 as the only Scheduler state/verdict authority and the one-way module/adapter import boundaries.
- Reuse the existing M4/M5/M6 modules and current M1 1.2.0 ports; do not add a third-party dependency or schema
  migration without a demonstrated need and a separately reviewed contract.
- Keep durable module state under private local `.state` storage, outside versioned requirement files and separate
  from M1. Retain existing bounded stores, permissions, retention, leases and sandbox limits.
- M4 remains an advisory observer; M5 recommends recovery; M6 verifies but does not resolve manual review.
- Do not push, commit, merge, change production data, activate a live run or install per-user autostart.

## Priorities & phases
- Must: required runtime stores/ports, owner-driven M4 stream/outbox loop, M5/M6 lifecycle, fail-closed behavior,
  resume, FIFO path fix, regression/E2E tests, package audit and D-052 superseding prior opt-in boundaries.
- Won't in this change: route selection from M4 metric history, legacy default migration unless scope round selects it,
  live-provider validation.

## Timeline & dependencies
- One local repository/worktree; depends on the existing M1/M2/M3/M4/M5/M6 modules and REQ-021 E2E contracts.
- Current worktree contains concurrent uncommitted changes. Patch only the required runtime composition, adapter,
  tests, packaging and project documentation; preserve all unrelated edits.
- Verify component and integrated Scheduler suites plus installed-wheel coverage; do not run live providers.

## Assumptions
- All Scheduler-owned launches (`scheduler-run` and `launch --scheduler`) become M4-M6-required; the existing
  legacy launcher stays separate unless scope round 1 chooses otherwise. Recommended to preserve D-051's authority
  boundary and avoid migrating historical `RUN.json` runs.
- Use the existing default `QualityPolicy`; if bubblewrap is missing or checks cannot be sandboxed, M6 leaves the
  item in `NEEDS_REVIEW` and never falls back to unsandboxed execution.
- Keep M2's current deterministic route selection. M4 metric history is not added as a ranking input because that
  would change routing beyond this request and conflict with D-050's evidence gate.
- Low-level compositions may still omit ports for isolated tests, but the supported owner runtime cannot.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Deferred — assumption A; confirmed at plan approval |
| Out of scope | Clear — legacy default migration excluded under assumption A |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear |

## Clarifications
- Round 1 (`rounds/round-01.json`) asks whether to preserve the legacy launcher. No answer has been recorded.
- Planning uses assumption A: require M4–M6 in every Scheduler-owned launch while leaving the legacy launcher separate.
  This is an explicit working assumption, not a recorded owner answer; the plan approval gate can confirm or change it.
