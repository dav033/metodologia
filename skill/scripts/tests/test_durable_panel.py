"""The run panel shows the Solucionador (REQ-031 US-6): the session at work (task, trigger, since, its tmux name), the
last ones with their outcome, the owner's question and the report, and what waits. Read from `RUN.solver/state.json`,
which the engine writes; every text is escaped (it comes from agents)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_durable_panel
import bt_page_planning_run
import bt_page_solver


class SolverCard(unittest.TestCase):
    def setUp(self):
        self.rdir = Path(tempfile.mkdtemp(prefix="bt-solver-panel-")) / "pictures" / "requirements" / "REQ-021-x"
        (self.rdir / "RUN.solver" / "s1").mkdir(parents=True)
        (self.rdir / "RUN.solver" / "s1" / "REPORT.md").write_text("# report\n")
        state = {"active": "s2", "sessions": [
            {"id": "s1", "name": "bit-pictures-REQ-021-solver", "status": "asked_owner", "task": "T93",
             "kind": "repeat", "started_at": "2026-10-29T19:00:00", "ended_at": "2026-10-29T19:40:00",
             "summary": "necesita una clave", "question": "¿Me das <la clave> de Stripe?"},
            {"id": "s2", "name": "bit-pictures-REQ-021-solver", "status": "running", "task": "T95", "kind": "stuck",
             "reason": "state routing unchanged", "started_at": "2026-10-29T19:45:00", "provider": "claude",
             "model": "opus"}],
            "triggers": {"a": {"status": "queued"}, "b": {"status": "pending"}, "c": {"status": "limit"},
                         "d": {"status": "fixed"}}}
        (self.rdir / "RUN.solver" / "state.json").write_text(json.dumps(state))

    def test_the_state_the_panel_reads(self):
        state = bt_durable_panel.solver_state(self.rdir)
        self.assertEqual(state["active"]["task"], "T95")
        self.assertEqual([s["id"] for s in state["recent"]], ["s1"])
        self.assertEqual(state["recent"][0]["report_url"],
                         "/p/pictures/doc/requirements/REQ-021-x/RUN.solver/s1/REPORT.md")
        self.assertEqual((state["waiting"], state["left"]), (2, 1))
        self.assertIsNone(bt_durable_panel.solver_state(self.rdir.parent / "REQ-999-none"))

    def test_the_card_shows_the_session_its_question_and_report_escaped(self):
        html = bt_page_solver.card(bt_durable_panel.solver_state(self.rdir), "bitacora")
        for text in ("Solucionador", "T95", "tarea sin avance", "desde 19:45",
                     "tmux -L bitacora attach -t bit-pictures-REQ-021-solver", "te pregunta",
                     "¿Me das &lt;la clave&gt; de Stripe?", 'href="/p/pictures/doc/requirements/REQ-021-x/RUN.solver/s1/'
                     'REPORT.md"', "2 aviso(s) esperan", "1 caso(s) quedaron para ti"):
            self.assertIn(text, html)
        self.assertNotIn("<la clave>", html)
        self.assertEqual(bt_page_solver.card(None), "")

    def test_the_subplan_run_tab_carries_it_with_the_other_run_tools(self):
        status = {"solver": bt_durable_panel.solver_state(self.rdir), "decisions": []}
        html = bt_page_planning_run._run_tools({}, status, "/plans/pictures/REQ-021", "tok", "/back")
        self.assertIn("Solucionador</summary>", html)
        self.assertIn('id="solver"', html)


if __name__ == "__main__":
    unittest.main()
