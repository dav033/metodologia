"""Secure project ownership markers for the composition workspace."""
from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path


def ensure_owner_marker(path: Path, *, project: str, req: str, plan_id: str, revision: int, plan_sha256: str) -> None:
    identity = {"project": project, "req": req, "plan_id": plan_id}
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("OWNER_COMPOSITION_WORKSPACE_OWNERSHIP_UNVERIFIED")
        existing = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({**identity, "revision": revision, "plan_sha256": plan_sha256}, stream, sort_keys=True)
        return
    except (OSError, json.JSONDecodeError):
        raise ValueError("OWNER_COMPOSITION_WORKSPACE_OWNERSHIP_UNVERIFIED") from None
    if (not isinstance(existing, dict) or any(existing.get(key) != value for key, value in identity.items())
            or ("run_id" in existing and not isinstance(existing["run_id"], str))
            or ("revision" in existing and type(existing["revision"]) is not int)
            or ("plan_sha256" in existing and not isinstance(existing["plan_sha256"], str))):
        raise ValueError("OWNER_COMPOSITION_WORKSPACE_OWNERSHIP_MISMATCH")


def bind_owner_marker(path: Path, *, project: str, req: str, plan_id: str, revision: int,
                      plan_sha256: str, run_id: str) -> None:
    marker = json.loads(path.read_text(encoding="utf-8"))
    old_run_id, old_revision = marker.get("run_id"), marker.get("revision")
    if old_run_id not in (None, run_id) and old_revision in (None, revision):
        raise ValueError("OWNER_COMPOSITION_WORKSPACE_RUN_MISMATCH")
    if old_revision == revision and marker.get("plan_sha256", plan_sha256) != plan_sha256:
        raise ValueError("OWNER_COMPOSITION_WORKSPACE_REVISION_MISMATCH")
    marker.update(project=project, req=req, plan_id=plan_id, run_id=run_id, revision=revision,
                  plan_sha256=plan_sha256)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(marker, sort_keys=True))
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600, follow_symlinks=False)
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def owner_composition_view(plan: object) -> tuple[list[dict], list[dict], list[dict]]:
    """Normalize a loaded M1 plan into the plain view the Planner's composition rules read."""
    subplans = []
    for item in getattr(plan, "subplans", ()):
        ui = getattr(item, "ui", None)
        subplans.append({"id": getattr(item, "id", ""),
                         "produces": [dict(value) for value in getattr(item, "produces", ())],
                         "ui": ({"contract": ui.contract, "version": ui.version} if ui and
                                hasattr(ui, "contract") and hasattr(ui, "version") else None)})
    gates = [{"subplans": tuple(getattr(item, "subplans", ()))} for item in getattr(plan, "composition_gates", ())]
    tasks = [{"id": getattr(task, "id", ""), "repository": getattr(task, "repository", ""),
              "expected_paths": tuple(getattr(task, "expected_paths", ()))} for task in getattr(plan, "tasks", ())]
    return subplans, gates, tasks
