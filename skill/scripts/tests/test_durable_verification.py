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


class BuiltBeforeItsGate(unittest.TestCase):
    """A subplan whose tasks are all accepted is offered to try from its line's tip, before any composition gate folds
    it (D-243; pictures REQ-021 SP-11/SP-12 stayed «se está construyendo» while CG-11/CG-12 waited on other work)."""

    def setUp(self):
        import subprocess
        self.root = Path(tempfile.mkdtemp(prefix="bt-built-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        (self.rdir / ".planning").mkdir(parents=True)
        (self.rdir / ".planning" / "flow.json").write_text("{}")
        plan = {"subplans": [{"id": "SP-1", "title": "one"}, {"id": "SP-2", "title": "two"}],
                "tasks": [{"id": "T1", "subplan_id": "SP-1", "repository": "app"},
                          {"id": "T2", "subplan_id": "SP-1", "repository": "app"},
                          {"id": "T3", "subplan_id": "SP-2", "repository": "app"}]}
        (self.rdir / "PLAN.json").write_text(json.dumps(plan))
        (self.rdir / "plan-revisions").mkdir()
        (self.rdir / "plan-revisions" / "PLAN.r3.json").write_text(json.dumps(plan))
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"backend": "dbos", "run_id": "proj:REQ-021:r3"}))
        self.store = self.root / ".state" / "durable" / "composition"
        self.store.mkdir(parents=True)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git = lambda *args: subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True,
                                                text=True).stdout.strip()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "T")
        self.repos = patch("bt_workspace.repos", lambda root, project, discover=True: {"app": self.repo})
        self.repos.start()
        self.addCleanup(self.repos.stop)

    def commit(self, text: str) -> str:
        (self.repo / "f.txt").write_text(text)
        self.git("add", "f.txt")
        self.git("commit", "-q", "--allow-empty", "-m", text)
        return self.git("rev-parse", "HEAD")

    def line(self, subplan: str, commit: str) -> None:
        self.git("update-ref", f"refs/bt/subplan/proj/REQ-021/r3/app/{subplan}", commit)

    def states(self, **states) -> None:
        folder = self.root / ".state" / "durable" / "projections" / "proj"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "REQ-021-r3.json").write_text(json.dumps({"tasks": [{"id": k, "state": v} for k, v in states.items()]}))

    def rows(self) -> dict:
        return {r["id"]: r for r in verification.state(self.rdir)["subplans"]}

    def test_a_complete_subplan_is_offered_from_its_line_and_an_unfinished_one_is_not(self):
        one, two = self.commit("one"), self.commit("two")
        self.line("SP-1", one)
        self.line("SP-2", two)
        self.states(T1="completed", T2="inherited", T3="running")
        rows = self.rows()
        self.assertEqual((rows["SP-1"]["state"], rows["SP-1"]["version"], rows["SP-1"]["commit"]), ("to_test", 1, one))
        self.assertEqual(rows["SP-2"]["state"], "waiting")

    def test_the_same_tree_keeps_the_published_version_and_a_new_tree_is_a_new_one(self):
        published = self.commit("same")
        DurableVersions.publish(self, 2, "SP-1", 1, published, "2026-10-30T01:00:00+00:00")
        self.git("commit", "-q", "--allow-empty", "-m", "re-seeded, same tree")
        self.line("SP-1", self.git("rev-parse", "HEAD"))
        self.states(T1="completed", T2="completed", T3="running")
        row = self.rows()["SP-1"]
        self.assertEqual((row["version"], row["commit"]), (1, published))     # a re-seeded line is not a new version
        changed = self.commit("repaired")
        self.line("SP-1", changed)
        row = self.rows()["SP-1"]
        self.assertEqual((row["version"], row["commit"]), (2, changed))
