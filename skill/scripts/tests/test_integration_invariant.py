"""REQ-030 step 1: an integrated tree never silently loses the work of an accepted task (bt_integration_invariant)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_integration_invariant as inv
import bt_interventions
import bt_scheduler_integrator as integ
from scheduler_executor_support import git
import test_scheduler_integrator as base_tests
from test_scheduler_integrator import snapshot


def with_tree_of(repo: Path, parent: str, tree_from: str, message: str = "snap") -> str:
    """A commit whose parent is `parent` but whose files are those of `tree_from` (what an attempt leaves when its worktree
    dropped files its starting commit had)."""
    tree = git(repo, "rev-parse", f"{tree_from}^{{tree}}")
    return git(repo, "-c", "user.name=T", "-c", "user.email=t@t", "commit-tree", tree, "-p", parent, "-m", message)


def has(repo: Path, ref: str, name: str) -> bool:
    import subprocess
    return subprocess.run(["git", "-C", str(repo), "cat-file", "-e", f"{ref}:{name}"], capture_output=True).returncode == 0


class Base(unittest.TestCase):
    setUp, bound, accept = base_tests.Unit.setUp, base_tests.Unit.bound, base_tests.Unit.accept


class Req020Replica(Base):
    """T14 starts from T10 + T12 + T13; T13's snapshot descends from T12's (it was built on it) but its tree lacks
    `directions.ts`, so a merge that trusts ancestry drops it: the failure that cost REQ-020 three attempts."""
    SPEC = {"T10": ([], "app"), "T12": ([], "app"), "T13": ([], "app"), "T14": (["T10", "T12", "T13"], "app")}

    def build(self):
        self.s10 = snapshot(self.app, self.head, {"src/voice.ts": "voice\n"})
        self.s12 = snapshot(self.app, self.head, {"src/directions.ts": "directions\n"})
        wrong = snapshot(self.app, self.head, {"src/packages.ts": "packages\n"})
        self.s13 = with_tree_of(self.app, self.s12, wrong)                       # parent T12, tree without directions.ts
        for tid, sha in (("T10", self.s10), ("T12", self.s12), ("T13", self.s13)):
            self.accept(tid, sha)

    def test_the_plain_merge_loses_the_files_so_the_reproduction_is_not_vacuous(self):
        self.build()
        integrator = self.bound(self.SPEC)
        with mock.patch.object(integ.PredecessorIntegrator, "_guarantee", lambda self_, repo, task, merged, items: merged):
            tree = integrator.base_ref("T14")
        self.assertTrue(has(self.app, tree, "src/voice.ts"))
        self.assertFalse(has(self.app, tree, "src/directions.ts"))               # lost by the ancestry shortcut

    def test_no_file_of_an_accepted_task_is_missing_from_the_tree_a_task_starts_from(self):
        self.build()
        events = []
        integrator = self.bound(self.SPEC)
        integrator._bound["on_event"] = lambda kind, **fields: events.append((kind, fields))
        tree = integrator.base_ref("T14")
        for name in ("src/voice.ts", "src/directions.ts", "src/packages.ts", "README.md"):
            self.assertTrue(has(self.app, tree, name), name)
        self.assertEqual([(kind, f["result"]) for kind, f in events], [("integration_defect", "fixed")])
        self.assertIn("T12: src/directions.ts", events[0][1]["evidence"])
        self.assertEqual(integrator.base_ref("T14"), tree)                        # stable on a retry, no second repair event
        self.assertEqual(len(events), 1)

    def test_an_unrepairable_loss_is_a_stated_error_never_an_incomplete_tree(self):
        self.build()
        integrator = self.bound(self.SPEC)
        with mock.patch.object(inv, "restore", return_value=None):
            with self.assertRaises(integ.IntegrationError) as caught:
                integrator.base_ref("T14")
        self.assertEqual(caught.exception.code, "INTEGRATION_FILES_LOST")
        self.assertTrue(caught.exception.permanent)
        self.assertIn("src/directions.ts", caught.exception.detail)


class OnTheLine(Base):
    def test_the_line_restores_what_an_undeclared_deletion_removed_and_reports_it(self):
        import bt_integration_line as line_mod
        s12 = snapshot(self.app, self.head, {"src/directions.ts": "directions\n"})
        s13 = with_tree_of(self.app, s12, snapshot(self.app, self.head, {"src/packages.ts": "packages\n"}))
        self.accept("T12", s12)
        self.accept("T13", s13)
        integrator = self.bound({"T12": ([], "app"), "T13": ([], "app"), "T14": (["T12", "T13"], "app")})
        events = []
        integrator.attach_line(line_mod.Line(
            plan=integrator._bound["plan"], accepted=lambda: dict(self.accepted), snapshot_of=lambda a: self.snaps.get(a),
            repo_of=lambda role: self.app, default_repository="app", identity="r1-abc-1",
            on_event=lambda kind, **fields: events.append((kind, fields["result"]))))
        tree = integrator.base_ref("T14")
        for name in ("src/directions.ts", "src/packages.ts"):
            self.assertTrue(has(self.app, tree, name), name)
        self.assertEqual(events, [("integration_defect", "fixed")])


    def test_a_retry_that_continued_from_a_rejected_snapshot_applies_on_a_tip_that_never_held_it(self):
        import bt_integration_line as line_mod
        rejected = snapshot(self.app, self.head, {"result.txt": "first try\n"})            # attempt 1: never accepted, not in the tip
        retry = snapshot(self.app, rejected, {"result.txt": "second try\n"})              # attempt 2 continued from it
        integrator = self.bound({"T1": ([], "app")})
        line = line_mod.Line(plan=integrator._bound["plan"], accepted=lambda: {}, snapshot_of=lambda a: None,
                             repo_of=lambda role: self.app, default_repository="app", identity="r1-abc-1")
        merged, conflicts = line.apply("app", "T1", "att-2", retry, start_base=rejected)
        self.assertEqual(conflicts, ())
        self.assertEqual(git(self.app, "show", f"{merged}:result.txt"), "second try")

    def probe(self, spec):
        import bt_integration_line as line_mod
        import bt_scheduler_executor_wiring as wiring
        plan = self.bound(spec)._bound["plan"]
        return wiring._migration_probe(line_mod.Line(
            plan=plan, accepted=lambda: dict(self.accepted), snapshot_of=lambda a: self.snaps.get(a),
            repo_of=lambda role: self.app, default_repository="app", identity="r1-abc-1"))()

    def test_a_run_accepted_without_the_line_migrates_when_its_work_composes_and_not_when_it_overlaps(self):
        s1 = snapshot(self.app, self.head, {"one.ts": "1\n"})
        s2 = snapshot(self.app, s1, {"two.ts": "2\n"})                                # built on T1 (predecessor merge)
        s3 = snapshot(self.app, self.head, {"three.ts": "3\n"})
        for tid, sha in (("T1", s1), ("T2", s2), ("T3", s3)):
            self.accept(tid, sha)
        spec = {"T1": ([], "app"), "T2": (["T1"], "app"), "T3": ([], "app")}
        self.assertEqual(self.probe(spec), "")
        self.accept("T3", snapshot(self.app, self.head, {"two.ts": "other 2\n"}))     # T3 and T2 both create two.ts
        self.assertIn("does not fit the integrated tree", self.probe(spec))


class Rules(Base):
    def test_a_file_back_at_its_old_content_is_a_revert_and_is_restored(self):
        base = snapshot(self.app, self.head, {"cfg.json": "old\n"})
        s1 = snapshot(self.app, base, {"cfg.json": "new\n"})
        s2 = with_tree_of(self.app, s1, snapshot(self.app, base, {"other.ts": "o\n"}))   # built on s1, its tree has the old cfg.json
        self.accept("T1", s1)
        self.accept("T2", s2)
        spec = {"T1": ([], "app"), "T2": ([], "app"), "T3": (["T1", "T2"], "app")}
        integrator = self.bound(spec)
        integrator._bound["start_base_of"] = lambda attempt: base                     # T2 started from `base`: it never touched cfg.json
        tree = integrator.base_ref("T3")
        self.assertEqual(git(self.app, "show", f"{tree}:cfg.json"), "new")
        self.assertTrue(has(self.app, tree, "other.ts"))

    def test_a_deletion_a_task_declares_is_an_explicit_replacement_not_a_loss(self):
        base = snapshot(self.app, self.head, {"old.ts": "old\n"})
        s1 = snapshot(self.app, self.head, {"new.ts": "new\n"})
        s2 = with_tree_of(self.app, base, s1)                                      # drops old.ts, adds new.ts
        self.accept("T1", base)
        self.accept("T2", s2)
        spec = {"T1": ([], "app"), "T2": ([], "app"), "T3": (["T1", "T2"], "app")}
        integrator = self.bound(spec)
        integrator._bound["plan"].spec["T2"].expected_paths = ("old.ts", "new.ts")
        tree = integrator.base_ref("T3")
        self.assertFalse(has(self.app, tree, "old.ts"))
        self.assertTrue(has(self.app, tree, "new.ts"))

    def test_a_task_built_on_another_may_replace_what_it_built_on(self):
        s1 = snapshot(self.app, self.head, {"draft.ts": "draft\n"})
        s2 = with_tree_of(self.app, s1, self.head)                                 # T2 comes after T1 and removes draft.ts
        self.accept("T1", s1)
        self.accept("T2", s2)
        tree = self.bound({"T1": ([], "app"), "T2": (["T1"], "app"), "T3": (["T2"], "app")}).base_ref("T3")
        self.assertFalse(has(self.app, tree, "draft.ts"))

    def test_a_result_that_deletes_a_siblings_file_without_declaring_it_is_rejected_with_the_cause(self):
        self.accept("T1", snapshot(self.app, self.head, {"mine.ts": "x\n"}))
        integrator = self.bound({"T1": ([], "app"), "T2": ([], "app")})
        candidate = with_tree_of(self.app, snapshot(self.app, self.head, {"mine.ts": "x\n"}), self.head)
        clash = integrator.would_conflict("T2", "att-T2", candidate)
        self.assertTrue(clash.startswith("INTEGRATION_FILES_LOST T2"), clash)
        self.assertIn("T1: mine.ts", clash)
        integrator._bound["plan"].spec["T2"].expected_paths = ("mine.ts",)
        self.assertEqual(integrator.would_conflict("T2", "att-T2", candidate), "")

    def test_report_and_path_matching(self):
        self.assertTrue(inv.covers("src/lib", "src/lib/a/b.ts"))
        self.assertTrue(inv.covers("src/lib/**", "src/lib/a/b.ts"))
        self.assertTrue(inv.covers("src/*.ts", "src/a.ts"))
        self.assertFalse(inv.covers("src/lib", "src/library/a.ts"))
        self.assertFalse(inv.covers("", "a"))
        self.assertTrue(inv.Report({}, {}).ok)
        self.assertEqual(inv.Report({"T1": ("a", "b")}, {"T1": ("b", "c")}).files(), {"T1": ("a", "b", "c")})


if __name__ == "__main__":
    unittest.main()
