"""Remote commands for a durable run (REQ-030 M7): the uv side of `bt_durable_panel.dispatch`.

`bt-durable remote PROJECT REQ` reads one JSON request on stdin and prints one JSON result. Before anything is sent the
projection is rebuilt from DBOS (`projection.project`), and the command is refused when it is stale:

- its `expect.revision` (the subject's sequence the caller saw) or `expect.state` differs from the fresh projection;
- it answers a decision that is no longer open (the id names request and task round: `T2:d1@k3`);
- it does not apply to the current state (pause a paused run, retry a task that is not stopped).

What passes is sent as a durable DBOS message: run commands carry the caller's request id (DBOS applies one message
per idempotency key and destination; the run workflow also ignores a request id it has seen) and the state they were
built against (`expect_paused`, `expect_round`), which the run workflow checks again when it receives them; an answer
is keyed by its decision request and goes to that exact task round. Exactly-once is not claimed: a refusal inside the
workflow after the send is recorded in telemetry (`command_refused`).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import bt_durable_panel as panel
from bt_contracts.execution import RunRef
from bt_contracts.owner import OwnerAnswer

from . import projection

KINDS = ("pause", "resume", "retry_task", "answer")
EXPECT = "run_command_expect"          # the engine's bt.run checks RunCommand.expect_paused / expect_round
FEATURES = (EXPECT,)
_KEY = re.compile(r"^[A-Za-z0-9._:@-]{8,120}$")


def result(status: str, code: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "code": code, "message": message, **extra}


def write_marker(path: Path) -> None:
    """Written by the engine at start: its pid and the message features its workflows understand."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY | os.O_CLOEXEC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "features": list(FEATURES), "started_at": time.time()}, stream)
    os.replace(tmp, path)


def engine_features(path: Path) -> frozenset[str]:
    """What the RUNNING engine understands. An engine of older code writes no marker (or its pid is gone): commands
    are then sent without `expect_*` fields, because an older bt.run would refuse them as invalid and record a step
    the newer code does not replay. The fresh-projection check still applies."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        os.kill(int(data["pid"]), 0)
    except (OSError, ValueError, KeyError, TypeError):
        return frozenset()
    return frozenset(f for f in data.get("features") or [] if isinstance(f, str))


def handle(client, run: RunRef, request: Any, plan=None, features: frozenset[str] = frozenset(FEATURES)) -> dict:
    """Check `request` against a fresh projection and send it; never raises for a refused command."""
    expecting = EXPECT in features
    if not isinstance(request, dict) or request.get("command") not in KINDS:
        return result("REJECTED", "INVALID", f"command must be one of {', '.join(KINDS)}")
    key = request.get("request_id")
    if not isinstance(key, str) or not _KEY.match(key):
        return result("REJECTED", "INVALID", "request_id must be 8-120 characters of [A-Za-z0-9._:@-]")
    note, by = str(request.get("note") or "")[:6000], str(request.get("by") or "remote")[:80] or "remote"
    expect = request.get("expect") if isinstance(request.get("expect"), dict) else {}
    doc = projection.project(client.client, run, plan)
    seq = doc["sequence"]
    kind = request["command"]
    if kind in ("pause", "resume"):
        stale = _stale(expect, doc["status"], doc.get("status_seq"), "the run")
        if stale:
            return result("REJECTED", "STALE", stale, sequence=seq)
        wanted = "running" if kind == "pause" else "paused"
        if doc["status"] != wanted:
            return result("REJECTED", "NOT_APPLICABLE", f"{kind} does not apply: the run is {doc['status']}",
                          sequence=seq)
        client.command(run, kind, note=note, request_id=key, by=by,
                       expect_paused=(kind == "resume") if expecting else None)
        return result("OK", "SENT", f"{kind} sent to {doc['workflow_id']}", sequence=seq,
                      workflow_id=doc["workflow_id"], workflow_checked=expecting)
    if kind == "retry_task":
        task = next((t for t in doc["tasks"] if t.get("id") == request.get("task")), None)
        if task is None:
            return result("REJECTED", "INVALID", f"{request.get('task')!r} is not a task of {run.run_id}")
        stale = _stale(expect, panel.TASK_STATE.get(task["state"], "pending"), task.get("seq"), task["id"])
        if stale:
            return result("REJECTED", "STALE", stale, sequence=seq)
        if task["state"] not in panel.STOPPED:
            return result("REJECTED", "NOT_APPLICABLE", f"{task['id']} is {task['state']}: only a stopped task "
                          "(blocked, failed, cancelled) is started again", sequence=seq)
        if doc["status"] not in ("running", "paused"):
            return result("REJECTED", "NOT_APPLICABLE", f"the run is {doc['status']}: it no longer takes commands",
                          sequence=seq)
        client.command(run, "retry_task", task_id=task["id"], note=note, request_id=key, by=by,
                       expect_round=task.get("round") if expecting else None)
        return result("OK", "SENT", f"retry of {task['id']} (after round {task.get('round')}) sent", sequence=seq,
                      workflow_id=doc["workflow_id"], workflow_checked=expecting)
    decision_id = request.get("decision")
    found = next((d for d in doc["decisions"] if d.get("id") == decision_id), None)
    if found is None:
        open_now = ", ".join(d["id"] for d in doc["decisions"]) or "none"
        return result("REJECTED", "NOT_OPEN", f"decision {decision_id} is no longer open (open now: {open_now})",
                      sequence=seq)
    stale = _stale({"revision": expect.get("revision")}, "open", found.get("seq"), str(decision_id))
    if stale:
        return result("REJECTED", "STALE", stale, sequence=seq)
    action = request.get("action")
    if action not in (found.get("options") or panel.OPTIONS):
        return result("REJECTED", "INVALID", f"{action!r} is not an option of {decision_id}")
    answer = OwnerAnswer(request_id=found["request_id"], action=action, note=note, by=by)
    try:
        workflow = client.answer(run, found["task_id"], answer, round_no=found["round"])
    except LookupError as error:                     # the round closed between the projection and the send
        return result("REJECTED", "NOT_OPEN", str(error), sequence=seq)
    return result("OK", "SENT", f"{action} sent for {decision_id}", sequence=seq, workflow_id=workflow)


def _stale(expect: dict, state: str, revision: Any, subject: str) -> str:
    want_revision, want_state = expect.get("revision"), expect.get("state")
    if want_revision is not None and want_revision != revision:
        return f"stale: {subject} changed at sequence {revision} after the command was built (it saw {want_revision})"
    if want_state is not None and want_state != state:
        return f"stale: {subject} is {state} now, the command expected {want_state}"
    return ""
