"""Durable runs in the panels (REQ-030 M7): read the projection, map it to the panel vocabulary, send commands.

Stdlib only: the web server, the remote API and the hooks run under the system interpreter. The projection is
written by `bt_durable.projection` (the engine refreshes it, `bt-durable project` rebuilds it) from the DBOS
workflow statuses and events; it is a read model, never a second source of truth: nothing here or in the runtime
reads it back as state, and every command is checked again against DBOS itself before it is sent.

    path(rdir, run_id)          -> where the projection of one durable run lives (<root>/.state/durable/projections)
    read(rdir)                  -> the projection of the run that RUN.owner.json gives to the durable runtime, or None
    overlay(tasks, projection)  -> fill bt_planstatus task rows (state, attempts, history, revision)
    decisions(rdir)             -> open owner decisions, in the shape of bt_scheduler_decisions requests
    target_state(rdir, ...)     -> the optimistic-concurrency view the remote command ledger compares
    dispatch(...)               -> pause | resume | retry | answer through `bt-durable remote` (durable DBOS messages)

Projection vocabulary (`tasks[].state`): pending | queued | waiting_quota | running | verifying | recovering |
needs_decision | blocked | failed | completed | cancelled. Run `status`: running | paused | completed | blocked |
failed | cancelled | unknown. `sequence` is the projection's monotonic version; `status_seq`, `tasks[].seq` and
`decisions[].seq` are the sequence at which that subject last changed (the remote precondition `revision`).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "bt.durable-projection/1"
AUTHORITY = "dbos"
# projection task state -> plan/snapshot task state (bt_planstatus vocabulary; `rejected` stands for "recovering")
TASK_STATE = {"pending": "pending", "queued": "ready", "waiting_quota": "ready", "running": "running",
              "verifying": "verifying", "recovering": "rejected", "needs_decision": "rejected", "blocked": "blocked",
              "failed": "blocked", "completed": "completed", "cancelled": "cancelled"}
RUN_STATUSES = ("running", "paused", "completed", "blocked", "failed", "cancelled", "unknown")
STOPPED = ("blocked", "failed", "cancelled")             # a task the owner may start again (`retry_task`)
OPTIONS = {
    "retry": ("Reintentar", "Un intento nuevo de la tarea, con un intento más de presupuesto."),
    "retry_with_note": ("Reintentar con una nota", "Un intento nuevo que recibe tu indicación."),
    "retry_other_route": ("Reintentar con otra ruta", "Un intento nuevo que excluye la ruta que falló."),
    "stop": ("Detener la tarea", "La tarea queda bloqueada; sus dependientes no arrancan."),
}
# remote ledger command -> durable command
COMMANDS = {"pause": "pause", "resume": "resume", "reopen": "retry_task", "retry": "retry_task",
            "answer-decision": "answer"}
CLI_TIMEOUT = 120
_RUN_ID = re.compile(r"^(?P<project>[A-Za-z0-9][A-Za-z0-9._-]{0,63}):(?P<req>REQ-\d{3,}):r(?P<revision>\d+)$")


class DurableRejected(RuntimeError):
    """The durable runtime refused a command because its target changed (the ledger records STALE_PRECONDITION)."""

    code = "STALE_PRECONDITION"


# ------------------------------------------------------------------------------------------------- location
def path(rdir: Path | str, run_id: str) -> Path:
    """`<root>/.state/durable/projections/<project>/<REQ>-r<N>.json` for a requirement of the bitácora layout (the
    root's `.state` is local and private), else `<requirement>/RUN.durable-projection.json`."""
    rdir = Path(rdir)
    match = _RUN_ID.match(run_id or "")
    if not match:
        raise ValueError(f"not a durable run id: {run_id!r}")
    if rdir.parent.name == "requirements" and rdir.parent.parent.name:
        base = rdir.parent.parent.parent / ".state" / "durable" / "projections" / match["project"]
        return base / f"{match['req']}-r{match['revision']}.json"
    return rdir / "RUN.durable-projection.json"


def owner(rdir: Path | str) -> dict | None:
    """RUN.owner.json when it gives the run to the durable runtime; None otherwise (also when it is unreadable)."""
    import bt_run_owner
    try:
        record = bt_run_owner.read(rdir)
    except bt_run_owner.OwnerConflict:
        return None
    return record if record and record.get("backend") == AUTHORITY and _RUN_ID.match(str(record.get("run_id"))) \
        else None


def owned(rdir: Path | str) -> bool:
    return owner(rdir) is not None


def read(rdir: Path | str) -> dict | None:
    """The projection of the durable run that owns this requirement, when it exists and has the expected shape."""
    record = owner(rdir)
    if record is None:
        return None
    try:
        data = json.loads(path(rdir, record["run_id"]).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if not isinstance(data, dict) or data.get("schema") != SCHEMA or data.get("projection") is not True \
            or data.get("run_id") != record["run_id"] or data.get("status") not in RUN_STATUSES \
            or type(data.get("sequence")) is not int or not isinstance(data.get("tasks"), list) \
            or not isinstance(data.get("decisions"), list):
        return None
    return data


def iso(epoch: Any) -> str | None:
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)) or epoch <= 0:
        return None
    return dt.datetime.fromtimestamp(epoch, dt.UTC).isoformat(timespec="seconds")


