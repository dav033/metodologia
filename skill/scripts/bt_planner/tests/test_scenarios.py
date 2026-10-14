"""Representative planning scenarios, run through the module end to end.

`scenarios/<name>/` holds six plans written for real repositories (a sensitive one-function fix, a mechanical rename, a
cross-contract change with an unknown consumer, a new feature, an investigation, a system-level migration) as a planner
produced them: SPEC.md, PLAN.md, PLAN.json and EXPECT.json (what a reviewer asserts about the plan). They are the
fixtures of REQ-012's planning trials; the trials themselves (which also verify the evidence against the real
checkouts) live with that requirement. Here nothing depends on the machine: `file:` evidence is reported as unverified.

For each scenario: it publishes; its classification and critical path are what a reviewer expects; ten kinds of
corruption are each refused with a diagnosis naming the cause; approving freezes exactly the bytes approved; a later edit
is a new revision, never a silent change.
"""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from bt_planner import contract as pc  # noqa: E402
from bt_planner import quality  # noqa: E402
from bt_planner import revisions as rev  # noqa: E402
from bt_planner import sync  # noqa: E402

SCENARIOS = Path(__file__).resolve().parent / "scenarios"
NAMES = sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()) if SCENARIOS.is_dir() else []


class Scenarios(unittest.TestCase):
    def setUp(self):
        self.assertTrue(NAMES, "scenario fixtures are missing")

    def copy(self, name: str) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        target = Path(tmp.name) / name
        shutil.copytree(SCENARIOS / name, target)
        (target / "EXPECT.json").unlink()
        return target

    def plan(self, rdir: Path) -> dict:
        return json.loads((rdir / "PLAN.json").read_text(encoding="utf-8"))

    def test_there_are_six_representative_scenarios_covering_distinct_intents(self):
        intents = {json.loads((SCENARIOS / n / "EXPECT.json").read_text())["intent"] for n in NAMES}
        self.assertEqual(intents, {"sensitive-small-fix", "mechanical-large-change", "cross-contract", "new-feature",
                                   "investigation", "full-system-decomposition"})

    def test_each_scenario_publishes_and_meets_its_expectations(self):
        for name in NAMES:
            with self.subTest(scenario=name):
                rdir = self.copy(name)
                report = sync.check(rdir)
                self.assertEqual(report.errors, [], name)
                plan = self.plan(rdir)
                by_id = {t["id"]: t for t in plan["tasks"]}
                expect = json.loads((SCENARIOS / name / "EXPECT.json").read_text())
                analysis = quality.analyze(plan)
                if "critical_path" in expect:
                    self.assertEqual(analysis["critical_path"]["tasks"], expect["critical_path"])
                for tid, wanted in expect.get("classify", {}).items():
                    self.assertEqual({k: by_id[tid][k] for k in wanted}, wanted)
                if "low_confidence" in expect:
                    self.assertEqual(analysis["low_confidence"], sorted(expect["low_confidence"]))
                self.assertEqual(analysis["unordered_conflicts"], [])
                self.assertFalse(any(t["scope"] == "full_system" for t in plan["tasks"]), "must be decomposed")
                for task in plan["tasks"]:  # every dimension argued, none boilerplate shared with a neighbour
                    texts = [e["justification"] for e in task["classification_evidence"].values()]
                    self.assertEqual(len(set(texts)), len(texts), task["id"])

    def test_dimensions_stay_independent_in_real_plans(self):
        seen = set()
        for name in NAMES:
            for task in self.plan(SCENARIOS / name)["tasks"]:
                seen.add((task["complexity"], task["risk"]))
        self.assertIn(("low", "high"), seen)       # easy but sensitive (AC-04)
        self.assertIn(("high", "high"), seen)
        self.assertIn(("low", "low"), seen)
        self.assertTrue({"medium", "high"} <= {c for c, _ in seen})

    def test_uncertainty_is_kept_not_hidden(self):  # AC-09
        low = []
        for name in NAMES:
            for task in self.plan(SCENARIOS / name)["tasks"]:
                if task["confidence"] == "low":
                    low.append((name, task["id"]))
                    self.assertTrue(task["classification_evidence"]["confidence"]["justification"])
        self.assertGreaterEqual(len(low), 5)

    def test_every_corruption_is_refused_with_the_cause(self):
        for name in NAMES:
            rdir = self.copy(name)
            good = self.plan(rdir)
            md = (rdir / "PLAN.md").read_text(encoding="utf-8")
            first = good["tasks"][0]
            dependent = next(t for t in good["tasks"] if t["after"])

            def refused(label: str, plan: dict, needle: str, text: str | None = None, *, rdir=rdir, md=md, name=name) -> None:
                (rdir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
                (rdir / "PLAN.md").write_text(text or md, encoding="utf-8")
                errors = "\n".join(sync.check(rdir).errors)
                self.assertIn(needle, errors, f"{name}: {label}")

            with self.subTest(scenario=name):
                m = copy.deepcopy(good)
                refused("duplicate id in PLAN.md", m, f"{first['id']}: defined 2 times in PLAN.md",
                        md + f"- [ ] {first['id']} — Again · repo: {first['repository']}\n")
                m = copy.deepcopy(good)
                m["tasks"].append(copy.deepcopy(m["tasks"][0]))
                refused("duplicate id in PLAN.json", m, f"{first['id']}: duplicate task id")
                m = copy.deepcopy(good)
                m["tasks"][0]["title"] = "Rewrite everything"
                refused("title", m, f"{first['id']}.title")
                m = copy.deepcopy(good)
                m["tasks"][0]["repository"] = "elsewhere"
                refused("repository", m, f"{first['id']}.repository")
                m = copy.deepcopy(good)
                next(t for t in m["tasks"] if t["id"] == dependent["id"])["after"] = []
                refused("dependency", m, f"{dependent['id']}.after")
                m = copy.deepcopy(good)
                m["tasks"][0]["verification"] = [{"type": "command", "value": "make verify-everything",
                                                  "purpose": "a different command than PLAN.md states"}]
                if f"{first['id']} —" in md and "verify: `" in md.split(f"{first['id']} —")[1].split("\n")[0]:
                    refused("verification", m, f"{first['id']}.verification")
                m = copy.deepcopy(good)
                del m["tasks"][0]["classification_evidence"]["risk"]
                refused("evidence missing", m, f"{first['id']}.classification_evidence.risk")
                m = copy.deepcopy(good)
                m["tasks"][0]["classification_evidence"]["duration"]["justification"] = "n/a"
                refused("placeholder", m, "duration.justification")
                m = copy.deepcopy(good)
                m["tasks"][0]["confidence"] = "high"
                for entry in m["tasks"][0]["classification_evidence"].values():
                    entry["evidence"] = ["assumption:it is probably fine"]
                refused("high confidence on assumptions", m, f"{first['id']}.confidence")
                m = copy.deepcopy(good)
                m["tasks"][0]["risk"] = "critical"
                refused("invalid enum", m, f"{first['id']}.risk")

    def test_approval_freezes_exactly_what_was_approved_and_edits_become_revisions(self):
        for name in NAMES:
            with self.subTest(scenario=name):
                rdir = self.copy(name)
                good = self.plan(rdir)
                entry = sync.approve_freeze(rdir)
                self.assertEqual(entry["sha256"], rev.sha256(pc.dumps(good)))
                self.assertEqual(sync.bind_approved(rdir)["revision"], 1)
                edited = copy.deepcopy(good)
                edited["tasks"][0]["estimated_minutes"] += 10
                (rdir / "PLAN.json").write_text(pc.dumps(edited), encoding="utf-8")
                self.assertTrue(any("frozen and PLAN.json differs" in e for e in sync.check(rdir).errors))
                edited["revision"] = 2
                (rdir / "PLAN.json").write_text(pc.dumps(edited), encoding="utf-8")
                with self.assertRaises(pc.PlanContractError) as ctx:
                    sync.bind_approved(rdir)
                self.assertEqual(ctx.exception.code, "PLAN_DRIFT")
                sync.approve_freeze(rdir)
                self.assertEqual([r["revision"] for r in rev.list_revisions(rdir)], [1, 2])
                self.assertEqual(rev.load_revision(rdir, 1)["tasks"][0]["estimated_minutes"],
                                 good["tasks"][0]["estimated_minutes"])

    def test_a_system_level_task_alone_is_refused_but_its_decomposition_publishes(self):
        rdir = self.copy("TRAIN-6-postgres-migration")
        plan = self.plan(rdir)
        lone = copy.deepcopy(plan["tasks"][0])
        lone.update(id="T1", scope="full_system", complexity="extreme", after=[], milestone_id="M1")
        for entry in lone["classification_evidence"].values():  # the other tasks of the decomposition are gone
            entry["evidence"] = [r for r in entry["evidence"] if not r.startswith("task:")] or ["assumption:one unit"]
        plan["tasks"], plan["milestones"] = [lone], plan["milestones"][:1]
        (rdir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")
        (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n### M1 — Decide and prepare\n"
                                      "- [ ] T1 — Write the persistence port and decide the driver and migration "
                                      "strategy · repo: trainingapp\n", encoding="utf-8")
        self.assertTrue(any("full_system must be decomposed" in e for e in pc.validate(plan).errors))
        lone["scope_exception"] = {"reason": "the owner reviews the migration as one unit"}
        report = pc.validate(plan)
        self.assertTrue(report.ok)
        self.assertTrue(any("scope_exception" in w for w in report.warnings))


if __name__ == "__main__":
    unittest.main()
