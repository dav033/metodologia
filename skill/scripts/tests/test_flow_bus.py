import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import bt_flow_bus as bus
import bt_run_stores

RID = "a" * 32


def sql(path, *statements):
    conn = sqlite3.connect(path)
    try:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    finally:
        conn.close()


def make_run(root: Path):
    """A bitácora-layout requirement whose stores are seeded with a few real-shaped rows."""
    rdir = root / "demo" / "requirements" / "REQ-001-x"
    rdir.mkdir(parents=True)
    db = root / ".state" / "scheduler" / "demo-REQ-001.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    (db.parent / "demo-REQ-001-runtime.json").write_text(json.dumps({"runtime_id": RID}))
    mod = db.parent / f"demo-REQ-001-{RID}-modules"
    mod.mkdir()
    sql(db, "CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL, kind TEXT, plan_id TEXT, task_id TEXT, "
            "attempt_id TEXT, detail TEXT, incident_event_id TEXT)")
    for seq, at, kind, task, att, d in (
            (1, 100.0, "run_created", "", "", {"tasks": 1}),
            (2, 101.0, "dispatch_intent", "T1", "A-1", {"kind": "start"}),
            (3, 102.0, "attempt_transition", "T1", "A-1", {"from": "dispatched", "to": "running", "source": "executor"}),
            (4, 103.0, "dispatch_intent", "T1", "A-1", {"kind": "verify"}),
            (5, 104.0, "attempt_transition", "T1", "A-1", {"from": "verifying", "to": "rejected", "cause": "x"}),
            (6, 105.0, "brand_new_kind", "T1", "A-1", {})):
        sql(db, f"INSERT INTO audit VALUES ({seq}, {at}, '{kind}', 'REQ-001', '{task}', '{att}', "
                f"'{json.dumps(d)}', NULL)")
    m4 = mod / "m4-monitor.sqlite3"
    sql(m4, "CREATE TABLE normalized_events (event_id TEXT, execution_id TEXT, stream TEXT, sequence INT, "
            "offset_bytes INT, body TEXT)", "CREATE TABLE incidents (incident_id TEXT, resolution_state TEXT, body TEXT)")
    body = {"attempt_id": "A-1", "task_id": "T1", "event_type": "usage_reported", "provider": "codex", "model": "gpt",
            "received_at": "1970-01-01T00:01:42.500+00:00", "payload": {"metric_name": "total_tokens", "value": 99}}
    sql(m4, f"INSERT INTO normalized_events VALUES ('e','x','s',1,0,'{json.dumps(body)}')")
    m5 = mod / "m5-recovery.sqlite3"
    sql(m5, "CREATE TABLE decisions (seq INTEGER PRIMARY KEY, decision_id TEXT, run_id TEXT, task_id TEXT, "
            "attempt_id TEXT, cause TEXT, action TEXT)",
        "INSERT INTO decisions VALUES (1,'d','r','T1','A-1','verification_rejected','retry')")
    return rdir, db


