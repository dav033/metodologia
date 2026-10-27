import datetime as dt
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_agent_health as health
import bt_delegate

NOW = time.time()


class Delegations(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.object(bt_delegate, "DIR", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def make(self, did, *, claimed=None, outcome=None, log_age=10, task="Planning-time UI/UX design for subplan SP-2 of REQ-021",
             created_ago=600, role="designer"):
        d = Path(self.tmp.name) / did
        d.mkdir()
        (d / "TASK.json").write_text(json.dumps({
            "id": did, "role": role, "task": task, "project": "pictures", "workdir": "/x/REQ-021-demo", "profile": "codex-1",
            "model": "gpt-6.1-sol", "created": dt.datetime.fromtimestamp(NOW - created_ago).astimezone().isoformat()}))
        (d / "session.log").write_text("x")
        os.utime(d / "session.log", (NOW - log_age, NOW - log_age))
        if claimed is not None:
            (d / "CLAIMED").write_text(str(claimed))
        if outcome:
            (d / "OUTCOME.json").write_text(json.dumps(outcome))
        return d

    def by_state(self):
        return {a["id"]: a["state"] for a in health.delegations(NOW)}

    def test_each_delegation_is_classified_by_what_its_process_and_log_say(self):
        self.make("D-9-alive", task="job D-9-alive", claimed=os.getpid(), log_age=30)
        self.make("D-8-quiet", task="job D-8-quiet", claimed=os.getpid(), log_age=health.QUIET_S + 60)
        self.make("D-7-died", task="job D-7-died", claimed=2 ** 22 + 99)
        self.make("D-6-never", task="job D-6-never", created_ago=health.NEVER_STARTED_S + 60)
        self.make("D-5-fresh-unclaimed", task="job D-5-fresh-unclaimed", created_ago=30)
        self.make("D-4-done", task="job D-4-done", claimed=1, outcome={"status": "verified"})
        self.assertEqual(self.by_state(), {"D-9-alive": "working", "D-8-quiet": "quiet", "D-7-died": "died", "D-6-never": "never_started"})

    def test_a_newer_live_run_of_the_same_task_hides_the_dead_one_and_old_runs_are_ignored(self):
        self.make("D-1-died", claimed=2 ** 22 + 99)
        self.make("D-2-retry", claimed=os.getpid())                      # newer, alive, same task
        self.make("D-0-ancient", claimed=2 ** 22 + 98, task="old job", log_age=health.STALE_S + 60)
        self.assertEqual(self.by_state(), {"D-2-retry": "working"})

    def test_a_failure_shows_until_a_newer_run_of_the_same_task_succeeds(self):
        self.make("D-2-fail", claimed=1, outcome={"status": "failed", "summary": "codex crashed"})
        self.assertEqual(self.by_state(), {"D-2-fail": "failed"})
        self.make("D-3-retry", claimed=1, outcome={"status": "claimed"})      # newer (sorted later), same task: the retry worked
        self.assertEqual(self.by_state(), {})

    def test_problems_can_be_filtered_by_requirement_and_worst_come_first(self):
        self.make("D-1-quiet", claimed=os.getpid(), log_age=health.QUIET_S + 60)
        self.make("D-2-died", claimed=2 ** 22 + 99, role="implementer", task="another job")
        with patch("bt_agent_health.tmux_agents", return_value=[]):
            rows = health.problems(NOW)
            self.assertEqual([r["state"] for r in rows], ["died", "quiet"])
            mine = health.problems(NOW, req="REQ-021", project="pictures")
            self.assertEqual({r["req"] for r in mine}, {"REQ-021"})
            self.assertEqual(health.active_for("REQ-021", "pictures", NOW)[0]["state"], "quiet")

    def test_the_designer_label_carries_the_subplan(self):
        self.make("D-1", claimed=os.getpid())
        self.assertEqual(health.delegations(NOW)[0]["who"], "Designer SP-2")


class Pages(unittest.TestCase):
    def test_the_now_page_and_bar_show_problems_and_stay_quiet_when_all_is_well(self):
        import bt_page_now
        bad = {"id": "D-1", "kind": "delegation", "who": "Designer SP-2", "project": "pictures", "req": "REQ-021",
               "state": "died", "since": 600.0, "detail": "su proceso desapareció", "model": "codex-1 gpt-6.1-sol"}
        html = bt_page_now.health_html([bad])
        self.assertIn("murió", html)
        self.assertIn("Designer SP-2", html)
        self.assertIn("hace 10 min", html)
        self.assertIn("Todos los agentes", bt_page_now.health_html([]))
        self.assertIn("⚠ Designer SP-2 murió", bt_page_now.bar_html([], [], [], [bad]))
        self.assertEqual(bt_page_now.bar_html([], [], [], []), "")
        self.assertIn("now-health", bt_page_now.now_page([], [], [], [bad]))

    def test_the_plan_tab_names_the_dead_designer_of_its_requirement(self):
        import bt_page_planning_agent as view
        died = {"id": "D-1", "kind": "delegation", "who": "Designer SP-2", "project": "pictures", "req": "REQ-021",
                "state": "died", "since": 300.0, "detail": "su proceso desapareció", "model": ""}
        other = {**died, "id": "D-2", "req": "REQ-020", "who": "Designer SP-9"}
        ctx = {"project": "pictures", "rid": "REQ-021", "rdir": Path("/nowhere/REQ-021-x"), "root": Path("/nowhere"),
               "token": "t", "opts": {"sp": ""}, "flow": {"focus": "SP-2"}}
        with patch("bt_agent_health.agents", return_value=[died, other]), patch("bt_presence.sessions", return_value=[]), \
                patch("bt_agent_terminal.exists", return_value=False):
            html = view.strip(ctx, NOW)
        self.assertIn("Designer SP-2 · murió hace 5 min", html)
        self.assertNotIn("SP-9", html)


if __name__ == "__main__":
    unittest.main()


class Activity(unittest.TestCase):
    CODEX = """OpenAI Codex v0.164.0
user
do the design
codex
Aye, mantendré los tokens lila y los temas claro/oscuro de Pictures.
exec
/usr/bin/bash -lc "sed -n '70,84p' /x/PLAN.md"
 succeeded in 0ms:
apply patch
patch: completed
/x/design/cuentas-admin@v1.md
diff --git a/x b/x
exec
/usr/bin/bash -lc "cat > /x/design/cuentas-admin@v1.html <<'HTML'
<html>
codex
Aye, ambos archivos están escritos. Ahora comprobaré el mockup en Chromium.
hook: PostToolUse
"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.object(bt_delegate, "DIR", Path(self.tmp.name))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_a_codex_log_becomes_readable_steps_newest_first(self):
        d = Path(self.tmp.name) / "D-1"
        d.mkdir()
        (d / "session.log").write_text(self.CODEX)
        steps = health.activity("D-1", 6)
        self.assertEqual(steps[0], "Aye, ambos archivos están escritos. Ahora comprobaré el mockup en Chromium.")
        self.assertEqual(steps[1], "Escribe cuentas-admin@v1.html")
        self.assertEqual(steps[2], "Edita cuentas-admin@v1.md")
        self.assertEqual(steps[3], "Lee PLAN.md")
        self.assertEqual(health._command_summary("/usr/bin/bash -lc \"node <<'JS'\nconsole.log(1)\""), "Ejecuta un script (node)")

    def test_a_claude_stream_shows_its_tool_calls_and_bad_logs_give_nothing(self):
        d = Path(self.tmp.name) / "D-2"
        d.mkdir()
        event = {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Edit", "input": {"file_path": "/a/b.py"}}]}}
        (d / "session.log").write_text("{not json\n" + json.dumps(event) + "\n")
        self.assertEqual(health.activity("D-2"), ["Edit: /a/b.py"])
        self.assertEqual(health.activity("D-404"), [])


class DesignerProgress(unittest.TestCase):
    def ctx(self, tmp):
        return {"rdir": Path(tmp), "project": "pictures", "rid": "REQ-021"}

    def render(self, state, tmp, steps=("Escribe x.html",)):
        import bt_page_planning_views as views
        row = {"ref": "cuentas@v1", "delegation": "D-1", "reason": "focus"}
        with patch("bt_agent_health.one", return_value=state), patch("bt_agent_health.activity", return_value=list(steps)):
            return views._designer_progress(self.ctx(tmp), row)

    def test_it_says_whether_the_designer_works_thinks_or_died_and_lists_what_it_wrote(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "design").mkdir()
            (Path(tmp) / "design" / "cuentas@v1.md").write_text("# c\n" * 300)
            with patch("bt_design_drafts.paths", return_value=(Path(tmp) / "design" / "cuentas@v1.md", Path(tmp) / "design" / "cuentas@v1.html")):
                working = self.render({"state": "working", "age": 420, "since": 12, "detail": "activo"}, tmp)
                self.assertIn("Designer trabajando · lleva 7 min · última señal hace menos de 1 min", working)
                self.assertIn("✓ Contrato", working)
                self.assertIn("○ Mockup", working)
                self.assertIn("Escribe x.html", working)
                self.assertIn("quiet", self.render({"state": "quiet", "since": 1200, "detail": ""}, tmp).replace("wait", "quiet"))
                died = self.render({"state": "died", "since": 300, "detail": "su proceso desapareció"}, tmp)
                self.assertIn("murió hace 5 min", died)
                self.assertIn("pp-ag-dot bad", died)
                self.assertIn("Registrando el resultado", self.render(None, tmp))
