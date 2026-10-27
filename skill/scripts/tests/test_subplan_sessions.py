import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import unquote

import bt_subplan_sessions as sessions

SPEC = """# REQ-9 — demo

## Requirements
- R1. When a user adds a rectangular table, the system shall set size and chairs.
- R2. Something else entirely.
"""
PLAN = {"milestones": [{"id": "M1", "title": "One", "goal": "g"}],
        "subplans": [{"id": "SP-1", "milestone_id": "M1", "title": "Tables", "outcome": "A user adds a rectangular table.",
                      "covers": ["R1"], "acceptance_criteria": ["The shopping list shows the table."]},
                     {"id": "SP-2", "milestone_id": "M1", "title": "Backing", "outcome": "One category.", "covers": ["R2"],
                      "acceptance_criteria": ["Backing lists the props."]},
                     {"id": "SP-3", "milestone_id": "M1", "title": "Export", "outcome": "Blender.", "covers": [],
                      "acceptance_criteria": ["GLB opens."]}],
        "tasks": [{"id": "T1.2", "title": "Second", "subplan_id": "SP-1", "kind": "test", "after": ["T1.1"],
                   "acceptance_criteria": ["ok"], "verification": [{"type": "command", "value": "npm test -- tables", "purpose": "tables pass"}]},
                  {"id": "T1.1", "title": "First", "objective": "Build the table form.", "subplan_id": "SP-1", "kind": "implement",
                   "expected_paths": ["src/tables"], "acceptance_criteria": ["The form renders."], "verification": []},
                  {"id": "T2.1", "title": "t", "subplan_id": "SP-2", "kind": "implement", "acceptance_criteria": ["ok"]}]}


def git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True).stdout.strip()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "bitacora"
        self.rdir = self.root / "proj" / "requirements" / "REQ-009-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text(SPEC, encoding="utf-8")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
        origin, self.clone = Path(self.tmp.name) / "origin.git", Path(self.tmp.name) / "code"
        subprocess.run(["git", "init", "--bare", "-b", "main", str(origin)], capture_output=True, check=True)
        subprocess.run(["git", "clone", str(origin), str(self.clone)], capture_output=True, check=True)
        (self.clone / "a.txt").write_text("one\n")
        git(self.clone, "add", "."), git(self.clone, "commit", "-m", "first")
        git(self.clone, "push", "origin", "HEAD:main")
        git(self.clone, "fetch", "origin")
        (self.root / "proj" / "project.json").write_text(json.dumps({"repos": {"app": {"remote": "", "hint": str(self.clone)}}}))
        env = patch.dict(os.environ, {"BITACORA_SESSIONS_DIR": str(Path(self.tmp.name) / "sessions"),
                                      "BITACORA_WS_LOCAL": ""})
        env.start()
        self.addCleanup(env.stop)
        self.alive = set()
        for target, effect in (("bt_subplan_sessions.launch_agent", AssertionError("a test started a real agent")),
                               ("bt_agent_terminal.start", AssertionError("a test started a real tmux session"))):
            guard = patch(target, side_effect=effect)
            guard.start()
            self.addCleanup(guard.stop)
        alive = patch("bt_agent_terminal.exists", side_effect=lambda n: n in self.alive)
        alive.start()
        self.addCleanup(alive.stop)
        self.calls = []

    def launcher(self, worktree, name, prompt_file, model, effort):
        self.calls.append((worktree, name, Path(prompt_file).read_text(encoding="utf-8"), model, effort))
        self.alive.add(name)
        return name


