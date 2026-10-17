"""M4 ports used by the Scheduler owner loop; low-level composition remains optional."""
from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import bt_scheduler_decision_adapter as m2_adapter
import bt_scheduler_monitor_adapter as m4_adapter
from bt_scheduler_m4_stream_bridge import M4StreamIngestor
from bt_scheduler_stream_adapter import M3StreamAdapter

M3_LIVE_STATES = ("queued", "preparing", "running", "settling")
M3_TERMINAL_STATES = ("finished", "failed", "cancelled", "rejected")
MAX_TERMINAL_STREAMS_PER_POLL = 32


@dataclass
class M3StreamCandidates:
    """Track active streams and queue terminal streams without rescanning owner history."""

    pending: set[str] = field(default_factory=set)
    queue: deque[str] = field(default_factory=deque)
    queued: set[str] = field(default_factory=set)
    live: set[str] = field(default_factory=set)

    def track(self, attempt_id: str) -> None:
        if not isinstance(attempt_id, str) or not attempt_id:
            raise TypeError("M3 stream candidate must be non-empty text")
        if attempt_id not in self.pending:
            self.pending.add(attempt_id)
            self.queue_pending(attempt_id)

    def queue_pending(self, attempt_id: str) -> None:
        if attempt_id in self.pending and attempt_id not in self.queued:
            self.queue.append(attempt_id)
            self.queued.add(attempt_id)

    def update_live(self, attempt_ids: set[str]) -> set[str]:
        for attempt_id in attempt_ids:
            if attempt_id not in self.pending:
                self.track(attempt_id)
        for attempt_id in self.live - attempt_ids:
            self.queue_pending(attempt_id)
        self.live = set(attempt_ids)
        return set(self.live)

    def take_terminal_batch(self, live_attempts: set[str], *, limit: int) -> tuple[str, ...]:
        batch = []
        for _ in range(limit):
            if not self.queue:
                break
            attempt_id = self.queue.popleft()
            self.queued.discard(attempt_id)
            if attempt_id in self.pending and attempt_id not in live_attempts:
                batch.append(attempt_id)
        return tuple(batch)

    def forget(self, attempt_id: str) -> None:
        self.pending.discard(attempt_id)
        self.queued.discard(attempt_id)
        self.live.discard(attempt_id)


@dataclass
class MonitorRuntime:
    store: m4_adapter.MonitorStore
    ingestor: M4StreamIngestor
    store_path: Path
    scheduler: Any

    def consume(self, execution_id: str, stream_adapter: M3StreamAdapter) -> int:
        return self.ingestor.consume(execution_id,
            terminal_drained=stream_adapter.is_terminal_drained(execution_id))

    def metric_snapshots_for_route(self, *, provider: str, profile: str | None, model: str | None,
                                   name: str, unit: str, comparability_key: str
                                   ) -> tuple[m4_adapter.MetricSample, ...]:
        samples = m4_adapter.read_metric_snapshots(self.store_path)
        return m2_adapter.metric_samples_for_route(
            samples, provider=provider, profile=profile, model=model, name=name, unit=unit,
            comparability_key=comparability_key)

    def deliver_incidents(self, claim_token: str, *, now: float,
                          lease_seconds: float = 30.0, limit: int = 100
                          ) -> m4_adapter.IncidentDeliveryReport:
        return m4_adapter.deliver_incident_outbox(self.store, self.scheduler, claim_token, now=now,
                                                  lease_seconds=lease_seconds, limit=limit)

    def pending_incident_count(self) -> int:
        report = m4_adapter.operator_query("status", self.store_path)
        pending = report.get("outbox_pending")
        if type(pending) is not int or pending < 0:
            raise RuntimeError("M4 returned an invalid pending incident count")
        return pending


def create_monitor_runtime(stream_adapter: M3StreamAdapter, store_path: Path | str | None,
                           scheduler_db: Path, scheduler: Any) -> MonitorRuntime | None:
    if store_path is None:
        return None
    resolved_path = Path(store_path).resolve()
    if resolved_path == Path(scheduler_db).resolve():
        raise ValueError("M4 monitor store must be separate from the M1 scheduler database")
    store = m4_adapter.MonitorStore(resolved_path)
    return MonitorRuntime(store, M4StreamIngestor(stream_adapter.queue, store), resolved_path, scheduler)


def seed_terminal_streams(wiring: Any) -> int:
    """Seed every durable M3 terminal attempt once when the Scheduler owner starts or resumes."""
    attempt_ids = wiring.executor.ledger.ids_in_states(M3_TERMINAL_STATES)
    for attempt_id in attempt_ids:
        wiring.stream_candidates.track(attempt_id)
    return len(attempt_ids)


