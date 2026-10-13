"""Account profiles: the work gate, environment overlay and launcher/supervisor enforcement."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import bt_profiles  # noqa: E402


class ProfileGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="profiles-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "bitacora"
        for name, data in (("pictures", {"work": True}), ("personal", {"work": False}), ("untagged", {})):
            (self.root / name).mkdir(parents=True)
            (self.root / name / "project.json").write_text(json.dumps(data))
        (self.root / "noproject").mkdir()
        for target in ("bt_profiles.ROOT", "bt_profiles.STATE"):
            patcher = patch(target, self.root if target.endswith("ROOT") else self.root / ".state")
            patcher.start()
            self.addCleanup(patcher.stop)
        # machine-local accounts: the built-ins are generic, named accounts come from .state/profiles.json
        bt_profiles.add("claude-personal", "claude")
        bt_profiles.add("claude-work", "claude", {"CLAUDE_CONFIG_DIR": "~/.claude-work"}, work_only=True)
        bt_profiles.add("codex-1", "codex")
        bt_profiles.add("codex-luis", "codex", {"CODEX_HOME": "~/.codex-luis"})

    def test_claude_work_only_runs_projects_marked_work(self):
        bt_profiles.authorize("claude-work", "pictures")
        for project in ("personal", "untagged", "noproject", "missing"):
            with self.subTest(project=project), self.assertRaises(SystemExit) as ctx:
                bt_profiles.authorize("claude-work", project)
            self.assertIn("restricted to work projects", str(ctx.exception))

    def test_every_other_profile_runs_any_project(self):
        for pid in ("claude-personal", "codex-1", "codex-luis", "claude", "codex", "antigravity"):
            for project in ("pictures", "personal", "untagged", "noproject"):
                bt_profiles.authorize(pid, project)

    def test_no_profile_is_never_gated(self):
        bt_profiles.authorize(None, "personal")

    def test_unknown_profile_is_rejected(self):
        with self.assertRaises(SystemExit):
            bt_profiles.authorize("claude-nope", "pictures")

    def test_work_flag_roundtrip_keeps_other_fields(self):
        path = self.root / "personal" / "project.json"
        path.write_text(json.dumps({"root": "~/dev/x", "work": False}))
        bt_profiles.set_work("personal", True)
        self.assertTrue(bt_profiles.is_work_project("personal"))
        self.assertEqual(json.loads(path.read_text())["root"], "~/dev/x")

    def test_environment_overlay_selects_the_account_without_secrets(self):
        env = bt_profiles.env_of("claude-work")
        self.assertTrue(env["CLAUDE_CONFIG_DIR"].endswith("/.claude-work"))
        self.assertEqual(bt_profiles.env_of(None), {})
        self.assertTrue(bt_profiles.env_of("codex-luis")["CODEX_HOME"].endswith("/.codex-luis"))

    def test_local_file_overrides_and_adds_profiles(self):
        bt_profiles.add("codex-luis", "codex", {"CODEX_HOME": "~/.codex-luis"}, work_only=True)
        bt_profiles.add("extra", "claude")
        with self.assertRaises(SystemExit):
            bt_profiles.authorize("codex-luis", "personal")
        self.assertEqual(bt_profiles.provider_of("extra"), "claude")

    def test_builtins_are_machine_independent(self):
        self.assertEqual(set(bt_profiles.DEFAULTS), {"claude", "codex", "antigravity"})
        self.assertTrue(all(not spec["work_only"] and not spec["env"] for spec in bt_profiles.DEFAULTS.values()))
        with self.assertRaises(SystemExit):
            bt_profiles.add("x", "gemini")

    def test_launchable_providers_and_unknown_ones(self):
        self.assertEqual(bt_profiles.require_launchable("codex-luis"), "codex")
        self.assertEqual(bt_profiles.require_launchable("antigravity"), "antigravity")
        with patch.object(bt_profiles, "LAUNCHABLE", ("claude",)), self.assertRaises(SystemExit):
            bt_profiles.require_launchable("antigravity")


class WorkGateLauncherTests(ProfileGateTests):
    """Same fixtures; the gate resolves the current folder to a project."""

    def _with_project(self, project):
        return patch.object(bt_profiles.ws, "project_for_path", return_value=project)

    def test_work_only_profile_needs_a_work_project_folder(self):
        with self._with_project("pictures"):
            self.assertEqual(bt_profiles.gate_cwd("claude-work", "/x/pictures"), (True, ""))
        for project in ("personal", "untagged", None):
            with self.subTest(project=project), self._with_project(project):
                ok, why = bt_profiles.gate_cwd("claude-work", "/x")
                self.assertFalse(ok)
                self.assertIn("only runs inside work projects", why)

    def test_other_profiles_are_never_blocked_by_folder(self):
        with self._with_project(None):
            self.assertTrue(bt_profiles.gate_cwd("codex-luis", "/anywhere")[0])
            self.assertTrue(bt_profiles.gate_cwd("claude-personal", "/anywhere")[0])

    def test_wrapper_text_checks_gate_then_selects_account(self):
        posix = bt_profiles.wrapper_text("claude-work", "/usr/bin/claude", windows=False)
        lines = posix.splitlines()
        self.assertTrue(lines[0].startswith("#!"))
        self.assertIn("profiles gate claude-work || exit 1", posix)
        self.assertLess(posix.index("profiles gate"), posix.index("CLAUDE_CONFIG_DIR"))
        self.assertTrue(lines[-1].startswith('exec "/usr/bin/claude"'))
        win = bt_profiles.wrapper_text("claude-work", "C:/bin/claude.exe", windows=True)
        self.assertIn("exit /b 1", win)
        self.assertIn('"C:/bin/claude.exe" %*', win)
        self.assertIn("\r\n", win)

    def test_write_wrapper_refuses_foreign_files_and_shadowing(self):
        out = Path(self.tmp.name) / "bin"
        out.mkdir()
        fake_cli = out / "claudecli"
        fake_cli.write_text("#!/bin/sh\n")
        fake_cli.chmod(0o755)
        with patch("bt_profiles.shutil.which", return_value=str(fake_cli)):
            made = bt_profiles.write_wrapper("claude-work", out)
            self.assertIn("generated by metodologia", made.read_text())
            bt_profiles.write_wrapper("claude-work", out)  # regenerating our own file is fine
            made.write_text("#!/bin/sh\necho mine\n")
            with self.assertRaises(SystemExit):
                bt_profiles.write_wrapper("claude-work", out)
        with patch("bt_profiles.shutil.which", return_value=str(out / "claude-personal")):
            with self.assertRaises(SystemExit):
                bt_profiles.write_wrapper("claude-personal", out)


class AntigravityDriverTests(unittest.TestCase):
    def test_session_command_uses_headless_stream_json_and_keeps_the_prompt_last(self):
        import bt_runprompt
        state = {"agent": "antigravity", "model": "haiku"}
        argv, stdin = bt_runprompt.agent_argv(state, Path("/tmp"), "do the thing", "haiku", None)
        self.assertIn("--dangerously-skip-permissions", argv)
        self.assertIn("stream-json", argv)
        self.assertNotIn("--model", argv)  # the ladder's claude names mean CLI default
        self.assertNotIn("-p", argv)  # -p would swallow the next flag as its prompt
        self.assertEqual(argv[-1], "--print=do the thing")
        self.assertIsNone(stdin)
        argv, _ = bt_runprompt.agent_argv(state, Path("/tmp"), "x", "gemini-3.8-flash-high", "xhigh")
        self.assertEqual(argv[argv.index("--model") + 1], "gemini-3.8-flash-high")
        self.assertEqual(argv[argv.index("--effort") + 1], "xhigh")

    def test_ladder_only_raises_effort(self):
        import bt_runtier
        state = {"agent": "antigravity", "model": "gemini-3.8-flash-high"}
        self.assertEqual(bt_runtier.model_for(state, 0), ("gemini-3.8-flash-high", None))
        self.assertEqual(bt_runtier.model_for(state, 2), ("gemini-3.8-flash-high", "xhigh"))

    def test_result_event_is_parsed_as_verdict(self):
        import bt_runsettle
        ok = json.dumps({"event": "result", "result": {"status": "SUCCESS", "response": "done\n"}})
        bad = json.dumps({"event": "result", "result": {"status": "ERROR", "error": "quota exhausted"}})
        noise = json.dumps({"event": "step_update", "step_update": {"state": "DONE"}})
        self.assertEqual(bt_runsettle.parse_output(noise + "\n" + ok)["text"], "done\n")
        self.assertFalse(bt_runsettle.parse_output(noise + "\n" + ok)["is_error"])
        out = bt_runsettle.parse_output(noise + "\n" + bad)
        self.assertTrue(out["is_error"])
        self.assertIn("quota", out["text"])


if __name__ == "__main__":
    unittest.main()
