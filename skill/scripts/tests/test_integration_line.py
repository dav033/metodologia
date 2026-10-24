"""REQ-028: the integration line. Real git objects in temp repositories (no worktrees, no network)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_integration_line as line_mod
import bt_scheduler_integrator as integ
import scheduler_executor_support as s
from scheduler_executor_support import git
from scheduler_generated_case import delete_snapshot
from test_scheduler_integrator import FakePlan, snapshot

V1, V2, V3 = ("".join(f"line {i} v{v}\n" for i in range(5)) for v in (1, 2, 3))


class LineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = s.make_repo(Path(self.tmp.name) / "app")
        self.head = git(self.app, "rev-parse", "HEAD")
        self.accepted: dict[str, str] = {}
        self.snaps: dict[str, str | None] = {}
        self.repos = {"app": self.app}

    def line(self, spec, **extra):
        return line_mod.Line(plan=FakePlan(spec), accepted=lambda: dict(self.accepted), snapshot_of=lambda a: self.snaps.get(a),
                             repo_of=lambda role: self.repos.get(role), default_repository="app", identity="r1-abc-1", **extra)

    def accept(self, tid, sha, attempt=None):
        attempt = attempt or f"att-{tid}"
        self.accepted[tid] = attempt
        self.snaps[attempt] = sha

    def at(self, ref, name):
        return git(self.app, "show", f"{ref}:{name}")

    def tip_text(self, line, name):
        return self.at(line.tip("app"), name) + "\n"


class Basics(LineCase):
    def test_declared_generated_conflicts_keep_last_writer_and_mark_stale(self):
        names = ("registry.json", "registry/app/registry.json", "catalog/resolved.ts")
        self.accept("T1", snapshot(self.app, self.head, {**dict.fromkeys(names, "left\n"), "a.txt": "a\n"}))
        candidate = snapshot(self.app, self.head, {**dict.fromkeys(names, "right\n"), "b.txt": "b\n"})
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        line.plan.generated_paths = ("registry.json", "registry/**/registry.json", "catalog/resolved.ts")
        preview = line.apply("app", "T2", "att-T2", candidate)
        tip, conflicts = preview
        self.assertEqual(conflicts, ())
        self.assertEqual(set(preview.generated_stale), set(names))
        self.assertEqual(self.at(tip, "registry.json"), "right")
        self.accept("T2", candidate)
        state = line.recompute()["app"]
        self.assertEqual(state.applied, ("T1", "T2"))
        self.assertEqual(set(state.generated_stale), set(names))
        self.assertEqual(line.needs_resolution("app"), {})
        for name in names:
            self.assertEqual(self.at(state.tip, name), "right")
        for name in ("a.txt", "b.txt"):
            git(self.app, "cat-file", "-e", f"{state.tip}:{name}")
        self.assertEqual(line.recompute()["app"], state)
        fresh = self.line({"T1": ([], "app"), "T2": ([], "app"), "T3": ([], "app")})
        fresh.plan.generated_paths = line.plan.generated_paths
        self.assertEqual(fresh.state("app"), state)
        clean = snapshot(self.app, state.tip, {"c.txt": "c\n"})
        self.assertEqual(set(fresh.apply("app", "T3", "att-T3", clean).generated_stale), set(names))

    def test_generated_deletion_takes_candidate_and_is_not_restored_by_the_guard(self):
        base = snapshot(self.app, self.head, {"registry.json": "base\n"})
        self.accept("T1", snapshot(self.app, base, {"registry.json": "left\n", "a.txt": "a\n"}))
        candidate = delete_snapshot(self.app, base, "registry.json")
        self.accept("T2", candidate)
        line = self.line({"T1": ([], "app"), "T2": ([], "app")}, base_of=lambda role: base)
        line.plan.generated_paths = ("registry.json",)
        state = line.state("app")
        self.assertEqual(state.unresolved, {})
        self.assertEqual(state.generated_stale, ("registry.json",))
        self.assertNotIn("registry.json", git(self.app, "ls-tree", "--name-only", state.tip).splitlines())
        self.assertEqual(self.at(state.tip, "a.txt"), "a")

    def test_generated_paths_are_literal_and_resolution_does_not_touch_the_checkout(self):
        name = "catalog/with\tquote\".ts"
        self.accept("T1", snapshot(self.app, self.head, {name: "left\n"}))
        self.accept("T2", snapshot(self.app, self.head, {name: "right\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        line.plan.generated_paths = ("catalog/*",)
        (self.app / "local.txt").write_text("uncommitted\n")
        before = git(self.app, "status", "--porcelain")
        state = line.recompute()["app"]
        self.assertEqual(self.at(state.tip, name), "right")
        self.assertEqual(state.generated_stale, (name,))
        self.assertEqual(git(self.app, "status", "--porcelain"), before)

    def test_mixed_conflicts_report_only_sources_and_do_not_advance(self):
        self.accept("T1", snapshot(self.app, self.head, {"registry.json": "left\n", "README.md": "left\n"}))
        candidate = snapshot(self.app, self.head, {"registry.json": "right\n", "README.md": "right\n"})
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        line.plan.generated_paths = ("registry.json",)
        before = line.tip("app")
        result = line.apply("app", "T2", "att-T2", candidate)
        self.assertEqual(tuple(result), (before, ("README.md",)))
        self.assertEqual(result.generated_stale, ())
        self.accept("T2", candidate)
        self.assertEqual(line.needs_resolution("app"), {"T2": ("README.md",)})

    def test_undeclared_generated_file_still_clashes(self):
        self.accept("T1", snapshot(self.app, self.head, {"registry.json": "left\n"}))
        self.accept("T2", snapshot(self.app, self.head, {"registry.json": "right\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        self.assertEqual(line.needs_resolution("app"), {"T2": ("registry.json",)})

    def test_nothing_accepted_the_tip_is_the_run_base(self):
        line = self.line({"T1": ([], "app")})
        self.assertEqual(line.tip("app"), self.head)
        self.assertEqual(line.needs_resolution("app"), {})
        self.assertEqual(line.ref("app"), "refs/m3/line/r1-abc-1/app")

    def test_two_parallel_tasks_on_different_files_both_reach_the_tip(self):
        self.accept("T1", snapshot(self.app, self.head, {"a.txt": "a\n"}))
        self.accept("T2", snapshot(self.app, self.head, {"b.txt": "b\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        for name in ("a.txt", "b.txt", "README.md"):
            git(self.app, "cat-file", "-e", f"{line.tip('app')}:{name}")
        self.assertEqual(line.state("app").applied, ("T1", "T2"))

    def test_two_parallel_tasks_editing_the_same_lines_the_second_needs_resolution(self):
        self.accept("T1", snapshot(self.app, self.head, {"README.md": "left\n"}))
        self.accept("T2", snapshot(self.app, self.head, {"README.md": "right\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        self.assertEqual(self.tip_text(line, "README.md"), "left\n")
        self.assertEqual(line.needs_resolution("app"), {"T2": ("README.md",)})
        self.assertEqual(line.state("app").applied, ("T1",))

    def test_a_snapshot_that_already_holds_the_tip_fast_forwards_even_when_its_start_base_is_not_in_the_tip(self):
        """david-ui REQ-001 T1 att-0004: its snapshot continued from att-0003's, a commit the tip never held. Merged against THAT base the
        tip read as 'deleted everything' and the line commit had an EMPTY tree: T2 and T6 then clashed add/add on every file."""
        first = snapshot(self.app, self.head, {"a.txt": "a\n", "b.txt": "b\n", "c.txt": "c\n"})        # the rejected attempt
        retry = snapshot(self.app, first, {"a.txt": "a2\n"})                                              # carries it, changes one file
        self.accept("T1", retry)
        line = self.line({"T1": ([], "app")})
        self.assertEqual(self.tip_text(line, "a.txt"), "a2\n")
        for name in ("b.txt", "c.txt", "README.md"):
            git(self.app, "cat-file", "-e", f"{line.tip('app')}:{name}")
        self.assertEqual(line.needs_resolution("app"), {})

    def test_attempts_started_from_a_line_commit_with_an_empty_tree_are_read_against_the_parent_that_has_the_files(self):
        """The poisoned `m3 line: T1` of david-ui REQ-001 (empty tree): T2 and T6 started from it and then clashed add/add on every file."""
        t1 = snapshot(self.app, self.head, {"a.txt": "a\n", "package.json": "{}\n"})
        import subprocess

        tree = subprocess.run(["git", "mktree"], cwd=self.app, input=b"", check=True, capture_output=True).stdout.decode().strip()
        empty = git(self.app, "commit-tree", tree, "-p", self.head, "-p", t1, "-m", "m3 line: T1")
        t6 = snapshot(self.app, empty, {"a.txt": "a\n", "package.json": '{"x":1}\n', "six.txt": "6\n"})
        t2 = snapshot(self.app, empty, {"a.txt": "a\n", "package.json": "{}\n", "two.txt": "2\n"})
        self.accept("T1", t1)
        self.accept("T6", t6)
        self.accept("T2", t2)
        line = self.line({"T1": ([], "app"), "T6": (["T1"], "app"), "T2": (["T1"], "app")})
        self.assertEqual(line.needs_resolution("app"), {})
        for name in ("a.txt", "six.txt", "two.txt"):
            git(self.app, "cat-file", "-e", f"{line.tip('app')}:{name}")
        self.assertEqual(self.at(line.tip("app"), "package.json"), '{"x":1}')

    def test_an_empty_handoff_is_a_no_op(self):
        self.accept("T1", self.head)
        self.assertEqual(self.line({"T1": ([], "app")}).tip("app"), self.head)

    def test_an_accepted_task_without_a_snapshot_is_an_error_not_a_skip(self):
        self.accept("T1", None)
        with self.assertRaises(integ.IntegrationError) as caught:
            self.line({"T1": ([], "app")}).tip("app")
        self.assertEqual(caught.exception.code, "PREDECESSOR_HANDOFF_MISSING")

    def test_the_run_base_is_pinned_even_when_head_moves(self):
        line = self.line({"T1": ([], "app")})
        self.assertEqual(line.tip("app"), self.head)
        (self.app / "later.txt").write_text("x\n")
        git(self.app, "add", "-A")
        git(self.app, "commit", "-q", "-m", "later")
        self.assertEqual(self.line({"T1": ([], "app")}).tip("app"), self.head)

    def test_roles_are_independent_lines(self):
        self.repos["docs"] = s.make_repo(Path(self.tmp.name) / "docs")
        docs_head = git(self.repos["docs"], "rev-parse", "HEAD")
        self.accept("T1", snapshot(self.app, self.head, {"a.txt": "a\n"}))
        self.accept("T2", snapshot(self.repos["docs"], docs_head, {"d.txt": "d\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "docs")})
        self.assertEqual(line.roles(), ["app", "docs"])
        git(self.app, "cat-file", "-e", f"{line.tip('app')}:a.txt")
        git(self.repos["docs"], "cat-file", "-e", f"{line.tip('docs')}:d.txt")


class Redo(LineCase):
    SPEC = {"T8a": ([], "app"), "T9": (["T8a"], "app"), "T14": ([], "app"), "T15f": (["T8a"], "app"),
            "T16": (["T9", "T14", "T15f"], "app")}

    def v(self, text, name="edit.py"):
        return {name: text}

    def test_the_measured_failure_a_redone_fix_reaches_the_tip_never_the_old_text(self):
        base = snapshot(self.app, self.head, self.v(V1))
        t8a_v2 = snapshot(self.app, base, self.v(V2))
        self.accept("T8a", t8a_v2)
        self.accept("T9", snapshot(self.app, t8a_v2, {"nine.py": "9\n"}))        # built on the old fix
        self.accept("T14", snapshot(self.app, base, {"fourteen.py": "14\n"}))
        self.accept("T15f", snapshot(self.app, t8a_v2, {"fifteen.py": "15\n"}))  # its snapshot carries v2
        line = self.line(self.SPEC, base_of=lambda role: base)
        self.assertEqual(self.tip_text(line, "edit.py"), V2)

        t8a_v3 = snapshot(self.app, base, self.v(V3))                             # the audit sent T8a back
        self.accept("T8a", t8a_v3, "att-T8a-3")
        self.accept("T9", snapshot(self.app, t8a_v3, {"nine.py": "9\n"}), "att-T9-2")   # T9 rebuilt on v3
        # T15f was NOT rebuilt: it still carries v2, and the tip must nevertheless be v3
        state = self.line(self.SPEC, base_of=lambda role: base).state("app")
        self.assertEqual(self.at(state.tip, "edit.py") + "\n", V3)
        self.assertEqual(state.unresolved, {})
        for name in ("nine.py", "fourteen.py", "fifteen.py"):
            git(self.app, "cat-file", "-e", f"{state.tip}:{name}")

    def test_the_stale_dependent_that_touches_the_fixed_lines_is_made_visible_not_silent(self):
        base = snapshot(self.app, self.head, self.v(V1))
        t8a_v2 = snapshot(self.app, base, self.v(V2))
        self.accept("T8a", t8a_v2)
        self.accept("T15f", snapshot(self.app, t8a_v2, self.v(V2.replace("line 2 v2", "line 2 mine"))))
        line = self.line(self.SPEC, base_of=lambda role: base)
        self.assertEqual(line.needs_resolution("app"), {})
        self.accept("T8a", snapshot(self.app, base, self.v(V3)), "att-T8a-3")
        state = self.line(self.SPEC, base_of=lambda role: base).state("app")
        self.assertEqual(state.unresolved, {"T15f": ("edit.py",)})
        self.assertEqual(self.at(state.tip, "edit.py") + "\n", V3)                # never silently v2

    def test_redo_of_a_middle_task_drops_its_old_contribution(self):
        spec = {"T1": ([], "app"), "T2": (["T1"], "app"), "T3": (["T2"], "app")}
        s1 = snapshot(self.app, self.head, {"one.txt": "1\n"})
        s2 = snapshot(self.app, s1, {"two.txt": "old\n"})
        s3 = snapshot(self.app, s2, {"three.txt": "3\n"})
        for tid, sha in (("T1", s1), ("T2", s2), ("T3", s3)):
            self.accept(tid, sha)
        self.assertEqual(self.tip_text(self.line(spec), "two.txt"), "old\n")
        del self.accepted["T2"]                                                    # reworked: not accepted any more
        tip = self.line(spec).state("app")
        self.assertEqual(tip.applied, ("T1", "T3"))
        self.accept("T2", snapshot(self.app, s1, {"two.txt": "new\n"}), "att-T2-2")
        self.assertEqual(self.tip_text(self.line(spec), "two.txt"), "new\n")

    def test_apply_previews_a_candidate_and_reports_its_clash_without_moving_anything(self):
        self.accept("T1", snapshot(self.app, self.head, {"README.md": "left\n"}))
        line = self.line({"T1": ([], "app"), "T2": ([], "app")})
        line.recompute()
        ref_before = git(self.app, "rev-parse", line.ref("app"))
        clean, none = line.apply("app", "T2", "att-T2", snapshot(self.app, self.head, {"b.txt": "b\n"}))
        self.assertEqual(none, ())
        git(self.app, "cat-file", "-e", f"{clean}:b.txt")
        _, conflicts = line.apply("app", "T2", "att-T2", snapshot(self.app, self.head, {"README.md": "right\n"}))
        self.assertEqual(conflicts, ("README.md",))
        self.assertEqual(git(self.app, "rev-parse", line.ref("app")), ref_before)

    def test_apply_replaces_the_tasks_own_earlier_contribution(self):
        self.accept("T1", snapshot(self.app, self.head, {"README.md": "old\n"}))
        line = self.line({"T1": ([], "app")})
        new = snapshot(self.app, self.head, {"README.md": "new\n"})
        merged, conflicts = line.apply("app", "T1", "att-T1-2", new)
        self.assertEqual((conflicts, git(self.app, "show", f"{merged}:README.md")), ((), "new"))


class Persistence(LineCase):
    SPEC = {"T1": ([], "app"), "T2": ([], "app")}

    def seed(self):
        self.accept("T1", snapshot(self.app, self.head, {"a.txt": "a\n"}))
        self.accept("T2", snapshot(self.app, self.head, {"b.txt": "b\n"}))

    def test_recompute_is_idempotent_and_matches_a_fresh_instance(self):
        self.seed()
        first = self.line(self.SPEC)
        tip = first.recompute()["app"].tip
        self.assertEqual(git(self.app, "rev-parse", first.ref("app")), tip)
        self.assertEqual(first.recompute()["app"].tip, tip)
        self.assertEqual(self.line(self.SPEC).recompute()["app"].tip, tip)

    def test_a_crash_between_the_objects_and_the_ref_leaves_the_old_tip(self):
        self.seed()
        line = self.line(self.SPEC)
        old = line.recompute()["app"].tip
        self.accept("T1", snapshot(self.app, self.head, {"a.txt": "a2\n"}), "att-T1-2")
        crashing = self.line(self.SPEC)

        def boom():
            raise RuntimeError("crash")
        crashing._before_ref_update = boom
        with self.assertRaises(RuntimeError):
            crashing.recompute()
        self.assertEqual(git(self.app, "rev-parse", crashing.ref("app")), old)           # never half
        self.assertNotEqual(self.line(self.SPEC).recompute()["app"].tip, old)             # the restart finishes it

    def test_a_git_failure_is_a_stated_error_so_the_caller_can_fall_back(self):
        self.seed()
        self.repos["app"] = Path(self.tmp.name) / "missing"
        with self.assertRaises(integ.IntegrationError) as caught:
            self.line(self.SPEC).tip("app")
        self.assertEqual(caught.exception.code, "INTEGRATION_GIT")
        self.repos["app"] = None
        with self.assertRaises(integ.IntegrationError) as caught:
            self.line(self.SPEC).tip("app")
        self.assertEqual(caught.exception.code, "INTEGRATION_REPOSITORY")


if __name__ == "__main__":
    unittest.main()
