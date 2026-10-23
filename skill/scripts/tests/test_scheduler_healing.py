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

    def test_a_failing_command_names_the_file_it_runs_so_the_owner_of_that_file_is_found(self):
        """REQ-020 T14a: the project's e2e runner prints `[FAIL] asesor M1: ...`, no test-runner format. The command that failed
        (`exit code 1`) names the script; the manual checks that never ran (`exit code None`) name nothing."""
        verify = ("$ Coordinator runs `npx tsx scripts/e2e/asesor/run.ts --live` with .env.local\nexit code None\n\n"
                  "$ ASESOR_TEST_DATABASE_URL=postgresql://rag@127.0.0.1:5432/rag npx tsx --conditions=react-server "
                  "scripts/e2e/asesor/run.ts --start --fake-model --milestone M1\nexit code 1\n"
                  "[FAIL] asesor M1: Expected values to be strictly equal: 'error' !== 'final'\n")
        plan = core_plan(spec("T7", ["scripts/e2e/asesor/run.ts", "docs/m1.md"]), spec("T14a", ["docs/req-020/results.json"], kind="test"))
        doc = {"tasks": {"T7": {"state": "completed"}, "T14a": {"state": "blocked"}}}
        got = classify(request(task="T14a", reason="m5:attempts_exhausted"), verify=verify, failures=[verify], plan=plan, doc=doc)
        self.assertEqual((got.kind, got.owners, got.failing), ("regression", ("T7",), ("scripts/e2e/asesor/run.ts",)))
        manual_only = "$ Coordinator runs `npx tsx scripts/e2e/asesor/run.ts --live`\nexit code None\n"
        self.assertEqual(taxonomy.failing_tests(manual_only), ())

    def test_a_command_that_ran_and_failed_outranks_the_verifiers_doubt_about_the_mapping(self):
        """REQ-020 T14a after the coordinator: the open review carries CRITERION_MANUAL / CHECK_UNMAPPED AND the live command's failure
        in the note. The mapping branch used to win and the real failure was never repaired."""
        card = request(task="T14a", source="review", evidence=["CRITERION_MANUAL: only manual evidence", "CHECK_UNMAPPED: no criterion"])
        verify = ("The coordinator ran the live check and it FAILED, so nothing was attested:\n\n$ npx tsx --conditions=react-server "
                  "scripts/e2e/asesor/run.ts --start --live --milestone M2\nexit code 1\n[FAIL] asesor M2: correction did not regenerate the summary\n")
        plan = core_plan(spec("T7", ["scripts/e2e/asesor/run.ts"]), spec("T14a", ["docs/req-020/results.json"], kind="test"))
        doc = {"tasks": {"T7": {"state": "completed"}, "T14a": {"state": "blocked"}}}
        got = classify(card, verify=verify, plan=plan, doc=doc)
        self.assertEqual((got.kind, got.owners), ("regression", ("T7",)))
        self.assertEqual(classify(card, verify="$ Coordinator runs `x`\nexit code None\n").kind, "criterion_unmapped")   # never ran: still the mapping

    def test_the_signature_ignores_volatile_parts_and_keeps_the_kind(self):
        a = taxonomy.signature("T7", "transient", "ROUTE_INVALID att-0104 decision 2e7a754a87e5 at /tmp/x/1234")
        b = taxonomy.signature("T7", "transient", "ROUTE_INVALID att-0138 decision 91bc55aa09f1 at /var/y/99")
        self.assertEqual(a, b)
        self.assertNotEqual(a, taxonomy.signature("T7", "environment", "ROUTE_INVALID"))
        self.assertNotEqual(a, taxonomy.signature("T8", "transient", "ROUTE_INVALID"))


