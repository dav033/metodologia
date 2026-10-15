---
id: REQ-018
status: planned
created: 2026-10-15
track: standard
---
# REQ-018 — Scheduler M1-M4 integration and offline monitor recovery

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
M1, M2 and M3 already run an approved plan end to end with fake provider CLIs. M4 has separate persistence and adapter suites, but no single fixture flow proves that M3's bounded stream reaches M4's durable store and that M4's metric and incident ports connect back to M2 and M1. The approved P-038 recovery follow-up also has no implementation.

**Success looks like:** one disposable Planner→M1→M2→M3→M4 flow persists normalized provider evidence, exposes metrics read-only to M2, and delivers audit-only incidents to M1; an offline recovery workflow exports and verifies a full archive and prepares a bounded candidate without modifying the source store; P-036 is run with fresh eligible profiles if the live quota gate permits it.

## Users / actors / stakeholders
- David operates and reviews the local Scheduler and M4 store.
- M1 owns run/task/attempt state; M2 selects routes; M3 owns agent processes and raw output; M4 observes and stores normalized evidence.

## Scope (in)
<!-- User stories, ranked. Each one independently valuable and testable.
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

### US-1 (P1, Must) — M3 stream ingestion through M4
As the Scheduler owner, I want bounded M3 frames normalized and stored by M4 so monitor evidence is durable and queryable.
**Acceptance:** A fixture execution produces a normalized event or an explicit gap in a disposable M4 SQLite store; the input frame is acknowledged only after durable persistence.

### US-2 (P1, Must) — M1–M4 end-to-end verification
As the Scheduler owner, I want one fixture flow across all four modules so the public contracts and authority boundaries are verified together.
**Acceptance:** A frozen plan is routed by M2, executed by M3's fake provider, observed by M4, and independently verified by M1; M4 metrics are read-only in M2 and incident references do not change task state.

### US-3 (P1, Must) — Offline M4 recovery
As the store operator, I want a verified full archive and a safely prepared compact candidate when online retention cannot fit so recovery can be reviewed without risking the source.
**Acceptance:** Export, integrity verification, candidate preparation and rollback evidence work on a disposable capped store; the source remains byte-identical and no open incident or undelivered outbox item is lost.

### US-4 (P2, Must) — P-036 multi-profile route smoke
As the Scheduler owner, I want the persisted route-choice smoke completed with fresh eligible profiles so real quota evidence is tested at the M2 boundary.
**Acceptance:** Fresh quota evidence is recorded immediately before a bounded disposable smoke; no profile that is stale, exhausted, unknown or unauthorized is launched.

## Out of scope
- Changing default methodology launch/supervisor behavior or activating M1–M4 globally.
- Modifying, compacting, replacing or deleting any live M4 store; only disposable test stores are mutated.
- Resuming REQ-016/REQ-015 model training, adding Z.ai, committing, pushing or deploying.

## Requirements
<!-- EARS style, numbered so tests/plan can cite them:
- R1. When <trigger>, the system shall <response>.
- R2. If <unwanted condition>, then the system shall <response>.
- R3. While <state>, the system shall <response>.
For business processes, "the system" can be a role or the process ("the approver shall…"). -->

R1. When an M3 output frame is observed, the methodology adapter shall normalize provider JSONL into allowlisted M4 records and persist the source cursor atomically before acknowledging the queued frame.
R2. If parsing, storage, or queue capacity fails, the flow shall retain retryable input or persist an explicit bounded gap; it shall not fabricate successful monitoring evidence.
R3. M1 shall remain the sole authority for task state; M4 incident references shall be audit-only and M2 metric history shall be read-only.
R4. Offline recovery shall create a no-overwrite full archive, verify its integrity and manifest, and prepare a candidate under the existing 512 MiB active-store cap without modifying the source.
R5. Any recovery VACUUM shall receive the complete caller-supplied `sqlite_temp_dirs` list and shall fail closed when space or paths are insufficient.
R6. P-036 shall refresh quota immediately before execution and shall launch only a profile whose evidence is fresh, verified and permitted; if fewer than two profiles qualify, the smoke remains explicitly pending.
R7. The full fixture flow shall prove the M2-selected route reaches the matching fake provider and only the independent verifier can complete a task.

## Edge cases & errors
- Split or multiple JSONL events, malformed lines, provider mismatch, stream gaps, bounded queue pressure, SQLite full/busy, duplicate delivery, corrupt archive, destination already exists, active-store ceiling, insufficient VACUUM temp space, stale quota evidence, and no pair of eligible profiles.

## Constraints
Python standard library only in `bt_scheduler_monitor`; preserve existing D-022, D-024, D-029 and D-030–D-038 authority and compatibility decisions. M4 stores allowlisted normalized data only, never raw provider output. The M4 package reads no environment variables; recovery callers must pass all SQLite temporary directories. Fixture integration is offline. P-036 is a separate explicitly requested subscription-backed smoke and must remain isolated from fixture tests. Preserve all existing uncommitted work in the shared tree.

## Priorities & phases
Must: stream-to-store bridge, one full M1–M4 fixture flow, safe P-038 offline recovery, focused regressions. Must when eligible: complete P-036 with two fresh quota-valid profiles. This task does not activate the Scheduler for live methodology runs.

## Timeline & dependencies
Direct execution in the current session. Existing approved M1–M4 module contracts are prerequisites; P-036 is gated on a fresh quota read immediately before its separate smoke.

## Assumptions
The user's instruction to connect M1–M4, complete pending work and test the whole flow authorizes this local implementation and the already-tracked P-038 follow-up. Live provider use is limited to the explicitly tracked P-036 smoke; no live M4 store is changed.

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
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
