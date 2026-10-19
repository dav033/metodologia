import http.client
import json
import sqlite3
import statistics
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import bt_core
import bt_live_api as live
import bt_server
import test_flow_bus as fb

PLAN = {"schema_version": "1.1.0", "plan_id": "REQ-001", "revision": 1,
        "milestones": [{"id": "M1", "title": "First"}],
        "tasks": [{"id": "T1", "milestone_id": "M1", "title": "Do one", "after": [], "complexity": "high"}]}


def seed_running_state(db: Path, rdir: Path, now: float):
    doc = {"tasks": {"T1": {"state": "active", "attempts": ["A-1"]}},
           "attempts": {"A-1": {"id": "A-1", "task_id": "T1", "number": 1, "state": "running", "executor": "",
                                "created_at": now - 90, "updated_at": now - 5, "last_event_at": now - 2}}}
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE state (id INTEGER PRIMARY KEY, version INTEGER NOT NULL, doc TEXT NOT NULL)")
    conn.execute("INSERT INTO state VALUES (1, 1, ?)", (json.dumps(doc),))
    conn.commit()
    conn.close()
    projection = {"authority": "scheduler", "projection": True, "req": "REQ-001", "status": "running",
                  "heartbeat_at": "2026-10-18T11:00:00+00:00",
                  "plan_ref": {"plan_id": "REQ-001", "revision": 1, "sha256": "a" * 64},
                  "tasks": [{"id": "T1", "title": "Do one", "status": "in_progress", "scheduler_state": "active",
                             "attempts": 1, "provider": "claude", "model": "sonnet", "effort": "high",
                             "profile": "claude-work", "route_status": "assigned"}]}
    (rdir / "RUN.projection.json").write_text(json.dumps(projection), encoding="utf-8")
    (rdir / "PLAN.json").write_text(json.dumps(PLAN), encoding="utf-8")
    (rdir / "SPEC.md").write_text("# Spec — REQ-001 — Demo\n", encoding="utf-8")
    (rdir / "PLAN.md").write_text("---\nstatus: approved\n---\n# Plan\n", encoding="utf-8")


