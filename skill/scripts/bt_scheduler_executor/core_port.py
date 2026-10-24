"""Focused M3 ExecutionPort bridge, including candidate-base and Designer start gates."""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

TRANSIENT = frozenset({"PORT_ERROR", "LEDGER_ERROR", "ARTIFACT_ERROR"})
STATE_OF = {"queued": "running", "preparing": "running", "running": "running", "settling": "running",
            "finished": "finished", "failed": "failed", "cancelled": "cancelled", "not_found": "not_found"}


class CoreExecutionPort:
    def __init__(self, executor, plan, *, project: str, core, m3, integrator,
                 start_rejection_detail, gates, base_ref="HEAD", default_repository="",
                 composition_base: Callable[..., str | None] | None = None,
                 repo_of: Callable[[str], Path | None] | None = None):
        self.executor, self.plan, self.project = executor, plan, project
        self.base_ref, self.default_repository = base_ref, default_repository
        self.composition_base, self.repo_of = composition_base, repo_of
        self.core, self.m3, self.integrator = core, m3, integrator
        self.start_rejection_detail, self.gates = start_rejection_detail, gates
        self.on_accepted_attempt = None

    def start(self, order):
        if (order.plan_id, order.revision) != (self.plan.plan_id, self.plan.revision):
            return self.core.Ack("rejected", "ORDER_INVALID: the order is for another plan revision than the one wired")
        try:
            repo = self.plan.task(order.task_id).repository or self.default_repository
        except Exception:  # noqa: BLE001
            return self.core.Ack("rejected", "ORDER_INVALID: unknown task")
        if not repo:
            return self.core.Ack("rejected", "REPOSITORY_UNKNOWN: the task names no repository")
        if self.gates.composition_task(self.plan, order.task_id):
            if self.composition_base is None:
                return self.core.Ack("rejected", "COMPOSITION_BASE_MISSING: owner supplied no candidate/current commit", True)
            try:
                base = self.composition_base(order.task_id, order)
            except Exception as error:  # noqa: BLE001 - identity source is a typed fail-closed boundary
                return self.core.Ack("rejected", f"COMPOSITION_BASE_UNAVAILABLE: {type(error).__name__}", True)
            if not isinstance(base, str) or not base.strip():
                return self.core.Ack("rejected", "COMPOSITION_BASE_MISSING: owner supplied no candidate/current commit", True)
        else:
            try:
                base = self.base_ref(order.task_id) if callable(self.base_ref) else self.base_ref
            except self.integrator.IntegrationError as error:
                if not error.permanent:
                    raise RuntimeError(f"{error.code}: {error.detail}"[:300]) from None
                return self.core.Ack("rejected", self.start_rejection_detail(error))
        path = self.gates.contract_path(self.plan, order.task_id)
        if path is not None:
            repository = self.repo_of(repo) if self.repo_of else None
            if repository is None or not self.gates.has_blob(repository, base, path):
                return self.core.Ack("rejected", f"DESIGN_CONTRACT_MISSING: {path or 'invalid frozen UI contract'}",
                                     True, classification="blocked_environment")
        request = self.m3.StartRequest(
            idempotency_key=order.idempotency_key, plan_id=order.plan_id, revision=order.revision, task_id=order.task_id,
            attempt_id=order.attempt_id, token=order.token, executor=order.executor, repository=repo,
            project=self.project, base_ref=base, acceptance_criteria=tuple(order.acceptance_criteria),
            verification=tuple(order.verification), plan_sha256=self.plan.sha256)
        receipt = self.executor.start(request)
        if receipt.status == "rejected" and receipt.code in TRANSIENT:
            raise RuntimeError(f"{receipt.code}: {receipt.detail}")
        if receipt.status in {"accepted", "duplicate"} and self.on_accepted_attempt is not None:
            self.on_accepted_attempt(order.attempt_id)
        return self.core.Ack(receipt.status, f"{receipt.code}: {receipt.detail}".strip(": ")[:300])

    def cancel(self, order):
        receipt = self.executor.cancel(order.attempt_id, order.token, order.idempotency_key, order.reason)
        return self.core.Ack(receipt.status, f"{receipt.code}: {receipt.detail}".strip(": ")[:300])

    def query(self, attempt_id: str):
        if self.executor is None:
            raise self.core.PortNotReady("the executor is not composed yet")
        status = self.executor.query(attempt_id)
        return self.core.ExecutionStatus(STATE_OF[status.state], (status.cause or status.detail)[:300])
