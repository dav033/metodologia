"""Snapshot cache and event fan-out shared by every browser client.

The runtime polls the laptop once per cycle and publishes into this hub; clients only read from it,
so the laptop load does not depend on how many clients are connected.
"""

from __future__ import annotations

import json
import time
import uuid
from collections import deque
from threading import Condition
from typing import Any

BACKLOG_LIMIT = 1000


class StreamHub:
    def __init__(self, backlog_limit: int = BACKLOG_LIMIT, clock: Any = time.time):
        self._cond = Condition()
        self._clock = clock
        self._epoch = uuid.uuid4().hex[:8]
        self._backlog: deque[tuple[int, dict[str, Any]]] = deque(maxlen=backlog_limit)
        self._last_seq = 0
        self._snapshot: dict[str, Any] | None = None
        self._snapshot_at: float | None = None
        self._online = True
        self._closed = False

    def publish(self, event: dict[str, Any]) -> str:
        with self._cond:
            self._last_seq += 1
            self._backlog.append((self._last_seq, event))
            self._cond.notify_all()
            return f"{self._epoch}:{self._last_seq}"

    def update_snapshot(self, snapshot: dict[str, Any]) -> None:
        with self._cond:
            self._snapshot = snapshot
            self._snapshot_at = self._clock()

    def set_online(self, online: bool) -> None:
        with self._cond:
            self._online = online
            self._cond.notify_all()

    def read_snapshot(self) -> dict[str, Any]:
        """Cached snapshot with the time it was taken; served as-is while the laptop is offline."""
        with self._cond:
            return {
                "snapshot": self._snapshot,
                "cachedAt": self._snapshot_at,
                "online": self._online,
                "lastEventId": f"{self._epoch}:{self._last_seq}",
            }

    def close(self) -> None:
        with self._cond:
            self._closed = True
            self._cond.notify_all()

    @property
    def closed(self) -> bool:
        return self._closed

    def events_after(self, last_event_id: str | None) -> tuple[list[tuple[str, dict[str, Any]]], bool]:
        """Events newer than `last_event_id` and whether the client must re-fetch the snapshot.

        A resync is needed when the id belongs to another gateway run or the backlog no longer reaches back
        to it; a fresh client (no id) starts at the live edge and has no resync to do.
        """
        with self._cond:
            return self._events_after(last_event_id)

    def _events_after(self, last_event_id: str | None) -> tuple[list[tuple[str, dict[str, Any]]], bool]:
        if not last_event_id:
            return [], False
        epoch, _, raw = last_event_id.partition(":")
        try:
            seq = int(raw)
        except ValueError:
            return [], True
        if epoch != self._epoch or seq > self._last_seq:
            return [], True
        oldest = self._backlog[0][0] if self._backlog else self._last_seq + 1
        if seq + 1 < oldest:
            return [(f"{self._epoch}:{s}", e) for s, e in self._backlog], True
        return [(f"{self._epoch}:{s}", e) for s, e in self._backlog if s > seq], False

    def wait_for_events(self, last_event_id: str | None, timeout: float) -> tuple[list[tuple[str, dict[str, Any]]], bool]:
        """Block until something newer than `last_event_id` exists, the hub closes, or `timeout` passes."""
        with self._cond:
            result = self._events_after(last_event_id)
            if result[0] or result[1] or self._closed:
                return result
            self._cond.wait(timeout)
            return self._events_after(last_event_id)

    def live_cursor(self) -> str:
        with self._cond:
            return f"{self._epoch}:{self._last_seq}"


def format_sse(event_id: str | None, name: str, data: Any) -> bytes:
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {name}")
    lines.append("data: " + json.dumps(data, separators=(",", ":")))
    return ("\n".join(lines) + "\n\n").encode("utf-8")
