from __future__ import annotations

import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
<<<<<<< 994fd1e9ee28e03cae2f7c757218ab60ae7fe2e1
||||||| a4936d53d3e29e51d1bd14e4f17968ee51c77dfa
<<<<<<< fe6f41a9ce94e7e0d6f2e6de6f1bc7bda2c997ac
||||||| b5fb9e730a15b5f5a36ed676d8dc6b5caae4844d
||||||| be7c0f732ccaf1b2b6139dc222cbf0fb0cd9c8fa
||||||| a4dce0b93ae5079f85d1c9469a9fead921b507dd
import unittest
=======
import unittest
import http.client
import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock
>>>>>>> 592a10ffff06f8904cf34efa124eca7973d62ea2

<<<<<<< 34ab19a2491850919dd1d00647ea1a3883471932
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
=======
import unittest
import http.client
import json
import tempfile
import threading
from pathlib import Path
from unittest.mock import Mock
>>>>>>> 3f2cfc39914a25e7888c2fc9a4d34485f8cd0bed
=======
from unittest.mock import Mock
>>>>>>> af4745f7f09edb40bc2aff39c663b988ef7c9d07
=======
from unittest.mock import Mock
>>>>>>> 6a384ab4c1c843dcde961f5b5b47db14aa3d408d

from app import GatewayRuntime
from auth import SESSION_COOKIE, OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
from stream import StreamHub
from upstream import UpstreamError


class CountingLaptop:
    def __init__(self):
        self.calls = {"health": 0, "snapshot": 0, "events": 0}
        self.online = True
        self.feed = []

    def health(self):
        self.calls["health"] += 1
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}

    def snapshot(self):
        self.calls["snapshot"] += 1
        if not self.online:
            raise UpstreamError("offline")
        return {"schemaVersion": 1, "generatedAt": "2026-10-21T12:00:00Z", "cursor": "laptop-cursor",
                "runs": [{"status": "idle"}]}

    def events(self, after):
        self.calls["events"] += 1
        feed, self.feed = self.feed, []
        return {"events": feed, "nextCursor": "c"}


def parse_sse(raw: bytes):
    out = []
    for block in raw.decode().split("\n\n"):
        fields = {}
        for line in block.splitlines():
            if line.startswith(":") or ":" not in line:
                continue
            key, _, value = line.partition(":")
            fields[key] = value.strip()
        if "event" in fields:
            out.append((fields.get("id"), fields["event"], json.loads(fields["data"])))
    return out


