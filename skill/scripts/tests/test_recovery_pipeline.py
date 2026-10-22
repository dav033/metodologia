"""REQ-029 P-152/P-153: the structural recovery cycle from queue to closing proof, replayed with a controlled model.

Real: the exporter and the evidence collector over the run's stores, the diagnosis transport (only the provider CLI is a fake),
the compiler, the grant ledger, the journaled apply, the durable cycle table, the owner's `RecoveryAdapter` tick. Faked: the model's
answer, and the M1 move onto the new plan revision (`apply_plan_revision` and what reads the live M1 identity), as in
`test_recovery_apply`: the scheduler core is exercised by its own tests."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_plan_adapter
import bt_profiles
import bt_planner_runtime as runtime
import bt_recovery_diagnosis as dg
import bt_recovery_evidence as evidence_mod
import bt_recovery_export as export
import bt_recovery_pipeline as pipeline
import bt_run_stores
import bt_scheduler_adapter
import bt_scheduler_decisions
import bt_scheduler_ops
import bt_scheduler_run
from bt_scheduler_recovery_adapter import RecoveryAdapter
from recovery_run_fixture import RecoveryRun
from test_recovery_diagnosis import FakeCli

SHA = "b" * 64
REQUEST = {"id": "T2:1", "task": "T2", "attempt": "att-2", "source": "task", "reason": "m5:rework_limit", "unskippable": False,
           "options": [{"id": "retry"}, {"id": "rework_findings", "target": "T1"}, {"id": "stop"}]}
IDENTITY = {"plan_id": "REQ-029", "revision": 1, "stop_generation": 0, "accepted_map_digest": SHA, "paused": False,
            "cancelled": False, "live_attempts": []}


def proposal(refs, **over):
    body = {"schema_version": "recovery-proposal/1", "confidence": "confirmed", "causal_history": "the page was never rendered",
            "evidence_refs": refs,
            "actions": [{"type": "correct_tasks", "owner_task_id": "T1", "task_ids": ["T1"], "replacements": [{
                "id": "T1", "objective": "Implement page rendering behavior so the changed page renders its content",
                "verification": [{"type": "command", "value": "npm run typecheck", "purpose": "Types", "category": "static"},
                                 {"type": "command", "value": "npm run build", "purpose": "Build", "category": "static"},
                                 {"type": "command", "value": "python3 tests/test_page.py", "purpose": "The page renders its content",
                                  "category": "regression", "created_by": "T1"}]}]}],
            "symptom_oracle": {"symptom": "the page renders its content", "red_command": "python3 tests/test_page.py",
                               "command": "python3 tests/test_page.py"}}
    body.update(over)
    return json.dumps(body).encode()


class Cycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.run = RecoveryRun(root)
        self.rdir = self.run.rdir
        base = self.run.commit("base", {"README": "x"})
        fixed = self.run.commit("t1", {"web/page.tsx": "export const page = 1\n"})
        audit = self.run.commit("audit", {"reviews/audit.findings.json": "{}"})
        self.run.attempt("att-1", "T1", base=base, snapshot=fixed)
        self.run.attempt("att-2", "T2", base=fixed, snapshot=audit, token=2, verdict={
            "status": "NEEDS_REVIEW", "issues": [{"code": "AUDIT_GATE", "message": "audit gate: 2 open blocking findings"}],
            "checks": [{"command": "python3 -m unittest", "status": "fail", "exit_code": 1}]})
        self.run.set_state(
            {"T1": {"state": "completed", "attempts": ["att-1"]}, "T3": {"state": "completed", "attempts": []},
             "T2": {"state": "blocked", "attempts": ["att-2"], "reason": "m5:rework_limit"}},
            {"att-1": {"id": "att-1", "task_id": "T1", "state": "accepted", "token": 1},
             "att-2": {"id": "att-2", "task_id": "T2", "state": "rejected", "token": 2}})
        (self.rdir / "RUN.recovery-policy.json").write_text(json.dumps(
            {"schema_version": "recovery-policy/1", "run_id": "run-1", "identity": {"stop_generation": 0}}))
        audit_doc, attempt_doc = export.export(self.rdir, "T2", "att-2")
        collected = evidence_mod.collect_recovery_evidence(self.rdir, audit_doc, attempt_doc)
        self.assertTrue(collected["diagnosable"], collected["validation_problems"])
        self.refs = [f"m6:{collected['sources']['m6']['sha256']}"]
        self.identity = {**IDENTITY, "source_sha256": self.run.frozen["sha256"]}
        self.home = root / "home"
        agent_file = self.home / ".claude" / "agents" / "planner.md"
        agent_file.parent.mkdir(parents=True)
        agent_file.write_text(runtime.GENERATED_AGENT_MARKER)
        for target, name, value in ((bt_profiles, "get", {"provider": "claude", "bin": "claude", "env": {}}),
                                    (bt_profiles, "require_launchable", "claude"), (bt_profiles, "authorize", None),
                                    (bt_profiles, "session_env", {"PATH": "/usr/bin"}),
                                    (runtime.shutil, "which", "/usr/bin/claude"), (runtime, "_native_agent_path", agent_file),
                                    (bt_scheduler_decisions, "open_requests", [dict(REQUEST)]),
                                    (bt_scheduler_decisions, "evidence", "the audit found two blocking findings in web/page.tsx"),
                                    (bt_scheduler_adapter, "revision_identity", self.identity)):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.adapter = RecoveryAdapter(bt_run_stores.paths(self.rdir)["m5"], scheduler=None, run_id="run-1", describe=lambda _: None,
                                       rdir=self.rdir, recovery_sources=self.sources,
                                       diagnostic_pipeline=pipeline.owner_pipeline(self.rdir))
        self.addCleanup(self.adapter.close)

    def sources(self):
        return {"run_id": "run-1", "audit_lineage": "T2:rework_limit", "source_digests": ["c" * 64], "ordinary_exhausted": True,
                "conflict_observations": [], "observations": [], "owner_only_decision_pending": False,
                "ordinary_remediation_pending": False, "evidence_available": True, "planner_route": dg.route("demo"),
                "diagnosis_target": dg.target(self.rdir, [dict(REQUEST)])}

    def queue(self):
        with patch("bt_scheduler_recovery_adapter.sched.revision_identity", return_value=self.identity):
            return self.adapter.tick_diagnostic_recovery()

    def advance(self, cli, **over):
        return pipeline.advance("demo", "REQ-001", self.rdir, runner=cli.run, probe_runner=cli.probe, home=self.home, **over)

    def state(self):
        rows = self.adapter.recovery_status()["cycles"]
        return rows[0]["state"], json.loads(rows[0]["payload"]) if "payload" in rows[0] else rows[0]

    def row(self):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(bt_run_stores.paths(self.rdir)["m5"])) as conn:
            state, payload = conn.execute("SELECT state, payload_json FROM diagnostic_cycles").fetchone()
        return state, json.loads(payload)

    # ---- the way in: the owner only queues
    def test_the_owner_queues_the_cycle_and_touches_nothing_else(self):
        before = bt_plan_adapter.revisions(self.rdir)
        first = self.queue()
        self.assertEqual((first["state"], first["result"]["phase"]), ("applying", "queued"))
        self.assertEqual(first["result"]["goal"]["named"], ["T1"])
        self.assertEqual(bt_plan_adapter.revisions(self.rdir), before)                    # no revision, no model call, nothing applied
        self.assertTrue(self.queue()["duplicate"])

    # ---- the whole cycle
    def test_a_cycle_goes_from_the_queue_to_the_closing_proof_without_a_person(self):
        self.queue()
        cli = FakeCli(stdout=proposal(self.refs))
        self.assertTrue(self.advance(cli))                                                 # diagnose + compile
        state, payload = self.row()
        self.assertEqual((state, payload["phase"]), ("applying", "compiled"))
        self.assertEqual(len(cli.calls), 1)                                               # one model invocation
        self.assertIn("T1", payload["scope"])
        compiled = json.loads(next((self.rdir / pipeline.DIR).glob("cycle-*/compiled.json")).read_text())
        self.assertTrue(any(t.get("title") == "Run integrated recovery verification" for t in compiled["plan"]["tasks"]))
        with ExitStack() as stack:                                                        # the grant, the journaled apply
            for item in self.apply_patches():
                stack.enter_context(item)
            self.assertTrue(self.advance(cli))
        state, payload = self.row()
        self.assertEqual(state, "executing")
        self.assertEqual(len(cli.calls), 1)
        self.assertEqual(bt_plan_adapter.revisions(self.rdir)[-1]["sha256"], payload["target_sha256"])
        self.run.set_state({"T1": {"state": "ready", "attempts": []}, "T3": {"state": "completed", "attempts": []},
                            "T4": {"state": "pending", "attempts": []}, "T2": {"state": "pending", "attempts": []}}, {},
                           plan_sha256=payload["target_sha256"], revision=2)
        self.assertFalse(self.advance(cli))                                               # nothing to do until the run moves
        self.finish_the_run(payload, verdict="PASS")
        self.assertTrue(self.advance(cli))
        state, payload = self.row()
        self.assertEqual(state, "succeeded")
        self.assertEqual({c["task_id"] for c in payload["corrective_tasks"]}, set(payload["corrective"]))
        self.assertEqual({v["status"] for v in payload["independent_evidence"].values()}, {"verified"})
        import bt_interventions
        self.assertEqual(list(bt_interventions.read(self.rdir))[-1]["result"], "fixed")

    def apply_patches(self):
        @contextmanager
        def no_hold(_rdir, _why):
            yield None

        def approved(rdir):
            latest = bt_plan_adapter.latest_plan(rdir)
            text = bt_plan_adapter.planner_contract.dumps(latest)
            import hashlib
            return bt_scheduler_adapter.core.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                                       plan_id=latest["plan_id"], revision=latest["revision"])

        applied = {"status": "applied", "report": SimpleNamespace(from_revision=1, to_revision=2, kept=("T3",), reset=("T1",),
                                                                   added=(), removed=())}
        return (patch.object(bt_scheduler_adapter, "apply_plan_revision", return_value=applied),
                patch.object(bt_scheduler_adapter, "approved_plan", side_effect=approved),
                patch.object(bt_scheduler_ops, "hold", no_hold), patch.object(bt_scheduler_ops, "stop_owner", return_value=0),
                patch.object(bt_scheduler_run, "rebind_runtime"))

    def finish_the_run(self, payload, verdict):
        """The state the run is in once the ordinary scheduler has run the corrective tasks and the re-audit."""
        fixed = self.run.commit("t1-fixed", {"web/page.tsx": "export const page = 2\n"})
        integrated = self.run.commit("integrated", {"tests/test_page.py": "print(1)\n"})
        final = self.run.commit("audit-2", {"reviews/audit.findings.json": "{\"findings\": []}"})
        prior = self.run.commits["t1"]
        self.run.attempt("att-4", "T1", base=prior, snapshot=fixed)
        self.run.attempt("att-5", "T4", base=fixed, snapshot=integrated)
        self.run.attempt("att-6", "T2", base=integrated, snapshot=final, revision=2, verdict={"status": "PASS", "checks": []})
        self.run.attempt("att-7", "T2b", base=integrated, snapshot=final, revision=2, verdict={"status": verdict, "checks": []})
        done = (("T1", "att-4"), ("T4", "att-5"), ("T2", "att-6"), ("T2b", "att-7"), ("T3", "att-3"))
        tasks = {task: {"state": "completed", "attempts": [att]} for task, att in done}
        attempts = {att: {"id": att, "task_id": task, "state": "accepted", "token": n} for n, (task, att) in enumerate(done, 4)}
        self.run.set_state(tasks, attempts, plan_sha256=payload["target_sha256"], revision=2)

    # ---- the ways it stops, each with its exact code
    def blocked(self, cli=None, **over):
        self.queue()
        self.advance(cli or FakeCli(stdout=proposal(self.refs, **over)))
        state, payload = self.row()
        self.assertEqual(state, "blocked")
        return payload

    def test_a_proposal_the_compiler_refuses_blocks_the_cycle_and_changes_no_plan(self):
        before = bt_plan_adapter.revisions(self.rdir)
        weaker = proposal(self.refs)
        body = json.loads(weaker)
        body["actions"][0]["replacements"][0]["verification"] = body["actions"][0]["replacements"][0]["verification"][2:]   # drops two checks
        payload = self.blocked(FakeCli(stdout=json.dumps(body).encode()))
        self.assertEqual(payload["blocker"], "proposal_rejected")
        self.assertIn("WEAKENED_CHECKS", payload["detail"])
        self.assertEqual(bt_plan_adapter.revisions(self.rdir), before)

    def test_text_only_or_unsure_models_never_become_actions(self):
        for over, code in (({"confidence": "unknown", "actions": []}, "diagnosis_inconclusive"),
                           ({"evidence_refs": ["m6:" + "0" * 64]}, "proposal_rejected"),
                           ({"symptom_oracle": None}, "proposal_rejected")):
            with self.subTest(over=over):
                self.tearDown_cycle()
                self.assertEqual(self.blocked(**over)["blocker"], code)

    def tearDown_cycle(self):
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(bt_run_stores.paths(self.rdir)["m5"], isolation_level=None)) as conn:
            conn.execute("DELETE FROM diagnostic_cycles")
        import shutil
        shutil.rmtree(self.rdir / pipeline.DIR / "RECOVERY.diagnoses", ignore_errors=True)
        for folder in (self.rdir / pipeline.DIR).glob("cycle-*"):
            shutil.rmtree(folder)

    def test_the_prompt_asks_for_what_the_planner_contract_refuses_a_plan_without(self):
        """Found with a real model: a new check without `category` is a refused plan; the prompt now says it is required."""
        self.assertIn("category", dg.PROMPT)
        for name in ("static", "functional", "integration", "regression", "product"):
            self.assertIn(name, dg.PROMPT)


    def test_garbage_from_the_model_is_data_that_fails_not_text_that_is_repaired(self):
        payload = self.blocked(FakeCli(stdout=b"Sure! Here is my plan: ..."))
        self.assertEqual(payload["blocker"], "diagnosis_invalid_json")
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_findings_over_too_many_tasks_are_the_owners_call(self):
        self.queue()
        row_payload = self.row()[1]
        row_payload["goal"]["named"] = [f"T{n}" for n in range(1, 10)]
        import sqlite3
        from contextlib import closing
        with closing(sqlite3.connect(bt_run_stores.paths(self.rdir)["m5"], isolation_level=None)) as conn:
            conn.execute("UPDATE diagnostic_cycles SET payload_json=?", (json.dumps(row_payload),))
        cli = FakeCli(stdout=proposal(self.refs))
        self.advance(cli)
        self.assertEqual(self.row()[1]["blocker"], "findings_too_broad")
        self.assertEqual(cli.calls, [])                                                   # nothing was sent to a model

    def test_no_authorized_route_no_model_call(self):
        self.queue()
        cli = FakeCli(stdout=proposal(self.refs))
        with patch.object(dg, "route", return_value=None):
            self.advance(cli)
        self.assertEqual(self.row()[1]["blocker"], "authorized_planner_route_unavailable")
        self.assertEqual(cli.calls, [])

    def test_the_owners_stop_and_an_operator_hold_win_over_every_step(self):
        self.queue()
        cli = FakeCli(stdout=proposal(self.refs))
        (self.rdir / "RUN.recovery-policy.json").write_text(json.dumps(
            {"schema_version": "recovery-policy/1", "run_id": "run-1", "identity": {"stop_generation": 7}}))   # a stop advanced the fence
        self.assertFalse(self.advance(cli))
        (self.rdir / "RUN.recovery-policy.json").unlink()
        self.assertFalse(self.advance(cli))
        self.assertEqual(cli.calls, [])
        self.assertEqual(self.row()[0], "applying")                                       # still queued, nothing was decided

    def test_a_corrective_task_that_blocks_ends_the_cycle_with_its_name(self):
        self.queue()
        self.advance(FakeCli(stdout=proposal(self.refs)))
        with ExitStack() as stack:
            for item in self.apply_patches():
                stack.enter_context(item)
            self.advance(FakeCli())
        payload = self.row()[1]
        self.run.set_state({"T1": {"state": "blocked", "attempts": ["att-4"], "reason": "m5:attempts_exhausted"}}, {},
                           plan_sha256=payload["target_sha256"], revision=2)
        self.advance(FakeCli())
        self.assertEqual(self.row()[1]["blocker"], "corrective_task_blocked")
        self.assertIn("T1", self.row()[1]["detail"])

    def test_without_a_passing_verdict_on_the_final_tree_there_is_no_success(self):
        self.queue()
        self.advance(FakeCli(stdout=proposal(self.refs)))
        with ExitStack() as stack:
            for item in self.apply_patches():
                stack.enter_context(item)
            self.advance(FakeCli())
        self.finish_the_run(self.row()[1], verdict="FAIL")
        self.advance(FakeCli())
        self.assertEqual(self.row()[1]["blocker"], "independent_resulting_tree_proof_missing")


class Export(unittest.TestCase):
    def test_a_verdict_given_under_another_revision_is_not_evidence_of_this_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = RecoveryRun(Path(tmp))
            base = run.commit("base", {"a": "1"})
            snap = run.commit("s", {"b": "2"})
            run.attempt("att-2", "T2", base=base, snapshot=snap, revision=5, verdict={"status": "FAIL", "checks": []})
            run.set_state({"T2": {"state": "blocked", "attempts": ["att-2"]}},
                          {"att-2": {"id": "att-2", "task_id": "T2", "state": "rejected", "token": 1}})
            with self.assertRaisesRegex(export.ExportError, "plan r5"):
                export.export(run.rdir, "T2", "att-2")

    def test_the_exported_documents_are_the_ones_the_collector_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = RecoveryRun(Path(tmp))
            base = run.commit("base", {"a": "1"})
            snap = run.commit("s", {"web/page.tsx": "2"})
            run.attempt("att-2", "T2", base=base, snapshot=snap, verdict={"status": "FAIL", "checks": []})
            run.set_state({"T2": {"state": "blocked", "attempts": ["att-2"]}},
                          {"att-2": {"id": "att-2", "task_id": "T2", "state": "rejected", "token": 1}})
            audit, attempt = export.export(run.rdir, "T2", "att-2")
            found = evidence_mod.collect_recovery_evidence(run.rdir, audit, attempt)
            self.assertTrue(found["diagnosable"], found["validation_problems"])
            self.assertEqual(found["identity"]["plan_sha256"], run.frozen["sha256"])    # the plan document IS the frozen plan
            with self.assertRaises(export.ExportError):
                export.export(run.rdir, "T2", "att-9")


if __name__ == "__main__":
    unittest.main()
