"""Command ledger for remote control: each command is stored once per idempotency key, with its precondition."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

COMMANDS = ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve", "launch",
            "answer-decision", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note")
ORIGINS = ("web", "telegram")
PRECONDITION_FIELDS = ("state", "revision", "updatedAt")   # what a precondition may pin on the target
_LOCK = threading.Lock()
_SCHEMA = """CREATE TABLE IF NOT EXISTS commands (
    idempotency_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, command TEXT NOT NULL, target TEXT NOT NULL,
    origin TEXT NOT NULL, params TEXT NOT NULL, precondition TEXT NOT NULL,
    status TEXT NOT NULL, code TEXT, outcome TEXT, received_at TEXT NOT NULL, finished_at TEXT)"""

Handler = Callable[[str, dict], Any]            # (target, params) -> JSON-able result; raises on failure
StateReader = Callable[..., "dict | None"]        # target[, command, params] -> current precondition fields


def default_path() -> Path:
    root = Path(os.environ.get("BITACORA_ROOT") or Path.home() / "bitacora")
    return root / ".state" / "remote" / "commands.db"


def _run_target(target: str) -> tuple[str, str, Path]:
    """Resolve a stable project/requirement target under the configured Bitácora root."""
    import bt_core
    import bt_plans_api

    project, separator, req = target.partition("/")
    if not separator or not project or "/" in req:
        raise ValueError("target debe tener el formato project/REQ-NNN.")
    rdir = bt_plans_api.req_dir(bt_core.ROOT, project, req)
    return project, req, rdir


def _member_state(rdir: Path, command: str, params: dict) -> str | None:
    """Read the state of the task or attempt that a task-scoped command mutates."""
    import sqlite3

    import bt_scheduler_adapter as adapter

    if command == "cancel-attempt":
        kind, key = "attempts", params.get("attempt")
    else:
        kind, key = "tasks", params.get("task")
    if not isinstance(key, str) or not key:
        return None
    path = adapter.run_db_path(rdir).resolve()
    try:
        conn = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True, timeout=5)
        try:
            row = conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()
            doc = json.loads(row[0]) if row else {}
        finally:
            conn.close()
    except (sqlite3.Error, TypeError, ValueError, OSError):
        return None
    member = (doc.get(kind) or {}).get(key)
    return member.get("state") if isinstance(member, dict) else None


TASK_SCOPED = frozenset(("retry", "reopen", "cancel-attempt"))


def target_state(target: str, command: str | None = None, params: dict | None = None) -> dict | None:
    """Resolve current run/member state for the ledger's optimistic precondition."""
    import bt_core
    import bt_plans_api
    import bt_scheduler_decisions

    try:
        project, req, rdir = _run_target(target)
        status = bt_plans_api.status_of(bt_core.ROOT, project, req)
    except (ValueError, bt_plans_api.PlanError, OSError):
        return None
    run = status.get("run") or {}
    if run.get("authority") != "scheduler":
        return None
    revision = (run.get("plan_ref") or {}).get("revision")
    state = run.get("status")
    params = params or {}
    if command in TASK_SCOPED:
        member_state = _member_state(rdir, command, params)
        if member_state is None:
            return None
        state = member_state
    elif command == "answer-decision":
        request_id = params.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            return None
        is_open = any(item.get("id") == request_id for item in bt_scheduler_decisions.open_requests(rdir))
        state = "open" if is_open else "closed"
    return {"state": state, "revision": revision, "updatedAt": run.get("updated_at")}


def dispatch_run_command(command: str, target: str, params: dict) -> Any:
    """Apply a remote run move through the existing Scheduler operator and decision APIs."""
    project, req, rdir = _run_target(target)
    import bt_scheduler_ops as ops

    reason = params.get("reason", "")
    if not isinstance(reason, str):
        raise ValueError("reason debe ser texto.")
    if command == "pause":
        with ops.hold(rdir, reason or "remote pause", keep=True):
            return {"messages": [f"owner stopped: {ops.stop_owner(project, req)} process(es)"]}
    if command == "resume":
        return {"messages": [ops.resume(project, req, rdir)]}
    if command in {"cancel-attempt", "reopen", "revise"}:
        if command == "cancel-attempt":
            target_id = params.get("attempt")
            if not isinstance(target_id, str) or not target_id:
                raise ValueError("cancel-attempt requiere params.attempt.")
        elif command == "reopen":
            target_id = params.get("task")
            if not isinstance(target_id, str) or not target_id:
                raise ValueError("reopen requiere params.task.")
        else:
            target_id = ""
        messages = ops.apply(project, req, rdir, command, target_id, reason)
        messages.append(ops.resume(project, req, rdir))
        return {"messages": messages}
    if command == "retry":
        task = params.get("task")
        if not isinstance(task, str) or not task:
            raise ValueError("retry requiere params.task.")
        if params.get("route"):
            raise ValueError("retry con route requiere el despachador de recuperación.")
        messages = ops.retry(project, req, rdir, task, reason)
        messages.append(ops.resume(project, req, rdir))
        return {"messages": messages}
    if command == "answer-decision":
        request_id, option = params.get("request_id"), params.get("option")
        if not isinstance(request_id, str) or not request_id or not isinstance(option, str) or not option:
            raise ValueError("answer-decision requiere params.request_id y params.option.")
        import bt_scheduler_decisions as decisions
        return {"messages": decisions.answer(project, req, rdir, request_id, option, reason, by="remote")}
    raise ValueError(f"Comando no implementado por el despachador de runs: {command}.")


