"""How the methodology uses the scheduler core: only through bt_scheduler_adapter, one direction, one authority per
requirement, and historical runs untouched (plan SC-AC18).

The core's own behaviour is tested inside the module (bt_scheduler_core/tests). Here: the boundary seen from outside,
the module suite as an isolated subprocess, the frozen-plan hand-over, the authority rules (scheduler vs legacy
RUN.json), the RUN.json projection, and read-only compatibility fixtures taken from the repository's real runs.
"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))
REPO = SCRIPTS.parent.parent

import bt_scheduler_adapter as adapter
import bt_scheduler_core as sc
from bt_scheduler_core.simulation import simulate

TASKS = [{"id": "T1", "milestone_id": "M1", "title": "First", "repository": "app", "expected_paths": ["a/**"], "after": []},
         {"id": "T2", "milestone_id": "M1", "title": "Second", "repository": "app", "expected_paths": ["b/**"], "after": ["T1"]},
         {"id": "T3", "milestone_id": "M2", "title": "Third", "repository": "docs", "expected_paths": ["d/**"], "after": []}]


def plan_text(revision: int = 1, tasks=None) -> str:
    return json.dumps({"schema_version": "1.0.0", "plan_id": "REQ-042", "revision": revision, "tasks": tasks or TASKS},
                      indent=2) + "\n"


def freeze(rdir: Path, text: str, revision: int = 1) -> str:
    """Write a frozen revision exactly in the layout the planner documents (file + manifest entry)."""
    folder = rdir / "plan-revisions"
    folder.mkdir(exist_ok=True)
    (folder / f"PLAN.r{revision}.json").write_text(text, encoding="utf-8")
    manifest = json.loads((folder / "MANIFEST.json").read_text()) if (folder / "MANIFEST.json").exists() \
        else {"schema": 1, "revisions": []}
    digest = hashlib.sha256(text.encode()).hexdigest()
    manifest["revisions"].append({"revision": revision, "sha256": digest, "frozen_at": "2026-10-14T00:00:00+00:00"})
    (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return digest


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="sched-integ-")
        self.addCleanup(self._tmp.cleanup)
        self.rdir = Path(self._tmp.name) / "REQ-042-demo"
        self.rdir.mkdir()


class Boundary(unittest.TestCase):
    ALLOWED_USERS = frozenset({"bt_scheduler_adapter.py", "test_scheduler_integration.py",
                               "test_scheduler_decision_sources.py", "test_scheduler_decision_integration.py",
                               "test_plan_contract_compat.py",
                               "test_package_install.py"})

    def names_in(self, path: Path) -> set[str]:
        found = set()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                found |= {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom) and not node.level:
                found.add((node.module or "").split(".")[0])
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value.split(".")[0])
        return found

    def test_only_the_adapter_imports_the_core(self):
        offenders = []
        for path in sorted(REPO.rglob("*.py")):
            rel = path.relative_to(REPO)
            if ".git" in rel.parts or "bt_scheduler_core" in rel.parts or "node_modules" in rel.parts \
                    or ".venv" in rel.parts or rel.parts[0] == "bitacora" \
                    or path.name in self.ALLOWED_USERS:
                continue
            try:
                if "bt_scheduler_core" in self.names_in(path):
                    offenders.append(str(rel))
            except (SyntaxError, UnicodeError):
                continue
        self.assertEqual(offenders, [], "only bt_scheduler_adapter may reach the scheduler core")
        self.assertIn("bt_scheduler_core", self.names_in(SCRIPTS / "bt_scheduler_adapter.py"))

    def test_the_core_imports_nothing_of_the_methodology(self):
        stdlib = set(sys.stdlib_module_names)
        for path in (SCRIPTS / "bt_scheduler_core").rglob("*.py"):
            if "tests" in path.parts:
                continue
            outside = {n for n in self.names_in(path) if n and n not in stdlib and n != "bt_scheduler_core"
                       and " " not in n and "." not in n and n.isidentifier() and n.startswith(("bt_", "bitacora"))}
            self.assertEqual(outside, set(), path.name)

    def test_the_adapter_reaches_the_planner_only_through_its_own_adapter(self):
        self.assertNotIn("bt_" + "planner", self.names_in(SCRIPTS / "bt_scheduler_adapter.py"))
        self.assertIn("bt_plan_adapter", self.names_in(SCRIPTS / "bt_scheduler_adapter.py"))

    def test_module_suite_passes_in_an_isolated_interpreter(self):
        done = subprocess.run([sys.executable, "-I", "-m", "unittest", "discover", "-s",
                               str(SCRIPTS / "bt_scheduler_core" / "tests")], capture_output=True, text=True, check=False, timeout=600,
                              cwd=tempfile.gettempdir(),
                              env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1",
                                   "BT_SCHEDULER_CORE_ISOLATED_COPY": "1"})   # the lone-copy test is part of the module run
        self.assertEqual(done.returncode, 0, (done.stderr or done.stdout)[-1500:])
        self.assertRegex(done.stderr, r"Ran \d+ tests")

    def test_the_module_is_packaged_next_to_its_adapter(self):
        config = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]
        self.assertIn("bt_scheduler_core", config["packages"])
        self.assertIn("bt_scheduler_adapter", config["py-modules"])
        self.assertIn("README.md", tomllib.loads((REPO / "pyproject.toml").read_text())["tool"]["setuptools"]["package-data"]["bt_scheduler_core"])

    def test_retired_supervisor_is_not_packaged(self):
        config = tomllib.loads((REPO / "pyproject.toml").read_text())["tool"]["setuptools"]
        for name in ("bt_run", "bt_runentry", "bt_run_isolated"):
            self.assertNotIn(name, config["py-modules"])
            self.assertFalse((SCRIPTS / (name + ".py")).exists())


class ApprovedPlan(Case):
    def test_the_latest_frozen_revision_is_loaded_against_the_recorded_hash(self):
        digest = freeze(self.rdir, plan_text(1))
        plan = adapter.approved_plan(self.rdir)
        self.assertEqual((plan.plan_id, plan.revision, plan.sha256), ("REQ-042", 1, digest))
        freeze(self.rdir, plan_text(2, TASKS[:2]), 2)
        self.assertEqual((adapter.approved_plan(self.rdir).revision, len(adapter.approved_plan(self.rdir).tasks)), (2, 2))

    def test_a_requirement_without_a_frozen_plan_has_nothing_approved(self):
        (self.rdir / "PLAN.json").write_text(plan_text(1), encoding="utf-8")      # valid JSON, never approved
        with self.assertRaises(sc.SchedulerError) as cm:
            adapter.approved_plan(self.rdir)
        self.assertEqual(cm.exception.code, "PLAN_NOT_APPROVED")

    def test_a_frozen_file_edited_after_the_freeze_is_refused(self):
        freeze(self.rdir, plan_text(1))
        path = self.rdir / "plan-revisions" / "PLAN.r1.json"
        path.chmod(0o644)
        path.write_text(plan_text(1).replace("Second", "Tampered"), encoding="utf-8")
        with self.assertRaises(sc.SchedulerError) as cm:
            adapter.approved_plan(self.rdir)
        self.assertIn(cm.exception.code, ("PLAN_NOT_APPROVED",))

    def test_a_damaged_store_is_refused_not_guessed(self):
        folder = self.rdir / "plan-revisions"
        folder.mkdir()
        (folder / "MANIFEST.json").write_text("{", encoding="utf-8")
        with self.assertRaises(sc.SchedulerError) as cm:
            adapter.approved_plan(self.rdir)
        self.assertEqual(cm.exception.code, "PLAN_NOT_APPROVED")

    def test_the_frozen_plan_file_is_never_modified(self):
        freeze(self.rdir, plan_text(1))
        path = self.rdir / "plan-revisions" / "PLAN.r1.json"
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        scheduler = adapter.open_scheduler(self.rdir)
        scheduler.step()
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)


class Authority(Case):
    def test_a_fresh_requirement_gets_its_own_database_and_nothing_else_is_written_next_to_the_plan(self):
        freeze(self.rdir, plan_text(1))
        before = {p.name for p in self.rdir.iterdir()}
        scheduler = adapter.open_scheduler(self.rdir)
        self.assertEqual(adapter.authority(self.rdir), "scheduler")
        added = {p.name for p in self.rdir.iterdir()} - before
        self.assertTrue(added and all(name.startswith(adapter.RUN_DB) for name in added), added)   # db + wal/shm only
        self.assertEqual(scheduler.snapshot().status, "running")

    def test_in_the_bitacora_layout_the_database_lives_in_the_untracked_state_folder(self):
        root = Path(self._tmp.name) / "bitacora"
        rdir = root / "demo" / "requirements" / "REQ-042-demo"
        rdir.mkdir(parents=True)
        freeze(rdir, plan_text(1))
        before = {p.name for p in rdir.iterdir()}
        scheduler = adapter.open_scheduler(rdir)
        expected = root / ".state" / "scheduler" / "demo-REQ-042.db"
        self.assertEqual((adapter.run_db_path(rdir), expected.exists(), adapter.authority(rdir)),
                         (expected, True, "scheduler"))
        self.assertEqual({p.name for p in rdir.iterdir()}, before)        # nothing next to the versioned documents
        adapter.write_projection(rdir, scheduler)
        self.assertEqual({p.name for p in rdir.iterdir()} - before, {adapter.PROJECTION})
        with self.assertRaises(SystemExit):
            adapter.refuse_legacy_run(rdir)

    def test_a_legacy_run_is_never_taken_over_or_modified(self):
        freeze(self.rdir, plan_text(1))
        legacy = self.rdir / "RUN.json"
        legacy.write_text(json.dumps({"req": "REQ-042", "status": "running", "sessions": 3,
                                      "tasks": [{"id": "T1", "status": "done", "attempts": 2}]}), encoding="utf-8")
        before = legacy.read_bytes()
        self.assertEqual(adapter.authority(self.rdir), "legacy")
        with self.assertRaises(sc.SchedulerError) as cm:
            adapter.open_scheduler(self.rdir)
        self.assertEqual(cm.exception.code, "NOT_ALLOWED")
        self.assertFalse((self.rdir / adapter.RUN_DB).exists())
        self.assertEqual(legacy.read_bytes(), before)

    def test_a_scheduler_owned_requirement_cannot_be_run_by_the_legacy_supervisor(self):
        freeze(self.rdir, plan_text(1))
        adapter.open_scheduler(self.rdir)
        with self.assertRaises(SystemExit) as cm:
            adapter.refuse_legacy_run(self.rdir)
        self.assertIn("AUTHORITY_CONFLICT", str(cm.exception))


    def test_a_requirement_without_any_run_is_free_for_the_legacy_supervisor(self):
        self.assertEqual(adapter.authority(self.rdir), "none")
        adapter.refuse_legacy_run(self.rdir)                                   # returns quietly

    def test_reopening_the_same_requirement_resumes_the_same_run(self):
        freeze(self.rdir, plan_text(1))
        first = adapter.open_scheduler(self.rdir)
        first.step()
        again = adapter.open_scheduler(self.rdir)
        self.assertEqual(again.snapshot().tasks["T1"]["state"], first.snapshot().tasks["T1"]["state"])
        self.assertEqual(again.read(lambda c: len(c.state.attempts)), 1)

    def test_a_newer_frozen_revision_does_not_silently_hijack_an_existing_run(self):
        freeze(self.rdir, plan_text(1))
        adapter.open_scheduler(self.rdir).step()
        freeze(self.rdir, plan_text(2), 2)
        with self.assertRaises(sc.SchedulerError) as cm:
            adapter.open_scheduler(self.rdir)
        self.assertEqual(cm.exception.code, "PLAN_MISMATCH")


class Projection(Case):
    def finished_scheduler(self):
        freeze(self.rdir, plan_text(1))
        scheduler = adapter.open_scheduler(self.rdir, config=sc.Config(max_parallel_tasks=2))
        # drive with the core's own simulated world on the same repository
        snap, core = simulate(scheduler.plan, scheduler.repository, sc.Config(max_parallel_tasks=2))
        return core, snap

    def test_projection_joins_frozen_complexity_with_the_run_route(self):
        text = plan_text(tasks=[TASKS[0] | {"complexity": "medium"}])
        sha = freeze(self.rdir, text)
        plan = adapter.approved_plan(self.rdir)
        snap = sc.Snapshot(
            plan_id=plan.plan_id, revision=plan.revision, plan_sha256=sha, status="running",
            paused=False, cancel_requested=False,
            tasks={"T1": {
                "state": "ready", "unreachable": False, "attempts": 0, "evidence": "", "executor": "",
                "route_metadata": {"schema_version": sc.ROUTING_CONTRACT_VERSION, "provider": "claude",
                                   "model": "sonnet", "effort": "xhigh", "profile": "claude-work",
                                   "account_ref": "acct:opaque-1", "assignment_reason": "route_policy_preferred",
                                   "quota_state": "fresh", "quota_reason": "quota_fresh",
                                   "quota_observed_at": "1792170000.0", "quota_valid_until": "1792177200.0",
                                   "quota_used_percent": "12.5"},
                "route_status": "recommended", "route_reason": "",
            }},
            counts={"ready": 1, "live_attempts": 0}, unreachable=(), attention=(), pending_outbox=0,
        )

        row = adapter.project(snap, plan)["tasks"][0]

        self.assertEqual((row["id"], row["milestone"], row["complexity"]), ("T1", "M1", "medium"))
        self.assertEqual((row["profile"], row["model"], row["effort"], row["route_status"]),
                         ("claude-work", "sonnet", "xhigh", "recommended"))
        self.assertEqual(row["provider"], "claude")
        self.assertEqual((row["account_ref"], row["selection_reason"], row["quota_state"],
                          row["quota_reason"], row["quota_observed_at"], row["quota_valid_until"],
                          row["quota_used_percent"]),
                         ("acct:opaque-1", "route_policy_preferred", "fresh", "quota_fresh",
                          "1792170000.0", "1792177200.0", "12.5"))

    def test_projection_keeps_stable_no_route_reason_without_fabricating_route_telemetry(self):
        text = plan_text(tasks=[TASKS[0] | {"complexity": "high"}])
        sha = freeze(self.rdir, text)
        plan = adapter.approved_plan(self.rdir)
        snap = sc.Snapshot(
            plan_id=plan.plan_id, revision=plan.revision, plan_sha256=sha, status="running",
            paused=False, cancel_requested=False,
            tasks={"T1": {"state": "blocked", "unreachable": False, "attempts": 0, "evidence": "", "executor": "",
                          "route_metadata": {}, "route_status": "unavailable",
                          "route_reason": "m2_batch_unavailable"}},
            counts={"blocked": 1, "live_attempts": 0}, unreachable=(), attention=(), pending_outbox=0,
        )

        row = adapter.project(snap, plan)["tasks"][0]

        self.assertEqual((row["route_status"], row["route_reason"], row["model"], row["account_ref"],
                          row["quota_state"]),
                         ("unavailable", "m2_batch_unavailable", "", "", ""))

    def test_projection_uses_the_legacy_vocabulary_and_marks_its_authority(self):
        core, snap = self.finished_scheduler()
        path = adapter.write_projection(self.rdir, core)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual((path.name, data["authority"], data["status"], data["scheduler_status"]),
                         (adapter.PROJECTION, "scheduler", "done", "completed"))
        self.assertEqual(data["plan_ref"], {"plan_id": "REQ-042", "revision": 1, "sha256": snap.plan_sha256})
        self.assertEqual({t["status"] for t in data["tasks"]}, {"done"})
        self.assertEqual([t["id"] for t in data["tasks"]], ["T1", "T2", "T3"])
        self.assertEqual(data["tasks"][1]["after"], ["T1"])
        self.assertEqual(adapter.authority(self.rdir), "scheduler")

    def test_every_core_state_maps_to_a_legacy_word_the_old_tools_know(self):
        legacy_tasks = {"todo", "in_progress", "done", "blocked", "integration_pending"}
        legacy_runs = {"running", "waiting", "paused", "stopped", "blocked", "done", "needs_revalidation"}
        self.assertEqual(set(adapter.TASK_STATUS), {s.value for s in sc.TaskState})
        self.assertEqual(set(adapter.RUN_STATUS), {s.value for s in sc.RunStatus})
        self.assertLessEqual(set(adapter.TASK_STATUS.values()), legacy_tasks)
        self.assertLessEqual(set(adapter.RUN_STATUS.values()), legacy_runs)

    def test_a_projection_is_never_called_run_json_so_it_cannot_touch_a_legacy_state_file(self):
        freeze(self.rdir, plan_text(1))
        legacy = self.rdir / "RUN.json"
        legacy.write_text('{"req": "REQ-042", "status": "running", "tasks": []}', encoding="utf-8")
        before = legacy.read_bytes()
        scheduler = sc.SchedulerCore(adapter.approved_plan(self.rdir), sc.InMemoryRepository())
        scheduler.start()
        target = adapter.write_projection(self.rdir, scheduler)
        self.assertEqual((target.name, legacy.read_bytes()), ("RUN.projection.json", before))
        self.assertEqual([p.name for p in self.rdir.iterdir() if p.name.startswith(".RUN")], [])  # no temp litter
        self.assertEqual(adapter.authority(self.rdir), "legacy")          # a projection proves nothing about authority

    def test_a_legacy_control_write_has_no_scheduler_file_to_land_in(self):
        """bt_runstate-style tools read/write RUN.json only; with a scheduler run there is none for them to change."""
        freeze(self.rdir, plan_text(1))
        scheduler = adapter.open_scheduler(self.rdir)
        adapter.write_projection(self.rdir, scheduler)
        self.assertFalse((self.rdir / "RUN.json").exists())

    def test_a_projection_is_rewritten_in_place_as_the_run_advances(self):
        freeze(self.rdir, plan_text(1))
        scheduler = adapter.open_scheduler(self.rdir, config=sc.Config(max_parallel_tasks=2))
        first = json.loads(adapter.write_projection(self.rdir, scheduler).read_text())
        scheduler.step()
        second = json.loads(adapter.write_projection(self.rdir, scheduler).read_text())
        self.assertEqual({t["status"] for t in first["tasks"]}, {"todo"})
        self.assertIn("in_progress", {t["status"] for t in second["tasks"]})
        self.assertEqual(second["sessions"], 2)


class HistoricalRuns(unittest.TestCase):
    """The real RUN.json files in this repository's bitácora copies: read-only fixtures (SC-AC18)."""

    def fixtures(self) -> list[Path]:
        return sorted(REPO.glob("bitacora/*/requirements/*/RUN.json"))

    def test_there_are_real_runs_to_protect(self):
        self.assertTrue(self.fixtures(), "no historical RUN.json found: the compatibility check would be vacuous")

    def test_every_adapter_operation_leaves_historical_runs_byte_identical(self):
        for run in self.fixtures():
            with self.subTest(run=str(run.relative_to(REPO))), tempfile.TemporaryDirectory(prefix="sched-hist-") as tmp:
                rdir = Path(tmp) / run.parent.name
                shutil.copytree(run.parent, rdir, ignore=shutil.ignore_patterns("plan-revisions"))
                digests = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in rdir.iterdir() if p.is_file()}
                self.assertEqual(adapter.authority(rdir), "legacy")
                adapter.refuse_legacy_run(rdir)                                # legacy runs stay the supervisor's
                with self.assertRaises(sc.SchedulerError):
                    adapter.open_scheduler(rdir)
                scratch = sc.SchedulerCore(sc.load_plan(plan_text(1), approved_sha256=hashlib.sha256(
                    plan_text(1).encode()).hexdigest()), sc.InMemoryRepository())
                scratch.start()
                adapter.write_projection(rdir, scratch)
                after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in rdir.iterdir() if p.is_file()}
                self.assertEqual(after.pop(adapter.PROJECTION) != "", True)    # only a new, separate file appeared
                self.assertEqual(after, digests)
                self.assertEqual(adapter.authority(rdir), "legacy")
                self.assertFalse((rdir / adapter.RUN_DB).exists())

    def test_the_real_files_are_only_read_never_created_or_changed_by_a_check(self):
        for run in self.fixtures():
            before = (run.read_bytes(), run.stat().st_mtime_ns, sorted(p.name for p in run.parent.iterdir()))
            self.assertEqual(adapter.authority(run.parent), "legacy")
            self.assertEqual((run.read_bytes(), run.stat().st_mtime_ns, sorted(p.name for p in run.parent.iterdir())), before)

    def test_the_legacy_vocabulary_the_projection_speaks_is_the_one_real_runs_use(self):
        seen_run, seen_task = set(), set()
        for run in self.fixtures():
            data = json.loads(run.read_text(encoding="utf-8"))
            seen_run.add(data.get("status"))
            seen_task |= {t.get("status") for t in data.get("tasks", [])}
        self.assertLessEqual(seen_task, {"todo", "in_progress", "done", "blocked", "integration_pending"})
        self.assertLessEqual(seen_run, set(adapter.RUN_STATUS.values()) | {"waiting", "stopped", "needs_revalidation"})


if __name__ == "__main__":
    unittest.main()
