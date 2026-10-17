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
import sys
import time
import unittest
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also collected as tests.migration.*

import installed_wheel

REPO = installed_wheel.REPO
SCRIPTS = REPO / "skill" / "scripts"
RUNTIME_EXTRA = {"bitacora", "file_guard", "globalusage", "install_agents", "install_rtk", "relay_run",
                 "migration_inventory", "bt_cli_scheduler_monitor"}


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
                              cwd=self.cwd, env=self.env, timeout=120, check=False)


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
                         "bitacora_resources/agents/planner/skills/adversarial-plan-review/SKILL.md",
                         "bitacora_resources/agents/planner/skills/plan-mermaid-view/SKILL.md",
                         "bitacora_resources/agents/planner/skills/socratic-elicitation/SKILL.md",
                         "bitacora_resources/agents/planner/skills/wbs-dag-decomposition/SKILL.md",
                         "bitacora_resources/references/agents.md", "bitacora_resources/githooks/pre-commit",
                         "bt_planner/__init__.py", "bt_planner/contract.py", "bt_planner/data/plan.schema.json",
                         "bt_planner/data/plan.example.json", "bt_planner/README.md",
                         "plan_bench/__init__.py", "plan_bench/__main__.py", "plan_bench/planner_reports.py",
                         "plan_bench/data/rubric-v1.json",
                         "plan_bench/README.md", "bt_plan_bench.py",
                         "bt_scheduler_decision/__init__.py", "bt_scheduler_decision/api-contract.json",
                         "bt_scheduler_decision/README.md", "bt_scheduler_decision/laya-requirements.lock",
                         "bt_scheduler_executor/__init__.py", "bt_scheduler_executor/shim.py", "bt_scheduler_executor/README.md",
                         "bt_scheduler_monitor/__init__.py", "bt_scheduler_monitor/store.py",
                         "bt_scheduler_monitor/README.md", "bt_scheduler_monitor/providers/__init__.py",
                         "bt_scheduler_monitor/providers/claude.py", "bt_scheduler_monitor/providers/codex.py",
                         "bt_scheduler_monitor/providers/antigravity.py", "bt_scheduler_monitor/providers/gemini.py",
                         "bt_scheduler_recovery/__init__.py", "bt_scheduler_recovery/history.py",
                         "bt_scheduler_recovery/README.md", "bt_scheduler_recovery_adapter.py",
                         "bt_scheduler_quality/__init__.py", "bt_scheduler_quality/contracts.py",
                         "bt_scheduler_quality/api-contract.json", "bt_scheduler_quality/README.md",
                         "bt_scheduler_quality_adapter.py",
                         "bt_scheduler_executor_wiring.py", "bt_scheduler_retry.py", "bt_cli_scheduler_recovery.py"):
            self.assertIn(required, names)
        self.assertFalse([n for n in names if "/tests/" in n or n.startswith("tests/") or "ops_" in n])

    def test_console_scripts_map_to_the_single_legacy_main(self) -> None:
        with zipfile.ZipFile(self.wheel) as archive:
            entry = archive.read(next(n for n in archive.namelist() if n.endswith("entry_points.txt"))).decode()
        self.assertIn("bitacora = bitacora:main", entry)
        self.assertIn("bt = bitacora:main", entry)
        self.assertIn("bt-plan-bench = bt_plan_bench:main", entry)
        self.assertIn("bt-scheduler-monitor = bt_cli_scheduler_monitor:main", entry)
        self.assertIn("bt-scheduler-monitor-recovery = bt_scheduler_monitor_recovery:main", entry)
        self.assertIn("bt-scheduler-recovery = bt_cli_scheduler_recovery:main", entry)


