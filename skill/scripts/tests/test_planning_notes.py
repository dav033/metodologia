import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_agent_terminal as terminal
import bt_planning_notes as notes


class Notes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name) / "REQ-021-demo"
        self.rdir.mkdir()

    def test_notes_are_appended_validated_and_rendered_with_the_handoff_first(self):
        self.assertEqual(notes.render(self.rdir), [])
        notes.add(self.rdir, "Login lives in src/proxy.ts:25  and\tcookies", "finding")
        notes.add(self.rdir, "Chose invitation links: no mail service", "decision")
        notes.add(self.rdir, "Was about to define SP-1 inputs", "handoff")
        lines = notes.render(self.rdir)
        self.assertIn("3 saved", lines[0])
        self.assertTrue(lines[1].startswith("- HANDOFF"))
        self.assertIn("Login lives in src/proxy.ts:25 and cookies", "\n".join(lines))
        self.assertEqual(sum("Was about to define" in line for line in lines), 1)   # the handoff is not repeated
        with self.assertRaises(SystemExit):
            notes.add(self.rdir, "x", "gossip")
        with self.assertRaises(SystemExit):
            notes.add(self.rdir, "   ")

    def test_a_corrupt_line_is_skipped_and_long_text_is_cut(self):
        notes.add(self.rdir, "a" * 5000, "todo")
        with (self.rdir / ".planning" / "notes.jsonl").open("a") as f:
            f.write("{not json\n" + json.dumps({"kind": "bogus", "text": "x"}) + "\n")
        rows = notes.notes(self.rdir)
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]["text"]), notes.MAX_TEXT)

    def test_resume_prints_the_notes(self):
        import bt_planning_resume as resume
        notes.add(self.rdir, "SP-1 needs a one-time admin command", "decision")
        with patch("bt_planning_flow.state", return_value={"active": True, "phase": "subplans", "focus": "SP-1", "confirmed": 0,
                                                           "total": 1, "subplans": {"SP-1": {"state": "defining", "problems": []}},
                                                           "inputs": [], "editing": False}), \
                patch("bt_planning_resume.verification.tests_for", return_value=[{}]):
            text = resume.briefing("pictures", self.rdir)
        self.assertIn("Planner notes (1 saved", text)
        self.assertIn("SP-1 needs a one-time admin command", text)


class PlannerSession(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        home = Path(self.tmp.name) / "home"
        (home / ".claude-work").mkdir(parents=True)
        patcher = patch.dict(os.environ, {"HOME": str(home), "BITACORA_PLANNER_CLAUDE_CONFIG_DIR": str(home / ".claude-work")})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.home, self.root = home, Path(self.tmp.name) / "bitacora"
        self.rdir = self.root / "pictures" / "requirements" / "REQ-021-demo"
        self.rdir.mkdir(parents=True)
        self.started = []
        alive = patch("bt_agent_terminal.exists", return_value=False)
        alive.start()
        self.addCleanup(alive.stop)
        fake = patch("bt_agent_terminal.start", side_effect=lambda name, cwd, command, env=None: self.started.append((name, command, env)))
        fake.start()
        self.addCleanup(fake.stop)

    def test_the_first_start_pins_a_session_id_and_the_next_one_resumes_that_conversation(self):
        ok, msg = terminal.start_planner(self.root, "pictures", self.rdir)
        self.assertTrue(ok, msg)
        record = json.loads((self.rdir / ".planning" / "planner.json").read_text())
        sid = record["session_id"]
        self.assertIn(f"--session-id {sid}", self.started[0][1])
        self.assertIn("nueva", msg)
        # the conversation exists on disk: starting again resumes it instead of starting from zero
        log = terminal.transcript(record["config_dir"], record["cwd"], sid)
        log.parent.mkdir(parents=True)
        log.write_text("{}\n")
        ok, msg = terminal.start_planner(self.root, "pictures", self.rdir)
        self.assertTrue(ok, msg)
        self.assertIn(f"--resume {sid}", self.started[1][1])
        self.assertNotIn("--session-id", self.started[1][1])
        self.assertIn("retomó su conversación anterior", msg)
        ok, msg = terminal.start_planner(self.root, "pictures", self.rdir, fresh=True)
        self.assertIn("--session-id", self.started[2][1])
        self.assertNotEqual(json.loads((self.rdir / ".planning" / "planner.json").read_text())["session_id"], sid)

    def test_a_lost_transcript_falls_back_to_a_new_conversation_with_the_notes(self):
        terminal.remember_planner(self.rdir, "11111111-1111-1111-1111-111111111111", str(self.home / ".claude-work"), str(self.root))
        ok, msg = terminal.start_planner(self.root, "pictures", self.rdir)
        self.assertTrue(ok)
        self.assertIn("--session-id", self.started[0][1])
        self.assertIn("planning resume", Path(self.home / ".local/share/bitacora-sessions/pictures/bit-pictures-REQ-021-planner.prompt.md").read_text())

    def test_restart_needs_a_known_conversation_and_kills_before_starting(self):
        ok, msg = terminal.restart_planner(self.root, "pictures", self.rdir)
        self.assertFalse(ok)
        self.assertIn("No sé qué conversación", msg)
        terminal.remember_planner(self.rdir, "22222222-2222-2222-2222-222222222222", str(self.home / ".claude-work"), str(self.root))
        log = terminal.transcript(str(self.home / ".claude-work"), str(self.root), "22222222-2222-2222-2222-222222222222")
        log.parent.mkdir(parents=True)
        log.write_text("{}\n")
        with patch("bt_agent_terminal.kill") as kill:
            ok, msg = terminal.restart_planner(self.root, "pictures", self.rdir)
        kill.assert_called_once_with("bit-pictures-REQ-021-planner")
        self.assertTrue(ok, msg)
        self.assertIn("--resume 22222222", self.started[0][1])

    def test_the_prompt_tells_the_planner_to_keep_its_memory_in_files(self):
        text = terminal.planner_prompt("pictures", self.rdir)
        self.assertIn("planning note REQ-021", text)
        self.assertIn("--kind handoff", text)


if __name__ == "__main__":
    unittest.main()
