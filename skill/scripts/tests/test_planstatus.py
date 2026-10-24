"""Read-only plan status: derived difficulty, legacy and scheduler overlays, listing, fingerprint, no writes."""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import bt_planstatus as ps  # noqa: E402


def contract_task(tid, milestone, complexity, after=()):
    return {"id": tid, "milestone_id": milestone, "title": f"Task {tid}", "objective": "x", "repository": "r",
            "after": list(after), "complexity": complexity, "scope": "small_change", "risk": "low",
            "coupling": "isolated", "confidence": "high", "estimated_minutes": 10, "kind": "implement"}


PLAN = {"schema_version": "1.0.0", "plan_id": "REQ-001", "revision": 2, "spec_ref": "SPEC.md",
        "milestones": [{"id": "M1", "title": "First", "acceptance_criteria": ["a"]},
                       {"id": "M2", "title": "Second", "acceptance_criteria": ["b"]}],
        "tasks": [contract_task("T1", "M1", "low"), contract_task("T2", "M1", "medium", ["T1"]),
                  contract_task("T3", "M2", "high", ["T2"]), contract_task("T4", "M2", "extreme", ["T3"])]}


def snapshot_tree(root: Path) -> dict[str, tuple[int, str]]:
    return {str(p): (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest())
            for p in sorted(root.rglob("*")) if p.is_file()}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()

    def test_status_carries_contract_version_and_owner_approval_per_ui_subplan(self):
        plan = {**PLAN, "schema_version": "1.3.0", "subplans": [{"id": "SP-1", "title": "Checkout",
                 "ui": {"contract": "checkout", "version": 3, "design_task": "T1",
                        "visual_review_task": "T4"}}]}
        rdir = self.req(contract=plan)
        status = ps.plan_status("demo", rdir)
        item = status["design_subplans"][0]
        self.assertEqual(item["contract"], "checkout@v3")
        self.assertEqual(item["design_state"], "pending")
        self.assertIsNone(item["approval"])
        import bt_planblock
        self.assertIn("checkout@v3", bt_planblock.status_table(status))
        self.assertIn("checkout@v3", bt_planblock.render_block(status))
        (rdir / "design-approvals.json").write_text(json.dumps({"schema_version": 1, "approvals": {
            "checkout@v3": {"status": "approved", "sha256": "a" * 64}}}), encoding="utf-8")
        self.assertEqual(ps.plan_status("demo", rdir)["design_subplans"][0]["approval"]["status"], "approved")

    def req(self, project="demo", name="REQ-001-demo", *, plan=True, md="status: approved", contract=PLAN):
        rdir = self.root / project / "requirements" / name
        rdir.mkdir(parents=True, exist_ok=True)
        if plan:
            (rdir / "PLAN.md").write_text(f"---\n{md}\n---\n# Plan — {name[:7]} — Demo title\n", encoding="utf-8")
        if contract is not None:
            (rdir / "PLAN.json").write_text(json.dumps(contract), encoding="utf-8")
        return rdir


class SubplanGrouping(Base):
    def test_status_carries_membership_and_titles_without_hiding_unassigned_tasks(self):
        plan = json.loads(json.dumps(PLAN))
        plan["schema_version"] = "1.3.0"
        plan["subplans"] = [{"id": "SP-1", "milestone_id": "M1", "title": "Auth slice"}]
        plan["tasks"][0]["subplan_id"] = "SP-1"
        plan["tasks"][1]["subplan_id"] = "SP-1"
        status = ps.plan_status("demo", self.req(contract=plan))
        self.assertEqual([task["subplan_id"] for task in status["milestones"][0]["tasks"]], ["SP-1", "SP-1"])
        self.assertEqual([task["subplan_title"] for task in status["milestones"][0]["tasks"]],
                         ["Auth slice", "Auth slice"])
        self.assertEqual([task["id"] for milestone in status["milestones"] for task in milestone["tasks"]],
                         ["T1", "T2", "T3", "T4"])


class ContractPlan(Base):
    def test_derived_milestone_difficulty_and_counts(self):
        status = ps.plan_status("demo", self.req())
        m1, m2 = status["milestones"]
        self.assertEqual((m1["difficulty"], m2["difficulty"]), ("medium", "extreme"))
        self.assertEqual(m2["difficulty_counts"], {"low": 0, "medium": 0, "high": 1, "extreme": 1})
        self.assertEqual(status["summary"]["difficulty"], "extreme")
        self.assertEqual(status["plan"]["revision"], 2)
        self.assertTrue(status["plan"]["has_contract"])
        self.assertEqual(status["plan"]["status"], "approved")
        self.assertEqual(status["title"], "Demo title")
        self.assertEqual(status["run"], {"authority": "none", "status": None, "active": False,
                                         "updated_at": status["run"]["updated_at"]})
        self.assertEqual(status["summary"]["tasks_total"], 4)
        self.assertEqual(status["milestones"][0]["tasks"][1]["after"], ["T1"])
        json.dumps(status)

    def test_plan_without_run_has_pending_tasks_and_no_attempts(self):
        for task in ps.plan_status("demo", self.req())["milestones"][0]["tasks"]:
            self.assertEqual((task["state"], task["attempt"], task["history"]), ("pending", None, []))


