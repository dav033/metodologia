"""Planner → M1 → M2 → M3 → M4 → M5 → M6 rejection and recovery proof."""
from __future__ import annotations

import json
import stat
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bt_scheduler_adapter as scheduler_adapter
import bt_scheduler_executor_wiring as composition
import bt_scheduler_m4_wiring as m4_runtime
import bt_scheduler_run as runtime
import scheduler_chain_support as chain
import scheduler_executor_support as support
from bt_scheduler_monitor.contracts import Incident
from bt_scheduler_monitor.queries import events as query_events
from scheduler_executor_support import adapter, core


class SnapshotAgent:
    """A local M3 child that leaves a failing first snapshot and fixes it on retry."""

    def __init__(self):
        self.workspaces: list[Path] = []

    def prepare(self, route, prompt, workspace, timeout_seconds):
        self.workspaces.append(Path(workspace.path))
        command = (
            "import json,pathlib; "
            "partial=pathlib.Path('partial-progress.txt'); resumed=partial.exists(); "
            "partial.write_text('preserved partial work\\n'); "
            "pathlib.Path('result.txt').write_text('PASS\\n' if resumed else 'FAIL\\n'); "
            "print(json.dumps({'type':'result','subtype':'success','result':'TERMINAL-EVENT',"
            "'usage':{'output_tokens':3}}))"
        )
        return adapter.m3.Launch(argv=(sys.executable, "-c", command))

    def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False):
        if timed_out:
            return adapter.m3.Classification("timeout")
        terminal = "TERMINAL-EVENT" in raw
        status = "completed" if returncode == 0 and terminal else "failed"
        return adapter.m3.Classification(status, terminal_event=terminal, text=raw[-200:])


class RecordingM2Port(chain.M2Port):
    def __init__(self, ledger_path, route_table):
        super().__init__(ledger_path, route_table)
        self.history = []

    def propose(self, request):
        result = super().propose(request)
        self.history.extend(self.decisions.values())
        return result

    def close(self):
        pass


