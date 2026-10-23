"""The M1/M3 boundary for durable M6 verification and correlated verdict delivery."""

from __future__ import annotations

import logging
import subprocess
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import bt_audit_gate
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_executor_adapter as executor_adapter
from bitacora_platform import (
    quality_audit_evidence,
    quality_notes,
    quality_review_gate,
    quality_snapshot,
)
from bitacora_platform.quality_delivery import QualityDeliveryMethods
from bt_recovery_evidence import (
    audit_observation_from_ledger,
    recovery_coverage_problems,
)
from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.review import ReviewerPort
from bt_scheduler_quality.runner import CommandOutcome, SandboxRunner
from bt_scheduler_quality.snapshot import SnapshotResolver, SnapshotSource
from bt_scheduler_quality.store import QualityStore
from bt_scheduler_quality_orders import (
    matches_approved_plan as _matches_approved_plan,
)
from bt_scheduler_quality_orders import (
    order_mapping as _order_mapping,
)

_attempt_worktree = quality_snapshot._attempt_worktree
_read_snapshot_inputs = quality_snapshot._read_snapshot_inputs
_captured_handoff = quality_snapshot._captured_handoff
_build_snapshot_source = quality_snapshot._build_snapshot_source
UNRESOLVED = quality_notes.UNRESOLVED
REVERTED = quality_notes.REVERTED
_unresolved_note = quality_notes._unresolved_note
_reverted_note = quality_notes._reverted_note
_without_noise = quality_notes._without_noise
_integration_note = quality_notes._integration_note
_give_way_note = quality_notes._give_way_note
_ERROR_LINE = quality_notes._ERROR_LINE

m1 = scheduler_adapter.core
m3 = executor_adapter.m3
RepositoryResolver = Callable[[m1.VerifyOrder], Path | str | None]
LOGGER = logging.getLogger(__name__)


