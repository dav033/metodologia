"""A repair to a subplan reaches every subplan built on it by itself (D-297; pictures REQ-021 r39: «no pude combinar este
subplan con la versión actual de SP-2»; the owner: «lo que quiero que hagas es que algo así no vuelva a pasar»).

Real git. SP-1 and SP-2 build on nothing / SP-1; SP-3 builds on both. Each test lands a repair on an earlier subplan after
the later one was built, as a stage's repair does: nothing in the frozen plan makes the later line take it."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import bt_page_verification as page
import bt_verification as verification
import bt_verification_tree as tree
from bt_contracts.execution import RunRef, Snapshot
from bt_durable import reconcile, resolutions, solver
from bt_durable.adapters.composition import CompositionComposer
from bt_durable.adapters.integration import GitLineIntegrator

IDS = ("SP-1", "SP-2", "SP-3")
PLAN = {"subplans": [{"id": sid, "title": sid} for sid in IDS],
        "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2", "SP-3"], "task": "G1"}],
        "tasks": [{"id": "T1", "subplan_id": "SP-1", "repository": "app"},
                  {"id": "T2", "subplan_id": "SP-2", "repository": "app", "after": ["T1"]},
                  {"id": "T3", "subplan_id": "SP-3", "repository": "app", "after": ["T2"]},
                  {"id": "G1", "repository": "app", "after": ["T1", "T2", "T3"]}]}
FLAGS = {"solver.enabled": True, "healing.enabled": True, "healing.model_diagnosis": True, "diagnosis.auto": True,
         "solver.max_concurrent": 1, "solver.max_per_task": 3, "solver.max_minutes": 120, "solver.stuck_minutes": 45,
         "solver.resolution_after_seconds": 0, "solver.resolved_grace_minutes": 5}


class Lab(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="bt-reconcile-"))
        self.rdir = self.root / "proj" / "requirements" / "REQ-021-x"
        (self.rdir / ".planning").mkdir(parents=True)
        (self.rdir / ".planning" / "flow.json").write_text("{}")
        (self.rdir / "plan-revisions").mkdir()
        (self.rdir / "PLAN.json").write_text(json.dumps(PLAN))
        (self.rdir / "plan-revisions" / "PLAN.r3.json").write_text(json.dumps(PLAN))
        (self.rdir / "RUN.owner.json").write_text(json.dumps({"backend": "dbos", "run_id": "proj:REQ-021:r3"}))
        self.state_dir = self.root / ".state" / "durable"
        (self.state_dir / "composition").mkdir(parents=True)
        folder = self.state_dir / "projections" / "proj"
        folder.mkdir(parents=True)
        (folder / "REQ-021-r3.json").write_text(json.dumps({"tasks": [{"id": t["id"], "state": "completed"}
                                                                      for t in PLAN["tasks"]]}))
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "T")
        for patcher in (patch("bt_workspace.repos", lambda root, project, discover=True: {"app": self.repo}),
                        patch("bt_config.get", side_effect=lambda key, default=None: FLAGS.get(key, default))):
            patcher.start()
            self.addCleanup(patcher.stop)
        tree._CACHE.clear()
        self.run_ref = RunRef(project="proj", req="REQ-021", revision=3, plan_id="REQ-021", plan_sha256="0" * 64,
                              plan_path=self.rdir / "plan-revisions" / "PLAN.r3.json")
        self.one = self.write("shared.txt", "a\nb\nc\n", "T1")
        self.two = self.write("two.txt", "two\n", "T2")
        self.three = self.write("three.txt", "three\n", "T3")
        self.line("SP-1", self.one)
        self.line("SP-2", self.two)
        self.line("SP-3", self.three)

    def git(self, *args: str) -> str:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True).stdout.strip()

    def write(self, name: str, text: str, message: str, parent: str = "") -> str:
        if parent:
            self.git("checkout", "-q", "--detach", parent)
        (self.repo / name).write_text(text)
        self.git("add", name)
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def line(self, subplan: str, commit: str) -> None:
        self.git("update-ref", f"refs/bt/subplan/proj/REQ-021/r3/app/{subplan}", commit)

    def tip(self, subplan: str) -> str:
        return self.git("rev-parse", f"refs/bt/subplan/proj/REQ-021/r3/app/{subplan}")

    def rows(self) -> dict:
        return {r["id"]: r for r in verification.state(self.rdir)["subplans"]}

    def sweep(self, client=None) -> dict:
        return reconcile.sweep(self.root, self.rdir, self.run_ref, client=client, record=lambda rdir, text: None)

    def clash(self) -> None:
        """SP-3 edited a line of shared.txt its own way; a repair of SP-1 edits the same line."""
        self.line("SP-3", self.write("shared.txt", "a\nb by SP-3\nc\n", "T3b", parent=self.three))
        self.line("SP-1", self.write("shared.txt", "a\nb fixed\nc\n", "repair of SP-1", parent=self.one))

    @property
    def folder(self) -> Path:
        return self.state_dir / "composition" / "resolutions"


class ACleanRepair(Lab):
    def test_it_lands_on_the_later_lines_and_keeps_the_version_the_owner_saw(self):
        fixed = self.write("one.txt", "repair\n", "repair of SP-1", parent=self.one)
        self.line("SP-1", fixed)
        seen = self.rows()["SP-3"]                                  # the fold the owner is trying
        self.assertNotEqual(seen["commit"], self.three)
        with patch("bt_planning_activity.record"):
            self.assertIn("aprobado", verification.decide("proj", self.rdir, "SP-3", "approved"))
        self.sweep()
        self.assertEqual(self.git("show", f"{self.tip('SP-3')}:one.txt"), "repair")        # the line itself holds it
        self.assertEqual(self.git("show", f"{self.tip('SP-2')}:one.txt"), "repair")
        row = self.rows()["SP-3"]
        self.assertEqual((row["version"], row["commit"]), (seen["version"], seen["commit"]))
        self.assertEqual(row["state"], "approved")                  # the same tree: the decision stands
        self.assertEqual(reconcile.load(self.root, "proj", "REQ-021")["subplans"], {})

    def test_the_version_number_never_goes_back_when_the_line_takes_the_fold(self):
        fixed = self.write("one.txt", "repair\n", "repair of SP-1", parent=self.one)
        self.assertEqual(self.rows()["SP-3"]["version"], 1)         # v1: its line's tip, nothing folded yet
        self.line("SP-1", fixed)
        self.assertEqual(self.rows()["SP-3"]["version"], 2)
        self.sweep()
        self.assertEqual(self.rows()["SP-3"]["version"], 2)
        self.sweep()
        self.assertEqual(self.rows()["SP-3"]["version"], 2)
        self.line("SP-1", self.write("one.txt", "repair 2\n", "repair again", parent=fixed))
        self.sweep()
        self.assertEqual(self.rows()["SP-3"]["version"], 3)

    def test_an_earlier_subplan_never_moves_for_a_later_one_so_its_approval_stands(self):
        """pictures REQ-021: the owner approved SP-2 v2 (1c51118c0); SP-9's conflict with it must not touch it."""
        self.clash()
        tip = self.git("rev-parse", "refs/bt/subplan/proj/REQ-021/r3/app/SP-2")
        self.line("SP-2", self.git("rev-parse", "refs/bt/subplan/proj/REQ-021/r3/app/SP-2"))
        (self.rdir / "x").write_text("")
        self.line("SP-1", self.one)                                 # SP-2 holds SP-1: nothing lands on it
        approved = self.rows()["SP-2"]
        with patch("bt_planning_activity.record"):
            verification.decide("proj", self.rdir, "SP-2", "approved")
        self.line("SP-2", self.write("two.txt", "two fixed\n", "repair of SP-2", parent=tip))
        with patch("bt_planning_activity.record"):
            verification.decide("proj", self.rdir, "SP-2", "approved")
        approved = self.rows()["SP-2"]
        self.sweep()
        after = self.rows()["SP-2"]
        self.assertEqual((after["version"], after["commit"], after["state"]),
                         (approved["version"], approved["commit"], "approved"))
        self.assertEqual(self.git("show", f"{self.tip('SP-3')}:two.txt"), "two fixed")     # SP-3 took it


