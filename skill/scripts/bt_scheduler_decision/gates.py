"""Shared deterministic predicates for production decisions and offline evaluation."""
from __future__ import annotations

import math
from collections.abc import Mapping


def classifications_are_ambiguous(classifications: Mapping[str, object]) -> bool:
    """Share the planner classification threshold with offline selection evaluation."""
    required = {"complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence"}
    if not required.issubset(classifications) or classifications.get("confidence") == "low":
        return False
    return bool(
        classifications.get("complexity") in {"medium", "high", "extreme"} or
        classifications.get("scope") in {"large_change", "full_feature", "full_system"} or
        classifications.get("risk") in {"medium", "high"} or
        classifications.get("coupling") in {"medium", "high"}
    )


def decision_facts_are_ambiguous(classifications: Mapping[str, object], *, evidence_complete: bool,
                                 dependency_count: int, has_shared_resources: bool) -> bool:
    """Apply production's full ambiguity gate to planner or frozen benchmark facts."""
    required = {"complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence"}
    if not evidence_complete or not required.issubset(classifications) or \
            classifications.get("confidence") == "low":
        return False
    return classifications_are_ambiguous(classifications) or dependency_count > 1 or has_shared_resources


def laya_choice_passes_runtime_gate(*, quality_authorized: bool, task_ambiguous: bool,
                                    candidate_eligible: bool, answer_confidence: object,
                                    cutoff: float | None) -> bool:
    """Shared production/benchmark acceptance predicate for a local model choice."""
    try:
        confidence = float(answer_confidence)
        threshold = float(cutoff) if cutoff is not None else math.nan
    except (TypeError, ValueError, OverflowError):
        return False
    return quality_authorized is True and task_ambiguous is True and candidate_eligible is True and \
        isinstance(answer_confidence, (int, float)) and not isinstance(answer_confidence, bool) and \
        math.isfinite(confidence) and 0 <= confidence <= 1 and math.isfinite(threshold) and \
        0 <= threshold <= 1 and confidence >= threshold
