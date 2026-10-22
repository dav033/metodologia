"""Export the run's official records as the documents `bt_recovery_evidence.collect_recovery_evidence` reads (REQ-029 R2/R3, P-152).

The collector wants five JSON documents under the run directory, each pinned by its SHA-256: the M1 state (with the attempts), the
frozen plan, the M6 verdict of the failed attempt, the remediation history and the M3 manifest of the attempt. Nothing wrote them, so
the collector had never run on a real run. This module reads the owners' stores read-only, writes a private copy of each under
`RUN.recovery/<task>-<attempt>/` and returns the `audit` and `attempt` descriptors the collector takes.

Every document is a copy of an official record, never a summary: the plan document is the frozen plan's canonical bytes (so its digest
is the plan hash M1 holds), the M6 document is the stored verdict, the manifest is the executor's own file. A record that cannot be
read or does not belong to the attempt is a `ExportError` that names it: absent evidence is a blocker, never an empty document.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DIR = "RUN.recovery"


class ExportError(ValueError):
    """An official record is missing or does not belong to the attempt."""


def _write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _manifest_path(rdir: Path, attempt_id: str) -> Path:
    """The executor's manifest of the attempt: `<executor dir>/attempts/<dirname>/handoff/manifest.json` of the ledger that knows it."""
    import bt_run_stores

    state = bt_run_stores.paths(rdir)["m1"].parent.parent
    project = rdir.parent.parent.name
    req = "-".join(rdir.name.split("-")[:2]) if rdir.name.startswith("REQ-") else rdir.name
    for ledger in sorted((state / "executor").glob(f"{project}-{req}-*/ledger.db"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            conn = sqlite3.connect(f"file:{ledger}?mode=ro", uri=True)
            try:
                row = conn.execute("SELECT dirname FROM attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
            finally:
                conn.close()
        except sqlite3.Error:
            continue
        if row:
            path = ledger.parent / "attempts" / row[0] / "handoff" / "manifest.json"
            if path.is_file():
                return path
    raise ExportError(f"no M3 manifest for {attempt_id}")


def _m6_result(rdir: Path, task_id: str, attempt_id: str) -> tuple[dict, dict]:
    """(request, result) of the verification of this attempt: the stored M6 verdict, not a recomputation."""
    import bt_run_stores

    path = bt_run_stores.paths(rdir).get("m6")
    if path is None or not Path(path).exists():
        raise ExportError("no M6 store")
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT request_json, result_json FROM requests WHERE result_json IS NOT NULL").fetchall()
    except sqlite3.Error as error:
        raise ExportError(f"M6 store unreadable: {error}") from error
    finally:
        conn.close()
    found = None
    for request_json, result_json in rows:
        try:
            request, result = json.loads(request_json), json.loads(result_json)
        except ValueError:
            continue
        if request.get("task_id") == task_id and request.get("attempt_id") == attempt_id:
            found = (request, result)            # a later row (a retried verification) replaces an earlier one
    if found is None:
        raise ExportError(f"no M6 verdict for {task_id} {attempt_id}")
    return found


def export(rdir: Path | str, task_id: str, attempt_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Write the five documents of one failed attempt and return `(audit, attempt)` for `collect_recovery_evidence`."""
    import bt_plan_adapter
    import bt_scheduler_decisions as decisions

    rdir = Path(rdir)
    try:
        doc = decisions._state(rdir)
    except Exception as error:  # noqa: BLE001 - an unreadable run has no evidence
        raise ExportError(f"M1 state unreadable: {type(error).__name__}") from error
    attempt = (doc.get("attempts") or {}).get(attempt_id)
    if not isinstance(attempt, dict) or attempt.get("task_id") != task_id:
        raise ExportError(f"{attempt_id} is not an attempt of {task_id}")
    revision, plan_sha = doc.get("revision"), doc.get("plan_sha256")
    plan = next((bt_plan_adapter.planner_revisions.load_revision(rdir, row["revision"]) for row in bt_plan_adapter.revisions(rdir)
                 if row.get("revision") == revision), None)
    if plan is None:
        raise ExportError(f"the frozen plan r{revision} is not on disk")
    plan_bytes = bt_plan_adapter.planner_contract.dumps(plan).encode("utf-8")
    if hashlib.sha256(plan_bytes).hexdigest() != plan_sha:
        raise ExportError("the frozen plan on disk is not the one M1 runs")
    request, result = _m6_result(rdir, task_id, attempt_id)
    if request.get("revision") != revision:
        raise ExportError(f"the verdict of {attempt_id} was given under plan r{request.get('revision')}, the run is on r{revision}")
    manifest = _manifest_path(rdir, attempt_id)
    remediation = []
    try:
        for line in (rdir / "RUN.remediation.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                remediation.append(row)
    except OSError:
        pass
    folder = Path(DIR) / f"{task_id}-{attempt_id}"
    base = rdir / folder
    attempts = [{**vars_of(rec), "id": key} for key, rec in sorted((doc.get("attempts") or {}).items())]
    docs = {
        "m1": _json_bytes({"plan_id": doc.get("plan_id"), "revision": revision, "plan_sha256": plan_sha, "attempts": attempts}),
        "plan": plan_bytes,
        "m6": _json_bytes({"identity": {"plan_id": doc.get("plan_id"), "revision": revision, "task_id": task_id,
                                        "attempt_id": attempt_id, "token": request.get("token"), "plan_sha256": plan_sha},
                           "checks": result.get("checks") or [], "result": result}),
        "remediation": _json_bytes({"events": remediation}),
    }
    audit: dict[str, Any] = {"task_id": task_id, "plan_id": doc.get("plan_id"), "revision": revision}
    for name, data in docs.items():
        audit[f"{name}_path"] = (folder / f"{name}.json").as_posix()
        audit[f"{name}_sha256"] = _write(base / f"{name}.json", data)
    raw_manifest = manifest.read_bytes()
    manifest_digest = _write(base / "manifest.json", raw_manifest)
    try:
        body = json.loads(raw_manifest)
    except ValueError as error:
        raise ExportError("the M3 manifest is not JSON") from error
    return audit, {"attempt_id": attempt_id, "token": attempt.get("token"), "manifest_path": (folder / "manifest.json").as_posix(),
                   "manifest_sha256": manifest_digest, "repository": body.get("repository"), "base_sha": body.get("base_sha"),
                   "snapshot_sha": body.get("snapshot_sha")}


def vars_of(record: Any) -> dict[str, Any]:
    return dict(record) if isinstance(record, dict) else {}