class AConflictingRepair(Lab):
    def test_the_system_asks_for_it_when_it_appears_and_moves_no_line_until_it_is_settled(self):
        self.clash()
        before = self.tip("SP-3")
        done = self.sweep()
        self.assertEqual(self.tip("SP-3"), before)                  # nothing half-combined reaches the line
        entry = reconcile.load(self.root, "proj", "REQ-021")["subplans"]["SP-3"]
        self.assertEqual((entry["with"], entry["files"]), ("SP-1", ["shared.txt"]))
        self.assertEqual(len(entry["keys"]), 1)
        key = entry["keys"][0]
        self.assertEqual(done["bound"][key]["subplan"], "SP-3")
        self.assertEqual(json.loads((self.folder / f"{key}.json").read_text())["path"], "shared.txt")   # the existing file

    def test_a_recorded_resolution_settles_it_in_the_same_process_and_the_line_takes_it(self):
        self.clash()
        before_row = self.rows()["SP-3"]
        self.assertEqual(before_row["fold_conflict"]["with"], "SP-1")      # memoized in this process, like the web's
        key = self.sweep()["pending"]["SP-3"]["keys"][0]
        (self.folder / f"{key}.resolved").write_text("a\nb fixed by SP-3\nc\n")
        self.assertEqual(self.rows()["SP-3"].get("fold_conflict", {}), {})   # not stale until a restart
        self.sweep()
        self.assertEqual(self.git("show", f"{self.tip('SP-3')}:shared.txt"), "a\nb fixed by SP-3\nc")
        row = self.rows()["SP-3"]
        self.assertEqual(row["commit"], self.tip("SP-3"))
        self.assertEqual(row.get("fold_conflict", {}), {})
        self.assertEqual(reconcile.load(self.root, "proj", "REQ-021")["subplans"], {})

    def test_a_criss_cross_history_is_settled_against_a_virtual_base(self):
        """pictures REQ-021 SP-5 x SP-14 (2 merge bases): `_settled` answered None, so even a recorded resolution left the
        predecessor out for good."""
        left = self.write("shared.txt", "a\nb by SP-3\nc\n", "T3b", parent=self.three)
        right = self.write("shared.txt", "a\nb fixed\nc\n", "repair of SP-1", parent=self.one)
        self.git("checkout", "-q", "--detach", left)
        self.git("merge", "-q", "--no-edit", "-s", "ours", right)
        ours = self.git("rev-parse", "HEAD")
        self.git("checkout", "-q", "--detach", right)
        self.git("merge", "-q", "--no-edit", "-s", "ours", left)
        theirs = self.write("shared.txt", "a\nb fixed again\nc\n", "repair again")
        self.assertEqual(len(self.git("merge-base", "--all", ours, theirs).split()), 2)
        (self.folder).mkdir(parents=True, exist_ok=True)
        self.line("SP-3", ours)
        self.line("SP-1", theirs)
        pending = self.sweep()["pending"]["SP-3"]
        (self.folder / f"{pending['keys'][0]}.resolved").write_text("a\nb combined\nc\n")
        self.sweep()
        self.assertEqual(self.git("show", f"{self.tip('SP-3')}:shared.txt"), "a\nb combined\nc")

    def test_subplans_holding_the_same_versions_of_a_file_share_one_request(self):
        """pictures REQ-021: SP-5, SP-7, SP-8, SP-9.. meet SP-2 in the same 11 files; one resolution is enough."""
        self.line("SP-3", self.write("shared.txt", "a\nb by both\nc\n", "T3b", parent=self.three))
        self.line("SP-2", self.write("shared.txt", "a\nb by both\nc\n", "T2b", parent=self.two))
        self.line("SP-1", self.write("shared.txt", "a\nb fixed\nc\n", "repair of SP-1", parent=self.one))
        done = self.sweep()
        self.assertEqual(len(done["bound"]), 1)                     # SP-3 waits for SP-2 and asks nothing of its own
        self.assertEqual((done["pending"]["SP-3"]["with"], done["pending"]["SP-3"]["keys"]), ("SP-2", []))
        (self.folder / f"{done['pending']['SP-2']['keys'][0]}.resolved").write_text("a\nb fixed by both\nc\n")
        self.assertEqual(self.sweep()["pending"], {})               # the same versions of the file: settled for both
        self.assertEqual(len(list(self.folder.glob("*.json"))), 1)
        self.assertEqual(self.git("show", f"{self.tip('SP-3')}:shared.txt"), "a\nb fixed by both\nc")
        self.assertEqual(self.git("show", f"{self.tip('SP-2')}:shared.txt"), "a\nb fixed by both\nc")

    def test_a_later_line_waits_for_the_one_it_builds_on_instead_of_asking_twice(self):
        """pictures REQ-021 r39: SP-6 asked 16 files against an SP-5 about to change, and then moved twice."""
        self.clash()                                                 # SP-3's own edit clashes with SP-1's repair
        plan = json.loads(json.dumps(PLAN))
        plan["subplans"].append({"id": "SP-4", "title": "SP-4"})
        plan["tasks"].append({"id": "T4", "subplan_id": "SP-4", "repository": "app", "after": ["T3"]})
        for name in ("PLAN.json", "plan-revisions/PLAN.r3.json"):
            (self.rdir / name).write_text(json.dumps(plan))
        four = self.write("shared.txt", "a\nb by SP-4\nc\n", "T4", parent=self.three)
        self.line("SP-4", four)
        done = self.sweep()
        self.assertEqual(done["pending"]["SP-4"]["keys"], [])        # no request of its own while SP-3 is unsettled
        self.assertEqual(done["pending"]["SP-4"]["with"], "SP-3")
        self.assertEqual(list(done["bound"]), done["pending"]["SP-3"]["keys"])
        self.assertEqual(self.tip("SP-4"), four)
        self.assertEqual(reconcile.problems(self.run_ref, done["pending"]), [])
        self.assertEqual(reconcile.view(self.rdir, "SP-4")["state"], "queued")

    def test_a_join_in_progress_is_left_alone(self):
        self.clash()
        (self.rdir / "RUN.join.json").write_text("{}")
        self.assertEqual(self.sweep()["bound"], {})
        self.assertFalse(self.folder.exists() and list(self.folder.glob("*.json")))


