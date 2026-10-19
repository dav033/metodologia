"""Bounded, read-only projections for operator status and history commands."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .activity import ActivityState
from .serialization import event_from_dict
from .storage_limits import MAX_STORE_BYTES, WRITE_RESERVE_BYTES, measured_store_bytes

MAX_ACTIVITY_EVENTS = 1_000


def _connect(path: str | Path) -> sqlite3.Connection:
    database_uri = f"file:{quote(str(Path(path).resolve()), safe='/')}?mode=ro"
    connection = sqlite3.connect(database_uri, uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _bounded_limit(limit: int) -> int:
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    return min(limit, 100)


def _timestamp_key(value: object) -> datetime:
    if not isinstance(value, str):
        return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def status(path: str | Path, *, max_store_bytes: int | None = None) -> dict[str, object]:
    if max_store_bytes is not None and (type(max_store_bytes) is not int or max_store_bytes <= WRITE_RESERVE_BYTES):
        raise ValueError(f"max_store_bytes must be greater than {WRITE_RESERVE_BYTES}")
    connection = _connect(path)
    try:
        try:
            configured = connection.execute("SELECT max_store_bytes FROM store_limits WHERE singleton=1").fetchone()
        except sqlite3.OperationalError:
            configured = None
        limit_bytes = (configured[0] if configured else MAX_STORE_BYTES) if max_store_bytes is None else max_store_bytes
        measured_bytes = measured_store_bytes(path)
        pressure = measured_bytes + WRITE_RESERVE_BYTES > limit_bytes
        events = connection.execute("SELECT COUNT(*) FROM normalized_events").fetchone()[0]
        incidents = connection.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        open_incidents = connection.execute("SELECT COUNT(*) FROM incidents WHERE resolution_state='open'").fetchone()[0]
        cursors = connection.execute("SELECT COUNT(*) FROM source_cursors").fetchone()[0]
        outbox_pending = connection.execute("SELECT COUNT(*) FROM m1_outbox WHERE state!='acked'").fetchone()[0]
        try:
            stream_gaps = connection.execute("SELECT COUNT(*) FROM stream_gaps").fetchone()[0]
            stream_status = "degraded" if stream_gaps else "unknown"
        except sqlite3.OperationalError:
            stream_gaps = None
            stream_status = "unknown"
        health = None
        try:
            row = connection.execute("SELECT state,measured_bytes,updated_at FROM m4_retention_health WHERE singleton=1").fetchone()
            if row:
                health = {"state": row["state"], "measured_bytes": row["measured_bytes"],
                          "updated_at": row["updated_at"]}
        except sqlite3.OperationalError:
            pass
        storage_state = "storage_pressure" if pressure else "healthy"
        return {"status": "degraded" if pressure or (health and health["state"] == "storage_pressure") else "available",
                "events": events, "incidents": incidents, "open_incidents": open_incidents,
                "source_cursors": cursors, "outbox_pending": outbox_pending,
                "stream_status": stream_status, "stream_gaps": stream_gaps,
                "storage": {"state": storage_state, "measured_bytes": measured_bytes,
                            "limit_bytes": limit_bytes, "write_reserve_bytes": WRITE_RESERVE_BYTES,
                            "updated_at": health["updated_at"] if health else None}}
    finally:
        connection.close()


def events(path: str | Path, *, limit: int = 50, execution_id: str | None = None) -> dict[str, object]:
    count = _bounded_limit(limit)
    connection = _connect(path)
    try:
        if execution_id is None:
            rows = connection.execute("SELECT body FROM normalized_events ORDER BY rowid DESC LIMIT ?", (count,)).fetchall()
        else:
            rows = connection.execute("SELECT body FROM normalized_events WHERE execution_id=? ORDER BY rowid DESC LIMIT ?",
                                      (execution_id, count)).fetchall()
        items = []
        for row in rows:
            body = json.loads(row["body"])
            items.append({key: body.get(key) for key in ("event_id", "run_id", "task_id", "attempt_id", "execution_id",
                           "provider", "event_type", "source_event_type", "received_at", "stream", "sequence",
                           "offset_bytes", "quality")})
        return {"items": items, "count": len(items), "limit": count}
    finally:
        connection.close()


def incidents(path: str | Path, *, limit: int = 50, resolution_state: str | None = None) -> dict[str, object]:
    count = _bounded_limit(limit)
    if resolution_state not in (None, "open", "resolved"):
        raise ValueError("resolution_state must be open or resolved")
    connection = _connect(path)
    try:
        query = "SELECT body FROM incidents"
        params: tuple[object, ...] = ()
        if resolution_state is not None:
            query += " WHERE resolution_state=?"
            params = (resolution_state,)
        rows = connection.execute(query + " ORDER BY rowid DESC LIMIT ?", (*params, count)).fetchall()
        fields = ("incident_id", "run_id", "task_id", "attempt_id", "execution_id", "detector_id", "type",
                  "severity", "confidence", "first_seen_at", "last_seen_at", "occurrence_count", "resolution_state",
                  "resolved_at")
        items = [{key: payload.get(key) for key in fields} for payload in (json.loads(row["body"]) for row in rows)]
        return {"items": items, "count": len(items), "limit": count}
    finally:
        connection.close()


def metrics(path: str | Path, *, limit: int = 100) -> dict[str, object]:
    count = _bounded_limit(limit)
    connection = _connect(path)
    try:
        items: list[dict[str, Any]] = []
        try:
            rows = connection.execute("""SELECT body FROM metric_samples
                ORDER BY julianday(observed_at) DESC,metric_id DESC LIMIT ?""", (count,)).fetchall()
            for row in rows:
                sample = json.loads(row["body"])
                items.append({key: sample.get(key) for key in ("metric_id", "provider", "name", "value", "unit", "source",
                               "observed_at", "quality", "sample_count", "comparability_key", "profile_id", "model")})
            if len(items) < count:
                aggregate_rows = connection.execute("""SELECT * FROM daily_metric_aggregates
                    ORDER BY day DESC,group_key LIMIT ?""", (count - len(items),)).fetchall()
                for row in aggregate_rows:
                    items.append({"metric_id": None, "provider": row["provider"], "name": row["name"],
                                  "value": row["value_sum"], "unit": row["unit"], "source": row["source"],
                                  "observed_at": row["day"], "quality": row["quality"],
                                  "sample_count": row["sample_count"], "comparability_key": row["comparability_key"],
                                  "profile_id": row["profile_id"], "model": row["model"], "aggregate": True})
            return {"items": items, "count": len(items), "limit": count}
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc):
                raise
            return {"items": [], "count": 0, "limit": count, "availability": "unavailable"}
    finally:
        connection.close()


def activity(path: str | Path, *, limit: int = 50, execution_id: str | None = None) -> dict[str, object]:
    count = _bounded_limit(limit)
    connection = _connect(path)
    try:
        where = " WHERE execution_id=?" if execution_id is not None else ""
        params: tuple[object, ...] = (execution_id,) if execution_id is not None else ()
        rows = connection.execute("SELECT body FROM normalized_events" + where +
                                  " ORDER BY rowid DESC LIMIT ?", (*params, MAX_ACTIVITY_EVENTS + 1)).fetchall()
        truncated = len(rows) > MAX_ACTIVITY_EVENTS
        states: dict[tuple[str, str, str, str], ActivityState] = {}
        for row in reversed(rows[:MAX_ACTIVITY_EVENTS]):
            event = event_from_dict(json.loads(row["body"]))
            identity = (event.run_id, event.task_id, event.attempt_id, event.execution_id)
            states.setdefault(identity, ActivityState()).add(event)

        items: list[dict[str, object]] = []
        for state in states.values():
            view = state.snapshot()
            projection_incomplete = truncated or view.projection_truncated
            metric_items = []
            for metric_event in view.metrics:
                payload = dict(metric_event.payload)
                metric_items.append({
                    "event_id": metric_event.event_id,
                    "provider": metric_event.provider,
                    "profile_id": metric_event.profile_id,
                    "model": metric_event.model,
                    "metric_name": payload.get("metric_name"),
                    "value": payload.get("value"),
                    "unit": payload.get("unit"),
                    "source": payload.get("source"),
                    "sample_count": payload.get("sample_count"),
                    "quality": metric_event.quality,
                    "observed_at": metric_event.source_occurred_at,
                    "received_at": metric_event.received_at,
                })
            process_identity = view.process_identity
            item: dict[str, object] = {
                "run_id": view.run_id,
                "task_id": view.task_id,
                "attempt_id": view.attempt_id,
                "execution_id": view.execution_id,
                "provider": view.provider,
                "profile_id": view.profile_id,
                "model": view.model,
                "process_identity": None if process_identity is None else {
                    "platform": process_identity.platform,
                    "host_boot_id": process_identity.host_boot_id,
                    "pid": process_identity.pid,
                    "start_ticks": process_identity.start_ticks,
                },
                "last_source_event_type": view.last_source_event_type,
                "last_source_at": view.last_source_at,
                "last_received_io_at": view.last_received_io_at,
                "last_received_monotonic_ns": view.last_received_monotonic_ns,
                "last_sequence": view.last_sequence,
                "last_offset_bytes": view.last_offset_bytes,
                "last_tool_label": view.last_tool_label,
                "pending_tools": list(view.pending_tools),
                "pending_tools_truncated": view.pending_tools_truncated,
                "pending_tools_dropped_count": view.pending_tools_dropped_count,
                "pending_tools_uncertain": view.pending_tools_uncertain or truncated,
                "metrics": metric_items,
                "metrics_truncated": view.metrics_truncated,
                "metrics_dropped_count": view.metrics_dropped_count,
                "stream_integrity": "unknown" if truncated and view.stream_integrity == "complete" else view.stream_integrity,
                "process_status": view.process_status,
                "display_state": "unknown" if projection_incomplete else view.display_state,
                "identity_corroboration": view.identity_corroboration,
                "projection_truncated": projection_incomplete,
            }
            items.append(item)
        items.sort(key=lambda item: _timestamp_key(item["last_received_io_at"]), reverse=True)
        return {"items": items[:count], "count": min(len(items), count), "limit": count,
                "event_limit": MAX_ACTIVITY_EVENTS, "truncated": truncated}
    finally:
        connection.close()




MAX_SUMMARY_EVENTS = 50_000


_TOKEN_METRICS = ("input_tokens", "output_tokens", "total_tokens")


def attempt_summaries(path: str | Path, *, since_rowid: int = 0) -> dict[str, object]:
    """Per-attempt totals over the normalized stream: provider/profile/model as observed, last received time, event
    count and provider-reported token totals (``None`` when no usage was reported, never 0). Read-only and
    bounded; ``since_rowid`` lets a caller fold only new rows into totals it already holds (``cursor`` is the
    last rowid read)."""
    if type(since_rowid) is not int or since_rowid < 0:
        raise ValueError("since_rowid must be a non-negative integer")
    connection = _connect(path)
    try:
        rows = connection.execute("SELECT rowid, body FROM normalized_events WHERE rowid > ? ORDER BY rowid LIMIT ?",
                                  (since_rowid, MAX_SUMMARY_EVENTS + 1)).fetchall()
    finally:
        connection.close()
    truncated = len(rows) > MAX_SUMMARY_EVENTS
    rows = rows[:MAX_SUMMARY_EVENTS]
    attempts: dict[str, dict[str, object]] = {}
    for row in rows:
        try:
            body = json.loads(row["body"])
        except ValueError:
            continue
        attempt_id = body.get("attempt_id") if isinstance(body, dict) else None
        if not isinstance(attempt_id, str) or not attempt_id:
            continue
        item = attempts.setdefault(attempt_id, {
            "attempt_id": attempt_id, "task_id": body.get("task_id"), "run_id": body.get("run_id"),
            "provider": None, "profile_id": None, "model": None, "first_received_at": body.get("received_at"),
            "last_received_at": None, "events": 0, "tokens_total": None, "token_samples": 0,
            "tokens_by_metric": {}})
        item["events"] = int(item["events"]) + 1
        for name in ("provider", "profile_id", "model"):
            if body.get(name):
                item[name] = body[name]
        if isinstance(body.get("received_at"), str):
            item["last_received_at"] = body["received_at"]
        payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
        value = payload.get("value")
        name = payload.get("metric_name")
        if body.get("event_type") == "usage_reported" and name in _TOKEN_METRICS \
                and type(value) in (int, float) and value >= 0:
            by_metric = item["tokens_by_metric"]
            by_metric[name] = int(by_metric.get(name, 0)) + int(value)
            item["token_samples"] = int(item["token_samples"]) + 1
            if name == "total_tokens":
                item["tokens_total"] = int(item["tokens_total"] or 0) + int(value)
    return {"attempts": attempts, "cursor": int(rows[-1]["rowid"]) if rows else since_rowid, "truncated": truncated}


__all__ = ["MAX_ACTIVITY_EVENTS", "MAX_SUMMARY_EVENTS", "activity", "attempt_summaries", "events", "incidents",
           "metrics", "status"]
