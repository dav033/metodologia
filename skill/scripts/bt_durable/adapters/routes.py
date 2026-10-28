"""Router ports. `StaticRouter` serves an ordered list of allowed routes; `capacity` (optional) is the live quota
signal: it returns None (unknown), 0 (no capacity, with an optional reset epoch) or a positive number."""
from __future__ import annotations

from collections.abc import Callable, Sequence

from bt_contracts.execution import Route, RouteDecision, RunRef

from ..legacy import TaskSpec

Capacity = Callable[[Route], tuple[float | None, float | None]]   # (remaining or None if unknown, reset epoch)


def key(route: Route) -> str:
    return f"{route.provider}:{route.profile}:{route.model}"


class StaticRouter:
    def __init__(self, routes: Sequence[Route], capacity: Capacity | None = None):
        if not routes:
            raise ValueError("at least one allowed route is required")
        self.routes = tuple(routes)
        self.capacity = capacity

    def _allowed(self, exclude: tuple[str, ...]) -> list[Route]:
        return [r for r in self.routes if key(r) not in exclude]

    def decide(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...], now: float) -> RouteDecision:
        allowed = self._allowed(exclude)
        if not allowed:
            return RouteDecision(kind="unavailable", reason="every allowed route was excluded for this task")
        resets = []
        for route in allowed:
            remaining, reset = self.capacity(route) if self.capacity else (None, None)
            if remaining is None or remaining > 0:
                return RouteDecision(kind="run", route=route)
            if reset:
                resets.append(reset)
        if resets:
            return RouteDecision(kind="wait", not_before=min(resets), reason="no allowed route has capacity now")
        return RouteDecision(kind="unavailable", reason="no allowed route has capacity and no reset time is known")

    def alternatives(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...]) -> int:
        return len(self._allowed(exclude))
