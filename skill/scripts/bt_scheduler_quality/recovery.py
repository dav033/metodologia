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
