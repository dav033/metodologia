"""Planner warnings born from REQ-021 SP-1: a security surface needs abuse-case criteria and an oracle that is not the code."""
import unittest

from bt_planner import quality


def task(tid, kind="implement", after=(), risk="high", title="Server sessions and the permission guard", criteria=(), **extra):
    return {"id": tid, "kind": kind, "after": list(after), "risk": risk, "title": title,
            "acceptance_criteria": list(criteria), "expected_paths": [], **extra}


class SecuritySensitive(unittest.TestCase):
    def test_only_high_risk_implementation_that_names_a_security_surface(self):
        self.assertTrue(quality.security_sensitive(task("T1")))
        self.assertTrue(quality.security_sensitive(task("T1", title="Local mode", objective="Do not trust forwarded headers")))
        self.assertFalse(quality.security_sensitive(task("T1", risk="medium")))
        self.assertFalse(quality.security_sensitive(task("T1", kind="audit")))
        self.assertFalse(quality.security_sensitive(task("T1", kind="test")))
        self.assertFalse(quality.security_sensitive(task("T1", title="Public plans page")))
        self.assertFalse(quality.security_sensitive(None))


class AbuseCases(unittest.TestCase):
    def test_a_happy_path_only_security_task_is_reported(self):
        plan = {"tasks": [task("T1", criteria=["A signed-in user reaches the pages the role allows"])]}
        found = quality.security_abuse_cases(plan)
        self.assertEqual(len(found), 1)
        self.assertTrue(found[0].startswith("T1:"))

    def test_one_abuse_case_criterion_is_enough_and_other_tasks_are_left_alone(self):
        plan = {"tasks": [task("T1", criteria=["A forged X-Forwarded-For header never yields the local administrator"]),
                          task("T2", title="Public plans page", criteria=["It renders"])]}
        self.assertEqual(quality.security_abuse_cases(plan), [])


class OracleIndependence(unittest.TestCase):
    def plan(self, criteria, **over):
        return {"tasks": [task("T1", criteria=["x"]), task("T2", kind="test", after=["T1"], risk="medium", title="Matrix",
                                                        criteria=criteria, **over)]}

    def test_the_t17_matrix_is_reported_for_all_three_gaps(self):
        found = quality.oracle_independence(self.plan(
            ["Each role reaches the pages and API routes its role allows, derived from the route map"],
            expected_paths=["scripts/test/matrix.ts"]))
        self.assertEqual(len(found), 1)
        for fragment in ("taken from the implementation", "denied case", "writing method"):
            self.assertIn(fragment, found[0])

    def test_a_spec_based_matrix_with_denials_and_writes_is_clean(self):
        criteria = ["Expected access per role comes from the SPEC permission table (R2), not from the implementation",
                    "Every role sends GET, POST, PATCH and DELETE to each API route; the denied ones return 403"]
        self.assertEqual(quality.oracle_independence(self.plan(criteria)), [])

    def test_non_http_surfaces_do_not_need_a_writing_method(self):
        plan = {"tasks": [task("T1", title="Local mode", criteria=["x"]),
                          task("T2", kind="test", after=["T1"], risk="medium", title="Local mode check",
                               criteria=["Per SPEC R16 the start is refused outside loopback"])]}
        self.assertEqual(quality.oracle_independence(plan), [])

    def test_tests_without_a_security_task_upstream_are_ignored(self):
        plan = {"tasks": [task("T1", title="Plans page"), task("T2", kind="test", after=["T1"], criteria=["It renders"])]}
        self.assertEqual(quality.oracle_independence(plan), [])


class Wiring(unittest.TestCase):
    def test_the_warnings_reach_validate_only_for_schema_13_plans(self):
        import json
        from pathlib import Path

        from bt_planner import contract

        golden = Path(__file__).resolve().parent / "golden"
        legacy = json.loads((golden / "input-1.2.0.json").read_text(encoding="utf-8"))
        for task_ in legacy["tasks"]:
            task_.update(risk="high", title="Server sessions and the permission guard", acceptance_criteria=["It works"])
        text = "\n".join(contract.validate(legacy).warnings)
        self.assertNotIn("security checklist", text)
        self.assertNotIn("oracle independence", text)


if __name__ == "__main__":
    unittest.main()
