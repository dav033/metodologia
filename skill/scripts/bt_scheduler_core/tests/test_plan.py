"""Plan loader (SC-AC03, SC-AC04): approval is bound to a hash, invalid plans create nothing, the plan is never changed."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import approved, indep, plan_text, task

import bt_scheduler_core as sc

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "plan.example.json"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class Loading(unittest.TestCase):
    def test_a_contract_example_plan_loads_bound_to_id_revision_and_hash(self):
        text = FIXTURE.read_text(encoding="utf-8")
        plan = sc.load_plan(text, approved_sha256=digest(text), plan_id="REQ-EXAMPLE", revision=1)
        self.assertEqual((plan.plan_id, plan.revision, plan.sha256), ("REQ-EXAMPLE", 1, digest(text)))
        self.assertEqual(plan.ids(), ("T1", "T2"))
        self.assertEqual(plan.task("T2").after, ("T1",))
        self.assertEqual(plan.task("T1").shared_resources, ("auth-session-contract",))

    def test_classification_travels_as_opaque_meta_and_nothing_else_is_interpreted(self):
        text = FIXTURE.read_text(encoding="utf-8")
        meta = sc.load_plan(text, approved_sha256=digest(text)).task("T1").meta
        self.assertEqual((meta["risk"], meta["complexity"], meta["estimated_minutes"]), ("high", "low", 25))

    def test_planner_classification_evidence_travels_as_opaque_meta(self):
        evidence = {"risk": {"justification": "auth-sensitive operation", "evidence": ["file:src/auth.py"]}}
        data = json.loads(plan_text([task("T1", classification_evidence=evidence)]))
        text = json.dumps(data)
        meta = sc.load_plan(text, approved_sha256=digest(text)).task("T1").meta
        self.assertEqual(meta["classification_evidence"], evidence)

    def test_loading_a_file_never_modifies_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PLAN.json"
            text = plan_text([task("T1")])
            path.write_text(text, encoding="utf-8")
            before = (path.read_bytes(), path.stat().st_mtime_ns)
            os.chmod(path, 0o444)
            sc.load_plan_file(path, approved_sha256=digest(text))
            self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)

    def test_task_order_of_the_plan_is_preserved(self):
        plan, _ = approved(plan_text([task("T3"), task("T1"), task("T2")]))
        self.assertEqual(plan.ids(), ("T3", "T1", "T2"))

    def test_a_very_deep_chain_does_not_overflow_the_stack(self):
        tasks = [task("T0")] + [task(f"T{i}", [f"T{i - 1}"]) for i in range(1, 3000)]
        plan, _ = approved(plan_text(tasks))
        self.assertEqual(len(plan.ancestors("T2999")), 2999)
        self.assertEqual(len(plan.descendants("T0")), 2999)


class Approval(unittest.TestCase):
    def setUp(self):
        self.text = plan_text([task("T1")])

    def code(self, text, **kw):
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.load_plan(text, **kw)
        return cm.exception.code

    def test_valid_json_is_not_an_approved_plan(self):
        self.assertEqual(self.code(self.text, approved_sha256="0" * 64), "PLAN_NOT_APPROVED")

    def test_a_missing_or_malformed_approval_hash_is_refused(self):
        for bad in ("", "abc", "G" * 64, "A" * 64, None, 12):
            with self.subTest(bad=bad):
                self.assertEqual(self.code(self.text, approved_sha256=bad), "PLAN_NOT_APPROVED")

    def test_one_changed_byte_breaks_approval(self):
        self.assertEqual(self.code(self.text + " ", approved_sha256=digest(self.text)), "PLAN_NOT_APPROVED")

    def test_bytes_and_text_hash_the_same(self):
        self.assertEqual(sc.load_plan(self.text.encode(), approved_sha256=digest(self.text)).sha256, digest(self.text))

    def test_expected_identity_must_match(self):
        self.assertEqual(self.code(self.text, approved_sha256=digest(self.text), plan_id="REQ-OTHER"), "PLAN_MISMATCH")
        self.assertEqual(self.code(self.text, approved_sha256=digest(self.text), revision=2), "PLAN_MISMATCH")


class Invalid(unittest.TestCase):
    def code(self, text: str) -> str:
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.load_plan(text, approved_sha256=digest(text))
        return cm.exception.code

    def test_unreadable_inputs(self):
        for text in ("{not json", "", "[1]", '{"a": NaN}', '"x"', "\xff"):
            with self.subTest(text=text):
                self.assertIn(self.code(text), ("PLAN_UNREADABLE", "PLAN_INVALID"))

    def test_runaway_nesting_is_a_clean_error(self):
        self.assertEqual(self.code("[" * 100000 + "]" * 100000), "PLAN_UNREADABLE")

    def test_oversized_plan_is_refused(self):
        self.assertEqual(self.code(" " * 2_100_000), "PLAN_UNREADABLE")

    def test_unsupported_or_bad_schema_version(self):
        base = json.loads(plan_text([task("T1")]))
        self.assertEqual(self.code(json.dumps({**base, "schema_version": "2.0.0"})), "PLAN_SCHEMA_UNSUPPORTED")
        for bad in ("1", "one", None, 1):
            self.assertEqual(self.code(json.dumps({**base, "schema_version": bad})), "PLAN_INVALID")
        extended = json.loads(json.dumps(base))
        extended["schema_version"] = "1.7.3"
        for item in extended["tasks"]:
            item["kind"] = "implement"
            for check in item.get("verification", []):
                check["category"] = "functional"
        ok = json.dumps(extended)
        self.assertEqual(sc.load_plan(ok, approved_sha256=digest(ok)).schema_version, "1.7.3")

    def test_identity_fields(self):
        base = json.loads(plan_text([task("T1")]))
        for patch in ({"plan_id": ""}, {"plan_id": 3}, {"revision": 0}, {"revision": "1"}, {"revision": True}):
            with self.subTest(patch=patch):
                self.assertEqual(self.code(json.dumps({**base, **patch})), "PLAN_INVALID")

    def test_task_list_shape(self):
        for tasks in ([], None, {"id": "T1"}, ["T1"], [{"id": ""}], [{"title": "no id"}]):
            with self.subTest(tasks=tasks):
                self.assertEqual(self.code(plan_text(tasks)), "PLAN_INVALID")  # type: ignore[arg-type]

    def test_duplicate_ids_unknown_references_and_self_dependency(self):
        self.assertEqual(self.code(plan_text([task("T1"), task("T1")])), "PLAN_INVALID")
        self.assertEqual(self.code(plan_text([task("T1", ["T9"])])), "PLAN_INVALID")
        self.assertEqual(self.code(plan_text([task("T1", ["T1"])])), "PLAN_INVALID")
        self.assertEqual(self.code(plan_text([task("T1"), task("T2", ["T1", "T1"])])), "PLAN_INVALID")

    def test_cycles_are_reported_with_the_path(self):
        text = plan_text([task("T1", ["T3"]), task("T2", ["T1"]), task("T3", ["T2"]), task("T4")])
        with self.assertRaises(sc.SchedulerError) as cm:
            sc.load_plan(text, approved_sha256=digest(text))
        self.assertEqual(cm.exception.code, "PLAN_INVALID")
        self.assertIn("cycle", cm.exception.issues[0])
        self.assertIn("T1", cm.exception.issues[0])

    def test_wrong_field_types(self):
        for patch in ({"after": "T1"}, {"after": [1]}, {"shared_resources": [""]}, {"expected_paths": "x"},
                      {"repository": 3}, {"verification": "true"}, {"verification": ["true"]}):
            with self.subTest(patch=patch):
                self.assertEqual(self.code(plan_text([{**task("T1"), **patch}])), "PLAN_INVALID")

    def test_a_failed_load_leaves_no_state_anywhere(self):
        repo = sc.InMemoryRepository()
        with self.assertRaises(sc.SchedulerError):
            sc.load_plan("{bad", approved_sha256="0" * 64)
        with repo.transaction() as tx:
            self.assertIsNone(tx.state)
        self.assertEqual(repo.audit_log(), [])


class Graph(unittest.TestCase):
    def test_dependents_ancestors_descendants(self):
        plan, _ = approved(plan_text([indep("A"), indep("B", ["A"]), indep("C", ["A"]), indep("D", ["B", "C"]), indep("E")]))
        self.assertEqual(plan.descendants("A"), frozenset({"B", "C", "D"}))
        self.assertEqual(plan.ancestors("D"), frozenset({"A", "B", "C"}))
        self.assertEqual(plan.descendants("E"), frozenset())
        self.assertEqual(plan.dependents()["A"], ("B", "C"))

    def test_unknown_task_is_a_stable_error(self):
        plan, _ = approved(plan_text([task("T1")]))
        with self.assertRaises(sc.SchedulerError) as cm:
            plan.task("nope")
        self.assertEqual(cm.exception.code, "UNKNOWN_TASK")


if __name__ == "__main__":
    unittest.main()
