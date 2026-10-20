"""Thread-safe cached snapshot and replayable event stream for HTTP clients."""

from __future__ import annotations

import copy
import json
import threading
from collections import deque
from typing import Any


class SnapshotEventStream:
    """Keep the latest laptop snapshot and event history for reconnecting clients."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._snapshot: dict[str, Any] | None = None
        self._snapshot_fetched_at: str | None = None
        self._events: deque[tuple[int, dict[str, Any]]] = deque()
        self._next_id = 1

    def update_snapshot(self, snapshot: dict[str, Any], fetched_at: str) -> None:
        with self._condition:
            self._snapshot = copy.deepcopy(snapshot)
            self._snapshot_fetched_at = fetched_at

    def snapshot(self) -> dict[str, Any] | None:
        with self._condition:
            if self._snapshot is None:
                return None
            result = copy.deepcopy(self._snapshot)
            result["cachedAt"] = self._snapshot_fetched_at
            return result

    def publish(self, events: list[dict[str, Any]]) -> None:
        with self._condition:
            for event in events:
                self._events.append((self._next_id, copy.deepcopy(event)))
                self._next_id += 1
            if events:
                self._condition.notify_all()

    def after(self, last_event_id: str | None) -> list[tuple[int, dict[str, Any]]]:
        cursor = self.parse_last_event_id(last_event_id)
        with self._condition:
            return [(event_id, copy.deepcopy(event)) for event_id, event in self._events if event_id > cursor]

    def wait_after(self, last_event_id: int, timeout: float) -> list[tuple[int, dict[str, Any]]]:
        with self._condition:
            self._condition.wait_for(lambda: self._next_id - 1 > last_event_id, timeout=timeout)
            return [(event_id, copy.deepcopy(event)) for event_id, event in self._events if event_id > last_event_id]

    @staticmethod
    def parse_last_event_id(value: str | None) -> int:
        if value is None or value == "":
            return 0
        try:
            parsed = int(value)
        except ValueError as exc:
            raise ValueError("invalid Last-Event-ID") from exc
        if parsed < 0:
            raise ValueError("invalid Last-Event-ID")
        return parsed


def encode_sse(event_id: int, event: dict[str, Any]) -> bytes:
    data = json.dumps(event, separators=(",", ":"), ensure_ascii=False)
    return f"id: {event_id}\ndata: {data}\n\n".encode("utf-8")
