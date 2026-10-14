"""Wheel packaging gate G2 (REQ-007 T5): build from a copy of the sources, install without pip into a fresh
venv, hide the checkout and exercise the CLI, hooks, context and web assets from an unrelated directory.

The build runs through setuptools' PEP 517 backend in a temporary copy, so the repository gets no build litter.
If setuptools or the venv module is unavailable the tests are skipped with a reason, which is not a pass.
"""
from __future__ import annotations

import json
import re
import socket
import subprocess
import time
import unittest
import urllib.request
import zipfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also collected as tests.migration.*

import installed_wheel  # noqa: E402

REPO = installed_wheel.REPO
SCRIPTS = REPO / "skill" / "scripts"
RUNTIME_EXTRA = {"bitacora", "file_guard", "globalusage", "install_agents", "install_rtk", "relay_run",
                 "migration_inventory"}


def runtime_modules() -> set[str]:
    return {p.stem for p in SCRIPTS.glob("*.py") if p.stem.startswith("bt_") or p.stem in RUNTIME_EXTRA}


class PackageCase(unittest.TestCase):
    wheel: Path
    site: Path
    venv_python: Path
    work: Path

    @classmethod
    def setUpClass(cls) -> None:
        built = installed_wheel.get()
        cls.work, cls.wheel, cls.site, cls.venv_python = built.work, built.wheel, built.site, built.python

    def setUp(self) -> None:
        self.cwd = self.work / "unrelated-cwd"
        self.cwd.mkdir(exist_ok=True)
        self.root = self.work / "bitacora"
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(self.work / "home"), "BITACORA_ROOT": str(self.root),
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}

    def installed(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        return subprocess.run([str(self.venv_python), "-I", *args], input=stdin, capture_output=True, text=True,
                              cwd=self.cwd, env=self.env, timeout=120)


class WheelContentsTests(PackageCase):
    def test_py_modules_cover_every_runtime_script_and_nothing_else(self) -> None:
        with zipfile.ZipFile(self.wheel) as archive:
            names = set(archive.namelist())
        shipped = {n[:-3] for n in names if "/" not in n and n.endswith(".py")}
        self.assertEqual(shipped, runtime_modules(),
                         "update [tool.setuptools] py-modules in pyproject.toml")

    def test_resources_travel_in_the_wheel_and_tests_do_not(self) -> None:
        with zipfile.ZipFile(self.wheel) as archive:
            names = archive.namelist()
        for required in ("bitacora_resources/SKILL.md", "bitacora_resources/templates/SPEC.md",
                         "bitacora_resources/templates/arch/nextjs/eslint-boundaries.config.mjs",
                         "bitacora_resources/assets/style.css", "bitacora_resources/agents/reviewer.md",
                         "bitacora_resources/references/agents.md", "bitacora_resources/githooks/pre-commit"):
            self.assertIn(required, names)
        self.assertFalse([n for n in names if "/tests/" in n or n.startswith("tests/") or "ops_" in n])

    def test_console_scripts_map_to_the_single_legacy_main(self) -> None:
        with zipfile.ZipFile(self.wheel) as archive:
            entry = archive.read(next(n for n in archive.namelist() if n.endswith("entry_points.txt"))).decode()
        self.assertIn("bitacora = bitacora:main", entry)
        self.assertIn("bt = bitacora:main", entry)


class InstalledRuntimeTests(PackageCase):
    def test_no_module_resolves_from_the_checkout(self) -> None:
        code = ("import sys, json, bt_core, bt_server, bt_context, bt_hooks\n"
                "print(json.dumps({'path': sys.path, 'skill': str(bt_core.SKILL_DIR), 'script': str(bt_core.SCRIPT),"
                "'files': [m.__file__ for m in (bt_core, bt_server, bt_context, bt_hooks)]}))")
        done = self.installed("-c", code)
        self.assertEqual(done.returncode, 0, done.stderr)
        info = json.loads(done.stdout)
        everything = json.dumps(info)
        self.assertNotIn(str(REPO), everything)
        self.assertTrue(Path(info["skill"]).is_relative_to(self.site))
        self.assertTrue(Path(info["script"]).is_file())

    def test_module_and_cli_commands_work_from_an_unrelated_directory(self) -> None:
        init = self.installed("-m", "bitacora", "--project", "demo", "init")
        self.assertEqual(init.returncode, 0, init.stderr)
        self.assertTrue((self.root / "demo" / "DECISIONS.md").is_file())  # needs templates/
        self.assertIn("# Agent context", self.installed("-m", "bitacora", "--project", "demo", "context").stdout)
        help_text = self.installed("-m", "bitacora", "--help").stdout
        self.assertRegex(help_text, r"\{where,init,id,")

    def test_context_names_policy_files_inside_the_installed_package(self) -> None:
        self.installed("-m", "bitacora", "--project", "demo", "init")
        text = self.installed("-m", "bitacora", "--project", "demo", "context").stdout
        located = re.findall(r"`([^`]*references/agents\.md)`", text)
        self.assertTrue(located, text[-800:])
        self.assertTrue(all(Path(p).is_file() and Path(p).is_relative_to(self.site) for p in located))

    def test_codex_start_hook_injects_the_packaged_skill_body(self) -> None:
        self.installed("-m", "bitacora", "--project", "demo", "init")
        event = json.dumps({"session_id": "feedface-0000-0000-0000-000000000000", "cwd": str(self.cwd),
                            "source": "resume"})
        done = self.installed("-m", "bitacora", "hook", "--harness", "codex", "start", stdin=event)
        self.assertEqual(done.returncode, 0, done.stderr)
        context = json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("metodologia skill", context)

    def test_installed_web_server_finds_its_static_assets(self) -> None:
        self.installed("-m", "bitacora", "--project", "demo", "init")
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        process = subprocess.Popen([str(self.venv_python), "-I", "-m", "bitacora", "serve", "--port", str(port)],
                                   cwd=self.cwd, env=self.env, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        self.addCleanup(process.wait)
        self.addCleanup(process.terminate)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            with socket.socket() as client:
                client.settimeout(0.2)
                if client.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/static/style.css", timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertGreater(len(response.read()), 100)

    def test_platform_namespace_aliases_are_installed(self) -> None:
        done = self.installed("-c", "import bitacora_platform.core as a, bt_core; print(a is bt_core)")
        self.assertEqual((done.returncode, done.stdout.strip()), (0, "True"), done.stderr)

    def test_resource_override_beats_the_installed_package(self) -> None:
        override = self.work / "custom-resources"
        (override / "templates").mkdir(parents=True)
        done = subprocess.run(
            [str(self.venv_python), "-I", "-c", "import bt_core;print(bt_core.SKILL_DIR)"], capture_output=True,
            text=True, cwd=self.cwd, env={**self.env, "BITACORA_RESOURCES": str(override)})
        self.assertEqual(Path(done.stdout.strip()), override.resolve(), done.stderr)


if __name__ == "__main__":
    unittest.main()
