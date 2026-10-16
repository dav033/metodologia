---
status: approved
---
# REQ-019 execution plan

Authority: David's explicit request to implement the complete original M5 plan and verify Planner through M5.
Original: `/home/david/PLAN-FASE-5-M5-RECOVERY-MANAGER.md`. No acceptance item is removed.

## M5-H0 — Baseline and contract
- [x] T01 — Inspect real contracts, state, executor, handoff and existing test seams; INVENTORY.md.
- [x] T02 — Record SPEC and ADR D-041 before implementation.
- [x] T03 — Freeze unchanged M1/M6 signatures and isolated M5 schema; SPEC.md.

## M5-H1 — Pure policy
- [x] T04 — Validate bounded cases and hostile input.
- [x] T05 — Enforce identity, evidence, exclusivity and cancellation guards.
- [x] T06 — Classify known facts with conservative precedence.
- [x] T07 — Bound cooldowns, same-cause attempts, resets and repeated calls.
- [x] T08 — Deterministic pure policy and metamorphic tests.

## M5-H2 — Durable adaptation
- [x] T09 — Private bounded idempotent history with crash/concurrency tests.
- [x] T10 — Real RecoveryPort adapter and visible safe failure.
- [x] T11 — M3 public technical evidence and verified handoff.
- [x] T12 — Verification rejection evidence without accepting rejected work.

## M5-H3 — Operational integration
- [x] T13 — Optional wiring without M2/M4 and snapshot continuation.
- [x] T14 — New M2 assignment on retry; keep route hints advisory.
- [x] T15 — Legacy/config/worktree preservation, opaque telemetry and retention bounds.
- [x] T16 — Human/JSON inspection CLI with restart persistence.

## M5-H4 — Proof
- [x] T17 — Failure matrix and complete frozen Planner→M1→M2→M3→M4→M5→retry chain.
- [x] T18 — Crash checkpoints from receive to next attempt; no duplicate writer/decision.
- [ ] T19 — Bounded opt-in real CLI experiment in a disposable project with controlled failure.
- [ ] T20 — Independent spec/standards audit, acceptance matrix, measured report and handoff.

Rulings: policy metadata is versioned inside M5; M1 contract remains 1.2.0. Only finite validation is tightened
in M1. No live Scheduler activation. All provider experiments remain disposable and bounded.
T19 remains open: the required quota preflight found fewer than two eligible providers, so no provider process was
launched. T20 and closeout remain open until T19 is resolved. Production M6 verification is outside this M5
implementation and awaits the owner's answer to the pending verifier-boundary question.
