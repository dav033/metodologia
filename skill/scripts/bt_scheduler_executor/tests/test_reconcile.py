"""T10: a restarted executor tells the truth about processes that outlived or died with their supervisor."""
from __future__ import annotations

import json
import os
import signal
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
from bt_scheduler_executor import model as m
from bt_scheduler_executor import procinfo
from support import World, order, wait_for


def records(w, attempt_id):
    adir = Path(w.x.describe(attempt_id)["artifacts"]["dir"])
    assert wait_for(lambda: (adir / "shim.json").exists() and json.loads((adir / "shim.json").read_text()).get("child_ident"))
    # the agent has really begun (it wrote its first file) before anything is done to it
    assert wait_for(lambda: any(p.exists() for p in [q / n for q in (w.root / "ws" / "worktrees").glob(f"{attempt_id}*/")
                                                      for n in ("started.txt", "runs.txt")]))
    return adir, json.loads((adir / "shim.json").read_text())


def runs(w, attempt_id):
    wt = Path(w.x.describe(attempt_id)["handoff"]["worktree"]) if w.x.describe(attempt_id)["handoff"] else \
        next((w.root / "ws" / "worktrees").glob(f"{attempt_id}*/"))
    return (wt / "runs.txt").read_text().splitlines()


class Reconcile(unittest.TestCase):
    def test_a_live_agent_is_reattached_after_a_restart_and_finishes_once(self):
        w = World(self)
        w.x.start(order(1, "once:1.5"))
        records(w, "att-0001")
        w.restart()
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "finished")
        self.assertEqual(len(runs(w, "att-0001")), 1)
        self.assertTrue(wait_for(lambda: not w.strays(), 10), w.strays())
        self.assertEqual([e.event_id for e in w.sink.events].count("att-0001:finished"), 1)
        self.assertEqual([e.event_id for e in w.sink.events].count("att-0001:started"), 1)

    def test_an_agent_that_finished_while_no_executor_was_alive_is_finalised_from_its_exit_record(self):
        w = World(self)
        w.x.start(order(1, "once:0.6"))
        adir, _ = records(w, "att-0001")
        w.x.close()
        self.assertTrue(wait_for(lambda: (adir / "exit.json").exists()))
        if w.x.ledger.get("att-0001")["state"] in m.TERMINAL:      # the old executor won the race: nothing to reconcile
            self.skipTest("finished before close")
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("finished", "clean"))
        self.assertTrue((Path(d["handoff"]["worktree"]) / "work.txt").exists())
        self.assertEqual(len(runs(w, "att-0001")), 1)

    def test_a_vanished_agent_with_no_record_is_lost_and_its_work_is_preserved(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        adir, shim = records(w, "att-0001")
        w.x.close()
        os.killpg(shim["child_pid"], signal.SIGKILL)                       # agent and shim both die hard
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        self.assertFalse((adir / "exit.json").exists())
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "lost"))
        self.assertTrue(d["handoff"]["dirty"])
        self.assertTrue((Path(d["handoff"]["worktree"]) / "started.txt").exists())
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FAILED])

    def test_a_dead_supervisor_with_a_live_agent_is_not_trusted_the_orphan_is_stopped_first(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        _, shim = records(w, "att-0001")
        w.x.close()
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        self.assertTrue(procinfo.alive(shim["child_pid"], shim["child_ident"]))
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual(d["outcome"]["cause"], "lost")
        self.assertFalse(procinfo.alive(shim["child_pid"], shim["child_ident"]), "a second writer would be possible")

    def test_an_accepted_but_never_started_order_is_started_exactly_once_by_the_new_executor(self):
        w = World(self, autostart=False)
        w.x.start(order(1, "once:0.2"))
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.QUEUED)
        w.x = w.restart()
        w.x.start_loop()
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "finished")
        self.assertEqual(len(runs(w, "att-0001")), 1)

    def test_an_attempt_stuck_in_preparing_with_no_process_is_prepared_again_once(self):
        w = World(self, autostart=False)
        w.x.start(order(1, "once:0.2"))
        w.x.ledger.transition("att-0001", m.PREPARING, expect=(m.QUEUED,))   # the old executor died right here
        w.x = w.restart()
        w.x.start_loop()
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "finished")
        self.assertEqual(len(runs(w, "att-0001")), 1)

    def test_an_attempt_whose_shim_started_but_was_never_recorded_as_running_is_adopted_not_duplicated(self):
        w = World(self)
        w.x.start(order(1, "once:1.5"))
        records(w, "att-0001")
        w.x.close()
        with w.x.ledger._tx() as con:                                        # the crash lost the PREPARING->RUNNING txn
            con.execute("UPDATE attempts SET state='preparing', shim=NULL WHERE attempt_id='att-0001'")
            con.execute("DELETE FROM events")
        w.sink.events.clear()
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "finished")
        self.assertEqual(len(runs(w, "att-0001")), 1)
        started = w.sink.of("att-0001", m.EV_STARTED)
        self.assertEqual(len(started), 1)
        self.assertTrue(started[0].payload.get("adopted"))

    def test_an_attempt_stuck_in_settling_is_settled_once_with_the_stored_outcome(self):
        w = World(self)
        w.x.start(order(1, "commit"))
        d = w.finish("att-0001")
        with w.x.ledger._tx() as con:                                        # rewind to the moment before the terminal txn
            con.execute("UPDATE attempts SET state='settling', handoff=NULL WHERE attempt_id='att-0001'")
            con.execute("DELETE FROM events WHERE event_id='att-0001:finished'")
        w.sink.events.clear()
        w.x = w.restart()
        d2 = w.finish("att-0001")
        self.assertEqual((d2["state"], d2["outcome"]["cause"]), ("finished", "clean"))
        self.assertEqual(d2["handoff"]["snapshot_sha"], d["handoff"]["snapshot_sha"])
        self.assertEqual([e.event_id for e in w.sink.events if e.kind == m.EV_FINISHED], ["att-0001:finished"])

    def test_terminal_attempts_are_left_alone_by_a_restart(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        before = (w.x.ledger.get("att-0001"), list(w.x.ledger.events()))
        w.restart()
        self.assertEqual((w.x.ledger.get("att-0001"), list(w.x.ledger.events())), before)

    def test_query_reflects_process_reality_not_just_the_ledger(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        _, shim = records(w, "att-0001")
        self.assertEqual(w.x.query("att-0001").state, "running")
        w.x.close()
        os.killpg(shim["child_pid"], signal.SIGKILL)
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        w.x = w.build(autostart=False)
        status = w.x.query("att-0001")                       # the ledger still says RUNNING; reality says otherwise
        self.assertIn(status.state, ("settling", "failed"))
        w.x.start_loop()
        self.assertEqual(w.finish("att-0001")["outcome"]["cause"], "lost")
        self.assertEqual(w.x.query("att-0001").state, "failed")

    def test_unknown_and_rejected_attempts_have_clear_answers(self):
        w = World(self)
        self.assertEqual(w.x.query("nope").state, "not_found")
        w.x.start(order(1, executor="bogus"))
        self.assertEqual((w.x.query("att-0001").state, w.x.query("att-0001").cause), ("failed", "rejected"))

    def test_a_recycled_pid_is_never_signalled(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        _, shim = records(w, "att-0001")
        w.x.close()
        with w.x.ledger._tx() as con:        # the ledger now claims an identity that is not the running process
            row = json.loads(con.execute("SELECT shim FROM attempts WHERE attempt_id='att-0001'").fetchone()[0])
            row["ident"] = row["ident"] + "-recycled"
            con.execute("UPDATE attempts SET shim=? WHERE attempt_id='att-0001'", (json.dumps(row),))
        w.x = w.build()
        d = w.finish("att-0001")
        self.assertEqual(d["outcome"]["cause"], "lost")
        # the real shim (different identity from the recorded one) was never signalled by pid; the agent group was
        # stopped through ITS OWN recorded identity, so nothing unrelated could have been hit
        self.assertFalse(procinfo.alive(shim["child_pid"], shim["child_ident"]))


if __name__ == "__main__":
    unittest.main()
