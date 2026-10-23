"""Validation of a task's verification declarations."""
from __future__ import annotations

from . import quality


def text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check(errors: list[str], where: str, task: dict, ids: set[str], schema_12: bool = False) -> None:
    items = task.get("verification")
    if not isinstance(items, list) or not items:
        errors.append(f"{where}.verification: needs at least one command or explicit manual check")
        return
    for index, item in enumerate(items):
        spot = f"{where}.verification[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{spot}: must be an object")
            continue
        kind = item.get("type")
        if kind not in ("command", "manual"):
            errors.append(f"{spot}.type: {kind!r} is not one of {', '.join(("command", "manual"))}")
        if not text(item.get("value")):
            errors.append(f"{spot}.value: required")
        if not text(item.get("purpose")):
            errors.append(f"{spot}.purpose: required")
        if kind == "manual" and not text(item.get("expected")):
            errors.append(f"{spot}.expected: a manual check must state the expected result")
        created = item.get("created_by")
        if created is not None and not (isinstance(created, str) and created in ids):
            errors.append(f"{spot}.created_by: {created!r} is not a task of this plan")
        if schema_12:
            category = item.get("category")
            if category not in quality.VERIFICATION_CATEGORIES:
                if "category" not in item:
                    errors.append(f"{spot}.category: missing in schema 1.2.0")
                else:
                    errors.append(f"{spot}.category: {category!r} is not one of "
                                         f"{', '.join(quality.VERIFICATION_CATEGORIES)}")
