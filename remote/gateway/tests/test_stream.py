import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from stream import StreamHub, format_sse, parse_last_event_id
from upstream import UpstreamError
from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server


class FakeLaptop:
    def __init__(self):
        self.up = True
        self.snapshot_calls = 0
        self.event_calls = 0
        self.pending = []
        self.snap = {"runs": []}
        self.read_calls = []

    def snapshot(self):
        self.snapshot_calls += 1
        if not self.up:
            raise UpstreamError("offline")
        return dict(self.snap)

    def events(self, after):
        self.event_calls += 1
        if not self.up:
            raise UpstreamError("offline")
        out, self.pending = self.pending, []
        return {"events": out, "nextCursor": f"c{self.event_calls}"}

    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}


def events_of(items):
    return [(i, d["n"]) for i, name, d in items if name == "event"]


class StreamTests(unittest.TestCase):
    def setUp(self):
        self.laptop = FakeLaptop()
        self.now = 1000.0
        self.hub = StreamHub(self.laptop, buffer_size=5, clock=lambda: self.now)

    def push(self, *ns):
        self.laptop.pending = [{"n": n} for n in ns]
        self.hub.poll_once()

    def test_reconnect_with_last_event_id_loses_no_events(self):
        self.hub.poll_once()
        sub = self.hub.subscribe()
        self.push(1, 2)
        seen = events_of(sub.drain())
        self.assertEqual(seen, [(1, 1), (2, 2)])
        sub.close()
        self.push(3, 4)  # missed while disconnected
        resumed = self.hub.subscribe(parse_last_event_id("2"))
        self.push(5)
        got = events_of(resumed.drain())
        self.assertEqual(got, [(3, 3), (4, 4), (5, 5)])

    def test_resume_beyond_buffer_resyncs_with_snapshot(self):
        self.hub.poll_once()
        self.push(*range(1, 11))
        sub = self.hub.subscribe(1)
        names = [name for _, name, _ in sub.drain()]
        self.assertEqual(names[0], "snapshot")

    def test_resume_at_head_replays_nothing(self):
        self.push(1, 2)
        sub = self.hub.subscribe(2)
        self.assertEqual(events_of(sub.drain()), [])

    def test_offline_serves_cached_snapshot_with_time(self):
        self.laptop.snap = {"runs": [{"id": "r1"}]}
        self.hub.poll_once()
        self.now = 1100.0
        self.laptop.up = False
        self.hub.poll_once()
        cached = self.hub.cached_snapshot()
        self.assertEqual(cached["snapshot"], {"runs": [{"id": "r1"}]})
        self.assertEqual(cached["cachedAt"], 1000.0)
        self.assertTrue(cached["stale"])

    def test_laptop_polled_once_regardless_of_clients(self):
        subs = [self.hub.subscribe() for _ in range(10)]
        for _ in range(10):
            self.hub.cached_snapshot()
        self.assertEqual(self.laptop.snapshot_calls, 0)
        self.hub.poll_once()
        self.assertEqual((self.laptop.snapshot_calls, self.laptop.event_calls), (1, 1))
        self.assertEqual(self.hub.subscriber_count(), 10)
        for s in subs:
            s.close()
        self.assertEqual(self.hub.subscriber_count(), 0)

    def test_status_broadcast_on_transition(self):
        self.hub.poll_once()
        sub = self.hub.subscribe()
        sub.drain()
        self.laptop.up = False
        self.hub.poll_once()
        self.assertEqual([d["online"] for _, n, d in sub.drain() if n == "status"], [False])

    def test_format_and_parse(self):
        self.assertEqual(format_sse(3, "event", {"a": 1}), b'id: 3\nevent: event\ndata: {"a":1}\n\n')
        self.assertIsNone(parse_last_event_id("abc"))
        self.assertIsNone(parse_last_event_id(None))
        self.assertEqual(parse_last_event_id(" 7 "), 7)

    def test_authenticated_read_models_reach_laptop_at_http_entrypoint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "gateway.sqlite"
            oauth = OAuthConfig("client", "client-secret", "test-session-secret-with-more-than-32-bytes",
                                "https://flow.example.test", str(database))
            session = SessionStore(str(database), oauth.session_secret).create_session("owner")
            laptop = FakeLaptop()
            config = GatewayConfig("http://127.0.0.1:18765", "test-key", "test-token", "test-chat", database)
            runtime = create_runtime(config, laptop=laptop, sender=lambda _message: None)
            server = create_server(oauth, ("127.0.0.1", 0), runtime=runtime)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            paths = ["/api/remote/v1/attempts/a1/review", "/api/remote/v1/history",
                     "/api/remote/v1/quotas",
                     "/api/remote/v1/commands?after=&limit=100",
                     "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1"]
            try:
                for path in paths:
                    connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                    response = connection.getresponse()
                    payload = json.loads(response.read())
                    self.assertEqual(response.status, 200)
                    self.assertEqual(payload["source"], path)
                self.assertEqual(laptop.read_calls, paths)
            finally:
                connection.close()
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

if __name__ == "__main__":
    unittest.main()
