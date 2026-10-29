"""The durable runtime's prompt carries every section the legacy executor's prompt carries (REQ-030 item 2).

Both prompts are built for the same task of the same frozen 1.3.0 plan (a UI subplan), from the same requirement
folder: the owner's indications, the audit's findings, the attempt history (legacy M1 document plus RUN.notes), the
independent failure analysis, the last verification failure and the design contract. The legacy side is composed the
way `bt_scheduler_executor_wiring.wire` composes it; the durable side is `M3Attempts._brief` with `DurableBriefs`."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

PLAN = {
    "schema_version": "1.3.0", "plan_id": "REQ-900", "revision": 1,
    "subplans": [{"id": "SP-1", "milestone_id": "M1", "title": "checkout", "outcome": "checkout works", "covers": ["R1"],
                  "acceptance_criteria": ["checkout is accepted"], "integration_test_task": "T2", "audit_task": "T3",
                  "ui": {"contract": "checkout", "version": 1, "design_task": "T1", "visual_review_task": "T3"}}],
    "tasks": [
        {"id": "T1", "kind": "design", "subplan_id": "SP-1", "milestone_id": "M1", "repository": "app", "title": "design",
         "objective": "copy the contract", "acceptance_criteria": ["the contract is in the repo"],
         "expected_paths": ["design/contracts/checkout@v1.md"],
         "verification": [{"type": "command", "value": "test -f design/contracts/checkout@v1.md",
                           "purpose": "the contract is in the repo", "category": "static"}]},
        {"id": "T2", "kind": "implement", "subplan_id": "SP-1", "ui": True, "milestone_id": "M1", "repository": "app",
         "after": ["T1"], "title": "checkout screen", "objective": "build the screen",
         "acceptance_criteria": ["the screen renders"], "expected_paths": ["src/checkout.ts"],
         "verification": [{"type": "command", "value": "npm test", "purpose": "the screen renders",
                           "category": "functional"}]},
        {"id": "T3", "kind": "audit", "subplan_id": "SP-1", "milestone_id": "M1", "repository": "app", "after": ["T2"],
         "title": "visual review", "objective": "review", "acceptance_criteria": ["the review is written"],
         "expected_paths": ["docs/checkout.findings.json"],
         "verification": [{"type": "command", "value": "test -f docs/checkout.findings.json",
                           "purpose": "the review is written", "category": "static"}]},
    ]}
SECTIONS = ("## Task T2:", "## Objective", "## Design contract", "## Acceptance criteria", "## How the work will be checked",
            "Indications from the owner for this task", "use the fixture database",
            "Indications from the independent audit for this task", "F1 (high): the total is wrong",
            "Earlier attempts of this task", "Independent failure analysis", "Cause: the fixture is stale",
            "LAST VERIFICATION FAILURE", "Design contract: design/contracts/checkout@v1.md")


def git(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


class BriefParity(unittest.TestCase):
    def setUp(self):
        import bt_attempt_history
        import bt_scheduler_decisions as decisions
        self.root = Path(tempfile.mkdtemp(prefix="bt-briefs-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-900-briefs"
        (self.rdir / "plan-revisions").mkdir(parents=True)
        text = json.dumps(PLAN, indent=1) + "\n"
        (self.rdir / "plan-revisions" / "PLAN.r1.json").write_text(text)
        self.run_data = {"project": "proj", "req": "REQ-900", "plan_id": "REQ-900", "revision": 1,
                         "plan_sha256": hashlib.sha256(text.encode()).hexdigest(),
                         "plan_path": str(self.rdir / "plan-revisions" / "PLAN.r1.json")}
        self.repo = self.root / "app"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "design" / "contracts").mkdir(parents=True)
        (self.repo / "design" / "contracts" / "checkout@v1.md").write_text("# checkout contract\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.base = git(self.repo, "rev-parse", "HEAD")
        # the legacy run's M1 document (a migrated run) and the shared RUN.notes trail
        db = self.root / ".state" / "scheduler" / "proj-REQ-900.db"
        db.parent.mkdir(parents=True)
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, doc TEXT)")
        conn.execute("INSERT INTO state VALUES (1, ?)", (json.dumps(
            {"tasks": {"T2": {"attempts": ["att-1"]}}, "attempts": {"att-1": {"state": "rejected", "failure": "m6://x"}}}),))
        conn.commit()
        conn.close()
        notes = self.rdir / "RUN.notes"
        notes.mkdir()
        (notes / "T2.md").write_text("use the fixture database\n")
        decisions.write_audit_notes(self.rdir, "T2", "F1 (high): the total is wrong")
        bt_attempt_history.record(self.rdir, "T2", "att-1", "$ npm test\nexit code 1\nAssertionError: total 3 != 4")
        decisions.write_verify_notes(self.rdir, "T2", "LAST VERIFICATION FAILURE: npm test exited 1")
        (notes / "T2.analysis.json").write_text(json.dumps({"state": "done", "failures": 1, "confidence": "high",
                                                            "not_the_task": False, "cause": "the fixture is stale",
                                                            "solution": "regenerate it"}))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)

    def request(self, attempt, plan):
        from bt_durable.adapters.m3 import start_request
        return start_request(attempt, plan.task("T2"), base_ref=self.base, timeout=600)

    def legacy_prompt(self, plan, request) -> str:
        """What `bt_scheduler_executor_wiring.wire` hands the legacy executor: PlanBriefs + owner notes + design notes."""
        import bt_design_approval
        import bt_design_drafts
        import bt_scheduler_executor_adapter as api
        import bt_scheduler_executor_wiring as wiring

        def design_notes(req):
            return wiring.contract_notes(plan, req, lambda task: self.repo,
                                         lambda repo, base, path: bt_design_approval.check_tree(self.rdir, repo, base, path),
                                         lambda ref: bt_design_drafts.execution_notes(self.rdir, ref))
        # exactly as wire() leaves it: the design notes passed to PlanBriefs are replaced by owner_notes (see the note
        # there), so only the durable prompt carries the "Design contract:" line
        _ = design_notes
        briefs = api.PlanBriefs(plan, notes=wiring.owner_notes(self.rdir, plan, None))
        return api.m3.prompt.build_prompt(briefs.brief(request), request, workdir="/w", branch="b", report_path="/r",
                                          handoff_mode="snapshot", rtk=False)

    def durable_prompt(self, attempt, plan, request, note="") -> str:
        from bt_durable.adapters.briefs import DurableBriefs
        from bt_durable.adapters.m3 import M3Attempts
        from bt_durable.legacy import build_prompt
        attempts = M3Attempts(root=self.root / "durable", repositories_for=lambda project: {"app": self.repo},
                              plan_for=lambda a: plan, driver_for=lambda project: None,
                              briefs_for=DurableBriefs(repositories_for=lambda project: {"app": self.repo}))
        brief = attempts._brief(attempt, request, note)
        return build_prompt(brief, request, workdir="/w", branch="b", report_path="/r", handoff_mode="snapshot", rtk=False)

    def test_no_section_of_the_legacy_prompt_is_missing_from_the_durable_one(self):
        from bt_contracts.execution import AttemptRef, RunRef
        from bt_durable.legacy import load_plan
        run = RunRef.model_validate(self.run_data)
        plan = load_plan(Path(run.plan_path).read_text(), approved_sha256=run.plan_sha256, plan_id="REQ-900", revision=1)
        attempt = AttemptRef(run=run, task_id="T2", number=1, workflow_id="bt:x")
        request = self.request(attempt, plan)
        legacy, durable = self.legacy_prompt(plan, request), self.durable_prompt(attempt, plan, request)
        for section in SECTIONS:
            with self.subTest(section=section):
                if "Design contract" not in section:                       # the legacy prompt drops it (see above)
                    self.assertIn(section, legacy, "the fixture must exercise this section on the legacy side")
                self.assertIn(section, durable)
        headings = [line for line in legacy.splitlines() if line.startswith("## ")]
        durable_headings = [line for line in durable.splitlines() if line.startswith("## ")]
        self.assertEqual(headings, [line for line in durable_headings if line != "## Design contract"])

    def test_a_failure_note_of_the_workflow_replaces_the_same_last_failure_note(self):
        from bt_contracts.execution import AttemptRef, RunRef
        from bt_durable.legacy import load_plan
        run = RunRef.model_validate(self.run_data)
        plan = load_plan(Path(run.plan_path).read_text(), approved_sha256=run.plan_sha256, plan_id="REQ-900", revision=1)
        attempt = AttemptRef(run=run, task_id="T2", number=2, workflow_id="bt:x")
        request = self.request(attempt, plan)
        durable = self.durable_prompt(attempt, plan, request, note="The independent verification of your previous "
                                                                   "attempt failed. Decisive lines: total 3 != 4")
        self.assertIn("Decisive lines: total 3 != 4", durable)
        self.assertNotIn("LAST VERIFICATION FAILURE", durable)          # said once, not twice
        self.assertIn("use the fixture database", durable)


class RealRequirement(unittest.TestCase):
    """The live pictures REQ-021 folder, read only: the brief the durable runtime builds for T2.6 carries the owner's
    note in RUN.notes/T2.6.md (the note its legacy prompts carried and the durable a1 prompt lacked)."""

    RDIR = Path.home() / "bitacora" / "pictures" / "requirements" / "REQ-021-pilot-release-bilingual-ui-rectangular-t"

    def test_the_t26_brief_carries_the_owner_note(self):
        run_file = self.RDIR / "RUN.durable-run.json"
        if not run_file.is_file():
            self.fail(f"{run_file} is missing: this check reads the live bitácora")
        from bt_contracts.execution import AttemptRef, RunRef
        from bt_durable.adapters.briefs import DurableBriefs
        from bt_durable.adapters.m3 import start_request
        from bt_durable.legacy import load_plan, repositories
        run = RunRef.model_validate_json(run_file.read_text())
        plan = load_plan(run.plan_path.read_text(), approved_sha256=run.plan_sha256, plan_id=run.plan_id,
                         revision=run.revision)
        attempt = AttemptRef(run=run, task_id="T2.6", number=2, workflow_id="bt:check")
        request = start_request(attempt, plan.task("T2.6"), base_ref="HEAD", timeout=600)
        brief = DurableBriefs(repositories_for=lambda project: repositories(project))(attempt, plan, "").brief(request)
        owner_note = (self.RDIR / "RUN.notes" / "T2.6.md").read_text().strip().splitlines()[0]
        self.assertIn(owner_note, brief.notes)
        self.assertIn("Earlier attempts of this task", brief.notes)


if __name__ == "__main__":
    unittest.main()
