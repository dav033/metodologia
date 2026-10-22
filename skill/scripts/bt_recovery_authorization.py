"""Durable, run-scoped recovery grants. This ledger never writes M1 state."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

SCHEMA = "recovery-authorization/1"
KINDS = {"task", "supplementary_audit", "conflict_bootstrap"}


class AuthorizationError(ValueError):
    """A grant is missing, stale, malformed or already consumed by another caller."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def _validate(kind: str, grant: dict[str, Any]) -> None:
    if kind not in KINDS or not isinstance(grant, dict):
        raise AuthorizationError("invalid grant kind or body")
    if any(not isinstance(key, str) for key in grant):
        raise AuthorizationError("grant field names must be strings")
    common = ("case_id", "case_hash", "cycle_token", "stop_generation")
    required = {
        "task": common + ("case_hash", "proposal_hash", "source_sha256", "target_sha256", "scope",
                          "accepted_map_digest", "base_digest"),
        "supplementary_audit": common + ("audit_lineage", "accepted_map_digest", "base_digest"),
        "conflict_bootstrap": common + ("order_id", "task_id", "plan_hash", "source_parents",
                                         "conflict_tree", "base", "marker_path_digest", "accepted_map_digest"),
    }[kind]
    if any(key not in grant for key in required):
        raise AuthorizationError(f"{kind} grant is missing required fields")
    if (not isinstance(grant["case_id"], str) or not grant["case_id"].strip()
            or not isinstance(grant["cycle_token"], str) or not grant["cycle_token"].strip()):
        raise AuthorizationError("case and cycle identities must be strings")
    if type(grant["stop_generation"]) is not int or grant["stop_generation"] < 0:
        raise AuthorizationError("stop_generation must be a non-negative integer")
    digests = [key for key in grant if key.endswith("_sha256") or key.endswith("_digest") or key in {"case_hash", "plan_hash", "base_digest"}]
    if any(not _valid_digest(grant[key]) for key in digests):
        raise AuthorizationError("grant contains an invalid digest")
    if kind == "task" and (not isinstance(grant["scope"], list) or not grant["scope"] or
                            any(not isinstance(item, str) or not item for item in grant["scope"]) or
                            len(grant["scope"]) != len(set(grant["scope"]))):
        raise AuthorizationError("task scope must be a non-empty list of task ids")
    if kind == "supplementary_audit" and (not isinstance(grant["audit_lineage"], str)
                                           or not grant["audit_lineage"].strip()):
        raise AuthorizationError("audit_lineage must be a string")
    if kind == "conflict_bootstrap":
        if (not isinstance(grant["order_id"], str) or not grant["order_id"].strip()
                or not isinstance(grant["task_id"], str) or not grant["task_id"].strip()):
            raise AuthorizationError("bootstrap order and task ids must be strings")
        if not isinstance(grant["source_parents"], list) or len(grant["source_parents"]) != 2 or \
                any(not _valid_digest(item) for item in grant["source_parents"]):
            raise AuthorizationError("bootstrap needs two source parent hashes")
        if any(not _valid_digest(grant[name]) for name in ("conflict_tree", "base", "marker_path_digest")):
            raise AuthorizationError("bootstrap contains an invalid captured digest")


def database_path(rdir: str | Path) -> Path:
    """Place the independent WAL database beside the authoritative Scheduler database."""
    import bt_scheduler_adapter

    return bt_scheduler_adapter.run_db_path(Path(rdir)).with_name("RUN.recovery-authorization.db")