class LiveBase(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.rdir, self.db = fb.make_run(self.root)
        conn = sqlite3.connect(self.db)
        conn.execute("DELETE FROM audit WHERE kind = 'brand_new_kind'")
        conn.commit()
        conn.close()
        seed_running_state(self.db, self.rdir, time.time())
        for target, attr, value in ((bt_server, "ROOT", self.root), (bt_core, "ROOT", self.root),
                                    (bt_server, "STATE", self.root / ".state"), (bt_core, "STATE", self.root / ".state")):
            p = patch.object(target, attr, value)
            p.start()
            self.addCleanup(p.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        self.port = self.httpd.server_address[1]
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def get(self, path, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        c.request("GET", path, headers=headers or {})
        r = c.getresponse()
        return r.status, r.read().decode()

    def add_audit(self, seq, kind, at=None, task="T1", attempt="A-1", detail=None):
        conn = sqlite3.connect(self.db)
        conn.execute("INSERT INTO audit VALUES (?, ?, ?, 'REQ-001', ?, ?, ?, NULL)",
                     (seq, at or time.time(), kind, task, attempt, json.dumps(detail or {})))
        conn.commit()
        conn.close()


def read_frames(resp, want, timeout=4.0):
    """Frames (event, id, data) read from an SSE response until `want(frame)` or the timeout."""
    deadline, event, ident = time.monotonic() + timeout, None, ""
    while time.monotonic() < deadline:
        line = resp.fp.readline().decode()
        if line.startswith("event: "):
            event = line[7:].strip()
        elif line.startswith("id: "):
            ident = line[4:].strip()
        elif line.startswith("data: "):
            frame = (event, ident, json.loads(line[6:]))
            if want(frame):
                return frame
    return None


class NowAndReplay(LiveBase):
    def test_now_lists_the_live_attempt_with_its_progress(self):
        status, body = self.get("/api/now")
        items = json.loads(body)["items"]
        self.assertEqual(status, 200)
        self.assertEqual([(i["project"], i["req_id"], i["task"]) for i in items], [("demo", "REQ-001", "T1")])
        self.assertTrue(items[0]["attempt"]["live"])
        self.assertEqual(items[0]["progress"], {"done": 0, "total": 1})

    def test_flow_replay_is_scoped_and_resumable(self):
        events = json.loads(self.get("/api/flow?scope=run:demo/REQ-001")[1])["events"]
        self.assertGreater(len(events), 4)
        mid = events[2]["ord"]
        rest = json.loads(self.get(f"/api/flow?scope=run:demo/REQ-001&after={mid}")[1])["events"]
        self.assertEqual([e["ord"] for e in rest], [e["ord"] for e in events[3:]])
        other = json.loads(self.get("/api/flow?scope=project:nope")[1])["events"]
        self.assertEqual(other, [])
        only_task = json.loads(self.get("/api/flow?scope=task:demo/REQ-001/T9")[1])["events"]
        self.assertEqual(only_task, [])


class Fingerprint(LiveBase):
    def test_a_module_store_change_moves_the_plans_fingerprint(self):
        import bt_planstatus as ps
        import bt_run_stores
        before = ps.fingerprint(self.root)
        m4 = bt_run_stores.paths(self.rdir)["m4"]
        conn = sqlite3.connect(m4)
        conn.execute("INSERT INTO normalized_events VALUES ('e2','x','s',2,0,'{}')")
        conn.commit()
        conn.close()
        self.assertNotEqual(ps.fingerprint(self.root), before)


class Sse(LiveBase):
    def open(self, scope="global", headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=6)
        c.request("GET", f"/live?scope={scope}", headers=headers or {})
        resp = c.getresponse()
        self.addCleanup(c.close)
        return resp

    def test_first_frame_is_now_and_a_new_audit_row_arrives_as_flow(self):
        resp = self.open()
        self.assertEqual(resp.getheader("Content-Type").split(";")[0], "text/event-stream")
        first = read_frames(resp, lambda f: f[0] == "now")
        self.assertIn("REQ-001 T1", first[2]["html"]["bar"])
        self.assertIn("ncard", first[2]["html"]["cards"])
        self.add_audit(50, "run_paused")
        frame = read_frames(resp, lambda f: f[0] == "flow")
        self.assertEqual((frame[2]["kind"], frame[2]["from"]), ("run_paused", "owner"))
        self.assertEqual(frame[1], frame[2]["ord"])

    def test_last_event_id_resumes_after_it(self):
        events = json.loads(self.get("/api/flow?scope=global")[1])["events"]
        resp = self.open(headers={"Last-Event-ID": events[-3]["ord"]})
        got = []
        deadline = time.monotonic() + 3
        while len(got) < 2 and time.monotonic() < deadline:
            frame = read_frames(resp, lambda f: f[0] == "flow", 1.5)
            if frame:
                got.append(frame[2]["ord"])
        self.assertEqual(got, [events[-2]["ord"], events[-1]["ord"]])

    def test_latency_p95_under_one_second(self):
        resp = self.open()
        read_frames(resp, lambda f: f[0] == "now")
        samples = []
        for n in range(10):
            seq = 100 + n
            sent = time.time()
            self.add_audit(seq, "run_paused", at=sent)
            frame = read_frames(resp, lambda f, s=seq: f[0] == "flow" and f[2]["seq"] == f"m1:{s}", 3)
            self.assertIsNotNone(frame, f"event {seq} never arrived")
            samples.append(time.time() - sent)
        p95 = statistics.quantiles(samples, n=20)[-1]
        self.assertLess(p95, 1.0, samples)

    def test_client_cap_returns_503_and_disconnect_keeps_server_alive(self):
        with patch.object(live, "_slots", threading.BoundedSemaphore(0)):
            self.assertEqual(self.get("/live")[0], 503)
        resp = self.open()
        read_frames(resp, lambda f: f[0] == "now")
        resp.close()
        self.assertEqual(self.get("/api/now")[0], 200)


if __name__ == "__main__":
    unittest.main()
