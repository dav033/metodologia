"""«Probar» sees the subplan versions a durable run published, and the engine announces them (pictures REQ-021).

The durable composer keeps them in its own stores, never in RUN.projection.json, so a durable run's subplans stayed «se
está construyendo» and a stage queued behind one could never run."""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_verification as verification

A, B = "a" * 40, "b" * 40
PLAN = {"subplans": [{"id": "SP-1", "title": "one"}, {"id": "SP-2", "title": "two"}], "tasks": []}


class DurableVersions(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-durable-verify-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        (self.rdir / ".planning").mkdir(parents=True)
        (self.rdir / ".planning" / "flow.json").write_text("{}")
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))
        self.store = self.root / ".state" / "durable" / "composition"
        self.store.mkdir(parents=True)

    def owner(self, backend: str = "dbos") -> None:
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"backend": backend, "run_id": "proj:REQ-021:r3",
                                                              "workflow_id": "bt:proj:REQ-021:r3"}))

    def publish(self, revision: int, subplan: str, version: int, commit: str, at: str) -> None:
        with sqlite3.connect(self.store / f"proj-REQ-021-r{revision}-app.db") as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS versions(plan_id TEXT, subplan_id TEXT, version INTEGER, body TEXT, "
                         "request_sha256 TEXT)")
            conn.execute("INSERT INTO versions VALUES(?,?,?,?,?)",
                         (f"REQ-021.bt-r{revision}", subplan, version,
                          json.dumps({"commit": commit, "published_at": at, "subplan_id": subplan}), "x"))

    def test_a_legacy_run_keeps_reading_its_projection(self):
        self.owner("legacy")
        self.publish(1, "SP-1", 1, A, "2026-10-29T01:00:00+00:00")
        self.assertIsNone(verification.durable_versions(self.rdir))

    def test_published_versions_reach_probar_and_a_republished_tree_keeps_its_version(self):
        self.owner()
        self.publish(1, "SP-1", 1, A, "2026-10-29T01:00:00+00:00")
        self.publish(2, "SP-1", 1, A, "2026-10-29T02:00:00+00:00")         # a stage join re-publishes the same tree
        rows = {r["id"]: r for r in verification.state(self.rdir)["subplans"]}
        self.assertEqual((rows["SP-1"]["state"], rows["SP-1"]["version"], rows["SP-1"]["commit"]), ("to_test", 1, A))
        self.assertEqual(rows["SP-2"]["state"], "waiting")
        self.assertTrue(verification.applies(self.rdir))
        with patch("bt_planning_activity.record"):
            self.assertIn("SP-1 aprobado.", verification.decide("proj", self.rdir, "SP-1", "approved"))
        self.publish(3, "SP-1", 1, A, "2026-10-29T03:00:00+00:00")
        self.assertEqual({r["id"]: r["state"] for r in verification.state(self.rdir)["subplans"]}["SP-1"], "approved")

    def test_a_new_commit_is_a_new_version_and_outdates_the_decision(self):
        self.owner()
        self.publish(1, "SP-1", 1, A, "2026-10-29T01:00:00+00:00")
        with patch("bt_planning_activity.record"):
            verification.decide("proj", self.rdir, "SP-1", "approved")
        self.publish(1, "SP-1", 2, B, "2026-10-29T02:00:00+00:00")
        row = {r["id"]: r for r in verification.state(self.rdir)["subplans"]}["SP-1"]
        self.assertEqual((row["state"], row["version"], row["commit"]), ("outdated", 2, B))

    def test_the_engine_projector_announces_after_each_projection(self):
        from bt_contracts.execution import RunRef
        from bt_durable import projection

        class Row:
            workflow_id, status = "bt:proj:REQ-021:r3", "PENDING"
            input = {"args": [{"project": "proj", "req": "REQ-021", "plan_id": "REQ-021", "revision": 3,
                               "plan_sha256": "0" * 64, "plan_path": str(self.rdir / "plan-revisions" / "PLAN.r3.json")}]}

        class Source:
            def list_workflows(self, **_):
                return [Row()]

        (self.rdir / "plan-revisions").mkdir()
        with patch.object(projection, "project") as project, patch.object(projection, "load_plan", return_value=None), \
                patch.object(verification, "on_projection") as announce:
            self.assertEqual(projection.EngineProjector(Source()).refresh(), ["proj:REQ-021:r3"])
        project.assert_called_once()
        announce.assert_called_once_with(self.rdir)
        self.assertIsInstance(project.call_args.args[1], RunRef)


if __name__ == "__main__":
    unittest.main()