def drain_pending_streams(wiring: Any, run_id: str) -> int:
    """Drain one bounded batch from tracked M3 attempts into the required M4 observer."""
    if wiring.monitor is None:
        raise RuntimeError("M4 monitor is required by the Scheduler owner runtime")
    total = 0
    live_order = wiring.executor.ledger.ids_in_states(M3_LIVE_STATES)
    live_ids = set(live_order)
    live_attempts = wiring.stream_candidates.update_live(live_ids)
    open_readers = {attempt_id for attempt_id in live_order if wiring.stream_adapter.reader_open(attempt_id)}
    active = [attempt_id for attempt_id in live_order if attempt_id in open_readers]
    active.extend(attempt_id for attempt_id in live_order if attempt_id not in open_readers)
    for attempt_id in active:
        if wiring.stream_adapter.can_open_reader(attempt_id):
            total += _drain_candidate(wiring, attempt_id, run_id)
    terminal = wiring.stream_candidates.take_terminal_batch(
        live_attempts, limit=MAX_TERMINAL_STREAMS_PER_POLL)
    for index, attempt_id in enumerate(terminal):
        if not wiring.stream_adapter.can_open_reader(attempt_id):
            for queued_id in terminal[index:]:
                wiring.stream_candidates.queue_pending(queued_id)
            break
        total += _drain_candidate(wiring, attempt_id, run_id)
    return total


def drain_stream(wiring: Any, attempt_id: str, run_id: str, *, description: Mapping[str, Any] | None = None) -> int:
    """Drain one bounded M3 batch, bound to the active M1 run identity."""
    import bt_scheduler_executor_adapter as executor_runtime

    if not isinstance(run_id, str):
        raise TypeError("run_id must be text")
    if run_id != executor_runtime.run_identity(wiring.scheduler):
        raise ValueError("run_id must match the active M1 run identity")
    described = description if description is not None else wiring.executor.describe(attempt_id)
    if described is None:
        raise LookupError("cannot drain an unknown M3 attempt")
    if not isinstance(described, Mapping):
        raise TypeError("M3 attempt description must be an object")
    stream = described.get("stream")
    artifacts = described.get("artifacts")
    state = described.get("state")
    if not isinstance(stream, Mapping) or not isinstance(artifacts, Mapping) \
            or not isinstance(artifacts.get("dir"), str) or not isinstance(state, str):
        raise TypeError("M3 attempt description is invalid")
    status = dict(stream)
    status["state"] = state
    count = wiring.stream_adapter.drain(
        status, Path(artifacts["dir"]), run_id=run_id, preserve_for_consumer=True)
    if wiring.monitor is not None:
        wiring.monitor.consume(attempt_id, wiring.stream_adapter)
        if wiring.stream_adapter.is_terminal_drained(attempt_id):
            wiring.stream_adapter.forget(attempt_id, preserve_terminal=True)
    return count


def _drain_candidate(wiring: Any, attempt_id: str, run_id: str) -> int:
    description = wiring.executor.describe(attempt_id)
    if description is None:
        wiring.stream_candidates.forget(attempt_id)
        return 0
    if not _has_stream_activity(description):
        if description.get("state") in M3_TERMINAL_STATES:
            wiring.stream_candidates.forget(attempt_id)
        return 0
    total = wiring.drain_stream(attempt_id, run_id, description=description)
    if description.get("state") in M3_TERMINAL_STATES:
        if wiring.stream_adapter.is_terminal_drained(attempt_id):
            wiring.stream_candidates.forget(attempt_id)
        else:
            wiring.stream_candidates.queue_pending(attempt_id)
    return total


def has_live_attempts(wiring: Any) -> bool:
    """Whether the M3 owner may still create a stream endpoint for an accepted attempt."""
    return wiring.executor.ledger.count(M3_LIVE_STATES) > 0


def has_pending_streams(wiring: Any) -> bool:
    """Whether active or terminal M3 output still needs bounded M4 processing."""
    return bool(wiring.stream_candidates.pending)


def has_pending_incidents(wiring: Any) -> bool:
    """Whether durable M4 incident references still need delivery through M1."""
    if wiring.monitor is None:
        raise RuntimeError("M4 monitor is required by the Scheduler owner runtime")
    pending = wiring.monitor.pending_incident_count()
    if type(pending) is not int or pending < 0:
        raise RuntimeError("M4 returned an invalid pending incident count")
    return pending > 0


def _has_stream_activity(description: Any) -> bool:
    if not isinstance(description, dict):
        raise TypeError("M3 attempt description must be an object")
    state, artifacts = description.get("state"), description.get("artifacts")
    if not isinstance(state, str) or not isinstance(artifacts, dict) or not isinstance(artifacts.get("dir"), str):
        raise TypeError("M3 attempt description is invalid")
    attempt_dir = Path(artifacts["dir"])
    if state not in {"finished", "failed", "cancelled", "rejected"}:
        return True
    return any(_entry_exists(attempt_dir / name) for name in ("stream.fifo", "shim.json", "stream.json", "exit.json"))


def _entry_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def deliver_incidents(wiring: Any, claim_token: str, *, now: float) -> m4_adapter.IncidentDeliveryReport:
    """Deliver M4's bounded audit-only outbox through the M1 event boundary."""
    if wiring.monitor is None:
        raise RuntimeError("M4 monitor is required by the Scheduler owner runtime")
    return wiring.monitor.deliver_incidents(claim_token, now=now)


__all__ = ["M3StreamCandidates", "MonitorRuntime", "create_monitor_runtime", "deliver_incidents",
           "drain_pending_streams", "drain_stream", "has_live_attempts", "has_pending_incidents", "has_pending_streams",
           "seed_terminal_streams"]
