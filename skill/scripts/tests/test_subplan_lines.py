"""M3's subplan line isolation and redo semantics, using real Git objects."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_integration_line
import scheduler_executor_support as support
from scheduler_executor_support import git
from test_scheduler_integrator import snapshot


class Plan:
    schema_version = "1.3.0"
    generated_paths = ()
    subplans = (SimpleNamespace(id="SP-1"), SimpleNamespace(id="SP-2"))

    def __init__(self):
        self.tasks = tuple(SimpleNamespace(id=tid, after=tuple(after), repository="app", meta=meta,
                                           expected_paths=())
                           for tid, after, meta in (
                               ("T1", (), {"subplan_id": "SP-1"}),
                               ("T2", ("T1",), {"subplan_id": "SP-1"}),
                               ("T3", (), {"subplan_id": "SP-2"}),
                               ("T4", (), {})))
        self.by_id = {task.id: task for task in self.tasks}

    def task(self, task_id):
        return self.by_id[task_id]

    def ids(self):
        return tuple(task.id for task in self.tasks)

    def ancestors(self, task_id):
        found, stack = set(), list(self.task(task_id).after)
        while stack:
            current = stack.pop()
            if current not in found:
                found.add(current)
                stack.extend(self.task(current).after)
        return frozenset(found)


class SubplanLines(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = support.make_repo(Path(self.tmp.name) / "app")
        self.base = git(self.repo, "rev-parse", "HEAD")
        self.plan = Plan()
        self.accepted = {}
        self.snapshots = {}
        self.router = bt_integration_line.SubplanLineRouter(
            plan=self.plan, accepted=lambda: dict(self.accepted),
            snapshot_of=lambda attempt: self.snapshots.get(attempt),
            repo_of=lambda role: self.repo if role == "app" else None,
            default_repository="app", identity="run-1", base_of=lambda role: self.base)

    def accept(self, task, commit, attempt=None):
        attempt = attempt or f"att-{task}"
        self.accepted[task] = attempt
        self.snapshots[attempt] = commit

    def test_independent_subplans_and_unassigned_work_never_leak_and_refs_are_scoped(self):
        self.accept("T1", snapshot(self.repo, self.base, {"one.txt": "one\n"}))
        self.accept("T3", snapshot(self.repo, self.base, {"two.txt": "two\n"}))
        self.accept("T4", snapshot(self.repo, self.base, {"unrelated.txt": "unrelated\n"}))
        sp1 = self.router.tip("app", without="T2")
        self.assertEqual(git(self.repo, "show", f"{sp1}:one.txt"), "one")
        paths = git(self.repo, "ls-tree", "-r", "--name-only", sp1).splitlines()
        self.assertNotIn("two.txt", paths)
        self.assertNotIn("unrelated.txt", paths)
        self.assertEqual(self.router.lines["SP-1"].ref("app"), "refs/m3/line/run-1/app/SP-1")
        self.assertEqual(self.router.lines["SP-2"].ref("app"), "refs/m3/line/run-1/app/SP-2")

    def test_redo_replaces_only_its_delta_and_keeps_accepted_sibling_work(self):
        first = snapshot(self.repo, self.base, {"one.txt": "old\n"})
        sibling = snapshot(self.repo, first, {"two.txt": "sibling\n"})
        self.accept("T1", first)
        self.accept("T2", sibling)
        replacement = snapshot(self.repo, self.base, {"one.txt": "new\n"})
        self.accept("T1", replacement, "att-T1-2")
        tip = self.router.lines["SP-1"].tip("app")
        self.assertEqual(git(self.repo, "show", f"{tip}:one.txt"), "new")
        self.assertEqual(git(self.repo, "show", f"{tip}:two.txt"), "sibling")

    def test_real_conflict_stays_explicit_in_its_subplan_scope(self):
        self.accept("T1", snapshot(self.repo, self.base, {"README.md": "first\n"}))
        self.accept("T2", snapshot(self.repo, self.base, {"README.md": "second\n"}))
        self.accept("T3", snapshot(self.repo, self.base, {"README.md": "other subplan\n"}))
        conflicts = self.router.needs_resolution("app", "T1")
        self.assertEqual(conflicts, {"T2": ("README.md",)})

    def test_accepted_ancestor_of_a_subplan_member_is_in_scope(self):
        self.accept("T1", snapshot(self.repo, self.base, {"ancestor.txt": "accepted\n"}))
        subplan_one = self.router.lines["SP-1"]
        self.assertEqual(git(self.repo, "show", f"{subplan_one.tip('app')}:ancestor.txt"), "accepted")


if __name__ == "__main__":
    unittest.main()