class Commands(Lab):
    def test_the_run_is_told_once_when_a_line_moved(self):
        self.line("SP-1", self.write("one.txt", "repair\n", "repair of SP-1", parent=self.one))
        sent = []
        client = SimpleNamespace(command=lambda run, kind, **fields: sent.append((kind, fields["request_id"])))
        self.sweep(client)
        self.sweep(client)
        self.assertEqual([kind for kind, _ in sent], ["recheck_gates"])


class TheOwnersPanel(Lab):
    def test_a_pending_reconciliation_is_not_offered_to_judge(self):
        self.clash()
        self.sweep()
        row = self.rows()["SP-3"]
        self.assertEqual(page._shown(row), "reconciling")
        warning = page._fold_warning(row, self.rdir)
        self.assertIn("Todavía no es lo que debes juzgar", warning)
        self.assertIn("SP-1", warning)
        self.assertIn("shared.txt", warning)
        with patch("bt_planning_activity.record"):
            refused = verification.decide("proj", self.rdir, "SP-3", "approved")
        self.assertIn("todavía", refused)
        self.assertEqual(self.rows()["SP-3"]["state"], "to_test")

    def test_the_panel_says_who_is_working_on_it_and_when_it_was_escalated(self):
        self.clash()
        key = self.sweep()["pending"]["SP-3"]["keys"][0]
        run_key = f"proj:REQ-021:r3:resolution:{key}"
        row = self.rows()["SP-3"]
        self.assertIn("en cuanto haya turno", page._fold_warning(row, self.rdir))
        solver.save(self.rdir, {"triggers": {run_key: {"kind": "resolution", "status": "running", "session": "S1",
                                                       "at": "2026-11-01T14:00:00"}},
                                "active": "S1", "sessions": [{"id": "S1", "started_at": "2026-11-01T14:00:00"}]})
        self.assertIn("El Solucionador lo está combinando", page._fold_warning(row, self.rdir))
        solver.save(self.rdir, {"triggers": {run_key: {"kind": "resolution", "status": "limit", "session": "S1"}}})
        warning = page._fold_warning(row, self.rdir)
        self.assertIn("te lo pasó", warning)
        self.assertNotIn("en cuanto haya turno", warning)

    def test_with_no_engine_pass_yet_it_does_not_claim_anyone_is_working(self):
        self.clash()
        warning = page._fold_warning(self.rows()["SP-3"], self.rdir)
        self.assertNotIn("Solucionador lo está", warning)
        self.assertIn("todavía no empezó", warning)


