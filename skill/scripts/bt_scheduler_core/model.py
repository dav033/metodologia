"""Serialisable run state: the single operational record of one execution (what is happening).

Plain dataclasses with explicit to_dict/from_dict so every repository stores the same JSON. The PLAN.json is never
copied here beyond its identity (plan_id, revision, sha256): the plan says what to do, this says what is going on.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .contracts import route_metadata_valid
from .errors import SchedulerError

STATE_SCHEMA = 8
SEEN_LIMIT = 5000       # applied ids remembered; older ones are still refused by the attempt/token/state guards
REJECTED_LIMIT = 200
OUTBOX_LIMIT = 1000     # above this, settled orders of closed attempts are dropped (the audit log keeps the story)
OUTBOX_KEEP = 500       # ... keeping at least this many of the newest


@dataclass
class TaskRec:
    state: str
    attempts: list[str] = field(default_factory=list)  # attempt ids, oldest first
    budget_base: int = 0       # code attempts consumed before the last authorised reopen (fresh budget after it)
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
    budget_consumed: bool = False  # true only after M3 confirms code execution began
    failure_classification: str = ""  # structured executor classification; detail text is informational


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
    revision_barrier: dict[str, Any] | None = None
    revision_applications: dict[str, dict[str, Any]] = field(default_factory=dict)
    subplan_versions: dict[str, dict[str, Any]] = field(default_factory=dict)
    compositions: dict[str, dict[str, Any]] = field(default_factory=dict)
    frontier_applications: dict[str, dict[str, Any]] = field(default_factory=dict)
    review_holds: dict[str, dict[str, Any]] = field(default_factory=dict)
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
            "revision_barrier": dict(self.revision_barrier) if self.revision_barrier is not None else None,
            "revision_applications": {key: dict(value) for key, value in self.revision_applications.items()},
            "subplan_versions": {key: dict(value) for key, value in self.subplan_versions.items()},
            "compositions": {key: dict(value) for key, value in self.compositions.items()},
            "frontier_applications": {key: dict(value) for key, value in self.frontier_applications.items()},
            "review_holds": {key: dict(value) for key, value in self.review_holds.items()},
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
            if not isinstance(data, dict) or data.get("schema") not in {1, 2, 3, 4, 5, 6, 7, STATE_SCHEMA}:
                raise ValueError("unsupported or missing schema")
            routing_complete = data.get("routing_complete", False)
            if not isinstance(routing_complete, bool):
                raise ValueError("routing_complete must be boolean")
            barrier = data.get("revision_barrier")
            applications = data.get("revision_applications", {})
            barrier_keys = {"operation_key", "source", "target", "deadline"}
            extended_barrier_keys = barrier_keys | {"accepted_map_digest", "accepted_map", "live_attempt_ids"}
            if barrier is not None and (not isinstance(barrier, dict) or
                    frozenset(barrier) not in {frozenset(barrier_keys), frozenset(extended_barrier_keys)} or
                    not isinstance(barrier["operation_key"], str) or not isinstance(barrier["source"], str) or
                    not isinstance(barrier["target"], str) or not isinstance(barrier["deadline"], (int, float)) or
                    isinstance(barrier["deadline"], bool) or
                    (set(barrier) == extended_barrier_keys and
                     (not isinstance(barrier["accepted_map_digest"], str) or
                      re.fullmatch(r"[0-9a-f]{64}", barrier["accepted_map_digest"]) is None or
                      not isinstance(barrier["accepted_map"], dict) or
                      any(not isinstance(task_id, str) or not isinstance(attempt_id, str)
                          for task_id, attempt_id in barrier["accepted_map"].items()) or
                      not isinstance(barrier["live_attempt_ids"], list) or
                      any(not isinstance(attempt_id, str) for attempt_id in barrier["live_attempt_ids"]) or
                      len(barrier["live_attempt_ids"]) != len(set(barrier["live_attempt_ids"]))))):
                raise ValueError("revision barrier is invalid")
            if not isinstance(applications, dict) or any(
                    not isinstance(key, str) or not isinstance(value, dict) or
                    set(value) != {"source", "target", "report", "at"} or
                    not isinstance(value["source"], str) or not isinstance(value["target"], str) or
                    not isinstance(value["report"], dict) or not isinstance(value["at"], (int, float)) or
                    isinstance(value["at"], bool)
                    for key, value in applications.items()):
                raise ValueError("revision applications are invalid")
            versions = data.get("subplan_versions", {})
            if not isinstance(versions, dict) or any(
                    not isinstance(key, str) or re.fullmatch(r"SP-[1-9][0-9]*", key) is None or
                    not isinstance(value, dict) or
                    not {"plan_id", "revision", "version", "commit", "manifest_sha256"} <= set(value) or
                    set(value) - {"plan_id", "revision", "version", "commit", "manifest_sha256",
                                  "audit_attempt_id", "work_digest"} or
                    (("audit_attempt_id" in value or "work_digest" in value) and
                     (not isinstance(value.get("audit_attempt_id"), str) or not value["audit_attempt_id"] or
                      not isinstance(value.get("work_digest"), str) or
                      re.fullmatch(r"[0-9a-f]{64}", value["work_digest"]) is None)) or
                    not isinstance(value["plan_id"], str) or not value["plan_id"] or
                    type(value["revision"]) is not int or value["revision"] < 1 or
                    type(value["version"]) is not int or value["version"] < 1 or
                    not isinstance(value["commit"], str) or re.fullmatch(r"[0-9a-f]{40,64}", value["commit"]) is None or
                    not isinstance(value["manifest_sha256"], str) or
                    re.fullmatch(r"[0-9a-f]{64}", value["manifest_sha256"]) is None
                    for key, value in versions.items()):
                raise ValueError("subplan versions are invalid")
            compositions = data.get("compositions", {})
            if not isinstance(compositions, dict) or any(
                    not isinstance(key, str) or not 1 <= len(key) <= 128 or
                    not isinstance(value, dict) or set(value) - {"plan_id", "revision", "state", "members",
                                                                  "manifest_sha256", "reason", "tree_digest"} or
                    not {"plan_id", "revision", "state", "members", "manifest_sha256", "reason"} <= set(value) or
                    not isinstance(value["plan_id"], str) or not value["plan_id"] or
                    type(value["revision"]) is not int or value["revision"] < 1 or
                    value["state"] not in {"candidate", "published", "rejected"} or
                    not isinstance(value["members"], dict) or not 1 <= len(value["members"]) <= 64 or
                    any(not isinstance(sid, str) or re.fullmatch(r"SP-[1-9][0-9]*", sid) is None or
                        type(version) is not int or version < 1 for sid, version in value["members"].items()) or
                    not isinstance(value["manifest_sha256"], str) or
                    re.fullmatch(r"[0-9a-f]{64}", value["manifest_sha256"]) is None or
                    not isinstance(value["reason"], str) or len(value["reason"]) > 500 or
                    not isinstance(value.get("tree_digest", ""), str) or
                    (value.get("tree_digest", "") and
                     re.fullmatch(r"[0-9a-f]{40,64}", value["tree_digest"]) is None)
                    for key, value in compositions.items()):
                raise ValueError("composition facts are invalid")
            frontier_applications = data.get("frontier_applications", {})
            frontier_fields = {"source_task_id", "composition_id", "manifest_sha256", "tree_digest", "action",
                               "task_ids", "evidence_refs", "plan_id", "revision", "applied_task_ids"}
            if not isinstance(frontier_applications, dict) or any(
                    not isinstance(key, str) or not key or len(key) > 128 or
                    not isinstance(value, dict) or set(value) != frontier_fields or
                    any(not isinstance(value.get(name), str) or not value[name]
                        for name in ("source_task_id", "composition_id", "plan_id")) or
                    not isinstance(value.get("manifest_sha256"), str) or
                    re.fullmatch(r"[0-9a-f]{64}", value["manifest_sha256"]) is None or
                    not isinstance(value.get("tree_digest"), str) or
                    re.fullmatch(r"[0-9a-f]{40,64}", value["tree_digest"]) is None or
                    value.get("action") not in {"none", "reverify", "reintegrate", "audit", "adapt_contract", "modify", "reimplement"} or
                    type(value.get("revision")) is not int or value["revision"] < 1 or
                    not isinstance(value.get("task_ids"), list) or len(value["task_ids"]) > 128 or
                    any(not isinstance(task_id, str) or not task_id for task_id in value["task_ids"]) or
                    len(value["task_ids"]) != len(set(value["task_ids"])) or
                    not isinstance(value.get("evidence_refs"), list) or not 1 <= len(value["evidence_refs"]) <= 32 or
                    any(not isinstance(ref, str) or re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[0-9a-f]{64}", ref) is None
                        for ref in value["evidence_refs"]) or
                    not isinstance(value.get("applied_task_ids"), list) or
                    any(not isinstance(task_id, str) or task_id not in value["task_ids"]
                        for task_id in value["applied_task_ids"]) or
                    (value["action"] == "none") != (not value["task_ids"])
                    for key, value in frontier_applications.items()):
                raise ValueError("frontier applications are invalid")
            review_holds = data.get("review_holds", {})
            review_fields = {"plan_id", "revision", "task_id", "attempt_id", "token", "evidence_ref", "state",
                             "advice"}
            if not isinstance(review_holds, dict) or any(
                    not isinstance(key, str) or not key or not isinstance(value, dict) or
                    set(value) != review_fields or value.get("attempt_id") != key or
                    not isinstance(value.get("plan_id"), str) or not value["plan_id"] or
                    type(value.get("revision")) is not int or value["revision"] < 1 or
                    not isinstance(value.get("task_id"), str) or not value["task_id"] or
                    type(value.get("token")) is not int or value["token"] < 1 or
                    not isinstance(value.get("evidence_ref"), str) or
                    re.fullmatch(r"m6://result/[0-9a-f]{64}", value["evidence_ref"]) is None or
                    value.get("state") not in {"held", "waiting", "resumed", "blocked", "resolved"} or
                    value.get("advice") not in {"", "resume", "wait", "block"}
                    for key, value in review_holds.items()):
                raise ValueError("review holds are invalid")
            state = cls(plan_id=data["plan_id"], revision=data["revision"], plan_sha256=data["plan_sha256"],
                        created_at=data["created_at"], paused=bool(data["paused"]),
                        cancel_requested=bool(data["cancel_requested"]), routing_complete=routing_complete,
                        counters=dict(data["counters"]), schema=STATE_SCHEMA,
                        revision_barrier=dict(barrier) if barrier is not None else None,
                        revision_applications={key: dict(value) for key, value in applications.items()},
                        subplan_versions={key: dict(value) for key, value in versions.items()},
                        compositions={key: dict(value) for key, value in compositions.items()},
                        frontier_applications={key: dict(value) for key, value in frontier_applications.items()},
                        review_holds={key: dict(value) for key, value in review_holds.items()},
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
            state.attempts = {k: AttemptRec(**({**v, "budget_consumed": True}
                                               if "budget_consumed" not in v else v))
                              for k, v in data["attempts"].items()}
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
