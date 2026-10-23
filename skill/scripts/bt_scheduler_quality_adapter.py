"""The M1/M3 boundary for durable M6 verification and correlated verdict delivery."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import bt_scheduler_core as m1
import bt_scheduler_executor as m3
from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.identity import verdict_id
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.review import ReviewerPort
from bt_scheduler_quality.runner import SandboxRunner
from bt_scheduler_quality.snapshot import SnapshotResolver, SnapshotSource
from bt_scheduler_quality.store import QualityStore

RepositoryResolver = Callable[[m1.VerifyOrder], Path | str | None]
LOGGER = logging.getLogger(__name__)


class QualityVerificationPort:
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
    ):
        self.core = core
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
        self.engine = QualityEngine(
            policy, store, reviewer=reviewer, runner=runner, resolver=snapshot_resolver
        )
        self._pool = ThreadPoolExecutor(
            max_workers=policy.max_concurrent, thread_name_prefix="m6-quality"
        )
        self._active: set[str] = set()
        self._active_lock = threading.Lock()
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
        self.reconcile_outbox(force=True)
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._dispatch_loop, name="m6-quality-dispatch", daemon=True
        )
        self._thread.start()
        self._wake.set()

    def close(self, *, wait: bool = True) -> None:
        self._closed = True
        self._stop.set()
        self._wake.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._pool.shutdown(wait=wait, cancel_futures=False)

    def request(self, order: m1.VerifyOrder) -> m1.Ack:
        try:
            parsed = VerifyRequest.from_mapping(_order_mapping(order))
        except (QualityError, TypeError, ValueError) as error:
            code = error.code if isinstance(error, QualityError) else "ORDER_INVALID"
            return m1.Ack("rejected", code)
        if not _matches_approved_plan(self.core, order, parsed):
            return m1.Ack("rejected", "ORDER_DIFFERS_FROM_APPROVED_PLAN")
        try:
            state, _ = self.store.reserve(
                parsed, max_pending=self.policy.max_pending_requests
            )
        except QualityError as error:
            if error.code in {"IDEMPOTENCY_CONFLICT", "QUALITY_BUSY", "ORDER_INVALID"}:
                return m1.Ack("rejected", error.code)
            raise
        self._wake.set()
        return m1.Ack("duplicate" if state != "new" else "accepted", "durably admitted")

    def reconcile_outbox(self, *, force: bool = False) -> dict[str, int]:
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

    def _deliver_one(self, request_key: str) -> str:
        delivery = self.store.begin_delivery(request_key)
        if delivery is None:
            return "none"
        try:
            order = VerifyRequest.from_mapping(delivery["request_json"])
            result = delivery["result_json"]
            if result.get("status") in {"PASS", "FAIL"}:
                accepted = result["status"] == "PASS"
                verifier = result["verifier"]["identity"]
                evidence = result["evidence_manifest"]
                resolution_id = ""
            elif delivery.get("review_state") == "resolved" and delivery.get(
                "decision"
            ) in {"PASS", "FAIL"}:
                accepted = delivery["decision"] == "PASS"
                verifier = delivery["resolved_by"]
                evidence = delivery["evidence_ref"]
                resolution_id = delivery["resolution_id"]
            else:
                self.store.finish_delivery(
                    request_key, "pending", "review is not resolved"
                )
                return "pending"
            if (
                not isinstance(verifier, str)
                or not verifier.strip()
                or not isinstance(evidence, str)
                or not evidence
            ):
                self.store.finish_delivery(
                    request_key, "pending", "verdict evidence is incomplete"
                )
                return "pending"
            verdict = m1.Verdict(
                verdict_id(order, delivery["result_hash"], resolution_id=resolution_id),
                order.plan_id,
                order.revision,
                order.task_id,
                order.attempt_id,
                accepted,
                verifier,
                evidence,
                order.token,
            )
            response = self.core.submit_verdict(verdict)
        # Retain the outbox entry when any unexpected M1 integration failure occurs.
        except Exception as error:  # noqa: BLE001
            self.store.finish_delivery(request_key, "pending", type(error).__name__)
            LOGGER.warning(
                "M6 verdict submission remains pending (%s)", type(error).__name__
            )
            return "pending"
        if response.status in {"applied", "duplicate"}:
            self.store.finish_delivery(request_key, "delivered", response.status)
            return "delivered"
        if response.status == "stale":
            self.store.finish_delivery(request_key, "stale", response.reason)
            return "stale"
        self.store.finish_delivery(
            request_key, "pending", response.reason or response.status
        )
        return "pending"


def _read_snapshot_inputs(
    executor: m3.AgentExecutor,
    repository_for_order: RepositoryResolver,
    order: VerifyRequest,
) -> tuple[object, object]:
    try:
        return executor.describe(order.attempt_id), repository_for_order(
            _to_m1_order(order)
        )
    # M3 integrations can raise provider-specific exceptions; no provenance means review.
    except Exception as error:  # noqa: BLE001
        LOGGER.warning("M6 attempt description unavailable (%s)", type(error).__name__)
        return None, None


def _captured_handoff(
    description: object, attempt_id: str
) -> tuple[str, Mapping[str, object]] | None:
    if (
        not isinstance(description, Mapping)
        or description.get("attempt_id") != attempt_id
    ):
        return None
    handoff, artifacts = description.get("handoff"), description.get("artifacts")
    if (
        not isinstance(handoff, Mapping)
        or handoff.get("status") != "captured"
        or not isinstance(artifacts, Mapping)
    ):
        return None
    directory = artifacts.get("dir")
    if not isinstance(directory, str):
        return None
    return directory, handoff


def _build_snapshot_source(
    attempts_root: Path,
    attempt_id: str,
    directory: str,
    handoff: Mapping[str, object],
    repository: object,
) -> SnapshotSource | None:
    if not isinstance(repository, (str, Path)):
        return None
    attempt_dir = Path(directory)
    try:
        if ".." in attempt_dir.parts:
            return None
        root = attempts_root.resolve(strict=True)
        attempt_real = attempt_dir.resolve(strict=True)
        attempt_real.relative_to(root)
        if attempt_dir.is_symlink() or not attempt_real.is_dir():
            return None
        expected_manifest = attempt_dir / "handoff" / "manifest.json"
        advertised_manifest = handoff.get("manifest")
        if advertised_manifest is not None and (
            not isinstance(advertised_manifest, str)
            or Path(advertised_manifest) != expected_manifest
        ):
            return None
        repo = Path(repository).resolve(strict=True)
        if not repo.is_dir():
            return None
        base_sha, snapshot_sha = handoff.get("base_sha"), handoff.get("snapshot_sha")
        if not isinstance(base_sha, str) or not isinstance(snapshot_sha, str):
            return None
        return SnapshotSource(
            attempt_id,
            repo,
            attempt_real,
            expected_manifest,
            base_sha,
            snapshot_sha,
        )
    except (OSError, ValueError):
        return None


def _order_mapping(order: m1.VerifyOrder) -> dict[str, object]:
    if not isinstance(order, m1.VerifyOrder):
        raise QualityError(
            "ORDER_INVALID", "M1 supplied an invalid VerifyOrder instance"
        )
    return {
        "idempotency_key": order.idempotency_key,
        "plan_id": order.plan_id,
        "revision": order.revision,
        "task_id": order.task_id,
        "attempt_id": order.attempt_id,
        "token": order.token,
        "acceptance_criteria": list(order.acceptance_criteria),
        "verification": [
            dict(item) if isinstance(item, Mapping) else item
            for item in order.verification
        ],
    }


def _to_m1_order(order: VerifyRequest) -> m1.VerifyOrder:
    return m1.VerifyOrder(
        order.idempotency_key,
        order.plan_id,
        order.revision,
        order.task_id,
        order.attempt_id,
        order.token,
        order.acceptance_criteria,
        tuple(item.to_dict() for item in order.verification),
    )


def _matches_approved_plan(
    core: m1.SchedulerCore, order: m1.VerifyOrder, parsed: VerifyRequest
) -> bool:
    plan = core.plan
    if order.plan_id != plan.plan_id or order.revision != plan.revision:
        return False
    try:
        task = plan.task(order.task_id)
        expected = VerifyRequest.from_mapping(
            {
                **_order_mapping(order),
                "acceptance_criteria": list(task.acceptance_criteria),
                "verification": [dict(item) for item in task.verification],
            }
        )
    except (QualityError, ValueError, TypeError):
        return False
    return (
        parsed.acceptance_criteria == expected.acceptance_criteria
        and parsed.verification == expected.verification
    )


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
