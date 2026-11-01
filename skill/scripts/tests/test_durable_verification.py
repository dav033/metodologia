"""«Probar» sees the subplan versions a durable run published, and the engine announces them (pictures REQ-021).

The durable composer keeps them in its own stores, never in RUN.projection.json, so a durable run's subplans stayed «se
está construyendo» and a stage queued behind one could never run."""
from __future__ import annotations

import json
import sqlite3
import subprocess
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


class LaterSubplanTree(unittest.TestCase):
    """What the owner tries for a later subplan holds the current accepted work of the subplans it builds on (D-246;
    pictures REQ-021 r29: a repair added to SP-2 never reached SP-14's line, so «Probar» SP-14 showed SP-2's old defect).
    SP-2 builds on SP-1 (T2 comes after T1); a repair T1B lands on SP-1's line after SP-2 was built."""

    line, states, rows = BuiltBeforeItsGate.line, BuiltBeforeItsGate.states, BuiltBeforeItsGate.rows

    def setUp(self):
        BuiltBeforeItsGate.setUp(self)
        plan = {"subplans": [{"id": "SP-1", "title": "one"}, {"id": "SP-2", "title": "two"}],
                "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2"], "task": "G1"}],
                "tasks": [{"id": "T1", "subplan_id": "SP-1", "repository": "app"},
                          {"id": "T1B", "subplan_id": "SP-1", "repository": "app", "after": ["T1"]},
                          {"id": "T2", "subplan_id": "SP-2", "repository": "app", "after": ["T1"]},
                          {"id": "G1", "repository": "app", "after": ["T1", "T2"]}]}
        (self.rdir / "PLAN.json").write_text(json.dumps(plan))
        (self.rdir / "plan-revisions" / "PLAN.r3.json").write_text(json.dumps(plan))
        self.one = self.write("one.txt", "one\n", "T1")
        self.two = self.write("two.txt", "two\n", "T2")          # SP-2's line holds SP-1's work (its ancestor)
        self.line("SP-1", self.one)
        self.line("SP-2", self.two)
        DurableVersions.publish(self, 3, "SP-1", 1, self.one, "2026-10-31T01:00:00+00:00")   # as CG-1 composed them
        DurableVersions.publish(self, 3, "SP-2", 1, self.two, "2026-10-31T01:00:00+00:00")
        self.states(T1="completed", T1B="completed", T2="completed", G1="completed")

    def write(self, name: str, text: str, message: str, parent: str = "") -> str:
        if parent:
            self.git("checkout", "-q", "--detach", parent)
        (self.repo / name).write_text(text)
        self.git("add", name)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def blob(self, commit: str, name: str) -> str:
        return self.git("show", f"{commit}:{name}")

    def test_an_unchanged_predecessor_keeps_the_version_and_is_named(self):
        row = self.rows()["SP-2"]
        self.assertEqual((row["version"], row["commit"]), (1, self.two))
        self.assertEqual(row["includes"], [{"id": "SP-1", "version": 1}])
        import bt_page_verification as page
        self.assertIn("SP-1 v1", page._tree_text(row))

    def test_a_repair_of_the_predecessor_reaches_the_later_subplans_tree_once(self):
        fixed = self.write("one.txt", "one, fixed\n", "T1B", parent=self.one)
        self.line("SP-1", fixed)
        rows = self.rows()
        self.assertEqual((rows["SP-1"]["version"], rows["SP-1"]["commit"]), (2, fixed))
        row = rows["SP-2"]
        self.assertEqual(row["version"], 2)                                   # a new tree: a new version
        self.assertEqual((self.blob(row["commit"], "one.txt"), self.blob(row["commit"], "two.txt")), ("one, fixed", "two"))
        self.assertEqual((row["includes"], row["fold_conflict"]), ([{"id": "SP-1", "version": 2}], {}))
        self.assertEqual(self.git("rev-parse", "refs/bt/try/proj/REQ-021/r3/app/SP-2"), row["commit"])
        import bt_verification_tree
        bt_verification_tree._CACHE.clear()                                   # another process reads it again
        self.assertEqual(self.rows()["SP-2"]["commit"], row["commit"])        # deterministic: the same version
        self.git("checkout", "-q", "--detach", fixed)
        self.git("commit", "-q", "--allow-empty", "-m", "re-seeded, same tree")
        self.line("SP-1", self.git("rev-parse", "HEAD"))
        again = self.rows()["SP-2"]
        self.assertEqual((again["version"], again["commit"]), (2, row["commit"]))   # same tree: the owner's decision holds
        with patch("bt_planning_activity.record"):
            verification.decide("proj", self.rdir, "SP-2", "approved")
        self.assertEqual(self.rows()["SP-2"]["state"], "approved")

    def test_a_predecessor_that_cannot_be_combined_is_said_not_hidden(self):
        clash = self.write("one.txt", "one, by SP-2\n", "SP-2 edits one.txt", parent=self.two)
        self.line("SP-2", clash)
        fixed = self.write("one.txt", "one, fixed\n", "T1B", parent=self.one)
        self.line("SP-1", fixed)
        row = self.rows()["SP-2"]
        self.assertEqual(row["commit"], clash)                                # its own tree, not a guess
        self.assertEqual(row["fold_conflict"], {"with": "SP-1", "files": ["one.txt"], "missing": []})
        self.assertEqual(row["includes"], [])                     # SP-1's current line is not in it
        import bt_page_verification as page
        self.assertIn("pero sin la versión actual de SP-1", page._tree_text(row))
        warning = page._fold_warning(row)
        self.assertIn("no pude combinar este subplan con la versión actual de SP-1", warning)
        self.assertIn("one.txt", warning)
        self.assertIn("puede seguir mostrando un defecto que allí ya se arregló", warning)    # no other predecessor lacks

    def predecessors_of_six(self) -> dict[str, str]:
        """SP-6 builds on five subplans in plan order: SP-1 merges cleanly, SP-2 clashes, SP-3 is never reached, SP-4 is in
        its history and SP-5 only re-seeded SP-4's tree, so merging it changes nothing."""
        ids = ["SP-1", "SP-2", "SP-3", "SP-4", "SP-5", "SP-6"]
        tasks = [{"id": f"T{sid[3:]}", "subplan_id": sid, "repository": "app"} for sid in ids]
        tasks[-1]["after"] = [t["id"] for t in tasks[:-1]]
        plan = {"subplans": [{"id": sid, "title": sid} for sid in ids], "tasks": tasks}
        (self.rdir / "PLAN.json").write_text(json.dumps(plan))
        (self.rdir / "plan-revisions" / "PLAN.r3.json").write_text(json.dumps(plan))
        held = self.write("held.txt", "held\n", "SP-4", parent=self.one)
        self.git("commit", "-q", "--allow-empty", "-m", "re-seeded, same tree")
        tips = {"SP-4": held, "SP-5": self.git("rev-parse", "HEAD"),
                "SP-6": self.write("clash.txt", "six\n", "SP-6", parent=held),
                "SP-1": self.write("a.txt", "a\n", "SP-1", parent=self.one),
                "SP-2": self.write("clash.txt", "two\n", "SP-2", parent=self.one),
                "SP-3": self.write("c.txt", "c\n", "SP-3", parent=self.one)}
        for sid, tip in tips.items():
            self.line(sid, tip)
        self.states(**{task["id"]: "completed" for task in tasks})
        return tips

    def test_the_warning_names_every_predecessor_the_tree_lacks_not_only_the_one_that_clashed(self):
        tips = self.predecessors_of_six()
        row = self.rows()["SP-6"]
        self.assertEqual((row["commit"], row["version"]), (tips["SP-6"], 1))  # reporting only: the tried tree is the same
        self.assertEqual(self.git("for-each-ref", "refs/bt/try/proj/REQ-021/r3/app/SP-6"), "")
        self.assertEqual(row["fold_conflict"], {"with": "SP-2", "files": ["clash.txt"], "missing": ["SP-1", "SP-3"]})
        self.assertEqual([item["id"] for item in row["includes"]], ["SP-4"])
        import bt_page_verification as page
        self.assertIn("pero sin la versión actual de SP-2, SP-1 y SP-3.", page._tree_text(row))
        warning = page._fold_warning(row)
        self.assertIn("con la versión actual de SP-2 (choca en clash.txt) y, por eso, tampoco con la de SP-1 y SP-3.", warning)
        self.assertIn("sin los cambios recientes de todos ellos", warning)
        self.assertNotIn("SP-5", warning)                                     # merging it changes nothing: nothing lacks

    def test_every_way_of_not_folding_reports_what_the_tree_lacks(self):
        import bt_verification_tree as tree
        tips = self.predecessors_of_six()
        preds = [(sid, tips[sid]) for sid in ("SP-1", "SP-2", "SP-3", "SP-4")]
        real = tree._git

        def failing(word: str):
            def run(repo, *args, env=None):
                return subprocess.CompletedProcess(args, 128, "", "boom") if word in args else real(repo, *args, env=env)
            return patch.object(tree, "_git", run)

        with failing(tips["SP-2"]):                                           # git cannot merge SP-2 at all
            failed = tree.fold(self.repo, tips["SP-6"], preds, "refs/bt/try/failed")
        self.assertEqual((failed["commit"], failed["conflict"]),
                         (tips["SP-6"], {"with": "SP-2", "files": [], "error": "boom", "missing": ["SP-1", "SP-3"]}))
        with failing("commit-tree"):                                          # the folded commit could not be made
            refused = tree.fold(self.repo, tips["SP-6"], preds, "refs/bt/try/refused")
        self.assertEqual((refused["commit"], refused["conflict"]),
                         (tips["SP-6"], {"with": "SP-1", "files": [], "error": "boom", "missing": ["SP-2", "SP-3"]}))