class PlannerThroughM6(support.World):
    criterion = "result.txt contains PASS"

    def _approved_plan(self):
        repository = self.repos["app"]
        (repository / "verify_result.py").write_text(
            "from pathlib import Path\n"
            "if Path('result.txt').read_text(encoding='utf-8').strip() != 'PASS':\n"
            "    raise SystemExit(1)\n",
            encoding="utf-8",
        )
        support.git(repository, "add", "verify_result.py")
        support.git(repository, "commit", "-q", "-m", "Add snapshot verification command")

        tasks = [{"id": "T1", "title": "Complete the checked output", "repo": "app", "after": []}]
        pipeline = chain.Pipeline(self, "chainproj", "REQ-061", tasks, ["README.md"])
        (pipeline.rdir / "SPEC.md").write_text(
            "# Local M6 integration proof\n\n## Requirements\n"
            "- R1. Deliver the task through planner, scheduler, M5 retry and the M6 verifier.\n", encoding="utf-8")
        plan_markdown = chain.plan_md("REQ-061", tasks).replace(
            'python3 -c "raise SystemExit(0)"', "python3 verify_result.py"
        )
        (pipeline.rdir / "PLAN.md").write_text(plan_markdown, encoding="utf-8")
        pipeline.step("init")
        chain.classify(pipeline.rdir, tasks, ["README.md"])
        plan_path = pipeline.rdir / "PLAN.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        task = plan["tasks"][0]
        task["acceptance_criteria"] = [self.criterion]
        task["verification"] = [{
            "type": "command",
            "value": "python3 verify_result.py",
            "purpose": self.criterion,
            "category": "functional",
        }]
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        with patch.object(chain.bt_core, "ROOT", self.root):  # resolve the project's repositories for file: evidence
            pipeline.step("check")
            pipeline.step("freeze")
        self.rdir = pipeline.rdir
        return chain.bt_plan_adapter.run_state_fields(self.rdir)

    def test_planner_to_m6_rejection_m5_retry_and_m6_acceptance(self):
        frozen = self._approved_plan()
        original_head = support.git(self.repos["app"], "rev-parse", "HEAD")
        original_status = support.git(self.repos["app"], "status", "--porcelain")
        legacy = self.tmp / "untouched-RUN.json"
        legacy.write_bytes(b'{"schema":0,"opaque":"preserve"}\n')
        driver = SnapshotAgent()
        assignments = []
        captured = {}
        delivery_reports = []
        original_wire = runtime._wire
        original_composition_wire = composition.wire
        original_drain = m4_runtime.drain_pending_streams
        original_deliver = m4_runtime.deliver_incidents

        def make_assignment(project, ledger_path, *, laya_root):
            port = RecordingM2Port(
                ledger_path,
                lambda _task: [("claude", "sonnet", "claude-personal", "low")],
            )
            assignments.append(port)
            return port

        def capture_wire(project, rdir):
            wiring, assignment, runtime_id = original_wire(project, rdir)
            captured.update(wiring=wiring, assignment=assignment, runtime_id=runtime_id)
            return wiring, assignment, runtime_id

        def wire_with_retry_budget(*args, **kwargs):
            kwargs["config"] = core.Config(max_parallel_tasks=1, max_attempts=3)
            return original_composition_wire(*args, **kwargs)

        def drain_and_seed_incident(wiring, m1_run_id):
            drained = original_drain(wiring, m1_run_id)
            if not captured.get("incident_seeded"):
                attempts = wiring.scheduler.read(lambda ctx: tuple(ctx.state.attempts.values()))
                if attempts:
                    attempt = attempts[0]
                    description = wiring.executor.describe(attempt.id)
                    if description:
                        observed_at = datetime.now(UTC).isoformat()
                        incident = Incident(
                            "1.0.0", "sha256:" + "b" * 64, m1_run_id, attempt.task_id, attempt.id,
                            description["stream"]["execution_id"], "missed_heartbeat", "missed_heartbeat",
                            "medium", "high", observed_at, observed_at, 1, (), (), "open",
                        )
                        wiring.monitor.store.enqueue_incident(incident, "sha256:" + "c" * 64)
                        captured["incident_seeded"] = True
            return drained

        def deliver_incidents(wiring, claim_token, *, now):
            report = original_deliver(wiring, claim_token, now=now)
            delivery_reports.append(report)
            return report

        def inspect_terminal_runtime(_project, _req):
            wiring = captured.get("wiring")
            if wiring is None or captured.get("evidence") is not None:
                return
            snapshot = wiring.scheduler.snapshot()
            captured["terminal_status"] = snapshot.status
            captured["terminal_tasks"] = snapshot.tasks
            captured["terminal_audit"] = [entry.kind for entry in wiring.scheduler.audit_log()[-12:]]
            if snapshot.status != "completed":
                return
            attempt_records = wiring.scheduler.read(
                lambda ctx: [ctx.state.attempts[attempt_id] for attempt_id in ctx.state.tasks["T1"].attempts]
            )
            attempt_ids = wiring.executor.ledger.all_ids()
            results = [
                wiring.verification_store.get_result(
                    f"{frozen['plan_ref']['plan_id']}:r1:{record.id}:verify"
                )
                for record in attempt_records
            ]
            rows = sorted(
                (wiring.executor.ledger.get(attempt_id) for attempt_id in attempt_ids),
                key=lambda row: row["request"]["token"],
            )
            captured["evidence"] = {
                "snapshot": snapshot,
                "attempt_records": attempt_records,
                "attempt_ids": attempt_ids,
                "drained": bool(attempt_ids) and all(
                    wiring.stream_adapter.is_terminal_drained(attempt_id) for attempt_id in attempt_ids
                ),
                "results": results,
                "rows": rows,
                "m5_latest": wiring.recovery.latest(),
                "m1_incidents": [entry for entry in wiring.scheduler.audit_log()
                                 if entry.kind == "incident_observed"],
                "m4_gaps": wiring.monitor.store.list_stream_gaps(),
                "m4_path": wiring.monitor.store_path,
                "m5_path": wiring.recovery.path,
                "m6_path": wiring.verification_store.path,
            }

        with patch.object(runtime.bt_core, "ROOT", self.root), \
                patch("bt_workspace.repos", return_value=self.repos), \
                patch.object(scheduler_adapter, "DecisionAssignmentPort", side_effect=make_assignment), \
                patch.object(composition, "wire", side_effect=wire_with_retry_budget), \
                patch.object(composition.api, "MethodologyDriver", return_value=driver), \
                patch.object(runtime, "_wire", side_effect=capture_wire), \
                patch.object(runtime, "_install_autostart"), \
                patch.object(runtime, "_remove_autostart", side_effect=inspect_terminal_runtime), \
                patch.object(runtime.bt_notify, "notify"), \
                patch.object(m4_runtime, "drain_pending_streams", side_effect=drain_and_seed_incident), \
                patch.object(m4_runtime, "deliver_incidents", side_effect=deliver_incidents):
            self.assertEqual(runtime.run("chainproj", "REQ-061", self.rdir, resume=False, no_autostart=True), 0)

        self.assertIn("evidence", captured,
                      f"runtime ended at {captured.get('terminal_status')}: "
                      f"tasks={captured.get('terminal_tasks')}, audit={captured.get('terminal_audit')}, "
                      f"M4 reports={delivery_reports}")
        evidence = captured["evidence"]
        final = evidence["snapshot"]
        attempt_records = evidence["attempt_records"]
        self.assertTrue(captured["incident_seeded"])
        self.assertTrue(delivery_reports)
        self.assertTrue(any(report.applied == 1 for report in delivery_reports))
        self.assertEqual(final.status, "completed", final)
        self.assertEqual(final.plan_sha256, frozen["plan_ref"]["sha256"])
        self.assertEqual([record.state for record in attempt_records], ["rejected", "accepted"])
        self.assertTrue(all(record.verifier == "m6-quality/checker-v1" for record in attempt_records))
        self.assertTrue(attempt_records[0].evidence.startswith("m6://result/"))
        self.assertTrue(attempt_records[1].evidence.startswith("m6://result/"))

        self.assertTrue(evidence["drained"])
        rows = evidence["rows"]
        self.assertEqual(len(rows), 2)
        first, second = rows
        self.assertEqual(first["handoff"]["status"], "captured")
        self.assertEqual(second["request"]["base_ref"], first["handoff"]["snapshot_sha"])
        self.assertNotEqual(first["workspace"]["path"], second["workspace"]["path"])
        self.assertEqual((Path(second["workspace"]["path"]) / "partial-progress.txt").read_text(),
                         "preserved partial work\n")
        self.assertEqual((Path(second["workspace"]["path"]) / "result.txt").read_text(), "PASS\n")

        results = evidence["results"]
        self.assertEqual([result["status"] for result in results], ["FAIL", "PASS"])
        self.assertTrue(all(result["evidence_manifest"].startswith("m6://result/") for result in results))
        self.assertEqual(evidence["m5_latest"]["action"], "retry")
        self.assertEqual(len(assignments[0].history), 2)
        self.assertEqual(len({record.decision_id for record in assignments[0].history}), 2)
        self.assertNotEqual(first["route"]["reference"], second["route"]["reference"])
        self.assertEqual(len(evidence["m1_incidents"]), 1)
        m4_events = query_events(evidence["m4_path"])["items"]
        self.assertEqual(len(m4_events), 2, f"M4 did not normalize both M3 outputs: {m4_events}")
        self.assertTrue(all(event["event_type"] == "usage_reported" for event in m4_events), m4_events)
        self.assertFalse(evidence["m4_gaps"], f"M4 reported unexpected stream loss: {evidence['m4_gaps']}")
        module_paths = [evidence["m4_path"], evidence["m5_path"], evidence["m6_path"]]
        self.assertEqual(len({path.resolve() for path in module_paths}), 3)
        self.assertEqual(stat.S_IMODE(module_paths[0].parent.stat().st_mode), stat.S_IRWXU)
        self.assertTrue(all(stat.S_IMODE(path.stat().st_mode) == stat.S_IRUSR | stat.S_IWUSR
                            for path in module_paths))
        self.assertEqual(support.git(self.repos["app"], "rev-parse", "HEAD"), original_head)
        self.assertEqual(support.git(self.repos["app"], "status", "--porcelain"), original_status)
        self.assertEqual(legacy.read_bytes(), b'{"schema":0,"opaque":"preserve"}\n')


