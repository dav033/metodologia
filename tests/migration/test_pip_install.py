"""sdist completeness and a real installer run (REQ-007 T5, gate G2).

`uv pip install` is used as the installer: it writes RECORD and generates the console-script launchers exactly as
pip would, offline, from the wheel. The sdist is proven complete by building a second wheel from its extracted
contents. Interpreters 3.12, 3.13 and the running one are exercised when present; a missing one is a skip with a
reason, not a pass.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # also collected as tests.migration.*

import installed_wheel  # noqa: E402

UV = shutil.which("uv")


class SdistTests(unittest.TestCase):
    def test_sdist_contains_everything_needed_and_rebuilds_the_same_module_set(self) -> None:
        built = installed_wheel.get()
        with tarfile.open(built.sdist) as archive:
            names = archive.getnames()
            for required in ("pyproject.toml", "skill/SKILL.md", "skill/templates/SPEC.md",
                             "skill/assets/style.css", "skill/scripts/bitacora.py"):
                self.assertTrue(any(n.endswith(required) for n in names), required)
            with tempfile.TemporaryDirectory(prefix="sdist-rebuild-") as temp:
                archive.extractall(temp, filter="data")
                root = next(Path(temp).iterdir())
                done = subprocess.run([sys.executable, "-I", "-c",
                                       "from setuptools import build_meta; print(build_meta.build_wheel('out'))"],
                                      cwd=root, capture_output=True, text=True, timeout=300)
                self.assertEqual(done.returncode, 0, done.stderr[-1500:])
                rebuilt = zipfile.ZipFile(root / "out" / done.stdout.strip().splitlines()[-1]).namelist()
        original = zipfile.ZipFile(built.wheel).namelist()
        self.assertEqual(sorted(n for n in rebuilt if not n.endswith(("RECORD", "METADATA"))),
                         sorted(n for n in original if not n.endswith(("RECORD", "METADATA"))))


@unittest.skipUnless(UV, "uv is not installed")
class InstallerTests(unittest.TestCase):
    def interpreters(self) -> list[str]:
        found = []
        for version in ("3.12", "3.13", f"{sys.version_info.major}.{sys.version_info.minor}"):
            done = subprocess.run([UV, "python", "find", "--no-project", version], capture_output=True, text=True)
            if done.returncode == 0 and done.stdout.strip() and done.stdout.strip() not in found:
                found.append(done.stdout.strip())
        return found

    def test_wheel_installs_with_generated_launchers_on_each_available_python(self) -> None:
        built = installed_wheel.get()
        interpreters = self.interpreters()
        if not interpreters:
            self.skipTest("no interpreter found by uv")
        for interpreter in interpreters:
            with self.subTest(interpreter=interpreter), tempfile.TemporaryDirectory(prefix="uv-install-") as temp:
                temp_path = Path(temp)
                venv = temp_path / "venv"
                subprocess.run([UV, "venv", "--python", interpreter, str(venv)], check=True,
                               capture_output=True, text=True)
                subprocess.run([UV, "pip", "install", "--python", str(venv / "bin" / "python"), "--offline",
                                "--no-deps", str(built.wheel)], check=True, capture_output=True, text=True)
                env = {"PATH": "/usr/bin:/bin", "HOME": str(temp_path / "home"),
                       "BITACORA_ROOT": str(temp_path / "bit"), "PYTHONDONTWRITEBYTECODE": "1"}
                cwd = temp_path / "elsewhere"
                cwd.mkdir()
                for command in ("bitacora", "bt"):
                    launcher = venv / "bin" / command
                    self.assertTrue(launcher.exists(), command)
                    done = subprocess.run([str(launcher), "--project", "demo", "init"], capture_output=True,
                                          text=True, cwd=cwd, env=env, timeout=120)
                    self.assertEqual(done.returncode, 0, done.stderr)
                    self.assertTrue(json.loads(done.stdout)["created"] in (True, False))
                for command in ("file-guard", "relay-run", "bitacora-inventory", "install-agents", "globalusage"):
                    self.assertTrue((venv / "bin" / command).exists(), command)
                usage = subprocess.run([str(venv / "bin" / "relay-run")], capture_output=True, text=True,
                                       cwd=cwd, env=env)
                self.assertEqual(usage.returncode, 2)
                context = subprocess.run([str(venv / "bin" / "bitacora"), "--project", "demo", "context"],
                                         capture_output=True, text=True, cwd=cwd, env=env)
                self.assertIn(str(venv / "bin" / "python").replace("\\", "/"), context.stdout.replace("\\", "/"))
                self.assertNotIn('python "', context.stdout)


if __name__ == "__main__":
    unittest.main()