class TheSolucionador(Lab):
    def setUp(self):
        super().setUp()
        self.started, self.notified = [], []
        lab = self

        class Terminal:
            def exists(self, name):
                return any(s["name"] == name for s in lab.started)

            def name_for(self, project, req, role):
                return f"bit-{project}-{req}-{role}"

            def start(self, name, cwd, command, env, scope=""):
                lab.started.append({"name": name, "command": command})

            def screen(self, name, lines=20):
                return ""

            def send(self, name, text):
                pass

            def kill(self, name):
                lab.started[:] = [s for s in lab.started if s["name"] != name]

            def agent_state(self, name):
                return "busy"

        self.terminal = Terminal()
        (self.rdir / "RUN.durable-run.json").write_text(self.run_ref.model_dump_json())
        status = {"run_id": self.run_ref.run_id, "workflow_id": "bt:x", "workflow_status": "PENDING",
                  "summary": {"status": "running"}, "tasks": {}}
        self.client = SimpleNamespace(status=lambda run: status, command=lambda *a, **k: None)

    def solver(self):
        return solver.Solver(self.root, self.client, terminal=self.terminal,
                             route_for=lambda project, avoid: {"provider": "claude", "home": "", "model": "sonnet"},
                             notify=lambda title, text: self.notified.append(text),
                             record=lambda rdir, text: None, now=lambda: 2_000_000_000.0, work=self.root / "work",
                             state_dir=self.state_dir, integrating=lambda sid: [], weekly_cap=lambda *a: (None, ""))

    def test_a_conflict_nobody_decided_on_reaches_a_session_with_no_decision_open(self):
        self.clash()
        self.solver().run_pass([])
        state = solver.load(self.rdir)
        self.assertEqual(state["sessions"][0]["kind"], "resolution")
        session = Path(state["sessions"][0]["dir"])
        brief = (session / "BRIEF.md").read_text()
        self.assertIn("shared.txt", brief)
        self.assertIn("reconciliation", brief)
        self.assertNotIn("answer the task's open decision", brief)

    def test_a_session_that_leaves_the_request_open_does_not_close_it(self):
        """pictures REQ-021 20261101-015640-eab9 listed 30 requests as `handled` with no `.resolved`: nobody looked again."""
        self.clash()
        self.solver().run_pass([])
        state = solver.load(self.rdir)
        session = Path(state["sessions"][0]["dir"])
        (session / "result.json").write_text(json.dumps({"outcome": "fixed", "summary": "done", "handled": []}))
        self.solver().run_pass([])
        state = solver.load(self.rdir)
        self.assertEqual(len(state["sessions"]), 2)                 # it was given to another session at once
        self.assertEqual(len({t["status"] for t in state["triggers"].values()}), 1)

    def test_when_sessions_run_out_the_owner_is_told_and_the_panel_says_so(self):
        self.clash()
        for _ in range(4):
            self.solver().run_pass([])
            state = solver.load(self.rdir)
            if state.get("active"):
                session = Path(next(s for s in state["sessions"] if s["id"] == state["active"])["dir"])
                (session / "result.json").write_text(json.dumps({"outcome": "fixed", "summary": "done"}))
        self.solver().run_pass([])
        self.assertTrue(self.notified)
        state = solver.load(self.rdir)
        self.assertEqual({t["status"] for t in state["triggers"].values()}, {"limit"})
        self.assertIn("te lo pasó", page._fold_warning(self.rows()["SP-3"], self.rdir))

    def test_sessions_are_counted_once_each_however_many_files_they_hold(self):
        """pictures REQ-021: `tasks: {"T2.55": 18}` with few sessions: every file of a batch spent the task's sessions."""
        self.clash()
        (self.repo / "other.txt").write_text("x\n")
        self.line("SP-3", self.write("other.txt", "by SP-3\n", "T3c", parent=self.tip("SP-3")))
        self.git("checkout", "-q", "--detach", self.tip("SP-1"))
        self.line("SP-1", self.write("other.txt", "by repair\n", "repair 2"))
        self.solver().run_pass([])
        state = solver.load(self.rdir)
        self.assertEqual(len(state["triggers"]), 2)
        self.assertEqual(list(state["tasks"].values()), [1])

    def test_a_finished_plan_starts_nothing(self):
        self.clash()
        status = self.client.status(self.run_ref)
        status["summary"]["status"] = "completed"
        (self.rdir / ".planning" / "flow.json").unlink()            # not enrolled in owner verification: nothing to try
        self.solver().run_pass([])
        self.assertEqual(solver.load(self.rdir).get("sessions", []), [])
        self.assertFalse(self.folder.exists() and list(self.folder.glob("*.json")))

    def test_a_request_the_subplan_no_longer_needs_is_dropped(self):
        self.clash()
        self.solver().run_pass([])
        state = solver.load(self.rdir)
        session = Path(state["sessions"][0]["dir"])
        (session / "result.json").write_text(json.dumps({"outcome": "gave_up", "summary": "x"}))
        self.solver().run_pass([])
        self.line("SP-3", self.write("shared.txt", "a\nb fixed\nc\n", "SP-3 takes the repair by itself", parent=self.tip("SP-3")))
        self.solver().run_pass([])
        self.assertEqual(self.rows()["SP-3"].get("fold_conflict", {}), {})


