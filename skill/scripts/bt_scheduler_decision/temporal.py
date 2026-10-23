"""Prequential history evaluation using only outcome facts available by each cutoff."""
from __future__ import annotations

import datetime as dt
import math
import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .contracts import API_VERSION
from .history import (
    MAX_PERFORMANCE_CONTEXTS,
    PerformanceContext,
    aggregate_performance_history,
)
from .identity import sha256_json
from .performance_events import (
    MAX_PERFORMANCE_EVENTS,
    PerformanceEvent,
    reduce_performance_events,
)

MAX_TEMPORAL_CUTOFFS = 256
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ATTEMPT_KEY = tuple[str, int, str, str]


class TemporalEvaluationError(ValueError):
    """Stable temporal-evaluation input error without external data values."""

    code = "temporal_evaluation_invalid"

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"{self.code}:{reason}")


@dataclass(frozen=True)
class TemporalEvaluation:
    """Historical ranking feature and later observed outcomes, reported as separate descriptive facts."""

    schema_version: str
    route_id: str
    cutoff_epoch: float
    source_fingerprint: str
    selected_level: str
    training_route_attempts: int
    training_route_verified_samples: int
    history_feature_samples: int
    history_ranking_feature: float | None
    evaluation_attempts: int
    evaluation_verified_samples: int
    evaluation_successes: int
    evaluation_failures: int
    evaluation_nonquality: int
    evaluation_coverage: float | None
    evaluation_observed_rate: float | None
    evaluation_uncertainty_interval_95: tuple[float, float] | None
    history_feature_coverage: float | None
    untimed_attempts: int

    @property
    def is_future_success_probability(self) -> bool:
        return False

    def to_dict(self) -> dict[str, object]:
        interval = list(self.evaluation_uncertainty_interval_95) \
            if self.evaluation_uncertainty_interval_95 is not None else None
        return {
            "schema_version": self.schema_version,
            "route_id": self.route_id,
            "cutoff_epoch": self.cutoff_epoch,
            "source_fingerprint": self.source_fingerprint,
            "selected_level": self.selected_level,
            "training_route_attempts": self.training_route_attempts,
            "training_route_verified_samples": self.training_route_verified_samples,
            "history_feature_samples": self.history_feature_samples,
            "history_ranking_feature": self.history_ranking_feature,
            "evaluation_attempts": self.evaluation_attempts,
            "evaluation_verified_samples": self.evaluation_verified_samples,
            "evaluation_successes": self.evaluation_successes,
            "evaluation_failures": self.evaluation_failures,
            "evaluation_nonquality": self.evaluation_nonquality,
            "evaluation_coverage": self.evaluation_coverage,
            "evaluation_observed_rate": self.evaluation_observed_rate,
            "evaluation_uncertainty_interval_95": interval,
            "history_feature_coverage": self.history_feature_coverage,
            "untimed_attempts": self.untimed_attempts,
            "is_future_success_probability": False,
        }


def _valid_epoch(value: object) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _timestamp(value: str) -> float | None:
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(dt.UTC).timestamp()


def _attempt_key(event: PerformanceEvent) -> _ATTEMPT_KEY:
    return event.plan_id, event.revision, event.task_id, event.attempt_id


def _context_hashes(events: Sequence[PerformanceEvent],
                    contexts: Mapping[tuple[str, int, str], PerformanceContext]) -> list[str]:
    hashes = []
    identities = sorted({(event.plan_id, event.revision, event.task_id) for event in events})
    for identity in identities:
        context = contexts.get(identity)
        if context is None:
            continue
        normalized_identity = (identity[0], identity[1], identity[2])
        hashes.append(sha256_json({"identity": normalized_identity, "context": context.to_dict()}))
    return sorted(hashes)


def _selected_measurement(assessment, level: str):
    selected = "route" if level == "baseline" else level
    return next(item for item in assessment.measurements if item.level == selected)


