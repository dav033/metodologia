"""Auditable decision orchestration over deterministic eligibility and an optional local chooser."""
from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .contracts import (
    API_VERSION,
    Candidate,
    Confidence,
    DecisionRecord,
    DecisionRequest,
    LayaChoice,
    RouteSummary,
    ValidatedRequest,
)
from .gates import (
    decision_facts_are_ambiguous,
    laya_choice_passes_runtime_gate,
)
from .policy import CandidateRanking, rank_candidates
from .quality_evidence import load_quality_evidence
from .recorder import DecisionLedger, decision_id_for, idempotency_key
from .validation import validate_request

MAX_LAYA_CANDIDATES = 8
class Chooser(Protocol):
    def choose(self, request: DecisionRequest, candidates: tuple[Candidate, ...]) -> LayaChoice: ...


class QualityAuthorizer(Protocol):
    enabled: bool
    answer_confidence_cutoff: float | None
    calibration_version: str | None

    def authorizes(self, checkpoint_revision: str) -> bool: ...


@dataclass(frozen=True, init=False)
class QualityGate:
    enabled: bool
    answer_confidence_cutoff: float | None
    calibration_version: str | None
    checkpoint_revision: str | None
    evidence_sha256: str | None

    def __init__(self) -> None:
        object.__setattr__(self, "enabled", False)
        object.__setattr__(self, "answer_confidence_cutoff", None)
        object.__setattr__(self, "calibration_version", None)
        object.__setattr__(self, "checkpoint_revision", None)
        object.__setattr__(self, "evidence_sha256", None)

    @classmethod
    def from_artifacts(cls, calibration_path: str | Path,
                       calibration_results_path: str | Path, held_out_path: str | Path,
                       corpus_path: str | Path, manifest_path: str | Path) -> QualityGate:
        evidence = load_quality_evidence(calibration_path, calibration_results_path, held_out_path,
                                         corpus_path, manifest_path)
        gate = object.__new__(cls)
        object.__setattr__(gate, "enabled", True)
        object.__setattr__(gate, "answer_confidence_cutoff", evidence.confidence_cutoff)
        object.__setattr__(gate, "calibration_version", evidence.calibration_version)
        object.__setattr__(gate, "checkpoint_revision", evidence.checkpoint_revision)
        object.__setattr__(gate, "evidence_sha256", evidence.artifacts_sha256)
        return gate

    def authorizes(self, checkpoint_revision: str) -> bool:
        return self.enabled and checkpoint_revision == self.checkpoint_revision and \
            isinstance(self.evidence_sha256, str) and len(self.evidence_sha256) == 64


class ChooserFailure(RuntimeError):
    """Bounded local-worker failure represented by a stable M2 fallback reason."""

    def __init__(self, reason: str):
        if reason not in {"laya_unavailable", "laya_timeout", "laya_runtime_error", "laya_circuit_open"}:
            raise ValueError("unsupported chooser failure reason")
        self.reason = reason
        super().__init__(reason)


