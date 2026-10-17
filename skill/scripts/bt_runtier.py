"""Marathon escalation ladder: which model and effort a task's session runs with.

Tiers are capability levels shared by every provider (bt_agents.LADDER): 0 light, 1 standard, 2 top. Every failed
attempt moves the task one tier up. A run pinned to one agent keeps its historical behaviour: Claude runs the
configured model at tier 0 (haiku unless --model says otherwise), then sonnet --effort xhigh, then opus --effort xhigh;
a configured model already stronger than the tier's is kept, only the effort rises; Codex keeps its model and raises
model_reasoning_effort to xhigh from tier 1 up. A run with a pool of accounts gets its route (account, model, effort)
from bt_agents.route. Rules: references/marathon.md, "Escalation ladder", and references/agents.md.
"""
from __future__ import annotations

import os
import shlex
import subprocess

import bt_agents

TOP = bt_agents.TOP
LADDER = ("haiku", "sonnet", "opus")
EFFORT = "xhigh"
# Tier 0 is bounded tightly; a stored `session_timeout_min` (an explicit --timeout, or a run started before the table
# existed) stays the cap and, without `session_timeout_by_tier`, the only timeout. Sessions carrying several tasks
# scale by MILESTONE_TIMEOUT_FACTOR in bt_runsession, so the budget stays proportional and bounded.
TIMEOUT_BY_TIER = {"0": 25, "1": 45, "2": 60}
GROUP_MAX = {"0": 3, "1": 1, "2": 1}  # tasks per session, by tier (milestone grouping, bt_runstate.unit_of)
TARGETS = {"sonnet": 1, "opus": 2, "standard": 1, "top": 2}  # `task escalate --to`


def start_tier(level: str | None, kind: str | None = None, complexity: str | None = None,
               risk: str | None = None) -> int:
    """`level: architecture` on the PLAN task line starts the task at the top of the ladder; an audit, a task declared
    `complexity: L` and a `risk: high` task start at 1 (bt_routing_policy.start_tier has the rules and the reason)."""
    return bt_agents.start_tier(level, kind, complexity, risk)


def tier_of(task: dict | None) -> int:
    try:
        return max(0, min(TOP, int((task or {}).get("tier") or 0)))
    except (TypeError, ValueError):
        return 0


def model_for(state: dict, tier: int) -> tuple[str | None, str | None]:
    """(model, effort) of a session at this tier; effort None means the CLI default. A state carrying the session's
    route (pool mode) answers with it."""
    route = state.get("route")
    if route and route.get("tier") == tier:
        return route.get("model"), route.get("effort")
    if state.get("pool"):
        return bt_agents.model_for(state.get("agent") or "claude", tier, state.get("model"))
    return bt_agents.legacy_model_for(state, tier)


def label(model: str | None, effort: str | None) -> str:
    return (model or "default") + (f" · {effort}" if effort else "")


def model_args(agent: str | None, model: str | None, effort: str | None) -> list[str]:
    """The model/effort part of the agent command line."""
    if agent == "antigravity":  # the effort is part of the model id; `--effort` is not passed
        return ["--model", model or "gemini-3.8-flash-low"]
    if agent == "codex":
        args = ["-m", model] if model and bt_agents.provider_of_model(model) != "claude" else []
        return args + (["-c", f'model_reasoning_effort="{effort}"'] if effort else [])
    return ["--model", model or LADDER[0]] + (["--effort", effort] if effort else [])


def args_text(args: list[str]) -> str:
    """model_args quoted for a shell command line (the --agent-cmd {model_args} placeholder)."""
    return subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)


def _by_tier(table, tier: int, default: dict):
    for source in (table if isinstance(table, dict) else None, default):
        if source and str(tier) in source:
            return source[str(tier)]
    return None


def session_timeout_min(limits: dict, tier: int) -> float:
    """Timeout of a single-task session at `tier`: the tier's budget capped by the run's `session_timeout_min`."""
    cap = float(limits.get("session_timeout_min") or 60)
    budget = (limits.get("session_timeout_by_tier") or {}).get(str(tier))
    return min(cap, float(budget)) if budget else cap


def group_max(limits: dict, tier: int) -> int:
    """Most tasks one session takes at `tier` (limits.group_max, then config routing.group_max, then GROUP_MAX)."""
    configured = bt_agents._config("routing.group_max", {})
    value = _by_tier(limits.get("group_max"), tier, configured if isinstance(configured, dict) else {})
    try:
        return max(1, int(value if value is not None else GROUP_MAX[str(min(max(tier, 0), TOP))]))
    except (TypeError, ValueError):
        return 1
