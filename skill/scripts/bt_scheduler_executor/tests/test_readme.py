"""The README and the code cannot drift apart: every public name, error code, event kind, cause class and limit is
documented, and every test the acceptance table cites exists."""
from __future__ import annotations

import ast
import re
import sys
import unittest
from dataclasses import fields
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support  # noqa: F401
from bt_scheduler_executor import model as m

MODULE = Path(__file__).resolve().parents[1]
README = (MODULE / "README.md").read_text(encoding="utf-8")


def tests_in(path: Path) -> set[str]:
    out = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            out.add(node.name)
    return out


class Readme(unittest.TestCase):
    def test_every_public_name_is_documented(self):
        for name in ex.__all__:
            if name in ("CONTRACT_VERSION", "CODES", "CAUSES", "EVENT_KINDS"):
                continue
            self.assertIn(name, README, name)

    def test_every_error_code_is_listed(self):
        for code in ex.CODES:
            self.assertIn(f"`{code}`", README, code)

    def test_every_event_kind_and_cause_class_is_listed(self):
        for kind in ex.EVENT_KINDS:
            self.assertIn(f"`{kind}`", README, kind)
        for cause in ex.CAUSES:
            if cause in (m.CANCEL_CAUSE,):
                self.assertIn("`cancelled`", README)
            else:
                self.assertIn(f"`{cause}`", README, cause)

    def test_every_configuration_limit_is_listed_with_its_default(self):
        defaults = ex.Config()
        for field in fields(ex.Config):
            self.assertIn(f"`{field.name}", README, field.name)
        for name in ("max_running", "max_queued", "grace_seconds", "heartbeat_seconds", "poll_seconds"):
            self.assertIn(f"{name}={getattr(defaults, name):g}", README.replace("`", ""), name)

    def test_every_file_of_the_package_is_in_the_layout_table(self):
        for path in sorted(MODULE.glob("*.py")):
            if path.name in ("__init__.py", "__main__.py"):
                continue
            self.assertIn(path.name, README, path.name)

    def test_the_acceptance_table_cites_tests_that_exist(self):
        known = {}
        for path in sorted((MODULE / "tests").glob("test_*.py")) + sorted((MODULE.parent / "tests").glob("test_scheduler_executor_*.py")):
            known[path.stem] = tests_in(path)
        rows = re.findall(r"^\| ((?:US-|R)\d+[^|]*) \| (.+) \|$", README, flags=re.M)
        self.assertGreaterEqual(len(rows), 20, "the acceptance table is missing")
        for label, evidence in rows:
            cited = re.findall(r"`(test_[A-Za-z0-9_]+)\.(test_[A-Za-z0-9_]+)`", evidence)
            self.assertTrue(cited, f"{label} cites no test")
            for module_name, test_name in cited:
                if module_name.startswith("test_scheduler_executor_") and not (MODULE.parent / "tests").is_dir():
                    continue          # a lone copy of the package has no methodology around it to cite
                self.assertIn(test_name, known.get(module_name, set()), f"{label}: {module_name}.{test_name}")


if __name__ == "__main__":
    unittest.main()