class LeftOutMerges(Lab):
    """A merge whose conflict is left out by design opens no request nobody would ever answer (pictures REQ-021 r35 T94)."""

    def integrator(self):
        composer = SimpleNamespace(state_dir=self.state_dir)
        return GitLineIntegrator({"app": self.repo}, composer=composer)

    def requests(self) -> list[Path]:
        return list(self.folder.glob("*.json")) if self.folder.exists() else []

    def test_a_gate_base_that_leaves_a_line_out_asks_nothing(self):
        self.clash()
        task = SimpleNamespace(id="G1", repository="app")
        tip = self.integrator()._caught_up(self.repo, self.run_ref, task, self.tip("SP-1"), ("SP-3",))
        self.assertEqual(tip, self.tip("SP-1"))
        self.assertEqual(self.requests(), [])

    def test_a_line_that_is_left_out_asks_nothing_and_the_tasks_own_line_still_asks(self):
        self.clash()
        task = SimpleNamespace(id="T3b", repository="app")
        line = self.integrator()
        self.git("update-ref", line.line_ref(self.run_ref, "app"), self.one)
        self.git("update-ref", line.line_ref(self.run_ref, "app") + "-base", self.one)
        snapshot = self.write("shared.txt", "a\nb by the attempt\nc\n", "attempt", parent=self.one)
        done = line.integrate(self.run_ref, task, Snapshot(snapshot_sha=snapshot, base_sha=self.one, manifest_path=Path("/x")),
                              lines=("SP-1", "SP-3"), home="SP-3")
        self.assertIn("shared.txt", done[1])                        # its own line refuses it: this is worth asking
        self.assertEqual(len(self.requests()), 1)
        for request in self.requests():
            request.unlink()
        snapshot = self.write("one-more.txt", "x\n", "T3c", parent=self.tip("SP-3"))
        done = line.integrate(self.run_ref, task, Snapshot(snapshot_sha=snapshot, base_sha=self.tip("SP-3"), manifest_path=Path("/x")),
                              lines=("SP-1", "SP-3"), home="SP-3")
        self.assertEqual((done[1], list(done[3])), ("", ["SP-1"]))  # another subplan's line is left out
        self.assertEqual(self.requests(), [])


