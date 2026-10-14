"""The README is a contract: its API, error codes, commands and evidence table must match the code and the tests."""
from __future__ import annotations

import ast
import contextlib
import io
import re
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

import bt_scheduler_core as sc
from bt_scheduler_core import cli

MODULE = Path(__file__).resolve().parents[1]
README = (MODULE / "README.md").read_text(encoding="utf-8")


def test_names() -> set[str]:
    names = set()
    for path in (MODULE / "tests").glob("test_*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                names.add(node.name)
    return names


class Readme(unittest.TestCase):
    def test_every_error_code_is_documented_and_vice_versa(self):
        documented = set(re.findall(r"`([A-Z_]{6,})`", README.split("## Errors")[1].split("## Acceptance")[0]))
        self.assertEqual(documented, set(sc.CODES))

    def test_every_listed_source_file_exists(self):
        section = README.split("## Layout")[1].split("## Contracts")[0]
        for name in re.findall(r"`([a-z_]+\.py)`", section):
            self.assertTrue((MODULE / name).is_file(), name)

    def test_every_module_file_is_listed_in_the_layout(self):
        section = README.split("## Layout")[1].split("## Contracts")[0]
        listed = set(re.findall(r"`([a-z_]+\.py)`", section))
        for path in MODULE.glob("*.py"):
            self.assertIn(path.name, listed | {"__init__.py"}, path.name)

    def test_every_evidence_name_is_a_real_test_and_all_twenty_criteria_appear(self):
        rows = [line for line in README.split("## Acceptance evidence")[1].splitlines() if line.startswith("| SC-AC")]
        self.assertEqual([r.split("|")[1].split()[0] for r in rows], [f"SC-AC{n:02d}" for n in range(1, 21)])
        known = test_names()
        for row in rows:
            if row.startswith("| SC-AC18"):
                continue                                   # evidence lives in the methodology suite
            names = re.findall(r"`(test_[a-z0-9_]+)`", row)
            self.assertTrue(names, row)
            for name in names:
                self.assertIn(name, known, f"{row[:20]}: {name}")

    def test_documented_cli_actions_and_flags_exist(self):
        for action in ("validate", "simulate", "status", "audit"):
            self.assertIn(f"`{action} ", README)
        help_text = ""
        for action in ("validate", "simulate", "status", "audit"):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer), self.assertRaises(SystemExit) as cm:
                cli.main([action, "--help"])
            self.assertEqual(cm.exception.code, 0)
            help_text += buffer.getvalue()
        for flag in ("--sha256", "--db", "--parallel", "--max-attempts", "--fail", "--reject", "--since", "--json"):
            self.assertIn(flag, README)
            self.assertIn(flag, help_text)

    def test_the_documented_defaults_are_the_real_ones(self):
        config = sc.Config()
        for text in (f"max_parallel_tasks={config.max_parallel_tasks}", f"max_attempts={config.max_attempts}",
                     f"lease_seconds={int(config.lease_seconds)}", f"reconcile_seconds={int(config.reconcile_seconds)}",
                     f'repository_isolation="{config.repository_isolation}"', f'unknown_surface="{config.unknown_surface}"',
                     f"max_recovery_wait={int(config.max_recovery_wait)}", f"max_recovery_waits={config.max_recovery_waits}",
                     f"max_deliveries={config.max_deliveries}",
                     f"require_independent_verifier={config.require_independent_verifier}"):
            self.assertIn(text, README)

    def test_contract_version_is_the_documented_one(self):
        self.assertIn(f"version `{sc.CONTRACT_VERSION}`", README)

    def test_public_api_is_exactly_what_all_declares(self):
        for name in sc.__all__:
            self.assertTrue(hasattr(sc, name), name)
        public = {n for n in dir(sc) if not n.startswith("_") and n[0].isupper() or n in ("load_plan", "load_plan_file")}
        self.assertTrue(public <= set(sc.__all__) | {"Event"}, public - set(sc.__all__))

    def test_ports_are_structural_protocols_any_object_can_implement(self):
        class Anything:                                    # no inheritance from this package
            def propose(self, request): return []
            def start(self, order): ...
            def cancel(self, order): ...
            def query(self, attempt_id): ...
            def request(self, order): ...
        self.assertIsInstance(Anything(), sc.AssignmentPort)
        self.assertIsInstance(Anything(), sc.ExecutionPort)
        self.assertIsInstance(Anything(), sc.VerificationPort)
        self.assertIsInstance(Anything(), sc.RecoveryPort)


if __name__ == "__main__":
    unittest.main()
