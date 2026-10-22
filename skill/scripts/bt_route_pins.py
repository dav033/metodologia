"""Persist and apply owner-selected route constraints for Scheduler task retries."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

FIELDS = ("route", "model", "account")
FILE = "route-pins.json"


class PinError(ValueError):
    pass


def normalize(command: dict) -> dict | None:
    pin = {}
    for field in FIELDS:
        value = command.get(field)
        if value is None:
            continue
        # The web contract sends a route object; provider/model/profile identify that exact option.
        if field == "route" and isinstance(value, dict):
            value = value.get("route_id") or value.get("routeId") or value.get("provider")
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
            raise PinError(f"{field} must be a non-empty string")
        pin[field] = value.strip()
    return pin or None


def matches(pin: dict, candidate) -> bool:
    return (("route" not in pin or pin["route"] in (candidate.route_id, candidate.provider))
            and ("model" not in pin or pin["model"] == candidate.model)
            and ("account" not in pin or pin["account"] in (candidate.profile, candidate.account_ref)))


def usable(candidate) -> bool:
    return (candidate.source_status == "available" and candidate.runtime_status == "available"
            and candidate.profile_authorized and candidate.auth_status != "invalid"
            and candidate.quota_status == "available")


def candidates_for(project: str, rdir: Path, task: str) -> tuple:
    """Return the same current candidates the Scheduler assignment layer evaluates for this task."""
    import bt_scheduler_decision_adapter as sources
    import bt_scheduler_ops as ops

    spec = next((item for item in ops.bound_plan(rdir).tasks if item.id == task), None)
    if spec is None:
        return ()
    _, kind, classifications = sources.task_facts(
        task, spec.meta, spec.after, spec.acceptance_criteria, spec.verification,
        spec.shared_resources, spec.expected_paths,
    )
    return sources._candidate_rows(project, kind, classifications, time.time())


def available(project: str, rdir: Path, task: str, pin: dict) -> list:
    return [candidate for candidate in candidates_for(project, rdir, task)
            if matches(pin, candidate) and usable(candidate)]


def _path(rdir: Path) -> Path:
    return Path(rdir) / FILE


def load(rdir: Path) -> dict:
    try:
        data = json.loads(_path(rdir).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def get(rdir: Path, task: str) -> dict | None:
    value = load(rdir).get(task)
    return {key: value[key] for key in FIELDS if isinstance(value.get(key), str)} \
        if isinstance(value, dict) else None


def _write(rdir: Path, data: dict) -> None:
    folder = Path(rdir)
    folder.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=folder, prefix=".route-pins.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=1, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o644)
        os.replace(temporary, _path(folder))
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def set_pin(rdir: Path, task: str, pin: dict, by: str = "remote") -> None:
    data = load(rdir)
    data[task] = {**pin, "by": by}
    _write(rdir, data)


def clear(rdir: Path, task: str) -> None:
    data = load(rdir)
    if data.pop(task, None) is not None:
        _write(rdir, data)


def narrow(rdir: Path, task: str, candidates: tuple) -> tuple:
    pin = get(rdir, task) if rdir is not None else None
    return candidates if not pin else tuple(item for item in candidates if matches(pin, item))
