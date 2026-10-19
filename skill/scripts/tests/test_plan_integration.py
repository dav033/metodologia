"""How the methodology uses the planner module: only through bt_plan_adapter, one direction, nothing duplicated.

The module's own behaviour is tested inside the module (bt_planner/tests). Here: the boundary seen from outside, the
module suite run as an isolated subprocess, the hooks in handoff / launch / run state, the CLI plumbing, and parity of the
module's PLAN.md parser with the supervisor's parser on every real plan in the repository.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
REPO = SCRIPTS.parent.parent

import bt_cli_plan  # noqa: E402
import bt_config  # noqa: E402
import bt_handoff  # noqa: E402
import bt_launch  # noqa: E402
import bt_plan_adapter as adapter  # noqa: E402
import bt_runstate as rs  # noqa: E402
import bt_planner as planner  # noqa: E402
from bt_planner import markdown as planner_markdown  # noqa: E402
from bt_planner import revisions as planner_revisions  # noqa: E402


def classified(rdir: Path) -> dict:
    plan = planner.skeleton(rdir, plan_id=adapter.plan_id(rdir))
    for milestone in plan["milestones"]:
        milestone["title"] = milestone["title"] or milestone["id"]
        milestone["acceptance_criteria"] = [f"{milestone['id']} delivered"]
    for task in plan["tasks"]:
        why = {"complexity": "the change follows a pattern already present in the module so little reasoning is needed",
               "scope": "one small localized change confined to a single component of the repository",
               "duration": "comparable to similar edits in this module including running its local tests",
               "risk": "a mistake is local reversible and caught by the task verification command",
               "coupling": "no other task edits the same files or depends on a shared contract",
               "confidence": "the affected code was read and a precedent for this exact change exists"}
        task.update({"objective": f"Deliver the behaviour described by {task['title']} and keep tests passing",
                     "repository": task.get("repository", "app"),
                     "complexity": "low", "scope": "small_change", "estimated_minutes": 30, "risk": "medium",
                     "coupling": "low", "confidence": "medium", "estimate_rationale": "Known pattern in this module",
                     "classification_evidence": {d: {"justification": f"{task['id']}: {sentence}",
                                                     "evidence": ["spec:SPEC.md#spec", "command:python3 -m unittest -> the tests of the module ran"]}
                                                 for d, sentence in why.items()},
                     "expected_paths": task.get("expected_paths", [f"src/{task['id'].lower()}/**"]),
                     "shared_resources": [], "acceptance_criteria": [f"{task['title']} works as described"]})
        task["covers"] = list(plan["requirements"][:1])
        task["kind"] = "implement"
        if not task.get("verification"):
            task["verification"] = [{"type": "manual", "value": "read the diff", "purpose": "review",
                                     "expected": "matches the objective"}]
        for verification in task["verification"]:
            verification.setdefault("category", "functional")
    return plan


PLAN_MD = """---
status: {status}
---
# Plan

