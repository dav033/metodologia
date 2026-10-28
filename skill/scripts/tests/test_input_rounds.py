"""The system asks the owner what only he can confirm, never overwrites an answered round, and brings the Planner back."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_agent_terminal as terminal  # noqa: E402
import bt_input_rounds as ir  # noqa: E402
import bt_rounds as rounds  # noqa: E402

SPEC = """# Spec

## Inputs

| Item | Subplan | Where | Who | Status |
|---|---|---|---|---|
| Modelling rule for new Backings: only caja, cilindro and panel | SP-3 | Planner assumption 2026-10-27 (Assumptions) | Owner | pending: confirm when SP-3 is in focus |
| Shopify token | SP-3 | ~/.config/x.env | Owner | pending |
| Other assumption | SP-4 | Planner assumption | Owner | pending |
"""


def rows(spec_text: str) -> list[dict]:
    import bt_planning_flow as flow
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "SPEC.md").write_text(spec_text, encoding="utf-8")
        return flow.inputs(Path(tmp))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        self.state = {"focus": "SP-3", "editing": False}
        patcher = patch("bt_planning_flow.active", return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)


class Ensure(Base):
    def test_only_a_pending_owner_assumption_of_the_focused_subplan_is_asked(self):
        found = ir.assumptions(self.rdir, "SP-3")
        self.assertEqual([r["item"][:20] for r in found], ["Modelling rule for n"])     # the token row is not an assumption
        round_file = ir.ensure(self.rdir, self.state)
        data = rounds.load(round_file)
        self.assertEqual((data["status"], data["coverage"], len(data["questions"])), ("open", "SP-3", 1))
        self.assertEqual(data["questions"][0]["recommended"], "a")
        self.assertEqual(data["auto_input"][0]["id"], "q1")

    def test_it_is_idempotent_and_waits_for_an_open_round_to_be_answered(self):
        first = ir.ensure(self.rdir, self.state)
        self.assertIsNotNone(first)
        self.assertIsNone(ir.ensure(self.rdir, self.state))                              # already asked and still open
        rounds.answer_round(first, {"q1": {"choice": "a", "note": ""}}, "web")
        self.assertIsNone(ir.ensure(self.rdir, self.state))                              # answered rounds count as asked

    def test_nothing_is_asked_when_another_round_is_open_or_the_flow_is_off(self):
        rounds.new_round(self.rdir, {"title": "t", "questions": [{"text": "q", "options": [{"key": "a", "label": "x"}]}]})
        self.assertIsNone(ir.ensure(self.rdir, self.state))
        with patch("bt_planning_flow.active", return_value=False):
            self.assertIsNone(ir.ensure(self.rdir, self.state))


class Apply(Base):
    def test_a_confirmation_resolves_the_spec_row_and_the_flow_reads_it_as_resolved(self):
        round_file = ir.ensure(self.rdir, self.state)
        data = rounds.answer_round(round_file, {"q1": {"choice": "a", "note": ""}}, "web")
        self.assertEqual(ir.apply_answers(self.rdir, data), ["q1: confirmed"])
        self.assertEqual([r["pending"] for r in rows((self.rdir / "SPEC.md").read_text(encoding="utf-8"))], [False, True, True])
        self.assertEqual(ir.assumptions(self.rdir, "SP-3"), [])

    def test_a_change_becomes_a_note_for_the_planner_and_leaves_the_row_pending(self):
        round_file = ir.ensure(self.rdir, self.state)
        data = rounds.answer_round(round_file, {"q1": {"choice": "b", "note": "allow a new torus shape"}}, "web")
        with patch("bt_planning_notes.add") as add:
            self.assertEqual(ir.apply_answers(self.rdir, data), ["q1: owner wants a change"])
        self.assertIn("allow a new torus shape", add.call_args.args[1])
        self.assertTrue(rows((self.rdir / "SPEC.md").read_text(encoding="utf-8"))[0]["pending"])

    def test_a_round_the_planner_wrote_is_left_alone(self):
        self.assertEqual(ir.apply_answers(self.rdir, {"round": 3, "answers": {"q1": {"choice": "a"}}}), [])


class Numbering(Base):
    def test_a_new_round_takes_the_next_free_number_even_with_a_gap(self):
        folder = self.rdir / "rounds"
        folder.mkdir()
        for n in (1, 2, 11, 12, 13):
            (folder / f"round-{n:02d}.json").write_text(json.dumps({"round": n, "status": "answered"}), encoding="utf-8")
        created = rounds.new_round(self.rdir, {"title": "t", "questions": [{"text": "q", "options": [{"key": "a", "label": "x"}]}]})
        self.assertEqual(created.name, "round-14.json")
        self.assertEqual(json.loads((folder / "round-13.json").read_text())["status"], "answered")   # untouched


class Revive(unittest.TestCase):
    def make(self, root: Path, *, status: str, age_days: float, session: str = "sid") -> Path:
        import time
        rdir = root / "pictures" / "requirements" / "REQ-021-demo"
        (rdir / ".planning").mkdir(parents=True)
        (rdir / "PLAN.md").write_text(f"---\nstatus: {status}\n---\n# Plan\n", encoding="utf-8")
        stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(time.time() - age_days * 86400))
        (rdir / ".planning" / "planner.json").write_text(json.dumps({"session_id": session, "started_at": stamp}), encoding="utf-8")
        return rdir

    def run_revive(self, root: Path, alive: bool = False) -> tuple[list[str], list]:
        with patch.object(terminal, "exists", return_value=alive), \
                patch.object(terminal, "start_planner", return_value=(True, "ok")) as start:
            return terminal.revive_planners(root), start.call_args_list

    def test_a_planner_of_a_plan_still_in_planning_comes_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make(Path(tmp), status="draft", age_days=0.2)
            started, calls = self.run_revive(Path(tmp))
        self.assertEqual((started, len(calls)), (["pictures/REQ-021"], 1))

    def test_old_finished_running_or_conversationless_planners_stay_down(self):
        for kwargs in ({"status": "draft", "age_days": 9}, {"status": "approved", "age_days": 0.2},
                       {"status": "draft", "age_days": 0.2, "session": ""}):
            with tempfile.TemporaryDirectory() as tmp:
                self.make(Path(tmp), **kwargs)
                self.assertEqual(self.run_revive(Path(tmp))[0], [])
        with tempfile.TemporaryDirectory() as tmp:
            self.make(Path(tmp), status="draft", age_days=0.2)
            self.assertEqual(self.run_revive(Path(tmp), alive=True)[0], [])


if __name__ == "__main__":
    unittest.main()
