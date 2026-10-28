"""Plan pre-flight (REQ-030 M6): structural defects of a plan are found before freezing/dispatch, against a real git
repository, and legitimate plans (files a task declares it will create) are not rejected."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bt_plan_adapter import preflight_check


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=cwd, check=True, capture_output=True)


def check(cmd, *, task_id="T1", paths=(), after=(), requires=None):
    item = {"type": "command", "value": cmd, "purpose": "x"}
    if requires:
        item["requires"] = requires
    return {"id": task_id, "repository": "app", "after": list(after), "expected_paths": list(paths),
            "verification": [item]}


class Preflight(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp(prefix="preflight-"))
        self.addCleanup(shutil.rmtree, self.repo, True)
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "scripts").mkdir()
        (self.repo / "scripts" / "present.py").write_text("print(1)\n")
        (self.repo / "package.json").write_text(json.dumps({"scripts": {"test": "x", "lint": "y"}}))
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")

    def run_check(self, tasks, env=None):
        return preflight_check({"tasks": tasks}, {"app": self.repo}, env_available=env)

    def test_a_check_that_runs_an_undeclared_missing_script_is_an_error(self):
        report = self.run_check([check("npx tsx scripts/test/test-glb-todos-los-tipos.ts")])
        self.assertEqual(len(report.errors), 1)
        self.assertIn("PREFLIGHT_INPUT_MISSING", report.errors[0])

    def test_a_script_the_task_or_a_predecessor_declares_is_legitimate(self):
        own = check("npx tsx scripts/test/new.ts", paths=["scripts/test/**"])
        later = check("python3 scripts/gen/out.py", task_id="T3", after=["T2"])
        producer = {"id": "T2", "repository": "app", "after": [], "expected_paths": ["scripts/gen/out.py"],
                    "verification": []}
        self.assertTrue(self.run_check([own, producer, later]).ok, self.run_check([own, producer, later]).errors)

    def test_existing_scripts_and_cd_prefixes_resolve(self):
        self.assertTrue(self.run_check([check("cd scripts && python3 present.py")]).ok)
        self.assertTrue(self.run_check([check("python3 scripts/present.py --flag")]).ok)

    def test_npm_scripts_must_exist_unless_package_json_is_declared(self):
        self.assertTrue(self.run_check([check("npm test"), check("npm run lint", task_id="T2")]).ok)
        missing = self.run_check([check("npm run cuentas:test-integracion-ui")])
        self.assertTrue(missing.ok)                                     # a warning by default: plans add scripts
        self.assertIn("PREFLIGHT_SCRIPT_MISSING", missing.warnings[0])
        strict = preflight_check({"tasks": [check("npm run cuentas:test-integracion-ui")]}, {"app": self.repo},
                                 strict=True)
        self.assertIn("PREFLIGHT_SCRIPT_MISSING", strict.errors[0])
        declared = self.run_check([check("npm run cuentas:test-integracion-ui", paths=["package.json"])])
        self.assertTrue(declared.ok)

    def test_required_variables_without_a_source_are_found_before_any_attempt(self):
        report = self.run_check([check("npm test", requires=["PICTURES_REQ021_DATABASE_URL", "service:db"])],
                                env=lambda name: False)
        self.assertEqual(len(report.errors), 1)
        self.assertIn("PICTURES_REQ021_DATABASE_URL", report.errors[0])
        self.assertTrue(self.run_check([check("npm test", requires=["X_URL"])], env=lambda name: True).ok)

    def test_unordered_overlapping_paths_are_a_warning_not_an_error(self):
        a = check("true", paths=["src/**"])
        b = check("true", task_id="T2", paths=["src/lib/x.ts"])
        report = self.run_check([a, b])
        self.assertTrue(report.ok)
        self.assertIn("PREFLIGHT_PATHS_UNORDERED", report.warnings[0])
        ordered = check("true", task_id="T2", paths=["src/lib/x.ts"], after=["T1"])
        self.assertEqual(self.run_check([a, ordered]).warnings, [])

    def test_inline_code_and_unknown_repositories_are_not_guessed(self):
        self.assertTrue(self.run_check([check("python3 -c 'print(1)'"), {**check("python3 x.py"), "repository": "x"}]).ok)


if __name__ == "__main__":
    unittest.main()