class LegacyRun(Base):
    def test_run_json_states_attempts_model_and_account(self):
        rdir = self.req()
        run = {"status": "running", "heartbeat": {"at": "2026-10-18T10:00:00"}, "tasks": [
            {"id": "T1", "status": "done", "attempts": 1, "evidence": "ok"},
            {"id": "T2", "status": "in_progress", "attempts": 2},
            {"id": "T3", "status": "blocked", "attempts": 3},
            {"id": "T4", "status": "todo", "attempts": 0}],
            "log": [{"at": "2026-10-18T09:00:00", "task": "T1", "result": "done", "seconds": 60, "model": "opus",
                     "effort": "high", "cost_usd": 0.5, "profile": "claude-personal", "agent": "claude"},
                    {"at": "2026-10-18T09:30:00", "task": "T2", "result": "failed", "seconds": 30, "model": "haiku",
                     "profile": "codex-luis", "agent": "codex"}]}
        (rdir / "RUN.json").write_text(json.dumps(run), encoding="utf-8")
        status = ps.plan_status("demo", rdir)
        tasks = {t["id"]: t for m in status["milestones"] for t in m["tasks"]}
        self.assertEqual([tasks[i]["state"] for i in ("T1", "T2", "T3", "T4")],
                         ["completed", "running", "blocked", "pending"])
        first = tasks["T1"]["attempt"]
        self.assertEqual((first["model_requested"], first["account"], first["cost_usd"], first["state"]),
                         ("opus", "claude-personal", 0.5, "completed"))
        self.assertEqual(first["started_at"], "2026-10-18T08:59:00")
        self.assertEqual(tasks["T2"]["attempt"]["state"], "rejected")
        self.assertEqual(tasks["T2"]["attempts"], 2)
        self.assertEqual(status["run"], {"authority": "legacy", "status": "running", "active": True,
                                         "updated_at": "2026-10-18T10:00:00"})
        self.assertEqual([m["state"] for m in status["milestones"]], ["running", "blocked"])
        self.assertEqual(status["milestones"][0]["progress"], {"done": 1, "total": 2})


class SchedulerRun(Base):
    def make(self):
        rdir = self.req()
        db = self.root / ".state" / "scheduler" / "demo-REQ-001.db"
        db.parent.mkdir(parents=True)
        attempts = {
            "A1": {"id": "A1", "task_id": "T1", "number": 1, "state": "rejected", "created_at": 1760000000.0,
                   "updated_at": 1760000100.0},
            "A2": {"id": "A2", "task_id": "T1", "number": 2, "state": "accepted", "created_at": 1760000200.0,
                   "updated_at": 1760000300.0}}
        doc = {"tasks": {"T1": {"state": "completed", "attempts": ["A1", "A2"]},
                         "T2": {"state": "active", "attempts": []}}, "attempts": attempts}
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
        conn.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
        conn.commit()
        conn.close()
        projection = {"authority": "scheduler", "projection": True, "req": "REQ-001", "status": "running",
                      "heartbeat_at": "2026-10-18T11:00:00+00:00",
                      "plan_ref": {"plan_id": "REQ-001", "revision": 2, "sha256": "a" * 64},
                      "tasks": [{"id": "T1", "title": "Task T1", "status": "done", "scheduler_state": "completed",
                                 "attempts": 2, "evidence": "tests green", "provider": "claude", "model": "opus",
                                 "effort": "high", "profile": "claude-personal", "account_ref": "h" * 16},
                                {"id": "T2", "title": "Task T2", "status": "in_progress",
                                 "scheduler_state": "active", "attempts": 0}]}
        (rdir / "RUN.projection.json").write_text(json.dumps(projection), encoding="utf-8")
        return rdir, db

    def test_projection_and_core_attempts(self):
        rdir, db = self.make()
        status = ps.plan_status("demo", rdir)
        self.assertEqual((status["run"]["authority"], status["run"]["active"]), ("scheduler", True))
        self.assertEqual(status["plan"]["sha256"], "a" * 64)
        t1 = status["milestones"][0]["tasks"][0]
        self.assertEqual((t1["state"], t1["attempts"], t1["evidence"]), ("completed", 2, "tests green"))
        self.assertEqual([a["state"] for a in t1["history"]], ["rejected", "accepted"])
        self.assertIsNone(t1["history"][0]["model_requested"])
        self.assertEqual((t1["attempt"]["id"], t1["attempt"]["model_requested"], t1["attempt"]["account"],
                          t1["attempt"]["account_ref"]), ("A2", "opus", "claude-personal", "h" * 16))
        self.assertEqual(t1["attempt"]["ended_at"], "2025-10-09T08:58:20+00:00")
        self.assertEqual(t1["history"][0]["started_at"], "2025-10-09T08:53:20+00:00")
        self.assertEqual(status["milestones"][0]["tasks"][1]["state"], "running")

    def test_read_only_guarantee(self):
        rdir, db = self.make()
        before = snapshot_tree(self.root)
        ps.plan_status("demo", rdir)
        ps.list_plans(self.root)
        ps.fingerprint(self.root)
        self.assertEqual(snapshot_tree(self.root), before)

    def test_missing_database_document_degrades_to_projection(self):
        rdir, db = self.make()
        sqlite3.connect(db).execute("DROP TABLE state").connection.commit()
        t1 = ps.plan_status("demo", rdir)["milestones"][0]["tasks"][0]
        self.assertEqual(len(t1["history"]), 1)
        self.assertEqual(t1["attempt"]["model_requested"], "opus")


