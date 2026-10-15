---
status: draft
---
# metodologia — Week 2026-10 W3 (2026-10-12 → 2026-10-18)

_Rewritten at the end of each session that week. Set `status: final` once the week is over and rolled up._

## Highlights
- Scheduler work advanced through M4 and now has one tested Planner→M1→M2→M3→M4 fixture flow; P-036 and P-038 closed under REQ-018.
- M2 remains deterministic for live routing: the held-out Laya classifier did not beat the deterministic baseline and REQ-016 stays paused.
- REQ-008's T4 runtime fixes were verified, then the owner paused default activation and the remaining milestones.

## Done
- REQ-012 closed Planner phase 1 and its approval/plan synchronization gates.
- REQ-014/REQ-017 completed the Scheduler M3 executor and M4 observer; P-033, P-035, P-037 were closed, with measured host-local M4 fixture budgets.
- REQ-018 connected bounded M3 stream ingestion to M4, read-only metrics to M2, and audit incidents to M1; offline M4 recovery and the real two-profile P-036 smoke passed. Suites: M1 248, M2 65, M3 276, M4 135, Scheduler wildcard 236/4 skipped, package 15.
- REQ-007 migration proposal records M0–M9, a preservation inventory and rollback gates; implementation remains unapproved.

## Decisions
- D-027 keeps remaining Laya experiments English-only and separate from M2 route quality; D-035 pauses REQ-016 training.
- D-038 corrects the T12 sample count and retains its host-local budgets; D-039 keeps M1→M4 drain caller-driven; D-040 requires verified offline recovery candidates.

## Not done / dropped
- REQ-008 is paused at T4: default activation and T5–T8 remain pending the owner's explicit resume.
- REQ-015 remains awaiting plan approval; REQ-016 remains paused and no Laya checkpoint is enabled for live routing.
- REQ-007 implementation and the cross-platform matrix remain deferred; no repository push or deployment was part of this week's Scheduler closeout.

## Carried over to next week
- P-013 bitácora backup/sync decision; P-017 migration follow-ups; P-003 visual review; P-001 executor heartbeat/crash resume.
- P-036 and P-038 are closed. P-039 tracks existing M4 Ruff style findings. M4 stays opt-in; any live runtime caller must drain M3 from its owning M1 loop and manage the outbox retry cadence.

## REQ-008 — paused checkpoint
- M1/T3 implemented; T4 structured runtime and review fixes verified with 139 affected regressions and 10 wheel/install checks, plus scoped ruff.
- D-018 preserves completion history/counters through validated supersession. Owner paused execution; P-018 links the REPORT/HANDOFF. Defaults and T5–T8 remain pending; no active task writer/test handle or global installation.

## Migration planning — session 01a13754
- REQ-007: code-grounded platform migration proposal in [[../../migracion/README|migracion]], 10 milestones and 22 tasks, with no-loss inventory and rollback gates. Legacy baseline: 578 tests, 2 routing failures. Implementation remains unapproved.
