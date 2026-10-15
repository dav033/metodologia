"""T12: parallel attempts never share a directory, branch, index or output; bounded and ordered under load."""
from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor import model as m
from support import World, git, order


class Isolation(unittest.TestCase):
    def cfg(self, running=4):
        return ex.Config(poll_seconds=0.02, max_running=running, grace_seconds=1, timeout_seconds=60)

    def test_eight_parallel_attempts_on_one_repository_stay_apart(self):
        w = World(self, config=self.cfg(8))
        for n in range(1, 9):
            w.x.start(order(n, f"marker:M{n}"))
        self.assertTrue(w.x.wait_idle(60))
        paths, branches = set(), set()
        for n in range(1, 9):
            d = w.x.describe(f"att-{n:04d}")
            self.assertEqual(d["state"], "finished", d)
            wt = Path(d["handoff"]["worktree"])
            paths.add(str(wt))
            branches.add(d["handoff"]["branch"])
            self.assertEqual((wt / "marker.txt").read_text().strip(), f"M{n}")
            self.assertEqual([p.name for p in wt.glob("marker*.txt")], ["marker.txt"])
            out = Path(d["artifacts"]["output"]).read_text()
            self.assertIn(f"MARKER=M{n}", out)
            self.assertEqual(out.count("MARKER="), 1, "another attempt's output leaked in")
            files = git(w.repo, "ls-tree", "-r", "--name-only", d["handoff"]["snapshot_sha"]).splitlines()
            self.assertEqual(sorted(set(files) - {"README.md", "src.txt"}), ["marker.txt"])
        self.assertEqual((len(paths), len(branches)), (8, 8))

    def test_the_main_branch_and_checkout_are_untouched_by_a_parallel_run(self):
        w = World(self, config=self.cfg(4))
        head = git(w.repo, "rev-parse", "main")
        status = git(w.repo, "status", "--porcelain")
        for n in range(1, 7):
            w.x.start(order(n, "both"))
        self.assertTrue(w.x.wait_idle(60))
        self.assertEqual(git(w.repo, "rev-parse", "main"), head)
        self.assertEqual(git(w.repo, "status", "--porcelain"), status)
        names = {w.x.describe(f"att-{n:04d}")["handoff"]["branch"] for n in range(1, 7)}
        self.assertEqual(len(names), 6)
        for name in names:                       # every branch is its own ref, one commit above the same base
            self.assertEqual(git(w.repo, "rev-list", "--count", f"main..{name}"), "1")
        for n in range(1, 7):
            d = w.x.describe(f"att-{n:04d}")
            self.assertEqual(d["handoff"]["commit_count"], 1)
            self.assertTrue(d["handoff"]["dirty"])

    def test_attempts_on_different_repositories_run_together_and_do_not_mix(self):
        w = World(self, repos=3, config=self.cfg(6))
        roles = ["main", "repo1", "repo2"]
        for n in range(1, 7):
            w.x.start(order(n, f"marker:R{n}", repo=roles[n % 3]))
        self.assertTrue(w.x.wait_idle(60))
        for n in range(1, 7):
            d = w.x.describe(f"att-{n:04d}")
            self.assertEqual(d["state"], "finished")
            repo = w.repos[roles[n % 3]]
            self.assertIn(f"m3/att-{n:04d}", git(repo, "branch", "--list", "m3/*"))
            for other in w.repos.values():
                if other != repo:
                    self.assertNotIn(f"m3/att-{n:04d}", git(other, "branch", "--list", "m3/*"))

    def test_a_burst_of_thirty_orders_respects_the_ceiling_and_every_one_finishes_once(self):
        w = World(self, config=self.cfg(4))
        for n in range(1, 31):
            w.x.start(order(n, "marker:b"))
        peak = 0
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline and w.x.ledger.count(m.TERMINAL) < 30:
            peak = max(peak, w.x.ledger.count((m.PREPARING, m.RUNNING)))
            time.sleep(0.01)
        self.assertTrue(w.x.wait_idle(60))
        self.assertLessEqual(peak, 4)
        self.assertEqual(w.x.ledger.count((m.FINISHED,)), 30,
                         [(r["attempt_id"], r["state"], (r.get("outcome") or {}).get("cause"), (r.get("outcome") or {}).get("detail"), (r.get("outcome") or {}).get("exit"))
                          for r in w.x.ledger.in_states(m.TERMINAL) if r["state"] != m.FINISHED])
        started = [e.attempt_id for e in w.sink.events if e.kind == m.EV_STARTED]
        self.assertEqual(len(started), len(set(started)), "an attempt started twice")

    def test_a_failure_in_one_attempt_does_not_disturb_its_neighbours(self):
        w = World(self, config=self.cfg(4))
        scenarios = ["ok", "crash", "quota", "net", "commit", "partial", "dirty", "sleep:0.3"]
        for n, s in enumerate(scenarios, 1):
            w.x.start(order(n, s))
        self.assertTrue(w.x.wait_idle(60))
        got = {n: w.x.ledger.get(f"att-{n:04d}")["outcome"]["cause"] for n in range(1, 9)}
        self.assertEqual(got, {1: "clean", 2: "agent_error", 3: "quota_exhausted", 4: "connection_lost", 5: "clean",
                               6: "incomplete_output", 7: "clean", 8: "clean"})

    def test_two_executors_cannot_serve_the_same_root(self):
        w = World(self, autostart=False)
        with self.assertRaises(ex.ExecutorError) as caught:
            w.build()
        self.assertEqual(caught.exception.code, "ROOT_BUSY")
        w.x.close()
        w.build().close()                      # once the first one is closed the root is free again


if __name__ == "__main__":
    unittest.main()
