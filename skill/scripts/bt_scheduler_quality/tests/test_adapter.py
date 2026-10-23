from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path

import bt_scheduler_core as m1
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from bt_scheduler_quality_adapter import QualityVerificationPort, _retry_is_due
from test_snapshot import _make_snapshot


class DescribedM3:
    def __init__(self, attempts_root: Path):
        self.attempts_dir = attempts_root
        self.descriptions = {}

    def add_attempt(self, attempt_id: str, source) -> None:
        attempt_dir = self.attempts_dir / attempt_id
        handoff_dir = attempt_dir / "handoff"
        handoff_dir.mkdir(parents=True)
        manifest = {
            "schema": 1,
            "attempt_id": attempt_id,
            "repository": str(source.repository),
            "base_sha": source.base_sha,
            "snapshot_sha": source.snapshot_sha,
            "status": "captured",
            "dirty": True,
            "untracked_count": 1,
        }
        manifest_path = handoff_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        self.descriptions[attempt_id] = {
            "attempt_id": attempt_id,
            "state": "finished",
            "handoff": {
                "status": "captured",
                "base_sha": source.base_sha,
                "snapshot_sha": source.snapshot_sha,
                "manifest": str(manifest_path),
            },
            "artifacts": {"dir": str(attempt_dir)},
        }

    def describe(self, attempt_id: str):
        return self.descriptions.get(attempt_id)


class BlockingRunner:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.calls = []

    def run(self, check, snapshot_root, *, timeout_seconds=None):
        self.calls.append(check.command)
        self.started.set()
        if not self.release.wait(timeout=5):
            return CommandOutcome(
                "unknown", None, 5000, b"", b"", "CHECK_TIMEOUT", True
            )
        return CommandOutcome("pass", 0, 3, b"check passed\n", b"", None, True)


class ScriptedRunner:
    def __init__(self, failing_commands=()):
        self.failing_commands = set(failing_commands)
        self.calls = []

    def run(self, check, snapshot_root, *, timeout_seconds=None):
        self.calls.append(check.command)
        if check.command in self.failing_commands:
            return CommandOutcome("fail", 5, 2, b"test failure\n", b"", None, True)
        return CommandOutcome("pass", 0, 2, b"test pass\n", b"", None, True)


