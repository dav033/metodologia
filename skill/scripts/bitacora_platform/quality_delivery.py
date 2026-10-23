"""Verdict delivery, integration refusal, rework and failure notes for the M6 port."""
from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Mapping

import bt_audit_gate
import bt_scheduler_adapter as scheduler_adapter
from bt_scheduler_quality.contracts import VerifyRequest
from bt_scheduler_quality.identity import verdict_id
from bt_scheduler_recovery_adapter import (
    EvidenceUnavailable,
    integration_problem,
    publish_or_raise,
    refusal_detail,
)

from .quality_notes import (
    _ERROR_LINE,
    REVERTED,
    UNRESOLVED,
    _give_way_note,
    _integration_note,
    _reverted_note,
    _unresolved_note,
    _without_noise,
)
from .quality_review_gate import VERIFIER as AUDIT_GATE_VERIFIER

m1 = scheduler_adapter.core
LOGGER = logging.getLogger("bt_scheduler_quality_adapter")


class QualityDeliveryMethods:
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
        """Run the M6 structural check at its fail-closed boundary (a missing snapshot or an outage is NOT a pass)."""
        return integration_problem(lambda: self._snapshot_source(order), order.task_id, order.attempt_id,
                                   self.integration_check, self.unresolved_check, self.revert_check)

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
                or any(self._give_ways_of(t) >= self.integration_rework_limit for t in redo):
            return ()
        return redo

    def _give_ways_of(self, task_id: str) -> int:
        """How many times the integration gate itself sent `task_id` back to give way. Only these count against
        `integration_rework_limit`: audit and operator reworks (REQ-027 T18.3 had six of them) say nothing about a
        ping-pong between two tasks that keep clashing."""
        return sum(1 for entry in self.core.audit_log()
                   if entry.kind == "rework_requested" and entry.detail.get("by") == "integration-gate"
                   and task_id in (entry.detail.get("named") or ()))

    def _failure_digest(self, result) -> str:
        """The failing checks of an M6 result, with the tail of what each printed: what the agent must read to fix them."""
        seen: set[tuple] = set()
        blocks = []
        # what really FAILED first: the plan's order put two manual checks and a deferred one ahead of the e2e that failed, and the
        # three-block cap then hid the failure itself from the agent, the diagnosis and the self-healing (REQ-020 T14a, 14 attempts)
        ordered = sorted((c for c in result.get("checks") or () if isinstance(c, Mapping) and c.get("status") != "pass"),
                         key=lambda c: 0 if c.get("status") == "fail" else 1)
        for check in ordered:
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
            coverage_gate = self._recovery_coverage_gate(order, result) if accepted and isinstance(result, Mapping) else None
            gate = coverage_gate
            audit_kind = False
            try:
                audit_kind = self.core.plan.task(order.task_id).meta.get("kind") == "audit"
            except m1.SchedulerError:
                pass
            deferred = not accepted and result.get("status") == "FAIL" and self._only_ledger_checks_failed(order, result)
            negative_gate = verifier == AUDIT_GATE_VERIFIER and not accepted
            audit_gate = (self._audit_gate(order, evaluate_gate=accepted or deferred or negative_gate, check_status=str(result.get("status")))
                          if audit_kind and (result.get("status") in {"PASS", "FAIL"} or negative_gate) else None)
            if deferred:
                # the gate judges the ledger (and turns blocking findings into remediation); a check that asked the same
                # question as an exit code cannot also stop the audit before the gate speaks
                if audit_gate is not None and not audit_gate.ok:
                    accepted = True              # rejected below, by the gate, with its evidence and its remediation
                else:
                    audit_gate = None
            if gate is None:
                gate = audit_gate
            elif audit_gate is not None and not audit_gate.ok:
                gate = bt_audit_gate.Gate(False, (*gate.problems, *audit_gate.problems), audit_gate.blocking,
                                          audit_gate.rework)
            try:
                clash = self._integration_problem(order) if accepted and (gate is None or gate.ok) else ""
            except EvidenceUnavailable as error:
                if str(error).startswith("evidence_unavailable:"):
                    self.store.finish_delivery(request_key, "pending", str(error))
                    return "pending"
                raise
            give_way: tuple[str, ...] = ()
            if clash:
                give_way = self._dependents_to_redo(clash, order.task_id)
                if give_way:
                    # the task already tried to fit around them: its result is accepted and they are rebuilt on top of it
                    self._write_note(give_way, _give_way_note(order.task_id, clash))
                else:
                    accepted = False
                    refusal = refusal_detail(self.core, clash, order.task_id)
                    reference = publish_or_raise(self.publish_conflict_observation, order, clash,
                                                 "ordinary_rework_refused", refusal)
                    if reference is None:
                        evidence = f"integration gate: {clash} | rework refusal: {refusal} | M6 evidence: {evidence}"[:2000]
                    else:
                        evidence = f"integration conflict evidence: {reference} | M6 evidence: {evidence}"[:2000]
                    self._write_note((order.task_id,), _unresolved_note(clash) if clash.startswith(UNRESOLVED)
                                     else _reverted_note(clash) if clash.startswith(REVERTED)
                                     else _integration_note(clash))
            remediating = False
            stale_evidence = gate is not None and any(f.get("code") == "STALE_EVIDENCE" for f in gate.blocking)
            if gate is not None and gate.blocking and not gate.problems and not stale_evidence and self.remediate is not None:
                try:
                    remediating = bool(self.remediate(order.task_id, order.attempt_id, list(gate.blocking)))
                except Exception as error:  # noqa: BLE001 - when it cannot, the named tasks are sent back as before
                    LOGGER.warning("remediation not requested (%s)", type(error).__name__)
            if gate is not None and not gate.ok:
                accepted = False
                tail = " | the findings become remediation tasks; this audit runs again after them" if remediating else ""
                prefix = "verification_replan/blocked: " if coverage_gate is not None and not coverage_gate.ok else ""
                evidence = f"{prefix}{gate.summary()}{tail} | M6 evidence: {evidence}"[:2000]
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
                problem = self.core.rework_problem(ids, (order.task_id,), cascade)
                if not problem or problem.startswith(("limit", "impact")):
                    # also when the system will not send the tasks back by itself: the owner who decides to will find the
                    # real text of each finding already written for the task, not only the reason he types
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
                "M6 verdict submission remains pending (%s: %s)", type(error).__name__, str(error)[:300]
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
