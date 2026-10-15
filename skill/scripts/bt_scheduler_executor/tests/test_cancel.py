"""T9: cancellation is fenced by token, idempotent and safe in every state."""
from __future__ import annotations

import json
import os
import signal
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
from bt_scheduler_executor import model as m
from bt_scheduler_executor import procinfo
from support import World, order, wait_for


def shim_of(w, attempt_id):
    path = Path(w.x.describe(attempt_id)["artifacts"]["dir"]) / "shim.json"
    wait_for(lambda: path.exists() and json.loads(path.read_text()).get("child_ident"))
    return json.loads(path.read_text())


class Cancel(unittest.TestCase):
    def test_a_queued_attempt_is_cancelled_and_never_spawned(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, max_running=1, grace_seconds=1, timeout_seconds=60))
        w.x.start(order(1, "sleep:30"))
        w.x.start(order(2, "ok"))
        self.assertTrue(wait_for(lambda: w.x.ledger.get("att-0001")["state"] == m.RUNNING))
        r = w.x.cancel("att-0002", 1, "cancel-2", "no longer needed")
        self.assertEqual(r.status, "accepted")
        d2 = w.finish("att-0002")
        self.assertEqual((d2["state"], d2["outcome"]["cause"]), ("cancelled", "cancelled"))
        self.assertEqual(w.sink.kinds("att-0002"), [m.EV_CANCELLED])
        self.assertEqual(len(w.driver.prepared), 1)
        self.assertEqual(d2["handoff"]["status"], "none")
        self.assertFalse(list((w.root / "ws" / "worktrees").glob("att-0002*")))
        w.x.cancel("att-0001", 1, "cancel-1")
        w.finish("att-0001")

    def test_a_running_attempt_is_stopped_its_work_preserved_and_one_cancelled_event_emitted(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        shim = shim_of(w, "att-0001")
        wt = Path(w.x.ledger.get("att-0001")["workspace"]["path"])
        self.assertTrue(wait_for(lambda: (wt / "started.txt").exists()), "agent did not reach its running state")
        self.assertEqual(w.x.cancel("att-0001", 1, "k1", "operator").status, "accepted")
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"], d["outcome"]["signal"]), ("cancelled", "cancelled", "SIGTERM"))
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_CANCELLED])
        self.assertFalse(procinfo.alive(shim["child_pid"], shim["child_ident"]))
        self.assertFalse(procinfo.alive(shim["pid"], shim["ident"]))
        self.assertTrue(d["handoff"]["dirty"])                               # started.txt was written before the stop
        self.assertTrue((Path(d["handoff"]["worktree"]) / "started.txt").exists())
        self.assertTrue(wait_for(lambda: not w.strays(), 10), w.strays())      # nothing of the agent is left running
        self.assertIn("work", Path(d["artifacts"]["handoff"], "continue.md").read_text().lower())

    def test_an_agent_that_ignores_sigterm_is_killed_after_the_grace_period(self):
        w = World(self)
        w.x.start(order(1, "stubborn:60"))
        shim_of(w, "att-0001")
        wt = Path(w.x.ledger.get("att-0001")["workspace"]["path"])
        self.assertTrue(wait_for(lambda: (wt / "started.txt").exists()), "agent did not install its SIGTERM handler")
        t0 = time.monotonic()
        w.x.cancel("att-0001", 1, "k1")
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "cancelled")
        self.assertLess(time.monotonic() - t0, 20)
        self.assertEqual(d["outcome"]["signal"], "SIGKILL")

    def test_processes_the_agent_left_behind_die_with_it(self):
        w = World(self)
        w.x.start(order(1, "grandchild:60"))
        d0 = w.x.describe("att-0001")
        wt = lambda: next((w.root / "ws" / "worktrees").glob("att-0001*/grandchild.pid"), None)
        self.assertTrue(wait_for(lambda: wt() is not None))
        gpid = int(wt().read_text())
        w.x.cancel("att-0001", 1, "k1")
        w.finish("att-0001")
        self.assertTrue(wait_for(lambda: not procinfo.start_ident(gpid), 10), "a grandchild is still running")
        del d0

    def test_cancel_after_the_attempt_ended_changes_nothing(self):
        w = World(self)
        w.x.start(order(1, "ok"))
        d = w.finish("att-0001")
        before = (len(w.sink.events), w.x.ledger.events("att-0001"))
        r = w.x.cancel("att-0001", 1, "late")
        self.assertEqual((r.status, r.detail), ("duplicate", "already finished"))
        self.assertEqual(w.x.ledger.get("att-0001")["state"], "finished")
        self.assertEqual((len(w.sink.events), w.x.ledger.events("att-0001")), before)
        self.assertEqual(d["state"], "finished")

    def test_a_wrong_token_is_rejected_and_the_attempt_carries_on(self):
        w = World(self)
        w.x.start(order(1, "sleep:1", token=5))
        r = w.x.cancel("att-0001", 6, "k1")
        self.assertEqual((r.status, r.code), ("rejected", "TOKEN_MISMATCH"))
        self.assertFalse(w.x.ledger.get("att-0001")["cancel_requested"])
        self.assertEqual(w.finish("att-0001")["state"], "finished")

    def test_cancelling_twice_is_one_cancellation_and_one_terminal_event(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        shim_of(w, "att-0001")
        self.assertEqual(w.x.cancel("att-0001", 1, "k1").status, "accepted")
        self.assertEqual(w.x.cancel("att-0001", 1, "k1").status, "duplicate")
        w.finish("att-0001")
        terminal = [e for e in w.sink.events if e.kind in (m.EV_CANCELLED, m.EV_FINISHED, m.EV_FAILED)]
        self.assertEqual(len(terminal), 1)

    def test_a_cancel_that_arrives_while_the_attempt_is_still_preparing_stops_it_before_any_process(self):
        w = World(self)
        gate, entered = threading.Event(), threading.Event()
        original = w.x.workspaces.allocate

        def slow(request):
            entered.set()
            gate.wait(20)
            return original(request)
        w.x.workspaces.allocate = slow
        w.x.start(order(1, "sleep:60"))
        self.assertTrue(entered.wait(20))
        self.assertEqual(w.x.ledger.get("att-0001")["state"], m.PREPARING)
        self.assertEqual(w.x.cancel("att-0001", 1, "k1").status, "accepted")
        gate.set()
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("cancelled", "cancelled"))
        self.assertEqual(w.driver.prepared, [])                                   # no launch was ever prepared
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_CANCELLED])
        self.assertEqual(d["handoff"]["status"], "captured")                      # the worktree existed: its (empty) state is kept
        self.assertTrue(d["handoff"]["empty"])

    def test_cancel_racing_the_natural_exit_always_ends_with_exactly_one_terminal_event(self):
        w = World(self, config=ex.Config(poll_seconds=0.01, grace_seconds=1, timeout_seconds=60, max_running=4))
        outcomes = []
        for n in range(1, 13):
            w.x.start(order(n, "marker:x"))
            time.sleep((n % 6) * 0.04)
            w.x.cancel(f"att-{n:04d}", 1, f"k{n}")
        self.assertTrue(w.x.wait_idle(60))
        for n in range(1, 13):
            row = w.x.ledger.get(f"att-{n:04d}")
            terminal = [e for e in w.sink.events if e.attempt_id == f"att-{n:04d}"
                        and e.kind in (m.EV_CANCELLED, m.EV_FINISHED, m.EV_FAILED)]
            self.assertEqual(len(terminal), 1, (n, [e.kind for e in w.sink.events if e.attempt_id == f"att-{n:04d}"]))
            self.assertIn(row["state"], (m.FINISHED, m.CANCELLED), row["state"])
            outcomes.append(row["state"])
        self.assertTrue(set(outcomes) <= {m.FINISHED, m.CANCELLED})

    def test_if_the_shim_vanishes_after_a_cancel_the_orphan_is_stopped_and_the_attempt_is_cancelled(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        shim = shim_of(w, "att-0001")
        w.x.close()                                          # stop supervising so nothing signals the shim for us
        os.kill(shim["pid"], signal.SIGKILL)
        self.assertTrue(wait_for(lambda: not procinfo.alive(shim["pid"], shim["ident"])))
        self.assertTrue(procinfo.alive(shim["child_pid"], shim["child_ident"]))   # the agent is now an orphan
        w.x.ledger.request_cancel("att-0001", "k1", "operator")       # the intent was recorded before the supervisor died
        w.x = w.build(autostart=False)
        w.x.start_loop()
        d = w.finish("att-0001")
        self.assertEqual(d["state"], "cancelled")
        self.assertFalse(procinfo.alive(shim["child_pid"], shim["child_ident"]))

    def test_cancel_reason_is_stored_bounded(self):
        w = World(self)
        w.x.start(order(1, "sleep:30"))
        w.x.cancel("att-0001", 1, "k1", "r" * 1000)
        self.assertEqual(len(w.x.ledger.get("att-0001")["cancel_reason"]), 200)
        w.finish("att-0001")


if __name__ == "__main__":
    unittest.main()
