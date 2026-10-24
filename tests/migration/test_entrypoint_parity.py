"""Old script path versus installed console script (REQ-007 T6, gate G1/G2): same implementation, same behavior.

Each case runs the legacy file under skill/scripts and the entry point declared in the wheel's entry_points.txt
(executed the way pip's generated launcher does) with identical, separate throwaway HOME/BITACORA_ROOT trees,
then compares exit code, stdout and stderr after normalizing only temp paths and the program name.
"""
from __future__ import annotations

import configparser
import json
import re
import subprocess
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also collected as tests.migration.*

import installed_wheel  # noqa: E402

REPO = installed_wheel.REPO
SCRIPTS = REPO / "skill" / "scripts"
SESSION = "abc12345-0000-0000-0000-000000000000"


class EntrypointParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.built = installed_wheel.get()
        with zipfile.ZipFile(cls.built.wheel) as archive:
            name = next(n for n in archive.namelist() if n.endswith("entry_points.txt"))
            parser = configparser.ConfigParser()
            parser.optionxform = str
            parser.read_string(archive.read(name).decode())
        cls.entries = dict(parser["console_scripts"])

    _runs = 0

    def tree(self, label: str) -> dict:
        type(self)._runs += 1
        base = self.built.work / f"parity-{label}-{type(self)._runs}"
        (base / "home").mkdir(parents=True)
        (base / "cwd").mkdir()
        return {"base": base, "home": base / "home", "root": base / "bitacora", "cwd": base / "cwd"}

    def env(self, tree: dict) -> dict:
        return {"PATH": "/usr/bin:/bin", "HOME": str(tree["home"]), "BITACORA_ROOT": str(tree["root"]),
                "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}

    def normalize(self, text: str, tree: dict, script: str, command: str) -> str:
        # the interpreter is the one intended difference: each entry names its own `sys.executable`
        for value, token in ((str(tree["base"]), "<TMP>"), (str(SCRIPTS), "<SCRIPTS>"),
                             (str(self.built.site / "bitacora_resources"), "<RESOURCES>"),
                             (str(REPO / "skill"), "<RESOURCES>"),
                             (str(self.built.site), "<SCRIPTS>"), (str(self.built.python), "<PYTHON>"),
                             (Path(sys.executable).as_posix(), "<PYTHON>")):
            text = text.replace(value, token)
        # argparse wraps usage by program-name width, so only the words are compared
        return " ".join(text.replace(script, command).split())

    def run_legacy(self, script: str, tree: dict, args, stdin):
        return subprocess.run([sys.executable, str(SCRIPTS / script), *args], input=stdin, capture_output=True,
                              text=True, cwd=tree["cwd"], env=self.env(tree), timeout=120)

    def run_installed(self, command: str, tree: dict, args, stdin):
        module, function = self.entries[command].split(":")
        code = (f"import sys; from {module} import {function}; sys.argv[0] = {command!r}; "
                f"sys.exit({function}())")
        return subprocess.run([str(self.built.python), "-I", "-c", code, *args], input=stdin,
                              capture_output=True, text=True, cwd=tree["cwd"], env=self.env(tree), timeout=120)

    def assert_parity(self, script: str, command: str, args: tuple[str, ...] = (), stdin: str | None = None,
                      setup: tuple[tuple[str, ...], ...] = ()) -> None:
        results = []
        for label, runner, name in (("legacy", self.run_legacy, script), ("installed", self.run_installed, command)):
            tree = self.tree(label)
            for preparation in setup:  # same commands through the same runner so state starts equal
                runner(name, tree, preparation, None)
            done = runner(name, tree, args, stdin)
            results.append((done.returncode,
                            self.normalize(done.stdout, tree, script, command),
                            self.normalize(done.stderr, tree, script, command)))
        self.assertEqual(results[0], results[1], f"{script} {args}")

    def test_declared_console_scripts_target_existing_callables(self) -> None:
        for name, target in self.entries.items():
            with self.subTest(command=name):
                module, function = target.split(":")
                done = subprocess.run([str(self.built.python), "-I", "-c",
                                       f"import {module}; assert callable({module}.{function})"],
                                      capture_output=True, text=True, cwd=self.built.work)
                self.assertEqual(done.returncode, 0, done.stderr)

    def test_bitacora_commands_match(self) -> None:
        init = (("--project", "demo", "init"),)
        for args in (("--project", "demo", "init"), ("--project", "demo", "id", "D"),
                     ("--project", "demo", "config", "get", "audit.provider"),
                     ("--project", "demo", "req", "new", "Parity check"), ("--project", "demo", "index"),
                     ("--project", "demo", "trace"), ("nonsense",), ("--project", "demo", "id", "--nope")):
            with self.subTest(args=args):
                self.assert_parity("bitacora.py", "bitacora", args, setup=init if args[-1] != "init" else ())

    def test_bt_alias_is_the_same_entry_as_bitacora(self) -> None:
        self.assertEqual(self.entries["bt"], self.entries["bitacora"])

    def test_hook_start_and_stop_match(self) -> None:
        setup = (("--project", "demo", "init"), ("bind", SESSION, "demo"))
        event = json.dumps({"session_id": SESSION, "cwd": "<TMP>", "source": "startup"})
        for hook in ("start", "stop", "end"):
            with self.subTest(hook=hook):
                self.assert_parity("bitacora.py", "bitacora", ("hook", hook), stdin=event, setup=setup)

    def test_file_guard_matches(self) -> None:
        for payload in ("not json", "{}", json.dumps({"cwd": "/nonexistent", "tool_input": {"file_path": "x.py"}})):
            with self.subTest(payload=payload):
                self.assert_parity("file_guard.py", "file-guard", stdin=payload)

    def test_relay_run_usage_error_matches(self) -> None:
        self.assert_parity("relay_run.py", "relay-run", ())
        self.assert_parity("relay_run.py", "relay-run", ("p", "--", "definitely-not-an-agent"))

    def test_globalusage_matches_with_empty_state(self) -> None:
        self.assert_parity("globalusage.py", "globalusage", ("--guardado",))

    def test_inventory_cli_matches_on_real_capture_and_restore(self) -> None:
        # Same implementation reached through both entries: capture then restore a tiny tree under each.
        outputs = []
        for label, runner, name in (("legacy", self.run_legacy, "migration_inventory.py"),
                                    ("installed", self.run_installed, "bitacora-inventory")):
            tree = self.tree(label)
            source, state = tree["base"] / "src", tree["base"] / "state"
            source.mkdir()
            state.mkdir()
            (source / "a.txt").write_text("alpha")
            (state / "s.json").write_text("{}")
            capture = runner(name, tree, ("capture", "--source", str(source), "--state", str(state),
                                          "--destination", str(tree["base"] / "backup")), None)
            restore = runner(name, tree, ("restore", "--backup", str(tree["base"] / "backup"),
                                          "--destination", str(tree["base"] / "restored")), None)
            manifest = json.loads((tree["base"] / "backup" / "manifest.json").read_text())
            hashes = {k: sorted(v) for k, v in manifest["entries"].items()}
            outputs.append((capture.returncode, capture.stdout, restore.returncode, restore.stdout, hashes,
                            (tree["base"] / "restored" / "source" / "a.txt").read_text()))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0][0], 0)

    def test_inventory_usage_errors_match(self) -> None:
        self.assert_parity("migration_inventory.py", "bitacora-inventory", ("capture",))
    def test_install_agents_writes_identical_definitions_through_both_entries(self) -> None:
        written = []
        for label, runner, name in (("legacy", self.run_legacy, "install_agents.py"),
                                    ("installed", self.run_installed, "install-agents")):
            tree = self.tree(label)
            done = runner(name, tree, (), None)
            files = {str(path.relative_to(tree["home"])): path.read_text(encoding="utf-8")
                     for path in sorted(tree["home"].rglob("*")) if path.is_file()}
            skill_root = REPO / "skill" if label == "legacy" else self.built.site / "bitacora_resources"
            self.assertIn(f"Metodología skill root: `{skill_root}`", files[".claude/agents/planner.md"])
            files = {path: content.replace(str(skill_root), "<METODOLOGIA_SKILL_ROOT>")
                     for path, content in files.items()}
            written.append((done.returncode, files))
        self.assertEqual(written[0][0], 0)
        self.assertEqual(written[0], written[1])
        self.assertTrue(any(name.startswith(".claude/agents/") for name in written[0][1]))
        self.assertTrue(any(name.startswith(".codex/agents/") for name in written[0][1]))
        antigravity_path = ".gemini/config/agents/planner/agent.md"
        self.assertIn(antigravity_path, written[0][1])
        antigravity_agent = written[0][1][antigravity_path]
        antigravity_tool_lines = antigravity_agent.split("mainAgent:", 1)[0]
        antigravity_tools = re.findall(r'^  - "([^\"]+)"$', antigravity_tool_lines, re.MULTILINE)
        self.assertEqual(antigravity_tools, ["view_file", "grep_search", "find_by_name", "run_command",
                                             "write_to_file", "replace_file_content"])

    def test_codex_and_antigravity_hook_payloads_match(self) -> None:
        setup = (("--project", "demo", "init"), ("bind", SESSION, "demo"))
        event = json.dumps({"session_id": SESSION, "cwd": "<TMP>", "source": "startup"})
        for harness in ("codex", "antigravity"):
            for hook in ("start", "stop", "end"):
                with self.subTest(harness=harness, hook=hook):
                    self.assert_parity("bitacora.py", "bitacora", ("hook", "--harness", harness, hook),
                                       stdin=event, setup=setup)

    def test_install_rtk_entry_resolves_to_the_same_module_and_refuses_unverified_archives(self) -> None:
        # The installer downloads a release asset, so its parity is the shared module plus its checksum guard.
        code = ("import bt_entrypoints, install_rtk\n"
                "assert callable(bt_entrypoints.install_rtk)\n"
                "try:\n    install_rtk.verified_binary(b'not the pinned archive')\n"
                "except ValueError as error:\n    print('REFUSED', install_rtk.VERSION, 'checksum' in str(error))\n")
        legacy = subprocess.run([sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(SCRIPTS)!r})\n" + code],
                                capture_output=True, text=True)
        installed = subprocess.run([str(self.built.python), "-I", "-c", code], capture_output=True, text=True,
                                   cwd=self.built.work)
        self.assertEqual((legacy.returncode, installed.returncode), (0, 0), legacy.stderr + installed.stderr)
        self.assertTrue(installed.stdout.startswith("REFUSED"))
        self.assertEqual(legacy.stdout, installed.stdout)


if __name__ == "__main__":
    unittest.main()
