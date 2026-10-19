"""Atomic reservations, resource conflicts and real concurrency (SC-AC07, SC-AC08)."""
from __future__ import annotations

import subprocess
import sys
import threading
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, approved, indep, plan_text, sqlite_path, task

import bt_scheduler_core as sc
from bt_scheduler_core.resources import ALL, claims_for, conflict

PACKAGE_PARENT = Path(__file__).resolve().parents[2]


def spec(**kw):
    return approved(plan_text([task("T1", **kw)]))[0].task("T1")


class Claims(unittest.TestCase):
    def test_declared_resources_are_exclusive_and_repository_is_shared_by_default(self):
        got = dict(claims_for(spec(repo="app", paths=["src/a/**"], resources=["db"]), sc.Config()))
        self.assertEqual(got["res:db"], "x")
        self.assertEqual(got["repo:app"], "s")
        self.assertEqual(got["path:app:src/a/**"], "x")

    def test_exclusive_repository_mode(self):
        got = dict(claims_for(spec(repo="app", paths=["a"]), sc.Config(repository_isolation="exclusive")))
        self.assertEqual(got["repo:app"], "x")

    def test_unknown_surface_serialises_by_default(self):
        self.assertEqual(claims_for(spec(), sc.Config()), [(ALL, "x")])
        self.assertEqual(claims_for(spec(repo="app"), sc.Config()), [("repo:app", "x")])
        self.assertEqual(claims_for(spec(), sc.Config(unknown_surface="allow")), [])

    def test_conflict_rules(self):
        cases = [
            ([("res:db", "x")], [("res:db", "x")], True),
            ([("res:db", "x")], [("res:cache", "x")], False),
            ([("repo:a", "s")], [("repo:a", "s")], False),
            ([("repo:a", "s")], [("repo:a", "x")], True),
            ([("path:a:src/**", "x")], [("path:a:src/x/y.py", "x")], True),
            ([("path:a:src/**", "x")], [("path:a:docs/**", "x")], False),
            ([("path:a:src/**", "x")], [("path:b:src/**", "x")], False),
            ([("path:a:src/ab/**", "x")], [("path:a:src/a/**", "x")], False),   # prefix must end at a directory
            ([("path:a:**/x.py", "x")], [("path:a:src/y.py", "x")], True),        # leading glob: overlap assumed
            ([(ALL, "x")], [("res:db", "x")], True),
            ([], [("res:db", "x")], False),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assertEqual(conflict(a, b), expected)
                self.assertEqual(conflict(b, a), expected)  # symmetric


class Capacity(unittest.TestCase):
    def test_exclusive_resource_serialises_tasks_and_releases_on_completion(self):
        h = Harness([task("T1", repo="a", paths=["a/**"], resources=["db"]), task("T2", repo="b", paths=["b/**"], resources=["db"]),
                     indep("T3")], parallel=3)
        h.core.step()
        self.assertEqual(h.states(), {"T1": "active", "T2": "ready", "T3": "active"})  # T2 waits for the db
        h.finish_and_accept("T1")
        self.assertEqual(h.state("T2"), "active")

    def test_overlapping_paths_in_one_repository_serialise_disjoint_ones_do_not(self):
        h = Harness([task("A", repo="r", paths=["src/**"]), task("B", repo="r", paths=["src/x/**"]),
                     task("C", repo="r", paths=["docs/**"])], parallel=3)
        h.core.step()
        self.assertEqual(h.states(), {"A": "active", "B": "ready", "C": "active"})

    def test_exclusive_repository_mode_runs_one_task_per_repository(self):
        h = Harness([task("A", repo="r", paths=["a/**"]), task("B", repo="r", paths=["b/**"])],
                    config=sc.Config(max_parallel_tasks=3, repository_isolation="exclusive"))
        h.core.step()
        self.assertEqual(sorted(h.states().values()), ["active", "ready"])

    def test_tasks_with_unknown_surface_never_run_next_to_anything(self):
        h = Harness([task("U"), indep("A"), indep("B")], parallel=3)
        h.core.step()
        self.assertEqual(h.state("U"), "active")
        self.assertEqual((h.state("A"), h.state("B")), ("ready", "ready"))

    def test_claim_refusals_have_stable_reasons(self):
        h = Harness([indep("T1"), indep("T2", ["T1"]), task("T3", resources=["db"]), task("T4", resources=["db"])], parallel=2)
        reasons = {t: h.core.claim(sc.Assignment(t, "w")).reason for t in ("T2", "ghost")}
        self.assertEqual(reasons, {"T2": "not_ready", "ghost": "unknown_task"})
        self.assertTrue(h.core.claim(sc.Assignment("T3", "w")).ok)
        self.assertEqual(h.core.claim(sc.Assignment("T4", "w")).reason, "resource_conflict")
        self.assertTrue(h.core.claim(sc.Assignment("T1", "w")).ok)
        h2 = Harness([indep("T1"), indep("T2")], parallel=1)
        self.assertTrue(h2.core.claim(sc.Assignment("T1", "w")).ok)
        self.assertEqual(h2.core.claim(sc.Assignment("T2", "w")).reason, "no_capacity")
        self.assertEqual(h2.core.claim(sc.Assignment("T1", "w")).reason, "not_ready")
        self.assertEqual(h2.core.claim(sc.Assignment("T2", " ")).reason, "invalid_executor")

    def test_refused_claims_are_audited_and_change_nothing(self):
        h = Harness([task("T3", resources=["db"]), task("T4", resources=["db"])], parallel=2)
        h.core.claim(sc.Assignment("T3", "w"))
        before = h.core.read(lambda c: c.state.to_dict()["attempts"])
        h.core.claim(sc.Assignment("T4", "w"))
        self.assertEqual(h.core.read(lambda c: c.state.to_dict()["attempts"]), before)
        self.assertIn("reservation_refused", h.audit_kinds())

    def test_the_core_never_reads_classification_to_decide(self):
        """complexity/risk/estimates are opaque: two tasks differing only in them are treated identically."""
        h = Harness([indep("T1", risk="high", complexity="extreme", estimated_minutes=9999), indep("T2", risk="low")], parallel=2)
        h.core.step()
        self.assertEqual(set(h.states().values()), {"active"})


    def test_a_large_scope_runs_alone_in_its_repository_only_when_the_operator_names_it(self):
        tasks = [task("T1", repo="app", paths=["src/a/**"], scope="small_change"),
                 task("T2", repo="app", paths=["src/b/**"], scope="large_change"),
                 task("T3", repo="app", paths=["src/c/**"], scope="isolated_fix"),
                 task("T4", repo="other", paths=["x/**"], scope="full_feature")]
        plain = Harness(tasks, parallel=3)
        plain.core.step()
        self.assertEqual(sorted(t for t, s in plain.states().items() if s == "active"), ["T1", "T2", "T3"])
        ruled = Harness(tasks, config=sc.Config(max_parallel_tasks=3, exclusive_scopes=("large_change", "full_feature")))
        ruled.core.step()
        ruled.core.step()                                   # a refused claim leaves its slot for the next pass
        active = sorted(t for t, s in ruled.states().items() if s == "active")
        self.assertNotIn("T2", active)                      # waits: small tasks already hold the repository
        self.assertEqual(active, ["T1", "T3", "T4"])        # the large one in another repository runs beside them
        with self.assertRaises(sc.SchedulerError):
            sc.Config(exclusive_scopes=["large_change"])

class Concurrency(unittest.TestCase):
    """Two or more real claimers racing for the same task: at most one is authorised to write (SC-AC07)."""

    def race(self, repo_factory, workers=8, tasks=1):
        h = Harness([indep(f"T{i}") for i in range(tasks)], repository=repo_factory(), parallel=tasks)
        cores = [h.build() for _ in range(workers)]
        barrier, results, errors = threading.Barrier(workers), [], []

        def go(core, label):
            try:
                barrier.wait(timeout=10)
                for i in range(tasks):
                    results.append((f"T{i}", label, core.claim(sc.Assignment(f"T{i}", label)).ok))
            except Exception as exc:  # noqa: BLE001 - collected and asserted empty below - reported below
                errors.append(repr(exc))

        threads = [threading.Thread(target=go, args=(c, f"w{i}")) for i, c in enumerate(cores)]
        [t.start() for t in threads]
        [t.join(30) for t in threads]
        self.assertEqual(errors, [])
        return h, results

    def test_one_winner_per_task_in_memory(self):
        h, results = self.race(sc.InMemoryRepository, workers=8, tasks=3)
        for tid in ("T0", "T1", "T2"):
            self.assertEqual(sum(1 for t, _l, ok in results if t == tid and ok), 1, tid)
        self.assertEqual(h.core.read(lambda c: len(c.state.attempts)), 3)

    def test_one_winner_per_task_with_sqlite_connections(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        h, results = self.race(lambda: sc.SqliteRepository(path), workers=6, tasks=2)
        for tid in ("T0", "T1"):
            self.assertEqual(sum(1 for t, _l, ok in results if t == tid and ok), 1, tid)
        live = h.core.read(lambda c: [a.task_id for a in c.state.attempts.values()])
        self.assertEqual(sorted(live), ["T0", "T1"])

    def test_incompatible_resources_are_never_both_held_under_a_race(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        tasks = [task(f"T{i}", repo=f"r{i}", paths=[f"{i}/**"], resources=["db"]) for i in range(6)]
        h = Harness(tasks, repository=sc.SqliteRepository(path), parallel=6)
        cores = [h.build() for _ in range(6)]
        barrier, wins = threading.Barrier(6), []

        def go(core, i):
            barrier.wait(timeout=10)
            if core.claim(sc.Assignment(f"T{i}", "w")).ok:
                wins.append(i)

        threads = [threading.Thread(target=go, args=(c, i)) for i, c in enumerate(cores)]
        [t.start() for t in threads]
        [t.join(30) for t in threads]
        self.assertEqual(len(wins), 1)

    def test_separate_processes_cannot_both_win_the_same_task(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        h = Harness([indep("T1")], repository=sc.SqliteRepository(path))
        script = ("import sys; sys.path.insert(0, sys.argv[1]); import bt_scheduler_core as sc\n"
                  "plan = sc.load_plan(sys.argv[3], approved_sha256=sys.argv[4])\n"
                  "core = sc.SchedulerCore(plan, sc.SqliteRepository(sys.argv[2]), config=sc.Config(max_parallel_tasks=3))\n"
                  "print('WIN' if core.claim(sc.Assignment('T1', 'proc')).ok else 'LOSE')")
        procs = [subprocess.Popen([sys.executable, "-I", "-c", script, str(PACKAGE_PARENT), str(path), h.text, h.sha],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(5)]
        outs = [p.communicate(timeout=60) for p in procs]
        self.assertTrue(all(p.returncode == 0 for p in procs), outs)
        self.assertEqual(sum(1 for o, _ in outs if o.strip() == "WIN"), 1, outs)


if __name__ == "__main__":
    unittest.main()
