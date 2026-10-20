from __future__ import annotations

import hashlib
import json
import tempfile
import threading
import time
import unittest
from datetime import UTC, datetime
from pathlib import Path

import bt_audit_gate
import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_executor_adapter as executor_adapter
from bt_scheduler_quality.contracts import QualityError
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from bt_scheduler_quality_adapter import QualityVerificationPort, _retry_is_due
from test_snapshot import _make_snapshot

m1 = scheduler_adapter.core
m3 = executor_adapter.m3


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

    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
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

    def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
        self.calls.append(check.command)
        if check.command in self.failing_commands:
            return CommandOutcome("fail", 5, 2, b"test failure\n", b"", None, True)
        return CommandOutcome("pass", 0, 2, b"test pass\n", b"", None, True)


class M6M1AdapterTests(unittest.TestCase):
    def _system(
        self,
        tasks,
        *,
        runner=None,
        recovery=None,
        max_attempts=1,
        store_path=None,
        schema_version="1.0.0",
        read_ledger=None,
        read_changes=None,
        integration_check=None,
        unresolved_check=None,
        remediate=None,
        rework_notes=None,
        verify_notes=None,
        audit_policy=None,
    ):
        temporary = tempfile.TemporaryDirectory(prefix="m6-m1-")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        plan_value = {
            "schema_version": schema_version,
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
            read_ledger=read_ledger,
            read_changes=read_changes,
            integration_check=integration_check,
            unresolved_check=unresolved_check,
            remediate=remediate,
            rework_notes=rework_notes,
            verify_notes=verify_notes,
            audit_policy=audit_policy,
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

    # ---- audit gate: the ledger decides, and the system sends the named work back -------------------------------
    def _audit_system(self, ledger, notes, *, declare_ledger=True, policy=None, changes=(), remediate=None):
        implement = _task("T1", "python3 build.py")
        implement.update(kind="implement")
        implement["verification"][0]["category"] = "functional"
        audit = _task("T2", "test -s audit.md")
        audit.update(kind="audit", after=["T1"], expected_paths=["docs/audit.md"]
                     + (["docs/audit.findings.json"] if declare_ledger else []))
        audit["verification"][0]["category"] = "functional"
        system = self._system(
            [implement, audit],
            max_attempts=2,
            schema_version="1.2.0",
            read_ledger=ledger,
            read_changes=lambda order: tuple(changes),
            rework_notes=lambda task_id, text: text and notes.append((task_id, text)),
            audit_policy=policy,
            remediate=remediate,
        )
        root, core, _, executor, _, _ = system
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed")
        )
        self._start_attempts(core, executor, root, ("T2",))
        core.step()
        return core

    @staticmethod
    def _ledger(*findings):
        return json.dumps({"schema": "audit-findings/1", "findings": list(findings)}).encode()

    def test_an_audit_with_a_clean_ledger_is_accepted(self):
        notes = []
        core = self._audit_system(lambda order, path: self._ledger(), notes)
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T2"]["state"] == "completed")
        )
        self.assertEqual(notes, [])

    def test_blocking_findings_that_become_remediation_tasks_reject_the_audit_without_reopening_anything(self):
        finding = {"id": "F1", "severity": "high", "status": "open", "summary": "the gateway never listens",
                   "tasks": ["T1"], "evidence": "curl -> refused"}
        asked, notes = [], []

        def remediate(audit, attempt, findings):
            asked.append((audit, [f["id"] for f in findings], findings[0]["evidence"]))
            return True
        core = self._audit_system(lambda order, path: self._ledger(finding), notes, remediate=remediate)
        self.assertTrue(_wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T2"
                                              and e.detail.get("to") == "rejected" for e in core.audit_log())))
        self.assertEqual(asked, [("T2", ["F1"], "curl -> refused")])
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")
        self.assertNotIn("rework_requested", [e.kind for e in core.audit_log()])
        self.assertEqual(notes, [])

    def test_when_remediation_is_not_possible_the_named_tasks_are_sent_back_as_before(self):
        finding = {"id": "F1", "severity": "critical", "status": "open", "summary": "the gateway never listens",
                   "tasks": ["T1"]}
        core = self._audit_system(lambda order, path: self._ledger(finding), [], remediate=lambda *args: False)
        self.assertTrue(_wait_for(lambda: "rework_requested" in [e.kind for e in core.audit_log()]))
        self.assertNotEqual(core.snapshot().tasks["T1"]["state"], "completed")

    def test_an_open_critical_finding_rejects_the_audit_and_the_system_reopens_the_named_task(self):
        notes = []
        finding = {
            "id": "F1", "severity": "critical", "status": "open",
            "summary": "the gateway never listens", "tasks": ["T1"],
        }
        asked = []

        def ledger(order, path):
            asked.append(path)
            return self._ledger(finding)

        core = self._audit_system(ledger, notes)
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T1"]["state"] != "completed")
        )
        states = {t: v["state"] for t, v in core.snapshot().tasks.items()}
        self.assertIn(states["T1"], {"ready", "active"})
        self.assertEqual(states["T2"], "pending")
        self.assertEqual(asked[0], "docs/audit.findings.json")
        self.assertEqual({task for task, _ in notes}, {"T1", "T2"})
        self.assertIn("the gateway never listens", dict(notes)["T1"])
        kinds = [entry.kind for entry in core.audit_log()]
        self.assertIn("rework_requested", kinds)

    def test_an_audit_that_changes_source_is_rejected_and_the_builders_work_is_not_hidden(self):
        core = self._audit_system(lambda order, path: self._ledger(), [],
                                  changes=("docs/audit.md", "docs/audit.findings.json", "remote/gateway/server.py"))
        self.assertTrue(
            _wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T2"
                                  and e.detail.get("to") == "rejected" for e in core.audit_log())))
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")    # nothing is sent back: the audit reruns
        self.assertNotIn("rework_requested", [e.kind for e in core.audit_log()])

    def test_an_audit_that_only_writes_its_declared_files_is_accepted(self):
        core = self._audit_system(lambda order, path: self._ledger(), [],
                                  changes=("docs/audit.md", "docs/audit.findings.json"))
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T2"]["state"] == "completed"))

    def test_read_only_can_be_switched_off_by_configuration(self):
        core = self._audit_system(lambda order, path: self._ledger(), [], changes=("remote/gateway/server.py",),
                                  policy=bt_audit_gate.Policy(read_only=False))
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T2"]["state"] == "completed"))

    def _wide_audit_system(self, policy, finding_tasks, notes):
        """T1 root, T2 depends on it, T3 is a test over it, T4 the audit after all three; a finding names `finding_tasks`."""
        def spec(tid, kind, after, command, **extra):
            task = _task(tid, command)
            task.update(kind=kind, after=after, **extra)
            task["verification"][0]["category"] = "functional"
            return task
        tasks = [spec("T1", "implement", [], "python3 build.py"), spec("T2", "implement", ["T1"], "python3 build.py"),
                 spec("T3", "test", ["T1"], "python3 build.py"),
                 spec("T4", "audit", ["T1", "T2", "T3"], "test -s audit.md",
                      expected_paths=["docs/audit.md", "docs/audit.findings.json"])]
        finding = {"id": "F1", "severity": "high", "status": "open", "summary": "root is wrong", "tasks": finding_tasks}
        system = self._system(tasks, max_attempts=2, schema_version="1.2.0",
                              read_ledger=lambda order, path: self._ledger(finding), read_changes=lambda order: (),
                              rework_notes=lambda task_id, text: text and notes.append(task_id), audit_policy=policy)
        root, core, _, executor, _, _ = system
        for tid in ("T1", "T2", "T3"):
            self._start_attempts(core, executor, root, (tid,))
            core.step()
            self.assertTrue(_wait_for(lambda t=tid: core.snapshot().tasks[t]["state"] == "completed"))
        self._start_attempts(core, executor, root, ("T4",))
        core.step()
        self.assertTrue(_wait_for(lambda: "rework_requested" in [e.kind for e in core.audit_log()]))
        return core

    def test_by_default_a_finding_on_a_root_task_redoes_it_and_the_tests_not_what_depends_on_it(self):
        notes = []
        core = self._wide_audit_system(bt_audit_gate.Policy(), ["T1"], notes)
        states = {t: v["state"] for t, v in core.snapshot().tasks.items()}
        self.assertEqual(states["T2"], "completed")                      # keeps its accepted result
        self.assertNotEqual(states["T1"], "completed")
        self.assertNotEqual(states["T3"], "completed")                    # the test over it proves nothing now
        self.assertEqual(states["T4"], "pending")
        self.assertEqual(set(notes), {"T1", "T3", "T4"})

    def test_downstream_scope_still_redoes_everything_that_depends_on_the_finding(self):
        notes = []
        core = self._wide_audit_system(bt_audit_gate.Policy(rework_scope="downstream"), ["T1"], notes)
        states = {t: v["state"] for t, v in core.snapshot().tasks.items()}
        self.assertEqual([states[t] for t in ("T2", "T3", "T4")], ["pending"] * 3)
        self.assertEqual(set(notes), {"T1", "T2", "T3", "T4"})

    def test_a_result_that_cannot_be_combined_with_accepted_work_is_rejected_with_the_clash_and_a_note(self):
        notes, asked = [], []

        def check(task_id, attempt_id, snapshot):
            asked.append((task_id, len(snapshot)))
            return "T6+T10 vs T13 for T14: remote/gateway/app.py" if len(asked) == 1 else ""
        task = _task("T1", "python3 build.py")
        task.update(kind="implement")
        task["verification"][0]["category"] = "functional"
        root, core, _, executor, _, _ = self._system(
            [task], max_attempts=2, schema_version="1.2.0", integration_check=check,
            rework_notes=lambda task_id, text: text and notes.append((task_id, text)))
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(_wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T1"
                                              and e.detail.get("to") == "rejected" for e in core.audit_log())))
        self.assertEqual(asked[0][0], "T1")
        self.assertEqual([task_id for task_id, _ in notes], ["T1"])
        self.assertIn("T6+T10 vs T13 for T14", notes[0][1])
        self.assertIn("small change", notes[0][1])

    def _give_way_system(self, prior_clashes, notes):
        def spec(tid):
            task = _task(tid, "python3 build.py")
            task.update(kind="implement")
            task["verification"][0]["category"] = "functional"
            return task
        system = self._system([spec("T3"), spec("T1")], max_attempts=2, schema_version="1.2.0",
                              integration_check=lambda *args: "T1+T9 vs T3 for T4: remote/gateway/app.py",
                              rework_notes=lambda task_id, text: text and notes.append((task_id, text)))
        root, core, _, executor, _, adapter = system
        adapter._prior_clashes = lambda task_id: prior_clashes
        adapter.integration_retries = 2
        adapter.integration_check = (lambda task_id, attempt, snapshot:
                                     "T1+T9 vs T3 for T4: remote/gateway/app.py" if task_id == "T1" else "")
        self._start_attempts(core, executor, root, ("T3",))
        core.step()
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T3"]["state"] == "completed"))
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        return core

    def test_a_task_that_keeps_clashing_is_accepted_and_the_accepted_task_it_clashes_with_is_rebuilt(self):
        notes = []
        core = self._give_way_system(2, notes)
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed"))
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T3"]["state"] != "completed"))
        event = [e for e in core.audit_log() if e.kind == "rework_requested"][-1]
        self.assertEqual((event.detail["by"], event.detail["named"], event.detail["cascade"]),
                         ("integration-gate", ["T3"], False))
        self.assertEqual([task_id for task_id, _ in notes], ["T3"])
        self.assertIn("Redo this task on top of it", notes[0][1])

    def test_a_task_with_retries_left_is_rejected_instead_of_sending_the_others_back(self):
        notes = []
        core = self._give_way_system(0, notes)
        self.assertTrue(_wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T1"
                                              and e.detail.get("to") == "rejected" for e in core.audit_log())))
        self.assertEqual(core.snapshot().tasks["T3"]["state"], "completed")
        self.assertEqual([task_id for task_id, _ in notes], ["T1"])

    def test_a_verification_interrupted_by_a_restart_is_rerun_once_and_other_reviews_are_left_alone(self):
        calls = []

        class Store:
            def list_reviews(self):
                return ({"request_key": "interrupted"}, {"request_key": "needs-a-person"}, {"request_key": "again"})

            def retry_interrupted(self, key, operator, reason):
                calls.append((key, operator))
                if key == "needs-a-person":
                    raise QualityError("RETRY_INVALID", "not caused by an interruption")
                if key == "again":
                    raise QualityError("RETRY_EXHAUSTED", "already retried once")
        port = QualityVerificationPort.__new__(QualityVerificationPort)
        port.store = Store()
        self.assertEqual(port._retry_interrupted_reviews(), 1)
        self.assertEqual([key for key, _ in calls], ["interrupted", "needs-a-person", "again"])
        self.assertEqual({operator for _, operator in calls}, {"owner-restart"})

    def test_a_result_that_still_holds_merge_conflict_markers_is_rejected_with_a_note_to_resolve_them(self):
        task = _task("T1", "python3 build.py")
        task.update(kind="implement")
        task["verification"][0]["category"] = "functional"
        notes = []
        root, core, _, executor, _, _ = self._system(
            [task], max_attempts=2, schema_version="1.2.0", unresolved_check=lambda task_id, snapshot: ("a.py", "b.py"),
            rework_notes=lambda task_id, text: text and notes.append((task_id, text)))
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(_wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T1"
                                              and e.detail.get("to") == "rejected" for e in core.audit_log())))
        self.assertEqual([task_id for task_id, _ in notes], ["T1"])
        self.assertIn("a.py, b.py", notes[0][1])
        self.assertIn("delete the markers", notes[0][1])

    def test_a_failed_verification_leaves_the_failing_output_for_the_retry_and_a_pass_clears_it(self):
        class Failing(ScriptedRunner):
            fail = True

            def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
                if not self.fail:
                    return super().run(check, snapshot_root, timeout_seconds=timeout_seconds, mounts=mounts)
                return CommandOutcome("fail", 1, 2, b"", b"npm error code EROFS: read-only file system\n", None, True)

        runner, notes = Failing(), []
        task = _task("T1", "python3 build.py")
        task.update(kind="implement")
        task["verification"][0]["category"] = "functional"
        root, core, _, executor, _, _ = self._system([task], max_attempts=2, runner=runner,
                                                     verify_notes=lambda task_id, text: notes.append((task_id, text)))
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(_wait_for(lambda: bool(notes)))
        task_id, text = notes[0]
        self.assertEqual(task_id, "T1")
        self.assertIn("python3 build.py", text)
        self.assertIn("EROFS: read-only file system", text)
        self.assertIn("node_modules", text)

    def test_an_accepted_task_clears_the_notes_of_earlier_rounds(self):
        task = _task("T1", "python3 build.py")
        task.update(kind="implement")
        task["verification"][0]["category"] = "functional"
        calls = []
        root, core, _, executor, _, _ = self._system([task], max_attempts=2, schema_version="1.2.0",
                                                     rework_notes=lambda task_id, text: calls.append((task_id, text)))
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed"))
        self.assertEqual(calls, [("T1", "")])

    def test_a_result_that_combines_cleanly_is_accepted(self):
        task = _task("T1", "python3 build.py")
        task.update(kind="implement")
        task["verification"][0]["category"] = "functional"
        root, core, _, executor, _, _ = self._system([task], max_attempts=2, schema_version="1.2.0",
                                                     integration_check=lambda *args: "")
        self._start_attempts(core, executor, root, ("T1",))
        core.step()
        self.assertTrue(_wait_for(lambda: core.snapshot().tasks["T1"]["state"] == "completed"))

    def test_an_audit_with_a_missing_ledger_is_rejected_without_reopening_anything(self):
        notes = []
        core = self._audit_system(lambda order, path: None, notes)
        self.assertTrue(
            _wait_for(
                lambda: any(e.kind == "attempt_transition" and e.task_id == "T2"
                            and e.detail.get("to") == "rejected" for e in core.audit_log())
            )
        )
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")
        self.assertNotIn("rework_requested", [e.kind for e in core.audit_log()])
        self.assertEqual(notes, [])

    def test_an_audit_without_a_declared_ledger_is_rejected_by_default(self):
        core = self._audit_system(lambda order, path: self._ledger(), [], declare_ledger=False)
        self.assertTrue(
            _wait_for(lambda: any(e.kind == "attempt_transition" and e.task_id == "T2"
                                  and e.detail.get("to") == "rejected" for e in core.audit_log()))
        )

    def test_the_owner_can_let_an_old_plan_without_a_ledger_through_and_it_is_recorded(self):
        policy = bt_audit_gate.Policy(ledger_required=False)
        core = self._audit_system(lambda order, path: self._ledger(), [], declare_ledger=False, policy=policy)
        self.assertTrue(
            _wait_for(lambda: core.snapshot().tasks["T2"]["state"] == "completed")
        )
        self.assertIn("audit_gate_skipped", [e.kind for e in core.audit_log()])

    def test_an_unreadable_snapshot_leaves_the_verdict_pending_instead_of_judging_the_ledger(self):
        def unavailable(order, path):
            raise RuntimeError("the audited snapshot is unavailable")

        core = self._audit_system(unavailable, [])
        time.sleep(0.3)
        self.assertEqual(core.snapshot().tasks["T2"]["state"], "active")
        self.assertEqual(core.snapshot().tasks["T1"]["state"], "completed")

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