def task_is_ambiguous(validated: ValidatedRequest) -> bool:
    """Use only complete, cited planner facts; incomplete evidence takes the deterministic path."""
    task = validated.request.task
    classifications = task.classifications
    evidence = task.classification_evidence
    if validated.classification_warnings or any(
            classifications.get(key) is None for key in
            ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence")):
        return False
    if set(evidence) != {"complexity", "scope", "duration", "risk", "coupling", "confidence"}:
        return False
    if any(not isinstance(evidence.get(key), Mapping) or evidence[key].get("valid") is not True
           for key in evidence):
        return False
    return decision_facts_are_ambiguous(classifications, evidence_complete=True,
                                        dependency_count=len(task.dependencies),
                                        has_shared_resources=bool(task.shared_resources))


def _summary(candidate: Candidate, factors: tuple[str, ...] = ()) -> RouteSummary:
    return RouteSummary(candidate.route_id, candidate.provider, candidate.model, candidate.profile,
                        candidate.account_ref, candidate.effort, candidate.baseline_rank, factors)


def _history_factors(candidate: Candidate) -> set[str]:
    history = candidate.history
    factors = {"verified_history" if history.verified_successes + history.verified_failures >= 5 else
               "history_sparse" if history.verified_successes + history.verified_failures else
               "history_no_verified_samples"}
    if history.duration_samples:
        factors.add("duration_measured")
    if history.token_samples:
        factors.add("tokens_measured")
    return factors


class DecisionEngine:
    """Persist M2 recommendations; M1 remains the sole authority to accept and reserve them."""

    def __init__(self, ledger: DecisionLedger, *, chooser: Chooser | None = None,
                 quality_gate: QualityAuthorizer | None = None):
        self.ledger = ledger
        self.chooser = chooser
        self.quality_gate = quality_gate if quality_gate is not None else QualityGate()

    def decide(self, request: object) -> DecisionRecord:
        if not isinstance(request, DecisionRequest):
            raise TypeError("request must be a DecisionRequest")
        validated = validate_request(request)
        replay = self.ledger.lookup(request)
        if replay is not None:
            return replay

        ranking = rank_candidates(validated)
        if ranking.selected is None:
            return self._persist(request, validated, ranking, None, "deterministic", None,
                                 Confidence(None, "none", "none"), {"no_eligible_candidate"})

        factors: set[str] = {"estimated_duration"} if \
            validated.request.task.classifications.get("estimated_minutes") is not None else set()
        ambiguous = task_is_ambiguous(validated)
        factors.add("task_ambiguous" if ambiguous else "task_unambiguous")
        if not ambiguous:
            if validated.classification_warnings or set(validated.request.task.classification_evidence) != \
                    {"complexity", "scope", "duration", "risk", "coupling", "confidence"}:
                factors.add("classification_incomplete")
            factors.update(_history_factors(ranking.selected))
            factors.add("baseline_route")
            return self._persist(request, validated, ranking, ranking.selected, "deterministic", None,
                                 Confidence(None, "none", "none"), factors)

        if len(ranking.eligible) < 2:
            factors.update(_history_factors(ranking.selected))
            factors.update(("candidate_set_small", "baseline_route"))
            return self._persist(request, validated, ranking, ranking.selected, "deterministic", None,
                                 Confidence(None, "none", "none"), factors)
        if len(ranking.eligible) > MAX_LAYA_CANDIDATES:
            factors.update(_history_factors(ranking.selected))
            factors.add("candidate_set_large")
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback",
                                 "candidate_limit_exceeded", Confidence(None, "none", "none"), factors)
        if not self.quality_gate.authorizes(validated.request.checkpoint_revision):
            factors.update(_history_factors(ranking.selected))
            factors.add("baseline_route")
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback",
                                 "laya_quality_gate_disabled", Confidence(None, "none", "none"), factors)
        if self.chooser is None:
            factors.update(_history_factors(ranking.selected))
            factors.add("baseline_route")
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback", "laya_unavailable",
                                 Confidence(None, "none", "none"), factors)

        try:
            choice = self.chooser.choose(validated.request, ranking.eligible)
        except ChooserFailure as exc:
            factors.update(_history_factors(ranking.selected))
            factors.update(("laya_fallback", "baseline_route"))
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback", exc.reason,
                                 Confidence(None, "none", "none"), factors)
        except Exception:  # noqa: BLE001 - unexpected chooser failures must persist the deterministic fallback.
            factors.update(_history_factors(ranking.selected))
            factors.update(("laya_fallback", "baseline_route"))
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback",
                                 "laya_runtime_error", Confidence(None, "none", "none"), factors)

        eligible_by_id = {item.route_id: item for item in ranking.eligible}
        if not isinstance(choice, LayaChoice) or choice.route_id not in eligible_by_id or \
                choice.checkpoint_revision != validated.request.checkpoint_revision or \
                not isinstance(choice.answer_confidence, (int, float)) or \
                isinstance(choice.answer_confidence, bool) or not math.isfinite(choice.answer_confidence) or \
                not 0 <= choice.answer_confidence <= 1:
            factors.update(_history_factors(ranking.selected))
            factors.update(("laya_invalid_choice", "laya_fallback", "baseline_route"))
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback",
                                 "laya_invalid_output", Confidence(None, "none", "none"), factors)
        cutoff = self.quality_gate.answer_confidence_cutoff
        if not laya_choice_passes_runtime_gate(
                quality_authorized=self.quality_gate.authorizes(validated.request.checkpoint_revision),
                task_ambiguous=ambiguous, candidate_eligible=choice.route_id in eligible_by_id,
                answer_confidence=choice.answer_confidence, cutoff=cutoff):
            factors.update(_history_factors(ranking.selected))
            factors.update(("laya_score_below_cutoff", "laya_fallback", "baseline_route"))
            return self._persist(request, validated, ranking, ranking.selected, "deterministic_fallback",
                                 "laya_low_confidence", Confidence(None, "none", "none"), factors)

        selected = eligible_by_id[choice.route_id]
        factors.update(_history_factors(selected))
        factors.add("laya_choice_accepted")
        if selected.quota_used_percent is not None:
            factors.add("resource_pressure" if selected.quota_used_percent >= 80 else "quota_headroom")
        confidence = Confidence(float(choice.answer_confidence), "laya_answer_confidence",
                                "laya_calibrated_choice_score", self.quality_gate.calibration_version, cutoff)
        return self._persist(request, validated, ranking, selected, "laya", None, confidence, factors)

    def _persist(self, original_request: DecisionRequest, validated: ValidatedRequest,
                 ranking: CandidateRanking, selected: Candidate | None,
                 method: str, fallback_reason: str | None, confidence: Confidence,
                 factor_codes: set[str]) -> DecisionRecord:
        request = validated.request
        factors = tuple(sorted(factor_codes))
        key = idempotency_key(original_request)
        record = DecisionRecord(
            API_VERSION, decision_id_for(key), key, None, request.plan_id, request.revision, request.plan_sha256,
            request.task.task_id, request.requested_at,
            "recommended" if selected is not None else "no_eligible_candidate",
            _summary(selected, factors) if selected else None,
            tuple(_summary(item) for item in ranking.eligible if selected is None or item.route_id != selected.route_id),
            ranking.exclusions,
            ranking.selected.route_id if ranking.selected else None,
            method, fallback_reason, request.policy_version, request.checkpoint_revision,
            validated.candidate_snapshot_sha256, validated.quota_snapshot_sha256, confidence, factors, ";".join(factors),
        )
        return self.ledger.persist(original_request, record)
