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
    CONTRACT_VERSION,
    ROUTING_CONTRACT_VERSION,
    Assignment,
    AssignmentPort,
    AssignmentRequest,
    Event,
    ExecutionPort,
    IngestResult,
    PlannedRoute,
    PlanRoutingPort,
    PlanRoutingRequest,
    RecoveryPort,
    TaskView,
    Verdict,
    VerificationPort,
    route_metadata_valid,
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
from .transitions import Ctx, promote_ready, prune_outbox, set_task
from .views import Snapshot, snapshot

R = TypeVar("R")


@dataclass
class Ports:
    """The sibling modules, each optional. Absent port = a documented default (see README), never an AI fallback."""
    assignment: AssignmentPort | None = None
    execution: ExecutionPort | None = None
    verification: VerificationPort | None = None
    recovery: RecoveryPort | None = None
    routing: PlanRoutingPort | None = None


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
    contract_version = CONTRACT_VERSION

    def __init__(self, plan: Plan, repository: StateRepository, *, ports: Ports | None = None,
                 config: Config | None = None, clock: Callable[[], float] = time.time):
        self.plan, self.repository, self.config, self.clock = plan, repository, config or Config(), clock
        self.ports = ports or Ports()
        if self.ports.assignment is None:
            self.ports = Ports(FifoAssignment(), self.ports.execution, self.ports.verification, self.ports.recovery,
                               self.ports.routing)
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
        self._plan_all_routes()
        self._dispatcher.reconcile(everything=True)
        return self.snapshot()

    def _plan_all_routes(self) -> None:
        """Ask M2 for a non-reserving route map of the full DAG before reconciliation or dispatch."""
        port = self.ports.routing
        if port is None or self.read(lambda ctx: ctx.state.routing_complete):
            return

        def request(ctx: Ctx) -> PlanRoutingRequest:
            tasks = tuple(TaskView(
                spec.id, spec.milestone_id, spec.repository, spec.shared_resources,
                spec.expected_paths, len(ctx.state.tasks[spec.id].attempts), dict(spec.meta),
                dependencies=spec.after, acceptance_criteria=spec.acceptance_criteria,
                verification=spec.verification,
            ) for spec in self.plan.tasks)
            return PlanRoutingRequest(ctx.state.plan_id, ctx.state.revision, ctx.state.plan_sha256, tasks, ctx.now)

        route_request = self.read(request)
        try:
            proposals = port.plan(route_request)
        except Exception as exc:
            self.record("port_error", port="routing", error=type(exc).__name__)
            raise SchedulerError("ROUTING_UNAVAILABLE", "M2 could not produce the initial route map; resume to retry") from exc
        if (not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)) or
                len(proposals) != len(route_request.tasks) or
                not all(self._valid_planned_route(item) for item in proposals)):
            self.record("port_invalid", port="routing", contract_version=ROUTING_CONTRACT_VERSION)
            raise SchedulerError("ROUTING_INVALID", "M2 must return exactly one valid route result per plan task")
        expected = {task.id for task in route_request.tasks}
        ids = [item.task_id for item in proposals]
        if len(set(ids)) != len(ids) or set(ids) != expected:
            self.record("port_invalid", port="routing", reason="task_coverage")
            raise SchedulerError("ROUTING_INVALID", "M2 route results do not cover the approved plan exactly once")

        def persist(ctx: Ctx) -> None:
            if ctx.state.routing_complete:
                return
            planned = recommended = 0
            for item in proposals:
                rec = ctx.state.tasks[item.task_id]
                if rec.state in (T.COMPLETED.value, T.CANCELLED.value):
                    continue                    # a rebased run keeps the route of accepted work; nothing to recommend
                if rec.attempts and rec.state not in (T.PENDING.value, T.READY.value):
                    continue  # an older run may predate route maps; never replace a route after work has started
                planned += 1
                rec.route_metadata = dict(item.route_metadata)
                rec.route_status = "recommended" if item.route_metadata else "unavailable"
                rec.route_reason = item.reason
                recommended += bool(item.route_metadata)
            ctx.state.routing_complete = True
            ctx.audit("plan_routes_received", tasks=planned, recommended=recommended,
                      unavailable=planned - recommended, contract_version=ROUTING_CONTRACT_VERSION)

        self.write(persist)

    @staticmethod
    def _valid_planned_route(value: object) -> bool:
        if not isinstance(value, PlannedRoute) or value.contract_version != ROUTING_CONTRACT_VERSION:
            return False
        if (not isinstance(value.task_id, str) or not value.task_id.strip() or
                not route_metadata_valid(value.route_metadata) or
                not isinstance(value.reason, str) or len(value.reason) > 160 or
                any(ord(char) < 32 for char in value.reason)):
            return False
        return bool(value.route_metadata) != bool(value.reason)

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

    def rework_scope(self, task_ids: tuple[str, ...], also: tuple[str, ...] = (), cascade: bool = True) -> tuple[str, ...]:
        """Every task `reject_and_rework(..., task_ids)` would send back with the rejected task `also`."""
        return self.read(lambda c: operations.rework_scope(c, (*task_ids, *also), cascade))

    def rework_problem(self, task_ids: tuple[str, ...], also: tuple[str, ...] = (), cascade: bool = True) -> str:
        """Why `reject_and_rework` would be refused right now ('' when it would not)."""
        return self.read(lambda c: operations.rework_problem(c, tuple(task_ids), tuple(also), cascade=cascade))

    def rework(self, task_ids: tuple[str, ...], by: str, reason: str = "", cascade: bool = True) -> tuple[str, ...]:
        """Operator move: send accepted work back (see `operations.rework`)."""
        out = self.write(lambda c: operations.rework(c, tuple(task_ids), by, reason, owner=True, cascade=cascade))
        self._wake.set()
        return out

    def withdraw_rework(self, task_ids: tuple[str, ...], by: str, reason: str = "") -> tuple[str, ...]:
        """Operator move: take a rework back for tasks that have redone nothing since (see `operations.withdraw_rework`)."""
        out = self.write(lambda c: operations.withdraw_rework(c, tuple(task_ids), by, reason))
        self._wake.set()
        return out

    def reject_and_rework(self, verdict: Verdict, task_ids: tuple[str, ...], by: str, reason: str = "",
                          cascade: bool = True) -> tuple[IngestResult, tuple[str, ...]]:
        """Apply a REJECTING verdict and, in the same transaction, send the named accepted tasks (and what depends on
        them) back for rework together with the task just rejected. Three outcomes when the rework cannot start:
        `busy` (live attempts in scope) defers everything — the verdict is NOT applied, status `deferred`, and the
        caller offers it again later; `limit` applies the verdict and BLOCKS the rejected task at once with reason
        `rework_limit` (retrying the rejected task cannot fix work that was already sent back too often: the owner
        decides); `cancelled` just applies the verdict."""
        if verdict.accepted:
            raise SchedulerError("NOT_ALLOWED", "only a rejecting verdict can ask for rework")

        def both(ctx: Ctx) -> tuple[IngestResult, tuple[str, ...]]:
            ids = tuple(task_ids)
            problem = operations.rework_problem(ctx, ids, (verdict.task_id,), cascade=cascade)
            if problem.startswith("busy") and not ctx.state.has_seen(verdict.verdict_id):
                return IngestResult("deferred", problem, verdict.verdict_id), ()
            result = events.apply_verdict(ctx, verdict)
            if result.status != "applied":
                return result, ()
            if problem:
                ctx.audit("rework_refused", verdict.task_id, verdict.attempt_id, why=problem, named=list(ids))
                if problem.startswith("limit"):
                    rec = ctx.state.tasks[verdict.task_id]
                    if rec.state == T.RECOVERING.value:
                        rec.reason = "rework_limit"
                        set_task(ctx, verdict.task_id, T.BLOCKED, reason="rework_limit")
                return result, ()
            return result, operations.rework(ctx, ids, by, reason, also=(verdict.task_id,), cascade=cascade)

        out = self.write(both)
        self._wake.set()
        return out

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
                ready.append(TaskView(
                    spec.id, spec.milestone_id, spec.repository, spec.shared_resources,
                    spec.expected_paths, len(rec.attempts), dict(spec.meta),
                    dependencies=spec.after, acceptance_criteria=spec.acceptance_criteria,
                    verification=spec.verification,
                ))
            return (AssignmentRequest(ctx.state.plan_id, ctx.state.revision, tuple(ready), slots, ctx.now,
                                      plan_sha256=ctx.plan.sha256)
                    if ready and slots > 0 else None)

        request = self.read(eligible)
        if request is None:
            return []
        try:
            proposals = self.ports.assignment.propose(request)
            if not isinstance(proposals, Sequence) or isinstance(proposals, (str, bytes)) \
                    or not all(isinstance(p, Assignment) and route_metadata_valid(p.route_metadata) for p in proposals):
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
