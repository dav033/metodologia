<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
import unittest
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
import unittest
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
import unittest
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
<<<<<<< c0a5e47ed090adf0bb7ad5ad7bdf2c67e37ce775
||||||| 03ca13926945e4dcf4ecdc4e34dddc55b76da7e1
from pathlib import Path
=======
from pathlib import Path
import http.client
import json
>>>>>>> ede87253b5f40c74d13b25da89f0c8ea70ac0e63
=======
import tempfile
import threading
import http.client
import json
from pathlib import Path
import http.client
import json
>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6
=======
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======
import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path
>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603

from stream import StreamHub, format_sse, parse_last_event_id
from upstream import UpstreamError
<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
||||||| 03ca13926945e4dcf4ecdc4e34dddc55b76da7e1
from app import create_runtime
from config import GatewayConfig
from stream import SnapshotEventStream
=======
from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
from stream import SnapshotEventStream
>>>>>>> ede87253b5f40c74d13b25da89f0c8ea70ac0e63
from upstream import UpstreamError
=======
from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6
=======
from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======
from app import create_runtime
from auth import OAuthConfig, SessionStore
from config import GatewayConfig
from server import create_server
>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603


class FakeLaptop:
    def __init__(self):
        self.up = True
        self.snapshot_calls = 0
        self.event_calls = 0
        self.pending = []
        self.snap = {"runs": []}
<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
||||||| 03ca13926945e4dcf4ecdc4e34dddc55b76da7e1

    def health(self):
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}
=======
        self.read_calls = []

    def health(self):
        if not self.online:
            raise UpstreamError("offline")
        return {"status": "ok"}
>>>>>>> ede87253b5f40c74d13b25da89f0c8ea70ac0e63

=======
        self.read_calls = []
>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6

=======
        self.read_calls = []
>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a

=======
        self.read_calls = []
>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603

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

<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}

=======
    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}

    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}

>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6
=======
    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}

>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======
    def read_model(self, path):
        self.read_calls.append(path)
        return {"source": path}

>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603

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

<<<<<<< 0c2b75045d1c088b366d290e1236f82a6204b982
||||||| dc60481f471192cacb7e098604adb9e83f6ca85a
<<<<<<< b21af576095cc9c033b3326647f1e1a84fb3152f
||||||| d59402f2311e71a7d7b249554f3f9507983622f2
<<<<<<< 725ff33443950b7b5e0842d1366bc81f05c1a57c
||||||| 788d3dd30328bfccc7880c00baf691d188b0b6ed
    def test_authenticated_http_entrypoint_relays_required_read_models(self) -> None:
        database = Path(self.temp_dir.name) / "auth.sqlite"
        oauth = OAuthConfig("client", "client-secret", "test-session-secret-with-more-than-32-bytes",
                            "https://flow.example.test", str(database))
        session = SessionStore(str(database), oauth.session_secret).create_session("owner")
        server = create_server(oauth, ("127.0.0.1", 0), runtime=self.runtime)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
        paths = ["/api/remote/v1/attempts/a1/review", "/api/remote/v1/quotas",
                 "/api/remote/v1/commands?after=&limit=100",
                 "/api/remote/v1/routes?target=demo%2FREQ-001&task=T1"]
        try:
            for path in paths:
                connection.request("GET", path, headers={"Cookie": f"flow_session={session}"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(payload["source"], path)
            self.assertEqual(self.laptop.read_calls, paths)
        finally:
            connection.close()
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

=======
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
            paths = ["/api/remote/v1/attempts/a1/review", "/api/remote/v1/quotas",
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
>>>>>>> 7bab8d3fc65eb4681168829156ff0d7510a656a6
=======
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
            paths = ["/api/remote/v1/attempts/a1/review", "/api/remote/v1/quotas",
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
>>>>>>> ff6d46bc29f4b6a862628af4bad381b77e5a9d7a
=======
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
>>>>>>> 4714cf64fe4c866730eb7ff2dc4f69bf7c4a5603

if __name__ == "__main__":
    unittest.main()
