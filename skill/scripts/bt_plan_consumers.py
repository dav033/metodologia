"""Engine capability and independent-auditor policy gates for plan publication and execution."""
from __future__ import annotations

import json
import re
from pathlib import Path

PLAN_SCHEMA_CONSUMER_GATE_SINCE = (1, 2, 0)
_SCHEMA_VERSION_RE = re.compile(r"([0-9]{1,6})\.([0-9]{1,6})\.([0-9]{1,6})")


def _schema_version(plan_path: Path) -> tuple[str, tuple[int, int, int]] | None:
    """Read only the version marker; the Planner contract validates the whole document at every action gate."""
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError):
        return None
    if not isinstance(plan, dict):
        return None
    value = plan.get("schema_version")
    match = _SCHEMA_VERSION_RE.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    try:
        version = tuple(int(match.group(index)) for index in (1, 2, 3))
    except ValueError:
        return None
    return value, version


def plan_schema_version(plan_path: Path) -> str | None:
    """Return a syntactically valid version marker; the Planner owns full contract validation."""
    version = _schema_version(plan_path)
    return version[0] if version is not None else None


def second_auditor_required(plan: object) -> bool:
    """Expose the owner cross-check gate to pure plan transformations."""
    if not isinstance(plan, dict) or not isinstance(plan.get("schema_version"), str):
        return False
    match = _SCHEMA_VERSION_RE.fullmatch(plan["schema_version"])
    if match is None or tuple(int(match.group(index)) for index in (1, 2, 3)) < PLAN_SCHEMA_CONSUMER_GATE_SINCE:
        return False
    import bt_config
    return bool(bt_config.get("gates.second_auditor", True))


def plan_schema_version_details(plan_path: Path) -> tuple[str, tuple[int, int, int]] | None:
    """Return the syntactically valid version and parsed components for downstream compatibility checks."""
    return _schema_version(plan_path)


def second_auditor_problem(plan_path: Path) -> str | None:
    """Owner policy `gates.second_auditor` (default on): a plan with an audit needs an independent cross-check audit, so
    one auditor's omissions cannot decide the outcome. Schema 1.2.0 plans only; the planner only warns, the policy is
    configuration, so it lives here."""
    try:
        plan = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return second_auditor_lines(plan)


def second_auditor_lines(plan: object) -> str | None:
    """`second_auditor_problem` for an in-memory plan (a stage projection is judged before it is frozen)."""
    if not second_auditor_required(plan):
        return None
    tasks = plan.get("tasks")
    audits = [t.get("id") for t in tasks if isinstance(t, dict) and t.get("kind") == "audit"] if isinstance(tasks, list) else []
    if len(audits) == 1:
        return (f"SECOND_AUDITOR_MISSING: {audits[0]} is the only audit; gates.second_auditor is on, so add an independent "
                "cross-check audit task (own report and findings ledger) — `plan-json retrofit-audit REQ --cross-check` "
                "adds it — or turn the policy off with `bitacora.py config set gates.second_auditor false`")
    return None


def plan_consumer_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                          plan_path: Path | None = None) -> str | None:
    """Apply downstream capability and owner policy gates."""
    return _consumer_problem(rdir, compatibility_report=compatibility_report, plan_path=plan_path) or \
        second_auditor_problem(plan_path or (Path(rdir) / "PLAN.json"))


def _consumer_problem(rdir: Path, *, compatibility_report: dict[str, object] | None = None,
                      plan_path: Path | None = None) -> str | None:
    """Evaluate a caller-supplied capability report without importing downstream consumers."""
    version = _schema_version(plan_path or (Path(rdir) / "PLAN.json"))
    if version is None or version[1] < PLAN_SCHEMA_CONSUMER_GATE_SINCE:
        return None
    compatibility = compatibility_report if isinstance(compatibility_report, dict) else {}
    consumers = compatibility.get("consumers") if isinstance(compatibility.get("consumers"), dict) else {}
    unavailable, supported = [], []
    if compatibility.get("required_schema_version") != version[0]:
        reported = compatibility.get("required_schema_version")
        shown = reported if isinstance(reported, str) and _schema_version_value(reported) else "unknown"
        unavailable.append(f"capability report (schema {shown})")
    required_consumers = ("M1", "M2", "M6") + (("M3",) if version[1] >= (1, 3, 0) else ())
    for name in required_consumers:
        consumer = consumers.get(name)
        status = consumer.get("status") if isinstance(consumer, dict) else "unknown"
        versions = consumer.get("supported_schema_versions") if isinstance(consumer, dict) else None
        valid = isinstance(versions, list) and all(_schema_version_value(item) for item in versions)
        if not valid or (status == "supported" and version[0] not in versions):
            status = "malformed"
        if status not in ("supported", "unsupported", "unknown"):
            status = "malformed"
        supported.append(status == "supported")
        if status != "supported": unavailable.append(f"{name} ({status})")
    planner_info = compatibility.get("planner")
    planner_status = planner_info.get("status") if isinstance(planner_info, dict) else "unknown"
    planner_version = _schema_version_value(planner_info.get("schema_version")) if isinstance(planner_info, dict) else None
    if planner_version is None or (planner_status == "supported" and (planner_version[0] != version[1][0]
                                                                        or planner_version < version[1])):
        planner_status = "malformed"
    if planner_status not in ("supported", "unsupported", "unknown"):
        planner_status = "malformed"
    if planner_status != "supported":
        unavailable.insert(0, f"Planner ({planner_status})")
    if type(compatibility.get("supported")) is not bool or compatibility["supported"] != (planner_status == "supported" and all(supported)):
        unavailable.append("capability report (malformed or inconsistent summary)")
    if not unavailable:
        return None
    return (f"PLAN_SCHEMA_UNSUPPORTED_BY_ENGINE: PLAN.json schema {version[0]} requires compatible M1/M2/M6 consumers; "
            f"unsupported or unknown: {', '.join(unavailable)}. Check `bitacora.py plan-json compat "
            f"{plan_id(rdir)}` before approval or execution")


def _schema_version_value(value: object) -> tuple[int, int, int] | None:
    match = _SCHEMA_VERSION_RE.fullmatch(value) if isinstance(value, str) else None
    return tuple(int(part) for part in match.groups()) if match else None


def _compat_consumer_supported(rdir: Path, compatibility_report: dict[str, object] | None) -> bool:
    """Compat's publication-readiness answer; plans without a PLAN.json remain legacy-compatible."""
    path = Path(rdir) / "PLAN.json"
    return not path.exists() or (_schema_version(path) is not None and
                                 _consumer_problem(rdir, compatibility_report=compatibility_report, plan_path=path) is None)


def plan_id(rdir: Path) -> str:
    """`REQ-009-some-slug` -> `REQ-009` (the methodology's requirement id)."""
    return "-".join(Path(rdir).name.split("-")[:2])


