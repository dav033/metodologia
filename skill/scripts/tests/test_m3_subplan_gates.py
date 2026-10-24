"""M3 composition identity, Designer base-tree gate, and frozen visual brief metadata."""
from __future__ import annotations

import sys
import tempfile
import unittest
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_scheduler_executor as m3
from bt_scheduler_executor import gates
from bt_scheduler_executor.prompt import build_prompt
import scheduler_executor_support as support
from scheduler_executor_support import adapter, core, git
from bt_scheduler_core.recovery import attempts_used


class M3SubplanGates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = support.make_repo(Path(self.tmp.name) / "repo")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.ui = SimpleNamespace(contract="checkout", version=2, design_task="T1", visual_review_task="T3")
        self.subplan = SimpleNamespace(id="SP-1", ui=self.ui)
        self.task = SimpleNamespace(id="T2", repository="app", meta={"subplan_id": "SP-1", "ui": True},
                                    verification=(), acceptance_criteria=(), expected_paths=())
        self.gate = SimpleNamespace(id="T4", repository="app", meta={}, verification=(),
                                    acceptance_criteria=(), expected_paths=())
        self.plan = SimpleNamespace(schema_version="1.3.0", subplans=(self.subplan,), plan_id="REQ-1", revision=1,
                                    sha256="a" * 64, tasks=(self.task, self.gate),
                                    task=lambda task_id: {"T2": self.task, "T4": self.gate}[task_id])
        self.order = SimpleNamespace(plan_id="REQ-1", revision=1, task_id="T4", idempotency_key="k",
                                     attempt_id="att-1", token=1, executor="direct:claude/sonnet#high",
                                     acceptance_criteria=(), verification=())

    def test_ui_gate_refuses_a_symlink_in_place_of_the_contract(self):
        contract = self.repo / "design" / "contracts" / "checkout@v2.md"
        contract.parent.mkdir(parents=True, exist_ok=True)
        (self.repo / "outside.md").write_text("not the contract\n", encoding="utf-8")
        contract.symlink_to("../../outside.md")
        git(self.repo, "add", "outside.md", "design/contracts/checkout@v2.md")
        git(self.repo, "commit", "-m", "linked contract")
        self.assertFalse(gates.has_blob(self.repo, git(self.repo, "rev-parse", "HEAD"), "design/contracts/checkout@v2.md"))

    def test_ui_gate_requires_the_exact_version_as_a_blob_in_the_selected_tree(self):
        good_path = self.repo / "design/contracts/checkout@v2.md"
        good_path.parent.mkdir(parents=True)
        good_path.write_text("contract v2\n")
        git(self.repo, "add", "design/contracts/checkout@v2.md")
        git(self.repo, "commit", "-m", "contract")
        good = git(self.repo, "rev-parse", "HEAD")
        wrong = self.base
        self.assertEqual(gates.contract_path(self.plan, "T2"), "design/contracts/checkout@v2.md")
        self.assertTrue(gates.has_blob(self.repo, good, "design/contracts/checkout@v2.md"))
        self.assertFalse(gates.has_blob(self.repo, wrong, "design/contracts/checkout@v2.md"))

    def test_composition_task_uses_injected_candidate_and_missing_candidate_fails_closed(self):
        class Executor:
            def __init__(self):
                self.request = None

            def start(self, request):
                self.request = request
                return m3.Receipt("accepted", attempt_id=request.attempt_id)

        executor = Executor()
        port = adapter.CoreExecutionPort(executor, self.plan, project="proj", composition_base=lambda task, order: self.base,
                                         repo_of=lambda role: self.repo)
        ack = port.start(self.order)
        self.assertEqual(ack.status, "accepted")
        self.assertEqual(executor.request.base_ref, self.base)
        missing = adapter.CoreExecutionPort(executor, self.plan, project="proj", repo_of=lambda role: self.repo)
        blocked = missing.start(self.order)
        self.assertEqual(blocked.status, "rejected")
        self.assertIn("COMPOSITION_BASE_MISSING", blocked.detail)

    def test_legacy_plan_keeps_its_existing_base_selection(self):
        self.plan.schema_version = "1.2.0"
        self.plan.subplans = ()

        class Executor:
            def start(self, request):
                self.request = request
                return m3.Receipt("accepted", attempt_id=request.attempt_id)

        executor = Executor()
        port = adapter.CoreExecutionPort(executor, self.plan, project="proj", base_ref=lambda task: "legacy-base",
                                         repo_of=lambda role: self.repo)
        self.assertEqual(port.start(self.order).status, "accepted")
        self.assertEqual(executor.request.base_ref, "legacy-base")

    def test_ui_task_does_not_reach_executor_when_its_selected_base_lacks_contract(self):
        class Executor:
            called = False

            def start(self, request):
                self.called = True
                return m3.Receipt("accepted", attempt_id=request.attempt_id)

        ui_order = SimpleNamespace(**{**vars(self.order), "task_id": "T2"})
        wrong_version = self.repo / "design/contracts/checkout@v1.md"
        wrong_version.parent.mkdir(parents=True)
        wrong_version.write_text("only the old version\n")
        git(self.repo, "add", "design/contracts/checkout@v1.md")
        git(self.repo, "commit", "-m", "old contract")
        selected = git(self.repo, "rev-parse", "HEAD")
        uncommitted = self.repo / "design/contracts/checkout@v2.md"
        uncommitted.write_text("only in the checkout, not the selected base\n")
        executor = Executor()
        port = adapter.CoreExecutionPort(executor, self.plan, project="proj", base_ref=selected,
                                         repo_of=lambda role: self.repo)
        port.design_approval = lambda repo, base, path: {"state": "unapproved"}
        blocked = port.start(ui_order)
        self.assertEqual(blocked.status, "rejected")
        self.assertIn("DESIGN_CONTRACT_UNAPPROVED", blocked.detail)
        self.assertEqual(blocked.classification, "blocked_environment")
        self.assertFalse(executor.called)
        self.assertTrue(gates.has_blob(self.repo, selected, "design/contracts/checkout@v1.md"))
        self.assertFalse(gates.has_blob(self.repo, selected, "design/contracts/checkout@v2.md"))

    def test_ui_task_starts_when_the_exact_contract_blob_is_in_its_selected_base(self):
        contract = self.repo / "design/contracts/checkout@v2.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("approved contract\n")
        git(self.repo, "add", "design/contracts/checkout@v2.md")
        git(self.repo, "commit", "-m", "approved UI contract")
        selected = git(self.repo, "rev-parse", "HEAD")

        class Executor:
            called = False

            def start(self, request):
                self.called = True
                self.request = request
                return m3.Receipt("accepted", attempt_id=request.attempt_id)

        ui_order = SimpleNamespace(**{**vars(self.order), "task_id": "T2"})
        executor = Executor()
        port = adapter.CoreExecutionPort(executor, self.plan, project="proj", base_ref=selected,
                                         repo_of=lambda role: self.repo)
        port.design_approval = lambda repo, base, path: {"state": "approved"}
        ack = port.start(ui_order)
        self.assertEqual(ack.status, "accepted")
        self.assertTrue(executor.called)
        self.assertEqual(executor.request.base_ref, selected)

    def test_ui_task_with_an_approved_but_changed_contract_is_held_without_starting(self):
        contract = self.repo / "design/contracts/checkout@v2.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("new contract\n")
        git(self.repo, "add", "design/contracts/checkout@v2.md")
        git(self.repo, "commit", "-m", "new contract")
        selected = git(self.repo, "rev-parse", "HEAD")

        class Executor:
            called = False

            def start(self, request):
                self.called = True
                return m3.Receipt("accepted", attempt_id=request.attempt_id)

        executor = Executor()
        ui_order = SimpleNamespace(**{**vars(self.order), "task_id": "T2"})
        port = adapter.CoreExecutionPort(executor, self.plan, project="proj", base_ref=selected,
                                         repo_of=lambda role: self.repo)
        port.design_approval = lambda repo, base, path: {"state": "hash-mismatch"}
        ack = port.start(ui_order)
        self.assertEqual(ack.classification, "blocked_environment")
        self.assertIn("DESIGN_CONTRACT_HASH_MISMATCH", ack.detail)
        self.assertFalse(executor.called)

    def test_scheduler_holds_unapproved_ui_attempt_without_budget_then_owner_approval_releases_it(self):
        raw = {"schema_version": "1.3.0", "plan_id": "REQ-1", "revision": 1,
               "tasks": [{"id": tid, "milestone_id": "M1", "repository": "app", "after": [],
                          "acceptance_criteria": ["works"], "verification": [{"type": "command", "value": "true",
                                                                                "category": "functional"}],
                          "expected_paths": ["src/**"], **extra}
                         for tid, extra in (("T1", {"kind": "design"}),
                                            ("T2", {"kind": "implement", "subplan_id": "SP-1", "ui": True}),
                                            ("T3", {"kind": "test"}), ("T4", {"kind": "audit"}))],
               "subplans": [{"id": "SP-1", "milestone_id": "M1", "title": "Shop", "outcome": "Shop UI",
                             "covers": ["shop"], "acceptance_criteria": ["shop works"],
                             "integration_test_task": "T3", "audit_task": "T4",
                             "ui": {"contract": "checkout", "version": 1, "design_task": "T1",
                                    "visual_review_task": "T4"}}], "composition_gates": []}
        text = json.dumps(raw)
        plan = core.load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest())
        class Executor:
            starts = 0
            def start(self, request):
                self.starts += 1
                return adapter.m3.Receipt("accepted", attempt_id=request.attempt_id)
        executor = Executor()
        approved = {"state": "unapproved"}
        port = adapter.CoreExecutionPort(executor, plan, project="proj", base_ref=self.base,
                                         repo_of=lambda _role: self.repo)
        port.design_approval = lambda *_: approved
        scheduler = core.SchedulerCore(plan, core.InMemoryRepository(),
                                       ports=core.Ports(execution=port), config=core.Config(max_attempts=3))
        scheduler.start()
        scheduler.claim(core.Assignment("T2", "direct:claude/sonnet#high"))
        scheduler.step()
        scheduler.step()  # the subsequent recovery pass stores the environment hold
        snapshot = scheduler.snapshot()
        self.assertEqual(snapshot.tasks["T2"]["state"], "blocked")
        attempt = scheduler.read(lambda ctx: ctx.state.attempts[ctx.state.tasks["T2"].attempts[-1]])
        self.assertFalse(attempt.budget_consumed)
        self.assertEqual(attempts_used(scheduler.read(lambda ctx: ctx.state), "T2"), 0)
        approved["state"] = "approved"
        scheduler.reopen("T2", "owner", "contract approved")
        self.assertEqual(scheduler.snapshot().tasks["T2"]["state"], "ready")
        scheduler.claim(core.Assignment("T2", "direct:claude/sonnet#high"))
        scheduler.step()
        self.assertEqual(scheduler.snapshot().tasks["T2"]["state"], "active")
        self.assertEqual(executor.starts, 1)

    def test_visual_axis_is_derived_only_for_the_frozen_visual_review_task(self):
        review = SimpleNamespace(id="T3", repository="app", meta={"kind": "audit"}, verification=(),
                                 acceptance_criteria=(), expected_paths=())
        self.plan.task = lambda task_id: {"T2": self.task, "T3": review, "T4": self.gate}[task_id]
        brief = adapter.PlanBriefs(self.plan).brief(SimpleNamespace(task_id="T3"))
        self.assertEqual(brief.review_axis, "visual")
        prompt = build_prompt(brief, m3.StartRequest("k", "REQ-1", 1, "T3", "att", 1,
                                                     "direct:claude/sonnet#high", "app"),
                              workdir="/tmp/w", branch="m3/a", report_path="report.json", rtk=False)
        self.assertIn("Reviewer axis\nvisual", prompt)
        ordinary = adapter.PlanBriefs(self.plan).brief(SimpleNamespace(task_id="T2"))
        self.assertEqual(ordinary.review_axis, "")


if __name__ == "__main__":
    unittest.main()
