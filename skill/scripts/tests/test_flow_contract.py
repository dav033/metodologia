"""The flow map must cover every message the modules can produce (REQ SUPERRR T8.2).

A new M1 audit kind without a rule, or a new module table nobody classified, fails here instead of silently
disappearing from /flow.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

import bt_flow_bus as bus

SCRIPTS = Path(__file__).resolve().parents[1]
AUDIT_CALL = re.compile(r"(?:audit|record)\(\s*\"([a-z_]+)\"")
TABLE = re.compile(r"CREATE TABLE (?:IF NOT EXISTS )?([a-z_0-9]+)")
PACKAGES = {key: "bt_scheduler_" + name for key, name in (("m1", "core"), ("m2", "decision"), ("m3", "executor"),
                                                          ("m4", "monitor"), ("m5", "recovery"), ("m6", "quality"))}


def sources(package: str):
    for path in (SCRIPTS / package).rglob("*.py"):
        if "tests" not in path.relative_to(SCRIPTS / package).parts:
            yield path.read_text(encoding="utf-8")


class Coverage(unittest.TestCase):
    def test_every_m1_audit_kind_has_a_rule(self):
        kinds = {k for text in sources(PACKAGES["m1"]) for k in AUDIT_CALL.findall(text)}
        kinds |= {"amendment_applied", "audit_gate_skipped"}   # written by the methodology's adapters, not the core
        self.assertGreater(len(kinds), 20)                # the scan itself works
        self.assertEqual(sorted(kinds - set(bus.M1_RULES)), [], "M1 audit kinds the bus cannot map")

    def test_rules_do_not_name_kinds_that_do_not_exist(self):
        kinds = {k for text in sources(PACKAGES["m1"]) for k in AUDIT_CALL.findall(text)} | {"amendment_applied", "audit_gate_skipped"}
        self.assertEqual(sorted(set(bus.M1_RULES) - kinds), [], "rules for audit kinds nobody writes")

    def test_every_table_of_every_module_is_a_source_or_explained(self):
        for key, package in PACKAGES.items():
            tables = {t for text in sources(package) for t in TABLE.findall(text)}
            known = bus.COVERED_TABLES.get(key, set()) | {t for t in tables if t in bus.IGNORED_TABLES}
            self.assertEqual(sorted(tables - known), [], f"{package}: tables the bus neither reads nor explains")

    def test_covered_tables_really_exist_in_their_module(self):
        for key, package in PACKAGES.items():
            tables = {t for text in sources(package) for t in TABLE.findall(text)}
            self.assertTrue(bus.COVERED_TABLES.get(key, set()) <= tables, key)

    def test_every_rule_yields_known_parties_and_a_kind(self):
        class Row(dict):
            pass
        ctx = bus.Ctx(None, "p/REQ-1")
        for kind, rule in bus.M1_RULES.items():
            row = {"task_id": "T1", "attempt_id": "A-1", "at": 1.0, "seq": 1}
            frm, to, out_kind, text, extra = rule(ctx, row, {"kind": "start", "to": "running", "tasks": 2, "port": "x"})
            self.assertIn(frm, bus.PARTIES, kind)
            self.assertIn(to, bus.PARTIES, kind)
            self.assertTrue(out_kind and text, kind)


if __name__ == "__main__":
    unittest.main()
