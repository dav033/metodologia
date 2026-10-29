"""The panel relays `p<port>.localhost` requests to the test versions it runs, and only to them (pictures REQ-021)."""
from __future__ import annotations

import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_version_proxy as proxy


class Version(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"version {self.path} host={self.headers.get('Host')}".encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        data = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        self.send_response(201)
        self.end_headers()
        self.wfile.write(b"got " + data)

    def log_message(self, *args):
        pass


class Panel(BaseHTTPRequestHandler):
    def send(self, body, status=200, ctype="text/plain"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not proxy.serve(self):
            self.send("panel")

    do_POST = do_GET

    def log_message(self, *args):
        pass


def serve(handler) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


class VersionProxy(unittest.TestCase):
    def setUp(self):
        self.version, self.panel = serve(Version), serve(Panel)
        self.addCleanup(self.version.shutdown)
        self.addCleanup(self.panel.shutdown)
        self.vport, self.pport = self.version.server_address[1], self.panel.server_address[1]

    def ask(self, path: str, host: str, data: bytes | None = None) -> tuple[int, bytes]:
        request = urllib.request.Request(f"http://127.0.0.1:{self.pport}{path}", data=data, headers={"Host": host})
        try:
            with urllib.request.urlopen(request, timeout=10) as reply:
                return reply.status, reply.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def test_the_host_names_the_port(self):
        self.assertEqual(proxy.target_port("p3000.localhost:8765"), 3000)
        self.assertEqual(proxy.target_port("P3001.LOCALHOST"), 3001)
        for host in ("localhost:8765", "127.0.0.1:8765", "p3000.example.com", "x3000.localhost", ""):
            self.assertIsNone(proxy.target_port(host), host)

    def test_a_running_version_is_relayed_with_its_host_and_a_body(self):
        host = f"p{self.vport}.localhost:{self.pport}"
        with patch.object(proxy, "running_ports", return_value={self.vport}):
            self.assertEqual(self.ask("/3d?x=1", host), (200, f"version /3d?x=1 host={host}".encode()))
            self.assertEqual(self.ask("/api", host, data=b"payload"), (201, b"got payload"))

    def test_only_running_test_versions_are_relayed_and_the_panel_stays_the_panel(self):
        with patch.object(proxy, "running_ports", return_value=set()):
            status, body = self.ask("/", f"p{self.vport}.localhost:{self.pport}")
        self.assertEqual(status, 404)
        self.assertIn("no está en marcha", body.decode())
        self.assertEqual(self.ask("/", f"localhost:{self.pport}"), (200, b"panel"))

    def test_a_version_that_does_not_answer_yet_says_so(self):
        self.version.shutdown()
        self.version.server_close()
        with patch.object(proxy, "running_ports", return_value={self.vport}):
            status, body = self.ask("/", f"p{self.vport}.localhost:{self.pport}")
        self.assertEqual(status, 502)
        self.assertIn("todavía no responde", body.decode())


if __name__ == "__main__":
    unittest.main()
