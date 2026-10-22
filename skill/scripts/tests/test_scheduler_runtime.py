from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_scheduler_adapter as adapter
import bt_scheduler_run as runtime


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.rdir = self.root / "REQ-042-demo"
        self.rdir.mkdir()
        self.scheduler = SimpleNamespace(plan=SimpleNamespace(
            plan_id="REQ-042", revision=1, sha256="a" * 64, tasks=[]))
        self.scheduler.snapshot = lambda: SimpleNamespace(
            status="blocked", plan_id="REQ-042", revision=1, plan_sha256="a" * 64,
            tasks={}, attention=[])
        self.scheduler.read = lambda fn: fn(SimpleNamespace(
            config=SimpleNamespace(max_attempts=3), state=SimpleNamespace(tasks={})))
        self.scheduler._stalled = lambda snapshot: True
        self.scheduler.step = lambda: SimpleNamespace(progress=False)
        self.scheduler.audit_log = list
        self.wiring = SimpleNamespace(
            scheduler=self.scheduler,
            executor=SimpleNamespace(ledger=SimpleNamespace(
                all_ids=list, ids_in_states=lambda _states: [], count=lambda _states: 0)),
            stream_candidates=runtime.m4_runtime.M3StreamCandidates(),
            monitor=SimpleNamespace(deliver_incidents=lambda *_args, **_kwargs:
                                    SimpleNamespace(status="complete", pending=0),
                                    pending_incident_count=lambda: 0),
            recovery=object(), verification_runtime=object(), close=lambda: None,
        )

    def test_resume_refuses_when_scheduler_authority_is_missing(self):
        with patch.object(runtime, "_wire", side_effect=AssertionError("must not wire")), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=True, no_autostart=True)
        self.assertEqual(error.exception.code, "SCHEDULER_RUN_MISSING")

    def test_requirements_gate_runs_before_scheduler_wiring(self):
        with patch("bt_requirements_gate.require_ready", side_effect=SystemExit("requirements changed")), \
                patch.object(runtime, "_wire", side_effect=AssertionError("must not wire")), \
                self.assertRaisesRegex(SystemExit, "requirements changed"):
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=False, no_autostart=True)

    def test_fresh_run_refuses_legacy_authority_before_wiring(self):
        (self.rdir / adapter.RUN_JSON).write_text("{}", encoding="utf-8")
        with patch.object(runtime, "_wire", side_effect=AssertionError("must not wire")), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=False, no_autostart=True)
        self.assertEqual(error.exception.code, "AUTHORITY_CONFLICT")

    def test_resume_refuses_conflicting_legacy_state_even_when_scheduler_database_exists(self):
        (self.rdir / adapter.RUN_JSON).write_text("{}", encoding="utf-8")
        adapter.run_db_path(self.rdir).parent.mkdir(parents=True, exist_ok=True)
        adapter.run_db_path(self.rdir).touch()
        with patch.object(runtime, "_wire", side_effect=AssertionError("must not wire")), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=True, no_autostart=True)
        self.assertEqual(error.exception.code, "AUTHORITY_CONFLICT")

    def test_owner_lock_refuses_a_second_startup_owner(self):
        with adapter.owner_lock(self.rdir):
            scheduler_owner = adapter.owner_lock(self.rdir)
            with self.assertRaises(adapter.core.SchedulerError) as scheduler_error:
                scheduler_owner.__enter__()
        self.assertEqual(scheduler_error.exception.code, "OWNER_ACTIVE")

    def test_owner_loop_writes_heartbeat_and_deduplicates_terminal_notification(self):
        notifications = []
        def wire(*args):
            adapter.run_db_path(self.rdir).parent.mkdir(parents=True, exist_ok=True)
            adapter.run_db_path(self.rdir).touch()
            return self.wiring, SimpleNamespace(close=lambda: None), "a" * 32
        with patch.object(runtime, "_wire", side_effect=wire), \
                patch.object(runtime, "_install_autostart"), \
                patch.object(runtime, "_remove_autostart"), \
                patch.object(runtime, "_notification_generation", return_value=4), \
                patch.object(runtime.bt_notify, "notify", side_effect=lambda *args: notifications.append(args)), \
                patch.object(runtime, "_remove_autostart"), \
                patch.object(runtime.time, "sleep", return_value=None):
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=False, no_autostart=True, max_steps=1)
            runtime.run("demo", "REQ-042-demo", self.rdir, resume=True, no_autostart=True, max_steps=1)
        projection = json.loads((self.rdir / adapter.PROJECTION).read_text(encoding="utf-8"))
        self.assertEqual(projection["authority"], "scheduler")
        self.assertIn("heartbeat_at", projection)
        self.assertEqual(list(self.rdir.glob(".RUN.projection.*.tmp")), [])
        self.assertEqual(len(notifications), 1)

    def test_terminal_owner_drains_more_than_one_m4_outbox_batch_before_exit(self):
        notifications = []
        self.scheduler.next_deadline = lambda: 0.05
        with patch.object(runtime, "_wire", return_value=(self.wiring, SimpleNamespace(close=lambda: None), "a" * 32)), \
                patch.object(runtime, "_install_autostart"), \
                patch.object(runtime, "_remove_autostart"), \
                patch.object(runtime.bt_notify, "notify", side_effect=lambda *args: notifications.append(args)), \
                patch.object(self.wiring.monitor, "pending_incident_count", side_effect=[1, 0]) as pending, \
                patch.object(runtime.time, "sleep", return_value=None):
            self.assertEqual(runtime.run("demo", "REQ-042-demo", self.rdir, resume=False, no_autostart=True), 0)

        self.assertEqual(pending.call_count, 2)
        self.assertEqual(len(notifications), 1)

    def test_notifications_are_claimed_before_delivery_and_repeat_on_a_new_transition(self):
        notifications = []
        delivered_generations = []
        state = adapter.run_db_path(self.rdir).with_name(adapter.run_db_path(self.rdir).stem + "-notifications.json")

        def notify(*args):
            delivered_generations.append(json.loads(state.read_text(encoding="utf-8"))["generation"])
            notifications.append(args)

        with patch.object(runtime.bt_notify, "notify", side_effect=notify):
            runtime._notify_terminal(self.rdir, "REQ-042", "blocked", "a" * 32, 4)
            runtime._notify_terminal(self.rdir, "REQ-042", "blocked", "a" * 32, 4)
            runtime._notify_terminal(self.rdir, "REQ-042", "blocked", "a" * 32, 8)
        self.assertEqual(len(notifications), 2)
        self.assertEqual(delivered_generations, [4, 8])
        self.assertEqual(json.loads(state.read_text(encoding="utf-8"))["generation"], 8)

    def test_notification_state_failure_skips_delivery_without_raising(self):
        with patch.object(runtime.os, "replace", side_effect=OSError("read-only")), \
                patch.object(runtime.bt_notify, "notify") as notify, \
                patch.object(runtime.sys, "stderr"):
            runtime._notify_terminal(self.rdir, "REQ-042", "blocked", "a" * 32, 4)
        notify.assert_not_called()

    def test_notification_generation_ignores_clean_process_resume_but_tracks_operator_transition(self):
        scheduler = SimpleNamespace(audit_log=lambda: [
            SimpleNamespace(seq=3, kind="task_blocked"),
            SimpleNamespace(seq=4, kind="run_resumed_by_process"),
        ])
        self.assertEqual(runtime._notification_generation(scheduler), 3)
        scheduler.audit_log = lambda: [
            SimpleNamespace(seq=3, kind="task_blocked"),
            SimpleNamespace(seq=4, kind="run_resumed_by_process"),
            SimpleNamespace(seq=5, kind="run_resumed"),
        ]
        self.assertEqual(runtime._notification_generation(scheduler), 5)

    def test_scheduler_autostart_command_is_mode_specific(self):
        import bt_notify
        from bt_notify import install_autostart
        with patch.object(bt_notify.host, "platform", return_value="linux"), \
                patch.object(bt_notify.bt_autostart, "install") as install:   # the objects bt_notify holds, whatever an
            install_autostart("demo", "REQ-042", scheduler=True)              # earlier test did to the platform or imports
        self.assertIs(install.call_args.kwargs["scheduler"], True)

    def test_composition_requires_distinct_private_m4_m5_m6_stores(self):
        import bt_scheduler_executor_wiring as composition
        import bt_workspace

        assignment = SimpleNamespace(close=lambda: None)
        plan = SimpleNamespace(plan_id="REQ-042", revision=1, sha256="a" * 64)
        with patch.object(adapter, "approved_plan", return_value=plan), \
                patch.object(runtime, "_runtime_binding", return_value="a" * 32), \
                patch.object(adapter, "DecisionAssignmentPort", return_value=assignment) as make_m2, \
                patch.object(bt_workspace, "repos", return_value={}), \
                patch.object(composition, "wire", return_value=self.wiring) as wire, \
                patch.object(runtime, "_secure_store_file") as secure:
            result = runtime._wire("demo", self.rdir)
        self.assertEqual(result, (self.wiring, assignment, "a" * 32))
        self.assertIn("a" * 32, str(make_m2.call_args.args[1]))
        self.assertIs(wire.call_args.kwargs["assignment"], assignment)
        self.assertTrue(wire.call_args.kwargs["autostart"])
        stores = [wire.call_args.kwargs[name] for name in
                  ("monitor_store_path", "recovery_store_path", "quality_store_path")]
        self.assertEqual(len(set(stores)), 3)
        self.assertEqual([path.name for path in stores], [
            "m4-monitor.sqlite3", "m5-recovery.sqlite3", "m6-quality.sqlite3",
        ])
        self.assertEqual(stat.S_IMODE(stores[0].parent.stat().st_mode), 0o700)
        self.assertEqual([call.args[0] for call in secure.call_args_list], stores)

    def test_insecure_required_module_directory_fails_before_composition(self):
        import bt_scheduler_executor_wiring as composition

        identity = "b" * 32
        db_path = adapter.run_db_path(self.rdir)
        module_root = db_path.parent / f"{db_path.stem}-{identity}-modules"
        module_root.mkdir(mode=0o755, parents=True)
        with patch.object(runtime, "_runtime_binding", return_value=identity), \
                patch.object(adapter, "DecisionAssignmentPort") as make_m2, \
                patch.object(composition, "wire") as wire, \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime._wire("demo", self.rdir)

        self.assertEqual(error.exception.code, "MODULE_STORE_UNAVAILABLE")
        make_m2.assert_not_called()
        wire.assert_not_called()

    def test_runtime_binding_reuses_only_the_same_frozen_plan_namespace(self):
        plan = SimpleNamespace(plan_id="REQ-042", revision=1, sha256="a" * 64)
        with patch.object(adapter, "approved_plan", return_value=plan):
            identity = runtime._runtime_binding(self.rdir, resume=False)
            resumed = runtime._runtime_binding(self.rdir, resume=True)
        self.assertEqual(resumed, identity)
        plan.revision = 2
        with patch.object(adapter, "approved_plan", return_value=plan), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime._runtime_binding(self.rdir, resume=True)
        self.assertEqual(error.exception.code, "PLAN_MISMATCH")

    def test_rebind_keeps_the_runtime_identity_and_follows_the_new_revision(self):
        plan = SimpleNamespace(plan_id="REQ-042", revision=1, sha256="a" * 64)
        with patch.object(adapter, "approved_plan", return_value=plan):
            identity = runtime._runtime_binding(self.rdir, resume=False)
        newer = SimpleNamespace(plan_id="REQ-042", revision=2, sha256="b" * 64)
        with patch.object(adapter, "approved_plan", return_value=newer):
            runtime.rebind_runtime(self.rdir)
            self.assertEqual(runtime._runtime_binding(self.rdir, resume=True), identity)
        with patch.object(adapter, "approved_plan", return_value=plan), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime._runtime_binding(self.rdir, resume=True)
        self.assertEqual(error.exception.code, "PLAN_MISMATCH")

    def test_the_executor_timeout_comes_from_the_configuration_with_a_sane_fallback(self):
        import bt_config

        with patch.object(bt_config, "get", return_value=90):
            self.assertEqual(runtime._executor_config().timeout_seconds, 5400.0)
        for bad in (0, -5, True, "x", None):
            with patch.object(bt_config, "get", return_value=bad):
                self.assertEqual(runtime._executor_config().timeout_seconds, 7200.0)
        self.assertEqual(bt_config.get("scheduler.attempt_timeout_minutes"), 120)

    def test_rebind_without_a_binding_is_refused(self):
        newer = SimpleNamespace(plan_id="REQ-042", revision=2, sha256="b" * 64)
        with patch.object(adapter, "approved_plan", return_value=newer), \
                self.assertRaises(runtime.RuntimeErrorCode) as error:
            runtime.rebind_runtime(self.rdir)
        self.assertEqual(error.exception.code, "RUNTIME_BINDING_MISSING")



class RunLimits(unittest.TestCase):
    def test_parallelism_and_exclusive_scopes_reach_the_core_and_the_executor_ceiling(self):
        import bt_config
        import bt_scheduler_run as run
        with patch.object(bt_config, "load", return_value={"scheduler": {"max_parallel_tasks": 3, "max_attempts": 3,
                                                                           "attempt_timeout_minutes": 120,
                                                                           "exclusive_scopes": ["large_change"]},
                                                          "gates": {"max_reworks": 4}}):
            core_config, m3_config = run._run_config(), run._executor_config()
        self.assertEqual((core_config.max_parallel_tasks, core_config.exclusive_scopes), (3, ("large_change",)))
        self.assertEqual(core_config.max_reworks, 4)
        self.assertEqual((m3_config.max_running, m3_config.timeout_seconds), (3, 7200.0))


if __name__ == "__main__":
    unittest.main()
