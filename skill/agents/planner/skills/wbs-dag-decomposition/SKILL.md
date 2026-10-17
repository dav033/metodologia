---
name: wbs-dag-decomposition
description: Breaks a validated requirement into milestones, independently actionable tasks, acceptance criteria, and dependency edges that fit this methodology's PLAN.json contract.
---

Source: addyosmani/agent-skills@aeac41d (MIT), `skills/planning-and-task-breakdown/SKILL.md`. Adapted: codebase-first dependency mapping, small verifiable tasks, acceptance and verification. Original: milestone/task IDs, classifications, evidence, and dependency semantics come from `bt_planner`.

# Contract-compatible work breakdown

Use the actual code and validated requirement to create the smallest plan that covers the requested result.

1. Identify the required behavior and its boundaries. Inspect candidate files and consumers; use exact paths and existing verification commands.
2. Group work into milestones with acceptance criteria. Break each milestone into independently actionable tasks, each with an observable result, task-level acceptance criteria, expected paths, verification, and evidence-backed classification.
3. For non-trivial behavior, specify only what the implementer must not decide independently: relevant inputs and outputs, precedence or algorithm, invariants, preserved contract, error/exception behavior, and objective acceptance. Do not compress a known business rule into vague prose; do not prescribe internals that cannot affect the required behavior. Surface unresolved product decisions explicitly.
4. Use `PLAN.json` schema 1.2.0. Map every numbered requirement through each task's `covers` IDs to acceptance criteria and verification; declare cross-task contracts in the plan's `interfaces`; give every task a supported `kind` and every verification item its `category`. Map every task back to the goal and use only fields the schema defines.
5. Separate verification into static, functional, integration, regression and product evidence when those categories apply. Inspect that named commands exist. Mark planned checks as planned; do not imply a passing test establishes product acceptance.
6. Put a dependency in `after` only when one task needs a result produced by another. Order shared-contract or conflicting work explicitly. Leave tasks unordered only when the plan contract can safely treat them as independent; coupling is a signal, not permission to parallelize. For shared interfaces, name producer/consumer tasks, ownership, inputs/outputs, invariants and integration criteria.
7. Keep tasks small enough for one focused implementation and verification pass. Split a task when it crosses independent behavior, contracts, or verification boundaries.
8. Build the acyclic graph using only task IDs and `after`. The schema has no `parent_id` or nested subtask records; milestones group tasks, and all task entries are actionable leaves. Never add unsupported `subtasks`, `depends_on`, schedule, or executor fields.
9. Before estimating from history, query `python3 skill/scripts/bitacora.py --project <project> plan-json history --kind <kind> [--complexity <value>] [--scope <value>] [--risk <value>] [--coupling <value>]`. Use observed duration, failure, retry, quality or consumption data only when verified and comparable; retain units, source quality, sample count and uncertainty. Otherwise keep it unknown. Never choose or rank providers/services, accounts, models, effort, quota or worker count; those belong to the caller or M2/Scheduler.
10. Verify that each dependency names a real task and no task is orphaned from the goal. Let `bt_planner check` enforce the structural and graph invariants it actually implements; report its limits separately.

Do not invent dates, effort, code paths, precedent, command results, or product decisions. Record uncertainty and its downstream impact rather than hiding it in an estimate.
