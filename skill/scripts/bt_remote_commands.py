"""Command ledger for remote control: each command is stored once per idempotency key, with its precondition."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

COMMANDS = ("pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve", "launch",
            "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note")
ORIGINS = ("web", "telegram")
PRECONDITION_FIELDS = ("state", "revision", "updatedAt")   # what a precondition may pin on the target
_LOCK = threading.Lock()
_SCHEMA = """CREATE TABLE IF NOT EXISTS commands (
    idempotency_key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, command TEXT NOT NULL, target TEXT NOT NULL,
    origin TEXT NOT NULL, params TEXT NOT NULL, precondition TEXT NOT NULL,
    status TEXT NOT NULL, code TEXT, outcome TEXT, received_at TEXT NOT NULL, finished_at TEXT)"""

Handler = Callable[[str, dict], Any]            # (target, params) -> JSON-able result; raises on failure
StateReader = Callable[[str], "dict | None"]    # target -> {"state", "revision", "updatedAt"} or None if absent


def default_path() -> Path:
    root = Path(os.environ.get("BITACORA_ROOT") or Path.home() / "bitacora")
    return root / ".state" / "remote" / "commands.db"


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

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        return db

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
            current = state_of(req["target"])
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
