"""Request-origin validation and bounded in-process rate limiting for the gateway."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from urllib.parse import urlsplit


def _normalized_origin(value: str) -> tuple[str, str, int] | None:
    parsed = urlsplit(value)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
            or parsed.path or parsed.query or parsed.fragment):
        return None
    try:
        port = parsed.port
    except ValueError:
        return None
    return parsed.scheme.lower(), parsed.hostname.lower(), port or (443 if parsed.scheme == "https" else 80)


def origin_matches(origin: str | None, allowed_origin: str) -> bool:
    """Compare browser origins by scheme, hostname and effective port."""
    if not origin:
        return False
    supplied = _normalized_origin(origin)
    return supplied is not None and supplied == _normalized_origin(allowed_origin)


class RateLimiter:
    """Track recent events per scope and client key using a rolling time window."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, max_keys: int = 10_000) -> None:
        self._clock = clock
        self._max_keys = max_keys
        self._events: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()

    def acquire(self, scope: str, key: str, limit: int, window_seconds: float) -> bool:
        """Atomically allow and record an event unless the rolling limit is already reached."""
        now = self._clock()
        with self._lock:
            identity = (scope, key)
            events = self._recent_events(identity, now, window_seconds)
            if len(events) >= limit:
                return False
            events.append(now)
            if len(self._events) > self._max_keys:
                oldest = min(self._events, key=lambda item: self._events[item][-1])
                del self._events[oldest]
            return True

    def reset(self, scope: str, key: str) -> None:
        with self._lock:
            self._events.pop((scope, key), None)

    def _recent_events(self, identity: tuple[str, str], now: float, window_seconds: float) -> deque[float]:
        events = self._events.setdefault(identity, deque())
        while events and now - events[0] >= window_seconds:
            events.popleft()
        if not events:
            self._events.pop(identity, None)
            return self._events.setdefault(identity, deque())
        return events
