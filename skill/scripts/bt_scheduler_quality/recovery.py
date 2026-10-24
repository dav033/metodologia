"""Audited, bounded recovery for interrupted quality verification requests."""

from __future__ import annotations

import hashlib
import json
import sqlite3

from .contracts import QualityError
from .evidence import finished_at


def retry_interrupted(
    connection: sqlite3.Connection, request_key: str, operator: str, reason: str
) -> None:
    """Requeue an interrupted review inside the caller's validated transaction."""
    row = connection.execute(
        "SELECT r.state,r.result_json,r.result_hash,v.state AS review_state "
        "FROM requests r LEFT JOIN reviews v ON v.request_key=r.idempotency_key "
        "WHERE r.idempotency_key=?", (request_key,),
    ).fetchone()
    if row is None or row["state"] != "needs_review" or row["review_state"] != "open":
        raise QualityError("RETRY_INVALID", "only open interrupted reviews can be retried")
    result_raw = row["result_json"]
    if hashlib.sha256(result_raw.encode("utf-8")).hexdigest() != row["result_hash"]:
        raise QualityError("STORE_CORRUPT", "interrupted result failed its content hash")
    result = json.loads(result_raw)
    if (result.get("status") != "NEEDS_REVIEW"
        or {item.get("code") for item in result.get("issues", [])} != {"ENGINE_INTERRUPTED"}
        or any(check.get("issue_code") != "ENGINE_INTERRUPTED"
               for check in result.get("checks", []))):
        raise QualityError("RETRY_INVALID", "review was not caused solely by engine interruption")
    if connection.execute(
        "SELECT 1 FROM verification_retries WHERE request_key=?", (request_key,)
    ).fetchone():
        raise QualityError("RETRY_EXHAUSTED", "interrupted request already retried once")
    timestamp = finished_at()
    connection.execute(
        "INSERT INTO verification_retries(request_key,operator,reason,created_at,previous_result_json) "
        "VALUES(?,?,?,?,?)", (request_key, operator, reason, timestamp, result_raw),
    )
    connection.execute("DELETE FROM reviews WHERE request_key=?", (request_key,))
    connection.execute(
        "UPDATE requests SET state='queued',result_json=NULL,result_hash=NULL,updated_at=? "
        "WHERE idempotency_key=?", (timestamp, request_key),
    )


ATTESTABLE = frozenset({"CRITERION_MANUAL", "CHECK_MANUAL", "CHECK_UNMAPPED"})


def retry_attested(connection: sqlite3.Connection, request_key: str, operator: str, reason: str) -> None:
    """Requeue an open review whose ONLY doubt was manual evidence, once the coordinator has attested it (REQ-030). The
    attestation receipts are looked up again when the checks run; one retry per request, like an interrupted one."""
    row = connection.execute(
        "SELECT r.state,r.result_json,r.result_hash,v.state AS review_state "
        "FROM requests r LEFT JOIN reviews v ON v.request_key=r.idempotency_key "
        "WHERE r.idempotency_key=?", (request_key,),
    ).fetchone()
    if row is None or row["state"] != "needs_review" or row["review_state"] != "open":
        raise QualityError("RETRY_INVALID", "only open reviews can be retried after an attestation")
    result_raw = row["result_json"]
    if hashlib.sha256(result_raw.encode("utf-8")).hexdigest() != row["result_hash"]:
        raise QualityError("STORE_CORRUPT", "result failed its content hash")
    result = json.loads(result_raw)
    codes = {item.get("code") for item in result.get("issues", [])}
    if result.get("status") != "NEEDS_REVIEW" or not codes or not codes <= ATTESTABLE or "CRITERION_MANUAL" not in codes:
        raise QualityError("RETRY_INVALID", "the review is about more than manual evidence an attestation can settle")
    if connection.execute("SELECT 1 FROM verification_retries WHERE request_key=?", (request_key,)).fetchone():
        raise QualityError("RETRY_EXHAUSTED", "this request was already retried once")
    timestamp = finished_at()
    connection.execute(
        "INSERT INTO verification_retries(request_key,operator,reason,created_at,previous_result_json) "
        "VALUES(?,?,?,?,?)", (request_key, operator, reason, timestamp, result_raw),
    )
    connection.execute("DELETE FROM reviews WHERE request_key=?", (request_key,))
    connection.execute(
        "UPDATE requests SET state='queued',result_json=NULL,result_hash=NULL,updated_at=? "
        "WHERE idempotency_key=?", (timestamp, request_key),
    )


def retry_m5_transient(connection: sqlite3.Connection, request_key: str, operator: str, reason: str) -> None:
    """Requeue only a current open timeout/flaky review after M5 explicitly advises same-attempt verification."""
    row = connection.execute(
        "SELECT r.state,r.result_json,r.result_hash,v.state AS review_state "
        "FROM requests r LEFT JOIN reviews v ON v.request_key=r.idempotency_key "
        "WHERE r.idempotency_key=?", (request_key,),
    ).fetchone()
    if row is None or row["state"] != "needs_review" or row["review_state"] != "open":
        raise QualityError("RETRY_INVALID", "only open M6 reviews can be resumed by M5")
    result_raw = row["result_json"]
    if hashlib.sha256(result_raw.encode("utf-8")).hexdigest() != row["result_hash"]:
        raise QualityError("STORE_CORRUPT", "M5 resume result failed its content hash")
    result = json.loads(result_raw)
    if (result.get("status") != "NEEDS_REVIEW" or
            result.get("reason_code") not in {"TIMEOUT", "FLAKY_SUSPECTED"}):
        raise QualityError("RETRY_INVALID", "only timeout or flaky M6 evidence can resume verification")
    if connection.execute("SELECT 1 FROM verification_retries WHERE request_key=?", (request_key,)).fetchone():
        raise QualityError("RETRY_EXHAUSTED", "M6 verification already resumed once")
    timestamp = finished_at()
    connection.execute(
        "INSERT INTO verification_retries(request_key,operator,reason,created_at,previous_result_json) "
        "VALUES(?,?,?,?,?)", (request_key, operator, reason, timestamp, result_raw),
    )
    connection.execute("DELETE FROM reviews WHERE request_key=?", (request_key,))
    connection.execute("UPDATE requests SET state='queued',result_json=NULL,result_hash=NULL,updated_at=? "
                        "WHERE idempotency_key=?", (timestamp, request_key))