class Sessions(Base):
    def test_start_opens_a_worktree_on_its_own_branch_and_tells_the_agent_what_to_build(self):
        ok, msg = sessions.start(self.root, "proj", self.rdir, "SP-1", "opus", launcher=self.launcher)
        self.assertTrue(ok, msg)
        worktree, title, text, model, effort = self.calls[0]
        self.assertEqual((model, effort), ("opus", "high"))
        self.assertEqual(git(worktree, "rev-parse", "--abbrev-ref", "HEAD"), "session/req-009-sp-1")
        self.assertEqual(git(worktree, "rev-parse", "HEAD"), git(self.clone, "rev-parse", "origin/main"))
        self.assertNotIn(str(self.clone), str(worktree))                       # outside every repository
        for expected in ("subplan SP-1", "A user adds a rectangular table.", "The shopping list shows the table.",
                         "R1. When a user adds a rectangular table", "Do not push, merge", "sessions finish REQ-009 SP-1"):
            self.assertIn(expected, text)
        self.assertNotIn("Something else entirely", text)                      # only the requirements it covers
        row = sessions.active(self.rdir, "SP-1")
        self.assertEqual((row["status"], row["branch"]), ("running", "session/req-009-sp-1"))

    def test_autonomous_execution_is_the_schedulers_now(self):  # D-134
        ok, msg = sessions.start(self.root, "proj", self.rdir, "SP-1", "sonnet", "auto", launcher=self.launcher)
        self.assertFalse(ok)
        self.assertIn("SESSION_AUTO_SUPERSEDED", msg)
        self.assertIn("stage run REQ-009 SP-1", msg)
        self.assertEqual(self.calls, [])
        self.assertTrue(sessions.start(self.root, "proj", self.rdir, "SP-3", "sonnet", "hands", launcher=self.launcher)[0])

    def test_a_second_session_is_refused_while_the_window_lives_and_allowed_when_it_is_gone(self):
        sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=self.launcher)
        ok, msg = sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=self.launcher)
        self.assertFalse(ok)
        self.assertIn("Ya hay una sesión en marcha", msg)
        self.alive.clear()                                                     # the agent's tmux session is gone
        ok, msg = sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=self.launcher)
        self.assertTrue(ok, msg)
        self.assertEqual([s["status"] for s in sessions.sessions(self.rdir, "SP-1")], ["closed", "running"])
        self.assertTrue(sessions.active(self.rdir, "SP-1")["branch"].endswith("sp-1-2"))

    def test_finish_records_the_branch_head_and_what_was_left_uncommitted(self):
        sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=self.launcher)
        worktree = Path(self.calls[0][0])
        (worktree / "table.txt").write_text("rect\n")
        git(worktree, "add", "."), git(worktree, "commit", "-m", "rectangular table")
        (worktree / "wip.txt").write_text("not committed\n")
        msg = sessions.finish(self.rdir, "SP-1")
        self.assertIn("1 commit(s)", msg)
        self.assertIn("1 archivo(s) sin commit", msg)
        row = sessions.sessions(self.rdir, "SP-1")[0]
        self.assertEqual((row["status"], row["commits"], row["head"]), ("finished", 1, git(worktree, "rev-parse", "HEAD")))
        self.assertIn("no tiene una sesión en marcha", sessions.finish(self.rdir, "SP-1"))

    def test_a_window_that_cannot_open_keeps_the_worktree_and_records_nothing(self):
        def broken(*args):
            raise RuntimeError("sin escritorio")
        ok, msg = sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=broken)
        self.assertFalse(ok)
        self.assertIn("sin escritorio", msg)
        self.assertEqual(sessions.sessions(self.rdir), [])

    def test_unknown_or_unsafe_subplans_are_refused(self):
        for sid in ("SP-9", "../x", ""):
            self.assertFalse(sessions.start(self.root, "proj", self.rdir, sid, launcher=self.launcher)[0])
        self.assertEqual(self.calls, [])


class SessionsWeb(Base):
    def ctx(self):
        return {"project": "proj", "rid": "REQ-009", "rdir": self.rdir, "token": "tok", "root": self.root, "opts": {"lang": "en"}}

    def test_the_tab_offers_to_open_then_to_finish_and_lists_the_history(self):
        import bt_page_sessions as page
        sub = {"id": "SP-1"}
        html = page.panel(self.ctx(), sub)
        self.assertIn("session-start", html)
        self.assertIn("Opus 5.5 · high", html)
        self.assertIn("confírmalo y pulsa «Ejecutar subplan»", html)
        self.assertNotIn("name=mode value=auto", html)
        self.assertIn("name=mode value=hands", html)
        self.assertIn("Trabajar contigo", html)
        self.assertIn("Esta sesión no es el Scheduler", html)
        self.assertEqual(page.tab_label(self.rdir, "SP-1"), "Sesión")
        sessions.start(self.root, "proj", self.rdir, "SP-1", launcher=self.launcher)
        html = page.panel(self.ctx(), sub)
        self.assertIn("session-finish", html)
        self.assertNotIn("session-start", html)
        self.assertIn("session/req-009-sp-1", html)
        self.assertNotIn("Ejecutar el subplan", html)
        self.assertEqual(page.tab_label(self.rdir, "SP-1"), "Sesión · en marcha")
        sessions.finish(self.rdir, "SP-1")
        self.assertIn("Terminada", page.panel(self.ctx(), sub))
        self.assertEqual(page.tab_label(self.rdir, "SP-1"), "Sesión ✓")

    def test_the_server_action_only_accepts_loopback_and_valid_ids(self):
        import bt_server
        stub = SimpleNamespace(client_address=("203.0.113.9", 5000))
        call = lambda s, sid, action="session-start": bt_server.Handler.session_post(  # noqa: E731
            s, "proj", "REQ-009", self.rdir, action, {"anchor": sid, "model": "opus"}, "/p/proj/req/REQ-009")
        with patch.object(bt_server, "ROOT", self.root), patch("bt_subplan_sessions.start") as start:
            self.assertIn("solo se abren desde esta máquina", unquote(call(stub, "SP-1")))
            local = SimpleNamespace(client_address=("127.0.0.1", 5000))
            start.return_value = (True, "abierta")
            self.assertIn("msg=abierta", call(local, "SP-1"))
            start.assert_called_once_with(self.root, "proj", self.rdir, "SP-1", "opus", "hands")
            self.assertIn("Subplan no válido", unquote(call(local, "../x")))

    def test_the_cli_starts_lists_and_finishes(self):
        import bt_cli_sessions
        args = lambda **kw: SimpleNamespace(req="REQ-009", subplan="SP-1", model="sonnet", mode="hands", **kw)  # noqa: E731
        with patch("bt_subplan_sessions.launch_agent", self.launcher):      # replaces the guard for this call
            self.assertEqual(bt_cli_sessions.dispatch(args(action="start"), self.root, "proj"), 0)
            self.assertEqual(bt_cli_sessions.dispatch(args(action="finish"), self.root, "proj"), 0)
        self.assertEqual(sessions.sessions(self.rdir, "SP-1")[0]["status"], "finished")


if __name__ == "__main__":
    unittest.main()
