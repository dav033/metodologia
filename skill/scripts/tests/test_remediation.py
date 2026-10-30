"""REQ-028: blocking audit findings become tasks on the integrated tree instead of a rebuild of the tasks they name."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_attempt_log
import bt_audit_gate
import bt_plan_adapter as plans
import bt_scheduler_ops
import bt_remediation as rem


def evidence_for(tid):
    texts = {"complexity": "One module with a known pattern", "scope": "A single focused change to behaviour",
             "duration": "About half an hour of careful work", "risk": "Moderate: other code depends on it",
             "coupling": "Shares one contract with its neighbours", "confidence": "Similar changes were made before"}
    return {key: {"evidence": ["spec:SPEC.md"], "justification": f"{text} in {tid}"} for key, text in texts.items()}


def task(tid, after=(), kind="implement", paths=None, command="pytest -q", category="functional", **over):
    paths = paths if paths is not None else [f"src/{tid.lower()}.py"]
    if command == "pytest -q":
        command = f"pytest {paths[0]}"
    base = {"id": tid, "milestone_id": "M1", "title": f"Task {tid}", "objective": f"Deliver task {tid} completely",
            "repository": "app", "after": list(after), "complexity": "medium", "scope": "small_change",
            "estimated_minutes": 30, "risk": "medium", "coupling": "medium", "confidence": "medium",
            "estimate_rationale": "Known pattern in this module",
            "classification_evidence": evidence_for(tid),
            "expected_paths": paths, "shared_resources": ["contract"],
            "acceptance_criteria": [f"{tid} behaves as described"], "covers": ["R1"], "kind": kind,
            "verification": [{"type": "command", "value": command, "purpose": f"{tid} behaves as described",
                              "category": category}] if command else [{"type": "manual", "value": "look",
                                                                         "purpose": f"{tid} behaves as described"}]}
    base.update(over)
    return base


def plan(*tasks):
    return {"schema_version": "1.2.0", "plan_id": "REQ-X", "revision": 1, "spec_ref": "SPEC.md", "requirements": ["R1"],
            "milestones": [{"id": "M1", "title": "Base", "acceptance_criteria": ["Everything is delivered"]}],
            "tasks": list(tasks)}


def finding(fid, tasks, severity="high", summary="Something is wrong", evidence=""):
    return {"id": fid, "severity": severity, "summary": summary, "tasks": list(tasks), "evidence": evidence}


BASE = plan(task("T1"), task("T2", ["T1"], paths=["src/two.py"]), task("T3", ["T2"], kind="test", category="integration", paths=["src/three.py"]),
            task("T4", ["T3"], kind="audit", paths=["docs/audit.md", "docs/audit.findings.json"]),
            task("T5", ["T3", "T4"]))


class Build(unittest.TestCase):
    def test_non_ui_repair_inherits_explicit_non_ui_contract(self):
        owner = task("T1", paths=["scripts/test/form.test.tsx"], ui=False)
        audit = task("T4", ["T1"], kind="test", ui=False, subplan_id="SP-1")
        repair = rem._task("T4.1", audit, [finding("F1", ["T1"])], {"T1": owner}, ["T1"], 1,
                           "SPEC.md", {"subplans": [{"id": "SP-1"}]}, commands=[[{"command": "pytest test.py"}]])
        self.assertIs(repair.get("ui"), False)

    def test_generated_repair_checks_are_admitted_by_m6(self):
        from bt_scheduler_quality.contracts import VerifyRequest

        revised = rem.build_revision(BASE, "T4", [finding("F1", ["T1"])])
        repair = next(t for t in revised["tasks"] if t["id"].startswith("T4."))
        request = VerifyRequest.from_mapping({
            "idempotency_key": "repair-verify", "plan_id": revised["plan_id"],
            "revision": revised["revision"], "task_id": repair["id"],
            "attempt_id": "att-1", "token": 1,
            "acceptance_criteria": repair["acceptance_criteria"],
            "verification": repair["verification"],
        })
        self.assertEqual(len(request.verification), len(repair["verification"]))

    def test_findings_become_tasks_after_the_audits_prerequisites_and_the_audit_waits_for_them(self):
        revised = rem.build_revision(BASE, "T4", [finding("F1", ["T1"], summary="Login returns 404"),
                                                  finding("F2", ["T3"], severity="critical")])
        self.assertEqual(revised["revision"], 2)
        by_id = {t["id"]: t for t in revised["tasks"]}
        self.assertEqual(set(by_id) - {"T1", "T2", "T3", "T4", "T5"}, {"T4.1", "T4.2"})
        for new in ("T4.1", "T4.2"):
            self.assertEqual(by_id[new]["kind"], "implement")
            self.assertTrue(set(by_id[new]["after"]) >= {"T3"})
        self.assertEqual(set(by_id["T4"]["after"]), {"T3", "T4.1", "T4.2"})
        self.assertEqual(by_id["T5"]["after"], ["T3", "T4"])                           # what follows the audit is untouched
        self.assertIn("Login returns 404", by_id["T4.1"]["objective"] + by_id["T4.2"]["objective"])
        self.assertEqual(plans.plan_errors(revised), [])
        self.assertEqual(BASE["revision"], 1)                                          # the input plan is not changed

    def test_remediation_tasks_join_the_subplan_of_the_audit_when_the_plan_has_subplans(self):
        by_id = {t["id"]: t for t in BASE["tasks"]}
        audit = {**by_id["T4"], "subplan_id": "SP-1"}
        args = ("T4.1", audit, [finding("F1", ["T1"])], by_id, ["T3"], 1, "SPEC.md")
        commands = [[{"command": "pytest src/t1.py"}]]
        flat = rem._task(*args, BASE, commands=commands)
        nested = rem._task(*args, {**BASE, "subplans": [{"id": "SP-1", "audit_task": "T4"}]}, commands=commands)
        self.assertNotIn("subplan_id", flat)
        self.assertEqual(nested["subplan_id"], "SP-1")

    def test_remediation_does_not_inherit_the_package_manifest_resource_so_it_can_run_beside_other_work(self):
        spec = plan(task("T1", shared_resources=["contract:session-guard", "package.json scripts"]),
                    task("T2", ["T1"], kind="test", category="integration", paths=["src/two.py"]),
                    task("T3", ["T2"], kind="audit", paths=["docs/audit.md", "docs/audit.findings.json"]))
        revised = rem.build_revision(spec, "T3", [finding("F1", ["T1"])])
        fix = next(t for t in revised["tasks"] if t["id"].startswith("T3."))
        self.assertEqual(fix["shared_resources"], ["contract:session-guard"])

    def test_each_criterion_is_checked_by_the_command_of_the_task_that_owns_the_finding(self):
        spec = plan(task("T1", command="python -m unittest a/a.py", paths=["a/a.py"]),
                    task("T2", ["T1"], kind="test", category="integration", command="python -m unittest b/b.py",
                         paths=["b/b.py"]),
                    task("T3", ["T2"], kind="audit", paths=["a.md", "a.findings.json"]))
        revised = rem.build_revision(spec, "T3", [finding("F1", ["T2"]), finding("F2", ["T1"])])
        fixed = [t for t in revised["tasks"] if t["id"].startswith("T3.")]
        commands = {v["purpose"].split(" ")[0]: v["value"] for t in fixed for v in t["verification"]}
        self.assertEqual(commands, {"F1": "python -m unittest b/b.py", "F2": "python -m unittest a/a.py"})
        for t in fixed:
            self.assertEqual({v["purpose"] for v in t["verification"]}, set(t["acceptance_criteria"]))

    def test_findings_that_share_a_task_or_a_path_are_chained_and_big_sets_are_cut(self):
        many = [finding(f"F{n}", ["T1"]) for n in range(1, 7)]
        revised = rem.build_revision(BASE, "T4", many)
        new = [t for t in revised["tasks"] if t["id"].startswith("T4.")]
        self.assertEqual([len(t["acceptance_criteria"]) for t in new], [4, 2])
        self.assertEqual(new[1]["after"], ["T3", "T4.1"])                              # the second piece sees the first
        areas = plan(task("T1", kind="test", category="integration"), task("T2"),
                     task("T3", ["T1", "T2"], kind="audit", paths=["a.md", "a.findings.json"]))
        two = [finding("F1", ["T1"]), finding("F2", ["T2"])]
        chained = rem.build_revision(areas, "T3", two, parallel=False)
        serial = {t["id"]: t["after"] for t in chained["tasks"] if t["id"].startswith("T3.")}
        self.assertEqual(serial, {"T3.1": ["T1", "T2"], "T3.2": ["T1", "T2", "T3.1"]})   # one after another when switched off
        parallel = {t["id"]: t["after"] for t in rem.build_revision(areas, "T3", two)["tasks"] if t["id"].startswith("T3.")}
        self.assertEqual(parallel, {"T3.1": ["T1", "T2"], "T3.2": ["T1", "T2"]})       # independent areas side by side by default

    def test_side_by_side_remediation_needs_the_integration_line_of_the_run(self):
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp)
            self.assertFalse(rem.parallel_for(rdir))                                        # predecessor merge: chained, as D-114
            (rdir / "RUN.integration-line").write_text("on")
            self.assertTrue(rem.parallel_for(rdir))
            with mock.patch.object(rem, "_parallel", return_value=False):
                self.assertFalse(rem.parallel_for(rdir))                                    # the setting still wins

    def test_a_second_auditor_gets_its_own_numbering(self):
        spec = plan(task("T1", kind="test", category="integration"),
                    task("T2", ["T1"], kind="audit", paths=["a.md", "a.findings.json"]),
                    task("T2b", ["T1", "T2"], kind="audit", paths=["b.md", "b.findings.json"]))
        revised = rem.build_revision(rem.build_revision(spec, "T2", [finding("F1", ["T1"])]), "T2b", [finding("F9", ["T1"])])
        ids = {t["id"] for t in revised["tasks"]}
        self.assertTrue({"T2.1", "T2.1b"} <= ids)
        self.assertEqual(revised["revision"], 3)

    def test_nothing_is_built_when_it_cannot_be_built_soundly(self):
        self.assertIsNone(rem.build_revision(BASE, "T4", [finding("F1", ["T99"])]))          # no owner in this plan
        self.assertIsNone(rem.build_revision(BASE, "T4", []))
        self.assertIsNone(rem.build_revision(BASE, "T9", [finding("F1", ["T1"])]))           # not a task of the plan
        manual = plan(task("T0", kind="test", category="integration"), task("T1", ["T0"], command=None),
                      task("T2", ["T1"], kind="audit", paths=["a.md", "a.findings.json"]))
        self.assertIsNone(rem.build_revision(manual, "T2", [finding("F1", ["T1"])]))         # nothing checks that area


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir = Path(self.tmp.name)
        plans.freeze_revision(self.rdir, BASE, "approval")
        self.policy = bt_audit_gate.Policy()

    def test_the_gate_hook_records_a_request_then_the_apply_turns_it_into_a_frozen_revision(self):
        ask = rem.hook(self.rdir, self.policy)
        self.assertTrue(ask("T4", "att-0001", [finding("F1", ["T1"])]))
        self.assertTrue(rem.requested(self.rdir))
        built = rem.apply(self.rdir)
        self.assertEqual((built["audit"], built["round"], built["revision"], built["tasks"]), ("T4", 1, 2, ["T4.1"]))
        self.assertFalse(rem.requested(self.rdir))
        self.assertEqual(plans.latest_plan(self.rdir)["revision"], 2)
        self.assertEqual(json.loads((self.rdir / "PLAN.json").read_text())["revision"], 2)
        self.assertEqual(rem.rounds_used(self.rdir, "T4"), 1)
        self.assertIsNone(rem.apply(self.rdir))                                              # nothing left to apply

    def test_the_apply_keeps_the_owners_confirmation_of_subplans_that_held(self):
        ask = rem.hook(self.rdir, self.policy)
        ask("T4", "att-0001", [finding("F1", ["T1"])])
        state = {"subplans": {"SP-1": {"state": "confirmed"}, "SP-2": {"state": "changed"}, "SP-3": {"state": "pending"}}}
        with patch("bt_planning_flow.active", return_value=True), patch("bt_planning_flow.state", return_value=state), \
                patch("bt_planning_flow.keep_confirmed") as keep:
            rem.apply(self.rdir)
        keep.assert_called_once_with(self.rdir, ["SP-1"], "auto remediation of T4")

    def test_the_apply_writes_the_new_tasks_into_plan_md_so_a_later_stage_can_be_approved(self):
        lines = ["# Plan", "", "### M1 — Base"]
        for t in BASE["tasks"]:
            lines.append(f"- [ ] {t['id']} — {t['title']} · repo: app · after: {', '.join(t['after'])} · files: {', '.join(t['expected_paths'])}")
        (self.rdir / "PLAN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        ask = rem.hook(self.rdir, self.policy)
        ask("T4", "att-0001", [finding("F1", ["T1"])])
        rem.apply(self.rdir)
        text = (self.rdir / "PLAN.md").read_text(encoding="utf-8")
        self.assertIn("- [ ] T4.1 — Remediate T4 findings F1", text)
        self.assertLess(text.index("T4.1 —"), text.index("- [ ] T4 —"))                      # before the audit it gates
        self.assertRegex(text, r"- \[ \] T4 — .*after: T3, T4\.1")
        plan_json = json.loads((self.rdir / "PLAN.json").read_text())
        mentioned = [p for p in plans.plan_md_consistency(self.rdir, plan_json, plan_id=plan_json["plan_id"]) if p.startswith(("T4.1", "T4."))]
        self.assertEqual([p for p in mentioned if "missing from PLAN.md" in p or ".after" in p], [])

    def test_a_planning_flow_that_is_off_or_fails_never_blocks_the_remediation(self):
        ask = rem.hook(self.rdir, self.policy)
        ask("T4", "att-0001", [finding("F1", ["T1"])])
        with patch("bt_planning_flow.active", side_effect=RuntimeError("boom")):
            self.assertEqual(rem.apply(self.rdir)["revision"], 2)

    def test_an_audit_that_used_its_rounds_or_cannot_be_built_falls_back_to_sending_tasks_back(self):
        policy = bt_audit_gate.Policy(remediation_rounds=1)
        ask = rem.hook(self.rdir, policy)
        self.assertTrue(ask("T4", "att-1", [finding("F1", ["T1"])]))
        rem.apply(self.rdir)
        self.assertFalse(ask("T4", "att-2", [finding("F2", ["T1"])]))                       # round limit spent
        self.assertFalse(rem.hook(self.rdir, bt_audit_gate.Policy(remediate=False))("T4", "a", [finding("F1", ["T1"])]))
        self.assertFalse(rem.hook(self.rdir, self.policy)("T4", "a", [finding("F1", ["T99"])]))
        self.assertFalse(rem.requested(self.rdir) and rem.read_request(self.rdir) is None)

    def test_owner_hold_preserves_the_pending_request_without_freezing_a_revision(self):
        ask = rem.hook(self.rdir, self.policy)
        self.assertTrue(ask("T4", "att-held", [finding("F1", ["T1"])]))
        hold = bt_scheduler_ops.hold_path(self.rdir)
        hold.parent.mkdir(parents=True, exist_ok=True)
        hold.write_text('{"why":"owner stop"}\n', encoding="utf-8")
        before = plans.latest_plan(self.rdir)
        self.assertIsNone(rem.apply(self.rdir))
        self.assertEqual(plans.latest_plan(self.rdir), before)
        self.assertTrue(rem.requested(self.rdir))
        self.assertEqual(plans.latest_plan(self.rdir)["revision"], 1)

    def test_interruption_after_freeze_adopts_the_journaled_revision_once(self):
        ask = rem.hook(self.rdir, self.policy)
        self.assertTrue(ask("T4", "att-crash", [finding("F1", ["T1"])]))
        original_freeze = plans.freeze_revision

        def freeze_then_interrupt(rdir, revised, source):
            original_freeze(rdir, revised, source)
            raise RuntimeError("simulated interruption after freeze")

        with patch.object(plans, "freeze_revision", side_effect=freeze_then_interrupt):
            with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                rem.apply(self.rdir)
        self.assertTrue(rem.requested(self.rdir))
        self.assertEqual(json.loads((self.rdir / rem.APPLY_JOURNAL).read_text())["stage"], "prepared")
        built = rem.apply(self.rdir)
        self.assertEqual((built["revision"], built["tasks"]), (2, ["T4.1"]))
        self.assertEqual([item["revision"] for item in plans.revisions(self.rdir)], [1, 2])
        self.assertEqual(rem.rounds_used(self.rdir, "T4"), 1)
        self.assertFalse(rem.requested(self.rdir))

    def test_committed_journal_accepts_a_later_remediation_request(self):
        ask = rem.hook(self.rdir, self.policy)
        self.assertTrue(ask("T4", "att-first", [finding("F1", ["T1"])]))
        self.assertEqual(rem.apply(self.rdir)["revision"], 2)
        self.assertTrue(ask("T4", "att-second", [finding("F2", ["T1"])]))
        result = rem.apply(self.rdir)
        self.assertEqual((result["revision"], result["tasks"]), (3, ["T4.2"]))
        self.assertEqual([item["revision"] for item in plans.revisions(self.rdir)], [1, 2, 3])

    def test_each_remediated_finding_is_charged_to_the_tasks_that_own_it(self):
        rem.record(self.rdir, "T4", 1, ["T4.1"], [finding("F1", ["T1"]), finding("F2", ["T2", "T3"])])
        events = rem.events(self.rdir)
        self.assertEqual([sorted(e["named"]) for e in events], [["T1"], ["T2", "T3"]])
        self.assertTrue(all(e["by"] == "audit-gate" for e in events))
        self.assertEqual(bt_attempt_log.overturn_of("T1", None, events, 3), "audit")

    def test_the_policy_reads_the_remediation_settings(self):
        values = {"gates.audit_remediation": False, "gates.remediation_rounds": 5}
        policy = bt_audit_gate.policy_from(lambda key, default=None: values.get(key, default))
        self.assertEqual((policy.remediate, policy.remediation_rounds), (False, 5))
        bad = bt_audit_gate.policy_from(lambda key, default=None: {"gates.remediation_rounds": -1}.get(key, default))
        self.assertEqual((bad.remediate, bad.remediation_rounds), (True, 2))


class Ledger(unittest.TestCase):
    def test_blocking_findings_carry_the_auditors_evidence(self):
        ledger = {"schema": "audit-findings/1", "findings": [
            {"id": "F1", "severity": "high", "status": "open", "summary": "Broken", "tasks": ["T1"], "evidence": "curl -> 404"}]}
        gate = bt_audit_gate.evaluate(json.dumps(ledger), ["T1", "T2"], "T2")
        self.assertEqual(gate.blocking[0]["evidence"], "curl -> 404")


if __name__ == "__main__":
    unittest.main()
