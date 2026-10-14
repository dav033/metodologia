"""Characterization of the legacy `bitacora.py` process boundary (REQ-007 T4, gate G1).

These tests pin what the current runtime does today, through subprocesses with a throwaway HOME and
BITACORA_ROOT, so the same file can later be pointed at the installed package. They do not judge whether the
behavior is ideal; a failure here means a compatibility contract changed and needs an explicit decision.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

SCRIPT = Path(os.environ.get("BITACORA_ENTRYPOINT",
                             Path(__file__).resolve().parents[2] / "skill" / "scripts" / "bitacora.py"))
SESSION = "abc12345-0000-0000-0000-000000000000"

# The command matrix of the legacy CLI. Adding a command is fine (update this set on purpose);
# removing or renaming one is a compatibility break.
LEGACY_COMMANDS = {
    "where", "init", "id", "req", "index", "rollups", "bind", "launch", "run", "task", "run-control", "watch",
    "monitor", "round", "plan", "workspace", "profiles", "work", "delegate", "metrics", "agents", "usage",
    "config", "learn", "handoff", "context", "audit", "serve", "graph", "web", "secrets", "pending", "trace",
    "commit", "hook", "relay",
}


class LegacyContractCase(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="legacy-contract-")
        self.addCleanup(temporary.cleanup)
        self.tmp = Path(temporary.name)
        self.home, self.root, self.work = self.tmp / "home", self.tmp / "bitacora", self.tmp / "work"
        for directory in (self.home, self.work):
            directory.mkdir()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith(("BITACORA_", "CLAUDE_", "CODEX_"))}
        self.env.update(HOME=str(self.home), BITACORA_ROOT=str(self.root), PYTHONDONTWRITEBYTECODE="1",
                        PYTHONIOENCODING="utf-8")

    def run_cli(self, *args: str, stdin: str | None = None, project: str | None = "demo",
                check: bool = True) -> subprocess.CompletedProcess:
        command = [sys.executable, str(SCRIPT)] + (["--project", project] if project else []) + list(args)
        done = subprocess.run(command, input=stdin, capture_output=True, text=True, env=self.env,
                              cwd=self.work, timeout=60)
        if check:
            self.assertEqual(done.returncode, 0, f"{args}: {done.stderr}")
        return done

    def init(self) -> dict:
        return json.loads(self.run_cli("init").stdout)


class CommandMatrixTests(LegacyContractCase):
    def test_every_legacy_command_is_still_registered(self) -> None:
        text = self.run_cli("--help", project=None).stdout
        listed = set(re.search(r"\{([a-z\-,]+)\}", text).group(1).split(","))
        self.assertTrue(LEGACY_COMMANDS <= listed, f"removed commands: {sorted(LEGACY_COMMANDS - listed)}")

    def test_unknown_command_and_unknown_argument_exit_two_with_usage_on_stderr(self) -> None:
        for args in (("nonsense",), ("id", "--nope")):
            with self.subTest(args=args):
                done = self.run_cli(*args, project=None, check=False)
                self.assertEqual(done.returncode, 2)
                self.assertIn("usage:", done.stderr)
                self.assertEqual(done.stdout, "")

    def test_every_command_answers_help_with_exit_zero(self) -> None:
        for command in sorted(LEGACY_COMMANDS):
            with self.subTest(command=command):
                done = self.run_cli(command, "--help", project=None, check=False)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertIn("usage:", done.stdout)


class DocumentsAndIdsTests(LegacyContractCase):
    def test_init_is_idempotent_and_creates_the_documented_tree(self) -> None:
        first, second = self.init(), self.init()
        self.assertIs(first["created"], True)
        self.assertIs(second["created"], False)
        for key in ("summary", "architecture", "decisions", "pending", "day", "week", "month"):
            self.assertTrue(Path(first[key]).exists(), key)
        project = Path(first["project_dir"])
        self.assertEqual(project, self.root / "demo")
        self.assertTrue((project / "INDEX.md").exists())
        self.assertRegex(Path(first["day"]).name, r"^\d{4}-\d{2}-\d{2}\.md$")
        self.assertRegex(Path(first["week"]).parent.name, r"^W[1-6]$")

    def test_id_is_next_free_and_does_not_consume(self) -> None:
        self.init()
        self.assertEqual(self.run_cli("id", "D").stdout.strip(), "D-001")
        self.assertEqual(self.run_cli("id", "D").stdout.strip(), "D-001")
        self.assertEqual(self.run_cli("id", "P").stdout.strip(), "P-001")
        self.assertEqual(self.run_cli("id", "REQ").stdout.strip(), "REQ-001")

    def test_new_requirement_takes_the_next_id_and_slug_and_writes_a_spec(self) -> None:
        self.init()
        spec = Path(self.run_cli("req", "new", "Hello, wörld!").stdout.strip())
        self.assertEqual(spec.name, "SPEC.md")
        self.assertRegex(spec.parent.name, r"^REQ-001-hello-w")
        self.assertEqual(self.run_cli("id", "REQ").stdout.strip(), "REQ-002")
        self.assertIn("REQ-001", spec.read_text(encoding="utf-8"))

    def test_id_high_water_survives_a_pruned_item(self) -> None:
        paths = self.init()
        day = Path(paths["day"])
        day.write_text(day.read_text(encoding="utf-8") + "\n- ✓ P-007 closed and later pruned\n", encoding="utf-8")
        self.assertEqual(self.run_cli("id", "P").stdout.strip(), "P-008")


class ConfigTests(LegacyContractCase):
    def test_config_round_trip_is_plain_json_under_state(self) -> None:
        self.init()
        self.assertEqual(json.loads(self.run_cli("config", "get", "audit.provider").stdout), "antigravity")
        self.assertIn("Set audit.provider", self.run_cli("config", "set", "audit.provider", "claude").stdout)
        self.assertEqual(json.loads(self.run_cli("config", "get", "audit.provider").stdout), "claude")
        stored = json.loads((self.root / ".state" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, {"audit": {"provider": "claude"}})  # dotted keys are stored nested
        self.run_cli("config", "unset", "audit.provider")
        self.assertEqual(json.loads(self.run_cli("config", "get", "audit.provider").stdout), "antigravity")

    def test_config_set_and_unset_preserve_everything_else_in_the_file(self) -> None:
        # REQ-007 R4 / F-M1-01 (repaired): a newer version's sections and keys, and values this version cannot use,
        # survive a `config set` / `unset` of another key; only the edited key changes.
        self.init()
        state = self.root / ".state"
        state.mkdir(parents=True, exist_ok=True)
        original = {"future": {"keep": [1, None, 0]}, "audit": {"provider": "codex", "newer_key": {"a": 1}},
                    "routing": {"mode": "not-a-mode"}}
        (state / "config.json").write_text(json.dumps(original), encoding="utf-8")
        self.run_cli("config", "set", "approval.max_tasks", "12")
        stored = json.loads((state / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(stored, {**original, "approval": {"max_tasks": 12}})
        self.run_cli("config", "unset", "approval.max_tasks")
        self.assertEqual(json.loads((state / "config.json").read_text(encoding="utf-8")), original)
        self.run_cli("config", "set", "audit.provider", "claude")
        stored = json.loads((state / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["audit"], {"provider": "claude", "newer_key": {"a": 1}})
        self.assertEqual(stored["future"], original["future"])

    def test_config_rejects_unknown_key_and_invalid_value_with_nonzero_exit(self) -> None:
        self.init()
        for args in (("set", "no.such.key", "1"), ("set", "audit.provider", "\"not-a-provider\"")):
            with self.subTest(args=args):
                done = self.run_cli("config", *args, check=False)
                self.assertNotEqual(done.returncode, 0)
                self.assertFalse((self.root / ".state" / "config.json").exists())


class HookTests(LegacyContractCase):
    def event(self, name: str) -> str:
        return json.dumps({"session_id": SESSION, "cwd": str(self.work), "hook_event_name": name,
                           "source": "startup", "stop_hook_active": False})

    def test_start_hook_returns_claude_additional_context_for_a_bound_session(self) -> None:
        self.init()
        self.run_cli("bind", SESSION, "demo")
        done = self.run_cli("hook", "start", stdin=self.event("SessionStart"))
        output = json.loads(done.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "SessionStart")
        self.assertIn("[bitácora]", output["additionalContext"])
        self.assertIn("demo", output["additionalContext"])
        self.assertIn(SESSION[:8], output["additionalContext"])

    def test_stop_and_end_hooks_exit_zero(self) -> None:
        self.init()
        self.run_cli("bind", SESSION, "demo")
        for name in ("stop", "end"):
            with self.subTest(hook=name):
                self.assertEqual(self.run_cli("hook", name, stdin=self.event(name.title())).returncode, 0)

    def test_hooks_never_fail_the_session_on_garbage_input(self) -> None:
        for name in ("start", "stop", "end"):
            for payload in ("", "not json", "[]", "{\"cwd\": 3}"):
                with self.subTest(hook=name, payload=payload):
                    self.assertEqual(self.run_cli("hook", name, stdin=payload, project=None,
                                                  check=False).returncode, 0)

    def test_session_binding_is_recorded_in_state_sessions_json(self) -> None:
        self.init()
        self.run_cli("bind", SESSION, "demo")
        sessions = json.loads((self.root / ".state" / "sessions.json").read_text(encoding="utf-8"))
        self.assertIn(SESSION, json.dumps(sessions))


class HistoricalRunStateTests(LegacyContractCase):
    """RUN.json written by an older supervisor must still load, with unknown fields kept through a save."""

    def test_old_run_without_newer_fields_loads_and_unknown_fields_round_trip(self) -> None:
        scripts = str(SCRIPT.parent)
        rdir = self.tmp / "bitacora" / "demo" / "requirements" / "REQ-001-old"
        rdir.mkdir(parents=True)
        historical = {"req": "REQ-001", "status": "running", "tasks": [
            {"id": "T1", "title": "old task", "status": "done", "attempts": []},
            {"id": "T2", "title": "next", "status": "pending", "after": ["T1"]}],
            "future_field": {"nested": [1, None, False]}, "log": []}
        (rdir / "RUN.json").write_text(json.dumps(historical), encoding="utf-8")
        code = (f"import sys,json; sys.path.insert(0,{scripts!r}); import bt_runstate as s; from pathlib import Path\n"
                f"r=Path({str(rdir)!r}); st=s.load(r); s.save(r, st); print(json.dumps(s.load(r), sort_keys=True))")
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        loaded = json.loads(done.stdout)
        self.assertEqual(loaded["future_field"], {"nested": [1, None, False]})
        self.assertEqual([t["id"] for t in loaded["tasks"]], ["T1", "T2"])
        self.assertEqual(loaded["tasks"][1]["after"], ["T1"])

    def test_unreadable_run_json_is_reported_not_replaced(self) -> None:
        scripts = str(SCRIPT.parent)
        rdir = self.tmp / "req"
        rdir.mkdir()
        (rdir / "RUN.json").write_text("{truncated", encoding="utf-8")
        code = (f"import sys,time; sys.path.insert(0,{scripts!r}); import bt_runstate as s; from pathlib import Path\n"
                "s.time.sleep=lambda *_: None\n"
                f"\ntry:\n    s.load(Path({str(rdir)!r}))\nexcept s.RunStateError: print('RunStateError')")
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=self.env)
        self.assertEqual(done.stdout.strip(), "RunStateError", done.stderr)
        self.assertEqual((rdir / "RUN.json").read_text(encoding="utf-8"), "{truncated")


class WebTests(LegacyContractCase):
    def start_server(self) -> int:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        self.env["BITACORA_PORT"] = str(port)
        self.init()
        process = subprocess.Popen([sys.executable, str(SCRIPT), "serve"], env=self.env, cwd=self.work,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(process.wait)
        self.addCleanup(process.terminate)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            with socket.socket() as client:
                client.settimeout(0.2)
                if client.connect_ex(("127.0.0.1", port)) == 0:
                    return port
            time.sleep(0.1)
        self.fail("server did not start")

    def test_dashboard_serves_html_on_loopback_and_posts_need_the_token(self) -> None:
        port = self.start_server()
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])
        request = urllib.request.Request(f"http://127.0.0.1:{port}/plan/approve", data=b"x=1", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request, timeout=10)
        caught.exception.close()
        self.assertIn(caught.exception.code, (400, 403, 404))
        self.assertTrue((self.root / ".state" / "server-token").exists())
        server = json.loads((self.root / ".state" / "server.json").read_text(encoding="utf-8"))
        self.assertEqual(server["port"], port)



class ShellMutationHeuristicTests(LegacyContractCase):
    """`bt_hooks.needs_logging` decides from the transcript whether work happened since the last bitácora write."""

    def verdict(self, command: str, tool: str = "Bash") -> bool:
        transcript = self.tmp / "transcript.jsonl"
        event = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": tool, "input": {"command": command}}]}}
        transcript.write_text(json.dumps(event) + "\n", encoding="utf-8")
        code = (f"import sys; sys.path.insert(0, {str(SCRIPT.parent)!r}); import bt_hooks; from pathlib import Path\n"
                f"print(bt_hooks.needs_logging(Path({str(transcript)!r}))[0])")
        done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=self.env)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout.strip() == "True"

    def test_shell_writes_and_commits_count_as_work(self) -> None:
        for command in ("git commit -m x", "echo hi > out.txt", "echo hi >> log.md", "printf x | tee out.txt",
                        "sed -i s/a/b/ file.py", "cat > notes.md", "cat <<EOF\nbody\nEOF",
                        "Set-Content -Path a.txt -Value x"):
            with self.subTest(command=command):
                self.assertTrue(self.verdict(command))

    def test_read_only_shell_commands_are_not_work(self) -> None:
        for command in ("ls -la", "git status", "git log --oneline -3", "grep -rn needle src",
                        "python -m unittest discover -s tests", "cat README.md", "diff a.txt b.txt 2>&1"):
            with self.subTest(command=command):
                self.assertFalse(self.verdict(command))

    def test_known_misses_and_false_positives_are_pinned(self) -> None:
        # Characterization of today's regex heuristic. Changing either list is a behavior change that needs its
        # own evidence (PLAN T4); it is not a refactoring side effect.
        for command in ("cp a.txt b.txt", "mv a.txt b.txt", "rm -f a.txt", "python generate.py"):
            with self.subTest(false_negative=command):
                self.assertFalse(self.verdict(command))
        self.assertTrue(self.verdict('echo "if a > b.c then"'))

    def test_writes_into_the_bitacora_root_are_logging_not_work(self) -> None:
        self.assertFalse(self.verdict(f"echo hi > {self.root}/demo/notes.md"))


class FileGuardTests(LegacyContractCase):
    GUARD = SCRIPT.parent / "file_guard.py"

    def guard(self, relative: str, lines: int, payload: str | None = None) -> subprocess.CompletedProcess:
        target = self.work / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("x = 1\n" * lines, encoding="utf-8")
        event = payload if payload is not None else json.dumps(
            {"cwd": str(self.work), "tool_input": {"file_path": relative}})
        return subprocess.run([sys.executable, str(self.GUARD)], input=event, capture_output=True, text=True,
                              env=self.env)

    def test_source_file_over_500_lines_gets_advisory_context_and_exit_zero(self) -> None:
        done = self.guard("big.py", 501)
        self.assertEqual(done.returncode, 0)
        output = json.loads(done.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PostToolUse")
        self.assertIn("501 lines", output["additionalContext"])

    def test_limit_boundary_and_exempt_files_stay_silent(self) -> None:
        for relative, lines in (("exact.py", 500), ("node_modules/pkg/index.js", 900), ("a.test.ts", 900),
                                ("notes.md", 900), ("bundle.min.js", 900)):
            with self.subTest(file=relative):
                done = self.guard(relative, lines)
                self.assertEqual((done.returncode, done.stdout), (0, ""))

    def test_codex_apply_patch_paths_are_checked_and_garbage_input_is_ignored(self) -> None:
        (self.work / "patched.py").write_text("x = 1\n" * 600, encoding="utf-8")
        patch = json.dumps({"cwd": str(self.work), "tool_input": {"patch": "*** Update File: patched.py\n+x"}})
        self.assertIn("600 lines", json.loads(subprocess.run(
            [sys.executable, str(self.GUARD)], input=patch, capture_output=True, text=True,
            env=self.env).stdout)["hookSpecificOutput"]["additionalContext"])
        done = self.guard("ignored.py", 1, payload="not json")
        self.assertEqual((done.returncode, done.stdout), (0, ""))

if __name__ == "__main__":
    unittest.main()
