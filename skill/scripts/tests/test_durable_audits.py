"""Scenario K of REQ-030 (item 4): a milestone audit with several related failures compiles ONE bounded repair, verifies
it and audits again — end to end with real git, the real provider driver (fake `claude`), the M6 sandbox and DBOS.

The plan (1.3.0, one subplan): T1 → T2 → audit TA → T9. The fake auditor reports two related high findings (F1, F2, both
naming T1) until `fixed-k.txt` exists; T1 writes it only when its brief is a coordinated REMEDIATION. A second plan uses
an auditor that never clears, to prove the round limit."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import durable_support as lab_support
from bt_contracts.execution import RunRef
from durable_support import subplan, task
from test_durable_e2e import FAST, EngineCase

SERIAL = FAST.model_copy(update={"max_parallel": 1})


def plan_tasks(auditor: str) -> list[dict]:
    return [task("T1", scenario="fixk", subplan="SP-1", kind="implement"),
            task("T2", scenario="own", subplan="SP-1", kind="implement", after=["T1"]),
            task("TA", scenario=auditor, subplan="SP-1", kind="audit", after=["T2"],
                 paths=["docs/TA.md", "docs/TA.findings.json"]),
            task("T9", scenario="own", kind="implement", after=["TA"])]


class DurableAudits(EngineCase):
    def setUp(self):
        super().setUp()
        self.lab.configure(gates=lab_support.REAL_AUDIT_POLICY)
    def freeze(self, auditor: str) -> RunRef:
        return RunRef.model_validate(self.lab.freeze(plan_tasks(auditor), schema="1.3.0",
                                                     subplans=[subplan("SP-1", "T2", "TA")]))

    def per_task(self) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for launch in self.lab.launches():
            out.setdefault(launch["task"], []).append(launch)
        return out

    def projected(self, run: RunRef) -> dict[str, dict]:
        """The panels' read model of `run`, built from DBOS as the engine builds it (REQ-030 item 6)."""
        from bt_durable import projection
        doc = projection.build(self.client.client, run, projection.load_plan(run))
        return {item["id"]: item for item in doc["tasks"]}

    def events(self, name: str) -> list[dict]:
        rows = [json.loads(line) for line in (self.lab.state / "telemetry.jsonl").read_text().splitlines()]
        return [row for row in rows if row.get("event") == name]

    def test_related_audit_findings_become_one_coordinated_repair_then_the_audit_passes(self):
        run = self.freeze("auditk")
        self.start_engine()
        self.client.start(run, SERIAL)
        status = self.settled(run, timeout=420)
        self.assertEqual(status["summary"]["status"], "completed", status)
        launches = self.per_task()
        self.assertEqual({task_id: len(items) for task_id, items in launches.items()},
                         {"T1": 2, "T2": 1, "TA": 2, "T9": 1})          # one repair for both findings, one re-audit
        self.assertFalse(launches["T1"][0]["remediation"])
        self.assertTrue(launches["T1"][1]["remediation"])
        blocked = self.events("audit_blocked")
        self.assertEqual(len(blocked), 1, blocked)
        self.assertEqual(blocked[0]["repairs"], [{"owner": "T1", "findings": ["F1", "F2"]}])
        prompt = next(self.lab.state.glob("attempts-root/attempts/*-T1-a101-*/prompt.txt")).read_text()
        for needle in ("REMEDIATION", "F1 (high)", "F2 (high)", lab_support.CHECK_GOOD):
            self.assertIn(needle, prompt)                                # every finding and its probe in one brief
        # the audit ran again only after the repair was accepted, and its dependent only after the audit passed
        self.assertLess(launches["T1"][1]["at"], launches["TA"][1]["at"])
        self.assertLess(launches["TA"][1]["at"], launches["T9"][0]["at"])
        for ref in ("refs/bt/subplan/proj/REQ-900/r1/app/SP-1", "refs/bt/line/proj/REQ-900/r1/app"):
            self.assertIn("fixed-k.txt", lab_support.git(self.lab.repo, "ls-tree", "--name-only", ref).split())
        self.assertEqual(len(self.events("audit_passed")), 1)
        self.assertEqual(self.projected(run)["TA"]["state"], "completed")

    def test_an_audit_that_never_clears_stops_at_its_round_limit(self):
        run = self.freeze("auditnever")
        self.start_engine()
        self.client.start(run, SERIAL)
        status = self.settled(run, timeout=420)
        self.assertEqual(status["summary"]["status"], "blocked", status)
        self.assertEqual(status["summary"]["tasks"]["TA"], "blocked")
        self.assertIn("remediation round", status["summary"]["results"]["TA"]["audit"])
        launches = self.per_task()
        # gates.remediation_rounds = 2: two coordinated repairs, three audits, and nothing after the audit
        self.assertEqual({task_id: len(items) for task_id, items in launches.items()}, {"T1": 3, "T2": 1, "TA": 3})
        self.assertEqual(len(self.events("audit_blocked")), 3)
        # the panels show the audit held by the run (its last round itself completed), with the reason, and offer retry
        import bt_durable_panel as panel
        held = self.projected(run)["TA"]
        self.assertEqual((held["state"], held["workflow_status"]), ("blocked", "SUCCESS"))
        self.assertIn("remediation round", panel.reason_of(held))
        self.assertIn(held["state"], panel.STOPPED)


