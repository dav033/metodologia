"""Optional independent review boundary; it is disabled unless operator policy requires it."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from .contracts import QualityError, VerifyRequest


@dataclass(frozen=True)
class ReviewerEvidence:
    reviewer_identity: str
    approved: bool
    evidence: str
    subject_hash: str

    @classmethod
    def from_value(cls, value: object) -> ReviewerEvidence:
        if isinstance(value, ReviewerEvidence):
            evidence = value.to_dict()
        elif isinstance(value, Mapping):
            evidence = value
        else:
            raise QualityError(
                "REVIEW_INVALID", "reviewer returned an invalid evidence object"
            )
        expected = {"reviewer_identity", "approved", "evidence", "subject_hash"}
        if set(evidence) != expected:
            raise QualityError(
                "REVIEW_INVALID", "reviewer evidence has missing or unknown fields"
            )
        identity, approved = evidence.get("reviewer_identity"), evidence.get("approved")
        reference, subject_hash = evidence.get("evidence"), evidence.get("subject_hash")
        if not _bounded_text(identity, 256) or not isinstance(approved, bool):
            raise QualityError(
                "REVIEW_INVALID", "reviewer identity or decision is invalid"
            )
        if not _bounded_text(reference, 2048) or not _sha256(subject_hash):
            raise QualityError(
                "REVIEW_INVALID",
                "reviewer evidence reference or subject hash is invalid",
            )
        return cls(identity, approved, reference, subject_hash)

    def to_dict(self) -> dict[str, object]:
        return {
            "reviewer_identity": self.reviewer_identity,
            "approved": self.approved,
            "evidence": self.evidence,
            "subject_hash": self.subject_hash,
        }


class ReviewerPort(Protocol):
    def review(self, order: VerifyRequest, result: Mapping[str, object]) -> object: ...


def validate_reviewer_evidence(
    value: ReviewerEvidence, order: VerifyRequest, secret_values: tuple[str, ...]
) -> ReviewerEvidence:
    evidence = ReviewerEvidence.from_value(value)
    authors = {item.created_by for item in order.verification if item.created_by}
    if evidence.reviewer_identity in authors:
        raise QualityError(
            "REVIEW_NOT_INDEPENDENT", "reviewer identity matches a command author"
        )
    if evidence.subject_hash != order.input_hash:
        raise QualityError(
            "REVIEW_INVALID", "reviewer evidence is bound to different input"
        )
    if any(secret and secret in evidence.evidence for secret in secret_values):
        raise QualityError(
            "REVIEW_INVALID", "reviewer evidence contains a configured secret"
        )
    return evidence


def _bounded_text(value: object, maximum: int) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    try:
        if len(value.encode("utf-8")) > maximum:
            return False
    except UnicodeEncodeError:
        return False
    return not any(ord(char) < 32 or ord(char) == 127 for char in value)


def _sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )
