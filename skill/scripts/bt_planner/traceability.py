"""Requirement-to-task validation extension for PLAN.json schema 1.2.0."""
from __future__ import annotations

import re
from pathlib import Path

REQUIREMENT_ID_RE = re.compile(r"[A-Z][A-Z0-9]{0,7}-?[0-9]{1,4}")
_SPEC_REQUIREMENT_ID = re.compile(r"^[ \t]*(?:[-*+]|[0-9]+[.)])[ \t]+([A-Z][A-Z0-9]{0,7}-?[0-9]{1,4})[.:](?:[ \t]+|$)")
_SPEC_HEADING = re.compile(r"^[ \t]{0,3}(#{1,6})[ \t]+(.+?)[ \t]*$")
_SPEC_FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_SPEC_FENCE_CLOSE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*$")


def requirements_from_spec(text: str) -> set[str] | None:
    """Read IDs at the start of list items in a SPEC Requirements section; None means no such heading."""
    heading_level: int | None = None
    requirement_ids: set[str] = set()
    fence_char: str | None = None
    fence_length = 0
    for line in text.splitlines():
        if fence_char is not None:
            closing_fence = _SPEC_FENCE_CLOSE.match(line)
            if closing_fence and closing_fence.group(1)[0] == fence_char \
                    and len(closing_fence.group(1)) >= fence_length:
                fence_char = None
                fence_length = 0
            continue
        fence = _SPEC_FENCE_OPEN.match(line)
        if fence:
            fence_char = fence.group(1)[0]
            fence_length = len(fence.group(1))
            continue

        heading = _SPEC_HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            title = re.sub(r"[ \t]+#+[ \t]*$", "", heading.group(2)).strip()
            if heading_level is not None and level <= heading_level:
                return requirement_ids
            if heading_level is None and title.casefold() == "requirements":
                heading_level = level
            continue
        if heading_level is not None:
            match = _SPEC_REQUIREMENT_ID.match(line)
            if match:
                requirement_ids.add(match.group(1))
    return requirement_ids if heading_level is not None else None


def read_spec_ids(directory: Path, spec_ref: object) -> set[str] | None:
    """Read only a SPEC contained by the plan directory; unsafe or unreadable references are unavailable."""
    root = Path(directory).resolve()
    try:
        target = (root / str(spec_ref or "SPEC.md")).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            return None
        return requirements_from_spec(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, RuntimeError):
        return None


def check(plan: object, spec_ids: set[str] | None = None) -> tuple[list[str], list[str]]:
    """Return traceability errors and warnings for a 1.2.0-or-newer plan.

    `spec_ids` is supplied by the sync layer when the referenced SPEC has a Requirements heading. Contract-only
    validation passes None and reports that comparison as unavailable. The caller owns the schema-version gate.
    """
    if not isinstance(plan, dict):
        return [], []

    errors: list[str] = []
    warnings: list[str] = []
    declared: set[str] = set()
    raw_requirements = plan.get("requirements")
    if not isinstance(raw_requirements, list) or not raw_requirements:
        errors.append("plan.requirements: must be a non-empty list of unique requirement IDs")
    else:
        for index, value in enumerate(raw_requirements):
            if not isinstance(value, str) or REQUIREMENT_ID_RE.fullmatch(value) is None:
                errors.append(f"requirements[{index}]: {value!r} is not a valid requirement ID")
                continue
            if value in declared:
                errors.append(f"requirements: duplicate requirement ID {value}")
                continue
            declared.add(value)

    if spec_ids is None:
        warnings.append("plan.spec_ref: SPEC Requirements IDs are unavailable; plan IDs could not be compared")
    else:
        for requirement_id in sorted(spec_ids - declared):
            errors.append(f"requirements: SPEC requirement {requirement_id} is missing from PLAN.json")
        for requirement_id in sorted(declared - spec_ids):
            errors.append(f"requirements: {requirement_id} is declared in PLAN.json but missing from SPEC Requirements")

    coverage = {requirement_id: [] for requirement_id in declared}
    tasks = plan.get("tasks")
    if isinstance(tasks, list):
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue  # The contract validator reports malformed task objects.
            task_id = task.get("id")
            where = task_id if isinstance(task_id, str) and task_id else f"tasks[{index}]"
            covers = task.get("covers")
            if not isinstance(covers, list) or not covers:
                errors.append(f"{where}.covers: must list at least one requirement ID (orphan work)")
                continue

            valid_links: set[str] = set()
            seen: set[str] = set()
            for cover_index, value in enumerate(covers):
                if not isinstance(value, str) or REQUIREMENT_ID_RE.fullmatch(value) is None:
                    errors.append(f"{where}.covers[{cover_index}]: {value!r} is not a valid requirement ID")
                    continue
                if value in seen:
                    errors.append(f"{where}.covers: duplicate requirement ID {value}")
                    continue
                seen.add(value)
                if value not in declared:
                    errors.append(f"{where}.covers[{cover_index}]: {value} is not declared in plan.requirements")
                    continue
                valid_links.add(value)
                coverage[value].append(where)
            if not valid_links:
                errors.append(f"{where}.covers: task covers no declared requirement (orphan work)")

    for requirement_id, task_ids in coverage.items():
        if not task_ids:
            errors.append(f"requirements.{requirement_id}: no task covers this requirement")

    return errors, warnings


def coverage_report(plan: object) -> dict[str, list[str]]:
    """Map every declared requirement to its planned task IDs; an empty list is an uncovered requirement."""
    if not isinstance(plan, dict):
        return {}
    requirements = plan.get("requirements")
    if not isinstance(requirements, list):
        return {}
    coverage: dict[str, set[str]] = {
        requirement_id: set() for requirement_id in requirements
        if isinstance(requirement_id, str) and REQUIREMENT_ID_RE.fullmatch(requirement_id)
    }
    tasks = plan.get("tasks")
    if isinstance(tasks, list):
        for task in tasks:
            if not isinstance(task, dict) or not isinstance(task.get("id"), str):
                continue
            covers = task.get("covers")
            if not isinstance(covers, list):
                continue
            for requirement_id in covers:
                if isinstance(requirement_id, str) and requirement_id in coverage:
                    coverage[requirement_id].add(task["id"])
    return {requirement_id: sorted(task_ids) for requirement_id, task_ids in coverage.items()}
