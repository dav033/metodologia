"""Pure command and owner-surface verification helpers for recovery compilation."""
from __future__ import annotations

import copy
import re
import shlex
from collections.abc import Mapping
from typing import Any


class RecoveryCompilationError(ValueError):
    """Typed refusal raised when a recovery input cannot safely produce a revision."""

    def __init__(self, code: str, reason: str):
        self.code = code
        self.reason = reason
        super().__init__(f"{code}: {reason}")


def _refuse(reason: str, code: str = "RECOVERY_REFUSED") -> None:
    raise RecoveryCompilationError(code, reason)


def _task_id(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"T[0-9]+(?:\.[0-9]+)?[a-z]?", value) is not None


def _path(value: object) -> bool:
    return (isinstance(value, str) and bool(value) and not value.startswith("/") and "\\" not in value
            and "\x00" not in value and all(part not in ("", ".", "..") for part in value.split("/")))


def _commands(task: Mapping[str, Any]) -> list[str]:
    checks = task.get("verification", [])
    return [item["value"] for item in checks if isinstance(item, Mapping) and item.get("type") == "command"
            and isinstance(item.get("value"), str)] if isinstance(checks, list) else []


def _slug(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_.:-]+", "_", value.strip()).strip("_.:-")
    return (token or "symptom")[:128]


