"""Snapshot cache and SSE fan-out: one laptop poller serves any number of clients."""

from __future__ import annotations

import json
import queue
import threading
import time
from collections import deque
from typing import Any, Callable

from upstream import UpstreamError


def format_sse(event_id: int | None, name: str, data: Any) -> bytes:
    """Encode one Server-Sent Event frame."""
    lines = []
    if event_id is not None:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {name}")
    lines.append("data: " + json.dumps(data, separators=(",", ":")))
    return ("\n".join(lines) + "\n\n").encode("utf-8")


def parse_last_event_id(value: str | None) -> int | None:
    """Return the resume position from a Last-Event-ID header, or None if absent/invalid."""
    if value is None:
        return None
    value = value.strip()
    if not value.isdigit():
        return None
    return int(value)


class Subscription:
    """One client's ordered stream; frames are (id, name, data) tuples."""

    def __init__(self, hub: "StreamHub"):
        self._hub = hub
        self._queue: queue.Queue = queue.Queue()

    def _put(self, item: tuple[int | None, str, Any]) -> None:
        self._queue.put(item)

    def get(self, timeout: float | None = None) -> tuple[int | None, str, Any] | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def drain(self) -> list[tuple[int | None, str, Any]]:
        items = []
        while True:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                return items

    def close(self) -> None:
        self._hub._unsubscribe(self)


class StreamHub:
    def __init__(self, laptop: Any, buffer_size: int = 1000, clock: Callable[[], float] = time.time):
        self._laptop = laptop
        self._clock = clock
        self._lock = threading.Lock()
        self._buffer: deque[tuple[int, dict[str, Any]]] = deque(maxlen=buffer_size)
        self._subscribers: list[Subscription] = []
        self._snapshot: dict[str, Any] | None = None
        self._snapshot_at: float | None = None
        self._online = False
        self._seq = 0
        self._cursor = ""

    # --- polling (the only code that talks to the laptop) ---

    def poll_once(self) -> None:
        try:
            snapshot = self._laptop.snapshot()
            result = self._laptop.events(self._cursor)
        except UpstreamError:
            with self._lock:
                changed = self._online
                self._online = False
                if changed:
                    self._broadcast(None, "status", self._status_locked())
            return
        events = result.get("events")
        events = [e for e in events if isinstance(e, dict)] if isinstance(events, list) else []
        with self._lock:
            was_online = self._online
            self._online = True
            self._snapshot = snapshot
            self._snapshot_at = self._clock()
            next_cursor = result.get("nextCursor")
            if isinstance(next_cursor, str):
                self._cursor = next_cursor
            if not was_online:
                self._broadcast(None, "status", self._status_locked())
            for event in events:
                self._seq += 1
                self._buffer.append((self._seq, event))
                self._broadcast(self._seq, "event", event)

    def _broadcast(self, event_id: int | None, name: str, data: Any) -> None:
        for sub in self._subscribers:
            sub._put((event_id, name, data))

    # --- reads served from cache ---

    def _status_locked(self) -> dict[str, Any]:
        return {"online": self._online, "cachedAt": self._snapshot_at}

    def _snapshot_payload_locked(self) -> dict[str, Any]:
        return {
            "snapshot": self._snapshot,
            "cachedAt": self._snapshot_at,
            "stale": not self._online,
            "lastEventId": self._seq,
        }

    def cached_snapshot(self) -> dict[str, Any]:
        """The last good snapshot with its time; stale=True while the laptop is offline."""
        with self._lock:
            return self._snapshot_payload_locked()

    # --- fan-out ---

    def subscribe(self, last_event_id: int | None = None) -> Subscription:
        """Register a client; replay everything after last_event_id atomically with registration."""
        sub = Subscription(self)
        with self._lock:
            if last_event_id is None:
                sub._put((None, "snapshot", self._snapshot_payload_locked()))
            else:
                oldest = self._buffer[0][0] if self._buffer else self._seq + 1
                if last_event_id < oldest - 1:
                    # The gap fell out of the buffer: the client must resync from a snapshot.
                    sub._put((None, "snapshot", self._snapshot_payload_locked()))
                else:
                    for seq, event in self._buffer:
                        if seq > last_event_id:
                            sub._put((seq, "event", event))
            sub._put((None, "status", self._status_locked()))
            self._subscribers.append(sub)
        return sub

    def _unsubscribe(self, sub: Subscription) -> None:
        with self._lock:
            if sub in self._subscribers:
                self._subscribers.remove(sub)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)
