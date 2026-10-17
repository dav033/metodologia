"""Small validation helpers shared by the bounded batch planner boundary."""
from __future__ import annotations

from collections.abc import Mapping

from .contracts import DecisionInputError


def validate_baseline_overrides(raw: object, task_ids: set[str], maximum: int) -> dict[str, bool]:
    baseline = raw if raw is not None else {}
    if not isinstance(baseline, Mapping) or len(baseline) > maximum or any(
            not isinstance(task_id, str) or task_id not in task_ids or not isinstance(value, bool)
            for task_id, value in baseline.items()):
        raise DecisionInputError(("batch.baseline_identity",))
    return dict(baseline)
