"""Command ledger for remote control: each command is stored once per idempotency key, with its precondition."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import secrets
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

COMMANDS = ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve", "launch",
            "answer-decision", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note")
CHALLENGED = frozenset(("revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"))
ORIGINS = ("web", "telegram")
PRECONDITION_FIELDS = ("state", "revision", "updatedAt")   # what a precondition may pin on the target
# Covers key reservation, state precondition, effect, and outcome write as one process-local critical section.
_EFFECT_LOCK = threading.Lock()
_SCHEMA = """CREATE TABLE IF NOT EXISTS commands (
    idempotency_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, command TEXT NOT NULL, target TEXT NOT NULL,
    origin TEXT NOT NULL, params TEXT NOT NULL, precondition TEXT NOT NULL,
    status TEXT NOT NULL, code TEXT, outcome TEXT, received_at TEXT NOT NULL, finished_at TEXT)"""
_CHALLENGE_SCHEMA = """CREATE TABLE IF NOT EXISTS challenges (
    challenge_hash TEXT PRIMARY KEY, target TEXT NOT NULL, expires_at REAL NOT NULL, used_at TEXT)"""

Handler = Callable[[str, dict], Any]            # (target, params) -> JSON-able result; raises on failure
StateReader = Callable[..., "dict | None"]        # target[, command, params] -> current precondition fields


class RouteUnavailableError(ValueError):
    """A requested retry pin has no currently eligible Scheduler route."""


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
    plan = status.get("plan") or {}
    params = params or {}
    if command == "answer-round":
        round_number = params.get("round")
        if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
            return None
        try:
            import bt_rounds
            round_data = bt_rounds.load(rdir / "rounds" / f"round-{round_number:02d}.json")
        except (OSError, ValueError):
            return None
        if round_data.get("round") != round_number or round_data.get("status") != "open":
            return None
        return {"state": "open", "revision": round_data.get("revision")}
    if command in {"approve", "launch", "cancel-plan", "delete-plan"}:
        try:
            updated_at = dt.datetime.fromtimestamp((rdir / "PLAN.md").stat().st_mtime, dt.UTC).isoformat(
                timespec="microseconds")
        except OSError:
            updated_at = None
        return {"state": plan.get("status"), "revision": plan.get("revision"), "updatedAt": updated_at}
    if run.get("authority") != "scheduler":
        return None
    revision = (run.get("plan_ref") or {}).get("revision")
    state = run.get("status")
    if command in TASK_SCOPED:
        member_state = _member_state(rdir, command, params)
        if member_state is None:
            return None
        state = member_state
    elif command == "answer-decision":
        request_id = params.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            return None
        request = next((item for item in bt_scheduler_decisions.open_requests(rdir)
                        if item.get("id") == request_id), None)
        if request is None:
            return None
        return {"state": "open", **({"revision": request["revision"]}
                                     if isinstance(request.get("revision"), int) else {})}
    return {"state": state, "revision": revision, "updatedAt": run.get("updated_at")}


def dispatch_run_command(command: str, target: str, params: dict) -> Any:
    """Apply a remote run move through the existing Scheduler operator and decision APIs."""
    project, req, rdir = _run_target(target)
    import bt_scheduler_ops as ops

    if command == "revise":
        typed_req = params.get("typed_req")
        if not isinstance(typed_req, str) or typed_req.strip().upper() != req.upper():
            raise ValueError("revise requiere confirmar el id REQ del objetivo.")
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
        import bt_route_pins
        pin = bt_route_pins.normalize(params)
        if pin is not None:
            # Check the exact candidate set before ops.retry can reopen the task. This also fails closed when
            # quota refresh or account identity is unavailable.
            candidates = bt_route_pins.available(project, rdir, task, pin)
            if not candidates:
                raise RouteUnavailableError("La ruta fijada no está disponible; la tarea no se reabrió.")
            bt_route_pins.set_pin(rdir, task, pin)
        else:
            bt_route_pins.clear(rdir, task)
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


def dispatch_edit_brief(target: str, params: dict) -> Any:
    """Edit and approve a plan revision before rebasing its active run."""
    import bt_remote_edit
    return bt_remote_edit.dispatch_edit_brief(target, params)


def dispatch_plan_command(command: str, target: str, params: dict) -> Any:
    """Apply plan lifecycle and round answers through the existing file APIs."""
    project, req, rdir = _run_target(target)
    import bt_core
    import bt_plans_api as plans
    import bt_rounds

    reason = params.get("reason", "")
    if not isinstance(reason, str):
        raise ValueError("reason debe ser texto.")
    if command in {"approve", "launch"}:
        return {"message": plans.run_plan(bt_core.ROOT, project, req, command, by="remote")}
    if command == "cancel-plan":
        return {"message": plans.cancel_plan(bt_core.ROOT, project, req, params.get("typed_req", ""), by="remote")}
    if command == "delete-plan":
        return {"message": plans.delete_plan(bt_core.ROOT, project, req, params.get("typed_req", ""), by="remote",
                                               reason=reason)}
    if command == "answer-round":
        round_number, answers = params.get("round"), params.get("answers")
        if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
            raise ValueError("answer-round requiere params.round.")
        if not isinstance(answers, dict) or not answers:
            raise ValueError("answer-round requiere params.answers.")
        path = rdir / "rounds" / f"round-{round_number:02d}.json"
        data = bt_rounds.load(path)
        if data.get("status") != "open" or data.get("round") != round_number:
            raise ValueError("La ronda ya no está abierta.")
        saved = bt_rounds.answer_round(path, answers, "remote")
        return {"round": round_number, "status": saved["status"], "answers": saved["answers"]}
    raise ValueError(f"Comando no implementado por el despachador de planes: {command}.")


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
    params = req.get("params", {})
    pin_fields = {"route", "model", "account"}
    if req["command"] == "retry":
        for field in pin_fields & params.keys():
            value = params[field]
            if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
                return f"params.{field} debe ser texto no vacío de hasta 200 caracteres."
    elif pin_fields & params.keys():
        return "route, model y account solo se admiten en retry."
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

    def history(self, after: str = "", limit: int = 100) -> tuple[list[dict], str]:
        """Return a bounded, cursor-based public history without command parameters or preconditions."""
        if after and not re.fullmatch(r"cmd_[0-9]{1,18}", after):
            raise ValueError("El cursor no es válido.")
        columns = "rowid, idempotency_key, command, target, origin, status, code, received_at, finished_at"
        with self._db() as db:
            if after:
                rows = db.execute(f"SELECT {columns} FROM commands WHERE rowid>? ORDER BY rowid LIMIT ?",
                                  (int(after[4:]), limit)).fetchall()
            else:
                rows = db.execute(f"SELECT {columns} FROM (SELECT {columns} FROM commands ORDER BY rowid DESC LIMIT ?) "
                                  "ORDER BY rowid", (limit,)).fetchall()
        items = [{"id": row["idempotency_key"], "command": row["command"], "target": row["target"],
                  "origin": row["origin"], "submittedAt": row["received_at"], "finishedAt": row["finished_at"],
                  "result": row["code"] or row["status"]} for row in rows]
        return items, f"cmd_{rows[-1]['rowid']}" if rows else after

    def issue_challenge(self, target: str, typed_req: str, now: float | None = None) -> dict:
        """Issue a one-use, target-bound challenge after the caller types the target REQ id."""
        match = re.fullmatch(r"[^/]+/(REQ-\d+)", target) if isinstance(target, str) else None
        if not match or not isinstance(typed_req, str) or typed_req.strip().upper() != match.group(1):
            raise ValueError("Escribe el id REQ del objetivo para confirmar.")
        challenge_id = secrets.token_urlsafe(32)
        challenge_hash = hashlib.sha256(challenge_id.encode()).hexdigest()
        issued = dt.datetime.now(dt.timezone.utc).timestamp() if now is None else now
        with self._db() as db:
            db.execute("DELETE FROM challenges WHERE expires_at<? OR used_at IS NOT NULL", (issued,))
            db.execute("INSERT INTO challenges (challenge_hash,target,expires_at,used_at) VALUES (?,?,?,NULL)",
                       (challenge_hash, target, issued + 120))
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
        if req.get("command") not in COMMANDS:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "message": validate(req), "stored": False}
        # Serialize the state check, challenge consumption, reservation, effect, and outcome write.
        # This keeps two concurrent commands from both acting on the same stale state.
        with _EFFECT_LOCK:
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

            try:
                current = _read_state(state_of, req)
            except Exception as exc:
                return {"status": "FAILED", "code": "STATE_UNAVAILABLE", "stored": False,
                        "message": str(exc)[:300]}
            if not current or not _matches_precondition(req, current):
                outcome = {"message": "La precondición del objetivo ya no se cumple."}
                with self._db() as db:
                    db.execute("INSERT INTO commands VALUES (?,?,?,?,?,?,?,'REJECTED','STALE_PRECONDITION',?,?,?)",
                               (key, fp, req["command"], req["target"], req["origin"],
                                json.dumps(req["params"], sort_keys=True),
                                json.dumps(req["precondition"], sort_keys=True), json.dumps(outcome),
                                _now(), _now()))
                    row = db.execute("SELECT * FROM commands WHERE idempotency_key=?", (key,)).fetchone()
                return self._result(row, False)

            confirmation = req.get("confirmation")
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                if req["command"] in CHALLENGED:
                    challenge_id = confirmation.get("challenge_id", confirmation.get("challengeId"))
                    typed_req = confirmation.get("typed_req", confirmation.get("typedReq", "")).strip().upper()
                    expected_req = req["target"].rsplit("/", 1)[-1].upper()
                    challenge_hash = hashlib.sha256(challenge_id.encode()).hexdigest()
                    challenge = db.execute("SELECT * FROM challenges WHERE challenge_hash=?",
                                           (challenge_hash,)).fetchone()
                    now = dt.datetime.now(dt.timezone.utc).timestamp()
                    if (typed_req != expected_req or challenge is None or challenge["target"] != req["target"]
                            or challenge["used_at"] is not None or challenge["expires_at"] < now):
                        return {"status": "REJECTED", "code": "CONFIRMATION_REQUIRED", "stored": False,
                                "message": "El desafío falta, venció, ya se usó o no corresponde al objetivo."}
                    db.execute("UPDATE challenges SET used_at=? WHERE challenge_hash=? AND used_at IS NULL",
                               (_now(), challenge_hash))
                db.execute("INSERT INTO commands VALUES (?,?,?,?,?,?,?,'PENDING',NULL,NULL,?,NULL)",
                           (key, fp, req["command"], req["target"], req["origin"],
                            json.dumps(req["params"], sort_keys=True), json.dumps(req["precondition"], sort_keys=True),
                            _now()))

            params = dict(req["params"])
            if req["command"] in CHALLENGED:
                params["typed_req"] = confirmation.get("typed_req", confirmation.get("typedReq"))
            try:
                outcome = handlers[req["command"]](req["target"], params)
                status, code = "OK", None
            except RouteUnavailableError as exc:
                outcome, status, code = {"error": str(exc)[:300]}, "FAILED", "ROUTE_UNAVAILABLE"
            except Exception as exc:
                outcome, status, code = {"error": str(exc)[:300]}, "FAILED", "EFFECT_FAILED"
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
        if not current or not _matches_precondition(req, current):
            return "REJECTED", "STALE_PRECONDITION", {"expected": req["precondition"],
                                                       "actual": {k: (current or {}).get(k) for k in PRECONDITION_FIELDS}}
        try:
            result = handlers[req["command"]](req["target"], req["params"])
        except Exception as exc:
            return "FAILED", "EFFECT_FAILED", {"error": str(exc)[:300]}
        return "OK", None, result


def _matches_precondition(req: dict, current: dict) -> bool:
    """Treat the review label as the public equivalent of the scheduler's recoverable state for reopen."""
    expected = req["precondition"]
    if all(current.get(field) == value for field, value in expected.items()):
        return True
    return (req["command"] == "reopen" and expected.get("state") == "rejected"
            and current.get("state") == "recovering"
            and all(current.get(field) == value for field, value in expected.items() if field != "state"))
