"""Persistent per-task route constraints used by owner initiated retries."""
from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path

FILE = "route-pins.json"
FIELDS = ("route", "model", "account")
_LOCK = threading.Lock()


def normalize(params: dict) -> dict | None:
    """Validate route selectors and return only selectors, excluding retry metadata."""
    pin = {}
    for field in FIELDS:
        if field not in params:
            continue
        value = params[field]
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
            raise ValueError(f"params.{field} debe ser texto no vacío de hasta 200 caracteres.")
        pin[field] = value.strip()
    return pin or None


def matches(pin: dict, candidate) -> bool:
    """A route can be named by route id or provider; accounts by profile id or stable account reference."""
    return (("route" not in pin or pin["route"] in (candidate.route_id, candidate.provider)) and
            ("model" not in pin or pin["model"] == candidate.model) and
            ("account" not in pin or pin["account"] in (candidate.profile, candidate.account_ref)))


def _usable(candidate) -> bool:
    from bt_scheduler_decision.policy import _candidate_reasons
    return not _candidate_reasons(candidate)


def candidates_for(project: str, rdir: Path, task_id: str) -> tuple:
    """Build candidates from the same task facts and fresh quota preflight used for Scheduler assignment."""
    import bt_scheduler_adapter as scheduler
    import bt_scheduler_decision_adapter as sources
    import bt_scheduler_ops as ops
    import bt_scheduler_plan_routing as routing

    task_spec = next((task for task in ops.bound_plan(rdir).tasks if task.id == task_id), None)
    if task_spec is None:
        return ()
    _task, kind, classifications = sources.task_facts(
        task_id, task_spec.meta, task_spec.after, task_spec.acceptance_criteria, task_spec.verification,
        task_spec.shared_resources, task_spec.expected_paths,
    )
    quota = scheduler.refresh_quota_preflight(project)
    requested_at = routing.quota_aware_requested_at(time.time(), quota)
    candidates = sources._candidate_rows(project, kind, classifications, requested_at)
    return routing._apply_preflight(candidates, quota)


def available(project: str, rdir: Path, task_id: str, pin: dict) -> tuple:
    """Return pinned routes that pass the Scheduler's hard eligibility rules."""
    try:
        candidates = candidates_for(project, rdir, task_id)
        return tuple(candidate for candidate in candidates if matches(pin, candidate) and _usable(candidate))
    except (Exception, SystemExit):  # A broken quota/profile source cannot authorize a pinned retry.
        return ()


def _path(rdir: Path) -> Path:
    return Path(rdir) / FILE


def load(rdir: Path) -> dict:
    try:
        data = json.loads(_path(rdir).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def get(rdir: Path, task_id: str) -> dict | None:
    data = load(rdir).get(task_id)
    if not isinstance(data, dict):
        return None
    pin = {key: data[key] for key in FIELDS if isinstance(data.get(key), str)}
    return pin or None


def _write(rdir: Path, data: dict) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".route-pins.", suffix=".tmp", dir=rdir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
        os.chmod(temporary, 0o600)
        os.replace(temporary, _path(rdir))
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def set_pin(rdir: Path, task_id: str, pin: dict) -> None:
    with _LOCK:
        data = load(rdir)
        data[task_id] = pin
        _write(rdir, data)


def clear(rdir: Path, task_id: str) -> None:
    with _LOCK:
        data = load(rdir)
        if task_id in data:
            del data[task_id]
            _write(rdir, data)


def narrow(rdir: Path | None, task_id: str, candidates: tuple) -> tuple:
    """Apply the task's retry pin. A pin with no current match deliberately produces no assignment."""
    pin = get(rdir, task_id) if rdir is not None else None
    return candidates if pin is None else tuple(candidate for candidate in candidates if matches(pin, candidate))