class HubTests(unittest.TestCase):
    def test_resume_after_last_event_id_returns_every_missed_event(self):
        hub = StreamHub()
        ids = [hub.publish({"n": n}) for n in range(5)]
        events, resync = hub.events_after(ids[1])
        self.assertFalse(resync)
        self.assertEqual([e["n"] for _, e in events], [2, 3, 4])
        self.assertEqual([i for i, _ in events], ids[2:])

    def test_resume_at_the_edge_returns_nothing(self):
        hub = StreamHub()
        last = [hub.publish({"n": n}) for n in range(3)][-1]
        self.assertEqual(hub.events_after(last), ([], False))

    def test_trimmed_backlog_or_foreign_epoch_requests_resync(self):
        hub = StreamHub(backlog_limit=3)
        ids = [hub.publish({"n": n}) for n in range(10)]
        events, resync = hub.events_after(ids[0])
        self.assertTrue(resync)
        self.assertEqual([e["n"] for _, e in events], [7, 8, 9])
        self.assertTrue(hub.events_after("deadbeef:1")[1])
        self.assertTrue(hub.events_after("garbage")[1])

    def test_offline_serves_cached_snapshot_with_its_time(self):
        now = [1000.0]
        hub = StreamHub(clock=lambda: now[0])
        hub.update_snapshot({"runs": [1]})
        now[0] = 2000.0
        hub.set_online(False)
        state = hub.read_snapshot()
        self.assertEqual(state["snapshot"], {"runs": [1]})
        self.assertEqual(state["cachedAt"], 1000.0)
        self.assertFalse(state["online"])

    def test_phone_snapshot_response_flattens_cache_and_liveness(self):
        hub = StreamHub(clock=lambda: 1000.0)
        laptop_snapshot = {"schemaVersion": 1, "generatedAt": "2026-10-21T12:00:00Z",
                           "cursor": "laptop-cursor", "runs": [{"id": "run-1"}]}
        hub.update_snapshot(laptop_snapshot)
        hub.set_online(False)

        response = hub.read_snapshot_response()

        self.assertEqual(response["schemaVersion"], 1)
        self.assertEqual(response["runs"], [{"id": "run-1"}])
        self.assertEqual(response["cachedAt"], 1000.0)
        self.assertFalse(response["online"])
        self.assertFalse(response["laptop"]["online"])
        self.assertIn("lastEventId", response)
        self.assertNotIn("snapshot", response)

    def test_wait_wakes_on_publish(self):
        hub = StreamHub()
        cursor = hub.live_cursor()
        threading.Timer(0.05, lambda: hub.publish({"n": 1})).start()
        events, _ = hub.wait_for_events(cursor, 5)
        self.assertEqual(len(events), 1)


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = GatewayConfig("http://laptop.test", "k", "t", "c", Path(self.temp.name) / "g.sqlite")
        self.laptop = CountingLaptop()
        self.runtime = GatewayRuntime(self.config, laptop=self.laptop, sender=lambda *_: None)

    def test_laptop_is_polled_once_regardless_of_clients(self):
        self.runtime.poll_once()
        baseline = dict(self.laptop.calls)
        for _ in range(50):
            self.runtime.hub.read_snapshot()
            self.runtime.hub.events_after(self.runtime.hub.live_cursor())
        self.assertEqual(self.laptop.calls, baseline)
        self.assertEqual(baseline, {"health": 1, "snapshot": 1, "events": 1})

    def test_polled_events_are_fanned_out_and_offline_keeps_cache(self):
        self.runtime.poll_once()
        cursor = self.runtime.hub.live_cursor()
        self.laptop.feed = [{"type": "run.done", "id": "e1"}]
        self.runtime.poll_once()
        events, _ = self.runtime.hub.events_after(cursor)
        self.assertEqual([e["id"] for _, e in events], ["e1"])
        self.laptop.online = False
        for _ in range(3):
            self.runtime.poll_once()
        state = self.runtime.hub.read_snapshot()
        self.assertFalse(state["online"])
        self.assertEqual(state["snapshot"]["runs"], [{"status": "idle"}])
        self.assertIsNotNone(state["cachedAt"])


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        db = str(Path(self.temp.name) / "g.sqlite")
        secret = "test-session-secret-with-more-than-32-bytes"
        self.runtime = GatewayRuntime(
            GatewayConfig("http://laptop.test", "k", "t", "c", Path(self.temp.name) / "runtime.sqlite"),
            laptop=CountingLaptop(), sender=lambda *_: None)
        self.hub = self.runtime.hub
        self.server = create_server(
            OAuthConfig(client_id="i", client_secret="s", session_secret=secret,
                        frontend_origin="https://flow.example.test", database_path=db),
            ("127.0.0.1", 0), hub=self.hub)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.hub.close)
        self.cookie = f"{SESSION_COOKIE}={SessionStore(db, secret).create_session('dav033')}"

    def get(self, path, headers=None, auth=True):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        h = dict(headers or {})
        if auth:
            h["Cookie"] = self.cookie
        conn.request("GET", path, headers=h)
        return conn, conn.getresponse()

    def read_stream(self, headers, count):
        conn, resp = self.get("/api/remote/v1/stream", headers)
        self.assertEqual(resp.status, 200)
        self.assertEqual(resp.getheader("Content-Type").split(";")[0], "text/event-stream")
        buf = b""
        while len([e for e in parse_sse(buf[:buf.rfind(b"\n\n") + 2] if b"\n\n" in buf else b"")
                   if e[1] in ("event", "resync")]) < count:
            line = resp.fp.readline()
            if not line:
                break
            buf += line
        conn.close()
        return parse_sse(buf[:buf.rfind(b"\n\n") + 2])

    def test_requires_session(self):
        for path in ("/api/remote/v1/snapshot", "/api/remote/v1/stream"):
            conn, resp = self.get(path, auth=False)
            self.assertEqual(resp.status, 401)
            conn.close()

    def test_snapshot_endpoint_serves_cache(self):
        self.runtime.poll_once()
        self.hub.set_online(False)
        conn, resp = self.get("/api/remote/v1/snapshot")
        body = json.loads(resp.read())
        conn.close()
        self.assertEqual(body["schemaVersion"], 1)
        self.assertEqual(body["runs"], [{"status": "idle"}])
        self.assertFalse(body["online"])
        self.assertFalse(body["laptop"]["online"])
        self.assertIsNotNone(body["cachedAt"])
        self.assertIn("lastEventId", body)
        self.assertNotIn("snapshot", body)
        self.assertIn("generatedAt", body)
        self.assertIn("cursor", body)

    def test_reconnect_with_last_event_id_loses_no_events(self):
        first = self.hub.publish({"n": 0})
        for n in range(1, 6):
            self.hub.publish({"n": n})
        got = self.read_stream({"Last-Event-ID": first}, 5)
        self.assertEqual([d["n"] for _, _, d in got], [1, 2, 3, 4, 5])
        # Disconnected after n=2; two more arrive while away, then the client resumes.
        resume_from = got[1][0]
        for n in range(6, 8):
            self.hub.publish({"n": n})
        got = self.read_stream({"Last-Event-ID": resume_from}, 5)
        self.assertEqual([d["n"] for _, _, d in got], [3, 4, 5, 6, 7])

    def test_live_events_reach_a_connected_client(self):
        self.hub.publish({"n": 0})
        threading.Timer(0.2, lambda: self.hub.publish({"n": 1})).start()
        got = self.read_stream({}, 1)
        self.assertEqual([d["n"] for _, _, d in got], [1])

    def test_unknown_event_id_triggers_resync_with_snapshot(self):
        self.hub.update_snapshot({"schemaVersion": 1, "generatedAt": "2026-10-21T12:00:00Z",
                                  "cursor": "cursor", "runs": ["x"]})
        got = self.read_stream({"Last-Event-ID": "stale:9"}, 1)
        self.assertEqual(got[0][1], "resync")
        self.assertEqual(got[0][2]["runs"], ["x"])
        self.assertNotIn("snapshot", got[0][2])

