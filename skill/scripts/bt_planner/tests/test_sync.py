"""bt_planner sync: skeleton, PLAN.md consistency, immutable revisions, store robustness, compat, CLI."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # the folder that contains the bt_planner package
sys.path.insert(0, str(Path(__file__).resolve().parent))

from bt_planner import cli
from bt_planner import contract as pc
from bt_planner import revisions as rev
from bt_planner import sync
from support import classify

PLAN_MD = """---
req: REQ-042
status: {status}
created: 2026-10-14
---
# Plan — demo

## Tasks

### M1 — Base
- [ ] T1 — Fix validation · repo: backend · files: src/auth/**, tests/auth/** · verify: `pytest tests/auth -q`
- [ ] T2 — Add tests · after: T1 · repo: backend

### M2 — Next
- [ ] T3 — Wire it · after: T1, T2 · repo: backend · verify: `pytest -q`
"""


def tree_digest(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def classified_legacy(rdir: Path, *, plan_id: str | None = None) -> dict:
    skeleton = sync.skeleton(rdir, plan_id=plan_id)
    skeleton["schema_version"] = "1.2.0"
    return classify(skeleton)


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.rdir = self.root / "REQ-042-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "SPEC.md").write_text("# spec\n## Requirements\n- R1. Demo requirement\n", encoding="utf-8")
        self.write_md("approved")

    def write_md(self, status: str, text: str | None = None) -> None:
        (self.rdir / "PLAN.md").write_text((text or PLAN_MD).format(status=status) if text is None else text,
                                           encoding="utf-8")

    def write_json(self, plan: dict) -> None:
        (self.rdir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")

    def good(self) -> dict:
        plan = classified_legacy(self.rdir)
        self.write_json(plan)
        return plan


class Skeleton(Base):
    def test_skeleton_carries_only_what_plan_md_states(self):
        sk = sync.skeleton(self.rdir)
        self.assertEqual([t["id"] for t in sk["tasks"]], ["T1", "T2", "T3"])
        self.assertEqual(sk["tasks"][2]["after"], ["T1", "T2"])
        self.assertEqual([m["id"] for m in sk["milestones"]], ["M1", "M2"])
        self.assertEqual(sk["tasks"][0]["expected_paths"], ["src/auth/**", "tests/auth/**"])
        for key in ("complexity", "scope", "risk", "coupling", "confidence", "estimated_minutes", "objective"):
            self.assertNotIn(key, sk["tasks"][0])  # never defaulted silently

    def test_skeleton_is_not_publishable_until_classified(self):
        sync.write_skeleton(self.rdir)
        report = sync.check(self.rdir)
        self.assertFalse(report.ok)
        self.assertTrue(any("T1.complexity" in e for e in report.errors))

    def test_init_refuses_to_overwrite_unless_forced(self):
        sync.write_skeleton(self.rdir)
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.write_skeleton(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_EXISTS")
        sync.write_skeleton(self.rdir, force=True)

    def test_init_needs_tasks(self):
        self.write_md("approved", text="# empty\n")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.write_skeleton(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_MD_EMPTY")


class Consistency(Base):
    def test_classified_plan_is_consistent(self):
        self.good()
        report = sync.check(self.rdir)
        self.assertEqual(report.errors, [])

    def assertCheckMentions(self, plan: dict, *needles: str) -> None:
        self.write_json(plan)
        out = "\n".join(sync.check(self.rdir).errors)
        for needle in needles:
            self.assertIn(needle, out)

    def test_task_missing_from_json_and_extra_in_json(self):
        plan = classified_legacy(self.rdir)
        extra = dict(plan["tasks"][2], id="T4", after=["T3"])
        missing = plan["tasks"].pop(0)
        for t in plan["tasks"]:
            t["after"] = [a for a in t["after"] if a != missing["id"]]
        plan["tasks"].append(extra)
        self.assertCheckMentions(plan, "T1: in PLAN.md but missing from PLAN.json",
                                 "T4: in PLAN.json but missing from PLAN.md")

    def test_wrong_milestone_and_wrong_dependencies(self):
        plan = classified_legacy(self.rdir)
        plan["tasks"][1]["milestone_id"] = "M2"
        plan["tasks"][2]["after"] = ["T1"]
        self.assertCheckMentions(plan, "T2.milestone_id", "PLAN.md puts it under M1", "T3.after")

    def test_milestone_mismatches(self):
        plan = classified_legacy(self.rdir)
        plan["milestones"][1] = {"id": "M3", "title": "x", "acceptance_criteria": ["y"]}
        plan["tasks"][2]["milestone_id"] = "M3"
        self.assertCheckMentions(plan, "M3: milestone in PLAN.json has no `### M3` heading",
                                 "M2: milestone heading in PLAN.md missing from PLAN.json")

    def test_plan_id_and_spec_ref(self):
        plan = classified_legacy(self.rdir)
        plan["plan_id"], plan["spec_ref"] = "REQ-999", "NOPE.md"
        self.assertCheckMentions(plan, "plan.plan_id", "plan.spec_ref")

    def test_missing_and_unreadable_plan_json(self):
        self.assertIn("not found", "\n".join(sync.check(self.rdir).errors))
        (self.rdir / "PLAN.json").write_text("{", encoding="utf-8")
        self.assertIn("unreadable", "\n".join(sync.check(self.rdir).errors))

    def test_checkbox_progress_is_not_part_of_the_contract(self):
        self.good()
        text = (self.rdir / "PLAN.md").read_text(encoding="utf-8").replace("[ ] T1", "[x] T1")
        self.write_md("approved", text=text)
        self.assertTrue(sync.check(self.rdir).ok)


class Revisions(Base):
    def test_freeze_requires_approval_and_a_clean_check(self):
        self.good()
        self.write_md("in-progress")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_NOT_APPROVED")
        self.write_md("approved")
        (self.rdir / "PLAN.json").write_text(pc.dumps(sync.skeleton(self.rdir)), encoding="utf-8")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_INVALID")

    def test_freeze_is_idempotent_and_read_only(self):
        self.good()
        first = sync.approve_freeze(self.rdir)
        self.assertEqual(sync.approve_freeze(self.rdir), first)
        target = rev.revision_path(self.rdir, 1)
        self.assertTrue(target.exists())
        self.assertEqual(target.stat().st_mode & 0o222, 0)
        self.assertEqual([r["revision"] for r in rev.list_revisions(self.rdir)], [1])

    def test_an_edit_after_approval_is_a_draft_and_its_approval_is_the_next_revision(self):  # AC-10, D-134
        plan = self.good()
        sync.approve_freeze(self.rdir)
        plan["tasks"][0]["estimated_minutes"] = 90
        self.write_json(plan)
        self.assertTrue(sync.check(self.rdir).ok)                  # the working PLAN.json is a draft, not a revision
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.bind_approved(self.rdir)
        self.assertEqual(ctx.exception.code, "PLAN_DRIFT")
        sync.approve_freeze(self.rdir)                             # the store numbers it: the draft's field is not used
        self.assertEqual([r["revision"] for r in rev.list_revisions(self.rdir)], [1, 2])
        self.assertEqual(rev.load_revision(self.rdir, 1)["tasks"][0]["estimated_minutes"], 30)  # history recoverable
        self.assertEqual(rev.load_revision(self.rdir, 2)["tasks"][0]["estimated_minutes"], 90)

    def test_the_store_numbers_revisions_whatever_the_draft_says(self):
        plan = self.good()
        plan["revision"] = 3
        self.write_json(plan)
        self.assertEqual(sync.approve_freeze(self.rdir)["revision"], 1)
        self.assertEqual(rev.load_revision(self.rdir, 1)["revision"], 1)
        with self.assertRaises(pc.PlanContractError) as ctx:          # the store itself still refuses a gap
            rev.freeze(self.rdir, {**plan, "revision": 3})
        self.assertEqual(ctx.exception.code, "REVISION_ORDER")

    def test_tampering_with_a_frozen_file_is_detected(self):
        self.good()
        sync.approve_freeze(self.rdir)
        target = rev.revision_path(self.rdir, 1)
        os.chmod(target, 0o644)
        target.write_text(target.read_text(encoding="utf-8").replace('"low"', '"high"', 1), encoding="utf-8")
        self.assertTrue(any("changed after it was frozen" in e for e in sync.check(self.rdir).errors))
        with self.assertRaises(pc.PlanContractError) as ctx:
            rev.load_revision(self.rdir, 1)
        self.assertEqual(ctx.exception.code, "REVISION_TAMPERED")

    def test_unknown_revision(self):
        with self.assertRaises(pc.PlanContractError) as ctx:
            rev.load_revision(self.rdir, 7)
        self.assertEqual(ctx.exception.code, "REVISION_UNKNOWN")

    def test_formatting_changes_do_not_count_as_changes(self):
        plan = self.good()
        sync.approve_freeze(self.rdir)
        (self.rdir / "PLAN.json").write_text(json.dumps(plan, indent=4, sort_keys=True), encoding="utf-8")
        self.assertTrue(sync.check(self.rdir).ok)


class StoreRobustness(Base):
    """Reviewer findings on the revision store and the gate."""

    def test_check_never_raises_on_structurally_bad_plans(self):
        plan = classified_legacy(self.rdir)
        for mutate in (lambda p: p["tasks"][1].update(after=[[]]), lambda p: p.update(milestones=5),
                       lambda p: p["milestones"].__setitem__(0, {"id": []}), lambda p: p.update(tasks="x"),
                       lambda p: p["tasks"][0].update(milestone_id={})):
            broken = json.loads(json.dumps(plan))
            mutate(broken)
            (self.rdir / "PLAN.json").write_text(json.dumps(broken), encoding="utf-8")
            report = sync.check(self.rdir)
            self.assertFalse(report.ok)
            self.assertTrue(any("not evaluated" in w for w in report.warnings) or report.errors)

    def test_spec_ref_cannot_escape_the_requirement_folder(self):
        plan = classified_legacy(self.rdir)
        plan["spec_ref"] = "../../outside.md"
        self.write_json(plan)
        self.assertTrue(any("spec_ref" in e for e in sync.check(self.rdir).errors))

    def test_malformed_manifests_are_diagnosed(self):
        store = self.rdir / "plan-revisions"
        store.mkdir()
        for bad in ('{"revisions": [{"x": 1}]}', '{"revisions": [1]}', '{"revisions": [{"revision": true, '
                    '"sha256": "' + "a" * 64 + '"}]}', '{"revisions": [{"revision": 1, "sha256": "zz"}]}',
                    '{"revisions": [{"revision": 1, "sha256": "' + "a" * 64 + '"}, {"revision": 1, "sha256": "' +
                    "a" * 64 + '"}]}', "[]"):
            (store / "MANIFEST.json").write_text(bad, encoding="utf-8")
            with self.assertRaises(pc.PlanContractError) as ctx:
                rev.list_revisions(self.rdir)
            self.assertEqual(ctx.exception.code, "REVISION_STORE_UNREADABLE", bad)
            ref = rev.run_reference(self.rdir)  # an executor still starts, with a trace
            self.assertEqual(ref, {"plan_ref_error": "REVISION_STORE_UNREADABLE"})

    def test_tampered_store_leaves_a_trace_for_executors(self):
        self.good()
        sync.approve_freeze(self.rdir)
        target = rev.revision_path(self.rdir, 1)
        os.chmod(target, 0o644)
        target.write_text("{}", encoding="utf-8")
        self.assertEqual(rev.run_reference(self.rdir), {"plan_ref_error": "REVISION_TAMPERED"})

    def test_interrupted_freeze_is_adopted_when_identical_and_refused_otherwise(self):
        plan = self.good()
        folder = self.rdir / "plan-revisions"
        folder.mkdir()
        orphan = rev.revision_path(self.rdir, 1)
        orphan.write_text(pc.dumps(plan), encoding="utf-8")  # file written, manifest never updated
        report = sync.check(self.rdir)
        self.assertTrue(any("interrupted" in w for w in report.warnings))  # visible, and freeze decides
        self.assertEqual(rev.verify_store(self.rdir), ["PLAN.r1.json: file exists but is not in the manifest "
                                                       "(interrupted freeze)"])
        entry = sync.approve_freeze(self.rdir)  # identical content: adopted, manifest completed
        self.assertEqual(entry["revision"], 1)
        self.assertEqual(sync.check(self.rdir).errors, [])
        # different content under the next revision number: refused with a diagnostic, not a traceback
        plan["revision"] = 2
        plan["tasks"][0]["estimated_minutes"] = 99
        self.write_json(plan)
        rev.revision_path(self.rdir, 2).write_text("{}", encoding="utf-8")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "REVISION_STORE_DAMAGED")

    def test_unwritable_and_symlinked_stores_give_diagnostics(self):
        self.good()
        store = self.rdir / "plan-revisions"
        store.mkdir()
        os.chmod(store, 0o555)
        self.addCleanup(os.chmod, store, 0o755)
        if os.access(store, os.W_OK):
            self.skipTest("directory permissions are not enforced (running as root?)")
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "REVISION_STORE_UNWRITABLE")

    def test_symlinked_store_is_refused(self):
        self.good()
        outside = self.root / "elsewhere"
        outside.mkdir()
        (self.rdir / "plan-revisions").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(pc.PlanContractError) as ctx:
            sync.approve_freeze(self.rdir)
        self.assertEqual(ctx.exception.code, "REVISION_STORE_UNSAFE")
        self.assertEqual(list(outside.iterdir()), [])

    def test_concurrent_freezes_leave_a_consistent_store(self):
        self.good()
        results, errors = [], []

        def worker():
            try:
                results.append(sync.approve_freeze(self.rdir)["revision"])
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        self.assertEqual(results, [1] * 6)
        self.assertEqual([r["revision"] for r in rev.list_revisions(self.rdir)], [1])
        self.assertEqual(rev.verify_store(self.rdir), [])
        self.assertEqual([p.name for p in (self.rdir / "plan-revisions").iterdir() if p.name.endswith(".tmp")], [])

    def test_freeze_checks_and_freezes_the_same_object(self):
        self.good()
        reads = []
        original = sync.read_plan

        def counting(rdir):
            reads.append(1)
            return original(rdir)

        with patch.object(sync, "read_plan", counting):
            sync.approve_freeze(self.rdir)
        self.assertEqual(len(reads), 1)

    def test_nan_in_plan_json_is_reported_not_crashing(self):
        (self.rdir / "PLAN.json").write_text('{"schema_version": "1.0.0", "revision": NaN}', encoding="utf-8")
        report = sync.check(self.rdir)
        self.assertFalse(report.ok)
        self.assertIn("unreadable", "\n".join(report.errors))


class ExecutorReference(Base):
    """`run_reference` is what an executor may copy into its own new state; the plan is never duplicated there."""

    def test_reference_only_when_a_revision_is_frozen(self):
        self.assertEqual(rev.run_reference(self.rdir), {})
        self.good()
        entry = sync.approve_freeze(self.rdir)
        self.assertEqual(rev.run_reference(self.rdir),
                         {"plan_ref": {"plan_id": "REQ-042", "revision": 1, "sha256": entry["sha256"]}})

    def test_damaged_store_is_reported_as_a_code_not_raised(self):
        (self.rdir / "plan-revisions").mkdir()
        (self.rdir / "plan-revisions" / "MANIFEST.json").write_text("{", encoding="utf-8")
        self.assertEqual(rev.run_reference(self.rdir), {"plan_ref_error": "REVISION_STORE_UNREADABLE"})


class SiblingFiles(Base):
    """AC-11: the module writes only PLAN.json and plan-revisions/; every other file in the directory is untouched."""

    def test_no_other_file_is_ever_modified(self):
        (self.rdir / "STATE.json").write_text(json.dumps({"status": "running", "attempts": 2}), encoding="utf-8")
        (self.rdir / "NOTES.md").write_text("notes\n", encoding="utf-8")
        watched = {"SPEC.md", "PLAN.md", "STATE.json", "NOTES.md"}
        before = {name: (self.rdir / name).read_bytes() for name in watched}
        sync.write_skeleton(self.rdir)
        self.good()
        sync.check(self.rdir)
        sync.approve_freeze(self.rdir)
        sync.compat(self.rdir)
        rev.run_reference(self.rdir)
        self.assertEqual({name: (self.rdir / name).read_bytes() for name in watched}, before)
        self.assertEqual(sorted(p.name for p in self.rdir.iterdir()),
                         sorted(watched | {"PLAN.json", "plan-revisions"}))


class Compatibility(Base):
    def test_compat_is_read_only_and_reports_gaps_without_inventing_values(self):  # AC-13
        text = PLAN_MD.replace("verify: `pytest -q`", "verify: `pytest -q` · complexity: M · risk: high")
        self.write_md("done", text=text.format(status="done"))
        before = tree_digest(self.rdir)
        info = sync.compat(self.rdir)
        self.assertEqual(tree_digest(self.rdir), before)
        self.assertFalse(info["has_plan_json"])
        self.assertEqual(info["task_count"], 3)
        t3 = next(t for t in info["tasks"] if t["id"] == "T3")
        self.assertIn("complexity", t3["needs_enrichment"])
        self.assertEqual((t3["legacy_complexity"], t3["legacy_risk"]), ("m", "high"))  # reported verbatim (lower-cased), never mapped
        self.assertNotIn("complexity", t3["derived"])
        self.assertGreater(info["skeleton_errors"], 0)

    def test_plan_without_milestone_headings_is_reported(self):
        self.write_md("done", text="---\nstatus: done\n---\n## Phase 1\n- [x] T1 — Old task · after: T0\n")
        info = sync.compat(self.rdir)
        self.assertEqual(info["tasks_without_milestone"], ["T1"])
        self.assertEqual(info["milestones_in_md"], [])


class Cli(Base):
    def run_cli(self, action: str, **extra) -> tuple[int, str]:
        lines: list[str] = []
        code = cli.run(action, self.rdir, emit=lines.append, **extra)
        return code, "\n".join(lines)

    def test_gate_exit_codes_and_diagnostics(self):
        code, out = self.run_cli("init")
        self.assertEqual(code, 0)
        self.assertIn("complexity x3", out)
        code, out = self.run_cli("check")
        self.assertEqual(code, 2)
        self.assertIn("ERROR T1.complexity", out)
        self.good()
        self.assertEqual(self.run_cli("check")[0], 0)
        code, out = self.run_cli("freeze")
        self.assertEqual((code, "revision 1" in out), (0, True))
        self.assertIn("r1@", self.run_cli("show")[1])

    def test_freeze_refusal_is_reported_not_raised(self):
        self.good()
        self.write_md("in-progress")
        code, out = self.run_cli("freeze")
        self.assertEqual(code, 2)
        self.assertIn("PLAN_NOT_APPROVED", out)

    def test_custom_approved_states_and_plan_id(self):
        self.good()
        self.write_md("ready")
        self.assertEqual(self.run_cli("freeze")[0], 2)
        self.assertEqual(self.run_cli("freeze", approved_states=("ready",))[0], 0)
        plan = classified_legacy(self.rdir, plan_id="OTHER-1")
        plan["revision"] = 2
        self.write_json(plan)
        self.assertEqual(self.run_cli("check")[0], 2)  # id derived from the directory name does not match
        self.assertEqual(self.run_cli("check", plan_id="OTHER-1")[0], 0)

    def test_json_output_and_compat(self):
        self.good()
        code, text = self.run_cli("check", as_json=True)
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(text)["ok"])
        code, text = self.run_cli("compat")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(text)["plan_id"], "REQ-042")

    def test_validate_a_single_file_without_plan_md(self):
        lonely = self.root / "alone.json"
        lonely.write_text(self.good() and (self.rdir / "PLAN.json").read_text(encoding="utf-8"), encoding="utf-8")
        lines: list[str] = []
        self.assertEqual(cli.run("validate", lonely, emit=lines.append), 0)
        lonely.write_text("{}", encoding="utf-8")
        self.assertEqual(cli.run("validate", lonely, emit=lines.append), 2)
        self.assertEqual(cli.run("validate", self.root / "missing.json", emit=lines.append), 2)
        self.assertEqual(cli.run("check", self.root / "missing-dir", emit=lines.append), 2)
        self.assertEqual(cli.run("check", emit=lines.append), 2)

    def test_schema_and_example_are_bundled(self):
        for action, needle in (("schema", '"$schema"'), ("example", '"plan_id"')):
            code, out = self.run_cli(action)
            self.assertEqual((code, needle in out), (0, True))


if __name__ == "__main__":
    unittest.main()
