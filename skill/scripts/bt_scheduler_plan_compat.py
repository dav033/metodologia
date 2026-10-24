"""Compatibility checks for PLAN.json consumers downstream of the methodology Planner."""
from __future__ import annotations

import importlib
import re
from collections.abc import Callable
from pathlib import Path

import bt_plan_adapter as plan_adapter

PLAN_SCHEMA_CAPABILITY_SINCE = (1, 2, 0)
DEFAULT_PLAN_SCHEMA_VERSION = "1.3.0"
_CONSUMERS = (
    ("M2", "bt_scheduler_decision_adapter"),
    ("M6", "bt_scheduler_quality.contracts"),
)
_SCHEMA_13_CONSUMERS = (("M3", "bt_scheduler_executor_adapter"),)
_SCHEMA_VERSION_RE = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)\Z")


def _version_tuple(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = _SCHEMA_VERSION_RE.fullmatch(value)
    if match is None:
        return None
    try:
        return tuple(int(match.group(index)) for index in (1, 2, 3))
    except ValueError:
        return None


def _consumer_capability(schema_version: str, declared: object) -> dict[str, object]:
    if not isinstance(declared, (set, frozenset, tuple, list)) or not all(
        isinstance(version, str) and _version_tuple(version) is not None for version in declared
    ):
        return {"status": "unknown", "supported_schema_versions": []}
    versions = sorted(set(declared))
    return {"status": "supported" if schema_version in versions else "unsupported",
            "supported_schema_versions": versions}


def downstream_compatibility(schema_version: str, *, planner_version: object,
                             m1_capabilities: object) -> dict[str, object]:
    """Report explicit Planner/M1/M2/M6 support, plus M3 for schema 1.3; malformed markers stay unknown."""
    required = _version_tuple(schema_version)
    installed = _version_tuple(planner_version)
    planner_status = "unknown" if required is None or installed is None else \
        "supported" if installed[0] == required[0] and installed >= required else "unsupported"
    consumers = {"M1": _consumer_capability(schema_version, m1_capabilities)}
    declared_consumers = (*_CONSUMERS, *_SCHEMA_13_CONSUMERS) if required is not None and required >= (1, 3, 0) else _CONSUMERS
    for name, module_name in declared_consumers:
        try:
            module = importlib.import_module(module_name)
            declared = getattr(module, "PLAN_SCHEMA_CAPABILITIES", None)
        except Exception:  # noqa: BLE001 - a missing downstream consumer must fail closed
            declared = None
        consumers[name] = _consumer_capability(schema_version, declared)
    return {"required_schema_version": schema_version,
            "planner": {"status": planner_status, "schema_version": planner_version},
            "supported": planner_status == "supported" and
            all(item["status"] == "supported" for item in consumers.values()),
            "consumers": consumers}


def compatibility_report(plan_path: Path, *, planner_version: object,
                          m1_capabilities: object) -> dict[str, object]:
    """Build a report for the schema encoded by a working or frozen PLAN.json."""
    details = plan_adapter.plan_schema_version_details(Path(plan_path))
    schema_version = details[0] if details is not None else DEFAULT_PLAN_SCHEMA_VERSION
    return downstream_compatibility(schema_version, planner_version=planner_version,
                                    m1_capabilities=m1_capabilities)


def consumer_problem(rdir: Path, *, plan_path: Path, planner_version: object,
                     m1_capabilities: object) -> str | None:
    """Fail closed when a plan is presented without every downstream capability required by its schema."""
    path = Path(plan_path)
    details = plan_adapter.plan_schema_version_details(path)
    if details is None or details[1] < PLAN_SCHEMA_CAPABILITY_SINCE:
        return None
    report = downstream_compatibility(details[0], planner_version=planner_version,
                                      m1_capabilities=m1_capabilities)
    return plan_adapter.plan_consumer_problem(rdir, compatibility_report=report, plan_path=path)


def run_gate(rdir: Path, state: dict | None,
             report_for_plan: Callable[[Path], dict[str, object]]) -> str | None:
    """Gate a new or resumed run, loading downstream capabilities only for schema 1.2.0+."""
    details = plan_adapter.plan_schema_version_details(Path(rdir) / plan_adapter.planner.PLAN_JSON)
    report = report_for_plan(rdir) if details is not None and details[1] >= PLAN_SCHEMA_CAPABILITY_SINCE else None
    if state is None:
        return plan_adapter.launch_problem(rdir, compatibility_report=report)
    return plan_adapter.resume_problem(rdir, state, compatibility_report=report)
