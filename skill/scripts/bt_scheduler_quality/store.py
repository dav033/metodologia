"""Private, durable SQLite ledger for M6 requests, evidence, reviews and verdict delivery."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sqlite3
import stat
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, Self

from .contracts import QualityError, VerifyRequest
from .evidence import canonical_json, finished_at, read_result
from .check_history import CHECK_HISTORY_SCHEMA, CheckHistory
from .recovery import requeue_after_clean_stop, retry_attested, retry_interrupted, retry_m5_transient

_SCHEMA_VERSION = 2


class QualityStore:
    def __init__(self, path: str | Path):
        raw_path = str(path)
        self._memory = raw_path == ":memory:"
        self.path = Path(raw_path) if not self._memory else None
        self._lock = threading.RLock()
        self._lock_fd: int | None = None
        if self._memory:
            self._connection = sqlite3.connect(
                ":memory:", isolation_level=None, check_same_thread=False
            )
        else:
            assert self.path is not None
            parent = self.path.parent
            parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            if stat.S_IMODE(parent.stat().st_mode) & 0o077:
                raise QualityError(
                    "STORE_PERMISSIONS",
                    "M6 store directory must be private (mode 0700)",
                )
            lock_path = self.path.with_suffix(self.path.suffix + ".lock")
            try:
                self._lock_fd = os.open(
                    lock_path,
                    os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW,
                    0o600,
                )
                if not stat.S_ISREG(os.fstat(self._lock_fd).st_mode):
                    raise OSError("lock file is not regular")
                os.fchmod(self._lock_fd, 0o600)
                fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                database_fd = os.open(
                    self.path,
                    os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW,
                    0o600,
                )
                if not stat.S_ISREG(os.fstat(database_fd).st_mode):
                    os.close(database_fd)
                    raise OSError("database file is not regular")
                os.close(database_fd)
                os.chmod(self.path, 0o600)
                self._connection = sqlite3.connect(
                    self.path, timeout=5, isolation_level=None, check_same_thread=False
                )
            except (OSError, sqlite3.Error) as error:
                self.close()
                if isinstance(error, BlockingIOError):
                    raise QualityError(
                        "STORE_IN_USE", "another M6 process owns this store"
                    ) from None
                raise QualityError(
                    "STORE_UNAVAILABLE", "M6 store could not be opened"
                ) from None
        self._connection.row_factory = sqlite3.Row
        try:
            version = self._connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1, _SCHEMA_VERSION):
                raise QualityError(
                    "STORE_SCHEMA_UNSUPPORTED", "M6 store schema version is unsupported"
                )
            self._connection.execute("PRAGMA foreign_keys=ON")
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA synchronous=FULL")
            self._connection.execute("PRAGMA secure_delete=ON")
            self._connection.executescript(_SCHEMA + CHECK_HISTORY_SCHEMA)
            self._check_history = CheckHistory(self._connection, self._lock, self._transaction)
            self._check_history.migrate()
            self._connection.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
            self._secure_database_files()
        except QualityError:
            self.close()
            raise
        except sqlite3.Error as error:
            self.close()
            raise QualityError(
                "STORE_UNAVAILABLE", "M6 store schema could not be initialized"
            ) from error

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                self._connection.execute("BEGIN IMMEDIATE")
                yield self._connection
                self._connection.execute("COMMIT")
                self._secure_database_files()
            except Exception:
                if self._connection.in_transaction:
                    self._connection.execute("ROLLBACK")
                raise

    def reserve(
        self, order: VerifyRequest, *, max_pending: int = 4096
    ) -> tuple[Literal["new", "existing", "queued", "running"], dict[str, Any] | None]:
        if (
            not isinstance(max_pending, int)
            or isinstance(max_pending, bool)
            or max_pending <= 0
        ):
            raise QualityError("STORE_FAILURE", "pending request limit is invalid")
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT input_hash,state,result_json FROM requests WHERE idempotency_key=?",
                (order.idempotency_key,),
            ).fetchone()
            if row is not None:
                if row["input_hash"] != order.input_hash:
                    raise QualityError(
                        "IDEMPOTENCY_CONFLICT",
                        "idempotency key was reused with different input",
                    )
                if row["state"] in {"queued", "running"}:
                    return row["state"], None
                result = read_result(json.loads(row["result_json"])) if row["result_json"] else None
                return "existing", result
            pending = connection.execute(
                "SELECT COUNT(*) FROM requests WHERE state IN ('queued','running')"
            ).fetchone()[0]
            if pending >= max_pending:
                raise QualityError(
                    "QUALITY_BUSY", "M6 pending verification capacity is full"
                )
            timestamp = finished_at()
            connection.execute(
                "INSERT INTO requests(idempotency_key,input_hash,request_json,state,created_at,updated_at)"
                " VALUES(?,?,?,'queued',?,?)",
                (
                    order.idempotency_key,
                    order.input_hash,
                    canonical_json(order.to_dict()).decode("utf-8"),
                    timestamp,
                    timestamp,
                ),
            )
        return "new", None

    def queued_requests(self, limit: int) -> tuple[tuple[str, dict[str, Any]], ...]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            return ()
        with self._lock:
            rows = self._connection.execute(
                "SELECT idempotency_key,request_json FROM requests WHERE state='queued' "
                "ORDER BY created_at,idempotency_key LIMIT ?",
                (limit,),
            ).fetchall()
        return tuple((row[0], json.loads(row[1])) for row in rows)

    def claim_work(self, request_key: str) -> bool:
        with self._transaction() as connection:
            cursor = connection.execute(
                "UPDATE requests SET state='running',updated_at=? WHERE idempotency_key=? "
                "AND state='queued'",
                (finished_at(), request_key),
            )
            return cursor.rowcount == 1

    def pending_requests(self) -> tuple[tuple[str, dict[str, Any]], ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT idempotency_key,request_json FROM requests WHERE state='running'"
                " ORDER BY created_at,idempotency_key"
            ).fetchall()
        return tuple((row[0], json.loads(row[1])) for row in rows)

    def finish(
        self,
        order: VerifyRequest,
        result: dict[str, Any],
        result_bytes: bytes,
        manifest_bytes: bytes,
        artifacts: dict[str, bytes],
    ) -> str:
        result_hash = hashlib.sha256(result_bytes).hexdigest()
        if canonical_json(result) != result_bytes:
            raise QualityError("RESULT_INVALID", "result bytes are not canonical")
        manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
        if result.get("evidence_manifest") != f"m6://result/{manifest_digest}":
            raise QualityError(
                "RESULT_INVALID",
                "result evidence manifest hash does not match its content",
            )
        for digest, content in artifacts.items():
            if hashlib.sha256(content).hexdigest() != digest:
                raise QualityError(
                    "RESULT_INVALID", "artifact hash does not match its content"
                )
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state,input_hash FROM requests WHERE idempotency_key=?",
                (order.idempotency_key,),
            ).fetchone()
            if (
                row is None
                or row["input_hash"] != order.input_hash
                or row["state"] != "running"
            ):
                raise QualityError(
                    "RESULT_CONFLICT", "request is not reserved for this result"
                )
            now = result.get("finished_at", finished_at())
            for digest, content in artifacts.items():
                connection.execute(
                    "INSERT OR IGNORE INTO artifacts(digest,media_type,content,created_at)"
                    " VALUES(?,?,?,?)",
                    (digest, "application/octet-stream", content, now),
                )
            connection.execute(
                "INSERT OR IGNORE INTO artifacts(digest,media_type,content,created_at) VALUES(?,?,?,?)",
                (manifest_digest, "application/json", manifest_bytes, now),
            )
            state = {
                "PASS": "complete",
                "FAIL": "complete",
                "NEEDS_REVIEW": "needs_review",
                "STALE": "stale",
            }.get(result.get("status"))
            if state is None:
                raise QualityError("RESULT_INVALID", "result has an unsupported status")
            connection.execute(
                "UPDATE requests SET state=?,result_json=?,result_hash=?,updated_at=?"
                " WHERE idempotency_key=?",
                (
                    state,
                    result_bytes.decode("utf-8"),
                    result_hash,
                    now,
                    order.idempotency_key,
                ),
            )
            if state == "needs_review":
                connection.execute(
                    "INSERT INTO reviews(request_key,state,created_at) VALUES(?,'open',?)",
                    (order.idempotency_key, now),
                )
            elif state == "complete":
                connection.execute(
                    "INSERT INTO outbox(request_key,state,attempts) VALUES(?,'pending',0)",
                    (order.idempotency_key,),
                )
        return result_hash

    def get_result(self, idempotency_key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT result_json,result_hash FROM requests WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
        if not row or not row[0]:
            return None
        if hashlib.sha256(row[0].encode("utf-8")).hexdigest() != row[1]:
            raise QualityError(
                "STORE_CORRUPT", "persisted result failed its content hash"
            )
        return read_result(json.loads(row[0]))

    def get_artifact(self, reference: str) -> bytes | None:
        if not isinstance(reference, str) or not reference.startswith("m6://artifact/"):
            return None
        digest = reference.removeprefix("m6://artifact/")
        if not _valid_sha256(digest):
            return None
        with self._lock:
            row = self._connection.execute(
                "SELECT content FROM artifacts WHERE digest=?", (digest,)
            ).fetchone()
        if not row:
            return None
        content = bytes(row[0])
        if hashlib.sha256(content).hexdigest() != digest:
            raise QualityError(
                "STORE_CORRUPT", "persisted artifact failed its content hash"
            )
        return content

    def get_result_manifest(self, reference: str) -> bytes | None:
        if not isinstance(reference, str) or not reference.startswith("m6://result/"):
            return None
        digest = reference.removeprefix("m6://result/")
        if not _valid_sha256(digest):
            return None
        with self._lock:
            row = self._connection.execute(
                "SELECT content FROM artifacts WHERE digest=?", (digest,)
            ).fetchone()
        if not row:
            return None
        content = bytes(row[0])
        if hashlib.sha256(content).hexdigest() != digest:
            raise QualityError(
                "STORE_CORRUPT", "persisted result manifest failed its content hash"
            )
        return content

    def list_reviews(
        self, *, include_resolved: bool = False
    ) -> tuple[dict[str, Any], ...]:
        states = ("open", "resolved", "stale") if include_resolved else ("open",)
        marks = ",".join("?" for _ in states)
        with self._lock:
            rows = self._connection.execute(
                f"SELECT request_key,state,created_at,resolved_at,resolved_by,reason,decision,"
                f"resolution_id,evidence_ref FROM reviews WHERE state IN ({marks}) "
                "ORDER BY created_at,request_key",
                states,
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def retry_interrupted(self, request_key: str, operator: str, reason: str) -> None:
        """Explicitly retry one interrupted verification, preserving its audit evidence.

        No verdict is created. Normal dispatch revalidates snapshot provenance and
        command policy and runs checks in the configured sandbox. One retry per
        request prevents restart/retry loops from replaying commands indefinitely.
        """
        _validate_operator(operator, reason, "FAIL")
        with self._transaction() as connection:
            retry_interrupted(connection, request_key, operator, reason)

    def requeue_after_clean_stop(self, request_key: str, reason: str) -> None:
        """Requeue a verification interrupted by a recorded, deliberate engine stop without using its one interrupted
        retry (recovery.requeue_after_clean_stop, D-210). No verdict is created; dispatch revalidates as usual."""
        if not reason.strip():
            raise QualityError("RETRY_INVALID", "a reason is required")
        with self._transaction() as connection:
            requeue_after_clean_stop(connection, request_key, reason)

    def open_reviews_of(self, task_id: str) -> tuple[str, ...]:
        """Request keys of the open reviews that belong to `task_id` (oldest first)."""
        found = []
        for review in self.list_reviews():
            with self._lock:
                row = self._connection.execute("SELECT request_json FROM requests WHERE idempotency_key = ?",
                                               (review["request_key"],)).fetchone()
            try:
                if row and json.loads(row["request_json"]).get("task_id") == task_id:
                    found.append(review["request_key"])
            except ValueError:
                continue
        return tuple(found)

    def open_review_attempts(self, task_id: str) -> tuple[str, ...]:
        """The attempts that the open reviews of `task_id` verify (each once, oldest first)."""
        found: list[str] = []
        for key in self.open_reviews_of(task_id):
            with self._lock:
                row = self._connection.execute("SELECT request_json FROM requests WHERE idempotency_key = ?", (key,)).fetchone()
            try:
                attempt = json.loads(row["request_json"]).get("attempt_id") if row else None
            except ValueError:
                continue
            if isinstance(attempt, str) and attempt and attempt not in found:
                found.append(attempt)
        return tuple(found)

    def retry_attested(self, request_key: str, operator: str, reason: str) -> None:
        """Requeue one open review that only waited for manual evidence, now attested (see `recovery.retry_attested`)."""
        _validate_operator(operator, reason, "FAIL")
        with self._transaction() as connection:
            retry_attested(connection, request_key, operator, reason)

    def retry_m5_transient(self, request_key: str) -> None:
        """Apply M5's one bounded same-attempt verification resume for TIMEOUT/FLAKY_SUSPECTED evidence."""
        with self._transaction() as connection:
            retry_m5_transient(connection, request_key, "m5-policy", "same-attempt verification resume")

    def resolve_review(
        self, request_key: str, operator: str, decision: str, reason: str
    ) -> str:
        _validate_operator(operator, reason, decision)
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state FROM reviews WHERE request_key=?", (request_key,)
            ).fetchone()
            if row is None:
                raise QualityError("REVIEW_NOT_FOUND", "review item does not exist")
            if row[0] != "open":
                raise QualityError(
                    "REVIEW_ALREADY_RESOLVED", "review item was already resolved"
                )
            timestamp = finished_at()
            resolution = {
                "schema_version": "m6.review-resolution/1",
                "request_key": request_key,
                "operator": operator,
                "decision": decision,
                "reason": reason,
                "resolved_at": timestamp,
            }
            content = canonical_json(resolution)
            digest = hashlib.sha256(content).hexdigest()
            connection.execute(
                "INSERT OR IGNORE INTO artifacts(digest,media_type,content,created_at) VALUES(?,?,?,?)",
                (digest, "application/json", content, timestamp),
            )
            connection.execute(
                "UPDATE reviews SET state='resolved',resolved_at=?,resolved_by=?,reason=?,decision=?,"
                "resolution_id=?,evidence_ref=? WHERE request_key=?",
                (
                    timestamp,
                    operator,
                    reason,
                    decision,
                    digest,
                    f"m6://resolution/{digest}",
                    request_key,
                ),
            )
            connection.execute(
                "INSERT INTO outbox(request_key,state,attempts) VALUES(?,'pending',0)",
                (request_key,),
            )
        return f"m6://resolution/{digest}"

    def pending_deliveries(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT o.request_key,o.attempts,r.request_json,r.result_json,r.result_hash,r.state AS request_state,"
                "v.state AS review_state,v.resolved_by,v.decision,v.evidence_ref,v.resolution_id,o.last_response_at "
                "FROM outbox o JOIN requests r ON o.request_key=r.idempotency_key "
                "LEFT JOIN reviews v ON o.request_key=v.request_key WHERE o.state='pending' "
                "ORDER BY r.created_at,o.request_key"
            ).fetchall()
        return tuple(dict(row) for row in rows)

    def begin_delivery(self, request_key: str) -> dict[str, Any] | None:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT o.state,o.attempts,r.request_json,r.result_json,r.result_hash,"
                "v.state AS review_state,"
                "v.resolved_by,v.decision,v.evidence_ref,v.resolution_id "
                "FROM outbox o JOIN requests r ON o.request_key=r.idempotency_key "
                "LEFT JOIN reviews v ON o.request_key=v.request_key "
                "WHERE o.request_key=?",
                (request_key,),
            ).fetchone()
            if row is None or row["state"] != "pending":
                return None
            connection.execute(
                "UPDATE outbox SET attempts=attempts+1,last_attempt_at=? WHERE request_key=?",
                (finished_at(), request_key),
            )
        payload = dict(row)
        payload["request_key"] = request_key
        payload["request_json"] = json.loads(payload["request_json"])
        result_raw = payload["result_json"]
        if (
            hashlib.sha256(result_raw.encode("utf-8")).hexdigest()
            != payload["result_hash"]
        ):
            raise QualityError(
                "STORE_CORRUPT", "pending result failed its content hash"
            )
        payload["result_json"] = json.loads(payload["result_json"])
        return payload

    def finish_delivery(
        self,
        request_key: str,
        state: Literal["delivered", "stale", "pending"],
        detail: str = "",
    ) -> None:
        if state not in {"delivered", "stale", "pending"}:
            raise QualityError("STORE_FAILURE", "delivery state is invalid")
        safe_detail = detail[:512] if isinstance(detail, str) else ""
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state FROM outbox WHERE request_key=?", (request_key,)
            ).fetchone()
            if row is None:
                raise QualityError(
                    "OUTBOX_NOT_FOUND", "verdict delivery is not recorded"
                )
            now = finished_at()
            reason_code = _delivery_reason_code(safe_detail)
            if state == "stale":
                self._persist_stale_result(connection, request_key, now, reason_code)
            connection.execute(
                "UPDATE outbox SET state=?,last_error=?,last_response_at=? WHERE request_key=?",
                (
                    state,
                    safe_detail[:512]
                    if state == "pending"
                    else reason_code
                    if state == "stale"
                    else "",
                    now,
                    request_key,
                ),
            )
            if state == "stale":
                connection.execute(
                    "UPDATE requests SET state='stale',updated_at=? WHERE idempotency_key=?",
                    (now, request_key),
                )
                connection.execute(
                    "UPDATE reviews SET state='stale' WHERE request_key=? AND state='resolved'",
                    (request_key,),
                )

    @staticmethod
    def _persist_stale_result(
        connection: sqlite3.Connection,
        request_key: str,
        timestamp: str,
        reason_code: str,
    ) -> None:
        row = connection.execute(
            "SELECT result_json,result_hash FROM requests WHERE idempotency_key=?",
            (request_key,),
        ).fetchone()
        if row is None or row["result_json"] is None:
            return
        result_raw = row["result_json"]
        if hashlib.sha256(result_raw.encode("utf-8")).hexdigest() != row["result_hash"]:
            raise QualityError("STORE_CORRUPT", "stale result failed its content hash")
        result = json.loads(result_raw)
        if not isinstance(result, dict):
            raise QualityError("STORE_CORRUPT", "stale result is not a JSON object")
        if result.get("status") == "STALE":
            return
        manifest_ref = result.get("evidence_manifest")
        if (
            not isinstance(manifest_ref, str)
            or not manifest_ref.startswith("m6://result/")
            or not _valid_sha256(manifest_ref.removeprefix("m6://result/"))
        ):
            raise QualityError(
                "STORE_CORRUPT", "stale result has an invalid evidence reference"
            )
        manifest_digest = manifest_ref.removeprefix("m6://result/")
        manifest_row = connection.execute(
            "SELECT content FROM artifacts WHERE digest=?", (manifest_digest,)
        ).fetchone()
        if manifest_row is None:
            raise QualityError(
                "STORE_CORRUPT", "stale result evidence manifest is missing"
            )
        manifest_raw = bytes(manifest_row[0])
        if hashlib.sha256(manifest_raw).hexdigest() != manifest_digest:
            raise QualityError(
                "STORE_CORRUPT",
                "stale result evidence manifest failed its content hash",
            )
        manifest = json.loads(manifest_raw)
        if not isinstance(manifest, dict):
            raise QualityError(
                "STORE_CORRUPT", "stale result evidence manifest is not a JSON object"
            )
        stale_manifest = {
            **manifest,
            "delivery": {
                "state": "stale",
                "reason_code": reason_code,
                "recorded_at": timestamp,
            },
        }
        stale_manifest_raw = canonical_json(stale_manifest)
        stale_manifest_digest = hashlib.sha256(stale_manifest_raw).hexdigest()
        stale_result = {
            **result,
            "status": "STALE",
            "evidence_manifest": f"m6://result/{stale_manifest_digest}",
        }
        stale_result_raw = canonical_json(stale_result)
        connection.execute(
            "INSERT OR IGNORE INTO artifacts(digest,media_type,content,created_at) VALUES(?,?,?,?)",
            (stale_manifest_digest, "application/json", stale_manifest_raw, timestamp),
        )
        connection.execute(
            "UPDATE requests SET state='stale',result_json=?,result_hash=?,updated_at=? "
            "WHERE idempotency_key=?",
            (
                stale_result_raw.decode("utf-8"),
                hashlib.sha256(stale_result_raw).hexdigest(),
                timestamp,
                request_key,
            ),
        )

    def cached_pass(self, key: str, max_age: float, now: float) -> sqlite3.Row | None:
        """A passing outcome stored under `key` no older than `max_age` seconds, else None."""
        return self._check_history.cached_pass(key, max_age, now)

    def remember_pass(self, key: str, exit_code: int | None, duration_ms: int, stdout: bytes, stderr: bytes,
                      now: float) -> None:
        self._check_history.remember_pass(key, exit_code, duration_ms, stdout, stderr, now)

    def record_check_outcome(self, key: str, status: str, now: float) -> bool:
        """Persist an evidence-key outcome; return true when this pass follows a prior failure."""
        return self._check_history.record_outcome(key, status, now)

    def last_check_ms(self, command_key: str) -> int | None:
        return self._check_history.last_ms(command_key)

    def record_check_ms(self, command_key: str, duration_ms: int, now: float) -> None:
        self._check_history.record_ms(command_key, duration_ms, now)

    def metrics(self) -> dict[str, Any]:
        with self._lock:
            state_rows = self._connection.execute(
                "SELECT state,COUNT(*) AS total FROM requests GROUP BY state"
            ).fetchall()
            results = self._connection.execute(
                "SELECT result_json FROM requests WHERE result_json IS NOT NULL"
            ).fetchall()
        counts = {"pass": 0, "fail": 0, "unknown": 0, "not_run": 0}
        for row in results:
            result = json.loads(row[0])
            for check in result.get("checks", []):
                status = check.get("status")
                if status in {"pass", "fail"}:
                    counts[status] += 1
                elif status == "unknown":
                    if check.get("issue_code") == "CHECK_NOT_RUN":
                        counts["not_run"] += 1
                    else:
                        counts["unknown"] += 1
        return {
            "requests_by_state": {row["state"]: row["total"] for row in state_rows},
            "checks": counts,
            "defect_count": None,
            "defect_count_measured": False,
            "unmeasured": ["defect_count"],
        }

    def _secure_database_files(self) -> None:
        if self.path is None:
            return
        for candidate in (
            self.path,
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
        ):
            try:
                # POSIX locks belong to the process: closing ANY descriptor for
                # SQLite's db/shm inode can release locks held by its own fd.
                # Never open these files merely to refresh permissions.
                if not stat.S_ISREG(candidate.lstat().st_mode):
                    raise QualityError(
                        "STORE_PERMISSIONS", "M6 database path is not a regular file"
                    )
                os.chmod(candidate, 0o600, follow_symlinks=False)
            except FileNotFoundError:
                continue
            except OSError as error:
                raise QualityError(
                    "STORE_PERMISSIONS", "M6 database files could not be kept private"
                ) from error

    def close(self) -> None:
        connection = getattr(self, "_connection", None)
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                pass
            self._connection = None
        if self._lock_fd is not None:
            try:
                os.close(self._lock_fd)
            except OSError:
                pass
            self._lock_fd = None

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    idempotency_key TEXT PRIMARY KEY,
    input_hash TEXT NOT NULL,
    request_json TEXT NOT NULL,
    state TEXT NOT NULL CHECK(state IN ('queued','running','complete','needs_review','stale')),
    result_json TEXT,
    result_hash TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS artifacts (
    digest TEXT PRIMARY KEY,
    media_type TEXT NOT NULL,
    content BLOB NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reviews (
    request_key TEXT PRIMARY KEY REFERENCES requests(idempotency_key),
    state TEXT NOT NULL CHECK(state IN ('open','resolved','stale')),
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    resolved_by TEXT,
    reason TEXT,
    decision TEXT,
    resolution_id TEXT,
    evidence_ref TEXT
);
CREATE TABLE IF NOT EXISTS verification_retries (
    request_key TEXT PRIMARY KEY REFERENCES requests(idempotency_key),
    operator TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    previous_result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS verification_restarts (
    request_key TEXT NOT NULL REFERENCES requests(idempotency_key),
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL,
    previous_result_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS outbox (
    request_key TEXT PRIMARY KEY REFERENCES requests(idempotency_key),
    state TEXT NOT NULL CHECK(state IN ('pending','delivered','stale')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK(attempts >= 0),
    last_error TEXT NOT NULL DEFAULT '',
    last_attempt_at TEXT,
    last_response_at TEXT
);
"""


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _delivery_reason_code(detail: str) -> str:
    if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", detail, flags=re.ASCII):
        return detail
    return "unspecified"


def _validate_operator(operator: str, reason: str, decision: str) -> None:
    if not isinstance(operator, str) or not operator.strip():
        raise QualityError(
            "REVIEW_INVALID", "operator identity must be bounded, non-empty text"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise QualityError(
            "REVIEW_INVALID", "review rationale must be bounded, non-empty text"
        )
    try:
        operator_bytes = operator.encode("utf-8")
        reason_bytes = reason.encode("utf-8")
    except UnicodeEncodeError:
        raise QualityError(
            "REVIEW_INVALID", "operator identity or rationale is not valid Unicode text"
        ) from None
    if len(operator_bytes) > 256 or any(
        ord(char) < 32 or ord(char) == 127 for char in operator
    ):
        raise QualityError(
            "REVIEW_INVALID", "operator identity must be bounded, non-empty text"
        )
    if len(reason_bytes) > 2048 or any(
        ord(char) < 32 or ord(char) == 127 for char in reason
    ):
        raise QualityError(
            "REVIEW_INVALID", "review rationale must be bounded, non-empty text"
        )
    if not isinstance(decision, str) or decision not in {"PASS", "FAIL"}:
        raise QualityError("REVIEW_INVALID", "review decision must be PASS or FAIL")