class QualityVerificationPort(QualityDeliveryMethods):
    """Persist M1 admission first, then verify asynchronously with bounded workers."""

    def __init__(
        self,
        core: m1.SchedulerCore,
        executor: m3.AgentExecutor,
        store: QualityStore,
        policy: QualityPolicy,
        repository_for_order: RepositoryResolver,
        *,
        attempts_root: Path | str | None = None,
        reviewer: ReviewerPort | None = None,
        runner: SandboxRunner | None = None,
        snapshot_resolver: SnapshotResolver | None = None,
        rework_notes: Callable[[str, str], None] | None = None,
        verify_notes: Callable[[str, str], None] | None = None,
        verify_history: Callable[[str, str, str], None] | None = None,
        audit_policy: bt_audit_gate.Policy | None = None,
        read_ledger: Callable[[VerifyRequest, str], bytes | None] | None = None,
        read_changes: Callable[[VerifyRequest], tuple[str, ...]] | None = None,
        integration_check: Callable[[str, str, str], str] | None = None,
        integration_retries: int = 0,
        integration_rework_limit: int = 6,
        unresolved_check: Callable[[str, str], tuple[str, ...]] | None = None,
        revert_check: Callable[..., tuple[str, ...]] | None = None,
        remediate: Callable[[str, str, list[dict]], bool] | None = None,
        attestations: Callable[..., str | None] | None = None,
        publish_audit_observation: Callable[[str, str, dict], None] | None = None,
        publish_conflict_observation: Callable[[VerifyRequest, str, str, str], str] | None = None,
    ):
        self.core = core
        self.rework_notes = rework_notes
        self.verify_notes = verify_notes                  # (task, text): why M6 rejected the attempt; '' clears it
        self.verify_history = verify_history              # (task, attempt, text): every rejection, kept for later retries
        self.audit_policy = audit_policy or bt_audit_gate.Policy()
        self._resolver = snapshot_resolver or SnapshotResolver(policy)
        self._read_ledger = read_ledger or self._ledger_from_snapshot
        self._read_changes = read_changes or self._changes_from_snapshot
        self.integration_check = integration_check        # (task, attempt, snapshot) -> '' or why it cannot be combined
        self.integration_retries = integration_retries    # clash rejections of one task before the dependents give way
        self.integration_rework_limit = integration_rework_limit  # times one task may be sent back to give way
        self.unresolved_check = unresolved_check          # (task, snapshot) -> files still holding merge conflict markers
        self.revert_check = revert_check                  # (task, snapshot) -> files changed back to an older version
        self.remediate = remediate                        # (audit, attempt, findings) -> True when they became remediation tasks
        self.publish_audit_observation = publish_audit_observation
        self.publish_conflict_observation = publish_conflict_observation
        self.executor = executor
        self.store = store
        self.policy = policy
        self.repository_for_order = repository_for_order
        configured_attempts = (
            attempts_root if attempts_root is not None else executor.attempts_dir
        )
        if not isinstance(configured_attempts, (str, Path)):
            raise TypeError("M3 attempts root must be a configured filesystem path")
        self.attempts_root = Path(configured_attempts)
        self._audit_runner = quality_audit_evidence.EvidenceRunner(
            runner or SandboxRunner(policy, progress=quality_audit_evidence.progress_observer(self)), lambda order, spec: quality_audit_evidence.owns_check(self, order, spec),
            lambda: CommandOutcome("pass", 0, 0, b"[M6] engine ledger contract and content provenance passed\n", b"", None, True))
        self.engine = QualityEngine(
            policy, store, reviewer=reviewer, runner=self._audit_runner, resolver=snapshot_resolver, attestations=attestations,
            own_outputs=self._own_outputs
        )
        self._pool = ThreadPoolExecutor(
            max_workers=policy.max_concurrent, thread_name_prefix="m6-quality"
        )
        self._active: set[str] = set()
        self._active_lock = threading.Lock()
        self._audit_review_seen: set[tuple[str, str | None]] = set()
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._closed = False

    def start(self) -> None:
        if self._closed:
            raise QualityError(
                "ADAPTER_CLOSED", "M6 adapter cannot be restarted after close"
            )
        if self._thread is not None and self._thread.is_alive():
            return
        self.engine.recover_interrupted()
        self._retry_interrupted_reviews()
        self.reconcile_outbox(force=True)
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._dispatch_loop, name="m6-quality-dispatch", daemon=True
        )
        self._thread.start()
        self._wake.set()

    def _retry_interrupted_reviews(self) -> int:
        """A verification cut short by a restart of the owner is repeated, not left for a person: the review it left is
        caused solely by the interruption (no check gave a verdict). The store allows one such retry per request, so a
        restart loop cannot replay commands indefinitely; a request already retried stays for the owner."""
        retried = 0
        for review in self.store.list_reviews():
            try:
                self.store.retry_interrupted(review["request_key"], "owner-restart",
                                             "verification interrupted by a restart of the owner; rerun it")
                retried += 1
            except QualityError:
                continue                                # not an interruption, or already retried once
        return retried

    def close(self, *, wait: bool = True) -> None:
        self._closed = True
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            if wait:
                self._thread.join()
            else:
                self._thread.join(timeout=5)
        self._pool.shutdown(wait=wait, cancel_futures=False)

    def _own_outputs(self, order: VerifyRequest) -> tuple[str, ...]:
        """The report files this order's task writes, when it is a test or audit task (`reuse.own_outputs`)."""
        from bt_scheduler_quality import reuse

        try:
            task = self.core.plan.task(order.task_id)
        except Exception:  # noqa: BLE001 - an unknown task has no outputs to leave out of the key
            return ()
        meta = getattr(task, "meta", None) or {}
        return reuse.own_outputs(meta.get("kind"), getattr(task, "expected_paths", ()))

    def request(self, order: m1.VerifyOrder) -> m1.Ack:
        try:
            parsed = VerifyRequest.from_mapping(_order_mapping(order))
        except (QualityError, TypeError, ValueError) as error:
            code = error.code if isinstance(error, QualityError) else "ORDER_INVALID"
            return m1.Ack("rejected", code, permanent=True)          # the order is malformed: sending it again changes nothing
        if not _matches_approved_plan(self.core, order, parsed):
            return m1.Ack("rejected", "ORDER_DIFFERS_FROM_APPROVED_PLAN", permanent=True)
        try:
            state, _ = self.store.reserve(
                parsed, max_pending=self.policy.max_pending_requests
            )
        except QualityError as error:
            if error.code in {"IDEMPOTENCY_CONFLICT", "QUALITY_BUSY", "ORDER_INVALID"}:
                return m1.Ack("rejected", error.code, permanent=error.code != "QUALITY_BUSY")   # only a busy store may answer later
            raise
        self._wake.set()
        return m1.Ack("duplicate" if state != "new" else "accepted", "durably admitted")

    def reconcile_outbox(self, *, force: bool = False) -> dict[str, int]:
        quality_review_gate.advance(self)
        delivered = stale = pending = deferred = 0
        now = datetime.now(UTC)
        for item in self.store.pending_deliveries():
            if not force and not _retry_is_due(
                item.get("last_response_at"), item.get("attempts", 0), now
            ):
                deferred += 1
                continue
            state = self._deliver_one(item["request_key"])
            if state == "delivered":
                delivered += 1
            elif state == "stale":
                stale += 1
            elif state == "pending":
                pending += 1
        return {
            "delivered": delivered,
            "stale": stale,
            "pending": pending,
            "deferred": deferred,
        }

    def list_reviews(
        self, *, include_resolved: bool = False
    ) -> tuple[dict[str, Any], ...]:
        reviews = []
        for item in self.store.list_reviews(include_resolved=include_resolved):
            result = self.store.get_result(item["request_key"])
            reviews.append({**item, "result": result})
        return tuple(reviews)

    def inspect_review(self, request_key: str) -> dict[str, Any]:
        review = next(
            (
                item
                for item in self.list_reviews(include_resolved=True)
                if item["request_key"] == request_key
            ),
            None,
        )
        if review is None:
            raise QualityError("REVIEW_NOT_FOUND", "review item does not exist")
        return review

    def resolve_review(
        self, request_key: str, operator: str, decision: str, reason: str
    ) -> dict[str, Any]:
        review = self.inspect_review(request_key)
        if review["state"] != "open":
            raise QualityError(
                "REVIEW_ALREADY_RESOLVED", "review item was already resolved"
            )
        self.store.resolve_review(request_key, operator, decision, reason)
        result = self.inspect_review(request_key)
        delivery = self._deliver_one(request_key)
        return {**result, "delivery": delivery}

    def _dispatch_loop(self) -> None:
        while not self._stop.is_set():
            try:
                launched = self._schedule_queued()
                self.reconcile_outbox()
            # Keep polling after unexpected storage or port errors; the failure is logged.
            except Exception as error:  # noqa: BLE001
                LOGGER.error("M6 durable queue scan failed (%s)", type(error).__name__)
                launched = 0
            if launched == 0:
                self._wake.wait(timeout=1.0)
                self._wake.clear()

    def _schedule_queued(self) -> int:
        with self._active_lock:
            available = self.policy.max_concurrent - len(self._active)
        if available <= 0:
            return 0
        launched = 0
        for key, raw_order in self.store.queued_requests(available):
            if not self.store.claim_work(key):
                continue
            try:
                order = VerifyRequest.from_mapping(raw_order)
                with self._active_lock:
                    self._active.add(key)
                self._pool.submit(self._run_request, key, order)
                launched += 1
            # Convert an unexpected scheduling failure into a durable result where possible.
            except Exception as error:  # noqa: BLE001
                with self._active_lock:
                    self._active.discard(key)
                LOGGER.error(
                    "M6 could not schedule a durable request (%s)", type(error).__name__
                )
                try:
                    order = VerifyRequest.from_mapping(raw_order)
                    self.engine.finish_unavailable(order, "ENGINE_FAILURE")
                # Log failures even when the fallback result itself cannot be stored.
                except Exception as failure:  # noqa: BLE001
                    LOGGER.error(
                        "M6 could not persist a scheduling failure (%s)",
                        type(failure).__name__,
                    )
        return launched

    def _run_request(self, request_key: str, order: VerifyRequest) -> None:
        try:
            try:
                source = self._snapshot_source(order)
            # M3 port failures prevent provenance; return no source and require review.
            except Exception as error:  # noqa: BLE001
                LOGGER.warning("M6 handoff lookup failed (%s)", type(error).__name__)
                source = None
            with self._audit_runner.bind(order):
                result = self.engine.process_reserved(order, source)
        # Convert any engine failure into an explicit durable unavailable result.
        except Exception as error:  # noqa: BLE001
            LOGGER.error(
                "M6 worker failed before a durable result (%s)", type(error).__name__
            )
            try:
                self.engine.finish_unavailable(order, "ENGINE_FAILURE")
            # Surface failures to persist that fallback in the log.
            except Exception as failure:  # noqa: BLE001
                LOGGER.error(
                    "M6 could not persist a worker failure (%s)", type(failure).__name__
                )
        else:
            if result["status"] in {"PASS", "FAIL"}:
                try:
                    self._deliver_one(request_key)
                # Keep the verdict in the durable outbox for later reconciliation.
                except Exception as error:  # noqa: BLE001
                    LOGGER.warning(
                        "M6 durable verdict remains pending (%s)", type(error).__name__
                    )
        finally:
            with self._active_lock:
                self._active.discard(request_key)
            self._wake.set()

    def _snapshot_source(self, order: VerifyRequest) -> SnapshotSource | None:
        description, repository = _read_snapshot_inputs(
            self.executor, self.repository_for_order, order
        )
        handoff_data = _captured_handoff(description, order.attempt_id)
        if handoff_data is None:
            return None
        directory, handoff = handoff_data
        return _build_snapshot_source(
            self.attempts_root, order.attempt_id, directory, handoff, repository
        )

    def _ledger_from_snapshot(self, order: VerifyRequest, path: str) -> bytes | None:
        """The audit's findings ledger as captured in the verified snapshot; None when the file is not there. A snapshot
        that cannot be produced raises: that is an outage to retry, not a verdict about the ledger."""
        source = self._snapshot_source(order)
        if source is None:
            raise RuntimeError("the audited snapshot is unavailable")
        relative = Path(path)
        if relative.is_absolute() or ".." in relative.parts:
            return None
        with self._resolver.materialize(source) as snapshot:
            target = snapshot.directory / relative
            if target.is_symlink() or not target.is_file():
                return None
            if target.stat().st_size > bt_audit_gate.MAX_BYTES:
                return b"x" * (bt_audit_gate.MAX_BYTES + 1)
            return target.read_bytes()

    def _changes_from_snapshot(self, order: VerifyRequest) -> tuple[str, ...]:
        """The paths the attempt changed against its base (exact: `git diff`, not the manifest's capped list). A snapshot
        that cannot be read raises: an outage to retry, not a verdict."""
        source = self._snapshot_source(order)
        if source is None:
            raise RuntimeError("the audited snapshot is unavailable")
        done = subprocess.run(["git", "-C", str(source.repository), "diff", "--name-only", "-z", "--no-renames",
                               source.base_sha, source.snapshot_sha], capture_output=True, timeout=60, check=False)
        if done.returncode:
            raise RuntimeError("the audited snapshot could not be compared with its base")
        return tuple(name for name in done.stdout.decode("utf-8", "replace").split("\0") if name)

    def _audit_gate(self, order: VerifyRequest, *, evaluate_gate: bool = True,
                    check_status: str = "PASS") -> bt_audit_gate.Gate | None:
        """None when the task is not an audit; otherwise the judgment of its findings ledger, whatever the checks said."""
        try:
            task = self.core.plan.task(order.task_id)
        except m1.SchedulerError:
            return None
        if task.meta.get("kind") != "audit":
            return None
        path = bt_audit_gate.ledger_path(task.expected_paths)
        if path is None:
            if not self.audit_policy.ledger_required:
                self.core.record("audit_gate_skipped", task_id=order.task_id, attempt_id=order.attempt_id,
                                 why="no findings ledger declared and gates.audit_ledger_required is off")
                return None
            return bt_audit_gate.Gate(
                False, (f"an audit task must declare one *{bt_audit_gate.LEDGER_SUFFIX} file",), (), ()
            )
        raw_ledger = self._read_ledger(order, path)
        gate = bt_audit_gate.evaluate(
            raw_ledger, [spec.id for spec in self.core.plan.tasks], order.task_id,
            self.audit_policy,
        )
        if not gate.problems and raw_ledger is not None and self.publish_audit_observation is not None:
            try:
                source = self._snapshot_source(order)
                status = "evaluated" if evaluate_gate else "not_run"
                observation = audit_observation_from_ledger(order, source, raw_ledger, gate_status=status)
                self.publish_audit_observation(order.task_id, order.attempt_id, observation)
            except (UnicodeDecodeError, ValueError, TypeError, KeyError) as error:
                raise RuntimeError("validated audit observation could not be published") from error
        if not evaluate_gate:
            return None
        if not gate.problems and raw_ledger is not None:
            gate = quality_audit_evidence.check(self, order, raw_ledger, gate)
        stray = bt_audit_gate.stray_changes(self._read_changes(order), task.expected_paths) \
            if self.audit_policy.read_only else ()
        if stray:
            return bt_audit_gate.Gate(False, (*gate.problems, bt_audit_gate.scope_problem(stray)), gate.blocking,
                                      gate.rework)
        return gate

    def _only_ledger_checks_failed(self, order: VerifyRequest, result) -> bool:
        """Whether the task is an audit whose every failed check names its own findings ledger. REQ-029 T8 verified with
        `recovery_acceptance.py audit --ledger <ledger>`, which exits 1 while a blocking finding is open: the audit could
        never pass, the gate that turns findings into remediation tasks never ran, and three attempts were spent."""
        try:
            task = self.core.plan.task(order.task_id)
        except m1.SchedulerError:
            return False
        path = bt_audit_gate.ledger_path(task.expected_paths) if task.meta.get("kind") == "audit" else None
        if path is None:
            return False
        # a check that was never run (CHECK_DEFERRED: a cheaper one failed first) is no failure of its own: REQ-020's T15 had `npm run gate`
        # deferred behind its two ledger checks, so «every failed check names the ledger» was false and the gate never spoke for 18 attempts
        failed = [c for c in result.get("checks") or () if isinstance(c, Mapping) and c.get("status") != "pass"
                  and c.get("issue_code") != "CHECK_DEFERRED"]
        return bool(failed) and all(str(c.get("command") or "").find(path) >= 0 for c in failed)

    def _recovery_coverage_gate(self, order: VerifyRequest, result: Mapping[str, Any]) -> bt_audit_gate.Gate | None:
        """Rechecks changed recovery surfaces against an M3 map and actual M6 check records."""
        problems = recovery_coverage_problems(self.core, order, result, self._resolver, self._snapshot_source,
                                              self._changes_from_snapshot)
        if problems is None:
            return None
        if problems:
            return bt_audit_gate.Gate(False, problems, (), ())
        return None


def _retry_is_due(last_response: object, attempts: object, now: datetime) -> bool:
    if not isinstance(attempts, int) or isinstance(attempts, bool) or attempts <= 0:
        return True
    if not isinstance(last_response, str):
        return True
    try:
        previous = datetime.fromisoformat(last_response)
        if previous.utcoffset() is None or now.utcoffset() is None:
            return True
        elapsed_seconds = (now - previous).total_seconds()
    except (TypeError, ValueError):
        return True
    delay = min(2 ** min(attempts - 1, 9), 300)
    return elapsed_seconds >= delay