class CompositionGuards(support.World):
    def setUp(self):
        super().setUp()
        self.rdir = self.tmp / "composition-guards"
        self.rdir.mkdir()
        self.approve([support.task("T1", "guard M6 composition")])

    def test_quality_store_aliases_are_rejected_before_m1_or_m6_creation(self):
        m1_path = adapter.sched.run_db_path(self.rdir)
        monitor_path = self.tmp / "monitor.sqlite3"
        recovery_path = self.tmp / "recovery.sqlite3"
        cases = (
            (m1_path, None, None),
            (monitor_path, monitor_path, None),
            (recovery_path, None, recovery_path),
        )
        for quality_path, monitor_store_path, recovery_store_path in cases:
            with self.subTest(path=quality_path):
                with self.assertRaisesRegex(ValueError, "must be separate"):
                    composition.wire(
                        self.rdir,
                        project="proj",
                        quality_store_path=quality_path,
                        monitor_store_path=monitor_store_path,
                        recovery_store_path=recovery_store_path,
                    )
                self.assertFalse(m1_path.exists())
                self.assertFalse(quality_path.exists())

    def test_custom_verifier_and_invalid_policy_fail_before_runtime_state_creation(self):
        with self.assertRaisesRegex(ValueError, "supply verification or quality_store_path"):
            composition.wire(
                self.rdir,
                project="proj",
                verification=object(),
                quality_store_path=self.tmp / "private" / "quality.sqlite3",
            )
        invalid_store = self.tmp / "private" / "invalid.sqlite3"
        with self.assertRaises(TypeError):
            composition.wire(
                self.rdir,
                project="proj",
                quality_store_path=invalid_store,
                quality_policy={"unknown_policy_field": True},
            )
        self.assertFalse(adapter.sched.run_db_path(self.rdir).exists())
        self.assertFalse(invalid_store.exists())

    def test_store_construction_failure_releases_executor_for_a_clean_retry(self):
        public_dir = self.tmp / "public-store-directory"
        public_dir.mkdir(mode=stat.S_IRWXU)
        public_dir.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        with self.assertRaisesRegex(ValueError, "private"):
            composition.wire(
                self.rdir,
                project="proj",
                autostart=False,
                quality_store_path=public_dir / "invalid.sqlite3",
            )

        private_dir = self.tmp / "retry-store-directory"
        private_dir.mkdir(mode=stat.S_IRWXU)
        wiring = composition.wire(
            self.rdir,
            project="proj",
            autostart=False,
            quality_store_path=private_dir / "quality.sqlite3",
        )
        self.wirings.append(wiring)
        self.assertIsNotNone(wiring.verification_runtime)
        self.assertEqual(stat.S_IMODE(private_dir.stat().st_mode), stat.S_IRWXU)

    def test_real_m6_handoff_replays_held_m1_review_after_wiring_restart_and_runs_resume(self):
        from bt_scheduler_quality_owner_adapter import handoff_needs_review

        quality_path = self.tmp / "quality.sqlite3"
        recovery_path = self.tmp / "recovery.sqlite3"

        def wire():
            result = composition.wire(
                self.rdir, project="proj", assignment=adapter.PinnedRoute("direct:claude/haiku"),
                repos=self.repos, default_repository="app", quality_store_path=quality_path,
                recovery_store_path=recovery_path, autostart=False,
            )
            self.wirings.append(result)
            return result

        wiring = wire()
        wiring.scheduler.claim(core.Assignment("T1", "worker"))
        attempt_id = wiring.scheduler.snapshot().tasks["T1"]["attempt"]
        wiring.scheduler.ingest(core.Event("finished-review", wiring.scheduler.plan.plan_id,
                                            wiring.scheduler.plan.revision, "T1", attempt_id, "worker",
                                            "execution_finished"))
        wiring.scheduler.step()
        identity = {"plan_id": wiring.scheduler.plan.plan_id, "revision": wiring.scheduler.plan.revision,
                    "task_id": "T1", "attempt_id": attempt_id, "token": 1}
        result = {"status": "NEEDS_REVIEW", "evidence_manifest": "m6://result/" + "d" * 64}
        wiring.recovery.needs_review_advice = lambda _case: (_ for _ in ()).throw(RuntimeError("M5 offline"))
        with self.assertRaisesRegex(RuntimeError, "M5 offline"):
            wiring.verification_runtime.needs_review_handoff(identity, result)
        self.assertEqual(wiring.scheduler.read(lambda ctx: ctx.state.review_holds[attempt_id]["state"]), "held")

        wiring.close()
        restarted = wire()
        self.assertEqual(restarted.scheduler.read(lambda ctx: ctx.state.review_holds[attempt_id]["state"]), "waiting")
        restarted.recovery.needs_review_advice = lambda _case: "resume"
        retried = []
        restarted.verification_runtime.store.retry_m5_transient = retried.append

        handoff_needs_review(restarted.verification_runtime, "request-key", identity, result)

        self.assertEqual(retried, ["request-key"])
        self.assertEqual(restarted.scheduler.read(lambda ctx: ctx.state.review_holds[attempt_id]["state"]), "resumed")


class ShutdownOrder(unittest.TestCase):
    def test_m6_and_m5_close_before_stream_and_m3(self):
        events = []

        class Runtime:
            def close(self, *, wait):
                events.append(("m6-runtime", wait))

        class Resource:
            def __init__(self, name):
                self.name = name

            def close(self):
                events.append(self.name)

        class Stream:
            def close_all(self):
                events.append("stream")

        class Executor:
            def close(self):
                events.append("m3")

        wiring = adapter.Wiring(None, Executor(), None, None, Stream())
        wiring.verification_runtime = Runtime()
        wiring.verification_store = Resource("m6-store")
        wiring.recovery = Resource("m5")
        wiring.close()
        self.assertEqual(events, [
            ("m6-runtime", True), "m6-store", "m5", "stream", "m3",
        ])


if __name__ == "__main__":
    unittest.main()