class M6M1AdapterTests(unittest.TestCase):
    def _system(
        self, tasks, *, runner=None, recovery=None, max_attempts=1, store_path=None
    ):
        temporary = tempfile.TemporaryDirectory(prefix="m6-m1-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        plan_value = {
            "schema_version": "1.0.0",
            "plan_id": "PLAN-M6-INTEGRATION",
            "revision": 1,
            "tasks": tasks,
        }
        plan_text = json.dumps(plan_value)
        plan = m1.load_plan(
            plan_text, approved_sha256=hashlib.sha256(plan_text.encode()).hexdigest()
        )
        execution = m1.FakeExecutor()
        ports = m1.Ports(execution=execution, recovery=recovery)
        core = m1.SchedulerCore(
            plan,
            m1.InMemoryRepository(),
            config=m1.Config(max_parallel_tasks=4, max_attempts=max_attempts),
            ports=ports,
        )
        core.start()
        attempts_root = root / "m3-attempts"
        attempts_root.mkdir(mode=0o700)
        executor = DescribedM3(attempts_root)
        store = QualityStore(store_path or ":memory:")
        adapter = QualityVerificationPort(
            core,
            executor,
            store,
            QualityPolicy(),
            lambda order: root / order.task_id,
            runner=runner or ScriptedRunner(),
        )
        core.ports.verification = adapter
        adapter.start()
        self.addCleanup(store.close)
        self.addCleanup(adapter.close)
        return root, core, execution, executor, store, adapter

    def _start_attempts(
        self,
        core: m1.SchedulerCore,
        executor: DescribedM3,
        root: Path,
        task_ids: tuple[str, ...],
    ):
        core.step()
        attempts = {}
        for task_id in task_ids:
            attempt_id = core.snapshot().tasks[task_id]["attempt"]
            attempts[task_id] = attempt_id
            source_root = root / f"source-{task_id}"
            source_root.mkdir()
            repo, source, _, _ = _make_snapshot(source_root)
            task_repo = root / task_id
            task_repo.symlink_to(repo, target_is_directory=True)
            executor.add_attempt(attempt_id, source)
            token = core.read(
                lambda ctx, current=attempt_id: ctx.state.attempts[current].token
            )
            for kind in ("execution_started", "execution_finished"):
                event = m1.Event(
                    f"{task_id}-{kind}",
                    core.plan.plan_id,
                    core.plan.revision,
                    task_id,
                    attempt_id,
                    "m3-test",
                    kind,
                    token=token,
                )
                self.assertEqual(core.ingest(event).status, "applied")
        return attempts

    def test_ack_is_durable_admission_and_execution_finished_does_not_complete(self):
        runner = BlockingRunner()
        task = _task("T1", "python3 verify.py")
        root, core, _, executor, store, _adapter = self._system([task], runner=runner)
        self.addCleanup(runner.release.set)
        attempts = self._start_attempts(core, executor, root, ("T1",))

        core.step()

        self.assertTrue(runner.started.wait(timeout=3))
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "active")
        request_key = _request_key(core, attempts["T1"])
        self.assertIn(request_key, {key for key, _ in store.pending_requests()})
        self.assertIsNone(store.get_result(request_key))
        runner.release.set()
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed")
        )
        result = store.get_result(request_key)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            core.snapshot().tasks["T1"]["evidence"].startswith("m6://result/"), True
        )

    def test_failed_check_reaches_m5_while_an_independent_task_completes(self):
        recovery = m1.ScriptedRecovery(
            {"T1": m1.RecoveryProposal("block", "required test failed")}
        )
        runner = ScriptedRunner({"python3 fail.py"})
        tasks = [_task("T1", "python3 fail.py"), _task("T2", "python3 pass.py")]
        root, core, _, executor, _, _ = self._system(
            tasks, runner=runner, recovery=recovery
        )
        attempts = self._start_attempts(core, executor, root, ("T1", "T2"))

        core.step()

        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T2"]["state"] == "completed")
        )
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "recovering")
        )
        core.step()
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "blocked")
        self.assertEqual(core.snapshot().tasks["T2"]["state"], "completed")
        self.assertEqual(
            [call.cause for call in recovery.calls], ["verification_rejected"]
        )
        self.assertEqual(set(attempts), {"T1", "T2"})

    def test_needs_review_keeps_m1_verifying_until_explicit_operator_resolution(self):
        task = _task("T1", "inspect visual output", manual=True)
        root, core, _, executor, _, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))

        core.step()

        self.assertTrue(_wait_for(lambda: len(adapter.list_reviews()) == 1))
        review = adapter.list_reviews()[0]
        self.assertEqual(review["result"]["status"], "NEEDS_REVIEW")
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "active")
        adapter.resolve_review(
            review["request_key"],
            "david",
            "PASS",
            "I inspected the approved visual output.",
        )

        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed")
        )
        self.assertEqual(
            adapter.inspect_review(review["request_key"])["state"], "resolved"
        )
        self.assertEqual(core.snapshot().tasks["T1"]["attempt"], attempts["T1"])

    def test_outbox_retries_the_same_verdict_id_after_m1_applied_but_ack_was_lost(self):
        task = _task("T1", "python3 verify.py")
        root, core, _, executor, store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        original = core.submit_verdict
        submitted_ids = []

        def apply_then_lose_ack(verdict):
            submitted_ids.append(verdict.verdict_id)
            result = original(verdict)
            if len(submitted_ids) == 1:
                raise ConnectionError("simulated lost acknowledgement")
            return result

        core.submit_verdict = apply_then_lose_ack
        core.step()

        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed")
        )
        request_key = _request_key(core, attempts["T1"])
        self.assertEqual(len(store.pending_deliveries()), 1)
        self.assertEqual(adapter.reconcile_outbox(force=True)["delivered"], 1)
        self.assertEqual(len(submitted_ids), 2)
        self.assertEqual(submitted_ids[0], submitted_ids[1])
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")
        self.assertEqual(store.pending_deliveries(), ())
        self.assertIsNotNone(request_key)

    def test_empty_evidence_is_never_submitted_as_an_m1_verdict(self):
        task = _task("T1", "python3 verify.py")
        root, core, _, executor, store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        submitted = []

        def unavailable(verdict):
            submitted.append(verdict)
            raise ConnectionError("M1 unavailable")

        core.submit_verdict = unavailable
        core.step()
        request_key = _request_key(core, attempts["T1"])
        self.assertTrue(_wait_for(lambda: len(store.pending_deliveries()) == 1))
        self.assertEqual(len(submitted), 1)

        original_begin_delivery = store.begin_delivery

        def erase_evidence(key):
            delivery = original_begin_delivery(key)
            if delivery is not None:
                delivery["result_json"]["evidence_manifest"] = ""
            return delivery

        store.begin_delivery = erase_evidence
        submitted.clear()
        result = adapter.reconcile_outbox(force=True)

        self.assertEqual(result["pending"], 1)
        self.assertEqual(submitted, [])
        self.assertEqual(len(store.pending_deliveries()), 1)
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "active")
        self.assertIsNotNone(store.get_result(request_key))

    def test_retry_time_without_timezone_is_treated_as_malformed(self):
        now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

        self.assertTrue(_retry_is_due("2026-10-15T11:59:00", 1, now))

    def test_retry_delay_caps_at_five_minutes(self):
        now = datetime(2026, 10, 15, 12, 0, tzinfo=UTC)

        self.assertFalse(_retry_is_due("2026-10-15T11:55:01+00:00", 10, now))
        self.assertTrue(_retry_is_due("2026-10-15T11:55:00+00:00", 10, now))

    def test_restart_replays_persisted_verdict_without_rerunning_the_check(self):
        task = _task("T1", "python3 verify.py")
        store_directory = tempfile.TemporaryDirectory(prefix="m6-restart-store-")
        self.addCleanup(store_directory.cleanup)
        store_path = Path(store_directory.name) / "quality.sqlite3"
        root, core, _, executor, store, adapter = self._system(
            [task], store_path=store_path
        )
        attempts = self._start_attempts(core, executor, root, ("T1",))
        runner = adapter.engine.runner
        submit = core.submit_verdict
        submitted_ids = []

        def unavailable(verdict):
            submitted_ids.append(verdict.verdict_id)
            raise ConnectionError("M1 unavailable")

        core.submit_verdict = unavailable
        core.step()
        request_key = _request_key(core, attempts["T1"])
        self.assertTrue(_wait_for(lambda: len(store.pending_deliveries()) == 1))
        self.assertEqual(store.get_result(request_key)["status"], "PASS")
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "active")

        adapter.close()
        store.close()
        reopened = QualityStore(store_path)
        resumed = QualityVerificationPort(
            core,
            executor,
            reopened,
            QualityPolicy(),
            lambda order: root / order.task_id,
            runner=runner,
        )
        self.addCleanup(reopened.close)
        self.addCleanup(resumed.close)
        core.ports.verification = resumed

        def recover(verdict):
            submitted_ids.append(verdict.verdict_id)
            return submit(verdict)

        core.submit_verdict = recover
        resumed.start()

        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")
        self.assertEqual(submitted_ids[0], submitted_ids[1])
        self.assertEqual(len(runner.calls), 1)
        self.assertEqual(reopened.pending_deliveries(), ())

    def test_order_changed_from_approved_plan_is_rejected_before_reservation_or_execution(
        self,
    ):
        task = _task("T1", "python3 verify.py")
        root, core, _, executor, store, adapter = self._system([task])
        attempts = self._start_attempts(core, executor, root, ("T1",))
        approved = _order_from_plan(core, "T1", attempts["T1"])
        tampered = m1.VerifyOrder(
            approved.idempotency_key,
            approved.plan_id,
            approved.revision,
            approved.task_id,
            approved.attempt_id,
            approved.token,
            approved.acceptance_criteria,
            (
                {
                    "type": "command",
                    "value": "python3 attacker.py",
                    "purpose": "T1 acceptance",
                },
            ),
        )

        response = adapter.request(tampered)

        self.assertEqual(response.status, "rejected")
        self.assertEqual(response.detail, "ORDER_DIFFERS_FROM_APPROVED_PLAN")
        self.assertEqual(store.pending_requests(), ())
        self.assertEqual(adapter.engine.runner.calls, [])

    def test_stale_m1_reply_marks_the_stored_result_and_stops_delivery(self):
        task = _task("T1", "python3 verify.py")
        runner = BlockingRunner()
        root, core, _, executor, store, _ = self._system([task], runner=runner)
        self.addCleanup(runner.release.set)
        attempts = self._start_attempts(core, executor, root, ("T1",))

        core.step()
        self.assertTrue(runner.started.wait(timeout=3))
        self.assertEqual(
            core.resolve_attempt(
                attempts["T1"], "failed", "david", "superseded during verification"
            ),
            "failed",
        )
        runner.release.set()

        request_key = _request_key(core, attempts["T1"])
        self.assertTrue(
            _wait_for(
                lambda: (store.get_result(request_key) or {}).get("status") == "STALE"
            )
        )
        self.assertEqual(store.pending_deliveries(), ())
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "recovering")


