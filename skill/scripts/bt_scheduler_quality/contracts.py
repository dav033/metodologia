"""Versioned, runtime-validated contracts owned by M6."""

from __future__ import annotations

import hashlib
import json
import re
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
OPTIONAL_ORDER_KEYS = frozenset({"composition_id", "manifest_sha256", "contract_identities", "environment_fingerprint"})
PLAN_SCHEMA_CAPABILITIES = frozenset({"1.0.0", "1.1.0", "1.2.0", "1.3.0"})
VERIFICATION_CATEGORIES = frozenset({"static", "functional", "integration", "regression", "product"})
COMMAND_KEYS = frozenset({"type", "value", "purpose", "created_by", "category", "environment", "requires", "authorization_needed"})
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
    category: str | None = None
    environment: str | None = None
    requires: tuple[str, ...] | None = None
    authorization_needed: str | None = None

    def to_dict(self) -> dict[str, object]:
        result = {"type": self.kind, "value": self.value, "purpose": self.purpose}
        if self.created_by:
            result["created_by"] = self.created_by
        if self.kind == "manual":
            result["expected"] = self.expected
        if self.category is not None:
            result["category"] = self.category
        if self.environment is not None:
            result["environment"] = self.environment
        if self.requires is not None:
            result["requires"] = list(self.requires)
        if self.authorization_needed is not None:
            result["authorization_needed"] = self.authorization_needed
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
    composition_id: str | None = None
    manifest_sha256: str | None = None
    contract_identities: tuple[tuple[str, str], ...] = ()
    environment_fingerprint: str | None = None

    @classmethod
    def from_mapping(cls, value: object) -> VerifyRequest:
        if (not isinstance(value, Mapping) or not ORDER_KEYS <= set(value)
                or set(value) - ORDER_KEYS - OPTIONAL_ORDER_KEYS):
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
        composition_id, manifest_sha256 = _parse_composition(value)
        contract_identities = _parse_contract_identities(value.get("contract_identities", {}))
        environment_fingerprint = _optional_sha256(value, "environment_fingerprint")
        request = cls(
            idempotency_key,
            plan_id,
            revision,
            task_id,
            attempt_id,
            token,
            criteria,
            checks,
            composition_id,
            manifest_sha256,
            contract_identities,
            environment_fingerprint,
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
        result = {
            "idempotency_key": self.idempotency_key,
            "plan_id": self.plan_id,
            "revision": self.revision,
            "task_id": self.task_id,
            "attempt_id": self.attempt_id,
            "token": self.token,
            "acceptance_criteria": list(self.acceptance_criteria),
            "verification": [item.to_dict() for item in self.verification],
        }
        if self.composition_id is not None:
            result.update(composition_id=self.composition_id, manifest_sha256=self.manifest_sha256)
        if self.contract_identities:
            result["contract_identities"] = dict(self.contract_identities)
        if self.environment_fingerprint is not None:
            result["environment_fingerprint"] = self.environment_fingerprint
        return result

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


def _optional_sha256(value: Mapping[str, object], name: str) -> str | None:
    if name not in value:
        return None
    digest = value[name]
    if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise QualityError("ORDER_INVALID", f"{name} must be a lowercase sha256 digest")
    return digest


def _parse_composition(value: Mapping[str, object]) -> tuple[str | None, str | None]:
    present = {name for name in ("composition_id", "manifest_sha256") if name in value}
    if not present:
        return None, None
    if present != {"composition_id", "manifest_sha256"}:
        raise QualityError("ORDER_INVALID", "composition_id and manifest_sha256 must be supplied together")
    composition_id = value["composition_id"]
    if not _is_text(composition_id, max_bytes=256):
        raise QualityError("ORDER_INVALID", "composition_id must be bounded, non-empty text")
    return composition_id, _optional_sha256(value, "manifest_sha256")


def _parse_contract_identities(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, Mapping) or len(value) > 128:
        raise QualityError("ORDER_INVALID", "contract_identities must be a bounded object")
    result = []
    for key, digest in value.items():
        if not _is_text(key, max_bytes=256) or not isinstance(digest, str) or len(digest) != 64 \
                or any(char not in "0123456789abcdef" for char in digest):
            raise QualityError("ORDER_INVALID", "contract identities require names and lowercase sha256 digests")
        result.append((key, digest))
    return tuple(sorted(result))


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
    if set(value) - allowed or not {"type", "value", "purpose"} <= set(value):
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
    category = None
    if "category" in value:
        raw_category = value["category"]
        if not isinstance(raw_category, str) or raw_category not in VERIFICATION_CATEGORIES:
            raise QualityError(
                "ORDER_INVALID", "category must be static, functional, integration, regression or product"
            )
        category = raw_category
    environment = _parse_environment(value)
    requires = _parse_requires(value["requires"]) if "requires" in value else None
    authorization = value.get("authorization_needed")
    if authorization is not None and (not _is_text(authorization) or _looks_like_secret(authorization)):
        raise QualityError("ORDER_INVALID", "authorization_needed must describe permission without secret values")
    if environment == "production" and authorization is None:
        raise QualityError("ORDER_INVALID", "production verification requires authorization_needed")
    if environment == "human_attestation" and (kind != "manual" or not expected):
        raise QualityError("ORDER_INVALID", "human_attestation requires a manual check with expected text")
    if kind == "command" and "expected" in value:
        raise QualityError(
            "ORDER_INVALID", "command verification cannot include manual expected text"
        )
    return VerificationSpec(kind, instruction, purpose, created_by, expected, category,
                            environment, requires, authorization)


def _parse_environment(value: Mapping[str, object]) -> str | None:
    if "environment" not in value:
        return None
    environment = value["environment"]
    allowed = {"sandbox", "external_authorized", "production", "human_attestation"}
    if not isinstance(environment, str) or environment not in allowed:
        raise QualityError("ORDER_INVALID", "verification environment is unsupported")
    return environment


def _parse_requires(value: object) -> tuple[str, ...]:
    items = _sequence(value, maximum=64)
    if items is None:
        raise QualityError("ORDER_INVALID", "requires must contain resource names only")
    result: list[str] = []
    for item in items:
        if not isinstance(item, str) or not re.fullmatch(r"(?:[A-Z][A-Z0-9_]{1,63}|service:[a-z0-9][a-z0-9-]{0,63})", item):
            raise QualityError("ORDER_INVALID", "requires must contain resource names only")
        result.append(item)
    if len(set(result)) != len(result):
        raise QualityError("ORDER_INVALID", "requires contains duplicate resources")
    return tuple(result)


def _looks_like_secret(value: str) -> bool:
    return bool(re.search(r"(?i)(?:https?://|postgres(?:ql)?://|token\s*[:=]|password\s*[:=]|secret\s*[:=]|api[_-]?key\s*[:=])", value)
                or re.search(r"\b\S+@\S+", value))
