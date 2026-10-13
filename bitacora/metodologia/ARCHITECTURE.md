# metodologia — Architecture

**Last verified:** 2026-10-10 against the current uncommitted working tree.
**Audit status:** complete · **Coverage:** methodology skill sources, CLI, templates, tests and eval inventory · **Independent review:** spec and standards reviews completed.

## 1. Goals and quality priorities
- Provide one durable, reviewable workflow for requirements, implementation, project memory, infrastructure and long-running development across supported agent harnesses.
- Priorities: accurate scope and evidence; safe autonomy with explicit gates; resumability without relying on conversation history.

## 2. Constraints and conventions
- Canonical source lives in this repository under `skill/`; installed copies are generated outputs.
- User-facing messages are Spanish; repository instructions and code follow the repository's English convention.
- No external orchestration runtime or global config change is required for the documented workflows.

## 3. Context (C4 level 1)
David gives a goal to Claude Code or Codex. The methodology skill routes the work through requirements, engineering, documentation and tool references. The bitácora is the durable project record; the repository's tests/evals verify mechanics and expected behavior.

## 4. Containers (C4 level 2)

| Container | Tech | Responsibility | Owns data | Talks to (protocol) |
|---|---|---|---|---|
| Skill instructions | Markdown | Requirements, audit, engineering, agent orchestration and marathon workflow | No runtime state | Agent harness loads references |
| Bitácora CLI | Python stdlib | Project/session resolution, deterministic inventory, plans, hooks and run state | Workspace metadata and run files under bitácora | Local filesystem; launches agent CLI for marathon |
| Templates | Markdown | Central project docs and requirement artifacts | No runtime state | Rendered by bitácora CLI or agent |
| Deterministic tests | Python unittest | Validate CLI, workspace, onboarding, marathon and platform behavior | Temporary test roots | Local processes/filesystem |
| Behavior evals | JSON + Python | Describe model behavior scenarios and graders | Eval fixtures/results | Claude CLI when explicitly run |

## 5. Modules
- `skill/scripts/bitacora.py` exposes the CLI. `bt_audit.py` builds read-only workspace inventory and does not scan product source.
- `bt_workspace.py` owns the workspace registry model; the audit path avoids its mutating discovery helpers.
- `skill/SKILL.md` routes to the focused references: `architecture-audit.md`, `agent-orchestration.md`, `subagents.md`, `marathon.md`, and `self-improvement.md`.
- UI/copy work loads `interface-quality.md` on demand; engineering links to it and to `subagents.md`'s evidence protocol. These extend existing acceptance and spec/standards review, without new runtimes or approval stages (D-004).
- Audit routing has a separate budget (D-005). `bt_subscription_sources.py` reads provider quota metadata; `bt_subscriptions.py` owns schema-v1 sample/history persistence, reservation and headroom validation; `bt_subscription_schedule.py` installs the hourly user-systemd timer. `bt_cli_accounts.py` owns account/usage/telemetry CLI presentation; the router reads only the local cache (D-006).

## 6. Key flows
1. New project: owner interview → confirmed intent in SUMMARY → inventory → repo-by-repo evidence → cross-repo synthesis → independent review → ARCHITECTURE/PENDING; zero-repo or incomplete coverage remains partial.
2. Existing project audit: restate prior intent and confirm changes → read-only inventory → bounded inspection and checks → update product-level architecture and coverage.
3. Autonomous implementation: approved PLAN → dependency-ordered task sessions → RUN.json checkpoints and bounded retries → independent verification → completion report.

## 7. Cross-cutting concepts
- The audit inventory never reads source or secret values, invokes Git, or changes workspace state; architecture judgment belongs to the agent workflow.
- Parallel writes require disjoint ownership and worktree isolation when available. The coordinator integrates and independently verifies every wave.
- A worker's completion claim is not evidence. Existing approval and external-action gates remain in force.

## 8. Deployment
Not applicable to the skill source itself. Installation is an explicit separate operation; this change was not installed globally.

## 10. Decisions, risks, glossary
- D-001 records how public orchestration patterns were adapted.
- Risks and debt: PENDING.md. The first duplicate full-suite attempt produced real-bitácora fixtures; cleanup authorization is pending.
- Workspace audit: one product can span several repos; `partial` means a repo, material answer, or independent review is missing.
