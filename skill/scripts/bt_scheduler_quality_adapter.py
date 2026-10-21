"""The M1/M3 boundary for durable M6 verification and correlated verdict delivery."""

from __future__ import annotations

import hashlib
import logging
import re
import subprocess
import threading
from collections.abc import Callable, Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_executor_adapter as executor_adapter
from bt_scheduler_quality.contracts import QualityError, VerifyRequest
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.identity import verdict_id
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.review import ReviewerPort
from bt_scheduler_quality.runner import SandboxRunner
import bt_audit_gate
from bt_scheduler_quality.snapshot import SnapshotResolver, SnapshotSource
from bt_scheduler_quality.store import QualityStore

m1 = scheduler_adapter.core
m3 = executor_adapter.m3
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
        remediate: Callable[[str, str, list[dict]], bool] | None = None,
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
        self.remediate = remediate                        # (audit, attempt, findings) -> True when they became remediation tasks
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

    def _audit_gate(self, order: VerifyRequest) -> bt_audit_gate.Gate | None:
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
        gate = bt_audit_gate.evaluate(
            self._read_ledger(order, path), [spec.id for spec in self.core.plan.tasks], order.task_id,
            self.audit_policy,
        )
        stray = bt_audit_gate.stray_changes(self._read_changes(order), task.expected_paths) \
            if self.audit_policy.read_only else ()
        if stray:
            return bt_audit_gate.Gate(False, (*gate.problems, bt_audit_gate.scope_problem(stray)), gate.blocking,
                                      gate.rework)
        return gate

    def _rework_plan(self, gate: bt_audit_gate.Gate, order: VerifyRequest) -> tuple[tuple[str, ...], bool]:
        """(tasks to send back, cascade). `downstream`: the named tasks and everything that depends on them. `named`
        (default): the named tasks plus the `kind: test` tasks over them, because their result no longer proves anything;
        what else depends on a named task keeps its accepted result, and the integrator merges the fix with it."""
        if self.audit_policy.rework_scope == "downstream":
            return tuple(gate.rework), True
        plan, ids = self.core.plan, list(gate.rework)
        for task_id in gate.rework:
            for later in plan.descendants(task_id):
                if later != order.task_id and later not in ids and plan.task(later).meta.get("kind") == "test":
                    ids.append(later)
        return tuple(spec.id for spec in plan.tasks if spec.id in ids), False

    def _integration_problem(self, order: VerifyRequest) -> str:
        """Why the verified result cannot be combined with the accepted work around it ('' when it can). A check that
        cannot run (no snapshot yet) is not a verdict: it returns ''."""
        if self.integration_check is None and self.unresolved_check is None:
            return ""
        try:
            source = self._snapshot_source(order)
            if not source:
                return ""
            left = self.unresolved_check(order.task_id, source.snapshot_sha) if self.unresolved_check else ()
            if left:
                return UNRESOLVED + ", ".join(left[:6])
            return self.integration_check(order.task_id, order.attempt_id, source.snapshot_sha) \
                if self.integration_check else ""
        except Exception as error:  # noqa: BLE001 - an outage is not a reason to reject work
            LOGGER.warning("integration check skipped (%s)", type(error).__name__)
            return ""

    def _write_note(self, task_ids, text: str) -> None:
        for task_id in task_ids if self.rework_notes is not None else ():
            try:
                self.rework_notes(task_id, text)
            except OSError as error:
                LOGGER.warning("note not written for %s (%s)", task_id, type(error).__name__)

    def _prior_clashes(self, task_id: str) -> int:
        return self.core.read(lambda ctx: sum(
            1 for attempt in ctx.state.tasks[task_id].attempts
            if str(ctx.state.attempts[attempt].failure).startswith("integration gate:")))

    def _dependents_to_redo(self, clash: str, task_id: str) -> tuple[str, ...]:
        """The accepted tasks on the other side of a clash, once `task_id` has been rejected `integration_retries` times
        for it and still cannot fit around them: they were built on the result it replaces, so they give way. Empty when
        the task still has retries, the other side is not a set of accepted tasks, or the rework cannot start now."""
        if self._prior_clashes(task_id) < self.integration_retries:
            return ()
        sides = clash.split(" for ")[0].split(" vs ")
        others = [t for side in sides if task_id not in side.split("+") for t in side.split("+")]
        known = {spec.id for spec in self.core.plan.tasks}
        done = self.core.read(lambda ctx: {t for t, rec in ctx.state.tasks.items() if rec.state == "completed"})
        redo = tuple(t for t in others if t in known and t in done and t != task_id)
        # The give-way is not an audit verdict on those tasks, so `max_reworks` (a limit on audit rework) must not
        # refuse it: it did, and the task that caused the clash was rejected again and again for a clash only the others
        # could resolve (REQ-027 T4a vs T5a, seven attempts). Its own ceiling stops a ping-pong.
        if not redo or self.core.rework_problem(redo, (), False, owner=True) \
                or self.core.read(lambda ctx: any(ctx.state.tasks[t].reworks >= self.integration_rework_limit for t in redo)):
            return ()
        return redo

    def _failure_digest(self, result) -> str:
        """The failing checks of an M6 result, with the tail of what each printed: what the agent must read to fix them."""
        seen: set[tuple] = set()
        blocks = []
        for check in result.get("checks") or ():
            if not isinstance(check, Mapping) or check.get("status") == "pass":
                continue
            key = (check.get("command"), check.get("stderr_ref"), check.get("stdout_ref"))
            if key in seen:
                continue
            seen.add(key)
            streams = []
            for ref in (check.get("stderr_ref"), check.get("stdout_ref")):
                try:
                    raw = self.store.get_artifact(ref) or b"" if isinstance(ref, str) else b""
                except Exception:  # noqa: BLE001 - a missing artifact only shortens the note
                    raw = b""
                text = _without_noise(raw.decode("utf-8", "replace"))
                if text:
                    streams.append(text)
            full = "\n".join(streams)          # both streams: a build prints its errors on stdout, its notices on stderr
            tail = full[-1500:]
            # a long run buries the first failures above the tail: name every failing test, then the error lines, before it
            names = [m.group(0)[:200] for m in re.finditer(r"(?m)^(?:FAIL|ERROR): .+|^FAILED \S+::.+", full)][:12]
            listing = ("Failing tests (" + str(len(names)) + (" shown" if len(names) == 12 else "") + "):\n"
                       + "\n".join(names) + "\n\n") if names else ""
            if len(full) > len(tail):
                lines = [line.strip()[:200] for line in full[:-len(tail)].splitlines() if _ERROR_LINE.search(line)][:20]
                listing += ("Earlier error lines:\n" + "\n".join(lines) + "\n\n") if lines else ""
            blocks.append(f"$ {check.get('command')}\nexit code {check.get('exit_code')}\n{listing}{tail}")
            if len(blocks) == 3:
                break
        if not blocks:
            return ""
        text = "\n".join(blocks)
        missing = ("A check cannot find a module or package: that is a dependency problem, not a code problem. Install the "
                   "locked dependencies in your worktree with the package manager (for npm: `npm ci --offline`) and run the "
                   "check yourself; do not edit configuration to avoid the import.\n\n"
                   if re.search(r"MODULE_NOT_FOUND|Cannot find (?:module|package)|No module named|ModuleNotFoundError", text)
                   else "")
        return (missing + "The independent verification of your previous attempt failed. The checks run in a sandbox: "
                "`node_modules` mounted read-only, a clean copy of your final files, none of your environment variables. Fix the cause shown here before "
                "anything else:\n\n" + "\n\n".join(blocks))

    def _write_verify_note(self, order: VerifyRequest, result) -> None:
        if self.verify_notes is None or not isinstance(result, Mapping):
            return
        try:
            if result.get("status") == "FAIL":
                digest = self._failure_digest(result)
                self.verify_notes(order.task_id, digest)
                if self.verify_history is not None:
                    self.verify_history(order.task_id, order.attempt_id, digest)
            elif result.get("status") == "PASS":
                self.verify_notes(order.task_id, "")
        except OSError as error:
            LOGGER.warning("verification note not written for %s (%s)", order.task_id, type(error).__name__)

    def _write_rework_notes(self, gate: bt_audit_gate.Gate, order: VerifyRequest) -> None:
        if self.rework_notes is None:
            return
        ids, cascade = self._rework_plan(gate, order)
        for task_id in self.core.rework_scope(ids, (order.task_id,), cascade):
            try:
                self.rework_notes(task_id, bt_audit_gate.note_for(gate, task_id, order.task_id))
            except OSError as error:
                LOGGER.warning("audit rework note not written for %s (%s)", task_id, type(error).__name__)

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
            self._write_verify_note(order, result)
            gate = self._audit_gate(order) if accepted else None
            clash = self._integration_problem(order) if accepted and (gate is None or gate.ok) else ""
            give_way: tuple[str, ...] = ()
            if clash:
                give_way = self._dependents_to_redo(clash, order.task_id)
                if give_way:
                    # the task already tried to fit around them: its result is accepted and they are rebuilt on top of it
                    self._write_note(give_way, _give_way_note(order.task_id, clash))
                else:
                    accepted = False
                    evidence = f"integration gate: {clash} | M6 evidence: {evidence}"[:2000]
                    self._write_note((order.task_id,), _unresolved_note(clash) if clash.startswith(UNRESOLVED)
                                     else _integration_note(clash))
            remediating = False
            if gate is not None and gate.blocking and not gate.problems and self.remediate is not None:
                try:
                    remediating = bool(self.remediate(order.task_id, order.attempt_id, list(gate.blocking)))
                except Exception as error:  # noqa: BLE001 - when it cannot, the named tasks are sent back as before
                    LOGGER.warning("remediation not requested (%s)", type(error).__name__)
            if gate is not None and not gate.ok:
                accepted = False
                tail = " | the findings become remediation tasks; this audit runs again after them" if remediating else ""
                evidence = f"{gate.summary()}{tail} | M6 evidence: {evidence}"[:2000]
            else:
                gate = None
            if accepted:
                self._write_note((order.task_id,), "")       # accepted: the notes of earlier rounds no longer apply
            identity = verdict_id(order, delivery["result_hash"], resolution_id=resolution_id)
            if gate is not None:  # a rejection by the gate is a different verdict from the PASS M6 reached
                material = f"{identity}\0audit-gate\0{gate.digest()}".encode()
                identity = "m6v-" + hashlib.sha256(material).hexdigest()
            verdict = m1.Verdict(
                identity,
                order.plan_id,
                order.revision,
                order.task_id,
                order.attempt_id,
                accepted,
                verifier,
                evidence,
                order.token,
            )
            if gate is not None and gate.rework and not remediating:
                ids, cascade = self._rework_plan(gate, order)
                if not self.core.rework_problem(ids, (order.task_id,), cascade):
                    self._write_rework_notes(gate, order)
                response, _moved = self.core.reject_and_rework(verdict, ids, "audit-gate", gate.summary(),
                                                               cascade=cascade)
            else:
                response = self.core.submit_verdict(verdict)
                if give_way and response.status == "applied":
                    self.core.rework(give_way, "integration-gate", f"{order.task_id} was accepted and clashes with "
                                     f"{', '.join(give_way)}: {clash}"[:300], cascade=False)
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