class Bus(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir, self.db = make_run(Path(self.tmp.name))

    def kinds(self, events):
        return [(e["seq"], e["from"], e["to"], e["kind"]) for e in events]

    def test_each_record_becomes_one_causally_ordered_event(self):
        events, cursors = bus.collect(self.rdir, "demo")
        by_seq = {e["seq"]: e for e in events}
        self.assertEqual(by_seq["m1:1"]["kind"], "run_created")
        self.assertEqual((by_seq["m1:2"]["from"], by_seq["m1:2"]["to"], by_seq["m1:2"]["kind"]), ("M1", "M3", "start_order"))
        self.assertEqual((by_seq["m1:4"]["to"], by_seq["m1:4"]["kind"]), ("M6", "verify_order"))
        self.assertEqual(by_seq["m4:1"]["data"]["tokens"], {"metric": "total_tokens", "value": 99})
        self.assertEqual((by_seq["m4:1"]["from"], by_seq["m4:1"]["to"], by_seq["m4:1"]["to_part"]), ("M3", "M4", "M4.stream"))
        self.assertEqual(by_seq["m5:1"]["kind"], "recommendation")
        self.assertGreater(by_seq["m5:1"]["at_epoch"], by_seq["m1:5"]["at_epoch"])    # M5 is timed from M1's failure
        self.assertEqual([e["ord"] for e in events], sorted(e["ord"] for e in events))
        self.assertEqual(cursors["m1"], 6)

    def test_unknown_record_is_visible_not_silenced(self):
        events = bus.snapshot(self.rdir, "demo")
        unknown = [e for e in events if e["kind"] == "unknown"]
        self.assertEqual([e["data"]["audit"] for e in unknown], ["brand_new_kind"])

    def test_m6_verdict_is_not_lost_when_a_queued_request_finishes_after_the_cursor_passed_it(self):
        m6 = next(self.db.parent.glob("*-modules")) / "m6-quality.sqlite3"
        sql(m6, "CREATE TABLE requests (idempotency_key TEXT PRIMARY KEY, request_json TEXT, state TEXT, "
                "result_json TEXT, updated_at TEXT)",
            "INSERT INTO requests VALUES ('k1','{\"attempt_id\":\"A-1\",\"task_id\":\"T1\"}','queued',NULL,"
            "'1970-01-01T00:01:50+00:00')")
        first, cursors = bus.collect(self.rdir, "demo")
        self.assertNotIn("verdict", [e["kind"] for e in first])
        sql(m6, "UPDATE requests SET state='complete', result_json='{\"status\":\"accepted\"}' "
                "WHERE idempotency_key='k1'")
        later, _ = bus.collect(self.rdir, "demo", cursors)
        self.assertEqual([e["kind"] for e in later], ["verdict"])

    def test_a_recovery_cycle_is_shown_and_shown_again_when_its_state_changes(self):
        m5 = next(self.rdir.parents[2].glob(".state/scheduler/*-modules/m5-recovery.sqlite3"))
        sql(m5, "CREATE TABLE diagnostic_cycles (lineage_id TEXT PRIMARY KEY, cycle_token TEXT NOT NULL UNIQUE, state TEXT NOT NULL, "
                "identity_json TEXT NOT NULL, payload_json TEXT NOT NULL, updated_at REAL NOT NULL)",
            "INSERT INTO diagnostic_cycles VALUES ('lin-1', 'cyc-1', 'diagnosing', '{}', '{}', 200.0)")
        _, cursors = bus.collect(self.rdir, "demo")
        again, cursors = bus.collect(self.rdir, "demo", cursors)
        self.assertEqual([e for e in again if e["kind"] == "recovery_cycle"], [])
        sql(m5, "UPDATE diagnostic_cycles SET state='blocked', payload_json='{\"blocker\": {\"code\": \"diagnostic_pipeline_unavailable\"}}', "
                "updated_at=300.0")
        new, _ = bus.collect(self.rdir, "demo", cursors)
        cycles = [e for e in new if e["kind"] == "recovery_cycle"]
        self.assertEqual(len(cycles), 1)
        self.assertIn("bloqueado", cycles[0]["summary"])
        self.assertEqual(cycles[0]["data"]["blocker"], "diagnostic_pipeline_unavailable")

    def test_cursor_resumes_without_repeats_and_picks_up_new_rows(self):
        _, cursors = bus.collect(self.rdir, "demo")
        again, _ = bus.collect(self.rdir, "demo", cursors)
        self.assertEqual(again, [])
        conn = sqlite3.connect(self.db)
        conn.execute("INSERT INTO audit VALUES (7, 106.0, 'run_paused', 'REQ-001', '', '', '{}', NULL)")
        conn.commit()
        new, cursors = bus.collect(self.rdir, "demo", cursors)
        self.assertEqual(self.kinds(new), [("m1:7", "owner", "M1", "run_paused")])
        self.assertEqual(cursors["m1"], 7)

    def test_missing_stores_skip_only_that_source(self):
        for path in (bt_run_stores.paths(self.rdir)["m4"],):
            path.unlink()
        events = bus.snapshot(self.rdir, "demo")
        self.assertTrue(any(e["ref"]["store"] == "m1" for e in events))
        self.assertFalse(any(e["ref"]["store"] == "m4" for e in events))

    def test_reading_creates_nothing(self):
        before = sorted(p for p in Path(self.tmp.name).rglob("*"))
        bus.collect(self.rdir, "demo")
        self.assertEqual(sorted(Path(self.tmp.name).rglob("*")), before)


if __name__ == "__main__":
    unittest.main()


class Malformed(unittest.TestCase):
    def test_a_record_missing_its_details_degrades_to_question_marks_not_to_unknown(self):
        ctx = bus.Ctx(None, "p/REQ-1")
        rows = [{"seq": 1, "at": 10.0, "kind": "incident_observed", "task_id": "T1", "attempt_id": "A-1", "detail": "{}"},
                {"seq": 2, "at": 11.0, "kind": "run_created", "task_id": "", "attempt_id": "", "detail": "not json"}]
        events = bus.audit_events("p/REQ-1", rows, ctx)
        self.assertEqual([e["kind"] for e in events], ["incident", "run_created"])
        self.assertIn("(?)", events[0]["summary"])


class ManyRuns(unittest.TestCase):
    """Reviewer's worry: one run's high ids must never hide another run's lower ones (cursors are per run)."""

    def test_cursors_are_per_run_and_a_quiet_run_is_not_skipped(self):
        import bt_live_api as live
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir_a, db_a = make_run(root)
            rdir_b = root / "other" / "requirements" / "REQ-002-y"
            rdir_b.mkdir(parents=True)
            (rdir_a / "PLAN.md").write_text("# plan\n")
            (rdir_b / "PLAN.md").write_text("# plan\n")
            db_b = root / ".state" / "scheduler" / "other-REQ-002.db"
            sql(db_b, "CREATE TABLE audit (seq INTEGER PRIMARY KEY, at REAL, kind TEXT, plan_id TEXT, task_id TEXT, "
                      "attempt_id TEXT, detail TEXT, incident_event_id TEXT)")
            for scope in ("global",):
                events, _, cursors = live.flow_events(root, scope)
                before = len(events)
                sql(db_b, "INSERT INTO audit VALUES (3, 200.0, 'run_paused', 'REQ-002', '', '', '{}', NULL)")
                sql(db_a, "INSERT INTO audit VALUES (90, 201.0, 'run_resumed', 'REQ-001', '', '', '{}', NULL)")
                more, _, cursors = live.flow_events(root, scope, "", cursors)
                self.assertEqual(sorted(e["run"] for e in more), ["demo/REQ-001", "other/REQ-002"])
                self.assertGreater(before, 3)

    def test_provider_detail_is_quiet_and_folded_per_attempt_beyond_the_row_window(self):
        import bt_live_api as live
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir, db = make_run(root)
            (rdir / "PLAN.md").write_text("# plan\n")
            m4 = bt_run_stores.paths(rdir)["m4"]
            gap = {"attempt_id": "A-1", "task_id": "T1", "event_type": "stream_gap", "received_at": "1970-01-01T00:01:43+00:00",
                   "payload": {"cause": "malformed_json"}}
            info = {"attempt_id": "A-1", "task_id": "T1", "type": "stream_gap", "severity": "info", "first_seen_at": 103.0}
            conn = sqlite3.connect(m4)
            conn.executemany("INSERT INTO normalized_events VALUES ('g','x','s',?,0,?)",
                             [(n, json.dumps(gap)) for n in range(3 * bus.LIMIT)])
            conn.executemany("INSERT INTO incidents VALUES (?, 'open', ?)", [(f"i{n}", json.dumps(info)) for n in range(5)])
            conn.commit()
            conn.close()
            conn = sqlite3.connect(db)          # M1 hears about each info incident too: more than one window of rows
            conn.executemany("INSERT INTO audit VALUES (?, 103.5, 'incident_observed', 'REQ-001', 'T1', 'A-1', ?, NULL)",
                             [(100 + n, json.dumps({"detector_id": "stream_gap", "severity": "info"}))
                              for n in range(bus.LIMIT + 10)])
            conn.execute("INSERT INTO audit VALUES (9000, 300.0, 'run_paused', 'REQ-001', '', '', '{}', NULL)")
            conn.commit()
            conn.close()
            self.assertTrue(all(e.get("quiet") for e in bus.snapshot(rdir, "demo")
                                if e["kind"] in ("stream", "incident", "incident_detected")
                                and (e.get("data") or {}).get("event_type") != "usage_reported"))
            events, digests, cursors = live.flow_events(root, "global")
            kinds = [e["kind"] for e in events]
            self.assertIn("run_paused", kinds)                    # beyond the first LIMIT rows of M1: read to the end
            self.assertFalse({"stream", "incident", "incident_detected"} & set(kinds))
            folded, = [d for d in digests if d["attempt"] == "A-1"]
            self.assertEqual((folded["stream"], folded["incidents"], folded["types"]["malformed_json"]),
                             (3 * bus.LIMIT + 1, bus.LIMIT + 10, 3 * bus.LIMIT))
            sql(db, "INSERT INTO audit VALUES (9001, 301.0, 'run_resumed', 'REQ-001', '', '', '{}', NULL)")
            more, changed, _ = live.flow_events(root, "global", "", cursors)
            self.assertEqual(([e["kind"] for e in more], changed), (["run_resumed"], []))

    def test_a_new_revision_ledger_is_read_from_its_start(self):
        import os
        import bt_live_api as live
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir, _ = make_run(root)
            (rdir / "PLAN.md").write_text("# plan\n")

            def ledger(rev, rows, when):
                path = root / ".state" / "executor" / f"demo-REQ-001-r{rev}-x" / "ledger.db"
                path.parent.mkdir(parents=True)
                sql(path, "CREATE TABLE events (seq INTEGER PRIMARY KEY, attempt_id TEXT, kind TEXT, body TEXT, created REAL)",
                    *[f"INSERT INTO events VALUES ({n}, 'A-{rev}', 'execution_started', '{{\"task_id\": \"T1\"}}', {when + n})"
                      for n in range(1, rows + 1)])
                os.utime(path, (when, when))
            ledger(1, 3, 1_000)
            _, _, cursors = live.flow_events(root, "global")
            ledger(2, 1, 2_000)                                  # revision 2 starts its own sequence at 1
            more, _, _ = live.flow_events(root, "global", "", cursors)
            self.assertEqual([(e["attempt"], e["kind"]) for e in more], [("A-2", "execution_started")])
            self.assertNotEqual(more[0]["seq"], "m3:1")         # unique across ledgers, so a browser keeps both

    def test_m5_decision_is_timed_even_when_its_failure_is_beyond_the_row_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir, db = make_run(Path(tmp))
            conn = sqlite3.connect(db)
            conn.executemany("INSERT INTO audit VALUES (?, ?, 'run_paused', 'REQ-001', '', '', '{}', NULL)",
                             [(100 + n, 200.0 + n) for n in range(bus.LIMIT + 50)])
            conn.commit()
            conn.close()
            events, _ = bus.collect(rdir, "demo")
            m5 = next(e for e in events if e["ref"]["store"] == "m5")
            self.assertGreater(m5["at_epoch"], 100.0)          # timed from M1's rejection of A-1 at t=104
