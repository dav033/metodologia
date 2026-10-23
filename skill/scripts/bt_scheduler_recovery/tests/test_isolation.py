import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class IsolationTests(unittest.TestCase):
    def test_module_alone_passes_suite_in_isolated_python(self):
        # The copied suite skips this single recursive test and exercises every other test.
        package = Path(__file__).resolve().parents[1]
        if package.parent.name == "isolated-module":
            return
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "isolated-module"
            shutil.copytree(package, root / package.name, ignore=shutil.ignore_patterns("__pycache__"))
            tests = root / package.name / "tests"
            script = (f"import sys,unittest;sys.path.insert(0,{str(root)!r});"
                      f"suite=unittest.defaultTestLoader.discover({str(tests)!r});"
                      "result=unittest.TextTestRunner(verbosity=0).run(suite);"
                      "sys.exit(not result.wasSuccessful())")
            result = subprocess.run([sys.executable, "-I", "-B", "-c", script], cwd=temporary,
                                    capture_output=True, text=True, timeout=60, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cli_from_unrelated_cwd_without_site_or_environment(self):
        package = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(package, root / package.name, ignore=shutil.ignore_patterns("__pycache__"))
            store = root / "state" / "decisions.db"
            setup = (f"import sys;sys.path.insert(0,{str(root)!r});"
                     "from bt_scheduler_recovery import DecisionStore;"
                     f"DecisionStore({str(store)!r}).close()")
            subprocess.run([sys.executable, "-I", "-B", "-c", setup], cwd="/", check=True, capture_output=True)
            for command in ("inspect", "metrics"):
                for structured in (False, True):
                    args = [command, "--store", str(store)] + (["--json"] if structured else [])
                    script = (f"import sys,runpy;sys.path.insert(0,{str(root)!r});"
                              f"sys.argv=['bt_scheduler_recovery']+{args!r};"
                              "runpy.run_module('bt_scheduler_recovery',run_name='__main__')")
                    result = subprocess.run([sys.executable, "-I", "-B", "-c", script], cwd="/",
                                            capture_output=True, text=True, timeout=10, check=False)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if structured:
                        json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