def _attempt_worktree(attempts_root: Path, attempt_dir: Path) -> Path | None:
    """`<executor>/ws/worktrees/<same name as the attempt directory>`, only when it really sits there."""
    try:
        parent = (attempts_root.parent / "ws" / "worktrees").resolve(strict=True)
        worktree = (parent / attempt_dir.name).resolve(strict=True)
        worktree.relative_to(parent)
    except (OSError, ValueError):
        return None
    return worktree if worktree.is_dir() else None


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


UNRESOLVED = "merge conflict markers left in: "


def _unresolved_note(clash: str) -> str:
    return (f"Your result still contains unresolved merge conflict markers ({clash.removeprefix(UNRESOLVED)}). Your tree "
            "started as a merge in progress: open every file with `<<<<<<<` / `=======` / `>>>>>>>` lines, combine both "
            "sides' behaviour, delete the markers, and run the tests again.")


_NOISE_LINE = re.compile(r"^\s*npm (?:notice|warn(?:ing)?)\b", re.IGNORECASE)
_ERROR_LINE = re.compile(r"\b(?:error|TS\d{4}|Traceback|AssertionError|Cannot find|not defined|is not a function)\b|✖|\bFAIL", re.IGNORECASE)


def _without_noise(text: str) -> str:
    """The output without lines that never explain a failure (`npm notice ...`, `npm warn ...`) and blank runs."""
    kept = [line for line in text.splitlines() if not _NOISE_LINE.match(line)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()



def _integration_note(clash: str) -> str:
    return ("Your result passed its checks but cannot be combined with work that was already accepted: "
            f"{clash}. Tasks that come after it, or were built on an earlier result of this one, would collide with it. "
            "Redo it as a small change on top of the result you started from: keep every file and function it already "
            "has, edit only what the task and the audit notes require, and do not rewrite or delete working code.")


def _give_way_note(task_id: str, clash: str) -> str:
    return (f"{task_id} was changed after this task was built (an audit finding needed it), and the two touch the same "
            f"code: {clash}. Your tree now contains the new {task_id}. Redo this task on top of it: keep what your earlier "
            "result did that is still right, adapt it to the new code instead of overwriting it, and do not delete working "
            "code.")


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
            _attempt_worktree(root, attempt_real),
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
