"""Scheduler projection facts that legacy read models need but the core snapshot omits."""
from __future__ import annotations

from typing import Any


def attempt_budgets(scheduler: Any) -> dict[str, dict[str, int | bool | str]]:
    """Read each task's active retry budget from the scheduler's authoritative state and config."""
    return scheduler.read(lambda ctx: {
        task_id: {
            "attempts_used": len(task.attempts) - task.budget_base,
            "max_attempts": ctx.config.max_attempts,
            "retries_remaining": max(0, ctx.config.max_attempts - (len(task.attempts) - task.budget_base)),
            "retry_exhausted": (task.state == "blocked" and task.reason == "attempts_exhausted"
                                and len(task.attempts) - task.budget_base >= ctx.config.max_attempts),
            "reason": task.reason,
        }
        for task_id, task in ctx.state.tasks.items()
    })