class Ledger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE IF NOT EXISTS grants (grant_key TEXT PRIMARY KEY, kind TEXT NOT NULL, "
                         "body TEXT NOT NULL, consumed_by TEXT, consumed_at TEXT, UNIQUE(kind, grant_key))")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_audit_grant_per_lineage_cycle "
                         "ON grants(json_extract(body, '$.audit_lineage'), json_extract(body, '$.cycle_token')) "
                         "WHERE kind='supplementary_audit'")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_grant_per_case_cycle_kind "
                         "ON grants(kind, json_extract(body, '$.case_id'), json_extract(body, '$.cycle_token')) "
                         "WHERE kind IN ('task', 'conflict_bootstrap')")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    @staticmethod
    def key(kind: str, grant: dict[str, Any]) -> str:
        return hashlib.sha256((SCHEMA + "\0" + kind + "\0" + _canonical(grant)).encode()).hexdigest()

    def issue(self, kind: str, grant: dict[str, Any]) -> str:
        _validate(kind, grant)
        key = self.key(kind, grant)
        body = _canonical(grant)
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                existing = conn.execute("SELECT body FROM grants WHERE grant_key=?", (key,)).fetchone()
                if existing and existing[0] != body:
                    raise AuthorizationError("grant key collision")
                conn.execute("INSERT OR IGNORE INTO grants(grant_key,kind,body) VALUES(?,?,?)", (key, kind, body))
                if conn.execute("SELECT changes()").fetchone()[0] == 0 and not existing:
                    raise AuthorizationError("a grant already exists for this case, lineage or cycle")
                conn.execute("COMMIT")
            except sqlite3.IntegrityError as exc:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise AuthorizationError("a grant already exists for this case, lineage or cycle") from exc
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        return key

    def issue_task_grant(self, grant: dict[str, Any]) -> str:
        return self.issue("task", grant)

    def issue_supplementary_audit_grant(self, grant: dict[str, Any]) -> str:
        return self.issue("supplementary_audit", grant)

    def issue_conflict_bootstrap_grant(self, grant: dict[str, Any]) -> str:
        return self.issue("conflict_bootstrap", grant)

    def get(self, kind: str, key: str) -> dict[str, Any]:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT body FROM grants WHERE kind=? AND grant_key=?", (kind, key)).fetchone()
        if row is None:
            raise AuthorizationError("grant not found")
        result = json.loads(row[0])
        _validate(kind, result)
        if self.key(kind, result) != key:
            raise AuthorizationError("grant record digest was tampered")
        return result

    def consume(self, kind: str, key: str, consumer: str, identities: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(consumer, str) or not consumer.strip():
            raise AuthorizationError("consumer identity is required")
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT body,consumed_by FROM grants WHERE kind=? AND grant_key=?", (kind, key)).fetchone()
                if row is None:
                    raise AuthorizationError("grant not found")
                grant = json.loads(row[0])
                _validate(kind, grant)
                if self.key(kind, grant) != key:
                    raise AuthorizationError("grant record digest was tampered")
                if identities is not None:
                    if not isinstance(identities, dict) or any(grant.get(name) != value for name, value in identities.items()):
                        raise AuthorizationError("grant identities are stale")
                if row[1] not in (None, consumer):
                    raise AuthorizationError("grant was consumed by another consumer")
                if row[1] is None:
                    conn.execute("UPDATE grants SET consumed_by=?, consumed_at=datetime('now') WHERE kind=? AND grant_key=?",
                                 (consumer, kind, key))
                conn.execute("COMMIT")
                return grant
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def consume_bootstrap(self, order: dict[str, Any], identities: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(order, dict) or not isinstance(identities, dict):
            raise AuthorizationError("bootstrap identities are required")
        key = order.get("grant_key")
        grant = self.get("conflict_bootstrap", key)
        expected = {"order_id": order.get("order_id"), "task_id": order.get("task_id"),
                    "plan_hash": identities.get("plan_hash"), "case_id": identities.get("case_id"),
                    "cycle_token": identities.get("cycle_token"), "accepted_map_digest": identities.get("accepted_map_digest"),
                    "stop_generation": identities.get("stop_generation")}
        if any(grant.get(name) != value for name, value in expected.items()):
            raise AuthorizationError("bootstrap identity or stop generation is stale")
        if order.get("source_parents") != grant["source_parents"] or order.get("conflict_tree") != grant["conflict_tree"] or \
                order.get("base") != grant["base"] or order.get("marker_path_digest") != grant["marker_path_digest"]:
            raise AuthorizationError("bootstrap digest or source parent was tampered")
        return self.consume("conflict_bootstrap", key, "order:" + str(order["order_id"]))


def open_for_run(rdir: str | Path) -> Ledger:
    return Ledger(database_path(rdir))
