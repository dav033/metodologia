"""Command ledger for remote control: each command is stored once per idempotency key, with its precondition."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import tempfile
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

COMMANDS = ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "answer-decision",
            "approve", "launch", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note")
CHALLENGED = frozenset(("revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"))
ORIGINS = ("web", "telegram")
PRECONDITION_FIELDS = ("state", "revision", "updatedAt")   # what a precondition may pin on the target
_LOCK = threading.Lock()
_SCHEMA = """CREATE TABLE IF NOT EXISTS commands (
    idempotency_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, command TEXT NOT NULL, target TEXT NOT NULL,
    origin TEXT NOT NULL, params TEXT NOT NULL, precondition TEXT NOT NULL,
    status TEXT NOT NULL, code TEXT, outcome TEXT, received_at TEXT NOT NULL, finished_at TEXT)"""
_CHALLENGE_SCHEMA = """CREATE TABLE IF NOT EXISTS challenges (
    challenge_hash TEXT PRIMARY KEY, target TEXT NOT NULL, expires_at REAL NOT NULL, used_at TEXT)"""

Handler = Callable[[str, dict], Any]            # (target, params) -> JSON-able result; raises on failure
StateReader = Callable[[str], "dict | None"]    # target -> {"state", "revision", "updatedAt"} or None if absent


def default_path() -> Path:
    root = Path(os.environ.get("BITACORA_ROOT") or Path.home() / "bitacora")
    return root / ".state" / "remote" / "commands.db"


def _run_target(target: str) -> tuple[str, str, Path]:
    """Resolve the stable remote run target `project/REQ-NNN` beneath the configured bitácora root."""
    import bt_core
    import bt_plans_api

    project, separator, req = target.partition("/")
    if not separator or not project or "/" in req:
        raise ValueError("target debe tener el formato project/REQ-NNN.")
    rdir = bt_plans_api.req_dir(bt_core.ROOT, project, req)
    return project, req, rdir


def _member_state(rdir: Path, command: str, params: dict) -> str | None:
    """State of the task/attempt a task-scoped command mutates.

    "" when the run database cannot be read (the caller keeps the run state), None when the member is absent."""
    import json as _json
    import sqlite3
    import bt_scheduler_adapter as adapter

    kind, key = (("attempts", params.get("attempt")) if command == "cancel-attempt"
                 else ("tasks", params.get("task")))
    if not isinstance(key, str) or not key:
        return ""
    try:
        conn = sqlite3.connect(f"{adapter.run_db_path(rdir).resolve().as_uri()}?mode=ro", uri=True, timeout=5)
        try:
            doc = _json.loads(conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()[0])
        finally:
            conn.close()
    except (sqlite3.Error, TypeError, ValueError, OSError):
        return ""
    row = (doc.get(kind) or {}).get(key)
    return row.get("state") if isinstance(row, dict) else None


TASK_SCOPED = frozenset(("retry", "reopen", "cancel-attempt"))


def target_state(target: str, command: str | None = None, params: dict | None = None) -> dict | None:
    """Return the same public run-state vocabulary used by the plans read model.

    Task-scoped commands (retry, reopen, cancel-attempt) get the state of the task/attempt they mutate.
    """
    import bt_core
    import bt_plans_api

    try:
        project, req, rdir = _run_target(target)
        status = bt_plans_api.status_of(bt_core.ROOT, project, req)
    except (ValueError, bt_plans_api.PlanError, OSError):
        return None
    run = status["run"]
    if not isinstance(run, dict):
        return None
    if command in {"answer-decision", "answer-round"}:
        import bt_remote_preconditions
        return bt_remote_preconditions.planning_target_state(rdir, command, params)
    # Plan commands pin the current plan revision; run commands pin the revision used by the live run.
    plan = status.get("plan") or {}
    revision = (run.get("plan_ref") or {}).get("revision")
    if run.get("authority") == "scheduler":
        run_state = run.get("status")
        if command in TASK_SCOPED:
            member = _member_state(rdir, command, params or {})
            if member is None:
                return None
            run_state = member or run_state
        return {"state": run_state, "revision": revision if revision is not None else plan.get("revision"),
                "updatedAt": run.get("updated_at"), "plan_state": plan.get("status"),
                "plan_revision": plan.get("revision"), "plan_updatedAt": _plan_updated_at(rdir)}
    try:
        updated_at = dt.datetime.fromtimestamp((rdir / "PLAN.md").stat().st_mtime, dt.UTC).isoformat(
            timespec="microseconds")
    except OSError:
        updated_at = None
    return {"state": plan.get("status"), "revision": plan.get("revision"), "updatedAt": updated_at}


def _plan_updated_at(rdir: Path) -> str | None:
    try:
        return dt.datetime.fromtimestamp((rdir / "PLAN.md").stat().st_mtime, dt.UTC).isoformat(
            timespec="microseconds")
    except OSError:
        return None


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
            attempt = params.get("attempt")
            if not isinstance(attempt, str) or not attempt:
                raise ValueError("cancel-attempt requiere params.attempt.")
            target_id = attempt
        elif command == "reopen":
            task = params.get("task")
            if not isinstance(task, str) or not task:
                raise ValueError("reopen requiere params.task.")
            target_id = task
        else:
            target_id = ""
        messages = ops.apply(project, req, rdir, command, target_id, reason)
        messages.append(ops.resume(project, req, rdir))
        return {"messages": messages}
    if command == "retry":
        task = params.get("task")
        if not isinstance(task, str) or not task:
            raise ValueError("retry requiere params.task.")
        task = ops.bound_plan(rdir).task(task).id
        route = params.get("route")
        if route is None and any(key in params for key in ("provider", "model", "account", "profile")):
            route = {key: params[key] for key in ("provider", "model", "account", "profile") if key in params}
        if route is not None:
            import bt_remote_recovery as recovery
            pin = recovery.validate_pin(route)
            recovery.validate_available(project, rdir, task, pin)
            recovery.write_pin(rdir, task, pin)
        note = params.get("reason", "")
        if note.strip():
            import bt_scheduler_decisions as decisions
            path = decisions.notes_path(rdir, task)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(note.strip() + "\n", encoding="utf-8")
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
    handlers = {command: (lambda target, params, action=command: dispatch_run_command(action, target, params))
                for command in ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "answer-decision")}
    handlers.update({command: (lambda target, params, action=command: dispatch_plan_command(action, target, params))
                     for command in ("approve", "launch", "answer-round", "cancel-plan", "delete-plan")})
    handlers["edit-brief"] = dispatch_edit_brief
    return handlers


def _write_plan_atomically(path: Path, content: str) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def dispatch_edit_brief(target: str, params: dict) -> Any:
    """Owner-edit task scope, freeze it as an approved revision, then rebase the active run."""
    project, req, rdir = _run_target(target)
    typed_req = params.get("typed_req")
    if not isinstance(typed_req, str) or typed_req.strip().upper() != req.upper():
        raise ValueError("edit-brief requiere confirmar el id REQ del objetivo.")
    task_id = params.get("task")
    field = params.get("field", "objective")
    value = params.get("value", params.get("brief"))
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("edit-brief requiere params.task.")
    if not isinstance(field, str):
        raise ValueError("edit-brief requiere un campo válido.")
    fields = {"brief": "objective", "criteria": "acceptance_criteria"}
    field = fields.get(field, field)
    if field not in {"objective", "acceptance_criteria"}:
        raise ValueError("edit-brief solo puede cambiar objective o acceptance_criteria.")
    if field == "objective" and (not isinstance(value, str) or not value.strip()):
        raise ValueError("edit-brief requiere un brief de tarea no vacío.")
    if field == "acceptance_criteria" and (not isinstance(value, list) or not value
                                             or any(not isinstance(item, str) or not item.strip() for item in value)):
        raise ValueError("edit-brief requiere una lista no vacía de criterios.")
    reason = params.get("reason", "Owner edited task brief")
    if not isinstance(reason, str):
        raise ValueError("reason debe ser texto.")

    from bt_planner import contract as plan_contract
    from bt_planner import revisions, sync

    current_path = rdir / "PLAN.json"
    if current_path.is_symlink() or not current_path.is_file():
        raise ValueError("PLAN.json debe ser un archivo regular para editarlo desde remoto.")
    original = current_path.read_bytes()
    latest = revisions.latest(rdir)
    if latest is None:
        raise ValueError("edit-brief requiere una revisión congelada para crear N+1.")
    frozen = revisions.load_revision(rdir, latest["revision"])
    current = plan_contract.load(current_path)
    if current.get("revision") != latest["revision"] or revisions.sha256(plan_contract.dumps(current)) != latest["sha256"]:
        raise ValueError("PLAN.json cambió desde la última revisión aprobada; no se aplicó el cambio.")
    edited = json.loads(json.dumps(frozen))
    task = next((item for item in edited.get("tasks", []) if item.get("id") == task_id), None)
    if task is None:
        raise ValueError(f"Tarea desconocida en la revisión {latest['revision']}: {task_id}.")
    task[field] = value
    edited["revision"] = latest["revision"] + 1
    content = plan_contract.dumps(edited)
    _write_plan_atomically(current_path, content)
    try:
        entry = sync.approve_freeze(rdir, req)
    except BaseException:
        _write_plan_atomically(current_path, original.decode("utf-8"))
        raise

    import bt_scheduler_ops as ops
    messages = ops.apply(project, req, rdir, "revise", "", reason)
    messages.append(ops.resume(project, req, rdir))
    return {"revision": entry["revision"], "sha256": entry["sha256"], "messages": messages}


def dispatch_plan_command(command: str, target: str, params: dict) -> Any:
    """Apply a plan or round command through the existing plan and round APIs."""
    project, req, rdir = _run_target(target)
    import bt_plans_api as plans
    import bt_rounds
    import bt_core

    reason = params.get("reason", "")
    if not isinstance(reason, str):
        raise ValueError("reason debe ser texto.")
    if command in {"approve", "launch"}:
        return {"message": plans.run_plan(bt_core.ROOT, project, req, command, by="remote")}
    if command == "cancel-plan":
        return {"message": plans.cancel_plan(bt_core.ROOT, project, req, params["typed_req"], by="remote")}
    if command == "delete-plan":
        return {"message": plans.delete_plan(bt_core.ROOT, project, req, params["typed_req"], by="remote",
                                                reason=reason)}
    if command == "answer-round":
        round_number, answers = params.get("round"), params.get("answers")
        if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
            raise ValueError("answer-round requiere params.round.")
        if not isinstance(answers, dict) or not answers:
            raise ValueError("answer-round requiere params.answers.")
        f = rdir / "rounds" / f"round-{round_number:02d}.json"
        data = bt_rounds.load(f)
        if data.get("status") != "open" or data.get("round") != round_number:
            raise ValueError("La ronda ya no está abierta.")
        return {"round": round_number, "status": "answered",
                "answers": bt_rounds.answer_round(f, answers, "remote")["answers"]}
    raise ValueError(f"Comando no implementado por el despachador de planes: {command}.")


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fingerprint(req: dict) -> str:
    """Digest of everything that changes the effect: a reused key with other content must not replay."""
    body = {k: v for k, v in req.items() if k != "idempotency_key"}
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
    if set(req) - {"idempotency_key", "command", "target", "origin", "params", "precondition", "confirmation"}:
        return "El comando contiene campos no reconocidos."
    if req["command"] in CHALLENGED:
        confirmation = req.get("confirmation")
        if not isinstance(confirmation, dict) or set(confirmation) not in (
                {"challenge_id", "typed_req"}, {"challengeId", "typedReq"}) \
                or not isinstance(confirmation.get("challenge_id", confirmation.get("challengeId")), str) \
                or not isinstance(confirmation.get("typed_req", confirmation.get("typedReq")), str):
            return "El comando requiere un desafío de confirmación válido."
    elif "confirmation" in req:
        return "Este comando no admite desafíos de confirmación."
    return None


def _read_state(state_of: StateReader, req: dict) -> dict | None:
    """Call the reader with command and params when it accepts them (task/attempt-scoped preconditions)."""
    import inspect

    try:
        takes = len(inspect.signature(state_of).parameters) >= 3
    except (TypeError, ValueError):
        takes = False
    return state_of(req["target"], req["command"], req["params"]) if takes else state_of(req["target"])


class Ledger:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute(_SCHEMA)
            db.execute(_CHALLENGE_SCHEMA)

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

    def issue_challenge(self, target: str, typed_req: str, now: float | None = None) -> dict:
        """Issue a one-use target-bound challenge after the caller types the target REQ id."""
        match = re.fullmatch(r"[^/]+/(REQ-\d+)", target)
        if not match or not isinstance(typed_req, str) or typed_req.strip().upper() != match.group(1):
            raise ValueError("Escribe el id REQ del objetivo para confirmar.")
        challenge_id = secrets.token_urlsafe(32)
        challenge_hash = hashlib.sha256(challenge_id.encode()).hexdigest()
        issued_at = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
        with self._db() as db:
            db.execute("DELETE FROM challenges WHERE expires_at<? OR used_at IS NOT NULL", (issued_at,))
            db.execute("INSERT INTO challenges (challenge_hash,target,expires_at,used_at) VALUES (?,?,?,NULL)",
                       (challenge_hash, target, issued_at + 120))
        return {"challengeId": challenge_id, "target": target, "expiresIn": 120}

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
        if not isinstance(req, dict):
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "message": validate(req), "stored": False}
        req = {**req, "params": req.get("params") or {}}
        key = req.get("idempotency_key")
        if not isinstance(key, str) or not 8 <= len(key) <= 120:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "message": validate(req), "stored": False}
        try:
            fp = fingerprint(req)
        except (TypeError, ValueError):
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "message": "El comando no es JSON válido.",
                    "stored": False}
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
        problem = validate(req)
        if problem:
            code = "CONFIRMATION_REQUIRED" if req.get("command") in CHALLENGED else "INVALID_COMMAND"
            return {"status": "REJECTED", "code": code, "message": problem, "stored": False}
        if req["command"] not in handlers:
            return {"status": "REJECTED", "code": "COMMAND_NOT_IMPLEMENTED", "stored": False,
                    "message": "El comando aún no tiene ejecutor."}
        fp, key = fingerprint(req), req["idempotency_key"]
        with _LOCK:
            # Existing keys replay before challenge validation: retrying a timed-out request remains safe.
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
            try:
                current = _read_state(state_of, req)
            except Exception as exc:
                return {"status": "FAILED", "code": "STATE_UNAVAILABLE", "stored": False,
                        "message": str(exc)[:300]}
            if req["command"] in {"approve", "launch", "cancel-plan", "delete-plan"} and current:
                current = {**current, "state": current.get("plan_state", current.get("state")),
                           "revision": current.get("plan_revision", current.get("revision")),
                           "updatedAt": current.get("plan_updatedAt", current.get("updatedAt"))}
            if not current or any(current.get(k) != v for k, v in req["precondition"].items()):
                return {"status": "REJECTED", "code": "STALE_PRECONDITION", "stored": False,
                        "message": "La precondición del objetivo ya no se cumple."}
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT * FROM commands WHERE idempotency_key=?", (key,)).fetchone()
                if row is not None:
                    if row["fingerprint"] != fp:
                        return {"status": "REJECTED", "code": "IDEMPOTENCY_CONFLICT", "stored": False,
                                "message": "La clave ya se usó con un contenido distinto."}
                    return self._result(row, True) if row["status"] != "PENDING" else {
                        "status": "UNKNOWN", "code": "UNKNOWN_OUTCOME", "replayed": True,
                        "idempotency_key": key, "message": "El comando se interrumpió; verifica el destino."}
                if req["command"] in CHALLENGED:
                    challenge = req["confirmation"]
                    challenge_id = challenge.get("challenge_id", challenge.get("challengeId"))
                    typed_req = challenge.get("typed_req", challenge.get("typedReq", "")).strip().upper()
                    expected = req["target"].rsplit("/", 1)[-1].upper()
                    challenge_hash = hashlib.sha256(challenge_id.encode()).hexdigest()
                    record = db.execute("SELECT * FROM challenges WHERE challenge_hash=?", (challenge_hash,)).fetchone()
                    now = dt.datetime.now(dt.timezone.utc).timestamp()
                    if (typed_req != expected or not record or record["target"] != req["target"]
                            or record["used_at"] is not None or record["expires_at"] < now):
                        return {"status": "REJECTED", "code": "CONFIRMATION_REQUIRED", "stored": False,
                                "message": "El desafío falta, venció, ya se usó o no corresponde al objetivo."}
                    db.execute("UPDATE challenges SET used_at=? WHERE challenge_hash=? AND used_at IS NULL",
                               (_now(), challenge_hash))
                db.execute("INSERT INTO commands VALUES (?,?,?,?,?,?,?,'PENDING',NULL,NULL,?,NULL)",
                           (key, fp, req["command"], req["target"], req["origin"],
                            json.dumps(req["params"], sort_keys=True), json.dumps(req["precondition"], sort_keys=True),
                            _now()))
            effective = dict(req["params"])
            if req["command"] in CHALLENGED:
                effective["typed_req"] = req["confirmation"].get(
                    "typed_req", req["confirmation"].get("typedReq"))
            try:
                outcome = handlers[req["command"]](req["target"], effective)
                status, code = "OK", None
            except Exception as exc:
                outcome, status, code = {"error": str(exc)[:300]}, "FAILED", "EFFECT_FAILED"
            with self._db() as db:
                db.execute("UPDATE commands SET status=?, code=?, outcome=?, finished_at=? WHERE idempotency_key=?",
                           (status, code, json.dumps(outcome, ensure_ascii=False), _now(), key))
                row = db.execute("SELECT * FROM commands WHERE idempotency_key=?", (key,)).fetchone()
            return self._result(row, False)
