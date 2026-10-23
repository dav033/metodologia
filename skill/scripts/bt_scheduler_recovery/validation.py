"""Closed, bounded wire validation. Errors never echo untrusted input."""
from __future__ import annotations

import math
import re
from dataclasses import fields


class RecoveryError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str = "INVALID_INPUT") -> None:
    if not condition:
        raise RecoveryError(code)


def integer(value: object, low: int = 0, high: int = 1_000_000) -> None:
    require(type(value) is int and low <= value <= high)


def number(value: object, low: float = 0, high: float = 1e12) -> None:
    require(type(value) in (int, float) and low <= value <= high and math.isfinite(value))


def identifier(value: object) -> None:
    require(type(value) is str and len(value) <= 128
            and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is not None)


def digest(value: object) -> None:
    require(type(value) is str and len(value) == 64 and re.fullmatch(r"[a-f0-9]{64}", value) is not None)


def snapshot(value: object) -> None:
    require(type(value) is str and len(value) in (40, 64)
            and re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", value) is not None)


def reference(value: object) -> None:
    require(type(value) is str and 66 <= len(value) <= 97
            and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", value) is not None)


def refs(value: object) -> None:
    require(type(value) is tuple and len(value) <= 32)
    for item in value:
        reference(item)
    require(len(set(value)) == len(value))


def enum(value: object, choices: tuple[str, ...]) -> None:
    require(type(value) is str and len(value) <= max(map(len, choices)) and value in choices)


def decode(cls: type, raw: object, schema: str | None = None) -> dict:
    require(type(raw) is dict)
    allowed = {f.name for f in fields(cls)}
    allowed_count = len(allowed) + (1 if schema else 0)
    require(len(raw) <= allowed_count)
    for key in raw:
        require(type(key) is str and len(key) <= 64)
        require(key in allowed or (schema is not None and key == "schema_version"), "UNKNOWN_FIELD")
    data = dict(raw)
    if schema:
        require(data.pop("schema_version", None) == schema, "SCHEMA_MISMATCH")
    if "evidence_refs" in data:
        require(type(data["evidence_refs"]) is list)
        require(len(data["evidence_refs"]) <= 32)
        data["evidence_refs"] = tuple(data["evidence_refs"])
    return data
