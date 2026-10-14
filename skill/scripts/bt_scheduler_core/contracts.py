"""Versioned contracts between the core (M1) and its sibling modules (M2..M5) and the verifier.

Everything crossing a port is a small frozen dataclass of JSON-compatible values, so any adapter (in-process, a queue,
a socket) can carry it. The core validates what comes back; it never trusts a port. Ports are `typing.Protocol`s:
a test double or a real module only needs the methods, no inheritance from this package.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from .errors import SchedulerError
from .states import EventKind

CONTRACT_VERSION = "1.0.0"

ACK = ("accepted", "duplicate", "rejected")
EXEC_STATES = ("running", "finished", "failed", "cancelled", "not_found", "unknown")
RECOVERY_ACTIONS = ("retry", "block", "wait")
FAIL_CAUSES = ("execution_failed", "verification_rejected", "lost")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


@dataclass(frozen=True)
class Event:
    """A fact emitted by a monitor/executor adapter (M4 -> M1). Not exactly-once: may repeat, arrive late or reordered."""
    event_id: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    source: str
    kind: str
    occurred_at: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)
    token: int | None = None        # fencing token of the attempt, when the adapter knows it
    contract_version: str = CONTRACT_VERSION

    @classmethod
    def from_dict(cls, data: Any) -> Event:
        if not isinstance(data, Mapping):
            raise SchedulerError("CONTRACT_VIOLATION", "event must be an object")
        bad = [k for k in ("event_id", "plan_id", "task_id", "attempt_id", "source", "kind") if not _text(data.get(k))]
        rev, token = data.get("revision"), data.get("token")
        if not isinstance(rev, int) or isinstance(rev, bool):
            bad.append("revision")
        if token is not None and (not isinstance(token, int) or isinstance(token, bool)):
            bad.append("token")
        if not isinstance(data.get("payload", {}), Mapping):
            bad.append("payload")
        if bad:
            raise SchedulerError("CONTRACT_VIOLATION", [f"event field invalid or missing: {', '.join(sorted(set(bad)))}"])
        if data["kind"] not in {k.value for k in EventKind}:
            raise SchedulerError("CONTRACT_VIOLATION", [f"unknown event kind {data['kind']!r}"])
        return cls(event_id=data["event_id"], plan_id=data["plan_id"], revision=rev, task_id=data["task_id"],
                   attempt_id=data["attempt_id"], source=data["source"], kind=data["kind"],
                   occurred_at=str(data.get("occurred_at", "")), payload=dict(data.get("payload", {})), token=token,
                   contract_version=str(data.get("contract_version", CONTRACT_VERSION)))

    def to_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, "plan_id": self.plan_id, "revision": self.revision, "task_id": self.task_id,
                "attempt_id": self.attempt_id, "source": self.source, "kind": self.kind, "occurred_at": self.occurred_at,
                "payload": dict(self.payload), "token": self.token, "contract_version": self.contract_version}


@dataclass(frozen=True)
class Verdict:
    """Independent acceptance evidence for one attempt (validator -> M1). Only this can complete a task."""
    verdict_id: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    accepted: bool
    verifier: str
    evidence: str = ""
    token: int | None = None
    occurred_at: str = ""


def verdict_problem(v: object) -> str:
    """'' when `v` satisfies the Verdict contract, else a stable reason. The core never trusts a port's types."""
    if not isinstance(v, Verdict):
        return "verdict_malformed"
    texts = (v.verdict_id, v.plan_id, v.task_id, v.attempt_id)
    if not all(_text(t) for t in texts) or not isinstance(v.revision, int) or isinstance(v.revision, bool):
        return "verdict_malformed"
    if not isinstance(v.accepted, bool) or not isinstance(v.verifier, str) or not isinstance(v.evidence, str):
        return "verdict_malformed"
    if v.token is not None and (not isinstance(v.token, int) or isinstance(v.token, bool)):
        return "verdict_malformed"
    return ""


@dataclass(frozen=True)
class IngestResult:
    status: str        # applied | duplicate | stale | invalid | noop
    reason: str = ""
    event_id: str = ""


@dataclass(frozen=True)
class TaskView:
    """What a sibling module may know about a task: identity, conflict signals, opaque classification."""
    id: str
    milestone_id: str
    repository: str
    shared_resources: tuple[str, ...]
    expected_paths: tuple[str, ...]
    attempts: int
    meta: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssignmentRequest:
    plan_id: str
    revision: int
    ready: tuple[TaskView, ...]     # eligible tasks, in plan order
    free_slots: int
    now: float


@dataclass(frozen=True)
class Assignment:
    task_id: str
    executor: str                   # opaque label; the core never interprets it
    note: str = ""


@dataclass(frozen=True)
class StartOrder:
    idempotency_key: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    token: int
    executor: str
    acceptance_criteria: tuple[str, ...] = ()
    verification: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class CancelOrder:
    idempotency_key: str
    attempt_id: str
    token: int
    reason: str = ""


@dataclass(frozen=True)
class VerifyOrder:
    idempotency_key: str
    plan_id: str
    revision: int
    task_id: str
    attempt_id: str
    token: int
    acceptance_criteria: tuple[str, ...] = ()
    verification: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class Ack:
    status: str                     # accepted | duplicate | rejected
    detail: str = ""


@dataclass(frozen=True)
class ExecutionStatus:
    state: str                      # running | finished | failed | cancelled | not_found | unknown
    detail: str = ""


@dataclass(frozen=True)
class FailureContext:
    plan_id: str
    task_id: str
    attempt_id: str
    cause: str                      # execution_failed | verification_rejected | lost
    attempts_used: int
    max_attempts: int
    detail: str = ""


@dataclass(frozen=True)
class RecoveryProposal:
    action: str                     # retry | block | wait
    reason: str = ""
    wait_seconds: float = 0.0


@runtime_checkable
class AssignmentPort(Protocol):
    """M1 <-> M2. Proposes who runs which eligible task; M1 validates and may refuse any proposal."""
    def propose(self, request: AssignmentRequest) -> Sequence[Assignment]: ...


@runtime_checkable
class ExecutionPort(Protocol):
    """M1 -> M3. Every call carries an idempotency key; `start` twice with the same key must not start two runs."""
    def start(self, order: StartOrder) -> Ack: ...
    def cancel(self, order: CancelOrder) -> Ack: ...
    def query(self, attempt_id: str) -> ExecutionStatus: ...


@runtime_checkable
class VerificationPort(Protocol):
    """Validator -> M1 (request side). The verdict comes back through `submit_verdict`, never as an event."""
    def request(self, order: VerifyOrder) -> Ack: ...


@runtime_checkable
class RecoveryPort(Protocol):
    """M1 <-> M5. Proposes what to do after a failed attempt; it cannot mutate state, only advise."""
    def propose(self, context: FailureContext) -> RecoveryProposal: ...


class EventPort(Protocol):
    """M4 -> M1 (what a monitor sees of the core): hand over facts and verdicts."""
    def ingest(self, event: Event | Mapping[str, Any]) -> IngestResult: ...
    def submit_verdict(self, verdict: Verdict) -> IngestResult: ...