class Cycle(unittest.TestCase):
    def setUp(self):
        spawn = patch("bt_block_agent.spawn", return_value=True)      # the model step must not start a real `scheduler-op diagnose`
        spawn.start()
        self.addCleanup(spawn.stop)
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

    def test_a_repair_task_that_fails_is_retried_not_repaired_by_another_task(self):
        """P-164: REQ-020's T14.3a failed, and the healing added T14.4a to repair the repair, then T14.5a, each carrying the previous checks."""
        healing.save(self.rdir, {"actions": 1, "cases": {"old": {"id": "old", "task": "T7", "class": "regression", "status": "applied",
                                                                 "applied": 1, "task_added": "T7.1", "history": []}}})
        self.verify = "$ npx tsx scripts/e2e/asesor/run.ts --live\nexit code 1\n[FAIL] boom"
        card = request(task="T7.1", source="review", id="key-7", options=[{"id": "review_fail"}, {"id": "review_pass"}, {"id": "stop"}])
        with patch("bt_healing_classify.owners_of", return_value=("T1",)), patch.object(healing, "repair_task") as nested:
            self.run_cycle([card])
        nested.assert_not_called()                                                          # no repair of the repair
        self.assertEqual([a[:2] for a in self.answers], [("key-7", "review_fail")])
        self.assertTrue(healing.added_by_healing(self.rdir, "T7.1"))
        self.assertFalse(healing.added_by_healing(self.rdir, "T7"))

    def test_a_stop_nothing_could_place_gets_the_cards_recommended_retry_a_bounded_number_of_times(self):
        """The owner wants no human in the loop: the last rung is the card's own recommended plain retry, never a verdict or an owner-only
        decision."""
        self.verify = "an error the taxonomy has never seen"
        card = request(options=[{"id": "retry"}, {"id": "retry_with_note"}], recommended="retry")
        with patch("bt_config.get", side_effect=lambda key, default=None: default):             # shipped defaults: model off, autonomy on
            self.assertEqual(self.run_cycle([card]), 1)
        self.assertEqual([a[:2] for a in self.answers], [("T7:3", "retry")])
        self.assertIn("recommended retry", self.answers[0][2])
        # never a review, an owner-only stop, or an option that is not a plain retry
        for bad in (request(source="review", options=[{"id": "retry"}], recommended="retry"),
                    request(unskippable=True, options=[{"id": "retry"}], recommended="retry"),
                    request(options=[{"id": "review_pass"}, {"id": "stop"}], recommended="stop")):
            self.answers.clear()
            with patch("bt_config.get", side_effect=lambda key, default=None: default):
                self.run_cycle([bad])
            self.assertEqual(self.answers, [], bad)

    def test_the_autonomous_retry_stops_after_its_bound_and_can_be_switched_off(self):
        self.verify = "an error the taxonomy has never seen"
        card = request(options=[{"id": "retry"}], recommended="retry")
        with patch("bt_config.get", side_effect=lambda key, default=None: False if key == "healing.autonomous_default" else default):
            self.assertEqual(self.run_cycle([card]), 0)
        self.assertEqual(self.answers, [])
        with patch("bt_scheduler_decisions.automatic_answers", return_value=healing.AUTONOMOUS_LIMIT), \
                patch("bt_config.get", side_effect=lambda key, default=None: default):
            self.assertEqual(self.run_cycle([card]), 0)
        self.assertEqual(self.answers, [])

    def test_a_finished_analysis_rides_along_whatever_places_the_stop(self):
        import bt_attempt_analyst as analyst

        analyst._save(self.rdir, "T7", {"state": "done", "failures": 6, "not_the_task": True, "confidence": "alta",
                                        "cause": "the client concatenates functionCall parts", "solution": "1. read the parts"})
        seen = []
        with patch.object(healing, "_repair", side_effect=lambda *a: seen.append(a[5]) or {"repair": "none", "result": "pending"}):
            self.run_cycle([request()])                                                      # placed by the rules (transient), not by the analyst
        self.assertIn("the client concatenates functionCall parts", seen[0]["analysis"])

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

    def test_a_revision_the_planner_refused_does_not_spend_the_case(self):
        """REQ-020 T15: «revision invalid: T15.1.objective repeats the same words» marked the case exhausted at the first try."""
        refused = {"repair": "revision invalid: T9.1.objective: repeats the same words", "result": "failed"}
        with patch.object(healing, "_repair", return_value=refused):
            for _ in range(healing.INVALID_TRIES):
                self.run_cycle([request()])
        entry = next(iter(healing.load(self.rdir)["cases"].values()))
        self.assertEqual((entry["status"], entry["applied"], entry["invalid"]), ("open", 0, healing.INVALID_TRIES))
        with patch.object(healing, "_repair", return_value=refused):
            self.run_cycle([request()])                                                       # the fourth refusal does count
        entry = next(iter(healing.load(self.rdir)["cases"].values()))
        self.assertEqual(entry["applied"], 1)

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

    # --- REQ-029 R3/R4: the diagnosing model, as a last resort -------------------------------------------------------
    def model_card(self, **agent):
        done = {"state": "done", "option": "retry_with_note", "note": "Fix the ledger path first, then run the audit again.",
                "confidence": "alta", "kind": "code", "headline": "the audit checks the wrong ledger", "model": "haiku"}
        return request(agent={**done, **agent}, reason="m5:attempts_exhausted")

    def with_model(self, on=True):
        def get(key, default=None):
            return on if key == "healing.model_diagnosis" else False if key == "diagnosis.auto" else default
        patcher = patch("bt_config.get", side_effect=get)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_an_unplaced_stop_follows_the_models_validated_option_once_when_the_owner_opted_in(self):
        self.verify = "an error the taxonomy has never seen"
        self.with_model()
        self.assertEqual(self.run_cycle([self.model_card()]), 1)
        self.assertEqual(self.answers[0][:2], ("T7:3", "retry_with_note"))
        self.assertIn("Fix the ledger path first", self.answers[0][2])
        self.assertIn("model diagnosis", self.answers[0][2])
        row = list(bt_interventions.read(self.rdir))[0]
        self.assertEqual((row["class"], row["source"], row["result"]), ("unknown", "auto", "fixed"))
        self.run_cycle([self.model_card()])                                                  # the same failure again: never repeated
        self.assertEqual(len(self.answers), 1)
        self.assertEqual(next(iter(healing.load(self.rdir)["cases"].values()))["status"], "exhausted")

    def test_the_models_option_is_ignored_unless_it_is_a_plain_retry_confident_and_offered(self):
        self.verify = "an error the taxonomy has never seen"
        self.with_model()
        for agent in ({"option": "stop"}, {"option": "revise"}, {"option": "review_pass"}, {"confidence": "baja"},
                      {"state": "failed"}):
            self.assertEqual(self.run_cycle([self.model_card(**agent)]), 0, agent)
            healing.save(self.rdir, {"cases": {}, "actions": 0})
        self.assertEqual(self.answers, [])
        card = self.model_card()
        card["options"] = [{"id": "stop"}]                                                   # retry is not offered
        self.assertEqual(self.run_cycle([card]), 0)
        self.assertEqual(self.answers, [])

    def test_an_owner_only_decision_and_a_review_are_never_answered_by_the_model(self):
        self.verify = "an error the taxonomy has never seen"
        self.with_model()
        for over in ({"unskippable": True}, {"source": "review", "options": [{"id": "retry"}, {"id": "review_pass"}]}):
            self.assertEqual(self.run_cycle([{**self.model_card(), **over}]), 0, over)
        self.assertEqual(self.answers, [])

    def test_the_model_step_is_off_by_default_and_a_thin_note_becomes_a_plain_retry(self):
        self.verify = "an error the taxonomy has never seen"
        with patch("bt_config.get", side_effect=lambda key, default=None: False if key == "healing.autonomous_default" else default):
            self.assertEqual(self.run_cycle([self.model_card()]), 0)                          # the shipped model default (off), autonomy aside
        self.with_model()
        self.assertEqual(self.run_cycle([self.model_card(note="redo")]), 1)
        self.assertEqual(self.answers[0][1], "retry")

    def test_a_stop_the_rules_cannot_repair_falls_through_to_the_model_and_a_missing_diagnosis_is_asked_for(self):
        self.with_model()
        self.verify = "an error the taxonomy has never seen"
        asked = []
        with patch("bt_block_agent.spawn", side_effect=lambda *a: asked.append(a) or True), \
                patch("bt_config.get", side_effect=lambda key, default=None: key in ("healing.model_diagnosis", "diagnosis.auto") or default):
            waiting = self.run_cycle([request()])                                            # no diagnosis yet: ask for it, record nothing
        self.assertEqual((waiting, len(asked), self.answers), (0, 1, []))
        self.assertEqual(healing.load(self.rdir)["actions"], 0)

    def test_a_placed_stop_with_no_rule_repair_also_falls_through_to_the_model(self):
        self.verify = "EROFS: read-only file system, mkdir node_modules"                      # environment, but no known note to retry with
        self.with_model()
        self.assertEqual(self.run_cycle([self.model_card()]), 1)
        self.assertEqual(self.answers[0][1], "retry_with_note")
        self.assertEqual(list(bt_interventions.read(self.rdir))[0]["class"], "environment")

    def test_a_verification_the_verifier_keeps_refusing_is_reported_once_not_looped_in_silence(self):
        """REQ-020 T14.1a: ORDER_INVALID on every re-send, every 5 minutes, for 100+ minutes, and nobody was told."""
        self.doc = {"tasks": {"T7": {"state": "active", "attempts": ["att-9"]}},
                    "attempts": {"att-9": {"updated_at": NOW - 3600, "state": "verifying", "task_id": "T7"}}}
        with patch.object(healing, "verify_rejections", return_value=["ORDER_INVALID"] * 4):
            self.assertEqual(self.run_cycle([]), 0)
            self.run_cycle([])                                                                   # the second cycle says nothing more
        self.assertEqual(len(self.notes), 1)
        self.assertIn("ORDER_INVALID", self.notes[0])
        row = list(bt_interventions.read(self.rdir))[0]
        self.assertEqual((row["class"], row["result"], row["task"]), ("plan_defect", "failed", "T7"))
        with patch.object(healing, "verify_rejections", return_value=["ORDER_INVALID", "ORDER_INVALID"]):
            self.assertEqual(healing.stuck_verifications(self.rdir, self.doc), [])   # two is not a pattern yet

    def test_the_rejections_are_read_from_the_runs_own_audit_log(self):
        import sqlite3
        import bt_scheduler_adapter as adapter
        db = self.rdir / "run.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL, kind TEXT, plan_id TEXT, task_id TEXT, attempt_id TEXT, detail TEXT, incident_event_id TEXT)")
        rows = [("dispatch_rejected", "att-1", {"kind": "verify", "detail": "ORDER_INVALID"}), ("dispatch_rejected", "att-1", {"kind": "start", "detail": "X"}),
                ("dispatch_rejected", "att-2", {"kind": "verify", "detail": "OTHER"}), ("lease_expired", "att-1", {})]
        for n, (kind, attempt, detail) in enumerate(rows, 1):
            conn.execute("INSERT INTO audit VALUES (?, 0, ?, 'P', 'T1', ?, ?, NULL)", (n, kind, attempt, json.dumps(detail)))
        conn.commit()
        conn.close()
        with patch.object(adapter, "run_db_path", return_value=db):
            self.assertEqual(healing.verify_rejections(self.rdir, "att-1"), ["ORDER_INVALID"])     # only verify rejections of that attempt
            self.assertEqual(healing.verify_rejections(self.rdir, "att-9"), [])

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

    def test_the_repair_of_an_audit_does_not_inherit_the_checks_that_read_the_audits_own_ledger(self):
        """REQ-020 T15.1: it carried T15's `check-findings.ts docs/req-020/T15.findings.json`, a file only the audit writes, and failed ENOENT
        on every attempt."""
        plan = self.plan()
        for task in plan["tasks"]:
            if task["id"] == "T3":
                task["kind"] = "audit"
        revised, new_id, _ = healing.build_fix_revision(plan, "T3", self.case(), {"verify": "FAIL: test_a boom"})
        commands = {v["value"] for v in {t["id"]: t for t in revised["tasks"]}[new_id]["verification"]}
        self.assertIn("pytest tests/test_a.py", commands)                                    # the owners' checks stay
        self.assertNotIn("pytest tests/test_a.py tests/test_b.py", commands)                  # the audit's own do not
        # a case that names no owner (the analyst said «not this task») names the audit itself: a command over ITS ledger still must not reach
        # the repair, whatever put it there
        for task in plan["tasks"]:
            if task["id"] == "T3":
                task["expected_paths"] = ["docs/report.md"]
                task["verification"] = [*task["verification"], {"type": "command", "value": "check docs/report.md", "purpose": "ledger",
                                                                "category": "functional"}]
        alone, alone_id, _ = healing.build_fix_revision(plan, "T3", self.case(owners=("T1",)), {"verify": "FAIL: x"})
        self.assertFalse([v for v in {t["id"]: t for t in alone["tasks"]}[alone_id]["verification"] if "docs/report.md" in v["value"]])

    def test_the_analysts_cause_and_advice_reach_the_repair_tasks_objective(self):
        case = taxonomy.Case("T3:1", "T3", "regression", ("independent analysis",), signature="s2")
        analysis = "Independent failure analysis (after 5 failed attempts): Cause: check-findings.ts ignores the positional path"
        revised, new_id, _ = healing.build_fix_revision(self.plan(), "T3", case, {"verify": "FAIL: x", "analysis": analysis})
        objective = {t["id"]: t for t in revised["tasks"]}[new_id]["objective"]
        self.assertIn("check-findings.ts ignores the positional path", objective)
        self.assertIn("the cause lies outside it", objective)
        from bt_plan_adapter import plan_errors
        self.assertEqual(plan_errors(revised), [])

    def test_applying_a_revision_retries_while_an_owner_is_starting_and_gives_up_on_anything_else(self):
        import bt_scheduler_ops as ops

        calls, pauses = [], []

        def apply(*args):
            calls.append(args)
            if len(calls) < 3:
                raise ops.core.SchedulerError("OWNER_ACTIVE", "another Scheduler or legacy owner is starting")
            return ["rebased"]

        with patch.object(ops, "apply", side_effect=apply):
            self.assertEqual(healing._revise("p", "REQ-1", Path("/x"), "why", sleep=pauses.append), ["rebased"])
        self.assertEqual((len(calls), pauses), (3, [healing.REVISE_PAUSE] * 2))
        with patch.object(ops, "apply", side_effect=ops.core.SchedulerError("OWNER_ACTIVE", "x")), \
                self.assertRaises(ops.core.SchedulerError):
            healing._revise("p", "REQ-1", Path("/x"), "why", sleep=lambda s: None)
        with patch.object(ops, "apply", side_effect=ops.core.SchedulerError("NOT_ALLOWED", "no")) as other, \
                self.assertRaises(ops.core.SchedulerError):
            healing._revise("p", "REQ-1", Path("/x"), "why", sleep=lambda s: None)
        self.assertEqual(other.call_count, 1)                                                # a real refusal is not retried

    def test_a_live_check_that_failed_becomes_a_coordinator_check_of_the_repair_itself(self):
        verify = ("The coordinator ran the live check and it FAILED, so nothing was attested:\n\n$ npx tsx --conditions=react-server "
                  "scripts/e2e/asesor/run.ts --start --live --milestone M2\nexit code 1\n[FAIL] asesor M2: correction did not regenerate the summary\n")
        revised, new_id, _ = healing.build_fix_revision(self.plan(), "T3", self.case(), {"verify": verify})
        fix = {t["id"]: t for t in revised["tasks"]}[new_id]
        manual = [v for v in fix["verification"] if v["type"] == "manual"]
        self.assertEqual(len(manual), 1)
        self.assertIn("Coordinator runs `npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2`", manual[0]["value"])
        self.assertIn(manual[0]["purpose"], fix["acceptance_criteria"])                      # the check maps to exactly one criterion
        import bt_coordinator
        self.assertEqual(bt_coordinator.commands_of(manual[0]["value"]), ["npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2"])
        from bt_plan_adapter import plan_errors
        self.assertEqual(plan_errors(revised), [])
        # an ordinary failure (no coordinator run) adds no manual check
        plain, plain_id, _ = healing.build_fix_revision(self.plan(), "T3", self.case(), {"verify": "FAIL: test_a boom"})
        self.assertFalse([v for v in {t["id"]: t for t in plain["tasks"]}[plain_id]["verification"] if v["type"] == "manual"])

    def test_an_analysis_that_quotes_the_failure_does_not_make_the_objective_repeat_itself(self):
        """REQ-020 T14.4a: the real analysis quoted the same command and `[FAIL]` line as the evidence, and the planner refused the
        objective ('repeats the same words')."""
        command = "$ npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2\nexit code 1\n"
        fail = "[FAIL] asesor M2: correction did not regenerate the summary\n"
        analysis = ("Independent failure analysis (after 15 failed attempts; confidence media): Cause: the live command "
                    "`npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --start --live --milestone M2` fails with "
                    "`[FAIL] asesor M2: correction did not regenerate the summary` because Gemini returns functionCall parts "
                    "that the client concatenates as text. What to do differently: 1. read the parts of the response.")
        case = taxonomy.Case("T3:1", "T3", "regression", ("e",), owners=("T1",), failing=("run.ts",), signature="s3")
        revised, new_id, _ = healing.build_fix_revision(self.plan(), "T3", case, {"verify": command + fail * 3, "analysis": analysis})
        from bt_plan_adapter import plan_errors
        self.assertEqual(plan_errors(revised), [])
        self.assertIn("functionCall parts", {t["id"]: t for t in revised["tasks"]}[new_id]["objective"])

    def test_a_repair_left_without_any_check_gets_a_manual_review_instead_of_being_refused_by_the_planner(self):
        """david-ui T25.1 / REQ-020 T15.3: «needs at least one command or explicit manual check»."""
        import bt_remediation
        from bt_plan_adapter import plan_errors

        plan = self.plan()
        target = {t["id"]: t for t in plan["tasks"]}["T3"]
        target["kind"] = "audit"
        target["verification"] = []
        original = bt_remediation._task

        def bare(*args, **kwargs):
            task = original(*args, **kwargs)
            if task is not None:
                task["verification"] = []
            return task
        case = taxonomy.Case("T3:1", "T3", "regression", ("e",), owners=("T1",), failing=("test_a",), signature="s7")
        with patch.object(bt_remediation, "_task", bare):
            revised, new_id, _ = healing.build_fix_revision(plan, "T3", case, {"verify": "FAIL: test_a boom"})
        fix = {t["id"]: t for t in revised["tasks"]}[new_id]
        self.assertEqual([v["type"] for v in fix["verification"]], ["manual"])
        self.assertEqual([e for e in plan_errors(revised) if e.startswith(new_id)], [])

    def test_a_template_tail_that_repeats_words_is_trimmed_instead_of_abandoning_the_repair(self):
        """REQ-020 T15.1: even the shortest evidence stayed invalid because the owners' own commands repeated the same words."""
        from bt_plan_adapter import plan_errors

        plan = self.plan()
        for task in plan["tasks"][:2]:
            task["verification"] = [{"type": "command", "value": f"npx tsx scripts/e2e/asesor/check-findings.ts docs/req-020/f.json --n {n}",
                                     "purpose": "scripts e2e asesor check findings docs req 020", "category": "functional"} for n in range(8)]
        case = taxonomy.Case("T3:1", "T3", "regression", ("e",), owners=("T1", "T2"), failing=("check-findings.ts",), signature="s5")
        revised, new_id, _ = healing.build_fix_revision(plan, "T3", case, {"verify": "$ npx tsx scripts/e2e/asesor/check-findings.ts\nexit code 1\n[FAIL] findings check\n"})
        self.assertEqual([e for e in plan_errors(revised) if e.startswith(f"{new_id}.objective")], [])

    def test_a_repair_of_a_repair_does_not_pile_up_repeated_checks_and_never_exceeds_what_the_scheduler_routes(self):
        """REQ-020 T14.5a had 42 checks: the decision engine refused its input and the owner looped for 30 minutes."""
        from bt_plan_adapter import plan_errors

        plan = self.plan()
        base = plan["tasks"][1]
        base["verification"] = base["verification"] + [{"type": "command", "value": f"pytest tests/test_x{n}.py", "purpose": f"x{n} passes",
                                                         "category": "regression"} for n in range(10)]
        case = taxonomy.Case("T3:1", "T3", "regression", ("e",), owners=("T1", "T2"), failing=("test_a",), signature="s4")
        revised, new_id, _ = healing.build_fix_revision(plan, "T3", case, {"verify": "FAIL: test_a"})
        fix = {t["id"]: t for t in revised["tasks"]}[new_id]
        values = [(c["type"], c["value"], c["purpose"]) for c in fix["verification"]]
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(plan_errors(revised), [])
        for n in range(40):                                                                  # too many DISTINCT checks: no repair at all
            base["verification"].append({"type": "command", "value": f"pytest tests/test_y{n}.py", "purpose": f"y{n} passes", "category": "regression"})
        self.assertIsNone(healing.build_fix_revision(plan, "T3", case, {"verify": "FAIL: test_a"}))

    def test_a_plan_the_scheduler_cannot_route_is_not_a_valid_revision(self):
        from bt_plan_adapter import plan_errors

        plan = self.plan()
        plan["tasks"][0]["verification"] = [{"type": "command", "value": f"pytest t{n}.py", "purpose": f"t{n}", "category": "functional"}
                                            for n in range(33)]
        self.assertTrue(any("routes at most 32" in e for e in plan_errors(plan)))

    def test_an_owner_that_repeats_the_same_port_error_is_seen(self):
        same = [{"port": "assignment", "error": "DecisionInputError", "detail": "decision_input_invalid: task.verification:invalid_sequence"}] * 12
        found = healing.looping_ports(Path("/nowhere"), same)
        self.assertEqual(found, [("assignment", "decision_input_invalid: task.verification:invalid_sequence", 12)])
        self.assertEqual(healing.looping_ports(Path("/nowhere"), same[:11]), [])                                  # a hiccup
        self.assertEqual(healing.looping_ports(Path("/nowhere"), same[:11] + [{"port": "query", "error": "X"}]), [])   # mixed: not a loop

    def test_a_repair_that_would_repeat_the_same_words_says_less_instead_of_being_refused(self):
        """REQ-020 T15.1: two failing commands with the same long script path, their exit codes and the analyst's text made the planner refuse
        the objective (`repeats the same words`) and the healing gave up on a repair that was sound."""
        cmd = "$ npx tsx --conditions=react-server scripts/e2e/asesor/check-findings.ts docs/req-020/T15.findings.json"
        verify = (f"{cmd}\nexit code 1\n[FAIL] findings check: ENOENT: no such file\n"
                  f"{cmd} --check-audit-diff --integration-results docs/req-020/integration-results.json\nexit code 1\n[FAIL] findings check: mismatch\n")
        analysis = "Independent failure analysis: Cause: check-findings.ts check-findings.ts check-findings.ts " * 6
        revised, new_id, _ = healing.build_fix_revision(self.plan(), "T3", self.case(), {"verify": verify, "analysis": analysis})
        from bt_plan_adapter import plan_errors
        self.assertEqual(plan_errors(revised), [])
        self.assertEqual([t["id"] for t in revised["tasks"]].count(new_id), 1)               # one repair task, however many variants were tried
        self.assertIn("check-findings.ts", {t["id"]: t for t in revised["tasks"]}[new_id]["objective"])

    def test_only_a_finished_confident_analysis_that_blames_something_else_places_a_stop(self):
        import bt_attempt_analyst as analyst

        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp)
            req = {"id": "r1", "task": "T3"}
            self.assertIsNone(healing.analyst_case(rdir, req))                                  # nothing analysed yet
            analyst._save(rdir, "T3", {"state": "done", "failures": 5, "not_the_task": False, "cause": "c", "solution": "s"})
            self.assertIsNone(healing.analyst_case(rdir, req))                                  # it blames the task itself
            analyst._save(rdir, "T3", {"state": "done", "failures": 5, "not_the_task": True, "confidence": "baja", "cause": "c", "solution": "s"})
            self.assertIsNone(healing.analyst_case(rdir, req))                                  # not sure
            analyst._save(rdir, "T3", {"state": "done", "failures": 5, "not_the_task": True, "confidence": "media", "source_available": True, "cause": "the checker is unreachable", "solution": "s"})
            case = healing.analyst_case(rdir, req)
            self.assertEqual((case.kind, case.task), ("regression", "T3"))
            self.assertIn("the checker is unreachable", case.evidence[0])

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
