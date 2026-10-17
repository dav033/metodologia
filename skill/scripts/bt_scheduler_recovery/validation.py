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
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", value) is not None)


def digest(value: object) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None)


def snapshot(value: object) -> None:
    require(isinstance(value, str) and re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", value) is not None)


def reference(value: object) -> None:
    require(isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", value) is not None)


def refs(value: object) -> None:
    require(type(value) is tuple and len(value) <= 32)
    for item in value:
        reference(item)
    require(len(set(value)) == len(value))


def enum(value: object, choices: tuple[str, ...]) -> None:
    require(type(value) is str and value in choices)


def decode(cls: type, raw: object, schema: str | None = None) -> dict:
    require(type(raw) is dict)
    data = dict(raw)
    if schema:
        require(data.pop("schema_version", None) == schema, "SCHEMA_MISMATCH")
    require(not (data.keys() - {f.name for f in fields(cls)}), "UNKNOWN_FIELD")
    if "evidence_refs" in data:
        require(type(data["evidence_refs"]) is list)
        data["evidence_refs"] = tuple(data["evidence_refs"])
    return data
