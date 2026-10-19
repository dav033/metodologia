"""Rebase of a run onto revision N+1: accepted unchanged work survives, everything else is redone (REQ SUPERRR T4.5)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]

from support import Harness, approved, indep, plan_text, sqlite_path

import bt_scheduler_core as sc


def next_plan(tasks, revision=2, plan_id="REQ-T"):
    plan, _ = approved(plan_text(tasks, plan_id, revision))
    return plan


def accepted_chain(*tasks, repository=None):
    """A run with T1 and T2 accepted (and the rest untouched) on revision 1."""
    h = Harness(list(tasks), repository=repository, parallel=1)
    for tid in ("T1", "T2"):
        h.core.step()
        h.finish_and_accept(tid)
    return h


class Rebase(unittest.TestCase):
    def tasks(self):
        return [indep("T1"), indep("T2", ["T1"]), indep("T3", ["T2"])]

    def test_unchanged_accepted_work_is_kept_and_new_work_starts_pending_then_ready(self):
        h = accepted_chain(*self.tasks())
        self.assertEqual((h.state("T1"), h.state("T2")), ("completed", "completed"))
        # T3 is live now: finish and reject its attempt so no attempt is alive, then rebase with a changed T3 + new T4
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3", accepted=False)
        new = next_plan(self.tasks()[:2] + [indep("T3", ["T2"], title="changed"), indep("T4", ["T3"])])
        report = sc.rebase_run(h.repo, h.plan, new, config=h.config, clock=h.clock)
        self.assertEqual((report.kept, report.reset, report.added, report.removed),
                         (("T1", "T2"), ("T3",), ("T4",), ()))
        core = sc.SchedulerCore(new, h.repo, config=h.config, clock=h.clock,
                                ports=sc.Ports(execution=h.executor, verification=h.verifier))
        core.start()
        states = {k: v["state"] for k, v in core.snapshot().tasks.items()}
        self.assertEqual(states["T1"], "completed")
        self.assertEqual(states["T2"], "completed")
        self.assertEqual(states["T3"], "ready")                      # its prerequisites are still accepted: it can run
        self.assertEqual(states["T4"], "pending")
        snap = core.snapshot()
        self.assertEqual(snap.revision, 2)

    def test_a_task_with_new_criteria_is_reset_and_so_are_its_dependents(self):
        h = accepted_chain(*self.tasks())
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3")
        h.core.step()
        changed_t1 = indep("T1")
        changed_t1["acceptance_criteria"] = ["T1 now also logs"]
        new = next_plan([changed_t1, indep("T2", ["T1"]), indep("T3", ["T2"])])
        report = sc.rebase_run(h.repo, h.plan, new, config=h.config, clock=h.clock)
        self.assertEqual((report.kept, report.reset), ((), ("T1", "T2", "T3")))      # built on a changed base: redo

    def test_classification_alone_never_resets_accepted_work(self):
        h = accepted_chain(*self.tasks())
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3")
        h.core.step()
        tasks = self.tasks()
        tasks[0]["complexity"], tasks[0]["risk"] = "extreme", "high"                # an estimate is not the work
        report = sc.rebase_run(h.repo, h.plan, next_plan(tasks), config=h.config, clock=h.clock)
        self.assertEqual((report.kept, report.reset), (("T1", "T2", "T3"), ()))

    def test_a_removed_task_is_dropped_and_its_history_stays(self):
        h = accepted_chain(*self.tasks())
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3")
        h.core.step()
        report = sc.rebase_run(h.repo, h.plan, next_plan(self.tasks()[:2]), config=h.config, clock=h.clock)
        self.assertEqual((report.removed, report.kept), (("T3",), ("T1", "T2")))
        core = sc.SchedulerCore(next_plan(self.tasks()[:2]), h.repo, config=h.config, clock=h.clock,
                                ports=sc.Ports(execution=h.executor, verification=h.verifier))
        core.start()
        self.assertEqual(set(core.snapshot().tasks), {"T1", "T2"})
        self.assertEqual(core.snapshot().status, "completed")

    def test_live_attempts_refuse_the_rebase_and_nothing_changes(self):
        h = Harness(self.tasks(), parallel=1)
        h.core.step()                                                # T1 is active
        before = h.core.audit_log()
        with self.assertRaises(sc.SchedulerError) as ctx:
            sc.rebase_run(h.repo, h.plan, next_plan(self.tasks()), config=h.config, clock=h.clock)
        self.assertEqual(ctx.exception.code, "NOT_ALLOWED")
        self.assertIn("alive", str(ctx.exception))
        self.assertEqual(len(h.core.audit_log()), len(before))
        self.assertEqual(h.core.snapshot().revision, 1)

    def test_other_refusals(self):
        h = accepted_chain(*self.tasks())
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3")
        h.core.step()
        for new, code in ((next_plan(self.tasks(), revision=1), "NOT_ALLOWED"),
                          (next_plan(self.tasks(), plan_id="REQ-OTHER"), "NOT_ALLOWED")):
            with self.assertRaises(sc.SchedulerError) as ctx:
                sc.rebase_run(h.repo, h.plan, new, config=h.config, clock=h.clock)
            self.assertEqual(ctx.exception.code, code)
        wrong_old, _ = approved(plan_text(self.tasks(), "REQ-T", 1) + " ")
        with self.assertRaises(sc.SchedulerError) as ctx:
            sc.rebase_run(h.repo, wrong_old, next_plan(self.tasks()), config=h.config, clock=h.clock)
        self.assertEqual(ctx.exception.code, "PLAN_MISMATCH")
        with self.assertRaises(sc.SchedulerError):
            sc.rebase_run(sc.InMemoryRepository(), h.plan, next_plan(self.tasks()))      # no run to move

    def test_audit_records_the_rebase_and_the_old_plan_no_longer_binds(self):
        h = accepted_chain(*self.tasks())
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3", accepted=False)
        new = next_plan(self.tasks() + [indep("T4", ["T3"])])
        sc.rebase_run(h.repo, h.plan, new, config=h.config, clock=h.clock)
        entry = [e for e in h.repo.audit_log() if e.kind == "run_rebased"][0]
        self.assertEqual((entry.detail["from_rev"], entry.detail["to_rev"], entry.detail["kept"], entry.detail["added"]),
                         (1, 2, ["T1", "T2"], ["T4"]))
        self.assertEqual(entry.detail["reset"], ["T3"])
        self.assertTrue(any(e.kind == "task_transition" and e.detail.get("decision") == "rebase"
                            for e in h.repo.audit_log()))
        with self.assertRaises(sc.SchedulerError) as ctx:
            h.build().start()                                         # revision 1 can no longer bind this run
        self.assertEqual(ctx.exception.code, "PLAN_MISMATCH")

    def test_it_works_on_the_durable_repository_and_survives_a_restart(self):
        tmp, path = sqlite_path()
        self.addCleanup(tmp.cleanup)
        h = accepted_chain(*self.tasks(), repository=sc.SqliteRepository(path))
        h.send("T3", "execution_finished")
        h.core.step()
        h.verdict("T3", accepted=False)
        new = next_plan(self.tasks() + [indep("T4", ["T3"])])
        sc.rebase_run(sc.SqliteRepository(path), h.plan, new, config=h.config, clock=h.clock)
        core = sc.SchedulerCore(new, sc.SqliteRepository(path), config=h.config, clock=h.clock,
                                ports=sc.Ports(execution=h.executor, verification=h.verifier))
        core.start()
        states = {k: v["state"] for k, v in core.snapshot().tasks.items()}
        self.assertEqual((states["T1"], states["T2"], states["T3"], states["T4"]),
                         ("completed", "completed", "ready", "pending"))

    def test_fingerprint_ignores_classification_and_order_of_prerequisites(self):
        a = next_plan([indep("T1"), indep("T2"), indep("T3", ["T1", "T2"])]).task("T3")
        b = next_plan([indep("T1"), indep("T2"), indep("T3", ["T2", "T1"], complexity="high")]).task("T3")
        self.assertEqual(sc.fingerprint(a), sc.fingerprint(b))
        c = indep("T3", ["T1", "T2"])
        c["verification"] = [{"type": "command", "value": "false"}]
        self.assertNotEqual(sc.fingerprint(a), sc.fingerprint(next_plan([indep("T1"), indep("T2"), c]).task("T3")))


if __name__ == "__main__":
    unittest.main()
