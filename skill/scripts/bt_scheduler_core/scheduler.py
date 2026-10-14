"""SchedulerCore: the deterministic coordinator. Wires plan + repository + ports; contains no AI of any kind.

One `step()` is one pass of: refresh -> reconcile flagged attempts -> recovery decisions -> assignments -> delivery.
`run()` repeats steps and otherwise sleeps on a wake-up event (set by `ingest`/`submit_verdict`), never busy-polling.
Ports are only ever called outside transactions; all decisions are validated again inside the reservation transaction.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, TypeVar

from . import events, operations, recovery, reservation
from .config import Config
from .contracts import (
    Assignment,
    AssignmentPort,
    AssignmentRequest,
    Event,
    ExecutionPort,
    IngestResult,
    RecoveryPort,
    TaskView,
    Verdict,
    VerificationPort,
)
from .dispatch import Dispatcher
from .errors import SchedulerError
from .model import AuditEntry, RunState, TaskRec
from .plan import Plan
from .repository import StateRepository
from .resources import claims_for, first_conflict
from .simulators import FifoAssignment
from .states import ATTEMPT_LIVE, RunStatus
from .states import AttemptState as A
from .states import TaskState as T
from .transitions import Ctx, promote_ready, prune_outbox
from .views import Snapshot, snapshot

R = TypeVar("R")


@dataclass
class Ports:
    """The sibling modules, each optional. Absent port = a documented default (see README), never an AI fallback."""
    assignment: AssignmentPort | None = None
    execution: ExecutionPort | None = None
    verification: VerificationPort | None = None
    recovery: RecoveryPort | None = None


@dataclass
class StepReport:
    promoted: int = 0
    reconciled: int = 0
    recovered: int = 0
    claimed: list[str] = field(default_factory=list)
    delivered: int = 0

    @property
    def progress(self) -> bool:
        return bool(self.promoted or self.reconciled or self.recovered or self.claimed or self.delivered)


class SchedulerCore:
    def __init__(self, plan: Plan, repository: StateRepository, *, ports: Ports | None = None,
                 config: Config | None = None, clock: Callable[[], float] = time.time):
        self.plan, self.repository, self.config, self.clock = plan, repository, config or Config(), clock
        self.ports = ports or Ports()
        if self.ports.assignment is None:
            self.ports = Ports(FifoAssignment(), self.ports.execution, self.ports.verification, self.ports.recovery)
        self._wake, self._step_lock = threading.Event(), threading.RLock()
        self._dispatcher = Dispatcher(self)

    # ------------------------------------------------------------------ transactions
    def write(self, fn: Callable[[Ctx], R]) -> R:
        with self.repository.transaction() as tx:
            if tx.state is None:
                raise SchedulerError("STATE_MISSING", "call start() first")
            return fn(Ctx(self.plan, self.config, tx, self.clock()))

    def read(self, fn: Callable[[Ctx], R]) -> R:
        """Look at the state without taking the writer lock (falls back to a normal transaction for a repository
        that offers no read-only one). `fn` must not change anything: nothing it changes is kept."""
        opener = getattr(self.repository, "read_transaction", self.repository.transaction)
        with opener() as tx:
            if tx.state is None:
                raise SchedulerError("STATE_MISSING", "call start() first")
            return fn(Ctx(self.plan, self.config, tx, self.clock()))

    def record(self, kind: str, /, *, task_id: str = "", attempt_id: str = "", **detail: Any) -> None:
        self.write(lambda c: c.audit(kind, task_id, attempt_id, **detail))

    # ------------------------------------------------------------------ lifecycle
    def start(self) -> Snapshot:
        """Bind to the approved plan (create the run or verify the persisted one matches), then reconcile."""
        plan = self.plan
        with self.repository.transaction() as tx:
            ctx = Ctx(plan, self.config, tx, self.clock())
            if tx.state is None:
                tx.state = RunState(plan.plan_id, plan.revision, plan.sha256, ctx.now,
                                    tasks={t.id: TaskRec(T.PENDING.value) for t in plan.tasks})
                ctx.audit("run_created", tasks=len(plan.tasks), sha256=plan.sha256)
                promote_ready(ctx)
            else:
                self._check_binding(tx.state)
                ctx.audit("run_resumed_by_process")
        self._dispatcher.reconcile(everything=True)
        return self.snapshot()

    def _check_binding(self, s: RunState) -> None:
        plan = self.plan
        if (s.plan_id, s.revision, s.plan_sha256) != (plan.plan_id, plan.revision, plan.sha256) \
                or set(s.tasks) != set(plan.ids()):
            raise SchedulerError("PLAN_MISMATCH", f"persisted run is {s.plan_id} r{s.revision} "
                                 f"{s.plan_sha256[:12]}…, not {plan.plan_id} r{plan.revision} {plan.sha256[:12]}…")

    def inspect(self) -> Snapshot:
        """Read-only: verify the persisted run belongs to this approved plan and describe it; writes nothing."""
        def look(ctx: Ctx):
            self._check_binding(ctx.state)
            return snapshot(self.plan, ctx.state)
        return self.read(look)

    def snapshot(self) -> Snapshot:
        return self.read(lambda c: snapshot(self.plan, c.state))

    def audit_log(self, since: int = 0) -> list[AuditEntry]:
        return self.repository.audit_log(since)

    def pending_orders(self) -> list[dict[str, Any]]:
        """Pull-style view of undelivered intents (for adapters that poll instead of being called)."""
        return self.read(lambda c: [{"id": i.id, "kind": i.kind, "attempt_id": i.attempt_id, "key": i.key,
                                     "payload": dict(i.payload)} for i in c.state.outbox if i.status == "pending"])

    # ------------------------------------------------------------------ inbound facts
    def ingest(self, event: Event | Mapping[str, Any]) -> IngestResult:
        try:
            ev = Event.from_dict(event.to_dict() if isinstance(event, Event) else event)   # re-validated, instance or not
        except (SchedulerError, AttributeError, TypeError, ValueError) as exc:
            if not isinstance(exc, SchedulerError):
                exc = SchedulerError("CONTRACT_VIOLATION", "event is not valid")
            self.record("message_rejected", status="invalid", reason="contract", issues=exc.issues[:3])
            return IngestResult("invalid", exc.issues[0] if exc.issues else exc.code)
        result = self.write(lambda c: events.apply_event(c, ev))
        self._wake.set()
        return result

    def submit_verdict(self, verdict: Verdict) -> IngestResult:
        result = self.write(lambda c: events.apply_verdict(c, verdict))
        self._wake.set()
        return result

    def claim(self, assignment: Assignment) -> reservation.ClaimResult:
        """Atomically reserve one task for an executor label; as many as one wins under concurrency."""
        return self.write(lambda c: reservation.claim(c, assignment))

    # ------------------------------------------------------------------ operator
    def pause(self, by: str, reason: str = "") -> None:
        self.write(lambda c: operations.pause(c, by, reason))

    def resume(self, by: str, reason: str = "") -> None:
        self.write(lambda c: operations.resume(c, by, reason))
        self._wake.set()

    def cancel(self, by: str, reason: str = "") -> None:
        self.write(lambda c: operations.cancel(c, by, reason))
        self._wake.set()

    def reopen(self, task_id: str, by: str, reason: str = "") -> None:
        self.write(lambda c: operations.reopen(c, task_id, by, reason))
        self._wake.set()

    def resolve_attempt(self, attempt_id: str, outcome: str, by: str, reason: str = "") -> str:
        out = self.write(lambda c: operations.resolve_attempt(c, attempt_id, outcome, by, reason))
        self._wake.set()
        return out

    # ------------------------------------------------------------------ the loop
    def step(self) -> StepReport:
        with self._step_lock:
            report = StepReport()
            report.promoted = self.write(self._refresh)
            report.reconciled = self._dispatcher.reconcile(everything=False)
            report.recovered = self._recover()
            report.claimed = self._assign()
            report.delivered = self._dispatcher.deliver_pending()
            return report

    @staticmethod
    def _refresh(ctx: Ctx) -> int:
        """Promote unblocked tasks; flag attempts whose lease lapsed. A lapsed lease proves nothing: it asks for a query."""
        for att in ctx.state.attempts.values():
            if A(att.state) in ATTEMPT_LIVE and not att.needs_reconcile and att.lease_expires_at <= ctx.now:
                att.needs_reconcile = True
                ctx.audit("lease_expired", att.task_id, att.id, lease_expires_at=att.lease_expires_at)
        prune_outbox(ctx)
        return promote_ready(ctx)

    def _recover(self) -> int:
        done = 0
        for context in self.read(recovery.pending):
            proposal = None
            if self.ports.recovery is not None:
                try:
                    proposal = self.ports.recovery.propose(context)
                except Exception as exc:  # noqa: BLE001 - a dead or buggy adapter must not stop the core
                    self.record("port_error", task_id=context.task_id, attempt_id=context.attempt_id, port="recovery",
                                error=type(exc).__name__)
            if self.write(lambda c, ctx_=context, p=proposal: recovery.apply_recovery(c, ctx_, p)) not in ("stale", "waiting"):
                done += 1
        return done

    def _assign(self) -> list[str]:
        def eligible(ctx: Ctx):
            if ctx.state.paused or ctx.state.cancel_requested:
                return None
            slots = reservation.free_slots(ctx)
            ready = []
            for spec in ctx.plan.tasks:
                rec = ctx.state.tasks[spec.id]
                if rec.state != T.READY.value or first_conflict(claims_for(spec, ctx.config), ctx.state.holds):
                    continue
                ready.append(TaskView(spec.id, spec.milestone_id, spec.repository, spec.shared_resources,
                                      spec.expected_paths, len(rec.attempts), dict(spec.meta)))
            return (AssignmentRequest(ctx.state.plan_id, ctx.state.revision, tuple(ready), slots, ctx.now)
                    if ready and slots > 0 else None)

        request = self.read(eligible)
        if request is None:
            return []
        try:
            proposals = self.ports.assignment.propose(request)
            if not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)) \
                    or not all(isinstance(p, Assignment) for p in proposals):
                raise TypeError("invalid assignment proposal")
        except Exception as exc:  # noqa: BLE001 - a dead or buggy adapter must not stop the core
            self.record("port_error" if not isinstance(exc, TypeError) else "port_invalid", port="assignment",
                        error=type(exc).__name__)
            return []
        claimed = []
        for proposal in proposals:                    # refused entries must not eat the slots of valid ones
            if len(claimed) >= request.free_slots:
                break
            result = self.claim(proposal)
            if result.ok:
                claimed.append(result.attempt_id)
        return claimed

    def next_deadline(self) -> float:
        """Seconds until something time-based needs a look (lease, recovery hold), capped by `reconcile_seconds`."""
        def soonest(ctx: Ctx):
            times = [a.lease_expires_at for a in ctx.state.attempts.values()
                     if A(a.state) in ATTEMPT_LIVE and not a.needs_reconcile]
            times += [r.hold_until for r in ctx.state.tasks.values() if r.state == T.RECOVERING.value and r.hold_until > ctx.now]
            return min(times, default=ctx.now + self.config.reconcile_seconds) - ctx.now
        return max(0.0, min(self.read(soonest), self.config.reconcile_seconds))

    def run(self, *, idle_timeout: float | None = None, max_steps: int | None = None,
            stop: Callable[[], bool] | None = None) -> Snapshot:
        """Step until the run is terminal or nothing can move without outside help (blocked, only uncertain attempts,
        paused with nothing live). Between steps it sleeps on the wake-up event; `idle_timeout` bounds total idleness."""
        steps, idle_since = 0, None
        while True:
            report = self.step()
            steps += 1
            snap = self.snapshot()
            if snap.status in (RunStatus.COMPLETED.value, RunStatus.CANCELLED.value) or self._stalled(snap):
                return snap
            if (max_steps is not None and steps >= max_steps) or (stop is not None and stop()):
                return snap
            if report.progress:
                idle_since = None
                continue
            idle_since = idle_since if idle_since is not None else time.monotonic()
            remaining = None if idle_timeout is None else idle_timeout - (time.monotonic() - idle_since)
            if remaining is not None and remaining <= 0:
                return snap
            wait = self.next_deadline()
            self._wake.wait(wait if remaining is None else min(wait, remaining))
            self._wake.clear()

    @staticmethod
    def _stalled(snap: Snapshot) -> bool:
        states = [t["state"] for t in snap.tasks.values()]
        if any(s in (T.READY.value, T.RECOVERING.value) for s in states):
            return False
        active = [t for t in snap.tasks.values() if t["state"] == T.ACTIVE.value]
        if snap.status == RunStatus.PAUSED.value:
            return not active
        if snap.status == RunStatus.BLOCKED.value:
            return True
        return bool(active) and all(t["attempt_state"] == A.UNCERTAIN.value for t in active)
