"""The only place where the methodology touches the planner module (`bt_planner`).

Dependency direction: methodology -> this adapter -> bt_planner. The module knows nothing about the methodology; the
methodology-specific meaning (which PLAN.md status words mean "approved", how a requirement folder maps to a plan id,
what to do on a launch) lives here. No other file may import `bt_planner` (test_plan_integration enforces it).
"""
from __future__ import annotations

from pathlib import Path

import bt_planner as planner
from bt_planner import cli as planner_cli

# What the methodology calls an approved plan; the module itself only has a default for these words.
APPROVED_STATES = ("approved", "launched", "done", "merged")


def plan_id(rdir: Path) -> str:
    """`REQ-009-some-slug` -> `REQ-009` (the methodology's requirement id)."""
    return "-".join(Path(rdir).name.split("-")[:2])


def run_cli(action: str, rdir: Path, *, force: bool = False, as_json: bool = False, emit=print) -> int:
    """Back the `bitacora.py plan-json <action> REQ-NNN` command."""
    return planner_cli.run(action, rdir, plan_id=plan_id(rdir), force=force, as_json=as_json,
                           approved_states=APPROVED_STATES, emit=emit)


def handoff_problems(rdir: Path, limit: int = 5) -> list[str]:
    """Reasons `handoff` must refuse the plan because its (opt-in) PLAN.json is invalid; [] for legacy plans."""
    if not (Path(rdir) / planner.PLAN_JSON).exists():
        return []
    errors = planner.check(rdir, plan_id=plan_id(rdir)).errors
    out = [f"PLAN.json: {e}" for e in errors[:limit]]
    if len(errors) > limit:
        out.append(f"PLAN.json: {len(errors) - limit} more error(s); run `bitacora.py plan-json check {plan_id(rdir)}`")
    return out


def freeze_on_launch(rdir: Path) -> None:
    """Freeze the approved revision before a launch. No PLAN.json -> nothing to do. Raises SystemExit with the cause."""
    try:
        planner.freeze_if_present(rdir, plan_id(rdir), APPROVED_STATES)
    except planner.PlanContractError as exc:
        raise SystemExit(f"{exc.code}: PLAN.json cannot be frozen: " + "; ".join(exc.issues[:5]) +
                         f" (bitacora.py plan-json check {plan_id(rdir)})") from exc


def run_state_fields(rdir: Path) -> dict:
    """Fields a NEW run state records about its plan: `plan_ref`, or `plan_ref_error` when the store is damaged."""
    return planner.run_reference(rdir)
