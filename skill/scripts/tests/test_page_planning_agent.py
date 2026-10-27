import unittest
from pathlib import Path
from unittest.mock import patch

import bt_page_planning_agent as agent

NOW = 10_000.0


def session(**kw):
    base = {"session": "4328eaaa", "project": "pictures", "agent": "claude", "state": "idle", "quiet": False,
            "last_event_at": NOW - 3500, "last_tool": "Bash", "activity": "planning", "req": "REQ-021",
            "req_project": "pictures", "steps": [{"at": NOW - 3500, "text": "Terminó su turno y espera"},
                                                 {"at": NOW - 3600, "text": "Write PLAN.json skeleton"}]}
    return {**base, **kw}


def ctx(focus="SP-1"):
    return {"project": "pictures", "rid": "REQ-021", "root": Path("/nowhere"), "rdir": Path("/nowhere/REQ-021-x"),
            "token": "tok", "opts": {"sp": ""}, "flow": {"focus": focus}}


class AgentStrip(unittest.TestCase):
    def render(self, *sessions, **kw):
        with patch("bt_presence.sessions", return_value=list(sessions)), patch("bt_agent_terminal.exists", return_value=False):
            return agent.strip(ctx(**kw), NOW)

    def test_the_strip_follows_the_planners_own_conversation_not_any_agent_that_ran_a_planning_command(self):
        import json
        import tempfile
        other = session(session="d05f524b", state="working", last_event_at=NOW - 2, steps=[{"at": NOW - 2, "text": "Run tests"}])
        planner = session(session="0bce6e53")
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp)
            (rdir / ".planning").mkdir()
            (rdir / ".planning" / "planner.json").write_text(json.dumps({"session_id": "0bce6e53-7937-47b3-87f8-f5c34d17fa5d"}))
            with patch("bt_presence.sessions", return_value=[other, planner]), patch("bt_agent_terminal.exists", return_value=False):
                html = agent.strip({**ctx(), "rdir": rdir}, NOW)
        self.assertIn("Esperando · inactivo", html)
        self.assertNotIn("Run tests", html)
        self.assertNotIn("Trabajando", html)

    def test_a_planner_opened_from_the_web_without_signals_yet_is_not_reported_absent(self):
        with patch("bt_presence.sessions", return_value=[]), patch("bt_agent_terminal.exists", return_value=True), \
                patch("bt_agent_terminal.screen", return_value="leyendo"):
            html = agent.strip(ctx(), NOW)
        self.assertIn("Planner abierto desde la web", html)
        self.assertNotIn("Ningún agente", html)

    def test_no_agent_says_so_and_how_to_wake_one(self):
        html = self.render()
        self.assertIn("Ningún agente está planificando", html)
        self.assertIn("agent-start", html)

    def test_other_requirements_and_non_planning_sessions_are_ignored(self):
        html = self.render(session(req="REQ-020"), session(activity="verify"), session(req_project="maros"))
        self.assertIn("Ningún agente", html)

    def test_an_idle_agent_explains_that_the_focus_label_is_not_work(self):
        html = self.render(session())
        self.assertIn("Esperando · inactivo hace 58 min", html)
        self.assertIn("escríbele en su ventana", html)
        self.assertIn("Pasos (2)", html)
        self.assertIn("Write PLAN.json skeleton", html)
        self.assertEqual(html.count("<details"), 1)              # one slim line: the steps are a floating menu, not a block

    def test_a_working_agent_shows_its_latest_step_and_no_warning(self):
        html = self.render(session(state="working", last_event_at=NOW - 3,
                                   steps=[{"at": NOW - 3, "text": "Escribió SPEC.md"}]))
        self.assertIn("Trabajando", html)
        self.assertIn("Escribió SPEC.md", html)
        self.assertNotIn("escríbele", html)

    def test_a_working_session_that_went_quiet_is_flagged(self):
        self.assertIn("Sin señales hace 5 min", self.render(session(state="working", quiet=True, last_event_at=NOW - 300)))

    def test_times_are_rounded_so_the_live_block_does_not_churn(self):
        self.assertEqual(agent._ago(3), "hace menos de 1 min")
        self.assertEqual(agent._ago(47), "hace menos de 1 min")
        self.assertEqual(agent._ago(3500), "hace 58 min")
        self.assertEqual(agent._ago(8000), "hace 2 h")


if __name__ == "__main__":
    unittest.main()
