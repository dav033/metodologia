"""The ports the executor needs and never implements itself: structural protocols, any object with the methods fits."""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .model import (
    Brief,
    Classification,
    Launch,
    Route,
    StartRequest,
    TechnicalEvent,
    Workspace,
)


@runtime_checkable
class RouteResolver(Protocol):
    """M2's route reference -> launchable parts. Raises ExecutorError(ROUTE_UNRESOLVABLE | ROUTE_INVALID | POLICY_DENIED)."""
    def resolve(self, request: StartRequest) -> Route: ...


@runtime_checkable
class BriefSource(Protocol):
    """The frozen plan's task as an agent brief. Raises ExecutorError(ORDER_INVALID) for a task it does not know."""
    def brief(self, request: StartRequest) -> Brief: ...


@runtime_checkable
class AgentDriver(Protocol):
    """Provider knowledge: how to launch an agent and how to read what it left. It never decides success."""
    def prepare(self, route: Route, prompt: str, workspace: Workspace, timeout_seconds: float) -> Launch: ...
    def classify(self, route: Route, raw: str, returncode: int | None, *, timed_out: bool = False,
                 cancelled: bool = False) -> Classification: ...


@runtime_checkable
class WorkspaceManager(Protocol):
    """Allocates the isolated checkout of one attempt. Must be idempotent per attempt id (a crashed allocation is reused)."""
    def allocate(self, request: StartRequest) -> Workspace: ...
    def check(self, request: StartRequest) -> str | None: ...   # raises REPOSITORY_UNKNOWN / BASE_UNRESOLVED before any side effect; returns the base commit it pinned (or None)


@runtime_checkable
class EventSink(Protocol):
    """Receives technical events at least once. Raising means "not delivered": the event stays in the outbox."""
    def deliver(self, event: TechnicalEvent) -> None: ...
