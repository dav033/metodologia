"""REQ-029 P-152: the structural recovery of an integration CONFLICT, from the clash to the closing proof, with a controlled model.

Two unordered tasks (T1, T5) both own `web/page.tsx`; each result was accepted; the consumer T3 needs both and its merge clashes.
Real: the clash in git, the facts derived from the run's records, the oracle's red step in the verifier sandbox, the convergence
compiler, the grant ledger, the journaled apply, the integrator's merge-in-progress start of the convergence writer, the cycle table.
Faked: the model's answer and the M1 move onto the new revision (as in `test_recovery_pipeline`)."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_interventions
import bt_plan_adapter
import bt_profiles
import bt_planner_runtime as runtime
import bt_recovery_diagnosis as dg
import bt_recovery_lineage as lineage
import bt_recovery_pipeline as pipeline
import bt_run_stores
import bt_scheduler_adapter
import bt_scheduler_decisions
import bt_scheduler_integrator as integ
from bt_scheduler_recovery_adapter import RecoveryAdapter
from recovery_run_fixture import RecoveryRun, conflict_plan
from test_recovery_diagnosis import FakeCli
import test_recovery_pipeline as audit_tests
from test_recovery_pipeline import IDENTITY

PAGE = "".join(f"line{n}\n" for n in range(1, 21))
TEST = ("import sys\ntext = open('web/page.tsx').read()\n"
        "sys.exit(0 if 'LEFT' in text and 'RIGHT' in text and '<<<<<<<' not in text else 1)\n")
REQUEST = {"id": "T3:0", "task": "T3", "attempt": "", "source": "task", "reason": "m5:attempts_exhausted", "unskippable": False,
           "error": "start rejected: INTEGRATION_CONFLICT: T1 vs T5 for T3: web/page.tsx",
           "options": [{"id": "retry"}, {"id": "stop"}], "diagnosis": {"kind": "conflict"}}


def answer(refs, **over):
    body = {"schema_version": "recovery-proposal/1", "confidence": "confirmed", "causal_history": "both tasks rewrote the first line",
            "semantic_conflict": False, "incompatible_requirements": [], "evidence_refs": refs,
            "symptom_oracle": {"symptom": "the page shows both behaviors", "path": "web/page.tsx",
                               "red_command": "python3 tests/test_page.py", "command": "python3 tests/test_page.py"}}
    body.update(over)
    return json.dumps(body).encode()


@unittest.skipUnless(shutil.which("bwrap"), "the oracle's red step runs in the verifier sandbox")
class Conflict(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.run = RecoveryRun(root, plan=conflict_plan())
        self.rdir = self.run.rdir
        base = self.run.commit("base", {"web/page.tsx": PAGE, "tests/test_page.py": TEST})
        left = self.run.commit("t1", {"web/page.tsx": "LEFT\n" + PAGE.split("\n", 1)[1]})
        self.run.git("checkout", "-q", "-b", "other", base)
        right = self.run.commit("t5", {"web/page.tsx": "RIGHT\n" + PAGE.split("\n", 1)[1]})
        self.run.git("checkout", "-q", "-")
        self.base, self.left, self.right = base, left, right
        verdict = {"status": "PASS", "checks": []}
        self.run.attempt("att-1", "T1", base=base, snapshot=left, verdict=verdict)
        self.run.attempt("att-5", "T5", base=base, snapshot=right, verdict=verdict)
        self.state(tasks_extra={"T3": {"state": "blocked", "attempts": [], "reason": "m5:attempts_exhausted"},
                                "T2": {"state": "pending", "attempts": []}})
        bt_interventions.record_conflict(self.rdir, task="T3", left="T1", right="T5", files=["web/page.tsx"], run="demo")
        (self.rdir / "RUN.recovery-policy.json").write_text(json.dumps(
            {"schema_version": "recovery-policy/1", "run_id": "run-1", "identity": {"stop_generation": 0}}))
        self.identity = {**IDENTITY, "plan_id": self.run.plan["plan_id"], "source_sha256": self.run.frozen["sha256"]}
        self.home = root / "home"
        agent_file = self.home / ".claude" / "agents" / "planner.md"
        agent_file.parent.mkdir(parents=True)
        agent_file.write_text(runtime.GENERATED_AGENT_MARKER)
        for target, name, value in ((bt_profiles, "get", {"provider": "claude", "bin": "claude", "env": {}}),
                                    (bt_profiles, "require_launchable", "claude"), (bt_profiles, "authorize", None),
                                    (bt_profiles, "session_env", {"PATH": "/usr/bin"}),
                                    (runtime, "_native_agent_path", agent_file),
                                    (bt_scheduler_decisions, "open_requests", [dict(REQUEST)]),
                                    (bt_scheduler_decisions, "evidence", "T3 cannot start: T1 and T5 changed web/page.tsx"),
                                    (bt_scheduler_adapter, "revision_identity", self.identity)):
            patcher = patch.object(target, name, return_value=value)
            patcher.start()
            self.addCleanup(patcher.stop)
        real_which = shutil.which
        patcher = patch.object(runtime.shutil, "which", side_effect=lambda name, *a, **k: "/usr/bin/claude" if name == "claude"
                               else real_which(name, *a, **k))                  # the sandbox still finds its own bwrap
        patcher.start()
        self.addCleanup(patcher.stop)
        import bt_recovery_oracle
        patcher = patch.object(bt_recovery_oracle, "policy_for", return_value=__import__("bt_scheduler_quality.policy",
                               fromlist=["QualityPolicy"]).QualityPolicy())
        patcher.start()
        self.addCleanup(patcher.stop)
        self.adapter = RecoveryAdapter(bt_run_stores.paths(self.rdir)["m5"], scheduler=None, run_id="run-1", describe=lambda _: None,
                                       rdir=self.rdir, recovery_sources=self.sources,
                                       diagnostic_pipeline=pipeline.owner_pipeline(self.rdir))
        self.addCleanup(self.adapter.close)
        self.refs = self.refs_of_clash()

    def state(self, tasks_extra=None, plan_sha=None, revision=1, done=None):
        tasks = {"T1": {"state": "completed", "attempts": ["att-1"]}, "T5": {"state": "completed", "attempts": ["att-5"]}}
        attempts = {"att-1": {"id": "att-1", "task_id": "T1", "state": "accepted", "token": 1},
                    "att-5": {"id": "att-5", "task_id": "T5", "state": "accepted", "token": 2}}
        tasks.update(tasks_extra or {})
        for name, attempt in (done or {}).items():
            tasks[name] = {"state": "completed", "attempts": [attempt]}
            attempts[attempt] = {"id": attempt, "task_id": name, "state": "accepted", "token": 9}
        self.run.set_state(tasks, attempts, plan_sha256=plan_sha, revision=revision)

    def refs_of_clash(self):
        import bt_recovery_evidence as evidence_mod
        import bt_recovery_export as export
        audit, attempt = export.export(self.rdir, "T1", "att-1", accepted=True)
        found = evidence_mod.collect_recovery_evidence(self.rdir, audit, attempt, states=("accepted",))
        self.assertTrue(found["diagnosable"], found["validation_problems"])
        return [f"m6:{found['sources']['m6']['sha256']}"]

    def sources(self):
        return {"run_id": "run-1", "conflict_lineage": "T3:T1:T5", "source_digests": ["c" * 64], "ordinary_exhausted": True,
                "conflict_observations": [], "observations": [], "owner_only_decision_pending": False,
                "ordinary_remediation_pending": False, "evidence_available": True, "planner_route": dg.route("demo"),
                "diagnosis_target": dg.target(self.rdir, [dict(REQUEST)])}

    def queue(self):
        with patch("bt_scheduler_recovery_adapter.sched.revision_identity", return_value=self.identity):
            return self.adapter.tick_diagnostic_recovery()

    def advance(self, cli):
        return pipeline.advance("demo", "REQ-001", self.rdir, runner=cli.run, probe_runner=cli.probe, home=self.home)

    def row(self):
        return audit_tests.Cycle.row(self)

    # ---- the facts
    def test_the_target_names_both_sides_and_every_path_of_the_clash(self):
        goal = dg.target(self.rdir, [dict(REQUEST)])
        self.assertEqual((goal["kind"], goal["left"], goal["right"], goal["files"]), ("conflict", "T1", "T5", ["web/page.tsx"]))

    def test_facts_are_derived_from_the_records_and_not_from_the_model(self):
        facts = lineage.gather(self.rdir, "demo", lineage.latest_conflict(self.rdir, "T3"))
        self.assertEqual((facts["left"], facts["right"], facts["consumers"]), ("T1", "T5", ["T3"]))
        self.assertEqual([s["snapshot_sha"] for s in facts["sides"]], [self.left, self.right])
        self.assertEqual(facts["sides"][0]["delta"], ["web/page.tsx"])
        self.assertEqual(facts["owners"]["T1"]["paths"], ["web"])

    def test_a_clash_that_is_not_shared_ownership_is_not_this_repairs_to_make(self):
        row = lineage.latest_conflict(self.rdir, "T3")
        with patch.object(bt_scheduler_decisions, "_state", return_value={**bt_scheduler_decisions._state(self.rdir),
                                                                          "tasks": {"T1": {"state": "completed", "attempts": ["att-1"]}}}):
            with self.assertRaises(dg.Blocked) as stale:
                lineage.gather(self.rdir, "demo", row)
        self.assertEqual(stale.exception.code, "lineage_stale")                               # T5 is not accepted any more
        with self.assertRaises(dg.Blocked) as escape:
            lineage.gather(self.rdir, "demo", {**row, "files": ["server/api.py"]})
        self.assertEqual(escape.exception.code, "scope_escape")                               # the sides do not own that path
        with self.assertRaises(dg.Blocked) as many:
            lineage.gather(self.rdir, "demo", {**row, "left": "T1+T5"})
        self.assertEqual(many.exception.code, "conflict_sides_not_two_tasks")

    # ---- the whole cycle
    def compiled(self, cli=None):
        self.queue()
        cli = cli or FakeCli(stdout=answer(self.refs))
        self.assertTrue(self.advance(cli))
        return cli

    def test_a_cycle_goes_from_the_clash_to_the_closing_proof(self):
        cli = self.compiled()
        state, payload = self.row()
        self.assertEqual((state, payload["phase"]), ("applying", "compiled"))
        compiled = json.loads(next((self.rdir / pipeline.DIR).glob("cycle-*/compiled.json")).read_text())
        rows = {t["id"]: t for t in compiled["plan"]["tasks"]}
        writer = rows["T6"]
        self.assertEqual(writer["recovery_owner_tasks"], ["T1", "T5"])
        self.assertEqual(writer["bootstrap"]["parents"], [self.left, self.right])
        self.assertIn("conflict markers", writer["objective"])
        self.assertTrue(any("awk" in c["value"] for c in writer["verification"]))             # a marker-free result is a check
        self.assertIn("T6", rows["T3"]["after"])                                               # it waits for the writer instead
        self.assertNotIn("T1", rows["T3"]["after"])                                            # the consumer no longer waits for the two sides
        self.assertNotIn("T5", rows["T3"]["after"])
        # the writer starts from the merge in progress of both accepted sides
        core_plan = self.core_plan(compiled["plan"])
        integrator = integ.PredecessorIntegrator()
        integrator.bind(plan=core_plan, accepted=lambda: {"T1": "att-1", "T5": "att-5"},
                        snapshot_of=lambda a: {"att-1": self.left, "att-5": self.right}.get(a),
                        repo_of=lambda role: self.run.repo, default_repository="repo", identity="r2-abc-1",
                        start_base_of=lambda attempt: self.base)
        start = integrator.base_ref("T6")
        merged = self.run.git("show", f"{start}:web/page.tsx")
        self.assertIn("<<<<<<<", merged)
        self.assertEqual(integrator.unresolved("T6", start), ("web/page.tsx",))
        with ExitStack() as stack:
            for item in audit_tests.Cycle.apply_patches(self):
                stack.enter_context(item)
            self.assertTrue(self.advance(cli))
        state, payload = self.row()
        self.assertEqual(state, "executing")
        self.assertIn("T6", payload["corrective"])
        self.finish(payload)
        self.assertTrue(self.advance(cli))
        state, payload = self.row()
        self.assertEqual(state, "succeeded", payload)
        self.assertEqual({v["status"] for v in payload["independent_evidence"].values()}, {"verified"})
        self.assertEqual(len(cli.calls), 1)                                                   # one model invocation for the whole cycle

    def core_plan(self, plan):
        import hashlib
        text = bt_plan_adapter.planner_contract.dumps(plan)
        return bt_scheduler_adapter.core.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                                  plan_id=plan["plan_id"], revision=plan["revision"])

    def finish(self, payload, last="PASS"):
        fixed = self.run.commit("converged", {"web/page.tsx": "LEFT\nRIGHT\n" + PAGE.split("\n", 2)[2]})
        final = self.run.commit("audit-2", {"reviews/audit.findings.json": "{\"findings\": []}"})
        verdict = {"status": "PASS", "checks": []}
        self.run.attempt("att-6", "T6", base=self.left, snapshot=fixed)
        self.run.attempt("att-7", "T7", base=fixed, snapshot=fixed)
        self.run.attempt("att-8", "T2", base=fixed, snapshot=final, revision=2, verdict=verdict)
        self.run.attempt("att-9", "T2b", base=fixed, snapshot=final, revision=2, verdict={"status": last, "checks": []})
        done = {"T6": "att-6", "T7": "att-7", "T3": "att-3", "T2": "att-8", "T2b": "att-9"}
        self.state(plan_sha=payload["target_sha256"], revision=2, done=done)

    # ---- the ways it stops
    def blocked(self, stdout):
        self.queue()
        self.advance(FakeCli(stdout=stdout))
        state, payload = self.row()
        self.assertEqual(state, "blocked")
        return payload

    def test_incompatible_requirements_are_the_owners_ruling_never_a_converged_guess(self):
        payload = self.blocked(answer(self.refs, semantic_conflict=True, incompatible_requirements=["T1 wants LEFT only"]))
        self.assertEqual(payload["blocker"], "incompatible_requirements")
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_an_oracle_that_does_not_fail_on_either_side_proves_nothing_and_stops_the_cycle(self):
        silly = answer(self.refs, symptom_oracle={"symptom": "always fine", "path": "web/page.tsx",
                                                  "red_command": "python3 --version", "command": "python3 --version"})
        self.assertEqual(self.blocked(silly)["blocker"], "oracle_not_red")
        self.assertEqual(len(bt_plan_adapter.revisions(self.rdir)), 1)

    def test_an_oracle_outside_the_clashing_files_or_an_unsafe_command_is_refused(self):
        elsewhere = answer(self.refs, symptom_oracle={"symptom": "x", "path": "web/other.tsx", "red_command": "python3 tests/test_page.py",
                                                     "command": "python3 tests/test_page.py"})
        self.assertEqual(self.blocked(elsewhere)["blocker"], "proposal_invalid")
        self.tearDown_cycle()
        shell = answer(self.refs, symptom_oracle={"symptom": "x", "path": "web/page.tsx", "red_command": "python3 -c 'import sys; sys.exit(1)'",
                                                  "command": "python3 tests/test_page.py"})
        self.assertIn(self.blocked(shell)["blocker"], ("oracle_unusable", "proposal_rejected", "oracle_not_red"))

    def tearDown_cycle(self):
        audit_tests.Cycle.tearDown_cycle(self)

    def test_the_converged_result_needs_a_passing_final_verdict(self):
        self.compiled()
        with ExitStack() as stack:
            for item in audit_tests.Cycle.apply_patches(self):
                stack.enter_context(item)
            self.advance(FakeCli())
        payload = self.row()[1]
        self.finish(payload, last="FAIL")
        self.advance(FakeCli())
        self.assertEqual(self.row()[1]["blocker"], "independent_resulting_tree_proof_missing")


if __name__ == "__main__":
    unittest.main()