def _task_record(value: object, *, existing_ids: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _refuse(f"{label} must be a complete task record", "INVALID_CONVERGENCE")
    row = copy.deepcopy(dict(value))
    if not _task_id(row.get("id")) or row["id"] in existing_ids:
        _refuse(f"{label} has an invalid or duplicate task id", "INVALID_CONVERGENCE")
    return row


def _safe_command(command: object) -> bool:
    if not isinstance(command, str) or not command.strip() or any(c in command for c in ("\n", "\r", "\x00", ";", "&&", "||", "|", ">", "<", "`", "$(", "${")):
        return False
    try:
        parts = shlex.split(command)
    except ValueError:
        return False
    executable = parts[0].rsplit("/", 1)[-1].lower() if parts else ""
    if executable in {"sh", "bash", "zsh", "fish", "dash", "sudo", "rm", "mv", "chmod", "chown"}:
        return False
    if executable in {"python", "python2", "python3", "node", "ruby", "perl"} and any(
            part in {"-c", "--command", "-e"} for part in parts[1:]):
        return False
    return bool(parts) and not any(part in {";", "&&", "||", "|", ">", "<"} for part in parts)


def coverage_checks(plan: Mapping[str, Any], owners: object, actual_paths: object, oracle: object) -> list[dict[str, str]]:
    """Return every relevant existing command check for each affected owner surface."""
    if not isinstance(plan, Mapping) or not isinstance(plan.get("tasks"), list):
        _refuse("current plan tasks are malformed", "INVALID_PLAN")
    if not isinstance(owners, (list, tuple)) or not owners or not all(_task_id(x) for x in owners):
        _refuse("affected owners are missing or malformed", "UNKNOWN_OWNER")
    if not isinstance(actual_paths, (list, tuple)) or not actual_paths or not all(_path(x) for x in actual_paths):
        _refuse("actual changed paths are missing or unsafe", "UNKNOWN_PATH")
    tasks = {row.get("id"): row for row in plan["tasks"] if isinstance(row, Mapping)}
    if len(tasks) != len(plan["tasks"]):
        _refuse("plan contains malformed or duplicate task identities", "INVALID_PLAN")
    checks: list[dict[str, str]] = []
    owner_rows: dict[str, Mapping[str, Any]] = {}
    for owner_id in owners:
        owner = tasks.get(owner_id)
        if owner is None:
            _refuse(f"unknown owner task: {owner_id}", "UNKNOWN_TASK")
        owner_rows[owner_id] = owner
        scopes = owner.get("expected_paths", [])
        owner_paths = [p for p in actual_paths if any(p == s or p.startswith(s.rstrip("/") + "/") for s in scopes if isinstance(s, str))]
        if not owner_paths:
            continue
        commands = _commands(owner)
        relevant = []
        for command in commands:
            if any(_command_covers(path, command) for path in owner_paths):
                relevant.append(command)
        if any(_is_web(path) for path in owner_paths):
            typechecks = []
            builds = []
            for command in commands:
                low = command.lower()
                if any(token in low for token in ("typecheck", "tsc --noemit")):
                    typechecks.append(command)
                if any(token in low for token in ("npm run build", "pnpm build", "yarn build")):
                    builds.append(command)
                if command in typechecks or command in builds:
                    relevant.append(command)
            if not typechecks or not builds:
                _refuse(f"web owner {owner_id} lacks frozen typecheck or build verification", "MISSING_OWNER_CHECK")
        for command in dict.fromkeys(relevant):
            checks.append({"check_id": f"{owner_id}:{len(checks) + 1}", "owner_task_id": owner_id, "command": command,
                           "symptom": str(oracle)})
    for path in actual_paths:
        matches = [owner_id for owner_id, owner in owner_rows.items()
                   if any(isinstance(scope, str) and (path == scope or path.startswith(scope.rstrip("/") + "/"))
                          for scope in owner.get("expected_paths", []))]
        if not matches:
            _refuse(f"changed path has unknown named owner: {path}", "UNKNOWN_OWNER")
        # a path two NAMED owners share is the clash a convergence repairs (the compiler refuses shared paths outside one): it
        # needs a relevant command of at least one of them
        if not any(check["owner_task_id"] in matches and _command_covers(path, check["command"]) for check in checks):
            _refuse(f"changed path has no relevant owner command: {path}", "MISSING_OWNER_CHECK")
    if not checks:
        _refuse("no existing owner command verifies the affected paths", "MISSING_OWNER_CHECK")
    return checks


def _is_web(path: str) -> bool:
    return path.split("/", 1)[0].lower() in {"web", "frontend", "client", "app", "apps"} or path.endswith((".tsx", ".jsx", ".css"))


def _command_covers(path: str, command: str) -> bool:
    top = path.split("/", 1)[0].lower()
    low = command.lower()
    if _is_web(path):
        return f"{top}/" in low or any(token in low for token in ("typecheck", "tsc --noemit", "npm run lint", "npm run build", "pnpm build", "yarn build"))
    return f"{top}/" in low or path.lower() in low or path.rsplit("/", 1)[-1].lower() in low


def replan_verification(plan: Mapping[str, Any], verification_map: object, actual_paths: object) -> list[dict[str, Any]]:
    """Return additive missing verification rows, refusing deletion or relaxation requests."""
    if (not isinstance(plan, Mapping) or not isinstance(plan.get("tasks"), list)
            or not isinstance(verification_map, Mapping)
            or set(verification_map) != {"schema_version", "changed_paths", "checks", "existing_owner_commands",
                                         "uncovered_paths", "uncovered_checks"}
            or verification_map.get("schema_version") != "recovery-verification-map/1"):
        _refuse("verification map schema is invalid", "INVALID_VERIFICATION_MAP")
    checks = verification_map.get("checks")
    mapped = verification_map.get("changed_paths")
    if (not isinstance(checks, list) or not checks or not isinstance(mapped, list)
            or not isinstance(verification_map.get("existing_owner_commands"), list)
            or verification_map["uncovered_paths"] != [] or verification_map["uncovered_checks"] != []):
        _refuse("verification map collections are malformed", "INVALID_VERIFICATION_MAP")
    if not isinstance(actual_paths, (list, tuple)) or not all(_path(path) for path in actual_paths):
        _refuse("actual changed paths are malformed", "UNKNOWN_PATH")
    if (not all(isinstance(row, Mapping) and set(row) == {"path", "source_digest", "owner_task_id"}
                for row in mapped)
            or len({row.get("path") for row in mapped}) != len(mapped)
            or {row.get("path") for row in mapped} != set(actual_paths)):
        _refuse("verification map does not cover exact changed paths", "UNKNOWN_PATH")
    owners = {task.get("id"): task for task in plan.get("tasks", []) if isinstance(task, Mapping)}
    for row in mapped:
        owner = owners.get(row.get("owner_task_id"))
        scopes = owner.get("expected_paths", []) if isinstance(owner, Mapping) else []
        if (not _path(row.get("path")) or not isinstance(row.get("source_digest"), str)
                or re.fullmatch(r"[a-f0-9]{64}", row["source_digest"]) is None
                or not isinstance(scopes, list) or not any(
                    isinstance(scope, str) and (row["path"] == scope or row["path"].startswith(scope.rstrip("/") + "/"))
                    for scope in scopes)):
            _refuse("verification map path has an unknown owner or source", "UNKNOWN_OWNER")
    check_ids: set[str] = set()
    rows = []
    for check in checks:
        if (not isinstance(check, Mapping) or set(check) != {"check_id", "owner_task_id", "command", "symptom", "verdict_identity"}
                or not _task_id(check.get("owner_task_id")) or check.get("owner_task_id") not in owners
                or not isinstance(check.get("check_id"), str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", check["check_id"]) is None
                or check["check_id"] in check_ids or not isinstance(check.get("symptom"), str)
                or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}", check["symptom"]) is None
                or not isinstance(check.get("verdict_identity"), str)
                or re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", check["verdict_identity"]) is None
                or check["command"] not in verification_map["existing_owner_commands"]
                or not _safe_command(check.get("command"))):
            _refuse("unsafe or malformed verification command", "UNSAFE_COMMAND")
        check_ids.add(check["check_id"])
        if check["command"] not in _commands(owners[check["owner_task_id"]]):
            _refuse("verification map adds or substitutes a frozen owner command", "WEAKENED_CHECKS")
        rows.append({"type": "command", "value": check["command"],
                     "purpose": f"Verify symptom recovery: {check['symptom']}", "category": "regression",
                     "created_by": check["owner_task_id"]})
    declared = {(check["owner_task_id"], check["command"]) for check in checks if isinstance(check, Mapping)
                and isinstance(check.get("owner_task_id"), str) and isinstance(check.get("command"), str)}
    for row in mapped:
        if not any(owner_id == row["owner_task_id"] and _command_covers(row["path"], command)
                   for owner_id, command in declared):
            _refuse("verification map path has no owner-scoped regression check", "MISSING_OWNER_CHECK")
    return rows


