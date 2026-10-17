"""bt_planner contract: enums, classification completeness, DAG integrity, negative diagnostics, determinism."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # the folder that contains the bt_planner package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import contract as pc

MODULE = Path(__file__).resolve().parents[1]
SCHEMA = MODULE / "data" / "plan.schema.json"


def task(tid: str = "T1", **over) -> dict:
    base = {
        "id": tid, "milestone_id": "M1", "title": "Fix session validation",
        "objective": "Reject expired sessions without touching valid ones", "repository": "backend", "after": [],
        "complexity": "low", "scope": "isolated_fix", "estimated_minutes": 25, "risk": "high", "coupling": "medium",
        "confidence": "medium", "estimate_rationale": "Localised change, sensitive because it touches auth",
        "expected_paths": ["src/auth/**", "tests/auth/**"], "shared_resources": ["auth-session-contract"],
        "acceptance_criteria": ["Expired sessions are rejected", "Valid sessions keep working"],
        "verification": [{"type": "command", "value": "pytest tests/auth -q", "purpose": "reject/accept sessions"}],
    }
    base.update(over)
    return base


def plan(*tasks: dict, milestones: list[dict] | None = None) -> dict:
    return {"schema_version": "1.0.0", "plan_id": "REQ-EXAMPLE", "revision": 1, "spec_ref": "SPEC.md",
            "milestones": milestones or [{"id": "M1", "title": "Base", "acceptance_criteria": ["API meets contract"]},
                                         {"id": "M2", "title": "Next", "acceptance_criteria": ["Done"]}],
            "tasks": list(tasks) or [task(), task("T2", milestone_id="M2", after=["T1"])]}


def errors(p: dict) -> str:
    return "\n".join(pc.validate(p).errors)


class ValidPlans(unittest.TestCase):
    def test_complete_plan_passes(self):
        self.assertEqual(pc.validate(plan()).errors, [])

    def test_low_complexity_with_high_risk_is_allowed(self):  # AC-04
        r = pc.validate(plan(task(complexity="low", risk="high", scope="isolated_fix"), task("T2", milestone_id="M2")))
        self.assertTrue(r.ok, r.errors)

    def test_large_but_easy_and_hard_but_small_are_allowed(self):  # dimensions are independent
        p = plan(task(complexity="low", scope="large_change", risk="low", coupling="low", shared_resources=[]),
                 task("T2", milestone_id="M2", complexity="extreme", scope="small_change", risk="low"))
        self.assertTrue(pc.validate(p).ok)

    def test_low_confidence_needs_number_and_rationale_but_is_accepted(self):  # AC-09
        p = plan(task(confidence="low"), task("T2", milestone_id="M2"))
        self.assertTrue(pc.validate(p).ok)

    def test_full_system_with_exception_is_accepted(self):  # AC-08
        t = task(scope="full_system", scope_exception={"reason": "mechanical rename, reviewed by owner"})
        self.assertTrue(pc.validate(plan(t, task("T2", milestone_id="M2"))).ok)

    def test_manual_check_with_expected_result_and_planned_test(self):  # AC-07
        t = task("T2", milestone_id="M2", verification=[
            {"type": "manual", "value": "open the page", "purpose": "see the badge", "expected": "badge is visible"},
            {"type": "command", "value": "pytest tests/new -q", "purpose": "new test", "created_by": "T1"}])
        self.assertTrue(pc.validate(plan(task(), t)).ok)

    def test_extra_fields_are_allowed(self):
        self.assertTrue(pc.validate(plan(task(notes="open question"), task("T2", milestone_id="M2"))).ok)


class Negative(unittest.TestCase):
    def assertMentions(self, p: dict, *needles: str) -> None:
        out = errors(p)
        self.assertTrue(out, "expected validation errors")
        for needle in needles:
            self.assertIn(needle, out)

    def test_every_classification_field_is_mandatory(self):  # AC-03, AC-14
        for key in ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence",
                    "estimate_rationale", "objective", "repository", "after", "acceptance_criteria",
                    "verification", "expected_paths", "shared_resources", "milestone_id", "title"):
            with self.subTest(key=key):
                t = task()
                del t[key]
                self.assertMentions(plan(t, task("T2", milestone_id="M2")), f"T1.{key}")

    def test_null_and_invalid_enums_name_task_and_field(self):
        self.assertMentions(plan(task(complexity=None), task("T2", milestone_id="M2")), "T1.complexity")
        self.assertMentions(plan(task(), task("T2", milestone_id="M2", risk="critical")), "T2.risk", "critical")
        self.assertMentions(plan(task(scope="huge"), task("T2", milestone_id="M2")), "T1.scope")

    def test_minutes_must_be_a_positive_integer(self):
        for bad in (0, -5, 2.5, "30", True, None):
            with self.subTest(bad=bad):
                self.assertMentions(plan(task(estimated_minutes=bad), task("T2", milestone_id="M2")),
                                    "T1.estimated_minutes")

    def test_blank_rationale_and_criteria_rejected(self):
        self.assertMentions(plan(task(estimate_rationale="  "), task("T2", milestone_id="M2")),
                            "T1.estimate_rationale")
        self.assertMentions(plan(task(acceptance_criteria=[]), task("T2", milestone_id="M2")), "T1.acceptance_criteria")
        self.assertMentions(plan(task(acceptance_criteria=[""]), task("T2", milestone_id="M2")),
                            "T1.acceptance_criteria")

    def test_full_system_without_exception_rejected(self):  # AC-08
        self.assertMentions(plan(task(scope="full_system"), task("T2", milestone_id="M2")), "T1.scope", "decomposed")

    def test_scope_exception_only_for_full_system(self):
        self.assertMentions(plan(task(scope_exception={"reason": "x"}), task("T2", milestone_id="M2")),
                            "T1.scope_exception")

    def test_verification_rules(self):  # AC-07
        self.assertMentions(plan(task(verification=[]), task("T2", milestone_id="M2")), "T1.verification")
        manual = [{"type": "manual", "value": "look", "purpose": "see"}]
        self.assertMentions(plan(task(verification=manual), task("T2", milestone_id="M2")), "verification[0].expected")
        bad = [{"type": "shell", "value": "x", "purpose": "y"}]
        self.assertMentions(plan(task(verification=bad), task("T2", milestone_id="M2")), "verification[0].type")
        ghost = [{"type": "command", "value": "x", "purpose": "y", "created_by": "T9"}]
        self.assertMentions(plan(task(verification=ghost), task("T2", milestone_id="M2")), "created_by")

    def test_duplicate_task_ids(self):  # AC-05
        self.assertMentions(plan(task(), task()), "T1: duplicate task id")

    def test_unknown_dependency_self_dependency_and_duplicates(self):
        self.assertMentions(plan(task(after=["T9"]), task("T2", milestone_id="M2")), "T1.after", "T9")
        self.assertMentions(plan(task(after=["T1"]), task("T2", milestone_id="M2")), "depend on itself")
        self.assertMentions(plan(task(), task("T2", milestone_id="M2", after=["T1", "T1"])), "duplicate prerequisite")

    def test_cycles_are_reported_with_their_members(self):
        p = plan(task("T1", after=["T3"]), task("T2", after=["T1"]), task("T3", after=["T2"]))
        p["milestones"] = p["milestones"][:1]
        self.assertMentions(p, "dependency cycle", "T1, T2, T3")

    def test_dependency_on_a_later_milestone(self):
        p = plan(task("T1", after=["T2"]), task("T2", milestone_id="M2"))
        self.assertMentions(p, "T1.after", "later milestone")

    def test_orphan_and_unknown_milestones(self):
        self.assertMentions(plan(task(), task("T2", milestone_id="M3")), "T2.milestone_id", "M2: orphan milestone")

    def test_milestones_need_criteria_and_unique_ids(self):
        dup = [{"id": "M1", "title": "a", "acceptance_criteria": ["x"]}, {"id": "M1", "title": "b",
                                                                        "acceptance_criteria": ["x"]}]
        self.assertMentions(plan(task(), milestones=dup), "M1: duplicate milestone id")
        empty = [{"id": "M1", "title": "a", "acceptance_criteria": []}]
        self.assertMentions(plan(task(), milestones=empty), "M1.acceptance_criteria")

    def test_scheduler_and_execution_fields_are_rejected(self):  # AC-11, AC-15
        for key in ("model", "account", "workers", "agent", "status", "attempts"):
            with self.subTest(key=key):
                self.assertMentions(plan(task(**{key: "x"}), task("T2", milestone_id="M2")), f"T1.{key}", "not allowed")

    def test_unsafe_expected_paths(self):
        self.assertMentions(plan(task(expected_paths=["/etc/passwd"]), task("T2", milestone_id="M2")),
                            "T1.expected_paths")
        self.assertMentions(plan(task(expected_paths=["../x"]), task("T2", milestone_id="M2")), "T1.expected_paths")

    def test_top_level_problems(self):
        p = plan()
        del p["spec_ref"]
        p["revision"] = 0
        p["schema_version"] = "2.0.0"
        self.assertMentions(p, "plan.spec_ref", "plan.revision", "plan.schema_version")
        self.assertMentions([], "top level")
        self.assertMentions({**plan(), "tasks": []}, "tasks")

    def test_task_not_an_object_and_bad_id(self):
        p = plan()
        p["tasks"].append("T3")
        p["tasks"].append(task("task-3"))
        self.assertMentions(p, "tasks[2]", "tasks[3].id")

    def test_shared_resources_warning_does_not_block(self):  # AC-06
        r = pc.validate(plan(task(coupling="high", shared_resources=[]), task("T2", milestone_id="M2")))
        self.assertTrue(r.ok)
        self.assertTrue(any("T1.shared_resources" in w for w in r.warnings))

    def test_huge_estimate_warns(self):
        r = pc.validate(plan(task(estimated_minutes=900), task("T2", milestone_id="M2")))
        self.assertTrue(r.ok)
        self.assertTrue(any("T1.estimated_minutes" in w for w in r.warnings))

    def test_validation_never_mutates_input(self):
        p = plan()
        before = copy.deepcopy(p)
        pc.validate(p)
        self.assertEqual(p, before)


class Robustness(unittest.TestCase):
    """Reviewer findings: malformed input yields diagnostics, never an exception, and never passes."""

    def test_unhashable_values_are_diagnosed_not_raised(self):
        for mutate, needle in (
            (lambda p: p["tasks"][0].update(milestone_id=[]), "T1.milestone_id"),
            (lambda p: p["tasks"][0].update(milestone_id={}), "T1.milestone_id"),
            (lambda p: p["tasks"][0]["verification"][0].update(created_by=[]), "created_by"),
            (lambda p: p["tasks"][1].update(after=[[]]), "T2.after"),
            (lambda p: p["tasks"][1].update(after=[{}]), "T2.after"),
            (lambda p: p.update(milestones=5), "milestones"),
            (lambda p: p["milestones"].__setitem__(0, {"id": [], "title": "x", "acceptance_criteria": ["y"]}), "id"),
            (lambda p: p["tasks"].append({"id": [], "milestone_id": "M1"}), "tasks[2]"),
        ):
            p = plan()
            mutate(p)
            self.assertIn(needle, errors(p))

    def test_fuzz_every_field_never_raises_and_never_passes_when_wrong(self):
        weird = [None, [], {}, [[]], [{}], [None], 1.5, "", " ", True, ["a", ["b"]], {"a": 1}, 10 ** 400,
                 float("nan"), -1, 0]
        base = plan()
        paths = [("tasks", 0, key) for key in pc.REQUIRED_TASK_KEYS] + [("tasks", 1, "after"), ("milestones", 0, "id"),
                                                                 ("milestones", 0, "acceptance_criteria")]
        paths += [(key,) for key in pc.TOP_REQUIRED]
        for path in paths:
            for value in weird:
                p = copy.deepcopy(base)
                node = p
                for part in path[:-1]:
                    node = node[part]
                node[path[-1]] = value
                try:
                    report = pc.validate(p)
                except Exception as exc:  # noqa: BLE001 - the point of the test
                    self.fail(f"validate raised {type(exc).__name__} for {path}={value!r}")
                if value != base_value(base, path):
                    # a changed value may still be legal for a few fields; "after"=[] and shared/expected lists are
                    legal = (path[-1] in ("after", "expected_paths", "shared_resources") and value == []) \
                        or (path[-1] == "after" and value == [])
                    if not legal:
                        self.assertFalse(report.ok, f"{path}={value!r} should be rejected")

    def test_forbidden_keys_at_every_level(self):  # AC-15
        for mutate, needle in (
            (lambda p: p.update(model="opus"), "plan.model"),
            (lambda p: p["milestones"][0].update(workers=3), "M1.workers"),
            (lambda p: p["tasks"][0].update(assignment={"model": "opus"}), "T1.assignment.model"),
            (lambda p: p["tasks"][0]["verification"][0].update(agent="codex"), "verification[0].agent"),
            (lambda p: p["tasks"][0].update(extra=[{"Account": "x"}]), "T1.extra[0].Account"),
        ):
            p = plan()
            mutate(p)
            self.assertIn(needle, errors(p))

    def test_ascii_digits_only(self):
        self.assertIn("T1.id", errors(plan(task("T\u0661"), task("T2", milestone_id="M2"))) .replace("tasks[0].id", "T1.id"))
        p = plan()
        p["schema_version"] = "\u0661.0.0"
        self.assertIn("schema_version", errors(p))
        p = plan()
        p["milestones"][0]["id"] = "M\u0661"
        self.assertIn("milestones[0].id", errors(p))

    def test_spec_ref_must_stay_inside_the_requirement(self):
        for bad in ("/etc/passwd", "../x.md", "a/../../x", "C:\\x"):
            p = plan()
            p["spec_ref"] = bad
            self.assertIn("plan.spec_ref", errors(p))

    def test_non_standard_json_is_refused(self):
        with self.assertRaises(ValueError):
            pc.loads('{"a": NaN}')
        with self.assertRaises(ValueError):
            pc.loads("[" * 100000)
        p = plan()
        p["tasks"][0]["extra"] = float("nan")
        self.assertIn("not serialisable", errors(p))
        with self.assertRaises(pc.PlanContractError) as ctx:
            pc.dumps(p)
        self.assertEqual(ctx.exception.code, "PLAN_NOT_SERIALISABLE")

    def test_revision_bounds_and_nesting(self):
        for bad in (0, -1, 10 ** 5000, pc.MAX_REVISION + 1):
            p = plan()
            p["revision"] = bad
            self.assertIn("plan.revision", errors(p))
        p = plan()
        deep: object = "x"
        for _ in range(60):
            deep = {"k": deep}
        p["tasks"][0]["extra"] = deep
        self.assertIn("nested deeper", errors(p))


def base_value(base: dict, path: tuple):
    node = base
    for part in path:
        node = node[part]
    return node


class Serialisation(unittest.TestCase):
    def test_canonical_output_is_deterministic_and_key_ordered(self):
        a = plan()
        b = json.loads(json.dumps(a))
        b["tasks"][0] = dict(reversed(list(b["tasks"][0].items())))
        self.assertEqual(pc.dumps(a), pc.dumps(b))
        text = pc.dumps(a)
        self.assertTrue(text.endswith("\n"))
        self.assertLess(text.index('"schema_version"'), text.index('"milestones"'))
        self.assertLess(text.index('"objective"'), text.index('"verification"'))
        self.assertEqual(json.loads(text), a)

    def test_load_reports_stable_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "ok.json").write_text(pc.dumps(plan()), encoding="utf-8")
            self.assertEqual(pc.load(d / "ok.json")["plan_id"], "REQ-EXAMPLE")
            (d / "bad.json").write_text("{", encoding="utf-8")
            (d / "inv.json").write_text(json.dumps({"schema_version": "1.0.0"}), encoding="utf-8")
            for name, code in (("missing.json", "PLAN_NOT_FOUND"), ("bad.json", "PLAN_NOT_JSON"),
                               ("inv.json", "PLAN_INVALID")):
                with self.subTest(code=code), self.assertRaises(pc.PlanContractError) as ctx:
                    pc.load(d / name)
                self.assertEqual(ctx.exception.code, code)


class PublishedSchema(unittest.TestCase):
    """The schema file is the contract document: it must agree with the validator's constants."""

    def setUp(self):
        self.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.task = self.schema["$defs"]["task"]["properties"]

    def test_enums_match(self):
        self.assertEqual(tuple(self.task["complexity"]["enum"]), pc.COMPLEXITY)
        self.assertEqual(tuple(self.task["scope"]["enum"]), pc.SCOPE)
        self.assertEqual(tuple(self.task["kind"]["enum"]), pc.TASK_KINDS)
        self.assertEqual(tuple(self.schema["$defs"]["level"]["enum"]), pc.LEVELS)
        self.assertEqual(tuple(self.schema["$defs"]["verification"]["properties"]["type"]["enum"]),
                         pc.VERIFICATION_TYPES)
        self.assertEqual(tuple(self.schema["$defs"]["verification"]["properties"]["category"]["enum"]),
                         pc.VERIFICATION_CATEGORIES)

    def test_required_lists_match(self):
        self.assertEqual(tuple(self.schema["required"]), pc.TOP_REQUIRED)
        self.assertEqual(tuple(self.schema["$defs"]["task"]["required"]), pc.REQUIRED_TASK_KEYS)
        self.assertEqual(tuple(self.schema["$defs"]["milestone"]["required"]), pc.MILESTONE_KEYS)
        self.assertEqual(tuple(self.schema["$defs"]["verification"]["required"]), ("type", "value", "purpose"))

    def test_schema_1_2_required_fields_are_version_gated(self):
        extension = self.schema["allOf"][1]
        self.assertIn("^1\\.([2-9]|[1-9][0-9]+)\\.",
                      extension["if"]["properties"]["schema_version"]["pattern"])
        self.assertIn("requirements", extension["then"]["required"])
        task = extension["then"]["properties"]["tasks"]["items"]
        self.assertEqual(set(task["required"]), {"covers", "kind"})
        self.assertEqual(task["properties"]["verification"]["items"]["required"], ["category"])

    def test_forbidden_keys_listed_in_schema_are_forbidden_in_code(self):
        listed = {next(iter(item["required"])) for item in self.task and self.schema["$defs"]["task"]["not"]["anyOf"]}
        self.assertTrue(listed <= pc.FORBIDDEN_TASK_KEYS)


