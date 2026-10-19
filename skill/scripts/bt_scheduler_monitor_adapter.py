"""Methodology boundary for sending durable M4 incident references to M1."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bt_scheduler_monitor.activity import ActivityState
from bt_scheduler_monitor.contracts import (
    NORMALIZER_VERSION,
    SCHEMA_VERSION,
    DroppedRange,
    ExecutionOutputFrame,
    MetricSample,
    NormalizedEvent,
    ProcessIdentity,
)
from bt_scheduler_monitor.detectors import STDERR_TEXT, DetectorContext, detect_events
from bt_scheduler_monitor.metrics import read_metric_snapshots as _read_metric_snapshots
from bt_scheduler_monitor.providers import (
    CollectorOutput,
    JsonlCollector,
    ProviderGap,
    ProviderRecord,
)
from bt_scheduler_monitor.queries import activity, attempt_summaries, events, incidents, metrics, status
from bt_scheduler_monitor.recovery import (
    RecoveryError,
    export_archive,
    prepare_candidate,
    verify_archive,
    verify_candidate,
)
from bt_scheduler_monitor.redaction import allowlist_payload
from bt_scheduler_monitor.storage_limits import StoreError
from bt_scheduler_monitor.store import (
    MonitorStore,
    OutboxItem,
    SourceCursor,
    StreamGapRecord,
)
from bt_scheduler_monitor.stream import BoundedFrameQueue, GapCapacityError, StreamGap

REQUIRED_M1_CONTRACT = "1.2.0"


@dataclass(frozen=True)
class IncidentDeliveryReport:
    status: str
    claimed: int = 0
    applied: int = 0
    duplicate: int = 0
    pending: int = 0


def _supports_incident_contract(scheduler: object) -> bool:
    import bt_scheduler_adapter as m1

    return m1.supports_incident_observed(scheduler)


def _incident_event(item: OutboxItem, store: MonitorStore, scheduler: Any) -> dict[str, object]:
    import bt_scheduler_adapter as m1

    incident = store.get_incident(item.incident_id)
    if incident is None:
        raise ValueError("incident_reference_missing")
    return m1.build_incident_observed_event(scheduler, dict(item.payload), confidence=incident.confidence,
                                            idempotency_key=item.idempotency_key,
                                            observed_at=incident.last_seen_at)


def deliver_incident_outbox(store: MonitorStore, scheduler: Any, claim_token: str, *, now: float,
                            lease_seconds: float = 30.0, limit: int = 100) -> IncidentDeliveryReport:
    """Deliver one bounded outbox batch; only applied/duplicate M1 results are acknowledged."""
    if not _supports_incident_contract(scheduler):
        return IncidentDeliveryReport("unsupported_contract")
    claimed = store.claim_outbox(claim_token, now=now, lease_seconds=lease_seconds, limit=limit)
    applied = duplicate = pending = 0
    for item in claimed:
        try:
            result = scheduler.ingest(_incident_event(item, store, scheduler))
            if result.status in ("applied", "duplicate"):
                if store.ack_outbox(item.idempotency_key, item.claim_token):
                    applied += result.status == "applied"
                    duplicate += result.status == "duplicate"
                else:
                    pending += 1
            else:
                store.retry_outbox(item.idempotency_key, item.claim_token, "rejected")
                pending += 1
        except (OSError, StoreError, ValueError, sqlite3.Error):
            store.retry_outbox(item.idempotency_key, item.claim_token, "unknown")
            pending += 1
    return IncidentDeliveryReport("complete", len(claimed), applied, duplicate, pending)


def attempt_usage(path: str | Path, *, since_rowid: int = 0) -> dict[str, object]:
    """Read-only per-attempt activity and provider-reported tokens from an M4 store (see M4 `attempt_summaries`)."""
    return attempt_summaries(path, since_rowid=since_rowid)


def read_metric_snapshots(path: str | Path, *, limit: int = 100) -> tuple[MetricSample, ...]:
    """Expose bounded M4 metric history to M2 without granting a write or refresh path."""
    return _read_metric_snapshots(path, limit=limit)


def persist_frame_event(queue: BoundedFrameQueue, store: MonitorStore, frame: ExecutionOutputFrame,
                        event: NormalizedEvent, cursor: SourceCursor) -> bool:
    """Commit a normalized frame event before acknowledging its in-memory queue slot."""
    return queue.persist_event(store, frame, event, cursor)


def operator_query(command: str, path: str | Path, *, limit: int = 50,
                   execution_id: str | None = None, state: str | None = None) -> dict[str, object]:
    """Run one bounded read-only SSH operator query against the M4 store."""
    if command == "status":
        return status(path)
    if command == "events":
        return events(path, limit=limit, execution_id=execution_id)
    if command == "activity":
        return activity(path, limit=limit, execution_id=execution_id)
    if command == "incidents":
        return incidents(path, limit=limit, resolution_state=state)
    if command == "metrics":
        return metrics(path, limit=limit)
    raise ValueError("unsupported monitor query")


def create_stream_adapter(project_state: str | Path, *, max_frames: int = 10_000,
                          max_bytes: int = 16 * 1024 * 1024, max_open_streams: int = 2) -> Any:
    """Create the methodology-owned M3 FIFO bridge without exposing M4 internals to its caller."""
    from bt_scheduler_stream_adapter import M3StreamAdapter

    return M3StreamAdapter(project_state, max_frames=max_frames, max_bytes=max_bytes,
                           max_open_streams=max_open_streams)


__all__ = [
    "NORMALIZER_VERSION",
    "REQUIRED_M1_CONTRACT",
    "SCHEMA_VERSION",
    "ActivityState",
    "BoundedFrameQueue",
    "CollectorOutput",
    "DetectorContext",
    "DroppedRange",
    "ExecutionOutputFrame",
    "GapCapacityError",
    "IncidentDeliveryReport",
    "JsonlCollector",
    "MetricSample",
    "MonitorStore",
    "NormalizedEvent",
    "ProcessIdentity",
    "ProviderGap",
    "ProviderRecord",
    "RecoveryError",
    "SourceCursor",
    "StoreError",
    "StreamGap",
    "StreamGapRecord",
    "allowlist_payload",
    "create_stream_adapter",
    "deliver_incident_outbox",
    "detect_events",
    "STDERR_TEXT",
    "export_archive",
    "operator_query",
    "persist_frame_event",
    "prepare_candidate",
    "read_metric_snapshots",
    "verify_archive",
    "verify_candidate",
]
