"""`/components`: the Designer kit gallery page, its sandboxed frames and the reference mockups."""
import http.client
import re
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode

import bt_core
import bt_kit
import bt_page_components as pc
import bt_server


class Page(unittest.TestCase):
    def test_lists_every_component_category_and_reference(self):
        html = pc.kit_page()
        data = bt_kit.manifest()
        for row in data["components"]:
            self.assertIn(f'id="c-{row["id"]}"', html)
            self.assertIn(f'src="/components/frame/{row["id"]}?theme=light&amp;motion=natural"', html)
        for cat in data["categories"]:
            self.assertIn(f'id="cat-{cat["id"]}"', html)
        for ref in data["references"]:
            self.assertIn(f'href="/components/kitref/{ref["id"]}"', html)
        self.assertEqual(html.count('sandbox="allow-scripts"'), len(data["components"]) + len(data["references"]))
        self.assertIn('<a href="/components">Componentes</a>', html)          # top navigation
        self.assertIn('<script src="/static/kit-gallery.js"></script>', html)
        for label in ("Claro", "Oscuro", "Sutil", "Natural", "Expresivo", "Móvil", "Tableta", "Escritorio"):
            self.assertIn(f">{label}</button>", html)

    def test_snippets_are_shown_escaped(self):
        html = pc.kit_page()
        self.assertIn("&lt;button class=&quot;button&quot;", html)
        self.assertIsNone(re.search(r"<script(?![^>]*\bsrc=)", html))         # no inline script in the trusted shell

    def test_manifest_text_is_escaped(self):
        row = {"id": "x", "name": "<img src=x onerror=alert(1)>", "category": "c", "priority": "P1", "description": "<b>",
               "states": ["<i>"], "contract": "A|B", "examples": [{"id": "e", "title": "<u>", "html": "<script>alert(1)</script>"}]}
        fake = {"categories": [{"id": "c", "title": "<em>Cat</em>"}], "components": [row], "references": []}
        with patch.object(bt_kit, "manifest", return_value=fake):
            html = pc.kit_page()
        self.assertNotIn("<img src=x", html)
        self.assertNotIn("<script>alert(1)", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("&lt;em&gt;Cat&lt;/em&gt;", html)

    def test_frame_doc_sanitises_theme_and_motion(self):
        doc = pc.frame_doc("button", '"><script>', "fast")
        self.assertIn('data-theme="light" data-motion="natural"', doc)
        self.assertIn("--background:", doc)                                    # the kit stylesheet is inlined
        self.assertIn('id="ex-variants"', doc)
        self.assertIn("kit: 'height'", doc)
        self.assertIn('data-theme="dark"', pc.frame_doc("button", "dark", "expressive"))
        self.assertIsNone(pc.frame_doc("../tokens", None, None))
        self.assertIsNone(pc.frame_doc("nope", None, None))

    def test_reference_lookup_only_by_manifest_id(self):
        _row, path = bt_kit.reference("acceso")
        self.assertTrue(path.is_file())
        self.assertIsNone(bt_kit.reference("../components/manifest"))


class Http(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        for target, attr, value in ((bt_server, "ROOT", root), (bt_core, "ROOT", root),
                                    (bt_server, "STATE", root / ".state"), (bt_core, "STATE", root / ".state")):
            p = patch.object(target, attr, value)
            p.start()
            self.addCleanup(p.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=10)
        c.request("GET", path)
        r = c.getresponse()
        return r.status, r.getheader("Content-Security-Policy") or "", r.read().decode()

    def test_routes(self):
        status, csp, body = self.get("/components")
        self.assertEqual(status, 200)
        self.assertIn("script-src 'self'", csp)
        self.assertIn("Componentes", body)
        status, csp, body = self.get("/components/frame/data-table?theme=dark")
        self.assertEqual(status, 200)
        self.assertTrue(csp.startswith("sandbox allow-scripts"))
        self.assertIn('data-theme="dark"', body)
        status, csp, body = self.get("/components/kitref/cuentas")
        self.assertEqual((status, csp.startswith("sandbox allow-scripts")), (200, True))
        self.assertIn('<select class="select" id="view">', body)
        for bad in ("/components/frame/..%2Ftokens", "/components/frame/nope", "/components/ref/x", "/components/x/y/z"):
            self.assertEqual(self.get(bad)[0], 404, bad)
        self.assertEqual(self.get("/static/kit-gallery.css")[0], 200)

    def test_direction_choice_uses_owner_token_and_notifies_planner(self):
        import bt_design_directions
        rdir = bt_server.ROOT / "demo/requirements/REQ-001-test"
        rdir.mkdir(parents=True)
        address = self.httpd.server_address[1]
        def post(token, origin=""):
            c = http.client.HTTPConnection("127.0.0.1", address, timeout=10)
            body = urlencode({"contract": "checkout@v1", "direction": "a", "token": token})
            c.request("POST", "/p/demo/req/REQ-001/design-choose", body, {"Origin": origin})
            response = c.getresponse()
            response.read()
            c.close()
            return response.status
        with patch.object(bt_design_directions, "choose", return_value="Dirección A elegida") as choose, \
                patch.object(bt_server, "commit"), patch.object(bt_server.Handler, "tell_planner") as notify:
            self.assertEqual(post("invalid"), 403)
            self.assertEqual(post(bt_server.token(), "https://untrusted.example"), 403)
            choose.assert_not_called()
            self.assertEqual(post(bt_server.token()), 303)
            choose.assert_called_once_with("demo", rdir, "checkout@v1", "a", "web")
            notify.assert_called_once()

    def test_direction_iteration_route_uses_owner_token(self):
        import bt_design_iterate
        rdir = bt_server.ROOT / "demo/requirements/REQ-001-test"
        rdir.mkdir(parents=True)
        address = self.httpd.server_address[1]
        def post(token):
            c = http.client.HTTPConnection("127.0.0.1", address, timeout=10)
            body = urlencode({"contract": "checkout@v1", "direction": "b", "comments": "Rounder", "token": token})
            c.request("POST", "/p/demo/req/REQ-001/design-iterate", body)
            response = c.getresponse()
            location = response.getheader("Location") or ""
            response.read()
            c.close()
            return response.status, location
        with patch.object(bt_design_iterate, "iterate", return_value="Iterando la dirección B") as it, \
                patch.object(bt_server, "commit"), patch.object(bt_server.Handler, "tell_planner"):
            self.assertEqual(post("invalid")[0], 403)
            it.assert_not_called()
            status, location = post(bt_server.token())
            self.assertEqual(status, 303)
            self.assertIn("Iterando", __import__("urllib.parse").parse.unquote(location))
            it.assert_called_once_with("demo", rdir, "checkout@v1", "b", "Rounder", "web")

    def test_design_amend_route_uses_owner_token(self):
        import bt_design_amend
        rdir = bt_server.ROOT / "demo/requirements/REQ-001-test"
        rdir.mkdir(parents=True)
        address = self.httpd.server_address[1]
        def post(token):
            c = http.client.HTTPConnection("127.0.0.1", address, timeout=10)
            body = urlencode({"contract": "checkout@v1", "comments": "Keep badges", "anchor": "SP-2", "token": token})
            c.request("POST", "/p/demo/req/REQ-001/design-amend", body)
            response = c.getresponse()
            location = response.getheader("Location") or ""
            response.read()
            c.close()
            return response.status, location
        with patch.object(bt_design_amend, "start", return_value="Actualizando checkout@v1") as amend, \
                patch.object(bt_server, "commit"), patch.object(bt_server.Handler, "tell_planner") as notify:
            self.assertEqual(post("invalid")[0], 403)
            amend.assert_not_called()
            status, location = post(bt_server.token())
            self.assertEqual(status, 303)
            self.assertIn("Actualizando", __import__("urllib.parse").parse.unquote(location))
            amend.assert_called_once_with("demo", rdir, "checkout@v1", "Keep badges", "web")
            notify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
