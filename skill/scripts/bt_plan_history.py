"""Conservative, route-agnostic history projection for Planner instructions."""
from __future__ import annotations

from collections.abc import Mapping

import bt_agents
from bt_scheduler_decision.contracts import (
    COMPLEXITY_VALUES,
    LEVEL_VALUES,
    SCOPE_VALUES,
)

SCHEMA_VERSION = "1.0.0"
CONTEXT_FIELDS = ("complexity", "scope", "risk", "coupling")
TASK_KINDS = bt_agents.KINDS
CONTEXT_VALUES = {
    "complexity": COMPLEXITY_VALUES,
    "scope": SCOPE_VALUES,
    "risk": LEVEL_VALUES,
    "coupling": LEVEL_VALUES,
}


class PlanningHistoryInputError(ValueError):
    """Stable input error that does not echo caller-provided values."""


def _context_value(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value not in CONTEXT_VALUES[field]:
        raise PlanningHistoryInputError(f"history_context_invalid:{field}")
    return value


def _unknown_metric(reason: str, fields: Mapping[str, object]) -> dict[str, object]:
    return {
        **fields,
        "source_quality": "unknown",
        "comparability_key": None,
        "status": "unknown",
        "reason": reason,
    }


def project_history(kind: object, context: object = None) -> dict[str, object]:
    """Return only measurements supported by a public cross-route comparable history source.

    Current M2 quality evidence is route-scoped, attempt telemetry is not correlated to applied M6
    outcomes, and token conventions differ between providers. Keep every metric unknown until an
    audited source can support the requested bucket without exposing route details.
    """
    if not isinstance(kind, str) or kind not in TASK_KINDS:
        raise PlanningHistoryInputError("history_kind_invalid")
    if context is None:
        context = {}
    if not isinstance(context, Mapping) or any(not isinstance(key, str) for key in context):
        raise PlanningHistoryInputError("history_context_invalid")
    if set(context) - set(CONTEXT_FIELDS):
        raise PlanningHistoryInputError("history_context_invalid:field")
    normalized_context = {field: _context_value(context.get(field), field) for field in CONTEXT_FIELDS}

    metrics = {
        "quality": _unknown_metric(
            "correlated_cross_route_m6_quality_unavailable",
            {"samples": None, "successes": None, "failures": None, "observed_rate": None,
             "uncertainty_interval_95": None},
        ),
        "duration": _unknown_metric(
            "cross_route_duration_comparability_unproven",
            {"samples": None, "unit": "seconds", "median": None, "range": None},
        ),
        "retries": _unknown_metric(
            "correlated_retry_identity_unavailable",
            {"samples": None, "count": None},
        ),
        "consumption": _unknown_metric(
            "cross_provider_token_units_not_comparable",
            {"samples": None, "unit": None, "median": None, "range": None, "coverage": None},
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "context": normalized_context,
        "status": "unknown",
        "metrics": metrics,
    }