class TheComposerAfterwards(Lab):
    """One resolution is enough: after the lines took it no gate meets the same clash (pictures REQ-021: fold and composer
    asked separately, so an agent would have resolved the same clash twice and the owner would approve one of the two)."""

    def composer(self):
        from durable_support import gate, subplan, task

        from bt_durable.legacy import load_plan
        tasks = [task("T1", subplan="SP-1", kind="implement"), task("T2", subplan="SP-2", kind="implement", after=["T1"]),
                 task("T3", subplan="SP-3", kind="implement", after=["T2"]), task("G1", kind="test", after=["T1", "T2", "T3"])]
        for item in tasks:
            item["repository"] = "app"
        text = json.dumps({"schema_version": "1.3.0", "plan_id": "REQ-021", "revision": 3, "tasks": tasks,
                           "subplans": [subplan("SP-1", "T1", "T1"), subplan("SP-2", "T2", "T2"), subplan("SP-3", "T3", "T3")],
                           "composition_gates": [gate("CG-1", ["SP-1", "SP-2", "SP-3"], "G1")]})
        import hashlib
        plan = load_plan(text, approved_sha256=hashlib.sha256(text.encode()).hexdigest(), plan_id="REQ-021", revision=3)
        lines = GitLineIntegrator({"app": self.repo})
        self.git("update-ref", lines.line_ref(self.run_ref, "app"), self.one)
        self.git("update-ref", lines.line_ref(self.run_ref, "app") + "-base", self.git("rev-parse", f"{self.one}"))
        lines.composer = composer = CompositionComposer(self.state_dir, lines=lines, plan_for=lambda run: plan)
        return composer

    def evidence(self):
        return {sid: [{"task_id": f"T{sid[3:]}", "kind": "implement", "verdict_id": f"m6://result/{'0'*64}", "snapshot": ""}]
                for sid in IDS}

    def test_a_member_still_being_reconciled_holds_the_gate_without_opening_requests_of_its_own(self):
        self.clash()
        built = self.composer().compose(self.run_ref, "CG-1", self.evidence())
        self.assertEqual(built["state"], "rejected")
        self.assertTrue(built["reason"].startswith(reconcile.PENDING), built["reason"])
        self.assertEqual(built.get("conflicts", {}), {})

    def test_after_the_lines_took_the_resolution_the_gate_composes_cleanly(self):
        self.clash()
        composer = self.composer()
        key = self.sweep()["pending"]["SP-3"]["keys"][0]
        (self.folder / f"{key}.resolved").write_text("a\nb fixed by SP-3\nc\n")
        self.sweep()
        count = len(list(self.folder.glob("*.json")))
        built = composer.compose(self.run_ref, "CG-1", self.evidence())
        self.assertEqual(built["state"], "candidate", built)
        self.assertEqual(self.git("show", f"{built['commit']}:shared.txt"), "a\nb fixed by SP-3\nc")   # the owner's tree
        self.assertEqual(len(list(self.folder.glob("*.json"))), count)                # nothing to resolve twice


class Open(unittest.TestCase):
    def test_a_bound_request_goes_to_its_run_with_nothing_to_name_it(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            (folder / "k1.json").write_text(json.dumps({"path": "x.ts", "commits": {}}))
            old = 1000
            os.utime(folder / "k1.json", (old, old))
            statuses = {"proj:REQ-021:r3": {"tasks": {}}}
            bound = {"k1": {"run_id": "proj:REQ-021:r3", "subplan": "SP-3", "with": "SP-1"}}
            self.assertEqual(resolutions.triggers(folder, statuses, 2000, 120), [])
            found = resolutions.triggers(folder, statuses, 2000, 120, bound=bound)
            self.assertEqual([(i["run_id"], i["subplan"], i["reconcile"]) for i in found],
                             [("proj:REQ-021:r3", "SP-3×SP-1", True)])
            self.assertEqual(solver.slot(found[0]), "SP-3×SP-1")


if __name__ == "__main__":
    unittest.main()