### M1 — Auth fix
- [ ] T1 — Reject expired sessions · repo: app · files: src/auth/** · verify: `python -m unittest`
- [ ] T2 — Document it · repo: app · after: T1
"""


class Isolated(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="plan-integration-")
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name) / "bitacora"
        self.rdir = self.root / "sample" / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("# Spec\n## Requirements\n- R1. Demo requirement\n", encoding="utf-8")
        self.set_status("draft")
        for target, value in (("bt_handoff.ROOT", self.root), ("bt_launch.ROOT", self.root)):
            patcher = patch(target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        repos = patch.object(bt_handoff.ws, "repos", lambda root, project: {"app": Path(self._tmp.name)})
        repos.start()
        self.addCleanup(repos.stop)
        cfg = patch.object(bt_config, "get", side_effect=lambda key, default=None: default)
        cfg.start()
        self.addCleanup(cfg.stop)

    def set_status(self, status: str) -> None:
        (self.rdir / "PLAN.md").write_text(PLAN_MD.format(status=status), encoding="utf-8")

    def good_plan(self) -> dict:
        plan = classified(self.rdir)
        (self.rdir / "PLAN.json").write_text(planner.dumps(plan), encoding="utf-8")
        return plan

    def compatibility_report(self) -> dict[str, object]:
        import bt_scheduler_adapter
        return bt_scheduler_adapter.plan_compatibility_report(self.rdir)


class Handoff(Isolated):
    def test_plans_without_the_contract_are_untouched(self):
        self.assertEqual(adapter.handoff_problems(self.rdir), [])
        self.assertFalse(any("PLAN.json" in p for p in bt_handoff.assess("sample", self.rdir)["problems"]))

    def test_an_incomplete_plan_json_blocks_the_handoff(self):
        planner.write_skeleton(self.rdir)
        report = bt_handoff.assess("sample", self.rdir)
        self.assertFalse(report["ok"] or report["auto"])
        self.assertTrue(any(p.startswith("PLAN.json: T1.") for p in report["problems"]), report["problems"])
        self.assertTrue(any("plan-json check REQ-001" in p for p in report["problems"]))

    def test_a_complete_plan_json_passes(self):
        self.good_plan()
        self.assertFalse(any("PLAN.json" in p for p in bt_handoff.assess("sample", self.rdir)["problems"]))


class Launch(Isolated):
    def launch_until_after_freeze(self):
        class Stop(Exception):
            pass
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch.ws, "clone_missing"), patch.object(bt_launch, "scheduler_script", side_effect=Stop):
            with self.assertRaises(Stop):
                bt_launch.launch("sample", "REQ-001")

    def test_launch_binds_the_revision_frozen_at_approval_and_never_creates_it(self):
        self.good_plan()
        self.set_status("approved")  # approved by hand: no approval record
        with self.assertRaises(SystemExit) as ctx:
            self.launch_until_after_freeze()
        self.assertIn("PLAN_NOT_FROZEN", str(ctx.exception))
        self.assertEqual(planner.list_revisions(self.rdir), [])
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        self.launch_until_after_freeze()
        self.launch_until_after_freeze()  # idempotent on retry
        self.assertEqual([r["revision"] for r in planner.list_revisions(self.rdir)], [1])

    def test_launch_refuses_an_invalid_approved_plan_json(self):
        planner.write_skeleton(self.rdir)
        self.set_status("approved")
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}):
            with self.assertRaises(SystemExit) as ctx:
                bt_launch.launch("sample", "REQ-001")
        self.assertIn("PLAN_INVALID", str(ctx.exception))
        self.assertEqual(planner.list_revisions(self.rdir), [])

    def test_a_plan_without_plan_json_is_refused_and_never_runs(self):
        self.set_status("approved")
        with self.assertRaisesRegex(SystemExit, "PLAN_NOT_FROZEN.*plan-json init"):
            self.launch_until_after_freeze()
        self.assertFalse((self.rdir / "plan-revisions").exists())

    def test_dry_run_never_writes(self):
        self.good_plan()
        self.set_status("approved")
        planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        before = sorted(p.name for p in (self.rdir / "plan-revisions").iterdir())
        with patch.object(bt_launch, "find_req", return_value=self.rdir), \
                patch("bt_requirements_gate.require_ready", return_value={"status": "ready"}), \
                patch.object(bt_launch, "scheduler_script", side_effect=RuntimeError("stop")), \
                self.assertRaises(RuntimeError):
            bt_launch.launch("sample", "REQ-001", dry_run=True)
        self.assertEqual(sorted(p.name for p in (self.rdir / "plan-revisions").iterdir()), before)


class RunState(Isolated):
    def test_new_run_records_plan_ref_only_when_a_revision_is_frozen(self):
        self.assertNotIn("plan_ref", rs.init_state("sample", self.rdir, "claude", "haiku", False))
        self.good_plan()
        self.set_status("approved")
        entry = planner.approve_freeze(self.rdir, adapter.plan_id(self.rdir), adapter.APPROVED_STATES)
        state = rs.init_state("sample", self.rdir, "claude", "haiku", False)
        self.assertEqual(state["plan_ref"], {"plan_id": "REQ-001", "revision": 1, "sha256": entry["sha256"]})
        self.assertNotIn("plan", state)  # the run never copies the plan: one source of truth

    def test_an_existing_run_json_is_never_modified_by_planner_operations(self):  # AC-11
        run = self.rdir / "RUN.json"
        run.write_text(json.dumps({"req": "REQ-001", "status": "running", "sessions": 3,
                                   "tasks": [{"id": "T1", "status": "done", "attempts": 2}]}), encoding="utf-8")
        before = run.read_bytes()
        self.set_status("approved")
        planner.write_skeleton(self.rdir)
        self.good_plan()
        adapter.run_cli("check", self.rdir, emit=lambda _: None)
        report = self.compatibility_report()
        adapter.run_cli("freeze", self.rdir, emit=lambda _: None, compatibility_report=report)
        adapter.run_cli("compat", self.rdir, emit=lambda _: None, compatibility_report=report)
        adapter.freeze_on_launch(self.rdir, compatibility_report=report)
        adapter.handoff_problems(self.rdir, compatibility_report=report)
        self.assertEqual(run.read_bytes(), before)

    def test_a_damaged_store_leaves_a_trace_and_does_not_stop_the_run(self):
        (self.rdir / "plan-revisions").mkdir()
        (self.rdir / "plan-revisions" / "MANIFEST.json").write_text("{", encoding="utf-8")
        state = rs.init_state("sample", self.rdir, "claude", "haiku", False)
        self.assertEqual(state["plan_ref_error"], "REVISION_STORE_UNREADABLE")
        self.assertNotIn("plan_ref", state)


class Cli(Isolated):
    def invoke(self, action: str, **flags) -> int:
        import argparse
        args = argparse.Namespace(action=action, req="REQ-001", force=False, json=False, **flags)
        with contextlib.redirect_stdout(io.StringIO()):
            return bt_cli_plan.dispatch(args, self.root, "sample")

    def test_command_plumbing_uses_the_requirement_id_and_the_methodology_states(self):
        self.assertEqual(self.invoke("init"), 0)
        self.assertEqual(self.invoke("check"), 2)
        self.good_plan()
        self.assertEqual(self.invoke("check"), 0)
        self.assertEqual(self.invoke("freeze"), 2)  # still `draft`
        self.set_status("approved")
        self.assertEqual(self.invoke("freeze"), 0)
        self.assertEqual(self.invoke("show"), 0)
        self.assertEqual(self.invoke("compat"), 0)
        self.assertEqual(self.invoke("bind"), 0)  # the launch gate, read-only
        self.assertEqual(self.invoke("report"), 0)
        self.assertEqual(adapter.plan_id(self.rdir), "REQ-001")

    def test_parser_registers_the_command(self):
        import argparse
        parser = argparse.ArgumentParser()
        bt_cli_plan.add_parser(parser.add_subparsers(dest="cmd"))
        self.assertEqual(parser.parse_args(["plan-json", "check", "REQ-009"]).action, "check")


class RefVerifier(Isolated):
    def test_it_knows_requirements_tasks_decisions_commands_and_commits(self):
        import bt_core
        project = self.rdir.parent.parent
        (project / "DECISIONS.md").write_text("## D-007 — x\n", encoding="utf-8")
        (project / "PENDING.md").write_text("- P-012 · y\n", encoding="utf-8")
        with patch.object(bt_core, "ROOT", self.root):  # never the owner's real bitácora
            verify = adapter.ref_verifier(self.rdir)
        self.assertTrue(verify("precedent", "REQ-001", ""))
        self.assertTrue(verify("precedent", "REQ-001/T1", ""))
        self.assertFalse(verify("precedent", "REQ-001/T9", ""))
        self.assertFalse(verify("precedent", "REQ-777", ""))
        self.assertTrue(verify("precedent", "D-007", ""))
        self.assertFalse(verify("precedent", "D-008", ""))
        self.assertTrue(verify("precedent", "P-012", ""))
        self.assertIsNone(verify("precedent", "https://example.test/x", ""))
        self.assertTrue(verify("command", "python3 -m unittest", "app"))
        self.assertTrue(verify("command", "FOO=1 python3 -c 'pass'", "app"))
        self.assertFalse(verify("command", "no-such-binary-xyz --help", ""))

    def test_a_real_interpreter_in_front_of_a_missing_script_or_npm_script_is_not_evidence(self):
        repo = Path(self._tmp.name)
        (repo / "scripts").mkdir()
        (repo / "scripts" / "real.py").write_text("print(1)\n", encoding="utf-8")
        (repo / "package.json").write_text('{"scripts": {"test": "x", "build": "y"}}', encoding="utf-8")
        import bt_core
        with patch.object(bt_core, "ROOT", self.root):
            verify = adapter.ref_verifier(self.rdir)
        self.assertTrue(verify("command", "python3 scripts/real.py --x", "app"))
        self.assertFalse(verify("command", "python3 scripts/does-not-exist.py", "app"))
        self.assertTrue(verify("command", "python3 -m unittest discover", "app"))
        self.assertTrue(verify("command", "npm run build", "app"))
        self.assertFalse(verify("command", "npm run nope", "app"))
        self.assertTrue(verify("command", "npm test", "app"))
        self.assertFalse(verify("command", "npx tsx scripts/missing.ts", "app"))
        self.assertFalse(verify("precedent", "XYZ-999999", "app"))
        self.assertFalse(verify("precedent", "JIRA-12", "app"))


class ParserParity(unittest.TestCase):
    """The module keeps its own PLAN.md parser so it can stand alone; this keeps both parsers from drifting apart."""

    FIELDS = ("id", "done", "milestone", "title", "repo", "verify", "after", "files", "resources")
    SIZE_WORDS = {"s": "S", "small": "S", "low": "S", "m": "M", "medium": "M", "med": "M", "l": "L", "large": "L",
                  "high": "L", "xl": "L"}  # the supervisor's own normalisation; the module reports the raw word

    def compare(self, text: str, label: str) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PLAN.md"
            path.write_text(text, encoding="utf-8")
            theirs, their_stones = rs.parse_plan(path), rs.milestones(path)
        ours, our_stones = planner_markdown.parse(text)
        self.assertEqual([t["id"] for t in ours], [t["id"] for t in theirs], label)
        for mine, other in zip(ours, theirs):
            for field in self.FIELDS:
                self.assertEqual(mine[field], other[field], f"{label} {mine['id']}.{field}")
            self.assertEqual(mine["risk"], other["risk"], f"{label} {mine['id']}.risk")
            self.assertEqual(self.SIZE_WORDS.get(mine["complexity"] or ""), other["complexity"],
                             f"{label} {mine['id']}.complexity")
        self.assertEqual(our_stones, their_stones, label)

    def test_synthetic_document(self):
        self.compare("""---
status: approved
---
<!-- - [ ] T9 — hidden · after: T1 -->
### M1 — First
- [ ] T1 — Do it · repo: backend · files: src/a.py, tests/** · verify: `pytest -k "a · b"` · risk: HIGH
- [x] T2.1: Next · after: T1, T0a, junk · resources: db, queue · complexity: Large
- [ ] T2.2 — Sized · size: m · risk: critical
### M2 - Second
- [ ] T3a -- Other · files: ../secret
## Appendix
- [ ] T4 — Orphan
#### M3 Deep
* [ ] T5 – Star bullet
""", "synthetic")

    def test_every_real_plan_in_the_repository(self):
        plans = sorted((REPO / "bitacora").glob("*/requirements/*/PLAN.md"))
        if not plans:
            self.skipTest("no real plans in this checkout")
        for plan in plans:
            with self.subTest(plan=plan.parent.name):
                self.compare(plan.read_text(encoding="utf-8"), plan.parent.name)


class RealHistoricalPlans(unittest.TestCase):
    """AC-13: compatibility is read-only and honest on REQ-013/015/016 of the pictures project."""

    REQUIREMENTS = REPO / "bitacora" / "pictures" / "requirements"
    CLASSIFICATION = ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence", "estimate_rationale")

    @staticmethod
    def digest(folder: Path) -> dict[str, str]:
        return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(folder.rglob("*")) if p.is_file()}

    def folder(self, req: str) -> Path:
        found = sorted(self.REQUIREMENTS.glob(f"{req}-*"))
        if not found:
            self.skipTest(f"{req} not present in this checkout")
        return found[0]

    def test_compat_changes_nothing_and_reports_missing_classification(self):
        for req in ("REQ-013", "REQ-015", "REQ-016"):
            with self.subTest(req=req):
                folder = self.folder(req)
                before = self.digest(folder)
                info = planner.compat(folder, adapter.plan_id(folder))
                planner.skeleton(folder, adapter.plan_id(folder))
                self.assertEqual(self.digest(folder), before)
                self.assertFalse((folder / "PLAN.json").exists() or (folder / "plan-revisions").exists())
                self.assertGreater(info["task_count"], 0)
                for task in info["tasks"]:
                    for key in self.CLASSIFICATION:
                        self.assertIn(key, task["needs_enrichment"])
                        self.assertNotIn(key, task["derived"])

    def test_plans_without_milestone_headings_are_flagged(self):
        info = planner.compat(self.folder("REQ-013"))
        self.assertEqual(info["milestones_in_md"], [])
        self.assertEqual(len(info["tasks_without_milestone"]), info["task_count"])

    def test_a_finished_run_json_keeps_its_bytes_and_has_no_plan_ref(self):
        run = self.folder("REQ-016") / "RUN.json"
        if not run.exists():
            self.skipTest("REQ-016 has no RUN.json here")
        before = run.read_bytes()
        planner.compat(run.parent)
        self.assertEqual(run.read_bytes(), before)
        self.assertNotIn(b"plan_ref", before)


class Wiring(unittest.TestCase):
    def test_skill_routes_to_the_reference_and_the_reference_to_the_module(self):
        skill = (REPO / "skill" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/plan-contract.md", skill)
        doc = (REPO / "skill" / "references" / "plan-contract.md").read_text(encoding="utf-8")
        self.assertIn("bt_planner/README.md", doc)
        self.assertTrue(planner_revisions.DIR in doc)

    def test_module_convention_is_documented(self):
        doc = (REPO / "skill" / "references" / "modules.md").read_text(encoding="utf-8")
        for needle in ("bt_planner", "adapter", "test_boundaries"):
            self.assertIn(needle, doc)


if __name__ == "__main__":
    unittest.main()