def _task(task_id: str, command: str, *, manual: bool = False) -> dict[str, object]:
    verification = (
        {
            "type": "manual",
            "value": command,
            "purpose": f"{task_id} acceptance",
            "expected": "the visual output matches",
        }
        if manual
        else {"type": "command", "value": command, "purpose": f"{task_id} acceptance"}
    )
    return {
        "id": task_id,
        "milestone_id": "M1",
        "after": [],
        "repository": task_id,
        "shared_resources": [],
        "expected_paths": [f"{task_id}/**"],
        "acceptance_criteria": [f"{task_id} acceptance"],
        "verification": [verification],
    }


def _request_key(core: m1.SchedulerCore, attempt_id: str) -> str:
    return core.read(
        lambda ctx: next(
            item.key
            for item in ctx.state.outbox
            if item.attempt_id == attempt_id and item.kind == "verify"
        )
    )


def _order_from_plan(
    core: m1.SchedulerCore, task_id: str, attempt_id: str
) -> m1.VerifyOrder:
    key = _request_key(core, attempt_id)
    spec = core.plan.task(task_id)
    token = core.read(lambda ctx: ctx.state.attempts[attempt_id].token)
    return m1.VerifyOrder(
        key,
        core.plan.plan_id,
        core.plan.revision,
        task_id,
        attempt_id,
        token,
        spec.acceptance_criteria,
        spec.verification,
    )


def _wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


if __name__ == "__main__":
    unittest.main()
