---
id: REQ-008
status: in-progress
created: 2026-10-14
track: deep
---
# REQ-008 — Fresh milestone orchestration and bounded context execution

## Problem & goal
The owner requires execution without a long-lived agent accumulating implementation context. Planning must aggressively establish requirements, limits, scope and acceptance, including on continuation. Execution must replace planning in the same terminal and use fresh milestone orchestrators with bounded context, delegated work, durable documentation and autonomous recovery.

## Actors
David approves scope and the plan. A deterministic terminal supervisor owns process lifecycle. Each fresh milestone orchestrator owns bounded delegation, integration, verification, recovery rulings and documentation. Independent agents implement, inspect or debate within assigned scope.

## Requirements and acceptance
- R1. At conversation entry, including `continue`, revalidate authoritative scope, requirements, limits and acceptance. Preserve confirmed decisions; ask about missing or contradictory decisions only. Execution cannot silently skip an unresolved material ambiguity. Acceptance: continuation fixtures with drift require clarification; unchanged approved scope retains approval.
- R2. Once the plan is approved, exit the planning session and execute successive fresh milestone orchestrators in the SAME terminal. Acceptance: a foreground launcher test proves identical TTY, distinct child processes/sessions and no resumed conversation argument; interrupt/exit restores terminal state.
- R3. Each orchestrator receives a bounded, milestone-specific context package with approved scope, constraints, acceptance, relevant decisions and evidence references. Never forward complete transcripts, all previous milestone notes or unbounded log text. Acceptance: oversized histories do not grow the input past its configured cap; mandatory constraints cannot be silently truncated.
- R4. Orchestrators delegate bounded implementation/exploration/testing, own integration and verification, and ensure documentation is persisted before completing or yielding. Acceptance: realistic fake-provider execution records delegated task ownership, verify evidence, updated documentation and final verdict.
- R5. Rotate before a configured context limit even within a milestone. Persist completed work, remaining work and evidence; resume with a new instance and a bounded package. Acceptance: injected context pressure produces a checkpoint and a distinct successor without duplicate completed effects. If reliable usage is unavailable, enforce an observable conservative turn/output budget; never claim estimated counts are exact tokens.
- R6. On a recoverable stall, automatically request THREE independent read-only proposals using available Haiku medium or gpt-6-luna medium accounts. Agents receive distinct solution briefs, then exchange bounded proposals and critique them. The orchestrator decides from evidence and persists alternatives, rationale and next action. Acceptance: fake-provider stall executes proposal, debate and ruling phases and resumes; consensus alone cannot mark a task done.
- R7. Recovery is durable, bounded and availability-aware: no recursive councils, unlimited retries, invented proposals or unauthorized side effects. Unavailable providers wait or produce an explicit blocked state; account restrictions and quotas remain enforced. Acceptance: crash/resume, repeated stall, missing proposals, quota and user-stop scenarios preserve recovery state and budgets.
- R8. Preserve approval, task dependencies, independent audits, verification, locks, isolation and no-push/no-commit permissions. Acceptance: regression suite plus end-to-end scheduler/relay tests; fresh orchestration never broadens approval.
- R9. Aggressively audit the actual entry, continuation, planning, launch, milestone, recovery and closing flows. Resolve contradictory instructions/templates and audit implementation independently. Acceptance: requirement-to-test evidence matrix, two fresh review axes and documented remaining limits.

## Out of scope
Push, merge, commits, deleting existing files, changing credentials/security permissions, unrelated fixes, global configuration changes and installing updated wrappers without specific authorization. Existing background runs must not be silently replaced or duplicated. Windows/macOS live validation stays deferred as previously requested; avoid introducing platform-specific regressions.

## Constraints and edge cases
Use existing local file-based state and providers. Preserve unrelated changes. No personal-browser control. A wrong or stale handoff, missing wrapper, concurrent run, oversized mandatory context, interrupted delegation, absent usage telemetry or unavailable accounts must produce explicit safe behavior. Infrastructure/access failures requiring owner permission cannot be solved by agent debate.

## Priorities and timeline
All R1–R9 are required for completion. No owner deadline. Implement in independently verified milestones after plan approval.

## Assumptions to validate during implementation
- Reuse the relay parent launcher lifecycle rather than typing commands into a terminal. Unsupported current launcher contexts need an explicit migration command, never a fabricated in-place replacement.
- Context thresholds and debate/output caps must be explicit configurable policy, documented and tested against actual provider telemetry; numeric defaults will be justified from measured entry packages and supported context capacity.
- A council proposes and critiques; only one writer integrates the chosen solution. Three agents can use the same eligible account if provider capacity allows; three different accounts are not required.

## Coverage
Goal, actors, scope, exclusions, flow, errors, acceptance, constraints and priorities: clear. Timeline: no deadline. Exact budget defaults: delegated engineering decision with measurement evidence.

## Clarifications — 2026-10-14
- Same terminal: owner confirmed replacing the planning session and rotating per milestone.
- Continue: owner selected revalidation, not repeating settled interview questions.
- Context: owner confirmed rotation by limit inside a milestone as well.
- Recovery: original request specifies three Haiku medium or Luna medium agents, proposals, debate and orchestrator ruling.

## Required operational contracts (fresh spec review)
- Bootstrap: an already-running client cannot acquire a new parent launcher. Implement and verify M1/M2 using the current bounded delegation mechanism; activate the new path only after its PTY checks pass. The concrete checkout-based launch command and supported wrapper preconditions must be produced before any live transition. If the current client lacks the required parent, report the supported manual entry command; never claim the current session was replaced or kill an unverified process. No global wrapper install is implied.
- Terminal proof: use real subprocesses inside a PTY, checking controlling terminal, foreground process group, planning-child exit, new provider conversation identity and terminal restoration on normal exit and interruption. Missing-wrapper paths must leave the existing session intact.
- Runtime context: account for reads, tool results and debate artifacts during execution, with aggregate output limits and reserved room for checkpoint/documentation. Test pressure during tool output and debate, not just initial prompt size. Reject oversized mandatory scope rather than truncating it.
- Stall taxonomy: recoverable implementation/verification failures and no-progress events trigger the council before terminal blocking; quota/capacity waits and missing authorization are separate states. Define validated triggers and durable per-task/per-milestone budgets before wiring the scheduler. Resume cannot reset these budgets. Incomplete proposal rounds cannot yield an implementation ruling; wait/retry within the budget or explicitly block.