class LegacyPlanMarkdown(Base):
    def test_plan_without_contract_falls_back_to_markdown(self):
        rdir = self.req(contract=None)
        (rdir / "PLAN.md").write_text(
            "---\nstatus: approved\n---\n# Plan — REQ-001 — Old\n### M1 — Start\n"
            "- [x] T1 — Do it · complexity: S\n- [ ] T2 — Next · after: T1\n### M2 — End\n- [ ] T3 — Last\n",
            encoding="utf-8")
        status = ps.plan_status("demo", rdir)
        self.assertFalse(status["plan"]["has_contract"])
        self.assertEqual([m["id"] for m in status["milestones"]], ["M1", "M2"])
        self.assertEqual(status["summary"]["tasks_done"], 1)
        self.assertEqual(status["milestones"][0]["difficulty"], "low")
        self.assertIsNone(status["milestones"][1]["difficulty"])
        self.assertEqual(status["milestones"][0]["tasks"][1]["after"], ["T1"])


class Listing(Base):
    def test_three_plans_two_active_and_filter(self):
        a = self.req("alpha", "REQ-001-a")
        b = self.req("beta", "REQ-002-b")
        c = self.req("beta", "REQ-003-c", md="status: archived")
        for rdir, status in ((a, "running"), (b, "paused")):
            (rdir / "RUN.json").write_text(json.dumps({"status": status, "tasks": []}), encoding="utf-8")
        (self.root / "gamma" / "requirements" / "REQ-004-nothing").mkdir(parents=True)
        rows = ps.list_plans(self.root)
        self.assertEqual([(r["project"], r["req_id"]) for r in rows],
                         [("alpha", "REQ-001"), ("beta", "REQ-002"), ("beta", "REQ-003")])
        self.assertEqual([r["active"] for r in rows], [True, True, False])
        self.assertEqual(rows[0]["difficulty"], "extreme")
        self.assertEqual(rows[0]["progress"], {"done": 0, "total": 4})
        self.assertEqual(rows[2]["plan_status"], "archived")
        self.assertEqual(len(ps.list_plans(self.root, include_inactive=False)), 2)
        self.assertEqual(ps.list_plans(self.root / "missing"), [])
        self.assertIsNotNone(c)

    def test_symlinked_root_is_resolved(self):
        self.req("alpha", "REQ-001-a")
        link = Path(self.tmp.name) / "link"
        link.symlink_to(self.root)
        self.assertEqual(len(ps.list_plans(link)), 1)


class Fingerprint(Base):
    def test_changes_only_when_a_watched_file_changes(self):
        rdir = self.req()
        first = ps.fingerprint(self.root)
        self.assertEqual(ps.fingerprint(self.root), first)
        (rdir / "notes.txt").write_text("irrelevant", encoding="utf-8")
        self.assertEqual(ps.fingerprint(self.root), first)
        (rdir / "RUN.json").write_text("{}", encoding="utf-8")
        second = ps.fingerprint(self.root)
        self.assertNotEqual(second, first)
        (rdir / "RUN.json").write_text('{"status": "running"}', encoding="utf-8")
        self.assertNotEqual(ps.fingerprint(self.root), second)


if __name__ == "__main__":
    unittest.main()
