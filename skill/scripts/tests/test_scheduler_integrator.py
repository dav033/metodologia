"""P-031: accepted prerequisite work reaches the tasks that come after it. Unit tests over real git objects (no worktrees,
no network), then the same through the real core + executor with the fake provider binaries."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_scheduler_integrator as integ
import scheduler_executor_support as s
from scheduler_executor_support import adapter, core, git


def snapshot(repo: Path, base: str, files: dict[str, str]) -> str:
    """A commit on top of `base` with `files` added or replaced, built with plumbing only (nothing is checked out)."""
    index = repo / ".git" / "snap-index"
    env = {**os.environ, "GIT_INDEX_FILE": str(index)}

    def run(*args, stdin=None):
        done = subprocess.run(["git", "-c", "user.name=T", "-c", "user.email=t@t", *args], cwd=str(repo), env=env,
                              input=stdin, capture_output=True, text=True, check=True)
        return done.stdout.strip()

    index.unlink(missing_ok=True)
    run("read-tree", base)
    for name, content in files.items():
        blob = run("hash-object", "-w", "--stdin", stdin=content)
        run("update-index", "--add", "--cacheinfo", f"100644,{blob},{name}")
    commit = run("commit-tree", run("write-tree"), "-p", base, "-m", "snap")
    index.unlink(missing_ok=True)
    return commit


class FakePlan:
    def __init__(self, spec):
        self.spec = {tid: SimpleNamespace(id=tid, after=tuple(after), repository=repo) for tid, (after, repo) in spec.items()}

    def task(self, tid):
        return self.spec[tid]

    def ids(self):
        return tuple(self.spec)


class Unit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = s.make_repo(Path(self.tmp.name) / "app")
        self.docs = s.make_repo(Path(self.tmp.name) / "docs")
        self.head = git(self.app, "rev-parse", "HEAD")
        self.accepted: dict[str, str] = {}
        self.snaps: dict[str, str | None] = {}
        self.earlier: dict[str, list[str]] = {}

    def bound(self, spec, default="app"):
        integrator = integ.PredecessorIntegrator()
        integrator.bind(plan=FakePlan(spec), accepted=lambda: dict(self.accepted), snapshot_of=lambda a: self.snaps.get(a),
                        repo_of=lambda role: {"app": self.app, "docs": self.docs}.get(role), default_repository=default,
                        identity="r1-abc-1", earlier_of=lambda tid: list(self.earlier.get(tid, ())))
        return integrator

    def accept(self, tid, sha):
        self.accepted[tid] = f"att-{tid}"
        self.snaps[f"att-{tid}"] = sha

    def test_a_task_with_no_predecessors_starts_from_the_fallback(self):
        self.assertEqual(self.bound({"T1": ([], "app")}).base_ref("T1"), "HEAD")

    def test_a_single_predecessor_is_handed_over_as_is_and_kept_alive_by_a_ref(self):
        s1 = snapshot(self.app, self.head, {"one.txt": "1\n"})
        self.accept("T1", s1)
        i = self.bound({"T1": ([], "app"), "T2": (["T1"], "app")})
        self.assertEqual(i.base_ref("T2"), s1)
        self.assertEqual(git(self.app, "rev-parse", f"refs/m3/integration/r1-abc-1/{integ.PredecessorIntegrator._ref_leaf('T2')}"), s1)

    def test_a_diamond_merges_both_branches_and_the_root(self):
        s1 = snapshot(self.app, self.head, {"root.txt": "r\n"})
        s2 = snapshot(self.app, s1, {"left.txt": "l\n"})
        s3 = snapshot(self.app, s1, {"right.txt": "r\n"})
        for tid, sha in (("T1", s1), ("T2", s2), ("T3", s3)):
            self.accept(tid, sha)
        i = self.bound({"T1": ([], "app"), "T2": (["T1"], "app"), "T3": (["T1"], "app"), "T4": (["T2", "T3"], "app")})
        base = i.base_ref("T4")
        for name in ("root.txt", "left.txt", "right.txt", "README.md"):
            git(self.app, "cat-file", "-e", f"{base}:{name}")
        self.assertEqual(len(git(self.app, "rev-list", "--parents", "-n1", base).split()) - 1, 2)   # a real merge
        self.assertEqual(i.base_ref("T4"), base)                                                   # a retry sees the same base

    def test_the_same_inputs_give_the_same_commit_in_a_fresh_integrator(self):
        s1 = snapshot(self.app, self.head, {"a.txt": "a\n"})
        s2 = snapshot(self.app, self.head, {"b.txt": "b\n"})
        self.accept("T1", s1)
        self.accept("T2", s2)
        spec = {"T1": ([], "app"), "T2": ([], "app"), "T3": (["T1", "T2"], "app")}
        self.assertEqual(self.bound(spec).base_ref("T3"), self.bound(spec).base_ref("T3"))

    def test_conflicting_predecessors_are_a_stated_error_not_a_guess(self):
        s2 = snapshot(self.app, self.head, {"README.md": "left\n"})
        s3 = snapshot(self.app, self.head, {"README.md": "right\n"})
        self.accept("T2", s2)
        self.accept("T3", s3)
        i = self.bound({"T2": ([], "app"), "T3": ([], "app"), "T4": (["T2", "T3"], "app")})
        with self.assertRaises(integ.IntegrationError) as caught:
            i.base_ref("T4")
        self.assertEqual(caught.exception.code, "INTEGRATION_CONFLICT")
        self.assertIn("README.md", caught.exception.detail)

    def redone_task_and_a_dependent(self):
        """T1 was accepted (v1), T2 was built on it, an audit sent T1 back and its redo (v2) started from the repository
        again: v2 and T2 both changed line 1 of the file v1 introduced, and T2 also changed line 20."""
        lines = [f"line{n}" for n in range(1, 21)]
        v1 = snapshot(self.app, self.head, {"f.txt": "\n".join(["t1 first draft", *lines[1:]]) + "\n"})
        t2 = snapshot(self.app, v1, {"f.txt": "\n".join(["t1 first draft", *lines[1:-1], "t2 own work"]) + "\n"})
        v2 = snapshot(self.app, self.head, {"f.txt": "\n".join(["t1 audited fix", *lines[1:]]) + "\n"})
        self.accept("T1", v2)
        self.accept("T2", t2)
        self.snaps["att-T1-v1"] = v1
        return {"T1": ([], "app"), "T2": (["T1"], "app"), "T3": (["T1", "T2"], "app")}

    def test_a_redone_task_that_clashes_with_its_dependent_merges_over_the_result_it_replaced(self):
        spec = self.redone_task_and_a_dependent()
        self.earlier["T1"] = ["att-T1-v1"]
        merged = self.bound(spec).base_ref("T3")
        text = git(self.app, "show", f"{merged}:f.txt")
        self.assertIn("t1 audited fix", text)                                      # the redo's fix
        self.assertIn("t2 own work", text)                                         # the dependent's work
        self.assertNotIn("t1 first draft", text)

    def test_a_real_overlap_with_the_earlier_result_as_base_still_conflicts(self):
        spec = self.redone_task_and_a_dependent()
        clash = snapshot(self.app, self.snaps["att-T1-v1"], {"f.txt": "t2 rewrote the same line\n"})
        self.accept("T2", clash)
        v2 = snapshot(self.app, self.head, {"f.txt": "t1 audited fix\n"})
        self.accept("T1", v2)
        self.earlier["T1"] = ["att-T1-v1"]
        with self.assertRaises(integ.IntegrationError) as caught:
            self.bound(spec).base_ref("T3")
        self.assertEqual(caught.exception.code, "INTEGRATION_CONFLICT")

    def carried_case(self, own_line):
        lines = [f"line{n}" for n in range(1, 21)]
        base = snapshot(self.app, self.head, {"up.txt": "\n".join(lines) + "\n"})
        v1 = snapshot(self.app, base, {"up.txt": "\n".join(["draft", *lines[1:]]) + "\n"})               # T1, first version
        own = snapshot(self.app, v1, {"own.txt": "T2 own work\n", **({"up.txt": own_line} if own_line else {})})
        v2 = snapshot(self.app, base, {"up.txt": "\n".join(["fixed", *lines[1:]]) + "\n"})               # T1 redone
        self.accept("T1", v2)
        self.accept("T2", own)
        self.snaps["att-T1-redo"] = v2
        return own, {"T1": ([], "app"), "T2": (["T1"], "app")}

    def test_an_earlier_result_is_carried_onto_the_redone_prerequisites_as_a_small_delta(self):
        own, spec = self.carried_case(None)
        carried = self.bound(spec).rebase("T2", own)
        self.assertEqual(git(self.app, "show", f"{carried}:own.txt"), "T2 own work")             # its own work is kept
        self.assertTrue(git(self.app, "show", f"{carried}:up.txt").startswith("fixed"))          # on the new prerequisite
        self.assertEqual(self.bound(spec).rebase("T2", own), carried)                            # deterministic
        self.assertIsNone(self.bound(spec).rebase("T2", "not-a-sha"))

    def test_an_earlier_result_that_overlaps_the_new_prerequisites_is_not_carried(self):
        own, spec = self.carried_case("T2 rewrote the file\n")
        self.assertIsNone(self.bound(spec).rebase("T2", own))

    def test_a_clash_caused_by_a_common_ancestor_that_was_redone_is_merged_over_its_earlier_result(self):
        lines = [f"line{n}" for n in range(1, 21)]
        base = snapshot(self.app, self.head, {"up.txt": "\n".join(lines) + "\n"})
        t0_v1 = snapshot(self.app, base, {"up.txt": "\n".join(["draft", *lines[1:]]) + "\n"})
        t1 = snapshot(self.app, t0_v1, {"one.txt": "T1 own\n"})                            # built on the first T0
        t0_v2 = snapshot(self.app, base, {"up.txt": "\n".join(["fixed", *lines[1:]]) + "\n"})   # T0 redone
        t2 = snapshot(self.app, t0_v2, {"two.txt": "T2 own\n"})                           # built on the redo
        self.accept("T0", t0_v2)
        self.accept("T1", t1)
        self.accept("T2", t2)
        self.snaps["att-T0-v1"] = t0_v1
        spec = {"T0": ([], "app"), "T1": (["T0"], "app"), "T2": (["T0"], "app"), "T3": (["T1", "T2"], "app")}
        self.earlier["T0"] = ["att-T0-v1"]
        merged = self.bound(spec).base_ref("T3")
        self.assertEqual({n: git(self.app, "show", f"{merged}:{n}")[:5] for n in ("one.txt", "two.txt", "up.txt")},
                         {"one.txt": "T1 ow", "two.txt": "T2 ow", "up.txt": "fixed"})

    def test_a_result_that_would_clash_with_accepted_work_is_reported_before_it_is_accepted(self):
        own, spec = self.carried_case(None)
        spec = {**spec, "T3": (["T1", "T2"], "app")}
        redo = self.snaps["att-T1"]
        del self.accepted["T1"]                                                    # T1 is being redone: v2 is the candidate
        self.assertEqual(self.bound(spec).would_conflict("T1", "att-T1-redo", redo), "")     # T2 carries over cleanly
        v1 = git(self.app, "rev-parse", f"{own}^1")
        self.snaps["att-T2"] = snapshot(self.app, v1, {"up.txt": "T2 rewrote the file\n"})  # now T2 overlaps the fix
        problem = self.bound(spec).would_conflict("T1", "att-T1-redo", redo)
        self.assertTrue(problem.startswith("T1 vs T2 for T") or problem.startswith("T2 vs T1 for T3"), problem)
        self.assertNotIn("att-T1-redo", self.accepted)                              # a dry run changes nothing

    def test_two_redone_prerequisites_are_merged_over_both_of_their_earlier_results_together(self):
        a_lines = [f"a{n}" for n in range(20)]
        b_lines = [f"b{n}" for n in range(20)]
        base = snapshot(self.app, self.head, {"a.txt": "\n".join(a_lines) + "\n", "b.txt": "\n".join(b_lines) + "\n"})
        a1 = snapshot(self.app, base, {"a.txt": "\n".join(["a draft", *a_lines[1:]]) + "\n"})
        b1 = snapshot(self.app, base, {"b.txt": "\n".join(["b draft", *b_lines[1:]]) + "\n"})
        tree = git(self.app, "merge-tree", "--write-tree", a1, b1).splitlines()[0]
        both = git(self.app, "-c", "user.name=T", "-c", "user.email=t@t", "commit-tree", tree, "-p", a1, "-p", b1, "-m", "both")
        built = snapshot(self.app, both, {"own.txt": "D own\n"})                    # D was built on both first versions
        a2 = snapshot(self.app, base, {"a.txt": "\n".join(["a fixed", *a_lines[1:]]) + "\n"})
        b2 = snapshot(self.app, base, {"b.txt": "\n".join(["b fixed", *b_lines[1:]]) + "\n"})
        self.accept("A", a2)
        self.accept("B", b2)
        self.accept("D", built)
        self.snaps["att-A-1"], self.snaps["att-B-1"] = a1, b1
        spec = {"A": ([], "app"), "B": ([], "app"), "D": (["A", "B"], "app"), "E": (["A", "B", "D"], "app")}
        self.earlier["A"], self.earlier["B"] = ["att-A-1"], ["att-B-1"]
        merged = self.bound(spec).base_ref("E")
        got = {n: git(self.app, "show", f"{merged}:{n}")[:7] for n in ("a.txt", "b.txt", "own.txt")}
        self.assertEqual(got, {"a.txt": "a fixed", "b.txt": "b fixed", "own.txt": "D own"})

    def test_a_result_is_checked_against_completed_tasks_built_on_the_one_it_replaces_even_if_nobody_else_waits(self):
        own, spec = self.carried_case(None)                                         # T2 was built on T1's first version
        redo = self.snaps["att-T1-redo"]
        del self.accepted["T1"]
        self.assertEqual(self.bound(spec).would_conflict("T1", "att-T1-redo", redo), "")     # merges over T2's own base
        clash = snapshot(self.app, self.snaps["att-T1-redo"], {"up.txt": "T1 redo, then T2 rewrote it\n"})
        self.accepted["T2"], self.snaps["att-T2"] = "att-T2", snapshot(self.app, git(self.app, "rev-parse", f"{own}^1"),
                                                                       {"up.txt": "T2 rewrote the same line\n"})
        problem = self.bound(spec).would_conflict("T1", "att-T1-redo", redo)
        self.assertTrue(problem.startswith("T1 vs T2 for T2"), problem)             # a real overlap, no task after them
        del clash

    def test_a_task_that_only_travels_in_the_merged_group_is_not_blamed_for_a_clash_it_cannot_fix(self):
        """B and C clash on f.txt whatever A does; A (a bystander merged with B) is a candidate whose result is harmless."""
        base = snapshot(self.app, self.head, {"f.txt": "\n".join(f"l{n}" for n in range(20)) + "\n"})
        b = snapshot(self.app, base, {"f.txt": "\n".join(["B", *[f"l{n}" for n in range(1, 20)]]) + "\n"})
        c = snapshot(self.app, base, {"f.txt": "\n".join(["C", *[f"l{n}" for n in range(1, 20)]]) + "\n"})
        a_old = snapshot(self.app, base, {"a.txt": "A old\n"})
        a_new = snapshot(self.app, base, {"a.txt": "A new\n"})
        self.accept("B", b)
        self.accept("C", c)
        self.accept("A", a_old)
        self.snaps["att-A-new"] = a_new
        spec = {"A": ([], "app"), "B": ([], "app"), "C": ([], "app"), "D": (["A", "B", "C"], "app")}
        with self.assertRaises(integ.IntegrationError):
            self.bound(spec).base_ref("D")                                          # the clash exists already
        self.assertEqual(self.bound(spec).would_conflict("A", "att-A-new", a_new), "")

    def test_a_clash_between_other_tasks_is_not_blamed_on_the_candidate(self):
        own, spec = self.carried_case(None)
        spec = {**spec, "T3": (["T1", "T2"], "app"), "T9": ([], "app")}
        self.assertEqual(self.bound(spec).would_conflict("T9", "att-T9", self.head), "")

    def test_an_accepted_predecessor_without_a_snapshot_blocks_instead_of_running_on_a_stale_tree(self):
        self.accept("T1", None)
        with self.assertRaises(integ.IntegrationError) as caught:
            self.bound({"T1": ([], "app"), "T2": (["T1"], "app")}).base_ref("T2")
        self.assertEqual(caught.exception.code, "PREDECESSOR_HANDOFF_MISSING")

    def test_a_predecessor_the_core_never_accepted_is_refused(self):
        with self.assertRaises(integ.IntegrationError) as caught:
            self.bound({"T1": ([], "app"), "T2": (["T1"], "app")}).base_ref("T2")
        self.assertEqual(caught.exception.code, "PREDECESSOR_NOT_ACCEPTED")

    def test_a_snapshot_that_is_not_in_the_repository_is_refused(self):
        self.accept("T1", "f" * 40)
        with self.assertRaises(integ.IntegrationError) as caught:
            self.bound({"T1": ([], "app"), "T2": (["T1"], "app")}).base_ref("T2")
        self.assertEqual(caught.exception.code, "PREDECESSOR_HANDOFF_MISSING")

    def test_ancestors_in_another_repository_are_not_merged_but_their_own_ancestors_are(self):
        s1 = snapshot(self.app, self.head, {"app-work.txt": "a\n"})
        docs_head = git(self.docs, "rev-parse", "HEAD")
        s2 = snapshot(self.docs, docs_head, {"doc.txt": "d\n"})
        self.accept("T1", s1)
        self.accept("T2", s2)
        i = self.bound({"T1": ([], "app"), "T2": (["T1"], "docs"), "T3": (["T2"], "app")})
        self.assertEqual(i.base_ref("T3"), s1)          # T2 lives in docs: only T1 (transitively) builds T3's tree
        self.assertEqual(i.base_ref("T2"), "HEAD")      # T1 is in another repository than T2

    def test_the_users_checkout_is_never_touched(self):
        s1 = snapshot(self.app, self.head, {"x.txt": "x\n"})
        s2 = snapshot(self.app, self.head, {"y.txt": "y\n"})
        self.accept("T1", s1)
        self.accept("T2", s2)
        before = (git(self.app, "rev-parse", "HEAD"), git(self.app, "status", "--porcelain"),
                  sorted(p.name for p in self.app.iterdir()))
        self.bound({"T1": ([], "app"), "T2": ([], "app"), "T3": (["T1", "T2"], "app")}).base_ref("T3")
        after = (git(self.app, "rev-parse", "HEAD"), git(self.app, "status", "--porcelain"),
                 sorted(p.name for p in self.app.iterdir()))
        self.assertEqual(before, after)

    def test_a_snapshot_another_snapshot_already_holds_is_not_merged_again(self):
        sa = snapshot(self.app, self.head, {"a.txt": "a\n"})
        sb = snapshot(self.app, self.head, {"b.txt": "b\n"})
        self.accept("A", sa)
        self.accept("B", sb)
        both = self.bound({"A": ([], "app"), "B": ([], "app"), "D": (["A", "B"], "app"), "E": (["D"], "app")}).base_ref("D")
        self.accept("D", snapshot(self.app, both, {"d.txt": "d\n"}))
        i = self.bound({"A": ([], "app"), "B": ([], "app"), "D": (["A", "B"], "app"), "E": (["D"], "app")})
        self.assertEqual(i.base_ref("E"), self.snaps["att-D"])        # D already holds A and B: E builds on D alone

    def test_any_task_id_gets_a_valid_distinct_ref(self):
        s1 = snapshot(self.app, self.head, {"a.txt": "a\n"})
        self.accept("T1", s1)
        for name in (".x", "a..b", "x.lock", "a/b", "a b", "-lead", "é"):
            spec = {"T1": ([], "app"), name: (["T1"], "app")}
            self.bound(spec).base_ref(name)
        leaves = {integ.PredecessorIntegrator._ref_leaf(n) for n in ("a/b", "a b")}
        self.assertEqual(len(leaves), 2)
        refs = git(self.app, "for-each-ref", "--format=%(refname)", "refs/m3/integration").splitlines()
        self.assertEqual(len(refs), 7)

    def test_a_hostile_git_environment_is_not_followed(self):
        s1 = snapshot(self.app, self.head, {"a.txt": "a\n"})
        self.accept("T1", s1)
        i = self.bound({"T1": ([], "app"), "T2": (["T1"], "app")})
        other = str(self.docs / ".git")
        old = os.environ.get("GIT_DIR")
        os.environ["GIT_DIR"] = other
        self.addCleanup(lambda: os.environ.pop("GIT_DIR", None) if old is None else os.environ.__setitem__("GIT_DIR", old))
        self.assertEqual(i.base_ref("T2"), s1)
        refs = subprocess.run(["git", "for-each-ref", "refs/m3/integration"], cwd=str(self.docs), capture_output=True,
                              text=True, env={k: v for k, v in os.environ.items() if k != "GIT_DIR"}).stdout
        self.assertEqual(refs.strip(), "", "a ref was written to another repository")
        self.assertTrue(git(self.app, "for-each-ref", "refs/m3/integration") if "GIT_DIR" not in os.environ else True)

    def test_the_conflict_detail_names_who_clashes_then_the_files_and_fits_the_core_limit(self):
        s2 = snapshot(self.app, self.head, {"README.md": "left\n"})
        s3 = snapshot(self.app, self.head, {"README.md": "right\n"})
        self.accept("T2", s2)
        self.accept("T3", s3)
        with self.assertRaises(integ.IntegrationError) as caught:
            self.bound({"T2": ([], "app"), "T3": ([], "app"), "T4": (["T2", "T3"], "app")}).base_ref("T4")
        self.assertTrue(caught.exception.detail.startswith("T2 vs T3 for T4: README.md"))
        self.assertLessEqual(len(f"{caught.exception.code}: {caught.exception.detail}"), 200)
        self.assertTrue(caught.exception.permanent)

    def test_an_unbound_integrator_says_so(self):
        with self.assertRaises(integ.IntegrationError) as caught:
            integ.PredecessorIntegrator().base_ref("T1")
        self.assertEqual(caught.exception.code, "INTEGRATION_UNBOUND")


class Through(s.World):
    """The same hand-over through the real core, the real executor and the fake provider binaries."""

    def attempt_of(self, w, task_id):
        rows = [w.executor.ledger.get(a) for a in w.executor.ledger.all_ids()]
        return next(r for r in rows if r["request"]["task_id"] == task_id)

    def test_a_dependent_task_starts_from_a_tree_that_contains_its_predecessors_work(self):
        self.approve([s.task("T1", "first"), s.task("T2", "second", after=["T1"])])
        w = self.wire("direct:claude/haiku")                       # on by default
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90), w.scheduler.snapshot())
        repo = self.repos["app"]
        t1, t2 = self.attempt_of(w, "T1"), self.attempt_of(w, "T2")
        snap1 = t1["handoff"]["snapshot_sha"]
        self.assertEqual(t1["workspace"]["base_sha"], git(repo, "rev-parse", "HEAD"))           # the first starts from HEAD
        self.assertEqual(t2["workspace"]["base_sha"], snap1)                                     # the second starts from T1's work
        git(repo, "cat-file", "-e", f"{t2['workspace']['base_sha']}:claude-made.txt")            # ...which has T1's file
        self.assertEqual(git(repo, "status", "--porcelain"), "")                                 # the user's checkout is clean

    def test_with_the_option_off_every_task_starts_from_head(self):
        self.approve([s.task("T1", "first"), s.task("T2", "second", after=["T1"])])
        w = self.wire("direct:claude/haiku", integrate_predecessors=False)
        self.assertTrue(self.run_until(w, lambda snap: snap.status == "completed", 90))
        head = git(self.repos["app"], "rev-parse", "HEAD")
        self.assertEqual({self.attempt_of(w, t)["workspace"]["base_sha"] for t in ("T1", "T2")}, {head})

    def test_a_transient_integration_failure_is_raised_for_a_retry_not_a_rejection(self):
        self.approve([s.task("T1", "first")])
        plan = adapter.sched.approved_plan(self.rdir)

        def hiccup(task_id):
            raise integ.IntegrationError("INTEGRATION_GIT", "git merge-tree: timed out")

        port = adapter.CoreExecutionPort(None, plan, project="proj", base_ref=hiccup, default_repository="app")
        order = SimpleNamespace(plan_id=plan.plan_id, revision=plan.revision, task_id="T1", attempt_id="att-0001", token=1,
                                executor="direct:claude/haiku", idempotency_key="k", acceptance_criteria=(), verification=())
        with self.assertRaises(RuntimeError):
            port.start(order)

    def test_an_integration_error_rejects_the_order_with_its_cause(self):
        self.approve([s.task("T1", "first")])
        plan = adapter.sched.approved_plan(self.rdir)

        def refuse(task_id):
            raise integ.IntegrationError("INTEGRATION_CONFLICT", "T2 and T3 change README.md")

        port = adapter.CoreExecutionPort(None, plan, project="proj", base_ref=refuse, default_repository="app")
        order = SimpleNamespace(plan_id=plan.plan_id, revision=plan.revision, task_id="T1", attempt_id="att-0001", token=1,
                                executor="direct:claude/haiku", idempotency_key="k", acceptance_criteria=(), verification=())
        ack = port.start(order)
        self.assertEqual(ack.status, "rejected")
        self.assertIn("INTEGRATION_CONFLICT", ack.detail)


if __name__ == "__main__":
    unittest.main()
