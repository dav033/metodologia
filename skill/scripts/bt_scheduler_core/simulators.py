"""Deterministic doubles of the sibling modules: enough to run the core end to end with no provider and no network.

`FifoAssignment` is also the core's default decision policy until a real Decision Engine exists: plan order, label
"local". Everything here is plain Python, scripted by the caller; none of it decides anything cognitive.
"""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping

from .contracts import (
    Ack,
    Assignment,
    AssignmentRequest,
    CancelOrder,
    PortNotReady,
    Event,
    ExecutionStatus,
    FailureContext,
    RecoveryProposal,
    StartOrder,
    Verdict,
    VerifyOrder,
)


class FifoAssignment:
    """First eligible tasks in plan order, one label for all of them."""

    def __init__(self, executor: str = "local"):
        self.executor = executor

    def propose(self, request: AssignmentRequest) -> list[Assignment]:
        return [Assignment(t.id, self.executor) for t in request.ready[:request.free_slots]]


class FakeExecutor:
    """ExecutionPort double. Records orders; knows nothing is running unless a test says so.

    `deliveries[key]` counts how many times an order arrived (duplicates are acknowledged, never run twice).
    `crash_after_start` raises a BaseException right after a start order is recorded (a process death at the worst
    moment). `status[attempt_id]` is what `query` answers (default not_found)."""

    class Crash(BaseException):
        """Stands for the scheduler process dying; deliberately not an Exception so the core cannot swallow it."""

    def __init__(self):
        self.lock = threading.Lock()
        self.deliveries: dict[str, int] = {}
        self.started: dict[str, StartOrder] = {}
        self.cancelled: dict[str, CancelOrder] = {}
        self.status: dict[str, ExecutionStatus] = {}
        self.crash_after_start = False
        self.unavailable = False
        self.not_ready = False                # the port exists but cannot answer yet (PortNotReady)
        self.reject_start = False
        self.fail_next_starts = 0
        self.latency_hook: Callable[[], None] | None = None

    def start(self, order: StartOrder) -> Ack:
        if self.latency_hook:
            self.latency_hook()
        if self.unavailable or self.fail_next_starts > 0:
            self.fail_next_starts = max(0, self.fail_next_starts - 1)
            raise ConnectionError("executor down")
        with self.lock:
            self.deliveries[order.idempotency_key] = self.deliveries.get(order.idempotency_key, 0) + 1
            duplicate = order.attempt_id in self.started
            if self.reject_start:
                return Ack("rejected", "scripted rejection")
            self.started.setdefault(order.attempt_id, order)
            self.status.setdefault(order.attempt_id, ExecutionStatus("running"))
        if self.crash_after_start:
            self.crash_after_start = False
            raise FakeExecutor.Crash()
        return Ack("duplicate" if duplicate else "accepted")

    def cancel(self, order: CancelOrder) -> Ack:
        if self.unavailable:
            raise ConnectionError("executor down")
        with self.lock:
            self.cancelled[order.attempt_id] = order
        return Ack("accepted")

    def query(self, attempt_id: str) -> ExecutionStatus:
        if self.not_ready:
            raise PortNotReady("not composed yet")
        if self.unavailable:
            raise ConnectionError("executor down")
        with self.lock:
            return self.status.get(attempt_id, ExecutionStatus("not_found"))

    def running_attempts(self) -> list[str]:
        with self.lock:
            return [a for a in self.started if self.status.get(a, ExecutionStatus("unknown")).state == "running"]


class FakeVerifier:
    """VerificationPort double: records requests; the verdict is submitted by the test through the core."""

    def __init__(self):
        self.requests: dict[str, VerifyOrder] = {}
        self.deliveries: dict[str, int] = {}
        self.reject: Ack | None = None            # when set, every request is answered with this rejection

    def request(self, order: VerifyOrder) -> Ack:
        self.deliveries[order.idempotency_key] = self.deliveries.get(order.idempotency_key, 0) + 1
        if self.reject is not None:
            return self.reject
        duplicate = order.attempt_id in self.requests
        self.requests.setdefault(order.attempt_id, order)
        return Ack("duplicate" if duplicate else "accepted")


class ScriptedRecovery:
    """RecoveryPort double: answers from a mapping task_id -> RecoveryProposal (or a callable); default 'retry'."""

    def __init__(self, answers: Mapping[str, RecoveryProposal] | Callable[[FailureContext], object] | None = None):
        self.answers, self.calls = answers or {}, []

    def propose(self, context: FailureContext):
        self.calls.append(context)
        if callable(self.answers):
            return self.answers(context)
        return self.answers.get(context.task_id, RecoveryProposal("retry", "scripted"))


def event(core_state_plan: str, revision: int, task_id: str, attempt_id: str, kind: str, event_id: str, *,
          token: int | None = None, source: str = "sim", reason: str = "") -> Event:
    """Small constructor for tests and the CLI simulation."""
    return Event(event_id, core_state_plan, revision, task_id, attempt_id, source, kind, "",
                 {"reason": reason} if reason else {}, token)


def accept(plan_id: str, revision: int, task_id: str, attempt_id: str, verdict_id: str, *, verifier: str = "validator",
           evidence: str = "all checks passed", token: int | None = None) -> Verdict:
    return Verdict(verdict_id, plan_id, revision, task_id, attempt_id, True, verifier, evidence, token)


class ManualClock:
    """A clock that only moves when told to: makes leases and holds reproducible."""

    def __init__(self, start: float = 1_000_000.0):
        self.now = float(start)

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> float:
        self.now += seconds
        return self.now
