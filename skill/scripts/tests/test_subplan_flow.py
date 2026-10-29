"""The Flow of one subplan (D-150): the durable runtime's telemetry as flow messages (`bt_flow_durable`), the
`subplan:P/REQ/SP` scope of the live API, the embedded Flow page and its frame under the subplan's «Ejecución»."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_core
import bt_flow_bus as bus
import bt_flow_durable as durable
import bt_live_api as live
import bt_page_flow
import test_flow_bus as fb
import test_subplan_control as control

RECORDS = [
    {"ts": 200.0, "event": "route_decision", "run_id": "demo:REQ-001:r1", "task_id": "T1", "route": "codex:luis:gpt",
     "basis": "m2"},
    {"ts": 201.0, "event": "attempt_started", "attempt_key": "demo-REQ-001-r1-T1-a1-0123abcd", "provider": "codex",  # gitleaks:allow (a fake attempt key)
     "model": "gpt"},
    {"ts": 202.0, "event": "attempt_started", "attempt_key": "other-REQ-001-r1-T1-a1-0123abcd", "provider": "x"},  # gitleaks:allow (a fake attempt key)
    {"ts": 203.0, "event": "recovery_decision", "run_id": "demo:REQ-001:r1", "task_id": "T1", "action": "escalate",
     "code": "CHECK_FAILED", "reason": "budget"},
    {"ts": 204.0, "event": "decision_requested", "run_id": "demo:REQ-001:r1", "task_id": "T1", "reason": "budget"},
    {"ts": 205.0, "event": "decision_answered", "run_id": "demo:REQ-001:r1", "task_id": "T1", "action": "retry"},
    {"ts": 206.0, "event": "something_new", "run_id": "demo:REQ-001:r1", "task_id": "T1"},
    {"ts": 207.0, "event": "task_settled", "run_id": "demo:REQ-002:r1", "task_id": "T1", "status": "completed"},
]


class DurableTelemetry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        state = self.root / ".state"
        (state / "durable").mkdir(parents=True)
        (state / "durable" / "telemetry.jsonl").write_text("\n".join(json.dumps(r) for r in RECORDS) + "\n")
        p = patch.object(bt_core, "STATE", state)
        p.start()
        self.addCleanup(p.stop)
        self.rdir = self.root / "demo" / "requirements" / "REQ-001-x"
        self.rdir.mkdir(parents=True)

    def test_records_of_the_run_become_messages_between_the_same_parties(self):
        self.assertEqual(durable.for_run("demo/REQ-001", self.rdir, 0), [])     # never owned by the durable runtime
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"run_id": "demo:REQ-001:r1", "backend": "dbos"}))
        events = durable.for_run("demo/REQ-001", self.rdir, 0)
        self.assertEqual([(e["from"], e["to"], e["kind"]) for e in events],
                         [("M2", "M1", "assignment"), ("M1", "M3", "execution_started"), ("M5", "M1", "recovery"),
                          ("M1", "owner", "recommendation"), ("owner", "M1", "manual_resolution"),
                          ("M1", "M1", "unknown")])                # another run's records stay out; an unknown one stays in
        self.assertEqual({e["task"] for e in events}, {"T1"})
        self.assertEqual(events[1]["attempt"], "demo-REQ-001-r1-T1-a1-0123abcd")
        self.assertIn("T1 → codex:luis:gpt", events[0]["summary"])
        self.assertIn("necesita tu decisión", events[3]["summary"])
        later = durable.for_run("demo/REQ-001", self.rdir, events[3]["ref"]["id"])   # the cursor is the line number
        self.assertEqual([e["kind"] for e in later], ["manual_resolution", "unknown"])
        self.assertEqual(bus.sources(self.rdir, "demo")["dbos"][0], str(self.root / ".state" / "durable" / "telemetry.jsonl"))


class SubplanScope(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.rdir, self.db = fb.make_run(self.root)
        plan = {"schema_version": "1.3.0", "plan_id": "REQ-001", "revision": 1,
                "subplans": [{"id": "SP-1"}, {"id": "SP-2"}],
                "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2"], "task": "G1"}],
                "tasks": [{"id": "T1", "subplan_id": "SP-1"}, {"id": "T2", "subplan_id": "SP-2"}, {"id": "G1"}]}
        (self.rdir / "PLAN.json").write_text(json.dumps(plan), encoding="utf-8")

    def test_a_subplan_scope_is_its_tasks_and_the_gates_that_compose_it(self):
        self.assertEqual(live.parse_scope("subplan:demo/REQ-001/SP-1"), ("subplan", "demo", "REQ-001", "SP-1"))
        self.assertEqual(live.scope_tasks(self.rdir, "subplan:demo/REQ-001/SP-1"), {"T1", "G1"})
        self.assertEqual(live.scope_tasks(self.rdir, "task:demo/REQ-001/T2"), {"T2"})
        self.assertIsNone(live.scope_tasks(self.rdir, "run:demo/REQ-001"))
        with patch.object(live, "runs", return_value=[("demo", self.rdir)]):
            mine, _, _ = live.flow_events(self.root, "subplan:demo/REQ-001/SP-1")
            other, _, _ = live.flow_events(self.root, "subplan:demo/REQ-001/SP-2")
            whole, _, _ = live.flow_events(self.root, "run:demo/REQ-001")
        self.assertTrue(mine)
        self.assertEqual({e["task"] for e in mine}, {"T1"})                  # the fixture's messages are about T1
        self.assertEqual(other, [])
        self.assertGreater(len(whole), len(mine))                          # run-level messages stay out of a subplan


class EmbeddedPage(unittest.TestCase):
    def test_the_embedded_flow_has_no_page_chrome_and_keeps_its_scope(self):
        page = bt_page_flow.flow_page("subplan:demo/REQ-001/SP-2", "demo/REQ-001", "tok", embed=True)
        self.assertIn('<body class="flow-embed">', page)
        self.assertIn('data-scope="subplan:demo/REQ-001/SP-2"', page)
        self.assertNotIn('class="flow-embed"', bt_page_flow.flow_page("run:demo/REQ-001", "demo/REQ-001", "tok"))


ROW = {"subplan_id": "SP-2", "attempts": 1, "after": [], "complexity": "low", "attempt": None, "history": []}


class RunFrame(unittest.TestCase):
    setUp = control.ControlTests.setUp
    write_plan = control.ControlTests.write_plan
    create = control.ControlTests.create
    finish = control.ControlTests.finish
    spec = control.ControlTests.spec
    page = control.ControlTests.page
    started = control.ControlTests.started

    def test_the_subplans_execution_frames_its_flow_once_it_is_in_the_run(self):
        self.spec("location given")
        self.started()
        self.assertNotIn("pp-flowtop", self.page(sp="SP-2", view="run"))   # not in a run yet: nothing to show
        run = {"run": {"status": "running"}, "decisions": [], "milestones": [{"tasks": [
            {**ROW, "id": "T2", "state": "completed", "title": "Design"},
            {**ROW, "id": "T3", "state": "running", "title": "Build", "after": ["T2"]}]}]}
        with patch("bt_page_planning_run._status", return_value=run):
            html = self.page(sp="SP-2", view="run")
        block = html.split('<details class="pp-flowtop"')[1].split("</details>")[0]
        self.assertIn('data-k="flowtop-SP-2"', block)
        self.assertIn(" open>", block.split(">")[0] + ">")                 # open by default; the page remembers a close
        self.assertIn('src="/flow?scope=subplan%3Ademo%2FREQ-001%2FSP-2&amp;embed=1"', block)
        self.assertIn("Abrir en su página", block)
        # full width above the plan's columns: never inside the subplan detail, where it was cramped or buried
        self.assertLess(html.index('class="pp-flowtop"'), html.index('class="pp-grid"'))
        self.assertNotIn("pp-flowtop", html.split('class="pp-detail"')[1])
        self.assertNotIn("pp-flowtop", self.page(sp="SP-2", view="tasks"))   # only while «Ejecución» is open
        # each task is one line; its full detail opens in a modal (SP-3's fifteen detailed tasks ran to 13,000 px)
        row = html.split('<div class="pp-trow">')[1].split("<dialog")[0]
        self.assertIn('data-open="tdlg-T2"', row)
        self.assertNotIn('class="task"', row)
        dialog = html.split('<dialog id="tdlg-T2"')[1].split("</dialog>")[0]
        self.assertIn('class="task"', dialog)
        self.assertIn("data-close", dialog)


if __name__ == "__main__":
    unittest.main()
