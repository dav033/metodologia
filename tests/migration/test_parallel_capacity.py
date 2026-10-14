"""Scheduling groups require path and shared-resource independence."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill" / "scripts"))
import bt_worktree as worktree  # noqa: E402


class ParallelCapacityTests(unittest.TestCase):
    def test_disjoint_scopes_share_a_group_and_sibling_prefixes_do_not_overlap(self) -> None:
        tasks = [{"id": "one", "scopes": ["src/app"]}, {"id": "two", "scopes": ["src/application"]},
                 {"id": "three", "scopes": ["docs"]}]
        groups = worktree.parallel_capacity(tasks, max_workers=3)
        self.assertEqual([[task["id"] for task in group] for group in groups], [["one", "two", "three"]])

    def test_shared_resources_and_overlapping_scopes_separate_groups(self) -> None:
        tasks = [{"id": "lock", "scopes": ["a"], "resources": ["lockfile"]},
                 {"id": "gen", "scopes": ["b"], "resources": ["lockfile"]},
                 {"id": "overlap", "scopes": ["a/sub"]}]
        groups = worktree.parallel_capacity(tasks, max_workers=3)
        self.assertEqual([[task["id"] for task in group] for group in groups], [["lock"], ["gen", "overlap"]])

    def test_missing_scope_serializes_and_max_workers_is_respected(self) -> None:
        tasks = [{"id": str(i), "scopes": [f"path/{i}"]} for i in range(5)] + [{"id": "unknown"}]
        groups = worktree.parallel_capacity(tasks, max_workers=2)
        self.assertEqual([len(group) for group in groups], [2, 2, 1, 1])
        self.assertEqual(groups[-1][0]["id"], "unknown")

    def test_serial_fallback_is_one_task_per_group(self) -> None:
        tasks = [{"id": "a", "scopes": ["a"]}, {"id": "b", "scopes": ["b"]}]
        self.assertEqual(worktree.parallel_capacity(tasks, max_workers=8, serial=True), [[tasks[0]], [tasks[1]]])

    def test_default_shared_paths_create_implicit_resource_conflicts(self) -> None:
        tasks = [{"id": "one", "scopes": ["a"], "paths": ["package-lock.json"]},
                 {"id": "two", "scopes": ["b"], "paths": ["src/file"]},
                 {"id": "three", "scopes": ["c"], "paths": ["dist/app.js"]}]
        groups = worktree.parallel_capacity(tasks, max_workers=3)
        self.assertEqual([[task["id"] for task in group] for group in groups], [["one", "two"], ["three"]])


if __name__ == "__main__":
    unittest.main()
