---
id: REQ-029
status: ready
created: 2026-10-20
track: standard
---
# REQ-029 — Autonomous recovery from repeated audit failures

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
The owner wants the system to resolve repeated technical failures with minimal human coordination. REQ-027 T18 reached eleven attempts and exhausted both remediation rounds and named-task rework allowances. The current fallback asks the owner to copy findings into task notes and reopen tasks. Improve that recovery system; do not manually repair REQ-027 product code or answer its current decision as a substitute.

**Success looks like:** the Scheduler diagnoses repeated failure from authoritative evidence, schedules a justified correction strategy, executes and independently verifies it, and shows progress or a concrete blocker in the visual monitor. A repeated retry on unchanged evidence is not progress.

## Users / actors / stakeholders
- Owner supervises/stops recovery and supplies genuinely missing permission or product decisions.
- M1 owns state, dependencies and dispatch; M2/M3 route and execute work; M4 observes; M5 advises recovery through its adapter; M6 and independent auditors verify closure. Planner coordination must preserve these boundaries.

## Scope (in)
- Durable recovery cases; diagnostic work over full evidence/history/snapshots; constrained corrective strategies applied through existing plan revisions and execution; independent re-audit; visual supervision; offline REQ-027 replay.
<!-- User stories, ranked. Each one independently valuable and testable.
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
- Hand-patching F2/F19/F20; auto-accepting security risks; disabling gates; raising ordinary retry/rework limits to conceal loops; arbitrary model-generated shell/state mutations; replacing the Scheduler; unrelated production/settings changes.

## Requirements
- R1. On exhausted automatic remediation/rework or repeated verified failure without progress, create one durable recovery case bound to run, revision/hash, audit attempt, audited base/snapshot and immutable findings evidence. Duplicate triggers/restarts must not duplicate work.
- R2. Preserve complete validated finding summaries, evidence, owners and verification results. F-numbers are local to one ledger: renumbering must not lose recurrence, and stripping numbers must not merge unrelated findings. Preserve semantic anchors and mark uncertain matches explicitly.
- R3. Before further corrective dispatch, diagnose what previous corrections changed, which problems persisted/fixed/appeared/regressed, and whether the audit examined the intended integrated tree. Missing evidence is an observable diagnostic blocker, never empty success.
- R4. Diagnostic output uses a versioned runtime-validated contract: supported corrective actions, evidence references, prerequisite order, expected changed outcome and falsifiable checks. Model text is untrusted data and cannot authorize arbitrary commands, paths, scope or state changes.
- R5. Apply validated corrections through existing task/revision mechanisms, preserving unrelated accepted work, current integration base, dependencies, permissions and M1 authority. Put audits/cross-checks after corrections; reject stale applications. Supply task findings/notes automatically from evidence.
- R6. Persist each recovery hypothesis, action, verification and progress result. Refuse repeating the same failed strategy on unchanged evidence. Preserve existing counters. Proposed bounded policy: one supervised diagnostic recovery cycle after ordinary budgets, then explicit escalation if no permitted strategy remains; specify policy and exhausted behavior in the approved plan.
- R7. `/flow` and plan views show diagnosing, preparing corrections, executing, re-auditing, resolved or genuinely blocked states with reasons/evidence and a stop control. Technical corrections must not require editing RUN.notes or using the CLI. Ask the owner only the specific permission/product choice the system lacks.
- R8. Only independent verification and audit evidence on the resulting integrated tree can close findings/accept work. Verification shall cover the reproduced symptom and all affected owner/code surfaces; choosing the first command of the first owner is insufficient. Compare actual changed paths against declared coverage before acceptance; uncovered changes require verification replanning or an explicit blocker. A corrective task modifying web code shall not be accepted with backend-only checks. Model confidence, exit zero, fewer F-numbers or a generated plan alone cannot establish success.
- R9. Keep legacy audit/decision records readable; reconcile existing cases without silently answering owner-only decisions. First produce a reviewable REQ-027 recovery preview. Approval of this plan conditionally authorizes one bounded REQ-027 recovery activation after the system upgrade passes independent audits, offline proof and a fresh preview, using the accepted tested runtime snapshot with ownership/stop/rollback preserved. Newly launched runs inherit the approved policy; other existing runs remain preview unless separately authorized. No second confirmation is required for this already scoped activation.
- R10. Cover repeated/renumbered findings, stale bases, exhausted ordinary budgets, prerequisite build failures, unavailable evidence, diagnostic timeout/failure, unsafe proposals, duplicate/restart/stale application and no progress. An isolated integration run must start real entry points and show system-generated corrections and independent re-audit without manual notes/decision workarounds.
<!-- EARS style, numbered so tests/plan can cite them:
- R1. When <trigger>, the system shall <response>.
- R2. If <unwanted condition>, then the system shall <response>.
- R3. While <state>, the system shall <response>.
For business processes, "the system" can be a role or the process ("the approver shall…"). -->

## Edge cases & errors
- Findings split/merge, simultaneous audits, user stop or revision changes during diagnosis, interrupted application, executor loss and unknown external side effects.
- A prerequisite build blocks E2E: distinguish the build failure from downstream assertions that never ran.
- No safe permitted action, unavailable evidence/diagnostician or exhausted diagnostic budget: durable explicit blocker and targeted escalation; no unbounded retries.

## Constraints
- Canonical code is `/home/david/dev/metodologia/skill`; preserve unrelated changes and all REQ-027 evidence.
- Extend existing recovery/orchestration boundaries; document any contract/persistence migration and rollback. M1 retains authority; M4 is observational.
- Use existing routing/agent authorization. Planner/spec must not choose providers, models, effort or worker counts.
- Immutable evidence references, bounded reads and model deadlines, redacted data; no private reasoning as authority.
- Product corrections belong to authorized system executors, not hand edits by the coordinator.

## Priorities & phases
Must: evidence/progress model, bounded diagnostic recovery, validated application and independent verification. Then visual supervision and rollout preview. Each milestone ends in an independent audit.

## Timeline & dependencies
- Start from current Scheduler and REQ-027 r9. Implementation follows one reviewed plan; accepted system audits, offline verification and fresh preview precede its conditionally authorized active-run rollout.

## Assumptions
- The owner authorizes a durable system improvement and offline use of REQ-027 evidence, without waiving blocking findings.
- A bounded diagnostic escalation is preferable to raising retry/rework limits. The plan exposes this default and rollout for review.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Clear |
| Users / actors | Clear |
| Scope | Clear |
| Out of scope | Clear |
| Flows & behavior | Clear |
| Edge cases | Clear |
| Acceptance criteria | Clear: R1–R10 |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear: reviewed plan before implementation |

## Clarifications
- Owner: T18 failed more than ten times; prepare the system to solve this class of failure, rather than fixing the task manually.
- Technical choices come from investigation; significant architectural choices receive one concrete plan review.
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
