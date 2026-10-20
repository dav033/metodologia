"""Serialisable run state: the single operational record of one execution (what is happening).

Plain dataclasses with explicit to_dict/from_dict so every repository stores the same JSON. The PLAN.json is never
copied here beyond its identity (plan_id, revision, sha256): the plan says what to do, this says what is going on.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import route_metadata_valid
from .errors import SchedulerError

STATE_SCHEMA = 2
SEEN_LIMIT = 5000       # applied ids remembered; older ones are still refused by the attempt/token/state guards
REJECTED_LIMIT = 200
OUTBOX_LIMIT = 1000     # above this, settled orders of closed attempts are dropped (the audit log keeps the story)
OUTBOX_KEEP = 500       # ... keeping at least this many of the newest


@dataclass
class TaskRec:
    state: str
    attempts: list[str] = field(default_factory=list)  # attempt ids, oldest first
    budget_base: int = 0       # attempts consumed before the last authorised reopen (fresh budget after it)
    reason: str = ""           # why blocked / cancelled
    hold_until: float = 0.0    # recovery asked to wait until this time (epoch seconds)
    waits: int = 0             # how many times recovery asked to wait since the last reopen
    reworks: int = 0           # how many times an audit sent this task back after it was accepted
    route_metadata: dict[str, str] = field(default_factory=dict)
    route_status: str = "unplanned"  # unplanned | recommended | unavailable | assigned
    route_reason: str = ""


@dataclass
class AttemptRec:
    id: str
    task_id: str
    number: int                # 1-based per task
    state: str
    token: int                 # fencing token: strictly increasing across the run
    executor: str              # opaque label chosen by the decision port
    key: str                   # idempotency key of the start order
    created_at: float
    updated_at: float
    lease_expires_at: float
    last_event_at: float = 0.0
    needs_reconcile: bool = False
    failure: str = ""          # cause when failed/rejected/cancelled
    evidence: str = ""         # accepted/rejected verdict evidence
    verifier: str = ""


@dataclass
class OutboxItem:
    id: str
    kind: str                  # start | cancel | verify
    attempt_id: str
    key: str
    status: str = "pending"    # pending | delivered | void
    deliveries: int = 0        # incremented BEFORE the port is called (write-ahead)
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunState:
    plan_id: str
    revision: int
    plan_sha256: str
    created_at: float
    tasks: dict[str, TaskRec] = field(default_factory=dict)
    attempts: dict[str, AttemptRec] = field(default_factory=dict)
    holds: dict[str, list[list[str]]] = field(default_factory=dict)   # attempt id -> [[resource, mode], ...]
    outbox: list[OutboxItem] = field(default_factory=list)
    seen_events: list[str] = field(default_factory=list)      # applied message ids, newest last, bounded (SEEN_LIMIT)
    rejected_recent: list[str] = field(default_factory=list)  # only to avoid auditing the same rejection over and over
    counters: dict[str, int] = field(default_factory=lambda: {"attempt": 0, "token": 0, "outbox": 0, "audit": 0})
    paused: bool = False
    cancel_requested: bool = False
    routing_complete: bool = False
    schema: int = STATE_SCHEMA

    def has_seen(self, message_id: str) -> bool:
        return message_id in self.seen_events      # bounded by SEEN_LIMIT, so a plain scan is cheap

    def remember(self, message_id: str) -> None:
        self.seen_events.append(message_id)
        del self.seen_events[:-SEEN_LIMIT]

    def next(self, counter: str) -> int:
        self.counters[counter] = self.counters.get(counter, 0) + 1
        return self.counters[counter]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema, "plan_id": self.plan_id, "revision": self.revision, "plan_sha256": self.plan_sha256,
            "created_at": self.created_at, "paused": self.paused, "cancel_requested": self.cancel_requested,
            "routing_complete": self.routing_complete,
            "counters": dict(self.counters), "seen_events": list(self.seen_events),
            "rejected_recent": list(self.rejected_recent),
            "tasks": {k: vars(v).copy() for k, v in self.tasks.items()},
            "attempts": {k: vars(v).copy() for k, v in self.attempts.items()},
            "holds": {k: [list(c) for c in v] for k, v in self.holds.items()},
            "outbox": [{**vars(o), "payload": dict(o.payload)} for o in self.outbox],
        }

    @classmethod
    def from_dict(cls, data: Any) -> RunState:
        try:
            if not isinstance(data, dict) or data.get("schema") not in {1, STATE_SCHEMA}:
                raise ValueError("unsupported or missing schema")
            routing_complete = data.get("routing_complete", False)
            if not isinstance(routing_complete, bool):
                raise ValueError("routing_complete must be boolean")
            state = cls(plan_id=data["plan_id"], revision=data["revision"], plan_sha256=data["plan_sha256"],
                        created_at=data["created_at"], paused=bool(data["paused"]),
                        cancel_requested=bool(data["cancel_requested"]), routing_complete=routing_complete,
                        counters=dict(data["counters"]), schema=STATE_SCHEMA,
                        seen_events=list(data["seen_events"]), rejected_recent=list(data.get("rejected_recent", [])))
            state.tasks = {}
            for task_id, value in data["tasks"].items():
                if not isinstance(value, dict):
                    raise ValueError("task record must be an object")
                route_metadata = value.get("route_metadata", {})
                route_status = value.get("route_status", "unplanned")
                route_reason = value.get("route_reason", "")
                if (not isinstance(route_metadata, dict) or not route_metadata_valid(route_metadata) or
                        not isinstance(route_status, str) or
                        route_status not in {"unplanned", "recommended", "unavailable", "assigned"} or
                        not isinstance(route_reason, str) or len(route_reason) > 160 or
                        any(ord(char) < 32 for char in route_reason)):
                    raise ValueError("task route record is invalid")
                state.tasks[task_id] = TaskRec(**value)
            state.attempts = {k: AttemptRec(**v) for k, v in data["attempts"].items()}
            state.holds = {k: [list(c) for c in v] for k, v in data["holds"].items()}
            state.outbox = [OutboxItem(**o) for o in data["outbox"]]
            return state
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SchedulerError("STATE_UNREADABLE", f"{type(exc).__name__}: {exc}") from exc


@dataclass(frozen=True)
class AuditEntry:
    seq: int
    at: float
    kind: str
    plan_id: str
    task_id: str
    attempt_id: str
    detail: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"seq": self.seq, "at": self.at, "kind": self.kind, "plan_id": self.plan_id, "task_id": self.task_id,
                "attempt_id": self.attempt_id, "detail": dict(self.detail)}
