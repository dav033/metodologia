"""Pinned retries for remote Scheduler recovery commands."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Mapping

PIN_FILE = "RUN.pins.json"
PIN_FIELDS = frozenset({"provider", "model", "profile", "account", "route_id"})


def validate_pin(value: object) -> dict[str, str]:
    if isinstance(value, str) and value.strip():
        return {"route_id": value.strip()}
    if not isinstance(value, Mapping) or not value or set(value) - PIN_FIELDS:
        raise ValueError("route debe indicar route_id, provider, model y/o account.")
    pin = {("profile" if key == "account" else key): item.strip()
           for key, item in value.items() if isinstance(item, str) and item.strip()}
    if "account" in value and "profile" in value:
        raise ValueError("Use account o profile, no ambos.")
    if len(pin) != len(value):
        raise ValueError("Los campos de route deben ser textos no vacíos.")
    if not pin:
        raise ValueError("route debe indicar route_id, provider, model y/o account.")
    return pin


def pin_path(rdir: Path) -> Path:
    return Path(rdir) / PIN_FILE


def read_pins(rdir: Path) -> dict[str, dict[str, str]]:
    try:
        payload = json.loads(pin_path(rdir).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError, ValueError):
        raise ValueError("El registro de rutas fijadas no se puede leer.") from None
    if not isinstance(payload, dict) or payload.get("schema_version") != 1 or not isinstance(payload.get("tasks"), dict):
        raise ValueError("El registro de rutas fijadas no tiene un formato válido.")
    tasks = payload["tasks"]
    if any(not isinstance(task, str) or not task or not isinstance(pin, dict) for task, pin in tasks.items()):
        raise ValueError("El registro de rutas fijadas contiene tareas no válidas.")
    return {task: validate_pin(pin) for task, pin in tasks.items()}


def write_pin(rdir: Path, task: str, pin: dict[str, str]) -> None:
    path = pin_path(rdir)
    pins = read_pins(rdir)
    pins[task] = pin
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"schema_version": 1, "tasks": pins}, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def task_candidates(project: str, rdir: Path, task_id: str):
    import bt_scheduler_ops as ops
    import bt_scheduler_decision_adapter as decision_sources

    plan = ops.bound_plan(rdir)
    task = plan.task(task_id)
    facts, kind, classifications = decision_sources.task_facts(
        task.id, task.meta, task.after, task.acceptance_criteria, task.verification,
        task.shared_resources, task.expected_paths,
    )
    return facts, decision_sources._candidate_rows(project, kind, classifications, time.time())


def matches(pin: Mapping[str, str], candidate) -> bool:
    return all(getattr(candidate, key) == value for key, value in pin.items())


def filter_candidates(pin: Mapping[str, str], candidates):
    return tuple(candidate for candidate in candidates if matches(pin, candidate))


def available(candidate) -> bool:
    """Delegates to the one rule pinned retries apply (bt_route_pins.usable), so a listed route is retryable (F22)."""
    import bt_route_pins
    return bt_route_pins.usable(candidate)


def route_options(project: str, rdir: Path, task_id: str) -> list[dict[str, object]]:
    """The task's current Scheduler candidates in the contract's RouteOption shape (bt_contracts.remote)."""
    import bt_route_pins
    return [{"routeId": item.route_id, "provider": item.provider, "model": item.model, "profile": item.profile,
             "available": available(item), "quotaStatus": item.quota_status}
            for item in bt_route_pins.candidates_for(project, rdir, task_id)]


def validate_available(project: str, rdir: Path, task_id: str, pin: Mapping[str, str]):
    _, candidates = task_candidates(project, rdir, task_id)
    found = [candidate for candidate in candidates if matches(pin, candidate)]
    candidate = next((candidate for candidate in found if available(candidate)), None)
    if candidate is None:
        raise ValueError("La ruta elegida no está disponible para esta tarea; no se reabrió.")
    return candidate

