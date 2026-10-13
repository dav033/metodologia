---
id: REQ-002
status: in-progress
created: 2026-10-10
track: deep
---
# REQ-002 — Proactive skill guidance and permanent improvement

## Problem & goal
The methodology skill is active in each session, but the user wants it to surface relevant capabilities when a task could benefit from them and to improve itself continuously instead of only following its existing instructions. Improvements may include skill-owned code, preferences and configuration.

**Success looks like:** When a user goal maps to an unfamiliar skill capability, the agent explains the relevant help briefly and contextually. Complex work is decomposed and coordinated across subagents only when parallelism is safe and useful; long autonomous work has durable checkpoints and a clear resume path. When evidence shows a durable skill defect or quality gap, the agent fixes the skill-owned source, validates it and reports the result without waiting for a separate request.

## Users / actors / stakeholders
- David, the skill owner and user.
- The AI agent, which applies the skill and maintains its source.

## Scope (in)
### US-1 (P1, Must) — Surface relevant skill capabilities
As a user, I want the skill to explain relevant capabilities when my goal suggests I may not know they exist so that I can use them effectively.
**Acceptance:**
- Given a request whose goal directly matches a skill capability that could change the approach or outcome (for example, a long project task, a deploy/hosting operation, or a project-status question), when that capability has not already been explained in the current workflow, then the agent briefly names it and explains how it helps with this request.
- The agent avoids generic skill pitches and repeated boilerplate when no capability materially helps or it has already been explained in the current workflow.
### US-2 (P1, Must) — Improve the skill proactively
As the skill owner, I want clear skill defects, repeated friction and quality gaps to be investigated and fixed permanently so that future sessions improve.
**Acceptance:**
- When there is explicit user feedback, a reproducible defect/check failure, a confirmed mismatch with an agreed requirement, or friction recurring across sessions, the agent inspects the cause and makes an appropriately scoped change to skill-owned code, instructions, tests, defaults, preferences or configuration. A speculative idea without such evidence is recorded as a proposal, not silently implemented.
- The canonical source is the tracked methodology repository (`~/dev/metodologia`); installed symlinks/copies are outputs. The agent edits the canonical source, not generated installation files, and runs the installer only when the specific installation update is authorized.
- The agent preserves unrelated changes, does not commit or push, and does not ask before low-risk, reversible, validated changes inside the methodology source repository that are within this request. If validation cannot run, it reports the exact blocked check and does not claim the improvement complete.
- Machine-wide Codex/Claude configuration is changed only when the request clearly authorizes the specific change; unrelated custom settings are preserved.
### US-4 (P1, Must) — Orchestrate parallel and autonomous work
As a solo developer, I want the skill to coordinate subagents and long-running work safely so that larger changes can progress with clear ownership, durable state, and trustworthy verification.
**Acceptance:**
- For substantial work, the skill builds a dependency-aware task graph, identifies independent tasks, assigns explicit file ownership and contracts, and dispatches only tasks that can safely run concurrently.
- Parallel writers use isolated worktrees when available; shared files have one owner. The coordinator waits for workers, reconciles their results, resolves conflicts, and independently verifies each completed wave before proceeding.
- Delegation briefs include the complete relevant context, scope, constraints, verification and stop conditions; the skill does not assume workers inherit the full conversation.
- Long autonomous runs persist progress at task/phase boundaries, resume from durable artifacts after interruption, bound retries/time/concurrency, and stop or request input at the established safety gates. They never report a worker claim as verified success without evidence.

### US-3 (P1, Must) — Handle rules that conflict with the user's goal
As a user, I want the skill to identify a rule that blocks my goal and ask what behavior I want so that I can choose a task-specific exception or a durable rule update.
**Acceptance:**
- When any user-controlled rule blocks the requested task—including skill rules, repository AGENTS/CLAUDE guidance, or David's own global preferences/configuration—the agent identifies the exact rule/source and impact, then asks whether the user wants a one-time exception or a permanent change before proceeding with the blocked behavior. If the rule is shared with collaborators or global, the question names that broader effect.
- Rules that the skill cannot change due to higher-priority instructions are explained clearly, with an allowed alternative where possible.

## Out of scope
- Rewriting global user preferences or machine-wide agent configuration unrelated to this skill.
- Changing external services, credentials, security permissions or destructive state without a clearly scoped user request.
- Generic explanations of every skill capability on every turn.
- Adding external orchestration runtimes, credentials, global settings or automatic permission bypasses as part of this documentation change.
- Speculative changes without explicit feedback, reproducible evidence, a confirmed requirement mismatch or repeated friction.

