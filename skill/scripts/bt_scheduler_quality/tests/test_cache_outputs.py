"""The pass cache key leaves out the report files a test/audit task itself writes (REQ-020 T14a paid a 10-minute suite at every attempt)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality import reuse
from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.store import QualityStore
from test_reuse import Runner, order
from test_snapshot import _make_snapshot

REPORT = "docs/req-020/results.json"


class OwnOutputs(unittest.TestCase):
    def test_only_report_files_of_test_and_audit_tasks_are_left_out(self):
        paths = [REPORT, "docs/notes.md", "src/app.ts", "reports/*.json", "docs/dir/"]
        self.assertEqual(reuse.own_outputs("test", paths), ("docs/notes.md", REPORT))
        self.assertEqual(reuse.own_outputs("audit", [REPORT]), (REPORT,))
        self.assertEqual(reuse.own_outputs("implement", paths), ())                     # the code under check is never ignored
        self.assertEqual(reuse.own_outputs("docs", paths), ())
        self.assertEqual(reuse.own_outputs(None, paths), ())


class Engine(unittest.TestCase):
    def snapshots(self, tmp):
        first = _make_snapshot(Path(tmp) / "a", files={REPORT: "attempt 1\n"}) if (Path(tmp) / "a").mkdir() is None else None
        second = _make_snapshot(Path(tmp) / "b", files={REPORT: "attempt 2, another report\n"}) if (Path(tmp) / "b").mkdir() is None else None
        return first[1], second[1]

    def verify(self, policy=None, commands=("python3 -m unittest -q",)):
        with tempfile.TemporaryDirectory() as tmp, QualityStore(":memory:") as store:
            one, two = self.snapshots(tmp)
            runner = Runner()
            engine = QualityEngine(policy or QualityPolicy(), store, runner=runner, own_outputs=lambda _order: (REPORT,))
            engine.verify(order("att-1", *commands), one)
            engine.verify(order("att-2", *commands), two)
            return runner.calls

    def test_a_retry_that_only_rewrote_the_report_reuses_the_pass(self):
        self.assertEqual(self.verify(), ["python3 -m unittest -q"])                      # ran once, not twice

    def test_a_check_that_names_the_report_reads_it_so_it_runs_again(self):
        reads = f"python3 check.py {REPORT}"
        self.assertEqual(self.verify(commands=("python3 -m unittest -q", reads)),
                         ["python3 -m unittest -q", reads, reads])

    def test_the_switch_restores_the_whole_tree_key(self):
        self.assertEqual(len(self.verify(QualityPolicy(cache_ignores_outputs=False))), 2)

    def test_the_trees_are_equal_without_the_report_and_different_with_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a").mkdir()
            (Path(tmp) / "b").mkdir()
            _, one, _, _ = _make_snapshot(Path(tmp) / "a", files={REPORT: "1\n"})
            _, two, _, _ = _make_snapshot(Path(tmp) / "b", files={REPORT: "2\n"})
            for side in ("a", "b"):                                                       # the live worktree moved on: neither HEAD nor the
                (Path(tmp) / side / "repo" / REPORT).write_text("edited since the snapshot\n")   # snapshot matches it (what `git rm --cached` refused)
            whole = [reuse.tree_id(s.repository, s.snapshot_sha) for s in (one, two)]
            pruned = [reuse.tree_id(s.repository, s.snapshot_sha, (REPORT,)) for s in (one, two)]
        self.assertNotEqual(whole[0], whole[1])
        self.assertEqual(pruned[0], pruned[1])


if __name__ == "__main__":
    unittest.main()