# --------------------------------------------------------------------------------------------- plan status
def overlay(tasks: dict[str, dict], projection: dict, history_cap: int = 10) -> None:
    """Fill bt_planstatus task rows from the projection: state in the plan vocabulary, attempts, history, reason."""
    for raw in projection.get("tasks") or []:
        task = tasks.get(raw.get("id")) if isinstance(raw, dict) else None
        if task is None:
            continue
        task["state"] = TASK_STATE.get(raw.get("state"), "pending")
        task["durable_state"] = raw.get("state")
        task["revision"] = raw.get("seq") if type(raw.get("seq")) is int else None
        task["attempts"] = raw.get("attempts") if type(raw.get("attempts")) is int else 0
        task["reason"] = reason_of(raw)
        spent = raw.get("round_attempts")
        if raw.get("limit_hit") == "max_attempts" and type(spent) is int and spent > 0:
            # the round's attempt budget is spent (what the panels call retries exhausted)
            task.update(attempts_used=spent, max_attempts=spent, retries_remaining=0, retry_exhausted=True)
        history =[_attempt(item) for item in (raw.get("history") or [])[-history_cap:] if isinstance(item, dict)]
        task["history"] = history
        task["attempt"] = history[-1] if history else None
        if raw.get("state") == "verifying" or (task["state"] == "running" and history
                                               and history[-1]["state"] == "verifying"):
            task["state"] = "verifying"


def reason_of(raw: dict) -> str | None:
    state = raw.get("state")
    if state == "waiting_quota":
        until = iso(raw.get("until"))
        return f"esperando cuota{' hasta ' + until if until else ''}"
    if state == "recovering":
        until = iso(raw.get("until"))
        return f"recuperándose{' hasta ' + until if until else ''}"
    if state == "needs_decision":
        return f"requiere decisión {raw.get('decision_id') or ''}".strip()
    if state == "failed":
        return f"el workflow terminó en {raw.get('workflow_status')}"
    if raw.get("outcome") == "inherited":
        return "heredada del runtime anterior (evidencia M6 re-comprobada)"
    return None


def _attempt(item: dict) -> dict[str, Any]:
    """A projection attempt in the bt_planstatus attempt shape (M1 attempt states)."""
    return {"id": item.get("id"), "number": item.get("number"), "state": item.get("state"),
            "provider": item.get("provider"), "model_requested": item.get("model"), "model_reported": None,
            "effort": item.get("effort") or None, "account": item.get("profile") or None, "account_ref": None,
            "started_at": iso(item.get("started_at")), "ended_at": iso(item.get("ended_at")), "cost_usd": None,
            "live": item.get("live") is True, "duration_s": item.get("duration_s"),
            "last_activity_at": iso(item.get("updated_at")), "tokens": None, "failure": item.get("failure") or None,
            "verdict": item.get("verdict")}


