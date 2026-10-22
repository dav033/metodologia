"""Fixes from the independent adversarial review of the recovery and self-healing surface (REQ-029 T14/T15)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_attestation as att
import bt_interventions
import bt_scheduler_adapter as adapter
import bt_scheduler_healing as healing
import bt_scheduler_ops as ops
from test_remediation import plan as make_plan, task as make_task
from test_scheduler_healing import NOW, request


class Holds(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        patcher = patch.object(adapter, "run_db_path", return_value=self.rdir / "SCHEDULER.db")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_nested_move_never_destroys_an_operators_stop(self):
        with ops.hold(self.rdir, "operator stop", keep=True):
            pass
        marker = ops.hold_path(self.rdir).read_text()
        with ops.hold(self.rdir, "healing move"):
            self.assertIn("healing move", ops.hold_path(self.rdir).read_text())
        self.assertTrue(ops.on_hold(self.rdir))                                       # the stop was there before: it is back
        self.assertEqual(ops.hold_path(self.rdir).read_text(), marker)

    def test_a_stop_that_lands_during_a_move_is_left_in_place(self):
        with ops.hold(self.rdir, "recovery move"):
            with ops.hold(self.rdir, "operator stop", keep=True):                     # the operator presses stop meanwhile
                pass
        self.assertTrue(ops.on_hold(self.rdir))
        self.assertIn("operator stop", ops.hold_path(self.rdir).read_text())

    def test_without_a_prior_hold_the_move_cleans_up_after_itself(self):
        with ops.hold(self.rdir, "move"):
            self.assertTrue(ops.on_hold(self.rdir))
        self.assertFalse(ops.on_hold(self.rdir))

    def test_a_stop_landing_between_two_repairs_stops_the_cycle(self):
        doc = {"tasks": {f"T{n}": {"state": "blocked", "attempts": [f"a{n}"]} for n in (1, 2)},
               "attempts": {f"a{n}": {"updated_at": NOW - 3600} for n in (1, 2)}}
        answers = []

        def answer(*args):
            answers.append(args)
            ops.hold_path(self.rdir).write_text('{"why": "operator stop"}\n')            # the stop lands after the first repair
            return ["ok"]

        verify = "start rejected: ROUTE_INVALID: the decision was replaced by 2e7a754a"
        with patch("bt_scheduler_decisions._state", return_value=doc), patch("bt_scheduler_decisions._plan", return_value=None), \
                patch("bt_scheduler_decisions._context", return_value={"verify": verify, "failures": [verify], "repeats": 0,
                                                                       "closed": "", "refused": {}}):
            done = healing.cycle("p", "REQ-1", self.rdir, requests=[request(id="T1:1", task="T1", attempt="a1"),
                                                                     request(id="T2:1", task="T2", attempt="a2")],
                                 now=lambda: NOW, answer=answer, revise=lambda why: [])
        self.assertEqual((done, len(answers)), (1, 1))                                   # the second repair did not run


class HealingFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)

    def test_a_malformed_record_is_normalised_not_fatal(self):
        for raw in ('[]', '{"cases": []}', '{"cases": {"x": "s"}}', '{"actions": "a", "cases": {"k": {"applied": "z", "history": 3}}}'):
            (self.rdir / healing.FILE).write_text(raw)
            data = healing.load(self.rdir)
            self.assertIsInstance(data["cases"], dict)
            self.assertIsInstance(data["actions"], int)
            for entry in data["cases"].values():
                self.assertIsInstance(entry["applied"], int)
                self.assertIsInstance(entry["history"], list)
            self.assertIsNotNone(healing.status(self.rdir))

    def test_the_record_cannot_be_inflated_by_distinct_error_texts(self):
        doc = {"tasks": {"T1": {"state": "blocked", "attempts": ["a1"]}}, "attempts": {"a1": {"updated_at": NOW - 3600}}}
        state = {"actions": 0, "cases": {f"s{n}": {"id": f"s{n}", "task": "T9", "class": "environment", "status": "unrepairable",
                                                   "applied": 0, "history": []} for n in range(healing.MAX_CASES)}}
        healing.save(self.rdir, state)
        verify = "EROFS: read-only file system, mkdir brand-new-error"
        with patch("bt_scheduler_decisions._state", return_value=doc), patch("bt_scheduler_decisions._plan", return_value=None), \
                patch("bt_scheduler_decisions._context", return_value={"verify": verify, "failures": [verify], "repeats": 0,
                                                                       "closed": "", "refused": {}}):
            healing.cycle("p", "R", self.rdir, requests=[request()], now=lambda: NOW, answer=lambda *a: [], revise=lambda w: [])
        self.assertEqual(len(healing.load(self.rdir)["cases"]), healing.MAX_CASES)

    def test_an_unrepairable_case_is_terminal_and_keeps_a_bounded_history(self):
        doc = {"tasks": {"T1": {"state": "blocked", "attempts": ["a1"]}}, "attempts": {"a1": {"updated_at": NOW - 3600}}}
        verify = "EROFS: read-only file system, mkdir x"                                 # a class with no safe repair without a note
        with patch("bt_scheduler_decisions._state", return_value=doc), patch("bt_scheduler_decisions._plan", return_value=None), \
                patch("bt_scheduler_decisions._context", return_value={"verify": verify, "failures": [verify], "repeats": 0,
                                                                       "closed": "", "refused": {}}):
            for _ in range(5):
                healing.cycle("p", "R", self.rdir, requests=[request()], now=lambda: NOW, answer=lambda *a: [], revise=lambda w: [])
        entry = next(iter(healing.load(self.rdir)["cases"].values()))
        self.assertEqual(entry["status"], "unrepairable")
        self.assertEqual(len(entry["history"]), 1)                                       # looked at once, then left alone


class Revert(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        self.plan = make_plan(make_task("T1", paths=["a.py"]), make_task("T2", ["T1"], paths=["b.py"]),
                              make_task("T3", ["T2"], kind="test", category="regression", paths=["r.md"]))
        self.fixed, self.new_id, self.restored = healing.build_fix_revision(
            self.plan, "T3", healing.classify_mod.Case("T3:1", "T3", "regression", ("x",), owners=("T1",), failing=("t",),
                                                       signature="s"), {"verify": "boom"})

    def record(self, **over):
        entry = {"id": "c", "task": "T3", "class": "regression", "status": "applied", "task_added": self.new_id, "target": "T3",
                 "after_restored": self.restored, "applied": 1, **over}
        healing.save(self.rdir, {"actions": 1, "cases": {"c": entry}})

    def revert(self, latest):
        frozen = []
        with patch.object(healing, "_latest_plan", return_value=latest), \
                patch.object(healing, "_freeze", side_effect=lambda r, p, s: frozen.append(p) or p):
            lines = healing.revert("p", "REQ-1", self.rdir, "c", revise=lambda why: [])
        return frozen[0], lines

    def test_only_the_repair_task_leaves_and_every_later_edge_stays(self):
        self.record()
        later = json.loads(json.dumps(self.fixed))
        next(t for t in later["tasks"] if t["id"] == "T2")["after"].append("T9")      # a later revision gave T2 a new prerequisite
        later["tasks"].append({**later["tasks"][0], "id": "T9"})
        back, _ = self.revert(later)
        self.assertEqual({t["id"]: t["after"] for t in back["tasks"]}["T2"], ["T1", "T9"])
        self.assertNotIn(self.new_id, [t["id"] for t in back["tasks"]])

    def test_a_forged_case_cannot_remove_a_real_task_or_an_accepted_one(self):
        self.record(task_added="T1", revision=4)
        with self.assertRaises(ValueError):
            self.revert(self.fixed)                                                       # T1 is not a repair task
        self.record()
        with patch.object(healing, "_is_accepted", return_value=True):
            with self.assertRaises(ValueError):
                self.revert(self.fixed)                                                   # an accepted repair stays
        self.record(task_added="T3.7")
        with self.assertRaises(ValueError):
            self.revert(self.fixed)                                                       # not in the current plan

    def test_a_frozen_revision_whose_application_failed_can_still_be_reverted(self):
        def boom(why):
            raise RuntimeError("impact above the ceiling")

        case = healing.classify_mod.Case("T3:1", "T3", "regression", ("x",), owners=("T1",), failing=("t",), signature="s")
        with patch.object(healing, "_latest_plan", return_value=self.plan), patch.object(healing, "_freeze", return_value={}):
            outcome = healing.repair_task("p", "R", self.rdir, request(task="T3"), case, {"verify": "boom"}, None, boom)
        self.assertEqual(outcome["result"], "failed")
        self.assertEqual(outcome["track"]["task_added"], "T3.1")                           # `revert` has what it needs


class Forgeries(unittest.TestCase):
    def test_forged_rows_are_dropped_or_reduced_to_known_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / bt_interventions.FILE
            path.write_text("\n".join([
                json.dumps({"at": "soon", "class": "transient"}), json.dumps({"at": 1.0, "class": "transient", "minutes_lost": "5"}),
                json.dumps({"at": 2.0, "class": "made-up", "source": "x", "result": "y", "task": "T1" * 500}), "not json", "[]",
                json.dumps({"at": float("inf"), "class": "quota"})]) + "\n")
            rows = list(bt_interventions.read(tmp))
        self.assertEqual([r["at"] for r in rows], [1.0, 2.0])
        self.assertIsNone(rows[0]["minutes_lost"])
        self.assertEqual((rows[1]["class"], rows[1]["source"], rows[1]["result"]), ("unknown", "auto", "pending"))
        self.assertLessEqual(len(rows[1]["task"]), bt_interventions.MAX_TEXT)

    def test_only_the_tail_of_a_huge_file_is_read(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(bt_interventions, "MAX_BYTES", 400):
            lines = [json.dumps({"at": float(n), "class": "transient"}) for n in range(100)]
            (Path(tmp) / bt_interventions.FILE).write_text("\n".join(lines) + "\n")
            rows = list(bt_interventions.read(tmp))
        self.assertLess(len(rows), 20)
        self.assertEqual(rows[-1]["at"], 99.0)

    def test_an_empty_or_short_key_never_seals_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            key = Path(tmp) / "attestation.key"
            key.write_bytes(b"")
            args = ("T9", "voice works", "open it on a phone", "ok", "Opened it on a phone and saw the transcript appear", "david")
            att.mint(Path(tmp) / "run", *args, key_file=key)
            self.assertGreaterEqual(len(key.read_bytes()), 32)                            # the damaged key was replaced
            self.assertIsNotNone(att.verify(Path(tmp) / "run", "T9", "voice works", "open it on a phone", "ok", key_file=key))
            body = json.loads(next((Path(tmp) / "run" / att.DIR).rglob("*.json")).read_text())
            forged = att._seal({k: v for k, v in body.items() if k != "seal"}, b"")       # a seal made with the empty key
            key.write_bytes(b"")
            next((Path(tmp) / "run" / att.DIR).rglob("*.json")).write_text(json.dumps({**body, "seal": forged}))
            self.assertIsNone(att.verify(Path(tmp) / "run", "T9", "voice works", "open it on a phone", "ok", key_file=key))


if __name__ == "__main__":
    unittest.main()
