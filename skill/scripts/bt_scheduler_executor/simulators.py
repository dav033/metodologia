"""Small doubles of the ports, for the CLI self-test and for the authors of M4/M5 who need an executor without a provider.

Nothing here knows a provider: a "route" maps to a plain command line and the classifier reads exit codes only.
"""
from __future__ import annotations

import threading
from collections.abc import Mapping, Sequence

from .errors import ExecutorError
from .model import (
    Brief,
    Classification,
    Launch,
    Route,
    StartRequest,
    TechnicalEvent,
    Workspace,
)


class StaticResolver:
    """`reference -> Route` from a dict; unknown references are unresolvable (never defaulted)."""

    def __init__(self, routes: Mapping[str, Route]):
        self.routes = dict(routes)

    def resolve(self, request: StartRequest) -> Route:
        try:
            return self.routes[request.executor]
        except KeyError:
            raise ExecutorError("ROUTE_UNRESOLVABLE", f"unknown reference {request.executor!r}") from None


class StaticBriefs:
    def brief(self, request: StartRequest) -> Brief:
        return Brief(title=f"task {request.task_id}", objective="(simulated)")


class ScriptedDriver:
    """`route.model` names a command line in `commands`; exit 0 = completed, anything else = failed."""

    def __init__(self, commands: Mapping[str, Sequence[str]]):
        self.commands = {k: tuple(v) for k, v in commands.items()}

    def prepare(self, route: Route, prompt: str, workspace: Workspace, timeout_seconds: float) -> Launch:
        try:
            return Launch(argv=self.commands[route.model])
        except KeyError:
            raise ExecutorError("ROUTE_INVALID", f"no command for model {route.model!r}") from None

    def classify(self, route: Route, raw: str, returncode: int | None, *, timed_out: bool = False,
                 cancelled: bool = False) -> Classification:
        if timed_out:
            return Classification("timeout")
        if returncode:
            return Classification("failed", text=raw[-200:])
        return Classification("completed", terminal_event=True, text=raw[-200:])


class ListSink:
    """Keeps every delivered event; `fail` makes it raise (to exercise redelivery)."""

    def __init__(self) -> None:
        self.events: list[TechnicalEvent] = []
        self.fail = False
        self._lock = threading.Lock()

    def deliver(self, event: TechnicalEvent) -> None:
        with self._lock:
            if self.fail:
                raise RuntimeError("sink unavailable")
            self.events.append(event)