def run_block(projection: dict) -> dict[str, Any]:
    status = projection.get("status")
    return {"authority": AUTHORITY, "status": status, "active": status in ("running", "paused"),
            "updated_at": iso(projection.get("projected_at")), "revision": projection.get("status_seq"),
            "sequence": projection.get("sequence"), "workflow_status": projection.get("workflow_status"),
            "counts": projection.get("counts") or {}}


# -------------------------------------------------------------------------------------------------- decisions
def decisions(rdir: Path | str) -> list[dict[str, Any]]:
    """Open owner decisions of the durable run, shaped like bt_scheduler_decisions requests (the panels render them
    unchanged). The id names the request and the task round (`T2:d1@k3`), so an answer to an older round is stale."""
    projection = read(rdir)
    if projection is None:
        return []
    out = []
    for item in projection.get("decisions") or []:
        if not isinstance(item, dict) or not item.get("id"):
            continue
        failure = item.get("failure") if isinstance(item.get("failure"), dict) else {}
        options = [o for o in item.get("options") or [] if o in OPTIONS] or list(OPTIONS)
        evidence = [text for text in (
            f"fallo: {failure.get('code')} ({failure.get('failure_class')})" if failure.get("code") else "",
            f"límite: {item['limit_hit']}" if item.get("limit_hit") else "",
            str(failure.get("summary") or "")[:500], str(failure.get("agent_note") or "")[:1500]) if text]
        out.append({"id": item["id"], "source": "durable", "task": item.get("task_id"), "attempt": item.get("attempt"),
                    "title": f"{item.get('task_id')} necesita tu decisión: {item.get('reason') or 'escalada'}"[:200],
                    "what": str(item.get("reason") or "El runtime durable escaló la tarea al propietario.")[:1000],
                    "needs": "Elegir cómo sigue la tarea.", "reason": failure.get("code") or item.get("limit_hit"),
                    "error": str(failure.get("summary") or "")[:2000] or None, "evidence": evidence,
                    "you_can": [OPTIONS[o][0] for o in options],
                    "options": [{"id": o, "label": OPTIONS[o][0], "consequence": OPTIONS[o][1]} for o in options],
                    "recommended": None, "unskippable": False, "revision": item.get("seq")})
    return out


# ------------------------------------------------------------------------------------------- remote commands
def target_state(rdir: Path | str, command: str | None, params: dict | None) -> dict | None:
    """What the remote ledger compares a command's precondition with: the subject's state and the sequence at which
    it last changed (`revision`). None when the subject does not exist (the ledger rejects the command as stale)."""
    projection = read(rdir)
    if projection is None:
        return None
    params = params or {}
    if command == "answer-decision":
        request_id = params.get("request_id")
        found = next((d for d in projection["decisions"] if isinstance(d, dict) and d.get("id") == request_id), None)
        return None if found is None else {"state": "open", "revision": found.get("seq")}
    if command in ("reopen", "retry"):
        task = _task(projection, params.get("task"))
        return None if task is None else {"state": TASK_STATE.get(task.get("state"), "pending"),
                                          "revision": task.get("seq")}
    return {"state": projection["status"], "revision": projection.get("status_seq")}


def _task(projection: dict, task_id: Any) -> dict | None:
    if not isinstance(task_id, str) or not task_id:
        return None
    return next((t for t in projection["tasks"] if isinstance(t, dict) and t.get("id") == task_id), None)


