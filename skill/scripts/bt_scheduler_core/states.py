"""State vocabularies and transition tables: the only place that says what may follow what.

Task states describe the logical unit; attempt states describe one concrete execution. A failed attempt is not a
blocked task: the task goes through RECOVERING and a recovery decision before it is READY again or BLOCKED.
"""
from __future__ import annotations

from enum import Enum


class TaskState(str, Enum):
    PENDING = "pending"        # a prerequisite is not completed yet
    READY = "ready"            # prerequisites accepted; may be reserved
    ACTIVE = "active"          # exactly one live attempt holds the reservation
    RECOVERING = "recovering"  # the last attempt ended badly; a recovery decision is due
    COMPLETED = "completed"    # terminal: an independent verdict accepted the current attempt
    BLOCKED = "blocked"        # attempts exhausted or recovery said stop; reopenable by an authorised operation
    CANCELLED = "cancelled"    # terminal


class AttemptState(str, Enum):
    RESERVED = "reserved"      # capacity/resources held, dispatch intent persisted, executor not confirmed yet
    DISPATCHED = "dispatched"  # executor acknowledged the order
    RUNNING = "running"        # executor reported it started
    VERIFYING = "verifying"    # executor reported it finished; waiting for an independent verdict
    ACCEPTED = "accepted"      # terminal
    FAILED = "failed"          # terminal
    REJECTED = "rejected"      # terminal: verdict refused the work
    CANCELLED = "cancelled"    # terminal
    UNCERTAIN = "uncertain"    # reconciliation could not tell what happened; the reservation is kept (no 2nd writer)


class RunStatus(str, Enum):
    RUNNING = "running"
    PAUSED = "paused"          # operator pause: nothing new is dispatched
    COMPLETED = "completed"    # every task completed with an accepted verdict
    BLOCKED = "blocked"        # nothing can progress, yet not everything is completed (completed_with_blockers)
    CANCELLED = "cancelled"    # authorised cancellation, nothing active left


class EventKind(str, Enum):
    EXECUTION_STARTED = "execution_started"
    EXECUTION_FINISHED = "execution_finished"    # the agent says "done": NOT an acceptance
    EXECUTION_FAILED = "execution_failed"
    EXECUTION_CANCELLED = "execution_cancelled"
    HEARTBEAT = "heartbeat"                       # liveness hint only; never proves death or life


T, A = TaskState, AttemptState

TASK_TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    T.PENDING: frozenset({T.READY, T.CANCELLED}),
    T.READY: frozenset({T.ACTIVE, T.BLOCKED, T.CANCELLED}),
    T.ACTIVE: frozenset({T.COMPLETED, T.RECOVERING, T.CANCELLED}),
    T.RECOVERING: frozenset({T.READY, T.BLOCKED, T.CANCELLED}),
    T.BLOCKED: frozenset({T.READY, T.CANCELLED}),
    T.COMPLETED: frozenset(),
    T.CANCELLED: frozenset(),
}

ATTEMPT_TRANSITIONS: dict[AttemptState, frozenset[AttemptState]] = {
    A.RESERVED: frozenset({A.DISPATCHED, A.RUNNING, A.VERIFYING, A.FAILED, A.CANCELLED, A.UNCERTAIN}),
    A.DISPATCHED: frozenset({A.RUNNING, A.VERIFYING, A.FAILED, A.CANCELLED, A.UNCERTAIN}),
    A.RUNNING: frozenset({A.VERIFYING, A.FAILED, A.CANCELLED, A.UNCERTAIN}),
    # FAILED from VERIFYING is operator-only (resolve_attempt): no executor event may cause it (EVENT_SOURCES)
    A.VERIFYING: frozenset({A.ACCEPTED, A.REJECTED, A.FAILED, A.CANCELLED, A.UNCERTAIN}),
    # RESERVED again only when the executor positively says it never received the order (safe to deliver once more)
    A.UNCERTAIN: frozenset({A.RESERVED, A.DISPATCHED, A.RUNNING, A.VERIFYING, A.FAILED, A.CANCELLED}),
    A.ACCEPTED: frozenset(),
    A.FAILED: frozenset(),
    A.REJECTED: frozenset(),
    A.CANCELLED: frozenset(),
}

ATTEMPT_TERMINAL = frozenset({A.ACCEPTED, A.FAILED, A.REJECTED, A.CANCELLED})
ATTEMPT_LIVE = frozenset(set(AttemptState) - ATTEMPT_TERMINAL)
TASK_TERMINAL = frozenset({T.COMPLETED, T.CANCELLED})

# Which attempt state an executor event leads to, from which states (anything else is stale or invalid).
_EARLY = frozenset({A.RESERVED, A.DISPATCHED, A.UNCERTAIN})
EVENT_SOURCES: dict[EventKind, frozenset[AttemptState]] = {
    EventKind.EXECUTION_STARTED: _EARLY,
    EventKind.EXECUTION_FINISHED: _EARLY | {A.RUNNING},
    EventKind.EXECUTION_FAILED: _EARLY | {A.RUNNING},
    EventKind.EXECUTION_CANCELLED: ATTEMPT_LIVE,
}
EVENT_TARGETS: dict[EventKind, AttemptState] = {
    EventKind.EXECUTION_STARTED: A.RUNNING,
    EventKind.EXECUTION_FINISHED: A.VERIFYING,
    EventKind.EXECUTION_FAILED: A.FAILED,
    EventKind.EXECUTION_CANCELLED: A.CANCELLED,
}
# Order in which a live attempt advances; used to tell "already past this" (stale/duplicate) from "invalid".
_RANK = {A.RESERVED: 0, A.DISPATCHED: 1, A.RUNNING: 2, A.VERIFYING: 3, A.UNCERTAIN: 1}


def rank(state: AttemptState) -> int:
    return _RANK.get(state, 4)