## Requirements
- R1. When the user's goal suggests a relevant skill capability they may not know, the agent shall explain that capability and its practical relevance concisely, without generic repeated boilerplate.
- R2. When feedback, repeated friction, a defect or a clear quality gap reveals an opportunity to improve the skill, the agent shall investigate the cause and proactively implement a durable skill-owned fix.
- R3. For skill-owned improvements, the agent shall update relevant code, documentation, tests, defaults, preferences or configuration as appropriate, run meaningful validation, preserve unrelated changes and report outcomes; it shall not commit or push.
- R4. The agent may make reversible, validated changes within the methodology skill repository under this standing authorization. It shall change machine-wide Codex/Claude settings only when the specific change is clearly authorized and shall preserve unrelated customizations.
- R5. When any user-controlled rule blocks the requested task—including skill rules, repository AGENTS/CLAUDE guidance, or David's own global preferences/configuration—the agent shall identify the rule/source and impact and ask whether the desired change is a one-time exception or a permanent rule update before performing the blocked behavior. If a permanent change affects a shared repo or global behavior, name that scope and make it only after the user chooses that change.
- R6. The agent shall not offer to change or bypass higher-priority instructions that it cannot modify; it shall explain the constraint and offer an allowed alternative.
- R7. For substantial multi-step work, the agent shall model task dependencies, explicitly assign ownership and contracts, use bounded concurrency, and isolate parallel writers when the harness supports it; it shall reconcile and independently verify each wave before continuing.
- R8. Delegated tasks shall receive a self-contained brief with goal, context, file scope, constraints, verification and stop conditions; the coordinator shall wait for all delegated work and validate reported outcomes.
- R9. Long autonomous runs shall maintain durable progress/checkpoints, task status, evidence and next actions so a fresh session can resume without relying on conversation history; retries, runtime duration and concurrency shall be bounded, and safety/approval gates remain in force.

## Edge cases & errors
- The task has no relevant skill capability: continue normally without a generic pitch.
- A change would affect global settings, security/permissions, credentials, external services, destructive data or unrelated system configuration: stop that portion and seek the required specific authorization. Do not treat general skill-improvement authorization as authorization for these changes.
- A requested behavior conflicts with any user-controlled rule: surface the exact source and impact, then ask whether the user wants a one-time exception or permanent update to that rule. Pause only the blocked behavior until answered.
- A request conflicts with a higher-priority non-editable instruction: explain the limit and provide an allowed alternative; do not ask the user to approve bypassing it.
- A proposed improvement cannot be validated: do not claim it is complete; record the exact check/command that remains and why. Independent work that does not depend on that check may continue.

## Constraints
- The canonical editable source is `~/dev/metodologia`; skill code, documentation, tests, defaults and installation templates/configuration are in scope. Generated installed copies are not canonical and are updated only when the specific install/change is authorized.
- Preserve user customizations and all unrelated working-tree changes.
- Code changes use the repository's existing language and conventions. Permanent behavioral changes need meaningful tests/evals where feasible; run relevant deterministic checks, and report unavailable/costly checks accurately.
- No commit or push without a separate explicit request.

## Priorities & phases
- Must: contextual feature discovery, proactive skill-owned fixes, meaningful verification/reporting, and conflict handling.
- Should: add evaluation cases for relevant feature discovery and rule-conflict handling.
- Out of default scope: unrelated global system changes and external state.

## Timeline & dependencies
- No deadline supplied.
- Requires access to the methodology source tree and its existing test/eval tooling.

## Assumptions
- “Preferences and configuration” includes the skill's own defaults, settings and installation templates; machine-wide preferences require clear authorization for the specific change.
- A one-time exception and a permanent update to the affected user-controlled rule are distinct choices and should be offered separately.
- Existing repository modifications unrelated to this request must remain untouched.

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
### Round 1 — 2026-10-10
- Q: When should the skill explain itself? → A: When a user's goal suggests a relevant feature they may not know the skill has; explain contextually, without a generic pitch.
- Q: How proactive should self-improvement be? → A: Investigate and implement permanent improvements to skill-owned code/configuration, test and report without waiting for another request.
- Q: What configuration is in scope? → A: Skill-owned code, instructions, tests, defaults and preferences; preserve settings and change global Codex/Claude configuration only when clearly authorized.
- Q: What autonomy boundaries apply? → A: Apply reversible validated changes in the skill repo directly; ask before global security/permissions, credentials, external services, destructive data or unrelated system settings. If a skill/rule blocks the user's goal, identify it and ask whether to change behavior.
### Round 2 — 2026-10-10
- Q: If a user-controlled rule blocks a request, should it ask about a one-time exception or permanent update? → A: Explain the exact rule and impact, then ask whether the user wants a one-time exception or a permanent rule change; pause the blocked action until answered.
### Round 3 — 2026-10-10
- User added that the skill must handle subagents, concurrency and orchestration well, support long autonomous development, and research public skills/repos for adaptable ideas. This scope is included by user instruction; adopt patterns with provenance and keep external code, permissions and runtimes out of scope.

## Implementation status
The approved plan is implemented and verified in the methodology working tree. The changes remain uncommitted for owner review; no merge or publication has occurred.
