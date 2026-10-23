"""Versioned, runtime-validated contracts owned by M6."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeGuard

ORDER_KEYS = frozenset(
    {
        "idempotency_key",
        "plan_id",
        "revision",
        "task_id",
        "attempt_id",
        "token",
        "acceptance_criteria",
        "verification",
    }
)
COMMAND_KEYS = frozenset({"type", "value", "purpose", "created_by"})
MANUAL_KEYS = COMMAND_KEYS | {"expected"}
MAX_TEXT_BYTES = 4096
MAX_CRITERIA = 64
MAX_CHECKS = 64


class QualityError(ValueError):
    """An invalid M6 contract or operation with a stable, non-secret diagnostic code."""

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail[:512]
        super().__init__(f"{code}: {self.detail}")


def _is_text(value: object, *, max_bytes: int = MAX_TEXT_BYTES) -> TypeGuard[str]:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return len(encoded) <= max_bytes and not any(
        ord(char) < 32 or ord(char) == 127 for char in value
    )


def _sequence(value: object, *, maximum: int) -> Sequence[object] | None:
    if (
        isinstance(value, (str, bytes, bytearray))
        or not isinstance(value, Sequence)
        or len(value) > maximum
    ):
        return None
    return value


def _positive_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _required_text(
    value: Mapping[str, object], name: str, *, max_bytes: int = MAX_TEXT_BYTES
) -> str:
    item = value.get(name)
    if not _is_text(item, max_bytes=max_bytes):
        raise QualityError("ORDER_INVALID", f"{name} must be bounded, non-empty text")
    return item


@dataclass(frozen=True)
class VerificationSpec:
    kind: str
    value: str
    purpose: str
    created_by: str = ""
    expected: str = ""

    def to_dict(self) -> dict[str, str]:
        result = {"type": self.kind, "value": self.value, "purpose": self.purpose}
        if self.created_by:
            result["created_by"] = self.created_by
        if self.kind == "manual":
            result["expected"] = self.expected
        return result


@dataclass(frozen=True)
class VerifyRequest:
    """Validated JSON-compatible projection of M1's immutable VerifyOrder."""

    idempotency_key: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    token: int
    acceptance_criteria: tuple[str, ...]
    verification: tuple[VerificationSpec, ...]

    @classmethod
    def from_mapping(cls, value: object) -> VerifyRequest:
        if not isinstance(value, Mapping) or set(value) != ORDER_KEYS:
            raise QualityError(
                "ORDER_INVALID", "VerifyOrder has missing or unknown fields"
            )
        idempotency_key = _required_text(value, "idempotency_key", max_bytes=512)
        plan_id = _required_text(value, "plan_id", max_bytes=256)
        task_id = _required_text(value, "task_id", max_bytes=256)
        attempt_id = _required_text(value, "attempt_id", max_bytes=256)
        revision, token = value.get("revision"), value.get("token")
        if not _positive_int(revision) or not _positive_int(token):
            raise QualityError(
                "ORDER_INVALID", "revision and token must be positive integers"
            )
        criteria = _parse_criteria(value.get("acceptance_criteria"))
        checks = _parse_verification(value.get("verification"))
        request = cls(
            idempotency_key,
            plan_id,
            revision,
            task_id,
            attempt_id,
            token,
            criteria,
            checks,
        )
        try:
            json.dumps(
                request.to_dict(), sort_keys=True, ensure_ascii=False, allow_nan=False
            )
        except (TypeError, ValueError, UnicodeEncodeError) as error:
            raise QualityError(
                "ORDER_INVALID", "VerifyOrder is not canonical JSON"
            ) from error
        return request

    def to_dict(self) -> dict[str, object]:
        return {
            "idempotency_key": self.idempotency_key,
            "plan_id": self.plan_id,
            "revision": self.revision,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "token": self.token,
            "acceptance_criteria": list(self.acceptance_criteria),
            "verification": [item.to_dict() for item in self.verification],
        }

    @property
    def input_hash(self) -> str:
        canonical = json.dumps(
            self.to_dict(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


def _parse_criteria(value: object) -> tuple[str, ...]:
    items = _sequence(value, maximum=MAX_CRITERIA)
    if items is None or not items:
        raise QualityError(
            "ORDER_INVALID", "acceptance_criteria must contain bounded text entries"
        )
    criteria_items: list[str] = []
    for item in items:
        if not _is_text(item):
            raise QualityError(
                "ORDER_INVALID", "acceptance criteria must be bounded, non-empty text"
            )
        criteria_items.append(item)
    criteria = tuple(criteria_items)
    if len(set(criteria)) != len(criteria):
        raise QualityError("ORDER_INVALID", "acceptance criteria contain duplicates")
    return criteria


def _parse_verification(value: object) -> tuple[VerificationSpec, ...]:
    items = _sequence(value, maximum=MAX_CHECKS)
    if items is None or not items:
        raise QualityError(
            "ORDER_INVALID",
            "verification must contain bounded command or manual checks",
        )
    return tuple(_parse_verification_item(item) for item in items)


def _parse_verification_item(value: object) -> VerificationSpec:
    if not isinstance(value, Mapping):
        raise QualityError("ORDER_INVALID", "verification entries must be objects")
    raw_kind = value.get("type")
    if raw_kind == "command":
        kind = "command"
        allowed = COMMAND_KEYS
    elif raw_kind == "manual":
        kind = "manual"
        allowed = MANUAL_KEYS
    else:
        raise QualityError(
            "ORDER_INVALID", "verification type must be command or manual"
        )
    if set(value) - allowed or not COMMAND_KEYS - {"created_by"} <= set(value):
        raise QualityError(
            "ORDER_INVALID", "verification entry has missing or unapproved fields"
        )
    instruction = _required_text(value, "value")
    purpose = _required_text(value, "purpose")
    raw_created_by = value.get("created_by", "")
    if not isinstance(raw_created_by, str) or (
        raw_created_by and not _is_text(raw_created_by, max_bytes=256)
    ):
        raise QualityError("ORDER_INVALID", "created_by must be bounded text")
    created_by = raw_created_by
    expected = _required_text(value, "expected") if kind == "manual" else ""
    if kind == "command" and "expected" in value:
        raise QualityError(
            "ORDER_INVALID", "command verification cannot include manual expected text"
        )
    return VerificationSpec(kind, instruction, purpose, created_by, expected)