def dispatch(project: str, req: str, rdir: Path | str, command: str, params: dict, *, key: str,
             precondition: dict | None = None, by: str = "remote") -> dict[str, Any]:
    """Send one remote command to the durable run as a DBOS message keyed by `key` (applied at most once).

    `bt-durable remote` rebuilds the projection from DBOS first and refuses the command when its subject is no longer
    in the state (and sequence) the caller saw, or when it answers a decision that is not open any more."""
    kind = COMMANDS.get(command)
    if kind is None:
        raise ValueError(f"El runtime durable no admite «{command}» (solo pausa, reanudación, reintento y respuesta "
                         "de decisiones).")
    if command == "retry" and any(params.get(name) for name in ("route", "model", "account")):
        raise ValueError("El runtime durable no admite fijar una ruta en el reintento; el enrutador la elige.")
    reason = params.get("reason", "")
    if not isinstance(reason, str):
        raise TypeError("reason debe ser texto.")
    request: dict[str, Any] = {"command": kind, "request_id": key, "by": by, "note": reason}
    expect = {name: value for name, value in (precondition or {}).items() if name in ("state", "revision")}
    if expect:
        request["expect"] = expect
    if kind == "retry_task":
        if not isinstance(params.get("task"), str) or not params["task"]:
            raise ValueError(f"{command} requiere params.task.")
        request["task"] = params["task"]
    if kind == "answer":
        decision, option = params.get("request_id"), params.get("option")
        if not isinstance(decision, str) or not decision or not isinstance(option, str) or not option:
            raise ValueError("answer-decision requiere params.request_id y params.option.")
        request.update({"decision": decision, "action": option})
    result = run_cli(["remote", project, req], request, root=_root_of(rdir))
    if result.get("status") == "OK":
        return {"messages": [str(result.get("message") or "enviado al runtime durable")],
                "durable": {k: result.get(k) for k in ("code", "sequence", "workflow_id", "workflow_checked")
                            if k in result}}
    message = str(result.get("message") or result.get("code") or "rechazado por el runtime durable")[:300]
    if result.get("status") == "REJECTED" and result.get("code") in ("STALE", "NOT_OPEN", "NOT_APPLICABLE"):
        raise DurableRejected(message)
    raise ValueError(message)


def _root_of(rdir: Path | str) -> Path | None:
    rdir = Path(rdir)
    return rdir.parent.parent.parent if rdir.parent.name == "requirements" else None


def cli() -> list[str]:
    """How to reach the uv environment: `execution.durable_cli` (an argv list), else `uv run --project <repo>` for a
    checkout, else `bt-durable` on PATH for a release copy that has no uv project next to it."""
    try:
        import bt_config
        configured = bt_config.get("execution.durable_cli")
    except Exception:  # noqa: BLE001 - an unreadable config falls back to the repository's own environment
        configured = None
    if isinstance(configured, list) and configured and all(isinstance(item, str) and item for item in configured):
        return list(configured)
    repo = Path(__file__).resolve().parents[2]
    installed = shutil.which("bt-durable")
    if not (repo / "pyproject.toml").is_file() and installed:   # a release copy without the uv project
        return [installed]
    uv = shutil.which("uv") or str(Path.home() / ".local" / "bin" / "uv")
    return [uv, "run", "--quiet", "--project", str(repo), "bt-durable"]


def run_cli(args: list[str], payload: dict | None = None, *, root: Path | None = None) -> dict[str, Any]:
    """Run `bt-durable <args>` with a JSON request on stdin and return its JSON answer (one object on stdout)."""
    env = dict(os.environ)
    if root is not None:
        env["BITACORA_ROOT"] = str(root)              # the CLI acts on the same bitácora as its caller
    try:
        done = subprocess.run([*cli(), *args], input=json.dumps(payload or {}), capture_output=True, text=True,
                              env=env, timeout=CLI_TIMEOUT, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise RuntimeError(f"bt-durable no respondió: {error}") from error
    lines = [line for line in done.stdout.splitlines() if line.strip().startswith("{")]
    try:
        result = json.loads(lines[-1]) if lines else None
    except ValueError:
        result = None
    if isinstance(result, dict):
        return result
    raise RuntimeError(f"bt-durable falló ({done.returncode}): {(done.stderr or done.stdout)[-300:]}")
