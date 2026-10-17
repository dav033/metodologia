"""Legacy supervisor bridge to the Planner's installed consumer compatibility gate."""
from __future__ import annotations

from pathlib import Path

import bt_scheduler_adapter
import bt_scheduler_plan_compat


def validate_run_plan(rdir: Path, state: dict | None) -> None:
    problem = bt_scheduler_plan_compat.run_gate(
        rdir, state, bt_scheduler_adapter.plan_compatibility_report
    )
    if problem:
        raise SystemExit(problem)
