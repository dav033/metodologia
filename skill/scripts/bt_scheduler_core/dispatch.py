"""Delivery of persisted intents (outbox) to the execution/verification ports, and reconciliation of live attempts.

Protocol for every start order: (1) the intent was persisted with the reservation; (2) before the port is called,
`deliveries` is incremented in its own transaction (write-ahead); (3) the port is called OUTSIDE any transaction with
the idempotency key; (4) the answer is recorded. A crash after (2) leaves `deliveries > 0` with the item pending, so the
next run asks the executor what really happened (query) BEFORE sending the order again. Uncertainty keeps the
reservation: never two writers.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .contracts import ACK, Ack, CancelOrder, ExecutionStatus, PortNotReady, StartOrder, VerifyOrder
from .recovery import apply_observation
from .states import ATTEMPT_LIVE, ATTEMPT_TERMINAL
from .states import AttemptState as A
from .transitions import end_attempt, mark_delivered, set_attempt

if TYPE_CHECKING:
    from .scheduler import SchedulerCore


class Dispatcher:
    def __init__(self, core: SchedulerCore):
        self.core = core

    # ------------------------------------------------------------------ delivery
    def deliver_pending(self) -> int:
        """Try every pending outbox item once; returns how many changed the state."""
        core, changed = self.core, 0
        ids = core.read(lambda c: [i.id for i in c.state.outbox if i.status == "pending"])
        for item_id in ids:
            changed += self._deliver_one(item_id)
        return changed

    def _deliver_one(self, item_id: str) -> int:
        core = self.core

        def prepare(ctx):
            item = next((i for i in ctx.state.outbox if i.id == item_id), None)
            if item is None or item.status != "pending":
                return None
            att = ctx.state.attempts[item.attempt_id]
            if A(att.state) in ATTEMPT_TERMINAL:
                item.status = "void"
                return None
            if item.kind == "start" and (ctx.state.paused or ctx.state.cancel_requested):
                if ctx.state.cancel_requested:     # a cancelled run never sends a start order, not even a retry
                    item.status = "void"
                    ctx.audit("dispatch_voided", att.task_id, att.id, kind="start", why="cancel_requested")
                return None
            if (core.ports.verification if item.kind == "verify" else core.ports.execution) is None:
                return None                        # pull mode: the order stays for pending_orders(), untouched
            if item.deliveries >= ctx.config.max_deliveries:   # abandoned and made visible, not retried forever
                item.status = "void"
                ctx.audit("delivery_abandoned", att.task_id, att.id, kind=item.kind, deliveries=item.deliveries)
                if item.kind == "start" and A(att.state) != A.UNCERTAIN:
                    set_attempt(ctx, att.id, A.UNCERTAIN, why="start_delivery_abandoned")
                return None
            before = item.deliveries
            item.deliveries += 1                                   # write-ahead: recorded before the call
            return item.kind, item.attempt_id, item.key, dict(item.payload), before, att.task_id

        job = core.write(prepare)
        if job is None:
            return 0
        kind, attempt_id, key, payload, before, task_id = job
        if kind == "start" and before > 0:                         # maybe delivered already: ask before re-sending
            status = self._query(attempt_id)
            seen = core.write(lambda c: apply_observation(c, attempt_id, status))
            if seen != "not_found" or not core.read(lambda c: self._still_unsent(c, attempt_id)):
                return 1
        ack = self._send(kind, attempt_id, key, payload, task_id)
        if ack is None:
            return 0
        return core.write(lambda c: self._record_ack(c, kind, attempt_id, ack))

    @staticmethod
    def _still_unsent(ctx, attempt_id: str) -> bool:
        att = ctx.state.attempts[attempt_id]
        return A(att.state) == A.RESERVED and any(
            i.attempt_id == attempt_id and i.kind == "start" and i.status == "pending" for i in ctx.state.outbox)

    def _send(self, kind: str, attempt_id: str, key: str, payload: dict, task_id: str):
        core = self.core
        port = core.ports.verification if kind == "verify" else core.ports.execution
        if port is None:
            return None
        state = core.read(lambda c: (c.state.plan_id, c.state.revision))
        if kind == "start":
            order = StartOrder(key, state[0], state[1], task_id, attempt_id, payload["token"], payload["executor"],
                               tuple(payload["acceptance_criteria"]), tuple(payload["verification"]),
                               dict(payload.get("meta", {})))
            call = port.start
        elif kind == "cancel":
            order, call = CancelOrder(key, attempt_id, payload["token"], payload.get("reason", "")), port.cancel
        else:
            order = VerifyOrder(key, state[0], state[1], task_id, attempt_id, payload["token"],
                                tuple(payload["acceptance_criteria"]), tuple(payload["verification"]))
            call = port.request
        try:
            ack = call(order)
        except Exception as exc:  # noqa: BLE001 - a dead or buggy adapter must not stop the core
            core.record("port_error", task_id=task_id, attempt_id=attempt_id, port=kind, error=type(exc).__name__)
            return None
        if not isinstance(ack, Ack) or ack.status not in ACK:
            core.record("port_invalid", task_id=task_id, attempt_id=attempt_id, port=kind)
            return None
        return ack

    @staticmethod
    def _record_ack(ctx, kind: str, attempt_id: str, ack: Ack) -> int:
        att = ctx.state.attempts[attempt_id]
        item = next((i for i in ctx.state.outbox if i.attempt_id == attempt_id and i.kind == kind
                     and i.status == "pending"), None)
        if item is None:
            return 0
        if ack.status == "rejected":
            ctx.audit("dispatch_rejected", att.task_id, attempt_id, kind=kind, detail=ack.detail[:200])
            item.status = "void"
            if kind == "start" and A(att.state) in ATTEMPT_LIVE:
                end_attempt(ctx, attempt_id, A.FAILED, "execution_failed", f"start rejected: {ack.detail[:200]}")
            elif kind == "verify" and ack.permanent and A(att.state) == A.VERIFYING:
                # the verifier refuses the ORDER itself: asking again at every lease expiry never changes that (REQ-020 att-0087 waited
                # 99 minutes and 20 re-sends). The attempt ends; whatever the executor kept of its work stays there for the retry
                end_attempt(ctx, attempt_id, A.FAILED, "execution_failed", f"verify rejected: {ack.detail[:200]}")
            return 1
        mark_delivered(ctx, attempt_id, kind)
        ctx.audit("dispatch_delivered", att.task_id, attempt_id, kind=kind, ack=ack.status)
        if kind == "cancel" and A(att.state) in ATTEMPT_LIVE:
            att.needs_reconcile = True             # an ack is not a confirmation: the next step asks what became of it
        if kind == "start" and A(att.state) == A.RESERVED:
            set_attempt(ctx, attempt_id, A.DISPATCHED, ack=ack.status)
        return 1

    # ------------------------------------------------------------------ reconciliation
    def _query(self, attempt_id: str) -> ExecutionStatus:
        port = self.core.ports.execution
        if port is None:
            return ExecutionStatus("unknown", "no execution port")
        try:
            status = port.query(attempt_id)
        except PortNotReady:
            raise
        except Exception as exc:  # noqa: BLE001 - a dead or buggy adapter must not stop the core
            self.core.record("port_error", attempt_id=attempt_id, port="query", error=type(exc).__name__)
            return ExecutionStatus("unknown", type(exc).__name__)
        return status if isinstance(status, ExecutionStatus) else ExecutionStatus("unknown", "invalid reply")

    def reconcile(self, *, everything: bool) -> int:
        """Ask the executor about live attempts (all of them at startup, flagged ones later). Never assumes."""
        core = self.core
        if core.ports.execution is None:
            return 0

        def targets(ctx):
            out = []
            for att in ctx.state.attempts.values():
                if A(att.state) not in ATTEMPT_LIVE or not (everything or att.needs_reconcile):
                    continue
                start = next((i for i in ctx.state.outbox if i.attempt_id == att.id and i.kind == "start"), None)
                if A(att.state) == A.RESERVED and start and start.status == "pending" and start.deliveries == 0:
                    continue                                       # never sent: the normal delivery path handles it
                out.append(att.id)
            return out

        changed = 0
        for attempt_id in core.read(targets):
            try:
                status = self._query(attempt_id)
            except PortNotReady:       # nothing was observed: keep the attempt as it is and ask again on a later step
                core.write(lambda c, a=attempt_id: setattr(c.state.attempts[a], "needs_reconcile", True))
                continue
            core.write(lambda c, a=attempt_id, s=status: apply_observation(c, a, s))
            changed += 1
        return changed