<<<<<<< 994fd1e9ee28e03cae2f7c757218ab60ae7fe2e1
||||||| a4936d53d3e29e51d1bd14e4f17968ee51c77dfa
<<<<<<< fe6f41a9ce94e7e0d6f2e6de6f1bc7bda2c997ac
||||||| b5fb9e730a15b5f5a36ed676d8dc6b5caae4844d
<<<<<<< df0c3380ae4eade2520bfd7c3fd1edb9a7ce2595
||||||| be7c0f732ccaf1b2b6139dc222cbf0fb0cd9c8fa
    def test_authenticated_gateway_reads_are_forwarded_to_laptop(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "gateway.sqlite")
            secret = "test-session-secret-with-at-least-32-characters"
            session = SessionStore(database, secret).create_session("dav033")
            config = OAuthConfig("client", "secret", secret, "http://localhost:3000", database)
            runtime = Mock()
            runtime.read_remote.side_effect = lambda path: {"path": path}
            server = create_server(config, ("127.0.0.1", 0), runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.addCleanup(thread.join, 2)

            paths = (
                "/api/remote/v1/attempts/a-1/review?target=demo%2FREQ-001",
                "/api/remote/v1/quotas",
                "/api/remote/v1/commands?after=&limit=10",
                "/api/remote/v1/history?after=&limit=10",
                "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1",
            )
            for path in paths:
                with self.subTest(path=path):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                    response = connection.getresponse()
                    body = json.loads(response.read())
                    connection.close()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(body["path"], path)

            runtime.read_remote.assert_any_call("/api/remote/v1/quotas")
            unauthenticated = http.client.HTTPConnection(*server.server_address, timeout=2)
            unauthenticated.request("GET", "/api/remote/v1/quotas")
            response = unauthenticated.getresponse()
            response.read()
            unauthenticated.close()
            self.assertEqual(response.status, 401)

=======
    def test_authenticated_gateway_reads_are_forwarded_to_laptop(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "gateway.sqlite")
            secret = "test-session-secret-with-at-least-32-characters"
            session = SessionStore(database, secret).create_session("dav033")
            config = OAuthConfig("client", "secret", secret, "http://localhost:3000", database)
            runtime = Mock()
            runtime.read_remote.side_effect = lambda path: {"path": path}
            server = create_server(config, ("127.0.0.1", 0), runtime=runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.addCleanup(thread.join, 2)

            paths = (
                "/api/remote/v1/attempts/a-1/review?target=demo%2FREQ-001",
                "/api/remote/v1/quotas",
                "/api/remote/v1/commands?after=&limit=10",
                "/api/remote/v1/history?after=&limit=10",
                "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1",
            )
            for path in paths:
                with self.subTest(path=path):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                    response = connection.getresponse()
                    body = json.loads(response.read())
                    connection.close()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(body["path"], path)

            runtime.read_remote.assert_any_call("/api/remote/v1/quotas")
            unauthenticated = http.client.HTTPConnection(*server.server_address, timeout=2)
            unauthenticated.request("GET", "/api/remote/v1/quotas")
            response = unauthenticated.getresponse()
            response.read()
            unauthenticated.close()
            self.assertEqual(response.status, 401)

>>>>>>> 3f2cfc39914a25e7888c2fc9a4d34485f8cd0bed

=======
    def test_authenticated_gateway_reads_are_forwarded_to_laptop(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "gateway.sqlite")
            secret = "test-session-secret-with-at-least-32-characters"
            session = SessionStore(database, secret).create_session("dav033")
            config = OAuthConfig("client", "secret", secret, "http://localhost:3000", database)
            runtime = Mock()
            runtime.read_remote.side_effect = lambda path: {"path": path}
            server = create_server(config, ("127.0.0.1", 0), runtime=runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.addCleanup(thread.join, 2)

            paths = (
                "/api/remote/v1/attempts/a-1/review?target=demo%2FREQ-001",
                "/api/remote/v1/quotas",
                "/api/remote/v1/commands?after=&limit=10",
                "/api/remote/v1/history?after=&limit=10",
                "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1",
            )
            for path in paths:
                with self.subTest(path=path):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                    response = connection.getresponse()
                    body = json.loads(response.read())
                    connection.close()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(body["path"], path)

            runtime.read_remote.assert_any_call("/api/remote/v1/quotas")
            unauthenticated = http.client.HTTPConnection(*server.server_address, timeout=2)
            unauthenticated.request("GET", "/api/remote/v1/quotas")
            response = unauthenticated.getresponse()
            response.read()
            unauthenticated.close()
            self.assertEqual(response.status, 401)
>>>>>>> af4745f7f09edb40bc2aff39c663b988ef7c9d07
=======

    def test_authenticated_gateway_reads_are_forwarded_to_laptop(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "gateway.sqlite")
            secret = "test-session-secret-with-at-least-32-characters"
            session = SessionStore(database, secret).create_session("dav033")
            config = OAuthConfig("client", "secret", secret, "http://localhost:3000", database)
            runtime = Mock()
            runtime.read_remote.side_effect = lambda path: {"path": path}
            server = create_server(config, ("127.0.0.1", 0), runtime=runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            self.addCleanup(thread.join, 2)

            paths = (
                "/api/remote/v1/attempts/a-1/review?target=demo%2FREQ-001",
                "/api/remote/v1/quotas",
                "/api/remote/v1/commands?after=&limit=10",
                "/api/remote/v1/history?after=&limit=10",
                "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1",
            )
            for path in paths:
                with self.subTest(path=path):
                    connection = http.client.HTTPConnection(*server.server_address, timeout=2)
                    connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                    response = connection.getresponse()
                    body = json.loads(response.read())
                    connection.close()
                    self.assertEqual(response.status, 200)
                    self.assertEqual(body["path"], path)

            runtime.read_remote.assert_any_call("/api/remote/v1/quotas")
            unauthenticated = http.client.HTTPConnection(*server.server_address, timeout=2)
            unauthenticated.request("GET", "/api/remote/v1/quotas")
            response = unauthenticated.getresponse()
            response.read()
            unauthenticated.close()
            self.assertEqual(response.status, 401)

>>>>>>> 6a384ab4c1c843dcde961f5b5b47db14aa3d408d

if __name__ == "__main__":
    unittest.main()