class SchedulerInterface(unittest.TestCase):
    """A consumer reads PLAN.json through `load`; the bundled example and the docs must stay true."""

    def test_bundled_example_loads_without_starting_anything(self):
        import subprocess
        from unittest.mock import patch
        with patch.object(subprocess, "Popen", side_effect=AssertionError), \
                patch.object(subprocess, "run", side_effect=AssertionError):
            plan_ = pc.load(MODULE / "data" / "plan.example.json")
        self.assertEqual([t["id"] for t in plan_["tasks"]], ["T1", "T2"])
        self.assertEqual((plan_["tasks"][0]["complexity"], plan_["tasks"][0]["risk"]), ("low", "high"))

    def test_readme_names_every_error_code_the_module_can_raise(self):
        import re
        doc = (MODULE / "README.md").read_text(encoding="utf-8")
        codes = set()
        for source in MODULE.glob("*.py"):
            codes |= set(re.findall(r'PlanContractError\(\s*"([A-Z_]+)"', source.read_text(encoding="utf-8")))
        self.assertTrue(codes, "no error codes found")
        for code in sorted(codes):
            if code in ("PLAN_EXISTS", "PLAN_MD_EMPTY", "PLAN_NOT_APPROVED"):
                continue  # planner-side refusals, listed with the CLI actions
            self.assertTrue(code in doc, f"{code} is raised but not documented")

    def test_readme_describes_every_cli_action(self):
        doc = (MODULE / "README.md").read_text(encoding="utf-8")
        for action in ("init", "check", "freeze", "show", "compat", "validate", "schema", "example"):
            self.assertIn(f"python -m bt_planner {action}", doc)


if __name__ == "__main__":
    unittest.main()
