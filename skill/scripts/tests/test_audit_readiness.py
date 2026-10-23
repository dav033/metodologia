"""REQ-020 T15 saga: real planner, healing, snapshots, verifier and scheduler; fake processes only."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / "bt_scheduler_quality" / "tests"))

import bt_attempt_analyst as analyst
import bt_audit_gate as audit
import bt_plan_adapter as plans
import bt_scheduler_adapter as scheduler
import bt_scheduler_decisions as decisions
import bt_scheduler_healing as healing
from bt_scheduler_quality.tests import test_adapter as quality_support
from scheduler_executor_support import freeze, git, make_repo
from test_remediation import plan, task

LEDGER = "docs/T15.findings.json"
EVIDENCE = "docs/integration-results.json"
COMMAND = f"npx tsx check-findings.ts {LEDGER} --integration-results {EVIDENCE}"


def audit_plan():
    return plan(task("T1", paths=["README.md"], command="python source.py"),
                task("T14a", ["T1"], kind="test", category="integration", paths=[EVIDENCE], command="python integration.py"),
                task("T14b", ["T14a"], paths=["README.md"], command="python source.py"),
                task("T15", ["T14b"], kind="audit", paths=["docs/T15.md", LEDGER], command=COMMAND))


class Readiness(unittest.TestCase):
    _system = quality_support.M6M1AdapterTests._system

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.repo = make_repo(self.directory / "app")
        self.plan = audit_plan()

    def commit(self, changes):
        for path, text in changes.items():
            target = self.repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "--allow-empty", "-qm", "result")
        return git(self.repo, "rev-parse", "HEAD")

    def start_attempt(self, system, tid, base, revision):
        root, core, _, executor, _, _ = system
        link = root / tid
        if not link.exists():
            link.symlink_to(self.repo, target_is_directory=True)
        core.step()
        attempt = core.snapshot().tasks[tid]["attempt"]
        executor.add_attempt(attempt, SimpleNamespace(repository=self.repo, base_sha=base, snapshot_sha=revision))
        token = core.read(lambda ctx: ctx.state.attempts[attempt].token)
        for kind in ("execution_started", "execution_finished"):
            event = scheduler.core.Event(f"{attempt}-{kind}", core.plan.plan_id, core.plan.revision,
                                         tid, attempt, "process", kind, token=token)
            self.assertEqual(core.ingest(event).status, "applied")
        core.step()
        return attempt

    def wait(self, predicate):
        self.assertTrue(quality_support._wait_for(predicate))

    def test_audit_reaches_findings_gate_despite_deferred_suite_and_reworks_stale_producer(self):
        self.content_saga()

    def test_a_real_whole_suite_failure_still_rejects_after_the_engine_replaces_a_legacy_checker(self):
        self.content_saga(failing_suite=True)

    def test_an_unrelated_check_reading_the_ledger_still_executes_and_rejects(self):
        self.content_saga(failing_suite=True, suite_command=f"python verify_integration.py --ledger {LEDGER}")

    def content_saga(self, failing_suite=False, suite_command="npm run gate"):
        outputs = audit.evidence_outputs(self.plan["tasks"], "app")
        initial = git(self.repo, "rev-parse", "HEAD")
        digest = audit.tree_digest(self.repo, initial, outputs)
        runner = quality_support.ScriptedRunner(failing_commands=(COMMAND, suite_command) if failing_suite else (COMMAND,))
        requested = []
        notes = []
        self.plan["tasks"][-1]["verification"].append({"type": "command", "value": suite_command,
             "purpose": self.plan["tasks"][-1]["acceptance_criteria"][0], "category": "regression"})
        system = self._system(self.plan["tasks"], schema_version="1.2.0", max_attempts=2, runner=runner,
                              remediate=lambda *args: requested.append(args) or True,
                              rework_notes=lambda tid, text: notes.append((tid, text)))
        _, core, _, _, store, _ = system
        self.start_attempt(system, "T1", initial, initial)
        self.wait(lambda: core.snapshot().tasks["T1"]["state"] == "completed")
        produced = self.commit({EVIDENCE: json.dumps({"tree_digest": digest, "revision": initial})})
        self.start_attempt(system, "T14a", initial, produced)
        self.wait(lambda: core.snapshot().tasks["T14a"]["state"] == "completed")
        changed = self.commit({"README.md": "integration changed the source\n"})
        self.start_attempt(system, "T14b", produced, changed)
        self.wait(lambda: core.snapshot().tasks["T14b"]["state"] == "completed")
        current = audit.tree_digest(self.repo, changed, outputs)
        ledger = {"schema": audit.SCHEMA, "findings": [], "tree_digest": current, "integration_evidence": [EVIDENCE]}
        audited = self.commit({LEDGER: json.dumps(ledger), "docs/T15.md": "review"})
        attempt = self.start_attempt(system, "T15", changed, audited)
        self.wait(lambda: "rework_requested" in [entry.kind for entry in core.audit_log()])
        self.assertEqual(core.snapshot().tasks["T14b"]["state"], "completed")
        self.assertIn(core.snapshot().tasks["T14a"]["state"], ("pending", "ready"))
        self.assertFalse(requested, "stale evidence must rerun its producer, not create an implement task")
        self.assertTrue(any(tid == "T14a" and "regenerate" in text for tid, text in notes))
        if suite_command == "npm run gate":
            self.assertNotIn(suite_command, runner.calls)
        self.assertTrue(any("STALE" in str(e.detail) for e in core.audit_log()), [str(e) for e in core.audit_log()])
        result = store.get_result(quality_support._request_key(core, attempt))
        if suite_command == "npm run gate":
            self.assertTrue(any(c.get("issue_code") == "CHECK_DEFERRED" for c in result["checks"]))
        refreshed = self.commit({EVIDENCE: json.dumps({"tree_digest": current, "revision": changed})})
        self.start_attempt(system, "T14a", audited, refreshed)
        self.wait(lambda: core.snapshot().tasks["T14a"]["state"] == "completed")
        final = self.commit({"docs/T15.md": "review rechecked"})
        final_attempt = self.start_attempt(system, "T15", refreshed, final)
        if failing_suite:
            self.wait(lambda: core.read(lambda ctx: ctx.state.attempts[final_attempt].state) == "rejected")
        else:
            self.wait(lambda: core.snapshot().tasks["T15"]["state"] == "completed")
        self.assertIn(suite_command, runner.calls)

    def test_ledger_arguments_do_not_turn_other_commands_into_contract_checks(self):
        from bitacora_platform.quality_audit_evidence import ledger_invocation

        self.assertTrue(ledger_invocation(COMMAND, LEDGER))
        for command in (f"npm run gate -- --ledger {LEDGER}", f"python verify_integration.py --ledger {LEDGER}",
                        f"{COMMAND} && npm run gate", f"{COMMAND};false", f"{COMMAND}&&false",
                        f"{COMMAND} --run-all", f"echo '{COMMAND}'"):
            self.assertFalse(ledger_invocation(command, LEDGER), command)

    def test_planner_reports_ignored_inputs_and_engine_accepts_both_ledger_spellings(self):
        self.commit({".gitignore": "ignored.json\n"})
        self.plan["tasks"][-1]["verification"].append({"type": "command", "value": "node check.js ignored.json",
                "purpose": "T15 behaves as described", "category": "functional"})
        self.assertFalse(any("git-ignored" in error for error in plans.plan_errors(self.plan, roots={"app": self.repo})))
        # Unknown script arguments are advice, because the planner cannot infer which ones are inputs.
        report = plans.planner_contract.validate(self.plan, ignored_path=plans.ignore_resolver({"app": self.repo}))
        self.assertTrue(any("git-ignored" in warning for warning in report.warnings))
        canonical = {"id": "F1", "severity": "high", "status": "fixed", "tasks": ["T1"],
                     "summary": "rechecked", "evidence": "integration passed"}
        alias = {k: v for k, v in canonical.items() if k != "tasks"}
        alias.update(status="closed", taskReferences=["T1"])
        for finding in (canonical, alias):
            self.assertEqual(audit.validate_ledger({"schema": audit.SCHEMA, "findings": [finding]}), [])

    def test_real_analyst_stop_and_refused_repair_leave_the_case_unspent(self):
        rdir = self.directory / "REQ-999-audit-readiness"
        rdir.mkdir()
        # The legacy fixture freezes bytes directly, as a preexisting plan would have been frozen.
        broken = audit_plan()
        broken["tasks"][0]["estimated_minutes"] = 0
        approved_sha = freeze(rdir, json.dumps(broken))
        (rdir / "PLAN.json").write_text(json.dumps(broken))
        loaded = scheduler.core.load_plan(json.dumps(broken), approved_sha256=approved_sha)
        core = scheduler.core.SchedulerCore(loaded, scheduler.core.SqliteRepository(rdir / "SCHEDULER.db"),
                                            ports=scheduler.core.Ports(execution=scheduler.core.FakeExecutor()))
        core.start()
        core.step()
        analyst._save(rdir, "T1", {"state": "done", "not_the_task": True, "confidence": "alta", "failures": 3,
                                  "source_available": True, "source_snapshot": git(self.repo, "rev-parse", "HEAD"),
                                  "cause": "The planner estimate is invalid", "solution": "Correct the plan contract"})
        # Only the OS process probe is faked: cancellation, decisions, validation and healing state are real.
        with patch("bt_scheduler_ops._processes", return_value=[]):
            self.assertEqual(healing.cycle("audit-readiness-test", "REQ-999", rdir), 0)
        state = healing.load(rdir)
        case = next(iter(state["cases"].values()))
        self.assertEqual((case["status"], case["applied"], case["invalid"], state["actions"]), ("open", 0, 1, 0))
        self.assertTrue(state["analyst_stops"])
        self.assertEqual(decisions._state(rdir)["tasks"]["T1"]["state"], "blocked")
        self.assertIn("revision invalid", case["history"][-1]["repair"])
        case_spec = healing.classify_mod.Case("audit-case", "T15", "regression", ("check failed",),
                                             owners=("T1",), signature="repair")
        revised, repair_id, _ = healing.build_fix_revision(self.plan, "T15", case_spec, {"verify": "FAIL: source"})
        repair = next(task for task in revised["tasks"] if task["id"] == repair_id)
        self.assertTrue(repair["verification"])
        self.assertFalse(any(LEDGER in check["value"] for check in repair["verification"]))
