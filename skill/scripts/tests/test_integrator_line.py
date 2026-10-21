"""REQ-028: PredecessorIntegrator with the integration line attached (gates.integration_line on)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_integration_line as line_mod
import bt_scheduler_integrator as integ
import scheduler_executor_support as s
from scheduler_executor_support import git
import test_scheduler_integrator as base_tests
from test_scheduler_integrator import snapshot
from unittest import mock

SPEC = {"T1": ([], "app"), "T2": (["T1"], "app"), "T3": ([], "app"), "T4": (["T2"], "app")}


class WithLine(base_tests.Unit):
    def lined(self, spec=SPEC, repo_of=None):
        integrator = self.bound(spec)
        integrator.attach_line(line_mod.Line(
            plan=integrator._bound["plan"], accepted=lambda: dict(self.accepted), snapshot_of=lambda a: self.snaps.get(a),
            repo_of=repo_of or (lambda role: {"app": self.app}.get(role)), default_repository="app", identity="r1-abc-1"))
        return integrator

    def test_base_ref_is_the_tip_and_includes_parallel_tasks_and_moves_the_ref(self):
        s1 = snapshot(self.app, self.head, {"one.txt": "1\n"})
        self.accept("T1", s1)
        self.accept("T3", snapshot(self.app, self.head, {"three.txt": "3\n"}))
        i = self.lined()
        base = i.base_ref("T2")
        for name in ("one.txt", "three.txt"):
            git(self.app, "cat-file", "-e", f"{base}:{name}")
        self.assertEqual(git(self.app, "rev-parse", "refs/m3/line/r1-abc-1/app"), base)

    def test_a_redo_starts_from_the_tip_without_its_own_earlier_result(self):
        self.accept("T1", snapshot(self.app, self.head, {"one.txt": "1\n"}))
        s2 = snapshot(self.app, self.head, {"two.txt": "old\n"})
        self.accept("T2", s2)
        base = self.lined().base_ref("T2")
        git(self.app, "cat-file", "-e", f"{base}:one.txt")
        self.assertEqual(subprocess_exists(self.app, base, "two.txt"), False)

    def test_a_new_result_is_checked_against_the_tip_not_only_its_predecessors(self):
        self.accept("T1", snapshot(self.app, self.head, {"README.md": "left\n"}))
        i = self.lined()
        clash = i.would_conflict("T3", "att-T3", snapshot(self.app, self.head, {"README.md": "right\n"}))
        self.assertTrue(clash.startswith("T3 vs line for T3"), clash)
        self.assertIn("README.md", clash)
        self.assertEqual(i.would_conflict("T3", "att-T3", snapshot(self.app, self.head, {"other.txt": "x\n"})), "")

    def test_a_task_waits_when_a_prerequisite_is_accepted_but_does_not_fit(self):
        self.accept("T3", snapshot(self.app, self.head, {"README.md": "left\n"}))
        self.accept("T1", snapshot(self.app, self.head, {"README.md": "right\n"}))
        i = self.lined({"T3": ([], "app"), "T1": ([], "app"), "T2": (["T1"], "app")})      # T3 comes first in plan order
        with self.assertRaises(integ.IntegrationError) as caught:
            i.base_ref("T2")
        self.assertEqual(caught.exception.code, "PREDECESSOR_NEEDS_RESOLUTION")
        self.assertFalse(caught.exception.permanent)          # it waits; it does not burn an attempt

    def test_an_unaccepted_prerequisite_is_still_stated(self):
        with self.assertRaises(integ.IntegrationError) as caught:
            self.lined().base_ref("T2")
        self.assertEqual(caught.exception.code, "PREDECESSOR_NOT_ACCEPTED")

    def test_when_the_line_cannot_be_computed_the_predecessor_merge_answers(self):
        s1 = snapshot(self.app, self.head, {"one.txt": "1\n"})
        self.accept("T1", s1)
        i = self.lined(repo_of=lambda role: self.app.parent / "gone")
        self.assertEqual(i.base_ref("T2"), s1)                               # the old behaviour, not an error
        self.assertEqual(i.would_conflict("T3", "att-T3", snapshot(self.app, self.head, {"x.txt": "x\n"})), "")
        i.recompute_line()                                                   # never raises


class ThroughLine(base_tests.Through):
    def test_with_the_flag_on_a_dependent_starts_from_the_tip_and_the_ref_exists(self):
        import bt_config
        real = bt_config.get
        flag = lambda key, default=None: True if key == "gates.integration_line" else real(key, default)   # noqa: E731
        self.approve([s.task("T1", "first"), s.task("T2", "second", after=["T1"])])
        with mock.patch.object(bt_config, "get", flag):
            w = self.wire("direct:claude/haiku")
            self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90), w.scheduler.snapshot())
        repo = self.repos["app"]
        t1, t2 = self.attempt_of(w, "T1"), self.attempt_of(w, "T2")
        self.assertEqual(t2["workspace"]["base_sha"], t1["handoff"]["snapshot_sha"])
        refs = git(repo, "for-each-ref", "refs/m3/line/")
        self.assertIn("/app", refs)
        self.assertEqual(git(repo, "status", "--porcelain"), "")


def subprocess_exists(repo, ref, name) -> bool:
    import subprocess
    return subprocess.run(["git", "cat-file", "-e", f"{ref}:{name}"], cwd=str(repo), capture_output=True).returncode == 0


if __name__ == "__main__":
    unittest.main()
