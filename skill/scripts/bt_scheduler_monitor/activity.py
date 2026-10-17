"""Per-attempt activity projection from normalized M4 events."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from .contracts import NormalizedEvent, ProcessIdentity
from .process_identity import corroborate_process_identity

_STREAM_INTEGRITY = frozenset(("complete", "gapped", "unknown"))
_M3_PROCESS_STATES = frozenset(("running", "terminal", "unknown"))
MAX_ACTIVITY_ITEMS = 256
MAX_RECENT_EVENT_IDS = 1_024
MAX_DROPPED_COUNT = 2**31 - 1


@dataclass(frozen=True)
class ActivityView:
    run_id: str | None
    task_id: str | None
    attempt_id: str | None
    execution_id: str | None
    provider: str | None
    profile_id: str | None
    model: str | None
    process_identity: ProcessIdentity | None
    last_source_event_type: str | None
    last_source_at: str | None
    last_received_io_at: str | None
    last_received_monotonic_ns: int | None
    last_sequence: int | None
    last_offset_bytes: int | None
    last_tool_label: str | None
    pending_tools: tuple[str, ...]
    metrics: tuple[NormalizedEvent, ...]
    stream_integrity: str
    process_status: str
    display_state: str
    identity_corroboration: str
    pending_tools_truncated: bool
    metrics_truncated: bool
    projection_truncated: bool
    pending_tools_dropped_count: int
    metrics_dropped_count: int
    pending_tools_uncertain: bool


@dataclass
class ActivityState:
    """Accumulates only normalized facts for a single execution attempt."""

    _identity: tuple[str, str, str, str] | None = field(default=None, init=False, repr=False)
    _provider: str | None = field(default=None, init=False, repr=False)
    _profile_id: str | None = field(default=None, init=False, repr=False)
    _model: str | None = field(default=None, init=False, repr=False)
    _process_identity: ProcessIdentity | None = field(default=None, init=False, repr=False)
    _last_source_event: NormalizedEvent | None = field(default=None, init=False, repr=False)
    _last_received_event: NormalizedEvent | None = field(default=None, init=False, repr=False)
    _last_tool_event: NormalizedEvent | None = field(default=None, init=False, repr=False)
    _pending_tools: list[str] = field(default_factory=list, init=False, repr=False)
    _tool_lifecycle_events: list[NormalizedEvent] = field(default_factory=list, init=False, repr=False)
    _tool_history_truncated: bool = field(default=False, init=False, repr=False)
    _pending_tools_uncertain: bool = field(default=False, init=False, repr=False)
    _metrics: list[NormalizedEvent] = field(default_factory=list, init=False, repr=False)
    _recent_event_ids: deque[str] = field(default_factory=deque, init=False, repr=False)
    _recent_event_id_set: set[str] = field(default_factory=set, init=False, repr=False)
    _pending_tools_dropped_count: int = field(default=0, init=False, repr=False)
    _metrics_dropped_count: int = field(default=0, init=False, repr=False)
    _stream_integrity: str = field(default="unknown", init=False, repr=False)

    def add(self, event: NormalizedEvent) -> None:
        if not isinstance(event, NormalizedEvent):
            raise ValueError("activity accepts normalized events only")
        identity = (event.run_id, event.task_id, event.attempt_id, event.execution_id)
        if self._identity is None:
            self._identity = identity
            self._provider, self._profile_id, self._model = event.provider, event.profile_id, event.model
            self._process_identity = event.process_identity
        elif identity != self._identity:
            raise ValueError("event belongs to a different attempt")
        elif (event.provider != self._provider or event.profile_id != self._profile_id
              or event.model != self._model or event.process_identity != self._process_identity):
            raise ValueError("event provider, profile, model or process identity disagrees within an attempt")

        # Persistent event-ID dedupe belongs to the store; callers must provide its
        # deduplicated stream for replays older than this bounded recent-ID cache.
        if event.event_id in self._recent_event_id_set:
            return
        if len(self._recent_event_ids) >= MAX_RECENT_EVENT_IDS:
            expired_id = self._recent_event_ids.popleft()
            self._recent_event_id_set.remove(expired_id)
        self._recent_event_ids.append(event.event_id)
        self._recent_event_id_set.add(event.event_id)

        if event.event_type == "stream_gap":
            self._stream_integrity = "gapped"
        elif self._stream_integrity == "unknown":
            self._stream_integrity = "complete"
        if event.event_type in ("tool_started", "tool_finished"):
            self._tool_lifecycle_events.append(event)
            if len(self._tool_lifecycle_events) > MAX_ACTIVITY_ITEMS * 2:
                self._tool_lifecycle_events.pop(0)
                self._tool_history_truncated = True
            self._rebuild_pending_tools()
        elif event.event_type == "usage_reported":
            if len(self._metrics) >= MAX_ACTIVITY_ITEMS:
                self._metrics.pop(0)
                self._metrics_dropped_count = min(MAX_DROPPED_COUNT, self._metrics_dropped_count + 1)
            self._metrics.append(event)
        previous_source_event = self._last_source_event
        if (event.source_occurred_at is not None and self._is_later_source_event(event, previous_source_event)) \
                or (event.source_occurred_at is None and
                    (previous_source_event is None or previous_source_event.source_occurred_at is None) and
                    self._is_later_received_event(event, previous_source_event)):
            self._last_source_event = event
        if self._is_later_received_event(event, self._last_received_event):
            self._last_received_event = event
        if event.event_type in ("tool_started", "tool_finished") and self._is_later_received_event(
            event, self._last_tool_event
        ):
            self._last_tool_event = event

    def _rebuild_pending_tools(self) -> None:
        self._pending_tools_uncertain = self._tool_history_truncated
        known_events = [event for event in self._tool_lifecycle_events if event.source_occurred_at is not None]
        unknown_events = [event for event in self._tool_lifecycle_events if event.source_occurred_at is None]
        if unknown_events:
            self._pending_tools_uncertain = True
        known_events.sort(key=lambda event: (self._utc_value(event.source_occurred_at),
                                             0 if event.event_type == "tool_finished" else 1))
        pending: dict[str, list[NormalizedEvent]] = {}
        same_time_events: dict[tuple[str, str], set[str]] = {}
        for event in known_events:
            label = str(dict(event.payload)["tool_label"])
            timestamp = str(event.source_occurred_at)
            same_time_events.setdefault((label, timestamp), set()).add(event.event_type)
            if event.event_type == "tool_started":
                pending.setdefault(label, []).append(event)
            elif pending.get(label):
                pending[label].pop()
        if any(len(kinds) > 1 for kinds in same_time_events.values()):
            self._pending_tools_uncertain = True
        pending_entries = [(event, label) for label, starts in pending.items() for event in starts]
        pending_entries.extend((event, str(dict(event.payload)["tool_label"])) for event in unknown_events
                               if event.event_type == "tool_started")
        pending_entries.sort(key=lambda item: self._utc_value(item[0].received_at))
        self._pending_tools_dropped_count = min(MAX_DROPPED_COUNT,
                                                max(0, len(pending_entries) - MAX_ACTIVITY_ITEMS))
        self._pending_tools = [label for _, label in pending_entries[-MAX_ACTIVITY_ITEMS:]]

    @staticmethod
    def _utc_value(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @classmethod
    def _is_later_received_event(cls, event: NormalizedEvent, previous: NormalizedEvent | None) -> bool:
        if previous is None:
            return True
        if event.host_boot_id is not None and event.host_boot_id == previous.host_boot_id \
                and event.received_monotonic_ns is not None and previous.received_monotonic_ns is not None:
            return event.received_monotonic_ns >= previous.received_monotonic_ns
        return cls._utc_value(event.received_at) >= cls._utc_value(previous.received_at)

    @classmethod
    def _is_later_source_event(cls, event: NormalizedEvent, previous: NormalizedEvent | None) -> bool:
        if previous is None:
            return True
        if event.source_occurred_at is None or previous.source_occurred_at is None:
            return cls._is_later_received_event(event, previous)
        return cls._utc_value(event.source_occurred_at) >= cls._utc_value(previous.source_occurred_at)

    def snapshot(self, *, proc_identity: ProcessIdentity | None = None,
                 m3_process_identity: ProcessIdentity | None = None, m3_process_state: str = "unknown",
                 stream_integrity: str | None = None,
                 monotonic_now_ns: int | None = None, monotonic_boot_id: str | None = None,
                 silent_after_seconds: float = 300.0) -> ActivityView:
        for value in (proc_identity, m3_process_identity):
            if value is not None and not isinstance(value, ProcessIdentity):
                raise ValueError("process identities must be ProcessIdentity or None")
        if m3_process_state not in _M3_PROCESS_STATES:
            raise ValueError("m3_process_state must be running, terminal, or unknown")
        if monotonic_now_ns is not None and (not isinstance(monotonic_now_ns, int)
                                             or isinstance(monotonic_now_ns, bool) or monotonic_now_ns < 0):
            raise ValueError("monotonic_now_ns must be a nonnegative integer or None")
        if monotonic_boot_id is not None and (not isinstance(monotonic_boot_id, str) or not monotonic_boot_id):
            raise ValueError("monotonic_boot_id must be non-empty text or None")
        m3_identity_result = corroborate_process_identity(self._process_identity, m3_process_identity)
        proc_identity_result = corroborate_process_identity(self._process_identity, proc_identity)
        identity_corroboration = m3_identity_result
        if m3_identity_result == "match" and proc_identity_result not in ("match", "unknown"):
            identity_corroboration = proc_identity_result
        elif m3_identity_result == "unknown" and proc_identity_result not in ("match", "unknown"):
            identity_corroboration = proc_identity_result
        process_status = "unknown"
        if m3_identity_result == "match" and m3_process_state == "running" and proc_identity_result == "match":
            process_status = "alive"
        elif m3_identity_result == "match" and m3_process_state == "terminal" and proc_identity_result != "match":
            process_status = "dead"
        elif m3_identity_result == "match" and m3_process_state == "terminal" and proc_identity_result == "match":
            identity_corroboration = "disagreement"
        integrity = stream_integrity if stream_integrity is not None else self._stream_integrity
        if integrity not in _STREAM_INTEGRITY:
            raise ValueError("stream_integrity must be complete, gapped, or unknown")
        if silent_after_seconds < 0:
            raise ValueError("silent_after_seconds must be nonnegative")
        event = self._last_received_event
        source_event = self._last_source_event
        if process_status == "dead":
            display_state = "process_confirmed_dead"
        elif event is None:
            display_state = "source_disconnected" if integrity == "gapped" else "unknown"
        elif self._pending_tools:
            display_state = "tool_pending"
        elif self._pending_tools_uncertain:
            display_state = "unknown"
        elif process_status == "alive" and monotonic_now_ns is not None and event.received_monotonic_ns is not None \
                and event.host_boot_id is not None and monotonic_boot_id == event.host_boot_id \
                and self._process_identity is not None \
                and self._process_identity.host_boot_id == monotonic_boot_id \
                and monotonic_now_ns >= event.received_monotonic_ns \
                and monotonic_now_ns - event.received_monotonic_ns >= silent_after_seconds * 1_000_000_000:
            display_state = "silent_but_live"
        elif integrity == "gapped":
            display_state = "source_disconnected"
        else:
            display_state = "active"
        run_id, task_id, attempt_id, execution_id = self._identity or (None, None, None, None)
        return ActivityView(
            run_id, task_id, attempt_id, execution_id, self._provider, self._profile_id, self._model,
            self._process_identity, source_event.source_event_type if source_event else None,
            source_event.source_occurred_at if source_event else None, event.received_at if event else None,
            event.received_monotonic_ns if event else None, event.sequence if event else None,
            event.offset_bytes if event else None,
            dict(self._last_tool_event.payload).get("tool_label") if self._last_tool_event else None,
            tuple(self._pending_tools), tuple(self._metrics), integrity, process_status, display_state,
            identity_corroboration, bool(self._pending_tools_dropped_count), bool(self._metrics_dropped_count),
            bool(self._pending_tools_dropped_count or self._metrics_dropped_count or self._tool_history_truncated),
            self._pending_tools_dropped_count, self._metrics_dropped_count, self._pending_tools_uncertain,
        )


__all__ = ["ActivityState", "ActivityView"]
