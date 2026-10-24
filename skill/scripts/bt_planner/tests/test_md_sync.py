"""PLAN.md <-> PLAN.json: duplicated ids and contradictions in titles, repositories, dependencies and verification."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import contract as pc  # noqa: E402
from bt_planner import markdown as md  # noqa: E402
from support import PLAN_MD, PlanDir  # noqa: E402


class Grammar(unittest.TestCase):
    def problems(self, text: str) -> list[str]:
        return md.parse_document(text)["problems"]

    def test_duplicate_task_ids_name_their_lines(self):
        out = self.problems("### M1 — A\n- [ ] T1 — one\n- [ ] T2 — two\n- [ ] T1 — again\n")
        self.assertEqual(len(out), 1)
        self.assertIn("T1: defined 2 times", out[0])
        self.assertIn("lines 2, 4", out[0])

    def test_a_task_inside_a_comment_is_not_a_duplicate_and_lines_survive_comments(self):
        text = "<!--\n- [ ] T1 — hidden\n-->\n### M1 — A\n- [ ] T1 — real\n- [ ] T1 — dup\n"
        tasks = md.parse_document(text)["tasks"]
        self.assertEqual([t["line"] for t in tasks], [5, 6])  # comment newlines are kept

    def test_duplicate_milestone_heading(self):
        out = self.problems("### M1 — A\n- [ ] T1 — one\n### M1 — B\n- [ ] T2 — two\n")
        self.assertTrue(any("M1: milestone heading appears 2 times" in p for p in out), out)
        same = self.problems("### M1 — A\n- [ ] T1 — one\n### M1 — A\n- [ ] T2 — two\n")
        self.assertEqual(same, [])  # the same heading repeated names the same milestone

    def test_silently_dropped_values_are_reported(self):
        out = "\n".join(self.problems(
            "### M1 — A\n- [ ] T1 — one · after: T9 · after: T2 · verify: pytest · files: /etc/x · "
            "resources: a,,b\n- [ ] T2 — two · after: T1, later, T1\n"))
        for needle in ("field 'after' is given more than once", "'later' is not a task id",
                       "after: lists the same task more than once", "verify must be a backticked command",
                       "files: contains an empty entry or an absolute", "resources: contains an empty entry"):
            self.assertIn(needle, out)

    def test_clean_plan_has_no_problems(self):
        self.assertEqual(self.problems(PLAN_MD.format(status="approved")), [])

    def test_covers_and_kind_fields_are_parsed_and_invalid_values_reported(self):
        document = md.parse_document("### M1 — Base\n- [ ] T1 — Work · covers: R1, R2 · kind: test\n")
        self.assertEqual(document["tasks"][0]["covers"], ["R1", "R2"])
        self.assertEqual(document["tasks"][0]["kind"], "test")
        bad = self.problems("### M1 — Base\n- [ ] T1 — Work · covers: R1,,R2 · kind: \n")
        self.assertTrue(any("covers: needs a non-empty" in issue for issue in bad), bad)
        self.assertTrue(any("kind: needs a non-empty" in issue for issue in bad), bad)
        repeated = self.problems("### M1 — Base\n- [ ] T1 — Work · covers: R1, R1\n")
        self.assertTrue(any("covers: lists the same requirement" in issue for issue in repeated), repeated)


class Contradictions(PlanDir):
    def setUp(self):
        super().setUp()
        self.plan = self.good()

    def edit(self, fn) -> str:
        fn(self.plan)
        self.write(self.plan)
        return self.errors()

    def test_baseline_is_consistent(self):
        self.assertEqual(self.errors(), "")

    def test_schema_1_2_reports_declared_covers_and_kind_contradictions(self):
        text = PLAN_MD.format(status="approved").replace(
            "verify: `pytest tests/auth -q`",
            "verify: `pytest tests/auth -q` · covers: R2 · kind: audit",
        )
        self.md(text=text)
        out = self.errors()
        self.assertIn("T1.covers: PLAN.md has ['R2'], PLAN.json has ['R1']", out)
        self.assertIn("T1.kind: PLAN.md says 'audit', PLAN.json says 'implement'", out)

    def test_schema_13_membership_and_ui_annotations_round_trip(self):
        self.plan["schema_version"] = "1.3.0"
        self.plan["tasks"][0]["subplan_id"] = "SP-1"
        self.plan["tasks"][0]["ui"] = True
        self.write(self.plan)
        text = PLAN_MD.format(status="approved").replace(
            "verify: `pytest tests/auth -q`",
            "verify: `pytest tests/auth -q` · subplan: SP-1 · ui: yes",
        )
        self.md(text=text)
        self.assertEqual(self.sync.consistency(self.rdir, self.plan), [])

    def test_schema_13_reports_omitted_and_mismatched_membership_and_ui(self):
        self.plan["schema_version"] = "1.3.0"
        self.plan["tasks"][0]["subplan_id"] = "SP-1"
        self.plan["tasks"][0]["ui"] = True
        self.write(self.plan)
        out = "\n".join(self.sync.consistency(self.rdir, self.plan))
        self.assertIn("T1.subplan_id: PLAN.md says None, PLAN.json says 'SP-1'", out)
        self.assertIn("T1.ui: PLAN.md does not declare ui, PLAN.json says True", out)

        text = PLAN_MD.format(status="approved").replace(
            "verify: `pytest tests/auth -q`", "verify: `pytest tests/auth -q` · subplan: SP-2 · ui: no")
        self.md(text=text)
        out = "\n".join(self.sync.consistency(self.rdir, self.plan))
        self.assertIn("T1.subplan_id: PLAN.md says 'SP-2', PLAN.json says 'SP-1'", out)
        self.assertIn("T1.ui: PLAN.md says False, PLAN.json says True", out)

    def test_legacy_schema_does_not_compare_new_markdown_fields(self):
        self.plan["schema_version"] = "1.1.0"
        self.write(self.plan)
        self.md(text=PLAN_MD.format(status="approved").replace(
            "verify: `pytest tests/auth -q`",
            "verify: `pytest tests/auth -q` · covers: R2 · kind: audit",
        ))
        self.assertEqual(self.errors(), "")

    def test_skeleton_derives_spec_requirements_and_leaves_covers_empty(self):
        skeleton = self.sync.skeleton(self.rdir)
        self.assertEqual(skeleton["schema_version"], "1.2.0")
        self.assertEqual(skeleton["requirements"], ["R1"])
        self.assertTrue(all(task["covers"] == [] for task in skeleton["tasks"]))
        self.assertTrue(all("kind" not in task for task in skeleton["tasks"]))

    def test_duplicate_id_in_plan_md_is_rejected_even_if_json_looks_fine(self):
        self.md(text=PLAN_MD.format(status="approved") + "- [ ] T2 — Another second task · repo: backend\n")
        out = self.errors()
        self.assertIn("T2: defined 2 times in PLAN.md", out)

    def test_duplicate_id_in_plan_json(self):
        out = self.edit(lambda p: p["tasks"].append(dict(p["tasks"][1])))
        self.assertIn("T2: duplicate task id", out)

    def test_title_contradiction(self):
        out = self.edit(lambda p: p["tasks"][0].update(title="Rewrite the whole auth layer"))
        self.assertIn("T1.title: PLAN.md says 'Fix validation', PLAN.json says 'Rewrite the whole auth layer'", out)

    def test_underscores_inside_identifiers_are_part_of_the_title(self):
        self.md(text=PLAN_MD.format(status="approved").replace("Fix validation", "Implement disable_auth flag"))
        self.plan["tasks"][0]["title"] = "Implement disableauth flag"
        self.write(self.plan)
        self.assertIn("T1.title: PLAN.md says 'Implement disable_auth flag'", self.errors())
        self.plan["tasks"][0]["title"] = "Implement disable_auth flag"
        self.write(self.plan)
        self.assertEqual(self.errors(), "")
        self.plan["tasks"][0]["title"] = "Implement _disable_auth_ flag"  # emphasis around a whole word is formatting
        self.write(self.plan)
        self.assertEqual(self.errors(), "")

    def test_repeated_internal_underscores_are_not_markdown_emphasis(self):
        for markdown_title, json_title in (("foo__bar", "foobar"), ("foo___bar", "foo__bar"),
                                           ("disable_ auth", "disable auth"), ("a _ b", "a b")):
            with self.subTest(markdown_title=markdown_title, json_title=json_title):
                self.md(text=PLAN_MD.format(status="approved").replace("Fix validation", markdown_title))
                self.plan["tasks"][0]["title"] = json_title
                self.write(self.plan)
                self.assertIn("T1.title:", self.errors())

    def test_title_formatting_is_not_a_contradiction(self):
        self.assertEqual(self.edit(lambda p: p["tasks"][0].update(title="  fix   `validation` ")), "")

    def test_repository_contradiction(self):
        out = self.edit(lambda p: p["tasks"][1].update(repository="frontend"))
        self.assertIn("T2.repository: PLAN.md says repo 'backend', PLAN.json says 'frontend'", out)

    def test_dependency_contradictions(self):
        out = self.edit(lambda p: p["tasks"][2].update(after=["T1"]))
        self.assertIn("T3.after: PLAN.md has ['T1', 'T2'], PLAN.json has ['T1']", out)

    def test_dependency_with_a_nonexistent_task_in_plan_md_is_flagged(self):
        self.md(text=PLAN_MD.format(status="approved").replace("after: T1, T2", "after: T1, T2, T7"))
        self.assertIn("T3.after: PLAN.md has ['T1', 'T2', 'T7']", self.errors())

    def test_verification_contradiction(self):
        out = self.edit(lambda p: p["tasks"][0].update(verification=[
            {"type": "command", "value": "npm test", "purpose": "unit tests"}]))
        self.assertIn("T1.verification: PLAN.md verifies with `pytest tests/auth -q` but PLAN.json has only `npm test`",
                      out)

    def test_manual_only_verification_contradicts_a_stated_command(self):
        out = self.edit(lambda p: p["tasks"][0].update(verification=[
            {"type": "manual", "value": "open it", "purpose": "see", "expected": "it opens"}]))
        self.assertIn("PLAN.json has no command verification", out)

    def test_extra_json_verifications_are_not_a_contradiction(self):
        out = self.edit(lambda p: p["tasks"][0]["verification"].append(
            {"type": "command", "value": "ruff check", "purpose": "lint", "category": "static"}))
        self.assertEqual(out, "")

    def test_legacy_risk_on_the_same_scale_must_agree(self):
        self.md(text=PLAN_MD.format(status="approved").replace("T2 — Add tests", "T2 — Add tests · risk: high"))
        out = self.errors()
        self.assertIn("T2.risk: PLAN.md says risk: high, PLAN.json says medium", out)
        self.md(text=PLAN_MD.format(status="approved").replace("T2 — Add tests", "T2 — Add tests · risk: critical"))
        self.assertEqual(self.errors(), "")  # not on the contract scale: reported nowhere, never converted

    def test_files_and_resources_stated_in_plan_md_must_be_in_plan_json(self):
        self.md(text=PLAN_MD.format(status="approved").replace("files: tests/new/**", "files: tests/new/**, other/x.py")
                .replace("verify: `pytest -q`", "verify: `pytest -q` · resources: dbx"))
        out = self.errors()
        self.assertIn("T2.expected_paths: PLAN.md `files:` lists other/x.py", out)
        self.assertIn("T3.shared_resources: PLAN.md `resources:` lists dbx", out)
        self.plan["tasks"][1]["expected_paths"].append("other/x.py")  # JSON may carry more, never less
        self.plan["tasks"][2]["shared_resources"] = ["dbx"]
        self.write(self.plan)
        self.assertEqual(self.errors(), "")

    def test_misspelt_fields_and_near_miss_task_lines_are_reported(self):
        self.md(text=PLAN_MD.format(status="approved").replace("T3 — Wire it · after: T1, T2 · repo: backend",
                                                               "T3 — Wire it · after: T1, T2 · repository: frontend")
                + "- [ ] t4 — lowercase id\n- [ ] T-5 — dashed id\n")
        out = self.errors()
        self.assertIn("field 'repository:' is not read; the field is 'repo:'", out)
        self.assertIn("'t4' looks like a task line but is not a task id", out)
        self.assertIn("'T-5' looks like a task line", out)
        self.md(text=PLAN_MD.format(status="approved") + "- [ ] T3.1.2 — three levels\n- [ ] **T9** — bold\n"
                "- [ ] T8 no dash\n")
        out = self.errors()
        for token in ("'T3.1.2'", "'T9'", "'T8'"):
            self.assertIn(f"{token} looks like a task line", out)

    def test_duplicate_ids_in_plan_json_name_their_positions(self):
        self.plan["tasks"].append(dict(self.plan["tasks"][1]))
        self.write(self.plan)
        self.assertIn("T2: duplicate task id (tasks[1], tasks[3])", self.errors())

    def test_milestone_title_contradiction_and_duplicate_heading(self):
        out = self.edit(lambda p: p["milestones"][0].update(title="Something else"))
        self.assertIn("M1.title: PLAN.md heading says 'Base', PLAN.json says 'Something else'", out)
        self.md(text=PLAN_MD.format(status="approved").replace("### M2 — Next", "### M1 — Base again"))
        self.assertIn("M1: milestone heading appears 2 times", self.errors())

    def test_plan_md_ambiguity_is_reported_even_when_the_json_is_invalid(self):
        del self.plan["tasks"][0]["complexity"]
        self.write(self.plan)
        self.md(text=PLAN_MD.format(status="approved") + "- [ ] T1 — dup\n")
        out = self.errors()
        self.assertIn("T1.complexity", out)
        self.assertIn("T1: defined 2 times in PLAN.md", out)

    def test_init_refuses_an_ambiguous_plan_md(self):
        (self.rdir / "PLAN.json").unlink()
        self.md(text=PLAN_MD.format(status="approved") + "- [ ] T2 — dup\n")
        with self.assertRaises(pc.PlanContractError) as ctx:
            self.sync.write_skeleton(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_MD_AMBIGUOUS")
        self.assertFalse((self.rdir / "PLAN.json").exists())

    def test_compat_report_lists_md_problems(self):
        self.md(text=PLAN_MD.format(status="approved") + "- [ ] T2 — dup\n")
        self.assertTrue(any("T2: defined 2 times" in p for p in self.sync.compat(self.rdir)["plan_md_problems"]))


if __name__ == "__main__":
    unittest.main()
