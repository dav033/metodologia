---
id: REQ-028
status: clarifying
created: 2026-10-20
track: standard
---
# REQ-028 — Per-run integration branch and remediation tasks: audit findings stop cascading rebuilds

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

## Problem & goal
Today every task builds on a merge of its ancestors' snapshots, so an audit finding that edits a base task makes every task built on it stale: they are redone one by one (REQ-027 round 3: T3 → T6/T10 → T12/T13 → T15b-f, with attempts spent on start rejections and gate rejections). D-087/D-088/D-089 bound and soften that, but the cause stays: there are parallel versions of the code and the scheduler reconciles them after the fact.

Two structural changes remove the cause (owner choice 2026-10-20, after the conflict resolver of D-089):
1. **Integration branch per run.** Every accepted task is merged at once into one branch of the run; the next task starts from its tip. A fix is one more commit, not a parallel version.
2. **Remediation tasks.** A blocking audit finding creates a task appended to the plan, on the integrated tree, scoped to the files of the finding and with its own verification; the audit is then rerun. History is not reopened, so nothing cascades.

**Success looks like:** on a replay of the REQ-027 audit rounds, a finding on a base task costs one remediation task plus one re-audit, with zero rebuilds of unaffected tasks and no `INTEGRATION_CONFLICT` card for the owner.

## Users / actors / stakeholders
-

## Scope (in)
<!-- User stories, ranked. Each one independently valuable and testable.
### US-1 (P1, Must) — <title>
As a <actor>, I want <capability> so that <benefit>.
**Acceptance:**
- Given <context>, when <action>, then <result>.
-->

## Out of scope
-

## Requirements
<!-- EARS style, numbered so tests/plan can cite them:
- R1. When <trigger>, the system shall <response>.
- R2. If <unwanted condition>, then the system shall <response>.
- R3. While <state>, the system shall <response>.
For business processes, "the system" can be a role or the process ("the approver shall…"). -->

## Edge cases & errors
-

## Constraints
_Tech, integrations, data, security/privacy, compliance, budget, people._

## Priorities & phases
_MoSCoW + what is MVP vs later._

## Timeline & dependencies
-

## Assumptions
_Best guesses taken instead of asking, with why. Revisit if they turn out wrong._

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Missing |
| Users / actors | Missing |
| Scope | Missing |
| Out of scope | Missing |
| Flows & behavior | Missing |
| Edge cases | Missing |
| Acceptance criteria | Missing |
| Constraints | Missing |
| Priorities & phases | Missing |
| Timeline | Missing |

## Clarifications
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->