class InstalledRuntimeTests(PackageCase):
    def test_benchmark_module_and_entry_point_run_from_the_installed_wheel(self) -> None:
        done = self.installed("-m", "plan_bench", "rubric")
        self.assertEqual(done.returncode, 0, done.stderr)
        rubric = json.loads(done.stdout)
        self.assertEqual(rubric["version"], "1.0.0")
        entry = self.installed("-c", "import sys;from bt_plan_bench import main;"
                               "sys.argv=['bt-plan-bench','rubric'];raise SystemExit(main())")
        self.assertEqual(entry.returncode, 0, entry.stderr)
        self.assertEqual(json.loads(entry.stdout), rubric)

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

    def test_scheduler_run_cli_is_packaged_without_starting_a_run(self) -> None:
        done = self.installed("-m", "bitacora", "scheduler-run", "REQ-042", "--help")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("--resume", done.stdout)
        self.assertIn("--no-autostart", done.stdout)

    def test_scheduler_run_control_helper_is_packaged_without_starting_a_run(self) -> None:
        done = self.installed("-c", "import bt_cli_run_control")
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_planner_module_runs_standalone_from_the_installed_wheel(self) -> None:
        done = self.installed("-m", "bt_planner", "example")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn('"plan_id"', done.stdout)
        probe = ("import bt_planner, sys; print(bt_planner.__file__, 'bt_core' in sys.modules, "
                 "'bitacora' in sys.modules)")
        out = self.installed("-c", probe)
        self.assertEqual(out.returncode, 0, out.stderr)
        path, core, bita = out.stdout.split()
        self.assertTrue(Path(path).is_relative_to(self.site))
        self.assertEqual((core, bita), ("False", "False"))  # importing the module pulls in nothing else

    def test_recovery_policy_adapters_and_operational_cli_run_from_installed_wheel(self) -> None:
        store = self.work / "m5-recovery.sqlite3"
        setup = self.installed("-c", (
            "import sys;from bt_scheduler_recovery import DecisionStore,RecoveryCase;"
            "case=RecoveryCase('run','plan',1,'a'*64,'task','attempt',1,'execution_failed');"
            "store=DecisionStore(sys.argv[1]);store.decide(case);store.close()"), str(store))
        self.assertEqual(setup.returncode, 0, setup.stderr)
        for module, arguments in (("bitacora", ("recovery", "inspect")),
                                  ("bt_cli_scheduler_recovery", ("recovery", "metrics")),
                                  ("bt_scheduler_recovery", ("inspect",))):
            done = self.installed("-m", module, *arguments, "--store", str(store), "--json")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIsInstance(json.loads(done.stdout), dict)
        probe = self.installed("-c", (
            "import bt_scheduler_recovery,bt_scheduler_recovery_adapter,bt_scheduler_retry,"
            "bt_scheduler_executor_wiring;print(bt_scheduler_recovery.__file__)"))
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertTrue(Path(probe.stdout.strip()).is_relative_to(self.site))

    def test_quality_verifier_package_and_adapter_import_from_installed_wheel(self) -> None:
        store = self.work / "m6-quality.sqlite3"
        probe = self.installed(
            "-c",
            "import sys;from bt_scheduler_quality.policy import QualityPolicy;"
            "from bt_scheduler_quality.store import QualityStore;"
            "import bt_scheduler_quality_adapter as adapter;"
            "import bt_scheduler_executor_wiring as wiring;"
            "store=QualityStore(sys.argv[1]);store.close();"
            "print(adapter.__file__,wiring.__file__,QualityPolicy().version)",
            str(store),
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        adapter_path, wiring_path, policy_version = probe.stdout.split()
        self.assertTrue(Path(adapter_path).is_relative_to(self.site))
        self.assertTrue(Path(wiring_path).is_relative_to(self.site))
        self.assertEqual(policy_version, "m6-policy/1")

    def test_executor_module_runs_standalone_from_the_installed_wheel(self) -> None:
        done = self.installed("-m", "bt_scheduler_executor", "selftest", "--json", "--keep", str(self.work / "m3-selftest"))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(json.loads(done.stdout)["ok"])
        probe = ("import bt_scheduler_executor, sys; print(bt_scheduler_executor.__file__, "
                 "sorted(m for m in sys.modules if m.startswith('bt_') and not m.startswith('bt_scheduler_executor')))")
        out = self.installed("-c", probe)
        self.assertEqual(out.returncode, 0, out.stderr)
        path, _, rest = out.stdout.partition(" ")
        self.assertTrue(Path(path).is_relative_to(self.site))
        self.assertEqual(rest.strip(), "[]")

    def test_monitor_package_adapters_and_cli_run_from_the_installed_wheel(self) -> None:
        store = self.work / "m4-monitor.sqlite3"
        setup = self.installed("-c", "from bt_scheduler_monitor.store import MonitorStore; import sys; MonitorStore(sys.argv[1])",
                               str(store))
        self.assertEqual(setup.returncode, 0, setup.stderr)

        done = self.installed("-m", "bt_cli_scheduler_monitor", "status", "--store", str(store))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("storage", json.loads(done.stdout))

        probe = (
            "import json, sys, bt_scheduler_monitor, bt_scheduler_monitor_adapter, bt_scheduler_stream_adapter, "
            "bt_scheduler_m4_stream_bridge, bt_scheduler_m4_wiring; "
            "from bt_scheduler_monitor.contracts import ExecutionOutputFrame, ProcessIdentity; "
            "from bt_scheduler_monitor.providers import JsonlCollector; "
            "frame = ExecutionOutputFrame('1.0.0', 'run', 1, 'task', 'attempt', 'execution', "
            "ProcessIdentity('linux'), 'claude', 'stdout', 0, 0, '2026-10-15T00:00:00Z', "
            "b'{\"type\":\"system\"}\\n'); "
            "output = JsonlCollector('claude').feed(frame); "
            "provider_files = [sys.modules['bt_scheduler_monitor.providers.' + name].__file__ "
            "for name in ('claude', 'codex', 'antigravity', 'gemini')]; "
            "print(json.dumps([bt_scheduler_monitor.__file__, bt_scheduler_monitor_adapter.__file__, "
            "bt_scheduler_stream_adapter.__file__, bt_scheduler_m4_stream_bridge.__file__, "
            "bt_scheduler_m4_wiring.__file__, *provider_files, len(output.records), "
            "output.records[0].parsed.status]))"
        )
        out = self.installed("-c", probe)
        self.assertEqual(out.returncode, 0, out.stderr)
        result = json.loads(out.stdout)
        self.assertTrue(all(Path(path).is_relative_to(self.site) for path in result[:9]))
        self.assertEqual(result[9:], [1, "ignored"])

    def test_monitor_recovery_cli_runs_archive_verify_and_candidate_from_the_wheel(self) -> None:
        source = self.work / "recovery-source.sqlite3"
        archive = self.work / "recovery-archive.sqlite3"
        archive_manifest = self.work / "recovery-archive.json"
        candidate = self.work / "recovery-candidate.sqlite3"
        candidate_manifest = self.work / "recovery-candidate.json"
        sqlite_temp = self.work / "sqlite-temp"
        sqlite_temp.mkdir()
        setup = self.installed("-c", "from bt_scheduler_monitor.store import MonitorStore; import sys; "
                               "MonitorStore(sys.argv[1])", str(source))
        self.assertEqual(setup.returncode, 0, setup.stderr)

        exported = self.installed("-m", "bt_scheduler_monitor_recovery", "archive", "--store", str(source),
                                  "--archive", str(archive), "--manifest", str(archive_manifest))
        self.assertEqual(exported.returncode, 0, exported.stderr)
        verified = self.installed("-m", "bt_scheduler_monitor_recovery", "verify-archive", "--archive", str(archive),
                                  "--manifest", str(archive_manifest))
        self.assertEqual(verified.returncode, 0, verified.stderr)
        prepared = self.installed("-m", "bt_scheduler_monitor_recovery", "prepare-candidate", "--archive",
                                  str(archive), "--archive-manifest", str(archive_manifest), "--candidate",
                                  str(candidate), "--candidate-manifest", str(candidate_manifest),
                                  "--sqlite-temp-dir", str(sqlite_temp))
        self.assertEqual(prepared.returncode, 0, prepared.stderr)
        self.assertTrue(json.loads(prepared.stdout)["ok"])
        checked = self.installed("-m", "bt_scheduler_monitor_recovery", "verify-candidate", "--candidate",
                                 str(candidate), "--manifest", str(candidate_manifest))
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)["ok"])

    def test_decision_module_and_contract_are_standalone_in_the_installed_wheel(self) -> None:
        probe = ("import bt_scheduler_decision, json, sys; print(json.dumps({'file': bt_scheduler_decision.__file__, "
                 "'other_bt_modules': sorted(m for m in sys.modules if m.startswith('bt_') "
                 "and not m.startswith('bt_scheduler_decision'))}))")
        out = self.installed("-c", probe)
        self.assertEqual(out.returncode, 0, out.stderr)
        info = json.loads(out.stdout)
        self.assertTrue(Path(info["file"]).is_relative_to(self.site))
        self.assertEqual(info["other_bt_modules"], [])

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
            text=True, cwd=self.cwd, env={**self.env, "BITACORA_RESOURCES": str(override)}, check=False)
        self.assertEqual(Path(done.stdout.strip()), override.resolve(), done.stderr)


if __name__ == "__main__":
    unittest.main()