def evaluate_prequential_history(
    events: Sequence[PerformanceEvent],
    contexts: Mapping[tuple[str, int, str], PerformanceContext],
    *,
    route_id: str,
    target_context: PerformanceContext,
    cutoffs: Sequence[float],
) -> tuple[TemporalEvaluation, ...]:
    """Rebuild past-only features and compare them with attempts first observed strictly after each cutoff."""
    if not isinstance(route_id, str) or not _SHA256.fullmatch(route_id):
        raise TemporalEvaluationError("route_id_invalid")
    if isinstance(events, (str, bytes)) or not isinstance(events, Sequence) or len(events) > MAX_PERFORMANCE_EVENTS:
        raise TemporalEvaluationError("events_invalid")
    if not isinstance(contexts, Mapping) or len(contexts) > MAX_PERFORMANCE_CONTEXTS:
        raise TemporalEvaluationError("contexts_invalid")
    if isinstance(cutoffs, (str, bytes)) or not isinstance(cutoffs, Sequence) or \
            len(cutoffs) > MAX_TEMPORAL_CUTOFFS or any(not _valid_epoch(value) for value in cutoffs):
        raise TemporalEvaluationError("cutoffs_invalid")
    cutoff_values = tuple(float(value) for value in cutoffs)
    if cutoff_values != tuple(sorted(set(cutoff_values))):
        raise TemporalEvaluationError("cutoffs_not_unique_and_sorted")

    try:
        checked_events = tuple(PerformanceEvent.from_dict(event.to_dict()) for event in events)
        context_snapshot = dict(contexts)
        target = PerformanceContext.from_dict(target_context.to_dict())
        aggregate_performance_history((), context_snapshot, route_id=route_id, target_context=target)
        normalized_contexts = {}
        for key, context in context_snapshot.items():
            normalized_key = (unicodedata.normalize("NFC", key[0].strip()), key[1],
                              unicodedata.normalize("NFC", key[2].strip()))
            normalized_contexts[normalized_key] = PerformanceContext.from_dict(context.to_dict())
        context_snapshot = normalized_contexts
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise TemporalEvaluationError("source_invalid") from exc

    source_events: list[tuple[float | None, PerformanceEvent]] = []
    for event in checked_events:
        timestamp = _timestamp(event.applied_at) \
            if event.application_status == "applied" and event.applied_at is not None else None
        source_events.append((timestamp, event))

    evaluations = []
    for cutoff in cutoff_values:
        known_raw = [event for timestamp, event in source_events if timestamp is not None and timestamp <= cutoff]
        future_raw = [event for timestamp, event in source_events if timestamp is not None and timestamp > cutoff]
        known_sources = reduce_performance_events(known_raw)
        future_sources = reduce_performance_events(future_raw)
        known_attempts = {_attempt_key(event) for event in known_sources}
        future_attempts = {_attempt_key(event) for event in future_sources}
        training = tuple(event for event in known_sources if event.route_id == route_id)
        future = tuple(event for event in future_sources
                       if event.route_id == route_id and _attempt_key(event) not in known_attempts)
        untimed_attempts = {
            _attempt_key(event) for timestamp, event in source_events
            if event.route_id == route_id and timestamp is None and
            _attempt_key(event) not in known_attempts and
            _attempt_key(event) not in future_attempts
        }

        historical = aggregate_performance_history(
            training, context_snapshot, route_id=route_id, target_context=target,
        )
        future_assessment = aggregate_performance_history(
            future, context_snapshot, route_id=route_id, target_context=target,
        )
        history_measurement = _selected_measurement(historical, historical.selected_level)
        future_measurement = _selected_measurement(future_assessment, historical.selected_level)
        training_route = next(item for item in historical.measurements if item.level == "route")
        source_fingerprint = sha256_json({
            "schema_version": API_VERSION,
            "evaluation_policy": "prequential-v1",
            "cutoff_epoch": cutoff,
            "route_id": route_id,
            "target_context": target.to_dict(),
            "source_event_hashes": sorted(sha256_json(event.to_dict()) for event in known_sources),
            "source_context_hashes": _context_hashes(known_sources, context_snapshot),
            "historical_assessment": historical.to_dict(),
        })
        evaluations.append(TemporalEvaluation(
            API_VERSION, route_id, cutoff, source_fingerprint, historical.selected_level,
            training_route.attempt_count, training_route.verified_samples,
            history_measurement.verified_samples if historical.selected_level != "baseline" else 0,
            historical.selected_shrunk_feature, future_measurement.attempt_count,
            future_measurement.verified_samples, future_measurement.verified_successes,
            future_measurement.verified_failures,
            future_measurement.attempt_count - future_measurement.verified_samples,
            future_measurement.coverage, future_measurement.observed_rate,
            future_measurement.uncertainty_interval_95,
            (1.0 if historical.selected_shrunk_feature is not None else 0.0)
            if future_measurement.attempt_count else None,
            len(untimed_attempts),
        ))
    return tuple(evaluations)