def dispatch_handlers() -> dict[str, Handler]:
    """Build handlers for commands owned by the Scheduler run surface."""
    return {command: (lambda target, params, action=command: dispatch_run_command(action, target, params))
            for command in ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "answer-decision")}


def _read_state(state_of: StateReader, req: dict) -> dict | None:
    """Pass command context to readers that support member-scoped preconditions."""
    import inspect

    try:
        takes_context = len(inspect.signature(state_of).parameters) >= 3
    except (TypeError, ValueError):
        takes_context = False
    if takes_context:
        return state_of(req["target"], req["command"], req["params"])
    return state_of(req["target"])


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint(req: dict) -> str:
    """Digest of everything that changes the effect: a reused key with other content must not replay."""
    body = {k: req[k] for k in ("command", "target", "params", "precondition")}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def validate(req: Any) -> str | None:
    if not isinstance(req, dict):
        return "El comando debe ser un objeto JSON."
    key = req.get("idempotency_key")
    if not isinstance(key, str) or not 8 <= len(key) <= 120:
        return "idempotency_key debe ser texto de 8 a 120 caracteres."
    if req.get("command") not in COMMANDS:
        return "Comando desconocido."
    if not isinstance(req.get("target"), str) or not req["target"]:
        return "target es obligatorio."
    if req.get("origin") not in ORIGINS:
        return "origin debe ser web o telegram."
    pre = req.get("precondition")
    if not isinstance(pre, dict) or not pre or set(pre) - set(PRECONDITION_FIELDS) \
            or any(not isinstance(v, (str, int)) or isinstance(v, bool) for v in pre.values()):
        return "precondition debe fijar state, revision y/o updatedAt del objetivo."
    if not isinstance(req.get("params", {}), dict):
        return "params debe ser un objeto."
    return None


class Ledger:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute(_SCHEMA)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def rows(self) -> list[dict]:
        with self._db() as db:
            return [dict(r) for r in db.execute("SELECT * FROM commands ORDER BY received_at, rowid")]

    @staticmethod
    def _result(row: sqlite3.Row, replay: bool) -> dict:
        res = {"status": row["status"], "code": row["code"], "replayed": replay,
               "idempotency_key": row["idempotency_key"]}
        if row["outcome"] is not None:
            res["outcome"] = json.loads(row["outcome"])
        return res

    def submit(self, req: Any, handlers: dict[str, Handler], state_of: StateReader) -> dict:
        """Validate, reserve the key (PENDING), check the precondition, run the effect, then record the outcome.

        OK is written only after the effect returned. A row left PENDING (crash mid-effect) replays as
        UNKNOWN_OUTCOME and is never executed again.
        """
        problem = validate(req)
        if problem:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "message": problem, "stored": False}
        req = {**req, "params": req.get("params") or {}}
        if req["command"] not in handlers:
            return {"status": "REJECTED", "code": "COMMAND_NOT_IMPLEMENTED", "stored": False,
                    "message": "El comando aún no tiene ejecutor."}
        fp, key = fingerprint(req), req["idempotency_key"]
        with _LOCK:
            with self._db() as db:
                row = db.execute("SELECT * FROM commands WHERE idempotency_key=?", (key,)).fetchone()
                if row is not None:
                    if row["fingerprint"] != fp:
                        return {"status": "REJECTED", "code": "IDEMPOTENCY_CONFLICT", "stored": False,
                                "message": "La clave ya se usó con un contenido distinto."}
                    if row["status"] == "PENDING":
                        return {"status": "UNKNOWN", "code": "UNKNOWN_OUTCOME", "replayed": True,
                                "idempotency_key": key, "message": "El comando se interrumpió; verifica el destino."}
                    return self._result(row, True)
                db.execute("INSERT INTO commands VALUES (?,?,?,?,?,?,?,'PENDING',NULL,NULL,?,NULL)",
                           (key, fp, req["command"], req["target"], req["origin"],
                            json.dumps(req["params"], sort_keys=True), json.dumps(req["precondition"], sort_keys=True),
                            _now()))
            status, code, outcome = self._apply(req, handlers, state_of)
            with self._db() as db:
                db.execute("UPDATE commands SET status=?, code=?, outcome=?, finished_at=? WHERE idempotency_key=?",
                           (status, code, json.dumps(outcome, ensure_ascii=False), _now(), key))
                row = db.execute("SELECT * FROM commands WHERE idempotency_key=?", (key,)).fetchone()
            return self._result(row, False)

    @staticmethod
    def _apply(req: dict, handlers: dict[str, Handler], state_of: StateReader) -> tuple[str, str | None, Any]:
        try:
            current = _read_state(state_of, req)
        except Exception as exc:
            return "FAILED", "STATE_UNAVAILABLE", {"error": str(exc)[:300]}
        if not current or any(current.get(k) != v for k, v in req["precondition"].items()):
            return "REJECTED", "STALE_PRECONDITION", {"expected": req["precondition"],
                                                       "actual": {k: (current or {}).get(k) for k in PRECONDITION_FIELDS}}
        try:
            result = handlers[req["command"]](req["target"], req["params"])
        except Exception as exc:
            return "FAILED", "EFFECT_FAILED", {"error": str(exc)[:300]}
        return "OK", None, result
