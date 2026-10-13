"""Marathon escalation ladder: which model and effort a task's session runs with.

Tier 0 is the run's configured model at the CLI's default effort (haiku unless --model says otherwise); every failed
attempt moves the task one tier up: 1 = sonnet --effort xhigh, 2 = opus --effort xhigh (the top). A configured model
already stronger than the tier's is kept, only the effort rises. Codex keeps its model and raises
model_reasoning_effort to xhigh from tier 1 up. Rules: references/marathon.md, "Escalation ladder".
"""
from __future__ import annotations

import os
import shlex
import subprocess

TOP = 2
LADDER = ("haiku", "sonnet", "opus")
EFFORT = "xhigh"
TARGETS = {"sonnet": 1, "opus": 2}  # `task escalate --to`


def start_tier(level: str | None) -> int:
    """`level: architecture` on the PLAN task line starts the task at the top of the ladder."""
    return TOP if (level or "").strip().lower() == "architecture" else 0


def tier_of(task: dict | None) -> int:
    try:
        return max(0, min(TOP, int((task or {}).get("tier") or 0)))
    except (TypeError, ValueError):
        return 0


def _rank(model: str | None) -> int:
    name = (model or "").lower()
    return 2 if "opus" in name else 1 if "sonnet" in name else 0


def model_for(state: dict, tier: int) -> tuple[str | None, str | None]:
    """(model, effort) of a session at this tier; effort None means the CLI default."""
    configured = state.get("model")
    if state.get("agent") in ("codex", "antigravity"):
        return configured, EFFORT if tier >= 1 else None
    if tier <= 0:
        return configured or LADDER[0], None
    tier = min(tier, TOP)
    return (configured if _rank(configured) >= tier else LADDER[tier]), EFFORT


def label(model: str | None, effort: str | None) -> str:
    return (model or "default") + (f" · {effort}" if effort else "")


def model_args(agent: str | None, model: str | None, effort: str | None) -> list[str]:
    """The model/effort part of the agent command line."""
    if agent == "antigravity":  # `agy models` ids; the ladder's claude names mean "use the CLI default"
        args = ["--model", model] if model and model not in LADDER else []
        return args + (["--effort", effort] if effort else [])
    if agent == "codex":
        args = ["-m", model] if model and model != "haiku" else []
        return args + (["-c", f'model_reasoning_effort="{effort}"'] if effort else [])
    return ["--model", model or LADDER[0]] + (["--effort", effort] if effort else [])


def args_text(args: list[str]) -> str:
    """model_args quoted for a shell command line (the --agent-cmd {model_args} placeholder)."""
    return subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)
