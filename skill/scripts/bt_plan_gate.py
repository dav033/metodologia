"""A planning session is not finished while the plan it wrote cannot pass `plan-json check`.

An agent that writes PLAN.md and stops at the PLAN.json skeleton hands the owner a plan with no classification: no
difficulty, no evidence, nothing M2 can route. The Stop hook asks this module which requirements the ending session
planned (`bt_presence`); each one still being drafted whose PLAN.json is missing or invalid keeps the session from
ending, with the exact next step. Bounded: a session is held at most MAX_HOLDS times per requirement, so a plan the agent
truly cannot fix never traps it.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import bt_presence
from bt_core import SCRIPT, find_req, req_id

MAX_HOLDS = 3
OPEN_STATUSES = ("draft", "review", "")          # an approved, launched or finished plan is not being drafted any more


def _status(plan: Path) -> str:
    found = re.search(r"^status:\s*([\w-]+)", plan.read_text(encoding="utf-8", errors="replace")[:2000], re.M)
    return found.group(1).lower() if found else ""


def _holds(root: Path, sid: str) -> dict[str, int]:
    try:
        data = json.loads((root / ".state" / "presence" / f"{sid}.gate.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: v for k, v in data.items() if isinstance(v, int)} if isinstance(data, dict) else {}


def _save_holds(root: Path, sid: str, holds: dict[str, int]) -> None:
    path = root / ".state" / "presence" / f"{sid}.gate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(holds), encoding="utf-8")


def problem(project: str, rdir: Path) -> str | None:
    """Why this requirement's plan is not ready to hand over, or None when it is (or is not a plan in progress)."""
    plan = rdir / "PLAN.md"
    if not plan.exists() or _status(plan) not in OPEN_STATUSES:
        return None
    rid = req_id(rdir)
    if not (rdir / "PLAN.json").exists():
        return f"{rid} has a PLAN.md but no PLAN.json (no classification)"
    check = subprocess.run([sys.executable, str(SCRIPT), "--project", project, "plan-json", "check", rid],
                           capture_output=True, text=True, timeout=12)
    if check.returncode == 0:
        return None
    last = (check.stdout.strip().splitlines() or ["invalid"])[-1]
    return f"{rid}: plan-json check fails ({last})"


def hold_reason(root: Path, project: str, sid: str) -> str | None:
    """The Stop-hook text when this session must keep working on a plan, else None. Counts each hold."""
    holds = _holds(root, sid)
    found = []
    for entry in bt_presence.planned_reqs(root, sid):
        owner, _, req = entry.rpartition(":")      # "project:REQ-001"; a bare REQ belongs to the session's project
        owner = owner or project
        try:
            rdir = find_req(root / owner, req)
            why = problem(owner, rdir)
        except (SystemExit, OSError, subprocess.SubprocessError):
            continue
        if why and holds.get(entry, 0) < MAX_HOLDS:
            holds[entry] = holds.get(entry, 0) + 1
            found.append((req, why, owner))
    if not found:
        return None
    _save_holds(root, sid, holds)
    lines = "\n".join(f"- {why}" for _, why, _ in found)
    first, project = found[0][0], found[0][2]
    return ("[bitácora] The plan you wrote is not finished: it cannot be handed over without its classification "
            f"(difficulty, scope, risk, coupling, confidence, estimate, each with evidence).\n{lines}\n"
            f"Fill PLAN.json for every task (rubric: skill/scripts/bt_planner/README.md), then run "
            f"`bitacora.py --project {project} plan-json check {first}` until it passes. Or let the Planner agent do it: "
            f"`bitacora.py --project {project} go {first} --dry-run`. Do not tell the owner the plan is ready before "
            "`check` passes.")
