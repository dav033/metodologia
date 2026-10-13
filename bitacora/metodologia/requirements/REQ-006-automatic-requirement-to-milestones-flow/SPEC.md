---
id: REQ-006
status: ready
created: 2026-10-12
track: standard
---
# REQ-006 — Automatic requirement-to-milestones flow with learning

> Note: earlier day-log headings of 2026-10-12 titled "REQ-006" refer to the unregistered Arch/SSH platform work
> (runtime port, profiles, telemetry, Agile delegation, concurrency). This is the first registered REQ-006.

## Problem & goal
Today the flow depends on the agent following written instructions and on manual steps: sizing a request, moving from
interview to execution (approve + launch), and nothing remembers what the owner prefers. The owner wants it automatic:
throw a requirement, the agent sizes it, interviews exhaustively when needed, the plan is cut into small-to-medium
milestones, each milestone runs in a new clean session with only the context it needs, everything persists and the
agent learns the project and the owner's preferences over time.

**Success looks like:** from a normal session in a project, a requirement ends in a verified implementation with at
most one explicit approval (and none when the plan is small and low-risk), executed headless, with permanent
decisions in DECISIONS.md and learned preferences available to every later session.

## Owner decisions (2026-10-12, interview)
- D1. Execution starts by itself after the interview; approval is requested only when the plan is large, touches
  money/security/data, or contains irreversible/external actions. The owner can pause or stop at any time.
- D2. One milestone = one clean session; it ends with verification and a commit. A milestone groups several related
  tasks and is verifiable on its own.
- D3. Learning: candidates with evidence; promoted to permanent when the owner confirms or it repeats.
- D4. Entry is the owner's normal Claude Code/Codex session in the project; executors run headless in the background
  (tmux/systemd) with notifications and status, no windows.

## Scope (in)
### US-1 (P1, Must) — automatic hand-off with a risk gate
As the owner, I want the finished plan to start executing by itself unless it is risky or large so that I am asked
only when it matters.
**Acceptance:** `handoff` validates the plan, lists the reasons when approval is needed, otherwise approves and launches.
### US-2 (P1, Must) — milestone sessions
As the owner, I want each plan milestone to run in its own clean session so that context stays small and work stays
resumable.
**Acceptance:** plans with `### M1 — …` groups run one session per milestone; plans without milestones behave as today.
### US-3 (P1, Must) — learning with evidence
As the owner, I want the agent to retain my preferences and project facts, as reviewable candidates, so that later
sessions start informed.
**Acceptance:** candidates are stored with evidence, promoted by confirmation or repetition, and injected into new
sessions concisely.
### US-4 (P2, Should) — background by default, driven from the normal session
As the owner, I want executors in the background and the whole flow runnable from my normal session so that I do not
babysit windows.

## Out of scope
- Same-repository parallelism with git worktrees (separate, still open).
- A learned task classifier / Laya (D-002).
- Changing the ladder (haiku → sonnet → opus) or the verification model.

## Requirements
- R1. When a plan is handed off, the system shall validate that it has tasks, each with a verify command or an explicit
  `verify: none` reason, and that repo roles are registered.
- R2. If the plan has more than 8 milestones, or any `level: architecture` task, or any task marked `risk: high`, or a
  task text mentioning irreversible/external/financial/security actions, then the system shall require approval and
  print every reason.
- R3. When no approval reason exists, the system shall mark the plan approved, launch the marathon in the background
  and record the hand-off in the day log.
- R4. While a plan declares milestones, the supervisor shall run all pending tasks of the current milestone in one
  session, in plan order, settle each task independently and start a new clean session for the next milestone.
- R5. If a milestone session ends with unfinished tasks, then the next session shall continue the same milestone;
  failure accounting, ladder and blocking stay per task.
- R6. When a learning is added, the system shall store it with scope (project|user), evidence and status candidate;
  it shall become confirmed on explicit confirmation or after 3 independent sightings; rejected items are not shown.
- R7. When a session starts, the system shall inject confirmed learnings (project + user) and the count of candidates
  awaiting review, within a bounded size.
- R8. When a milestone session ends, its prompt shall instruct the agent to propose learnings and to record permanent
  decisions in DECISIONS.md.
- R9. The default executor display shall be background; `config` shall allow switching to windows.
- R10. Plans without milestones, `delegate`, workers and every existing command shall keep working unchanged.

## Edge cases & errors
- A milestone whose tasks have different repo roles: its repo set is the union; concurrency only with disjoint sets.
- A task of a milestone blocked: the milestone does not advance to dependents; others continue per `after:`.
- Learnings with secrets: refused if they match credential patterns.
- No tmux and no systemd-run: hand-off falls back to printing the command; nothing silently skipped.

## Constraints
- Python stdlib only; Linux, macOS and Windows; tests must not touch the real bitácora; no push.

## Assumptions
- "Risky" keywords are a conservative lexical check on plan text; the owner can always approve manually.
- Promotion threshold (3 sightings) and the 8-milestone limit are defaults, configurable in `.state/config.json`.

## Coverage
| Topic | State |
|---|---|
| Goal & problem | Covered |
| Users / actors | Covered |
| Scope | Covered |
| Out of scope | Covered |
| Flows & behavior | Covered |
| Edge cases | Covered |
