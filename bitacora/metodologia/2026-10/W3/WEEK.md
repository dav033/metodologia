---
status: draft
---
# metodologia — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Scheduler work advanced through M4 and now has one tested Planner→M1→M2→M3→M4 fixture flow; P-036 and P-038 closed under REQ-018.
- REQ-020 M2 T13–T23 offline integration, adversarial validation and synthetic benchmark are complete with independent review; the live-provider gate remains open.
- M2 remains deterministic for live routing: the held-out Laya classifier did not beat the deterministic baseline and REQ-016 stays paused.
- REQ-008's T4 runtime fixes were verified, then the owner paused default activation and the remaining milestones.

## Done
- REQ-012 closed Planner phase 1 and its approval/plan synchronization gates.
- REQ-014/REQ-017 completed the Scheduler M3 executor and M4 observer; P-033, P-035, P-037 were closed, with measured host-local M4 fixture budgets.
- REQ-018 connected bounded M3 stream ingestion to M4, read-only metrics to M2, and audit incidents to M1; offline M4 recovery and the real two-profile P-036 smoke passed. Suites: M1 248, M2 65, M3 276, M4 135, Scheduler wildcard 236/4 skipped, package 15.
- REQ-021 wired opt-in M6 verification through the existing M1 boundary and proved Planner→M1→M2→M3→M4→M5→M6 rejection/recovery/acceptance. M6 package 67, integrated chain plus real-M3 test 6, and Scheduler wildcard 271 with 5 opt-in skips passed; the shutdown race found in review is fixed.
- REQ-019 T19 passed its fresh two-route gate and bounded live run in 74.351 s: one controlled quota failure, one real alternate-provider CLI invocation, two M5 decisions, continued snapshot and M1 completion. T20 spec and standards audits approved; acceptance matrix and final handoff are recorded, closing P-040.
- REQ-020 T13–T23 passed focused source, M1/M2/M3/M4/M5 E2E, adversarial and benchmark checks. Independent audit found and verified a fix for one eager M4 import; T20 metric history passed 5 tests and integrated T21 passed 8. The frozen benchmark labels/windows are synthetic and observed real quota/attribution coverage is 0%; T24–T26 remain gated.
- REQ-007 migration proposal records M0–M9, a preservation inventory and rollback gates; implementation remains unapproved.

## Decisions
- D-043 keeps M6 opt-in through unchanged M1 `VerificationPort`; D-027 keeps remaining Laya experiments English-only and separate from M2 route quality; D-035 pauses REQ-016 training.
- D-049 preserves legacy quota-cache keys while deduplicating effective account aliases in memory; D-048 keeps M2 shadow comparison opt-in and side-effect-free.
- D-038 corrects the T12 sample count and retains its host-local budgets; D-039 keeps M1→M4 drain caller-driven; D-040 requires verified offline recovery candidates.

## Not done / dropped
- REQ-008 is paused at T4: default activation and T5–T8 remain pending the owner's explicit resume.
- REQ-015 remains awaiting plan approval; REQ-016 remains paused and no Laya checkpoint is enabled for live routing.
- REQ-007 implementation and the cross-platform matrix remain deferred; no repository push or deployment was part of this week's Scheduler closeout.
- M6 remains opt-in under D-043; the full Planner→M6 chain is verified locally, and no global activation was requested.
- REQ-020 T24's bounded real-provider experiment and dependent T25/T26 are not authorized by plan execution alone; no live provider or quota operation was used in this session.

## Carried over to next week
- P-013 bitácora backup/sync decision; P-017 migration follow-ups; P-003 visual review; P-001 executor heartbeat/crash resume.
- P-036, P-038 and P-040 are closed. P-039 tracks existing M4 Ruff style findings. M4/M5/M6 stay opt-in; live callers must drain M3 from the owning M1 loop and manage their durable outbox cadence.

## REQ-008 — paused checkpoint
- M1/T3 implemented; T4 structured runtime and review fixes verified with 139 affected regressions and 10 wheel/install checks, plus scoped ruff.
- D-018 preserves completion history/counters through validated supersession. Owner paused execution; P-018 links the REPORT/HANDOFF. Defaults and T5–T8 remain pending; no active task writer/test handle or global installation.

## Migration planning — session 01a13754
- REQ-007: code-grounded platform migration proposal in [[../../migracion/README|migracion]], 10 milestones and 22 tasks, with no-loss inventory and rollback gates. Legacy baseline: 578 tests, 2 routing failures. Implementation remains unapproved.
