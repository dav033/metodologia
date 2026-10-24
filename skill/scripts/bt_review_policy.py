"""One rule for how much adversarial review a supervised task gets before a commit.

With the independent milestone audit active, that audit is the milestone's adversarial review: per-commit Antagonist
passes would repeat it at the price of an extra top-tier session per commit. Tests, linters, the task's `verify` and
the security rules stay mandatory either way. Without a milestone audit the per-commit gate is the only review left and
stays on. Both prompt builders (legacy `_rules` and the orchestrator package) take their wording from here, so the two
paths cannot drift apart. Reference: references/subagents.md §The antagonist gate.
"""
from __future__ import annotations

GATE = ("Follow references/engineering.md of the `metodologia` skill and run the antagonist review "
        "(references/subagents.md) before EVERY commit.")
WITH_AUDIT = ("Follow references/engineering.md of the `metodologia` skill. Run the task's verify, tests and linters "
              "before every commit. Do NOT run the antagonist per commit: the independent milestone audit reviews "
              "the consolidated milestone diff at the end. Invoking the antagonist subagent (Opus / Codex High) "
              "on individual commits is forbidden while this audit covers the work, including high-risk and "
              "architecture tasks. Keep all security checks mandatory.")


def milestone_audit_active(state: dict | None, unit: list[dict] | None = None) -> bool:
    """True when an independent audit of the unit's own milestone is still to run (todo or in progress). Without a
    unit: any pending audit. A task outside a milestone is never audited, so it keeps the per-commit gate."""
    milestones = {t.get("milestone") for t in unit or ()}
    if unit is not None and (not milestones or None in milestones):
        return False
    return any(t.get("synthetic") and t.get("kind") == "audit" and t.get("status") in ("todo", "in_progress")
               and (not milestones or t.get("milestone") in milestones)
               for t in (state or {}).get("tasks", []))


def _frozen_subplan_id(state: dict | None, unit: list[dict] | None) -> str | None:
    if not isinstance(state, dict) or not isinstance(unit, list) or not unit:
        return None
    plan = state.get("frozen_plan")
    if not isinstance(plan, dict) or plan.get("schema_version") != "1.3.0":
        return None
    if not isinstance(state.get("plan_id"), str) or state.get("plan_id") != plan.get("plan_id"):
        return None
    if (not isinstance(state.get("revision"), int) or isinstance(state.get("revision"), bool)
            or not isinstance(plan.get("revision"), int) or isinstance(plan.get("revision"), bool)
            or state.get("revision") != plan.get("revision")):
        return None
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        return None
    plan_tasks = {item.get("id"): item for item in tasks if isinstance(item, dict) and isinstance(item.get("id"), str)}
    unit_ids_list = [item.get("id") for item in unit if isinstance(item, dict)]
    if (len(unit_ids_list) != len(unit) or not unit_ids_list
            or any(not isinstance(task_id, str) for task_id in unit_ids_list)):
        return None
    unit_ids = set(unit_ids_list)
    if any(task_id not in plan_tasks for task_id in unit_ids):
        return None
    declared_ids = [plan_tasks[task_id].get("subplan_id") for task_id in unit_ids]
    if any(not isinstance(subplan_id, str) or not subplan_id for subplan_id in declared_ids):
        return None
    unit_subplans = set(declared_ids)
    if len(unit_subplans) != 1:
        return None
    subplan_id = next(iter(unit_subplans))
    if any(plan_tasks[task_id].get("subplan_id") != subplan_id for task_id in unit_ids):
        return None
    return subplan_id


def subplan_audit_active(state: dict | None, unit: list[dict] | None = None) -> bool:
    """Use frozen PLAN.json membership and audit identity; RUN status alone cannot establish subplan coverage."""
    if not isinstance(state, dict):
        return False
    plan = state.get("frozen_plan")
    unit_subplan = _frozen_subplan_id(state, unit)
    if not isinstance(plan, dict) or not isinstance(plan.get("subplans"), list) or unit_subplan is None:
        return False
    declarations = [item for item in plan["subplans"] if isinstance(item, dict) and item.get("id") == unit_subplan]
    run_tasks = state.get("tasks")
    if len(declarations) != 1 or not isinstance(run_tasks, list):
        return False
    tasks = plan.get("tasks")
    plan_tasks = {item.get("id"): item for item in tasks if isinstance(item, dict) and isinstance(item.get("id"), str)}
    statuses = {item.get("id"): item.get("status") for item in run_tasks
                if isinstance(item, dict) and isinstance(item.get("id"), str)}
    audit_id = declarations[0].get("audit_task")
    audit = plan_tasks.get(audit_id)
    return bool(isinstance(audit_id, str) and isinstance(audit, dict)
                and audit.get("kind") == "audit" and audit.get("subplan_id") == unit_subplan
                and statuses.get(audit_id) in ("todo", "in_progress"))


def commit_review_rule(state: dict | None, unit: list[dict] | None = None) -> str:
    """The prompt line that tells a builder how much review to run before a commit."""
    plan = state.get("frozen_plan") if isinstance(state, dict) else None
    if isinstance(plan, dict) and plan.get("schema_version") == "1.3.0" and plan.get("subplans"):
        covered = subplan_audit_active(state, unit)
    else:
        covered = milestone_audit_active(state, unit if unit else None)
    if not covered:
        return GATE
    return WITH_AUDIT
