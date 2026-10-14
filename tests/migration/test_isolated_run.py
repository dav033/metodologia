"""End-to-end opt-in worktree runs against throwaway repositories and state."""
from __future__ import annotations

import json
import io
import os
import signal
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

try:
    from ._isolated_run_fixture import HOME, SCRIPTS, TMP, IsolatedRunFixture
except ImportError:
    from _isolated_run_fixture import HOME, SCRIPTS, TMP, IsolatedRunFixture

import bt_core
import bt_run
import bt_run_isolated as isolated
import bt_runsettle
import bt_runstate as rs


class IsolatedRun(IsolatedRunFixture):
    def test_three_disjoint_same_repo_tasks_integrate_and_keep_main_unchanged(self):
        head = self.git(self.repo, "rev-parse", "HEAD")
        tasks = [("T1", "a.txt"), ("T2", "b.txt"), ("T3", "c.txt"), ("T4", "d.txt")]
        self.files({tid: {"file": f"src/{name}"} for tid, name in tasks})
        rows = [f"- [ ] {tid} — {tid} · repo: app · files: src/{name} · verify: `python -c \"from pathlib import Path; assert Path('src/{name}').exists()\"`"
                for tid, name in tasks[:3]]
        rows.append("- [ ] T4 — dependent · repo: app · after: T1, T2 · files: src/d.txt · verify: `python -c \"from pathlib import Path; assert Path('src/d.txt').exists()\"`")
        self.plan(rows)
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=3), 0)
        state = rs.load(self.rdir)
        self.assertTrue(all(task["status"] == "done" for task in state["tasks"]))
        self.assertEqual(self.git(self.repo, "rev-parse", "main"), head)
        allocations = [a for key, a in state["worktrees"].items() if not key.startswith("__integration__")]
        integration = state["worktrees"]["__integration__:app"]
        for _, name in tasks:
            self.assertTrue((Path(integration["worktree"]) / "src" / name).is_file())
        dirs = {row["cwd"] for row in self.records() if row["task"] != "FINAL"}
        self.assertEqual(len(dirs), 4)
        self.assertTrue(all(not Path(a["worktree"]).exists() for a in allocations))
        listed = self.git(self.repo, "worktree", "list", "--porcelain")
        self.assertEqual(sum(line.startswith("worktree ") for line in listed.splitlines()), 2)
        self.assertTrue(any(row.get("isolation") == "worktree" and row.get("branch") for row in state["log"]))

    def test_three_disjoint_batch_stress_keeps_every_allocation(self):
        for _ in range(15):
            self.setUp()
            tasks = [(f"T{i}", f"stress-{i}.txt") for i in range(1, 4)]
            self.files({tid: {"file": f"src/{name}"} for tid, name in tasks})
            self.plan([f"- [ ] {tid} — {tid} · repo: app · files: src/{name} · verify: `python -c \"from pathlib import Path; assert Path('src/{name}').exists()\"`"
                       for tid, name in tasks])
            self.assertEqual(self.run_supervisor(isolation="worktree", workers=3), 0)
            state = rs.load(self.rdir)
            self.assertTrue(all(rs.get_task(state, tid)["status"] == "done" for tid, _ in tasks))
            self.assertEqual(set(state["worktrees"]) & {tid for tid, _ in tasks}, {tid for tid, _ in tasks})

    def test_three_workers_measurably_beat_one_on_three_disjoint_tasks(self):
        """T13 measurement: same plan, stub sessions of 2 s each, one worker then three. Numbers are printed and
        kept in the test's temp dir; the assertion only requires a clear win, not a specific speed-up."""
        os.environ["STUB_SLEEP"] = "2.0"
        self.addCleanup(os.environ.__setitem__, "STUB_SLEEP", "0.25")
        timings = {}
        for workers in (1, 3):
            self.setUp()
            os.environ["STUB_SLEEP"] = "2.0"
            tasks = [(f"T{i}", f"cap-{i}.txt") for i in range(1, 4)]
            self.files({tid: {"file": f"src/{name}"} for tid, name in tasks})
            self.plan([f"- [ ] {tid} — {tid} · repo: app · files: src/{name} · verify: `python -c \"from pathlib import Path; assert Path('src/{name}').exists()\"`"
                       for tid, name in tasks])
            started = time.monotonic()
            self.assertEqual(self.run_supervisor(isolation="worktree", workers=workers), 0)
            timings[workers] = round(time.monotonic() - started, 2)
            state = rs.load(self.rdir)
            self.assertTrue(all(rs.get_task(state, tid)["status"] == "done" for tid, _ in tasks))
        print(f"\nCAPACITY wall seconds for 3 tasks of 2 s: 1 worker {timings[1]} | 3 workers {timings[3]} | "
              f"load {os.getloadavg()}", file=sys.stderr)
        (TMP / "capacity.json").write_text(json.dumps({"seconds": timings, "load": os.getloadavg()}))
        self.assertLess(timings[3], timings[1] * 0.8)

    def test_concurrent_prepare_updates_worktree_records_by_key(self):
        self.plan(["- [ ] T1 — first · repo: app · files: a.txt",
                   "- [ ] T2 — second · repo: app · files: b.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 2, "isolation": "worktree"})
        rs.save(self.rdir, state)
        barrier = threading.Barrier(2)
        allocate = isolated.bt_worktree.allocate

        def allocate_together(*args, **kwargs):
            result = allocate(*args, **kwargs)
            barrier.wait(timeout=10)
            return result

        isolated.bt_worktree.allocate = allocate_together
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(isolated.prepare, self.project, state, self.rdir, [[task]])
                           for task in state["tasks"]]
                for future in futures:
                    future.result(timeout=20)
        finally:
            isolated.bt_worktree.allocate = allocate
        saved = rs.load(self.rdir)["worktrees"]
        self.assertTrue({"T1", "T2"}.issubset(saved))

    def _audit_change_run(self, action: str):
        self.files({"T1": {"file": "one.txt"}})
        self.plan(["### M1 — First", "- [ ] T1 — first · repo: app · files: one.txt"])
        os.environ["STUB_AUDIT_ACTION"] = action
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, audit=True), 0)
        os.environ.pop("STUB_AUDIT_ACTION", None)
        state = rs.load(self.rdir)
        integration = Path(state["worktrees"]["__integration__:app"]["worktree"])
        audit_head = next(row["head"] for row in self.records() if row["task"] == "M1-audit")
        self.assertEqual(self.git(integration, "rev-parse", "HEAD"), audit_head)
        self.assertEqual((self.repo / "README.md").read_text(), "base\n")
        branches = self.git(self.repo, "branch", "--list", "wt/M1-audit-audit-changes-*").splitlines()
        self.assertEqual(len(branches), 1)
        branch = branches[0].strip()
        self.assertEqual(self.git(self.repo, "show", f"{branch}:README.md"), "audit change")
        self.assertTrue(any(row.get("result") == "plan_warning" and branch in row.get("warning", "")
                            for row in state["log"]))
        self.assertTrue(rs.get_task(state, "M1-audit")["status"] == "done")

    def test_audit_commit_is_preserved_without_moving_integration_or_checkout(self):
        self._audit_change_run("commit")

    def test_audit_dirty_tree_is_preserved_without_moving_integration_or_checkout(self):
        self._audit_change_run("dirty")

    def test_audit_without_integration_worktree_uses_detached_throwaway(self):
        self.plan(["### M1 — First", "- [x] T1 — first · repo: app · files: one.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 1, "isolation": "worktree"}, audit=True)
        audit = rs.get_task(state, "M1-audit")
        audit.update(status="todo", evidence=None)
        rs.save(self.rdir, state)
        self.assertNotIn("__integration__", state.get("worktrees", {}))
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, audit=True), 0)
        record = next(row for row in self.records() if row["task"] == "M1-audit")
        self.assertNotEqual(Path(record["cwd"]).resolve(), self.repo.resolve())
        self.assertTrue(record["recorded"])

    def test_sigkill_during_dirty_audit_resumes_without_cleanliness_wedge(self):
        self.plan(["### M1 — First", "- [x] T1 — first · repo: app · files: one.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 1, "isolation": "worktree"}, audit=True)
        rs.get_task(state, "M1-audit").update(status="todo", evidence=None)
        rs.save(self.rdir, state)
        os.environ["STUB_AUDIT_ACTION"] = "sleep"
        code = (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import bt_run; "
                f"raise SystemExit(bt_run.supervise({self.project!r}, 'REQ-001', agent_cmd={self.cmd!r}, "
                "isolation='worktree', workers=1, audit=True, no_autostart=True))")
        proc = subprocess.Popen([sys.executable, "-c", code], env=os.environ.copy(), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        deadline = time.time() + 15
        while time.time() < deadline:
            if self.starts.exists() and any(row["task"] == "M1-audit" for row in self.records()):
                break
            time.sleep(0.05)
        self.assertTrue(self.starts.exists(), "audit session did not start")
        proc.kill()
        proc.wait(timeout=5)
        os.environ.pop("STUB_AUDIT_ACTION", None)
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, audit=True), 0)
        state = rs.load(self.rdir)
        self.assertEqual(rs.get_task(state, "M1-audit")["status"], "done")
        self.assertEqual((self.repo / "README.md").read_text(), "base\n")
        self.assertTrue(self.git(self.repo, "branch", "--list", "wt/M1-audit-audit-changes-*").strip())
        self.assertFalse(any("must be clean" in entry.get("warning", "") for entry in state["log"]))

    def test_overlapping_and_unscoped_tasks_serialize(self):
        self.files({"T1": {"file": "same.txt"}, "T2": {"file": "same.txt"}, "T3": {"file": "last.txt"}})
        self.plan(["- [ ] T1 — first · repo: app · files: same.txt",
                   "- [ ] T2 — overlap · repo: app · files: same.txt",
                   "- [ ] T3 — unscoped · repo: app"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 3, "isolation": "worktree"})
        self.assertEqual([[task["id"] for task in unit] for unit in rs.ready_units(state, 3)], [["T1"]])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=3, max_attempts=1), 2)
        records = self.records()
        task_records = [row for row in records if row["task"] != "FINAL"]
        self.assertEqual(len(task_records), 3)
        self.assertGreater(task_records[1]["time"], task_records[0]["time"])
        self.assertGreater(task_records[2]["time"], task_records[1]["time"])

    def test_shared_resource_tag_serializes_disjoint_file_scopes(self):
        self.files({"T1": {"file": "a.txt"}, "T2": {"file": "b.txt"}})
        self.plan(["- [ ] T1 — lock one · repo: app · files: a.txt · resources: lockfile",
                   "- [ ] T2 — lock two · repo: app · files: b.txt · resources: lockfile"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 3, "isolation": "worktree"})
        self.assertEqual([[task["id"] for task in unit] for unit in rs.ready_units(state, 3)], [["T1"]])

    def test_out_of_scope_candidate_is_rejected_and_preserved(self):
        self.files({"T1": {"file": "allowed.txt", "write": "escape.txt"}})
        self.plan(["- [ ] T1 — escape · repo: app · files: allowed.txt"])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, max_attempts=1), 2)
        task = rs.get_task(rs.load(self.rdir), "T1")
        self.assertEqual(task["status"], "blocked")
        self.assertIn("integration:", task["last_error"])
        allocation = rs.load(self.rdir)["worktrees"]["T1"]
        self.assertTrue(Path(allocation["worktree"]).is_dir())

    def test_failed_session_keeps_its_failure_instead_of_becoming_integration_failure(self):
        self.files({})
        self.plan(["- [ ] T1 — agent fails · repo: app · files: missing.txt"])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, max_attempts=1), 2)
        task = rs.get_task(rs.load(self.rdir), "T1")
        self.assertEqual(task["status"], "blocked")
        self.assertNotIn("integration:", task["last_error"] or "")

    def test_one_worker_still_integrates_into_the_requirement_branch(self):
        self.files({"T1": {"file": "serial.txt"}})
        self.plan(["- [ ] T1 — serial · repo: app · files: serial.txt"])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1), 0)
        state = rs.load(self.rdir)
        self.assertEqual(rs.get_task(state, "T1")["status"], "done")
        integration = state["worktrees"]["__integration__:app"]
        self.assertTrue((Path(integration["worktree"]) / "serial.txt").exists())

    def test_each_repo_role_gets_its_own_integration_worktree(self):
        other = TMP / f"docs{self.serial}"
        other.mkdir()
        self.git(other, "init", "-b", "main")
        self.git(other, "config", "user.name", "Test")
        self.git(other, "config", "user.email", "test@example.invalid")
        (other / "README.md").write_text("docs base\n")
        self.git(other, "add", "README.md")
        self.git(other, "commit", "-m", "base")
        bt_core.register_repo(self.project, other, "docs")
        self.files({"T1": {"file": "app.txt"}, "T2": {"file": "docs.txt"}})
        self.plan(["- [ ] T1 — app task · repo: app · files: app.txt",
                   "- [ ] T2 — docs task · repo: docs · files: docs.txt"])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=1), 0)
        state = rs.load(self.rdir)
        app = state["worktrees"]["__integration__:app"]
        docs = state["worktrees"]["__integration__:docs"]
        self.assertNotEqual(Path(app["repo"]).resolve(), Path(docs["repo"]).resolve())
        self.assertTrue((Path(app["worktree"]) / "app.txt").is_file())
        self.assertFalse((Path(app["worktree"]) / "docs.txt").exists())
        self.assertTrue((Path(docs["worktree"]) / "docs.txt").is_file())
        self.assertFalse((Path(docs["worktree"]) / "app.txt").exists())

    def _audit_allocation(self, label="M1-audit"):
        self.plan(["### M1 — First", "- [ ] T1 — first · repo: app · files: one.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 1, "isolation": "worktree"}, audit=True)
        rs.save(self.rdir, state)
        return isolated.prepare_audit(self.project, state, self.rdir, rs.get_task(state, label))

    def test_audit_preservation_branch_failure_keeps_worktree_and_warns(self):
        allocation = self._audit_allocation()
        Path(allocation["worktree"], "review.txt").write_text("review\n")
        original = subprocess.run

        def fail_preservation_branch(args, *positional, **kwargs):
            if args[:2] == ["git", "branch"] and args[2].startswith("wt/M1-audit-audit-changes-"):
                raise subprocess.CalledProcessError(1, args, stderr="branch conflict")
            return original(args, *positional, **kwargs)

        with patch("bt_run_isolated.subprocess.run", side_effect=fail_preservation_branch):
            self.assertIsNone(isolated.finish_audit(self.rdir, "M1-audit"))
        saved = rs.load(self.rdir)["worktrees"]["M1-audit"]
        self.assertEqual(saved["state"], "needs_attention")
        self.assertTrue(Path(saved["worktree"]).is_dir())
        self.assertTrue(any("audit_cleanup_failed" in row.get("warning", "") and saved["worktree"] in row["warning"]
                            for row in rs.load(self.rdir)["log"]))

    def test_audit_remove_failure_keeps_worktree_and_warns(self):
        allocation = self._audit_allocation()
        original = subprocess.run

        def fail_remove(args, *positional, **kwargs):
            if args[:3] == ["git", "worktree", "remove"]:
                raise subprocess.CalledProcessError(1, args, stderr="remove failed")
            return original(args, *positional, **kwargs)

        with patch("bt_run_isolated.subprocess.run", side_effect=fail_remove):
            self.assertIsNone(isolated.finish_audit(self.rdir, "M1-audit"))
        saved = rs.load(self.rdir)["worktrees"]["M1-audit"]
        self.assertEqual(saved["state"], "needs_attention")
        self.assertTrue(Path(allocation["worktree"]).is_dir())

    def test_audit_reports_shared_ref_created_in_review_worktree(self):
        allocation = self._audit_allocation()
        ref = "refs/heads/audit-leaked-ref"
        self.git(Path(allocation["worktree"]), "branch", "audit-leaked-ref")
        self.assertIsNone(isolated.finish_audit(self.rdir, "M1-audit"))
        self.assertEqual(self.git(self.repo, "show-ref", "--verify", ref).split()[1], ref)
        self.assertTrue(any(ref in row.get("warning", "") for row in rs.load(self.rdir)["log"]))

    def test_missing_audit_worktree_prunes_stale_git_metadata(self):
        path = TMP / f"stale-{self.serial}"
        self.git(self.repo, "worktree", "add", "--detach", str(path), "HEAD")
        shutil.rmtree(path)
        sha = self.git(self.repo, "rev-parse", "HEAD")
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 1, "isolation": "worktree"})
        state.setdefault("worktrees", {})["M1-audit"] = {"task_id": "M1-audit", "audit": True,
            "repo": str(self.repo), "worktree": str(path), "base_sha": sha, "state": "audit_running"}
        rs.save(self.rdir, state)
        isolated.finish_audit(self.rdir, "M1-audit")
        listed = self.git(self.repo, "worktree", "list", "--porcelain")
        self.assertEqual(sum(line.startswith("worktree ") for line in listed.splitlines()), 1)
        self.assertNotIn("M1-audit", rs.load(self.rdir)["worktrees"])

    def test_recovery_candidate_error_marks_attention_and_continues(self):
        self.plan(["- [ ] T1 — candidate pending · repo: app · files: one.txt",
                   "- [ ] T2 — candidate resumes · repo: app · files: two.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 1, "isolation": "worktree"})
        rs.get_task(state, "T1")["status"] = "integration_pending"
        rs.get_task(state, "T2")["status"] = "integration_pending"
        state.setdefault("worktrees", {})["T1"] = {"task_id": "T1", "task_ids": ["T1"],
            "repo": str(self.repo), "worktree": str(TMP / "missing-candidate"), "journal": str(TMP / "journal"),
            "state": "candidate"}
        state["worktrees"]["T2"] = {"task_id": "T2", "task_ids": ["T2"], "repo": str(self.repo),
            "worktree": str(TMP / "candidate-two"), "journal": str(TMP / "journal"), "state": "candidate"}
        rs.save(self.rdir, state)
        with patch("bt_run_isolated.bt_worktree.candidate",
                   side_effect=[isolated.bt_worktree.WorktreeError("candidate worktree missing"), "abc123"]), \
                patch("bt_run_isolated._integrate_one", return_value="accepted") as integrate:
            isolated.recover_recorded(self.project, self.rdir)
        saved = rs.load(self.rdir)
        self.assertEqual(saved["worktrees"]["T1"]["state"], "needs_attention")
        self.assertTrue(any("candidate worktree missing" in row.get("warning", "") for row in saved["log"]))
        integrate.assert_called_once()
        self.assertEqual(integrate.call_args.args[3]["task_id"], "T2")

    def test_conflicting_candidates_keep_the_rejected_branch(self):
        self.files({"T1": {"file": "shared.txt", "content": "one"},
                    "T2": {"file": "shared.txt", "content": "two"}})
        self.plan(["- [ ] T1 — first · repo: app · files: shared.txt",
                   "- [ ] T2 — second · repo: app · files: shared.txt"])
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=3, max_attempts=1), 2)
        state = rs.load(self.rdir)
        self.assertEqual(rs.get_task(state, "T1")["status"], "done")
        self.assertEqual(rs.get_task(state, "T2")["status"], "blocked")
        self.assertIn("integration:", rs.get_task(state, "T2")["last_error"])
        self.assertTrue(Path(state["worktrees"]["T2"]["worktree"]).exists())

    def test_default_same_repo_run_remains_serial(self):
        self.files({"T1": {"file": "a.txt"}, "T2": {"file": "b.txt"}})
        self.plan(["- [ ] T1 — first · repo: app", "- [ ] T2 — second · repo: app"])
        self.assertEqual(self.run_supervisor(workers=2, max_attempts=1), 0)
        task_rows = [row for row in self.records() if row["task"] != "FINAL"]
        self.assertEqual(len(task_rows), 2)
        self.assertGreaterEqual(task_rows[1]["time"], task_rows[0]["time"] + 0.2)

    def test_milestone_audits_and_final_run_on_recorded_throwaway_worktrees(self):
        self.files({"T1": {"file": "one.txt"}, "T2": {"file": "two.txt"}})
        self.plan(["### M1 — First", "- [ ] T1 — first · repo: app · files: one.txt · verify: `true`",
                   "### M2 — Second", "- [ ] T2 — second · repo: app · files: two.txt · verify: `true`"])
        verified_cwds = []
        original_verify = bt_runsettle.run_verify

        def record_verify(command, cwd):
            verified_cwds.append(Path(cwd).resolve())
            return original_verify(command, cwd)

        with patch("bt_runsettle.run_verify", side_effect=record_verify):
            self.assertEqual(self.run_supervisor(isolation="worktree", workers=1, audit=True), 0)
        state = rs.load(self.rdir)
        self.assertTrue(all(task["status"] == "done" for task in state["tasks"]))
        integration = Path(state["worktrees"]["__integration__:app"]["worktree"]).resolve()
        records = self.records()
        for label in ("M1-audit", "M2-audit", "FINAL"):
            row = next(row for row in records if row["task"] == label)
            self.assertNotEqual(Path(row["cwd"]).resolve(), integration)
            self.assertTrue(row["recorded"])
            if label.endswith("-audit"):
                self.assertIn(Path(row["cwd"]).resolve(), verified_cwds)
        self.assertEqual(len({row["cwd"] for row in records if row["task"] in ("M1-audit", "M2-audit", "FINAL")}), 3)
        self.assertTrue(all(rs.get_task(state, f"M{i}-audit")["status"] == "done" for i in (1, 2)))

    def test_invalid_scopes_serialize_and_warn_once(self):
        self.files({"T1": {"file": "x"}, "T2": {"file": "x"}, "T3": {"file": "x"}})
        self.plan([f"- [ ] T{i} — unsafe · repo: app · files: {value}"
                   for i, value in enumerate(("../x", ".", "/tmp/x"), 1)])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"workers": 3, "isolation": "worktree"})
        state = rs.sync_plan(state, self.rdir)
        self.assertEqual([task["files"] for task in state["tasks"]], [None, None, None])
        warnings = [entry for entry in state["log"] if entry.get("result") == "plan_warning"]
        self.assertEqual(len(warnings), 3)
        rs.sync_plan(state, self.rdir)
        self.assertEqual(len([entry for entry in state["log"] if entry.get("result") == "plan_warning"]), 3)
        self.assertEqual([[task["id"] for task in unit] for unit in rs.ready_units(state, 3)], [["T1"]])

    def test_resume_preserves_isolation_and_rejects_disabling_inflight_allocations(self):
        self.plan(["- [ ] T1 — task · repo: app · files: a.txt"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True,
                              {"isolation": "worktree"})
        rs.save(self.rdir, state)
        opened = bt_run._open(self.project, self.rdir, {})
        self.assertEqual(opened["limits"]["isolation"], "worktree")
        opened["worktrees"] = {"T1": {"state": "candidate"}}
        rs.save(self.rdir, opened)
        with self.assertRaisesRegex(SystemExit, "allocations are in flight"):
            bt_run._open(self.project, self.rdir, {"isolation": "off"})
        opened["worktrees"] = {"T1": {"state": "accepted"}, "__integration__": {"state": "allocated"}}
        rs.save(self.rdir, opened)
        self.assertEqual(bt_run._open(self.project, self.rdir, {"isolation": "off"})["limits"]["isolation"], "off")

    def test_zero_max_attempts_keeps_legacy_default(self):
        self.plan(["- [ ] T1 — task"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        rs.save(self.rdir, state)
        opened = bt_run._open(self.project, self.rdir, {"max_attempts": 0})
        self.assertEqual(opened["limits"]["max_attempts"], rs.DEFAULT_LIMITS["max_attempts"])

    def test_legacy_run_without_scope_keys_does_not_report_drift(self):
        self.plan(["- [ ] T1 — task · repo: app · files: a.txt · resources: cache"])
        state = rs.init_state(self.project, self.rdir, "claude", "haiku", True)
        state["tasks"][0].pop("files")
        state["tasks"][0].pop("resources")
        reopened = rs.sync_plan(state, self.rdir)
        self.assertEqual(reopened["plan_drift"], [])

    def test_repository_without_commits_fails_before_starting_a_session(self):
        empty_repo = TMP / f"empty{self.serial}"
        empty_repo.mkdir()
        self.git(empty_repo, "init", "-b", "main")
        bt_core.ensure_project(self.project + "empty")
        bt_core.register_repo(self.project + "empty", empty_repo, "app")
        self.project += "empty"
        self.rdir = bt_core.ROOT / self.project / "requirements" / "REQ-001-demo"
        self.rdir.mkdir(parents=True)
        (self.rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n- [ ] T1 — task · repo: app · files: a.txt\n")
        output = io.StringIO()
        with redirect_stdout(output):
            code = self.run_supervisor(isolation="worktree", workers=1)
        self.assertEqual(code, 1)
        self.assertIn("committed HEAD", output.getvalue())
        self.assertFalse(self.starts.exists())
        self.assertEqual(rs.load(self.rdir)["status"], "stopped")

    def test_sigkill_resume_recovers_allocated_worktree(self):
        self.files({"T1": {"file": "a.txt"}, "T2": {"file": "b.txt"}})
        self.plan(["- [ ] T1 — first · repo: app · files: a.txt", "- [ ] T2 — second · repo: app · files: b.txt"])
        os.environ["STUB_SLEEP"] = "5"
        code = (f"import sys; sys.path.insert(0, {str(SCRIPTS)!r}); import bt_run; "
                f"raise SystemExit(bt_run.supervise({self.project!r}, 'REQ-001', agent_cmd={self.cmd!r}, "
                "isolation='worktree', workers=2, no_autostart=True))")
        proc = subprocess.Popen([sys.executable, "-c", code], env=os.environ.copy(), stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        deadline = time.time() + 15
        while time.time() < deadline and not self.starts.exists():
            time.sleep(0.05)
        self.assertTrue(self.starts.exists(), "first session did not start")
        proc.kill()
        proc.wait(timeout=5)
        os.environ["STUB_SLEEP"] = "0.1"
        self.assertEqual(self.run_supervisor(isolation="worktree", workers=2), 0)
        state = rs.load(self.rdir)
        self.assertTrue(all(task["status"] == "done" for task in state["tasks"]))
        journal = Path(state["worktrees"]["T1"]["journal"]).read_text().splitlines()
        rows = [json.loads(line) for line in journal]
        self.assertEqual(sum(row.get("stage") == "accepted" and row.get("task_id") == "T1" for row in rows), 1)


if __name__ == "__main__":
    unittest.main()
