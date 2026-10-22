"""The remote listener serves the panel's pages and actions behind the gateway key and an allow-list."""
from __future__ import annotations

import http.client
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
import bt_remote_panel as panel  # noqa: E402

KEY = "test-only-gateway-key"


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


class Inventory(unittest.TestCase):
    def test_inner_path_strips_only_the_panel_prefix(self):
        self.assertEqual(panel.inner_path("/api/remote/v1/panel"), "/")
        self.assertEqual(panel.inner_path("/api/remote/v1/panel/p/demo"), "/p/demo")
        self.assertIsNone(panel.inner_path("/api/remote/v1/panelx"))
        self.assertIsNone(panel.inner_path("/api/remote/v1/snapshot"))

    def test_every_listed_page_is_allowed_for_get_and_actions_only_for_post(self):
        pages = ["/", "/metrics", "/metrics/model/a/b", "/live", "/learnings", "/flow", "/flow/review", "/now", "/plans",
                 "/plans/demo/REQ-001", "/events", "/api/now", "/api/flow", "/api/plans", "/static/app.js",
                 "/static/vendor/lib/x.js", "/go/demo/REQ-001", "/p/demo", "/p/demo/doc/SUMMARY.md",
                 "/p/demo/artifacts/a.png", "/p/demo/view/a.html", "/p/demo/graph", "/p/demo/req/REQ-001"]
        for path in pages:
            with self.subTest(path=path):
                self.assertTrue(panel.allowed("GET", path))
        actions = ["/api/flow/decision", "/api/flow/diagnose", "/plans/demo/restore", "/plans/demo/REQ-001/approve",
                   "/p/demo/req/REQ-001/run", "/p/demo/req/REQ-001/plan", "/p/demo/req/REQ-001/answer",
                   "/p/demo/req/REQ-001/review"]
        for path in actions:
            with self.subTest(path=path):
                self.assertTrue(panel.allowed("POST", path))
                self.assertFalse(panel.allowed("GET", path) and path.startswith("/api/flow/d"))
        self.assertFalse(panel.allowed("POST", "/p/demo"))
        self.assertFalse(panel.allowed("PUT", "/p/demo"))

    def test_unknown_routes_and_traversal_are_refused(self):
        for path in ["/admin", "/p/demo/secrets", "/p/demo/doc/../../etc/passwd.md", "/p/demo/doc/%2e%2e/x.md",
                     "/p/demo/doc/a%2fb.md", "/p/demo/doc/a%5cb.md", "/static/..%2f..%2fx", "/p/demo/doc/a.txt",
                     "/api/remote/v1/commands", "/p/demo/artifacts/\x00.png"]:
            with self.subTest(path=path):
                self.assertFalse(panel.allowed("GET", path))

    def test_every_top_level_panel_route_has_a_production_counterpart(self):
        """Parity check: a new top-level page or action in bt_server must be added to the inventory."""
        source = (SCRIPTS / "bt_server.py").read_text(encoding="utf-8")
        found: set[str] = set()
        for pattern in (r'parts\[:2\] == \["([a-z]+)"', r'parts == \["([a-z]+)"', r'parts\[0\] == "([a-z]+)"',
                        r'parts\[0\] != "([a-z]+)"'):
            found.update(re.findall(pattern, source))
        for group in re.findall(r'parts\[0\] in \(([^)]*)\)', source):
            found.update(re.findall(r'"([a-z]+)"', group))
        inventory = {route.split("/")[1] for route in panel.GET_ROUTES + panel.POST_ROUTES if route != "/"}
        missing = sorted(found - inventory)
        self.assertEqual(missing, [], f"panel routes without a production counterpart: {missing}")
        self.assertTrue({"metrics", "live", "flow", "plans", "p", "static", "go", "api"} <= found)


class Listener(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        req = self.root / "demo" / "requirements" / "REQ-001-fixture"
        req.mkdir(parents=True)
        (req / "SPEC.md").write_text("---\nid: REQ-001\nstatus: ready\n---\n# REQ-001 — Fixture\n", encoding="utf-8")
        (self.root / "demo" / "SUMMARY.md").write_text("# Demo\n", encoding="utf-8")
        self.port = free_port()
        env = {**os.environ, "BITACORA_ROOT": str(self.root), "FLOW_GATEWAY_KEY": KEY}
        self.proc = subprocess.Popen([sys.executable, str(SCRIPTS / "bitacora.py"), "serve-remote", "--port",
                                      str(self.port)], cwd=SCRIPTS, env=env, stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.05)
        self.fail("serve-remote did not start")

    def tearDown(self):
        self.proc.terminate()
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.tmp.cleanup()

    def call(self, method, path, key=KEY, body=None):
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        if body is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        conn.request(method, path, body=body, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        result = resp.status, resp.getheader("Content-Type", ""), data
        conn.close()
        return result

    def test_pages_need_the_gateway_key_and_render_the_panel(self):
        self.assertEqual(self.call("GET", "/api/remote/v1/panel/", key=None)[0], 401)
        self.assertEqual(self.call("GET", "/api/remote/v1/panel/", key="wrong")[0], 401)
        for path in ("/api/remote/v1/panel/", "/api/remote/v1/panel/p/demo", "/api/remote/v1/panel/p/demo/req/REQ-001",
                     "/api/remote/v1/panel/plans", "/api/remote/v1/panel/now", "/api/remote/v1/panel/metrics"):
            with self.subTest(path=path):
                status, content_type, body = self.call("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(content_type.startswith("text/html"))
                self.assertIn(b"<", body)
        status, _, body = self.call("GET", "/api/remote/v1/panel/api/now")
        self.assertEqual(status, 200)
        self.assertIn("items", json.loads(body))

    def test_unlisted_routes_and_the_panel_root_of_the_listener_stay_closed(self):
        self.assertEqual(self.call("GET", "/")[0], 404)
        self.assertEqual(self.call("GET", "/p/demo")[0], 404)
        self.assertEqual(self.call("GET", "/api/remote/v1/panel/admin")[0], 404)
        self.assertEqual(self.call("GET", "/api/remote/v1/panel/p/demo/doc/%2e%2e/%2e%2e/x.md")[0], 404)
        self.assertEqual(self.call("POST", "/api/remote/v1/panel/p/demo", body="token=x")[0], 404)

    def test_actions_keep_the_panel_token_check_and_leave_an_audit_line(self):
        path = "/api/remote/v1/panel/p/demo/req/REQ-001/run"
        self.assertEqual(self.call("POST", path, key=None, body="action=stop&token=x")[0], 401)
        status, _, _ = self.call("POST", path, body="action=stop&token=wrong")
        self.assertEqual(status, 403)
        audit = [p for p in self.root.rglob("remote-panel-audit.jsonl")]
        self.assertEqual(len(audit), 1)
        rows = [json.loads(line) for line in audit[0].read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["path"] for r in rows], ["/p/demo/req/REQ-001/run"])
        self.assertNotIn("wrong", audit[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
