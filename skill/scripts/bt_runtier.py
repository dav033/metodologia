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
TARGETS = {"sonnet": 1, "opus": 2, "standard": 1, "top": 2}  # `task escalate --to`


def start_tier(level: str | None, kind: str | None = None, complexity: str | None = None) -> int:
    """`level: architecture` on the PLAN task line starts the task at the top of the ladder; an audit and a task
    declared `complexity: L` start at 1."""
    return bt_agents.start_tier(level, kind, complexity)


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
