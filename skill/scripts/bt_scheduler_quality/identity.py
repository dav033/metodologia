"""Stable identities for M6 results and delivery attempts."""

from __future__ import annotations

import hashlib

from .contracts import QualityError, VerifyRequest


def verdict_id(
    order: VerifyRequest, result_hash: str, *, resolution_id: str = ""
) -> str:
    if not _sha256(result_hash) or (resolution_id and not _sha256(resolution_id)):
        raise QualityError(
            "RESULT_INVALID", "verdict identity requires valid content hashes"
        )
    material = f"m6.verdict/1\0{order.idempotency_key}\0{result_hash}\0{resolution_id}".encode()
    return "m6v-" + hashlib.sha256(material).hexdigest()


def criteria_hash(criteria: tuple[str, ...]) -> str:
    import json

    payload = json.dumps(
        list(criteria), ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def checks_hash(order: VerifyRequest) -> str:
    import json

    payload = json.dumps(
        [item.to_dict() for item in order.verification],
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha256(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )
