"""Shared run hashing and provider argument contracts."""
import unittest
from pathlib import Path
from unittest.mock import patch
from run_case_support import rs

class Units(unittest.TestCase):
    def test_error_hash_ignores_numbers_and_paths(self):
        self.assertEqual(rs.error_hash("boom 42 in C:\\x\\y 0xdeadbeef"), rs.error_hash("boom 7 in D:\\z 0xabcdef12"))
        self.assertNotEqual(rs.error_hash("boom"), rs.error_hash("bang"))

    def test_agent_argv(self):
        import bt_runprompt as rp
        argv, stdin = rp.agent_argv({"agent": "claude", "model": "haiku"}, Path("."), "PROMPT")
        self.assertEqual((argv[1:4], argv[-1], stdin), (["-p", "--model", "haiku"], "PROMPT", None))
        self.assertNotIn("--effort", argv)
        self.assertIn("stream-json", argv)
        argv, _ = rp.agent_argv({"agent": "claude", "model": "haiku"}, Path("."), "PROMPT", "opus", "xhigh")
        self.assertEqual(argv[1:6], ["-p", "--model", "opus", "--effort", "xhigh"])
        argv, stdin = rp.agent_argv({"agent": "codex", "model": "haiku"}, Path("."), "PROMPT")
        self.assertEqual((argv[1], argv[-1], stdin, "-m" in argv, "-c" in argv), ("exec", "-", "PROMPT", False, False))
        argv, _ = rp.agent_argv({"agent": "codex", "model": "gpt-5"}, Path("."), "PROMPT", "gpt-5", "xhigh")
        self.assertEqual(argv[-5:], ["-m", "gpt-5", "-c", 'model_reasoning_effort="xhigh"', "-"])

    def test_marathon_delegate_hint_includes_design_and_designer(self):
        import bt_runprompt as rp
        with patch("bt_agents.brief", return_value=""):
            team = "\n".join(rp._team("test-project"))
        self.assertIn("--kind implement|test|docs|audit|research|design", team)
        self.assertIn("|designer|", team)