class RepairCompilation(unittest.TestCase):
    """The repair compiler alone (pure, over the legacy grouping): related findings share one repair, unrelated ones
    get their own, and a finding naming no task of the plan has no owner."""

    def plan(self):
        import hashlib

        from bt_durable.legacy import load_plan
        tasks = [*plan_tasks("auditk"), task("T5", scenario="own", subplan="SP-1", kind="implement", paths=["lib/b.txt"])]
        text = json.dumps({"schema_version": "1.3.0", "plan_id": "REQ-900", "revision": 1, "tasks": tasks,
                           "subplans": [subplan("SP-1", "T2", "TA")]})
        return load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(), plan_id="REQ-900", revision=1)

    def test_grouping(self):
        from bt_durable.adapters.audit import repairs
        blocking = [{"id": "F1", "severity": "high", "summary": "a", "tasks": ["T1"], "evidence": ""},
                    {"id": "F2", "severity": "critical", "summary": "b", "tasks": ["T1"], "evidence": "e"},
                    {"id": "F3", "severity": "high", "summary": "c", "tasks": ["T5"], "evidence": ""}]
        out = repairs(self.plan(), "TA", blocking)
        self.assertEqual([(r["owner"], sorted(r["findings"])) for r in out], [("T1", ["F1", "F2"]), ("T5", ["F3"])])
        self.assertIn("F2 (critical)", out[0]["note"])
        orphan = repairs(self.plan(), "TA", [{"id": "F9", "severity": "high", "summary": "x", "tasks": [], "evidence": ""}])
        self.assertEqual(orphan[0]["owner"], "")


class AuditInThePanels(unittest.TestCase):
    """The projection (REQ-030 item 6) of an audit the run holds: its round workflow ended SUCCESS/completed, the run's
    summary says `remediating` while the coordinated repairs run, and dependents are not queued meanwhile."""

    def test_a_remediating_audit_is_not_shown_completed(self):
        from types import SimpleNamespace

        import bt_durable_panel as panel
        from bt_durable import projection
        run = RunRef(project="proj", req="REQ-900", revision=1, plan_id="REQ-900", plan_path="/nonexistent",
                     plan_sha256="0" * 64)
        wid = f"bt:{run.run_id}"
        rows = [SimpleNamespace(workflow_id=wid, name=projection.RUN, status="PENDING", output=None),
                SimpleNamespace(workflow_id=f"{wid}:TA:k1", name=projection.TASK, status="SUCCESS",
                                output={"status": "completed"}),
                SimpleNamespace(workflow_id=f"{wid}:T1:k2", name=projection.TASK, status="PENDING", output=None)]
        summary = {"status": "running", "tasks": {"TA": "remediating", "T1": "running"}, "results": {}}
        source = SimpleNamespace(
            list_workflows=lambda workflow_id_prefix, **_: [r for r in rows if r.workflow_id.startswith(workflow_id_prefix)],
            get_event=lambda workflow_id, key, **_: summary if (workflow_id, key) == (wid, "summary") else None)
        tasks = {item["id"]: item for item in projection.build(source, run)["tasks"]}
        self.assertEqual(tasks["TA"]["state"], "recovering")
        self.assertIn("reparación coordinada", panel.reason_of(tasks["TA"]))
        self.assertNotIn(tasks["TA"]["state"], panel.STOPPED)          # nothing to retry while the repair runs
        summary["tasks"]["TA"] = "completed"                             # the re-audit passed
        self.assertEqual({t["id"]: t["state"] for t in projection.build(source, run)["tasks"]}["TA"], "completed")


if __name__ == "__main__":
    unittest.main()
