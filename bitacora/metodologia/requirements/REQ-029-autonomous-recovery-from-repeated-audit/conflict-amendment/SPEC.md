---
id: REQ-029
status: draft
created: 2026-10-20
track: standard
---
# REQ-029 — Autonomous recovery from repeated audit and integration failures

<!-- status: clarifying → ready → planned → in-progress → done | dropped -->

**Candidate revision 2; planning only. Owner goal is paused. No approval, freeze, rebase or resume is implied.**

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

- R11. When either an INTEGRATION_CONFLICT start failure or an M6 integration gate observation occurs, classify it as an integration conflict, preserve the full validated observation before clipping and bind run, frozen revision/hash, task/attempt/token, repository, consumer, both merge sides, accepted attempt identities, original base/snapshot/tree digests, actual full conflicting paths and the precise refusal of ordinary dependent rework. A clipped message or cached free-form diagnosis cannot authorize repair; unavailable full evidence blocks recovery explicitly.
- R12. Before selecting a structural repair, compare official accepted lineage, candidate lineage, declared ownership, exact changed paths and the approved DAG. Distinguish stale accepted descendants/carry ancestry, actual scope escape or conflicting ownership/dependencies, and incompatible product meanings. Existing ordered overlaps alone do not prove a broken plan. Repair only demonstrated defects; ask a targeted question for a genuine incompatible meaning or missing authority.
- R13. Structural recovery shall generate authorized executable convergence work through existing Planner/M1 revisions, with one designated writer per affected responsibility and retained accepted-side provenance. Rebuild stale descendants on the current accepted base or resolve the affected owned paths as justified by evidence. Produce an actual marker-free converged snapshot, run the union of both sides' existing behavior checks and the symptom oracle on that same integrated tree, then independent audit/cross-check. A new dependency, schema-valid revision, clean textual merge or one side's green checks alone cannot close the conflict. Never discard accepted behavior or authorize scope escape retrospectively.
- R14. Exhausted ordinary attempts/reworks or two consecutive verified no-progress observations shall enter the existing one-cycle REQ-029 policy; no parallel supervisor or extra structural budget exists. One cycle per run/audit-or-conflict lineage survives revision, renumbering and restarts; at most one diagnosis and eight corrective implementation tasks, with ordinary per-task attempts and at most one scoped supplemental attempt per independent audit. Convergence/rebuild tasks count toward the eight. Block unchanged retry while preparing recovery. Distinct external waits without verified unchanged facts do not count as no progress. Failure or no permitted strategy after the cycle produces an exact durable blocker.
- R15. M1 alone applies structural revisions with source/revision/accepted-map digests, stop generation, CAS leases and idempotency checkpoints. Preserve history, ordinary attempts/budget_base/waits/reworks, permissions, unaffected accepted work and current integrated base. Unaffected runnable tasks continue during diagnosis; application waits for natural quiescence of incompatible live work, without cancellation or starvation by new conflicting dispatch. Stop/hold wins every race. On interrupted apply, adopt only the identical approved operation; rollback disables recovery on schema-capable code and retains authoritative state/evidence rather than restoring budgets or silently changing accepted snapshots.
- R16. Offline integration shall replay both REQ-027 T15b att-0124 start conflict and T15a:8/att-0208 M6 conflict, including att-0142 stale accepted T15b and att-0204 replacement T15 ancestry. Start shipped CLI/watch/owner/executor/verifier and web entrypoints with only external providers replaced by controlled fixtures; demonstrate automatic bounded convergence and independent proof for both sides without RUN.notes/card answers. Also cover missing/truncated evidence, false structural diagnosis, scope escape, incompatible product meanings, exhausted rework, duplicate/stop/crash/CAS/rollback and one-side-only green checks. Views show structural versus semantic blocker truthfully and migration preserves legacy readable records and policy authorization.

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
| Acceptance criteria | Clear: R1–R16 |
| Constraints | Clear |
| Priorities & phases | Clear |
| Timeline | Clear: reviewed plan before implementation |

## Clarifications
- Owner: T18 failed more than ten times; prepare the system to solve this class of failure, rather than fixing the task manually.
- Technical choices come from investigation; significant architectural choices receive one concrete plan review.
<!-- ### Round N — YYYY-MM-DD
- Q: … → A: … -->

## Structural amendment evidence
Observed from official frozen plan r9: T3 → T15 → T15a → T15b → T15c already exists; T15c also waits for T7. T15a/T15b broad remote/web ownership overlaps are ordered. T15b accepted att-0142 predates replacement T15 att-0204 and T15a redo. The repeated gate may be stale descendant/carry lineage, rather than a missing edge. The exact causal classification remains evidence-derived at recovery time.

`bt_scheduler_integrator._merge` clips conflict paths to six and detail to 170 characters before publication. `bt_scheduler_quality_adapter._dependents_to_redo` discards the precise M1 rework refusal; delivery falls back to candidate rejection. `bt_block_diagnosis.CONFLICT` misses M6's integration gate prefix; the recorded red assertion returns code/retry_with_note. See PLAN.md evidence and review notes for actual inspected sources.

Accepted REQ-029 contracts are inspected at cumulative base 0310c7dc4a78b2589fa5044476470342dd8b583d, from T4's official order, not its unfinished worktree. T1's recovery-proposal/1 actions are retry/wait/block/rework_findings; the amendment adds a separate runtime-validated structural envelope and reuses its CAS event store without rewriting accepted /1 records.

## Convergence bootstrap
A convergence task cannot start with both conflicting snapshots as ordinary prerequisite ancestors. The trusted integrator produces conflict-bootstrap/1 from the exact failed merge/carry sources, with the unresolved tree, both parent snapshots, exact marker paths and source digests. M1 grants only the named convergence order, current plan/accepted map and stop generation access to it through the existing M3 base_ref resolver. Ordinary tasks keep their gate. The bootstrap is never accepted; the convergence executor resolves its authorized paths, proves both behaviors and publishes a normal independently checked result. Revised consumers depend on this accepted convergence producer while retaining unrelated prerequisites and original requirement/criteria coverage. No arbitrary snapshot override or silent dropped side is permitted.

## Amendment assumptions and constraints
The conditional authorization described in R9 remains a candidate policy for one REQ-027 activation only after resumed owner approval and the final system/offline gates. Planning this amendment does not consume that authorization. REQ-027 semantic resolution is not promised before convergence proof; a genuine specific authority/product/evidence blocker is an allowed system outcome. Full paths missing from clipped historic strings must be reconstructed in a disposable replay from hash-bound official sources, never guessed from the card. The failed T4 attempt is unaccepted reusable material only; T1–T3 definitions and accepted behavior stay unchanged.
