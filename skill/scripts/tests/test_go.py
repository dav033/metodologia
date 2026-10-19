import http.client
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import bt_core
import bt_go
import bt_server


def build(root: Path):
    for project, reqs in (("alpha", ["REQ-005-x", "REQ-007-y"]), ("beta", ["REQ-005-z"])):
        for r in reqs:
            d = root / project / "requirements" / r
            d.mkdir(parents=True)
            (d / "SPEC.md").write_text("# Spec\n")
        (root / project / "project.json").write_text("{}")
    (root / "alpha" / "requirements" / "REQ-007-y" / "PLAN.json").write_text('{"tasks": [{"id": "T4"}]}')
    (root / "alpha" / "PENDING.md").write_text("## Open\n\n### P-013 · Something\n")
    (root / "beta" / "DECISIONS.md").write_text("## D-045 — Title\n")
    (root / "LEARNINGS.md").write_text("## LG-001 · convention\n")


class Resolve(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        build(self.root)

    def test_unique_ids_resolve_to_their_page_and_anchor(self):
        r = lambda *p: bt_go.resolve(self.root, list(p))  # noqa: E731
        self.assertEqual(r("REQ-007"), {"url": "/p/alpha/req/REQ-007"})
        self.assertEqual(r("alpha", "REQ-007", "T4"), {"url": "/plans/alpha/REQ-007#t-T4"})
        self.assertEqual(r("P-013"), {"url": "/p/alpha?tab=pending#P-013"})
        self.assertEqual(r("d-45"), {"url": "/p/beta?tab=decisions#D-045"})
        self.assertEqual(r("LG-001"), {"url": "/learnings#LG-001"})

    def test_ambiguous_id_offers_a_choice_and_a_project_prefix_settles_it(self):
        out = bt_go.resolve(self.root, ["REQ-005"])
        self.assertEqual([p for p, _ in out["choices"]], ["alpha", "beta"])
        self.assertEqual(bt_go.resolve(self.root, ["beta", "REQ-005"]), {"url": "/p/beta/req/REQ-005"})

    def test_a_task_the_plan_does_not_have_falls_back_to_the_requirement(self):
        (self.root / "alpha" / "requirements" / "REQ-007-y" / "PLAN.json").write_text('{"tasks": [{"id": "T4"}]}')
        self.assertEqual(bt_go.resolve(self.root, ["alpha", "REQ-007", "T4"]), {"url": "/plans/alpha/REQ-007#t-T4"})
        self.assertEqual(bt_go.resolve(self.root, ["alpha", "REQ-007", "T999"]), {"url": "/p/alpha/req/REQ-007"})

    def test_task_without_a_plan_falls_back_to_the_requirement(self):
        self.assertEqual(bt_go.resolve(self.root, ["alpha", "REQ-005", "T1"]), {"url": "/p/alpha/req/REQ-005"})

    def test_unknown_ids_are_errors_not_guesses(self):
        for parts in (["REQ-999"], ["P-999"], ["nonsense"], [], ["LG-099"], ["P-01"]):
            self.assertIn("error", bt_go.resolve(self.root, parts), parts)

    def test_prefix_of_a_longer_id_does_not_match(self):
        (self.root / "alpha" / "PENDING.md").write_text("### P-0130 · other\n")
        self.assertIn("error", bt_go.resolve(self.root, ["alpha", "P-013"]))


class Http(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        build(self.root)
        for target, attr, value in ((bt_server, "ROOT", self.root), (bt_core, "ROOT", self.root),
                                    (bt_server, "STATE", self.root / ".state"), (bt_core, "STATE", self.root / ".state")):
            p = patch.object(target, attr, value)
            p.start()
            self.addCleanup(p.stop)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), bt_server.Handler)
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        self.addCleanup(self.httpd.server_close)
        self.addCleanup(self.httpd.shutdown)

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=5)
        c.request("GET", path)
        r = c.getresponse()
        return r.status, r.getheader("Location"), r.read().decode()

    def test_redirects_choice_page_and_404(self):
        self.assertEqual(self.get("/go/P-013")[:2], (303, "/p/alpha?tab=pending#P-013"))
        status, _, body = self.get("/go/REQ-005")
        self.assertEqual(status, 200)
        self.assertIn("/p/alpha/req/REQ-005", body)
        self.assertIn("/p/beta/req/REQ-005", body)
        self.assertEqual(self.get("/go/REQ-404")[0], 404)
        self.assertEqual(self.get("/go/<script>")[0], 404)
        self.assertEqual(self.get("/learnings")[0], 200)


if __name__ == "__main__":
    unittest.main()
