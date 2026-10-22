"""REQ-030 step 5: self-healing. A closed taxonomy, the smallest safe repair of each class, bounded, idempotent, recorded and
reversible."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_healing_classify as taxonomy
import bt_interventions
import bt_scheduler_healing as healing
from test_remediation import plan as make_plan, task as make_task

NOW = 1_000_000.0


def request(**over):
    base = {"id": "T7:3", "task": "T7", "attempt": "att-9", "source": "task", "reason": "m5:attempts_exhausted", "error": "",
            "evidence": [], "diagnosis": {}, "options": [{"id": "retry"}, {"id": "retry_with_note"}, {"id": "stop"}]}
    base.update(over)
    return base


def classify(req=None, **kw):
    return taxonomy.classify(req or request(), **kw)


def core_plan(*specs):
    return SimpleNamespace(tasks=tuple(specs), task=lambda tid: next(s for s in specs if s.id == tid))


def spec(tid, paths=(), kind="implement"):
    return SimpleNamespace(id=tid, expected_paths=tuple(paths), meta={"kind": kind}, after=())


class Taxonomy(unittest.TestCase):
    def test_the_last_real_error_beats_a_quota_word_somewhere_else(self):
        noisy = "usage limit and 429 appear in an old log line\n" * 2
        got = classify(request(error=noisy), failures=["att-1 failed: quota exceeded", "start rejected: ROUTE_INVALID: the decision was replaced by 2e7a"],
                       verify=noisy)
        self.assertEqual(got.kind, "transient")                                    # REQ-029: it said "quota"
        self.assertEqual(classify(request(), failures=["agent stopped: you've hit your limit, resets 3pm"]).kind, "quota")
        self.assertIsNone(classify(request(), failures=["boom 429 items processed"]))   # a bare number is nothing

    def test_every_class_is_placed_from_its_evidence(self):
        cases = {
            "integration_defect": request(error="INTEGRATION_CONFLICT: T12 vs T13 for T14: a.ts"),
            "criterion_unmapped": request(source="review", evidence=["CRITERION_UNVERIFIABLE: no check maps to this criterion"]),
            "plan_defect": request(error="CHECK_UNSUPPORTED: pipes are not allowed"),
            "environment": request(error="EROFS: read-only file system, mkdir node_modules"),
        }
        for kind, req in cases.items():
            self.assertEqual(classify(req).kind, kind, kind)
        self.assertIn(classify(cases["environment"]).kind, taxonomy.CLASSES)
        self.assertIsNone(classify(request(error="something nobody has seen before")))     # unplaced: no guess

    def test_a_failing_test_of_another_accepted_task_is_a_regression_naming_its_owner(self):
        plan = core_plan(spec("T4", ["skill/scripts/tests/test_scheduler_run_controls.py", "skill/scripts/bt_run.py"]),
                         spec("T7", ["report.md"], kind="test"))
        doc = {"tasks": {"T4": {"state": "completed"}, "T7": {"state": "blocked"}}}
        verify = "FAIL: test_apply_control (test_scheduler_run_controls.Controls.test_apply_control)\nPLAN_MISMATCH"
        got = classify(request(), verify=verify, failures=[verify], plan=plan, doc=doc)
        self.assertEqual((got.kind, got.owners), ("regression", ("T4",)))
        self.assertIn("test_scheduler_run_controls", got.failing)
        # failing tests that nobody else owns, in a task that only executes and records: a defect of the plan
        alone = classify(request(), verify="FAIL: test_x (test_unowned.Case.test_x)", plan=plan, doc=doc)
        self.assertEqual(alone.kind, "plan_defect")

    def test_the_signature_ignores_volatile_parts_and_keeps_the_kind(self):
        a = taxonomy.signature("T7", "transient", "ROUTE_INVALID att-0104 decision 2e7a754a87e5 at /tmp/x/1234")
        b = taxonomy.signature("T7", "transient", "ROUTE_INVALID att-0138 decision 91bc55aa09f1 at /var/y/99")
        self.assertEqual(a, b)
        self.assertNotEqual(a, taxonomy.signature("T7", "environment", "ROUTE_INVALID"))
        self.assertNotEqual(a, taxonomy.signature("T8", "transient", "ROUTE_INVALID"))


class Cycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.answers, self.revisions, self.notes = [], [], []
        self.doc = {"tasks": {"T7": {"state": "blocked", "attempts": ["att-9"]}},
                    "attempts": {"att-9": {"updated_at": NOW - 3600, "state": "rejected"}}}
        self.verify = "start rejected: ROUTE_INVALID: the decision was replaced by 2e7a754a"

    def run_cycle(self, requests, **over):
        patches = (patch("bt_scheduler_decisions._state", return_value=self.doc), patch("bt_scheduler_decisions._plan", return_value=None),
                   patch("bt_scheduler_decisions._context", return_value={"verify": self.verify, "failures": [self.verify],
                                                                          "repeats": 0, "closed": "", "refused": {}}))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        return healing.cycle("p", "REQ-001", self.rdir, requests=requests, now=lambda: NOW,
                             answer=lambda *args: self.answers.append(args) or ["ok"],
                             revise=lambda why: self.revisions.append(why) or ["rebased"],
                             notify=lambda title, text: self.notes.append(text), **over)

    def test_a_transient_stop_is_retried_once_per_signature_budget_and_recorded(self):
        self.assertEqual(self.run_cycle([request()]), 1)
        self.assertEqual([a[:2] for a in self.answers], [("T7:3", "retry")])
        row = list(bt_interventions.read(self.rdir))[0]
        self.assertEqual((row["class"], row["source"], row["result"], row["task"]), ("transient", "auto", "fixed", "T7"))
        self.assertGreater(row["minutes_lost"], 50)                                          # an hour of waiting is on the record
        self.assertEqual(healing.status(self.rdir)["cases"][row["case"]]["status"], "applied")

    def test_the_same_failure_after_its_repair_is_bounded_never_repeated_forever(self):
        for _ in range(4):
            self.run_cycle([request()])
        self.assertEqual(len(self.answers), 2)                                               # transient: two repairs, then it gives up
        self.assertEqual(len(self.notes), 1)                                                 # and tells the owner once
        self.assertIn("T7", self.notes[0])
        entry = next(iter(healing.load(self.rdir)["cases"].values()))
        self.assertEqual(entry["status"], "exhausted")

    def test_a_fresh_quota_stop_waits_and_a_stopped_or_disabled_run_does_nothing(self):
        self.verify = "agent stopped: you've hit your limit"
        self.doc["attempts"]["att-9"]["updated_at"] = NOW - 10                               # just happened: wait for the reset
        self.assertEqual(self.run_cycle([request()]), 0)
        self.doc["attempts"]["att-9"]["updated_at"] = NOW - 3600
        (self.rdir / healing.OFF).write_text("off")
        self.assertEqual(self.run_cycle([request()]), 0)                                     # `heal stop` wins
        healing.start(self.rdir)
        self.assertEqual(self.run_cycle([request()]), 1)

    def test_the_run_wide_budget_and_the_per_cycle_cap_are_hard(self):
        many = [request(id=f"T{n}:1", task=f"T{n}", attempt=f"a{n}") for n in range(1, 6)]
        for n in range(1, 6):
            self.doc["tasks"][f"T{n}"] = {"state": "blocked", "attempts": [f"a{n}"]}
            self.doc["attempts"][f"a{n}"] = {"updated_at": NOW - 3600}
        self.assertEqual(self.run_cycle(many), healing.PER_CYCLE)
        with patch.object(healing, "limits", return_value={"per_task": 2, "actions": 3}):
            self.assertEqual(self.run_cycle(many), 1)                                        # only one action left in the budget
            self.assertEqual(self.run_cycle(many), 0)

    def test_an_audit_that_would_send_back_accepted_tasks_gets_one_more_remediation_round_once(self):
        import bt_remediation
        self.verify = "audit gate: 11 open blocking finding(s): F3 (high), F4 (high)"
        card = request(task="T8", id="T8:3", reason="rework_impact", error=self.verify)
        self.doc["tasks"]["T8"] = {"state": "blocked", "attempts": ["att-9"]}
        self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(self.answers[0][:2], ("T8:3", "retry"))
        self.assertEqual(bt_remediation.extra_rounds(self.rdir, "T8"), 1)
        self.assertFalse(bt_remediation.grant_round(self.rdir, "T8"))                         # one extra round per audit, no more
        self.assertEqual(self.run_cycle([card]), 0)                                          # it came back: the owner decides now

    def test_a_full_verifier_workspace_gets_a_bigger_one_but_a_full_disk_is_left_alone(self):
        import bt_config
        self.verify = "next build: ENOSPC: no space left on device, write"
        card = request(diagnosis={"kind": "environment"})
        changed = {}
        with patch.object(bt_config, "set_value", lambda key, value: changed.__setitem__(key, value)), \
                patch.object(bt_config, "get", lambda key, default=None: 2048 if key == "verifier.max_workspace_mb" else default), \
                patch("shutil.disk_usage", return_value=SimpleNamespace(free=50 << 30)):
            self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(changed, {"verifier.max_workspace_mb": 4096})
        self.assertEqual(self.answers[-1][1], "retry")
        again = request(id="T9:1", task="T9", attempt="a9", diagnosis={"kind": "environment"})
        self.doc["tasks"]["T9"] = {"state": "blocked", "attempts": ["a9"]}
        self.doc["attempts"]["a9"] = {"updated_at": NOW - 3600}
        with patch("shutil.disk_usage", return_value=SimpleNamespace(free=1 << 30)):         # the host itself is full
            self.assertEqual(self.run_cycle([again]), 0)

    def test_nothing_is_repaired_while_an_operator_move_holds_the_run(self):
        import bt_scheduler_ops as ops
        ops.hold_path(self.rdir).parent.mkdir(parents=True, exist_ok=True)
        with patch.object(ops, "on_hold", return_value=True):
            self.assertEqual(self.run_cycle([request()]), 0)
        self.assertEqual(self.answers, [])

    def test_an_unplaced_stop_is_left_alone(self):
        self.verify = "an error the taxonomy has never seen"
        self.assertEqual(self.run_cycle([request()]), 0)
        self.assertEqual(self.answers, [])

    def test_a_clash_the_diagnosis_knows_is_answered_like_the_owner_would(self):
        self.verify = "INTEGRATION_CONFLICT: T12 vs T13 for T7: a.ts"
        card = request(options=[{"id": "rework_conflict"}, {"id": "retry"}],
                       diagnosis={"kind": "conflict", "option": "rework_conflict", "confidence": "alta", "headline": "clash"})
        self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(self.answers[0][1], "rework_conflict")

    def test_an_environment_stop_with_a_known_note_retries_with_the_note_and_evidence(self):
        self.verify = "EROFS: read-only file system, mkdir node_modules"
        card = request(diagnosis={"kind": "environment", "note": "Do not install dependencies in tests."})
        self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(self.answers[0][1], "retry_with_note")
        self.assertIn("Do not install dependencies", self.answers[0][2])
        self.assertIn("EROFS", self.answers[0][2])                                           # the evidence is cited in the note

    def test_a_review_where_every_criterion_passed_but_an_extra_check_is_unmapped_is_accepted_with_the_reason(self):
        self.verify = "CHECK_UNMAPPED: a check does not map exactly to an acceptance criterion"
        card = request(source="review", id="key-1", options=[{"id": "review_fail"}, {"id": "review_pass"}, {"id": "stop"}],
                       evidence=["CHECK_UNMAPPED: a check does not map", "criterio PASS: it renders", "npm test → pass"])
        self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(self.answers[0][:2], ("key-1", "review_pass"))
        self.assertIn("all 1 criteria PASS", self.answers[0][2])


    def test_one_criterion_and_only_passing_checks_none_of_them_mapped_is_accepted_by_elimination(self):
        self.verify = "CRITERION_UNVERIFIABLE: No verification check maps exactly to this acceptance criterion."
        evidence = ["CRITERION_UNVERIFIABLE: No verification check maps exactly", "CHECK_UNMAPPED: A verification check does not map",
                    "criterio UNKNOWN: Both boundary tests pass and nothing is weakened",
                    "cd skill/scripts && python3 -m unittest discover -s tests -p test_a.py → pass",
                    "cd skill/scripts && python3 -m unittest discover -s tests -p test_b.py → pass"]
        options = [{"id": "review_fail"}, {"id": "review_pass"}, {"id": "stop"}]
        card = request(source="review", id="key-9", options=options, evidence=evidence)
        self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual(self.answers[0][:2], ("key-9", "review_pass"))
        self.assertIn("by elimination", self.answers[0][2])
        # a failing or undetermined check, or a second criterion, is never accepted this way
        for bad in (evidence[:4] + ["x → fail"], evidence[:4] + ["x → unknown (CHECK_TIMEOUT)"], evidence + ["criterio UNKNOWN: another"]):
            self.answers.clear()
            self.rdir = Path(tempfile.mkdtemp(dir=self.tmp.name))
            self.run_cycle([request(source="review", id="key-9", options=options, evidence=bad)])
            self.assertNotIn("review_pass", [a[1] for a in self.answers], bad[-1])


class PlanRepairs(unittest.TestCase):
    def plan(self):
        return make_plan(make_task("T1", paths=["src/a.py"], command="pytest tests/test_a.py"),
                         make_task("T2", ["T1"], paths=["src/b.py"], command="pytest tests/test_b.py"),
                         make_task("T3", ["T2"], kind="test", category="regression", paths=["docs/report.md"],
                                   command="pytest tests/test_a.py tests/test_b.py"))

    def case(self, owners=("T1",)):
        return taxonomy.Case("T3:1", "T3", "regression", ("failing tests of T1",), owners=owners, failing=("test_a",), signature="sig")

    def test_a_repair_task_is_inserted_before_the_task_that_can_only_execute_and_record(self):
        revised, new_id, restored = healing.build_fix_revision(self.plan(), "T3", self.case(), {"verify": "FAIL: test_a boom"})
        self.assertEqual((new_id, restored, revised["revision"]), ("T3.1", ["T2"], 2))
        by_id = {t["id"]: t for t in revised["tasks"]}
        self.assertEqual(by_id["T3"]["after"], ["T2", "T3.1"])                               # the blocked task waits for the repair
        fix = by_id["T3.1"]
        self.assertEqual((fix["after"], fix["kind"]), (["T2"], "implement"))                 # built on the integrated tree
        self.assertIn("FAIL: test_a boom", fix["objective"])                                  # the real evidence reaches the builder
        self.assertIn("do not edit or delete the failing tests", fix["objective"])
        commands = {v["value"] for v in fix["verification"]}
        self.assertTrue({"pytest tests/test_a.py", "pytest tests/test_a.py tests/test_b.py"} <= commands)   # owner's AND blocked task's own
        from bt_plan_adapter import plan_errors
        self.assertEqual(plan_errors(revised), [])
        self.assertEqual(self.plan()["revision"], 1)                                           # the input is untouched

    def test_nothing_is_built_for_a_task_the_plan_does_not_have(self):
        self.assertIsNone(healing.build_fix_revision(self.plan(), "T99", self.case(), {}))

    def test_a_check_spelled_differently_from_its_criterion_gets_the_criterion_text(self):
        base = make_task("T1", paths=["a.py"], command="pytest")
        base["acceptance_criteria"] = ["The login page returns 200 for a valid user", "Logout clears the session"]
        base["verification"] = [{**base["verification"][0], "purpose": "the login page returns 200 for a valid user."},
                                {**base["verification"][0], "value": "pytest tests/test_logout.py", "purpose": "Logout clears the session"}]
        revised = healing.remap_purposes(make_plan(base), "T1")
        self.assertEqual([v["purpose"] for v in revised["tasks"][0]["verification"]],
                         ["The login page returns 200 for a valid user", "Logout clears the session"])
        self.assertEqual(revised["revision"], 2)
        base["verification"][0]["purpose"] = "something entirely different about billing"
        self.assertIsNone(healing.remap_purposes(make_plan(base), "T1"))                      # no confident pairing: no guess

    def test_a_repair_can_be_reverted_to_the_previous_prerequisites(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp)
            plan = self.plan()
            revised, new_id, restored = healing.build_fix_revision(plan, "T3", self.case(), {"verify": "x"})
            healing.save(rdir, {"actions": 1, "cases": {"sig": {"id": "sig", "task": "T3", "class": "regression", "status": "applied",
                                                                  "task_added": new_id, "after_restored": restored, "target": "T3",
                                                                  "applied": 1}}})
            frozen = []
            with patch("bt_plan_adapter.latest_plan", return_value=revised), \
                    patch("bt_plan_adapter.freeze_revision", side_effect=lambda r, p, s: frozen.append(p) or p):
                lines = healing.revert("p", "REQ-001", rdir, "sig", revise=lambda why: ["rebased"])
                self.assertIn("T3.1 removed", lines[0])
                back = frozen[0]
                self.assertEqual((back["revision"], [t["id"] for t in back["tasks"]]), (3, ["T1", "T2", "T3"]))
                self.assertEqual({t["id"]: t["after"] for t in back["tasks"]}["T3"], ["T2"])
                self.assertEqual(healing.load(rdir)["cases"]["sig"]["status"], "reverted")
                self.assertEqual(healing.revert("p", "REQ-001", rdir, "sig", revise=lambda why: [])[0], "case sig was already reverted")
                with self.assertRaises(ValueError):
                    healing.revert("p", "REQ-001", rdir, "nope", revise=lambda why: [])
            self.assertEqual(list(bt_interventions.read(rdir))[-1]["source"], "manual")


if __name__ == "__main__":
    unittest.main()
