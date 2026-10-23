"""Scheduler healing cycle actions, budgets and recovery choices."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bt_interventions
import bt_scheduler_healing as healing
from test_scheduler_healing import NOW, request


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

    def test_an_audit_is_not_retried_without_an_applied_producer_repair(self):
        import bt_remediation
        self.verify = "audit gate: 11 open blocking finding(s): F3 (high), F4 (high)"
        card = request(task="T8", id="T8:3", reason="rework_impact", error=self.verify)
        self.doc["tasks"]["T8"] = {"state": "blocked", "attempts": ["att-9"]}
        self.assertEqual(self.run_cycle([card]), 0)
        self.assertEqual(self.answers, [])
        self.assertEqual(bt_remediation.extra_rounds(self.rdir, "T8"), 0)
        self.assertFalse(bt_remediation.requested(self.rdir))
        self.assertEqual(self.run_cycle([card]), 0)                                          # it came back: the owner decides now

    def test_a_model_choice_cannot_bypass_missing_producer_remediation(self):
        self.verify = "audit gate: open blocking finding F1"
        card = request(task="T8", id="T8:3", reason="rework_impact", error=self.verify)
        self.doc["tasks"]["T8"] = {"state": "blocked", "attempts": ["att-9"]}
        with patch.object(healing, "model_enabled", return_value=True), \
                patch.object(healing, "model_eligible", return_value=True), \
                patch.object(healing, "model_repair") as model:
            self.assertEqual(self.run_cycle([card]), 0)
        model.assert_not_called()
        self.assertEqual(self.answers, [])

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
