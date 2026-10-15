"""T2: durable ledger — unique keys, checked transitions, atomic terminal event, concurrency from threads and processes."""
from __future__ import annotations

import multiprocessing
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import model as m
from bt_scheduler_executor.ledger import Ledger


def _insert(args):
    path, n = args
    led = Ledger(path)
    req = support.order(1, key="same-key", attempt_id="att-0001")
    try:
        _, created = led.insert(req, dirname="d1", state=m.QUEUED, route={"provider": "p", "model": "m"})
        return "created" if created else "replay"
    except ex.ExecutorError as error:
        return error.code


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "l.db"
        self.led = Ledger(self.path)

    def add(self, n=1, **kw):
        return self.led.insert(support.order(n), dirname=f"d{n}", state=kw.pop("state", m.QUEUED),
                               route={"provider": "p", "model": "m", "profile": "", "effort": "", "reference": "r"}, **kw)

    def test_an_insert_is_created_once_and_replays_return_the_same_row(self):
        row, created = self.add()
        again, created2 = self.add()
        self.assertTrue(created)
        self.assertFalse(created2)
        self.assertEqual(row["attempt_id"], again["attempt_id"])
        self.assertEqual(self.led.count((m.QUEUED,)), 1)

    def test_the_same_key_with_another_order_is_a_conflict(self):
        self.add()
        other = support.order(1, scenario="crash")
        with self.assertRaises(ex.ExecutorError) as caught:
            self.led.insert(other, dirname="d1", state=m.QUEUED)
        self.assertEqual(caught.exception.code, "KEY_CONFLICT")

    def test_the_same_attempt_id_under_another_key_is_a_conflict(self):
        self.add()
        with self.assertRaises(ex.ExecutorError) as caught:
            self.led.insert(support.order(1, key="another-key"), dirname="d1", state=m.QUEUED)
        self.assertEqual(caught.exception.code, "KEY_CONFLICT")

    def test_a_full_queue_is_persisted_as_a_stable_rejection(self):
        self.add(1, max_queued=1)
        row, _ = self.add(2, max_queued=1)
        self.assertEqual(row["state"], m.REJECTED)
        self.assertEqual(row["rejection"]["code"], "QUEUE_FULL")
        again, created = self.add(2, max_queued=100)
        self.assertFalse(created)
        self.assertEqual(again["state"], m.REJECTED)

    def test_an_event_backlog_stops_new_work(self):
        for i in range(3):
            self.led.add_event(ex.TechnicalEvent(f"e{i}", m.EV_STARTED, "P", 1, "T", "a", 1, "t"))
        row, _ = self.add(1, max_backlog=3)
        self.assertEqual(row["rejection"]["code"], "QUEUE_FULL")

    def test_transitions_are_compare_and_set_along_legal_edges(self):
        self.add()
        self.assertTrue(self.led.transition("att-0001", m.PREPARING, expect=(m.QUEUED,)))
        self.assertFalse(self.led.transition("att-0001", m.PREPARING, expect=(m.QUEUED,)))      # lost the race
        with self.assertRaises(ValueError):
            self.led.transition("att-0001", m.FINISHED, expect=(m.RUNNING,))                      # no such edge
        self.assertEqual(self.led.get("att-0001")["state"], m.PREPARING)

    def test_a_terminal_state_has_no_way_out(self):
        self.add()
        for state in (m.PREPARING, m.RUNNING, m.SETTLING, m.FINISHED):
            prev = {m.PREPARING: m.QUEUED, m.RUNNING: m.PREPARING, m.SETTLING: m.RUNNING, m.FINISHED: m.SETTLING}[state]
            self.assertTrue(self.led.transition("att-0001", state, expect=(prev,)))
        for target in m.STATES:
            for prev in m.TERMINAL:
                if target in m.TRANSITIONS[prev]:
                    self.fail("terminal edge exists")
        self.assertFalse(self.led.transition("att-0001", m.SETTLING, expect=(m.RUNNING,)))

    def test_terminal_state_and_its_event_are_one_transaction(self):
        self.add()
        self.led.transition("att-0001", m.PREPARING, expect=(m.QUEUED,))
        self.led.transition("att-0001", m.RUNNING, expect=(m.PREPARING,))
        self.led.transition("att-0001", m.SETTLING, expect=(m.RUNNING,))
        event = ex.TechnicalEvent("att-0001:finished", m.EV_FINISHED, "REQ-T", 1, "T1", "att-0001", 1, "t")
        self.assertTrue(self.led.transition("att-0001", m.FINISHED, expect=(m.SETTLING,), event=event))
        self.assertFalse(self.led.transition("att-0001", m.FINISHED, expect=(m.SETTLING,), event=event))
        self.assertEqual([e["event_id"] for e in self.led.events("att-0001")], ["att-0001:finished"])

    def test_events_are_idempotent_ordered_and_marked_delivered(self):
        for i in (1, 2, 2, 3):
            self.led.add_event(ex.TechnicalEvent(f"e{i}", m.EV_STARTED, "P", 1, "T", "a", 1, "t"))
        self.assertEqual([e.event_id for e in self.led.pending_events(10)], ["e1", "e2", "e3"])
        self.led.mark_delivered("e1")
        self.assertEqual([e.event_id for e in self.led.pending_events(10)], ["e2", "e3"])
        self.assertEqual(self.led.undelivered(), 2)

    def test_cancel_intent_is_recorded_once(self):
        self.add()
        self.assertEqual(self.led.request_cancel("att-0001", "k1", "why"), "recorded")
        self.assertEqual(self.led.request_cancel("att-0001", "k2", "again"), "duplicate")
        self.assertEqual(self.led.request_cancel("nope", "k", ""), "unknown")
        self.assertTrue(self.led.get("att-0001")["cancel_requested"])
        self.led.transition("att-0001", m.SETTLING, expect=(m.QUEUED,))
        self.led.transition("att-0001", m.CANCELLED, expect=(m.SETTLING,))
        self.assertEqual(self.led.request_cancel("att-0001", "k3", ""), "terminal")

    def test_the_run_is_bound_by_the_first_order(self):
        self.assertTrue(self.led.bind_run("REQ-T", 1))
        self.assertTrue(self.led.bind_run("REQ-T", 1))
        self.assertFalse(self.led.bind_run("REQ-T", 2))
        self.assertFalse(self.led.bind_run("REQ-OTHER", 1))

    def test_data_survives_a_new_connection_and_a_new_object(self):
        self.add()
        self.led.transition("att-0001", m.PREPARING, expect=(m.QUEUED,), workspace={"path": "/w"})
        fresh = Ledger(self.path)
        row = fresh.get("att-0001")
        self.assertEqual((row["state"], row["workspace"]), (m.PREPARING, {"path": "/w"}))

    def test_only_declared_columns_are_mutable(self):
        self.add()
        with self.assertRaises(ValueError):
            self.led.update("att-0001", state="finished")
        with self.assertRaises(ValueError):
            self.led.update("att-0001", idem_key="x")

    def test_threads_racing_to_insert_one_key_produce_one_row(self):
        results = []

        def go():
            try:
                _, created = Ledger(self.path).insert(support.order(1), dirname="d1", state=m.QUEUED)
                results.append(created)
            except ex.ExecutorError as error:
                results.append(error.code)
        threads = [threading.Thread(target=go) for _ in range(12)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(results.count(True), 1, results)
        self.assertEqual(self.led.count((m.QUEUED,)), 1)

    def test_processes_racing_to_insert_one_key_produce_one_row(self):
        with multiprocessing.get_context("spawn").Pool(4) as pool:
            results = pool.map(_insert, [(str(self.path), i) for i in range(8)])
        self.assertEqual(results.count("created"), 1, results)
        self.assertEqual(self.led.count((m.QUEUED,)), 1)

    def test_an_unusable_path_is_a_ledger_error(self):
        blocker = Path(self.tmp.name) / "file"
        blocker.write_text("x")
        with self.assertRaises(ex.ExecutorError) as caught:
            Ledger(blocker / "sub" / "l.db")
        self.assertEqual(caught.exception.code, "LEDGER_ERROR")


if __name__ == "__main__":
    unittest.main()
