"""Native diagram capability (REQ-007 T16, gate G11): five types, safe failure, standalone output.

Fixtures are small IR files copied from the pinned upstream examples (MIT, tests/migration/fixtures/diagrams).
Tests that need Node are skipped with a reason when it is missing, which is a skip and not a pass.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "skill" / "scripts"))

import bt_diagram

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "diagrams"
FIVE = {"architecture": "web-app.architecture.json", "workflow": "incident-response.workflow.json",
        "sequence": "cache-miss-request.sequence.json", "dataflow": "event-stream.dataflow.json",
        "lifecycle": "deployment-release.lifecycle.json"}
HAS_NODE = shutil.which("node") is not None


class DiagramCase(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory(prefix="diagram-test-")
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        self.project = self.tmp / "proj"
        self.project.mkdir()


class PinTests(unittest.TestCase):
    def test_vendored_runtime_matches_its_pin_record(self) -> None:
        import hashlib
        root = bt_diagram.renderer_dir()
        pin = bt_diagram.pin()
        files = sorted(p for p in root.rglob("*") if p.is_file() and p.name != "PIN.json")
        digest = hashlib.sha256()
        for path in files:
            digest.update(str(path.relative_to(root)).encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        self.assertEqual(len(files), pin["files"])
        self.assertEqual(digest.hexdigest(), pin["tree_sha256"], "vendored Archify changed without a new PIN")
        self.assertEqual(pin["license"], "MIT")
        for notice in pin["notices"]:
            self.assertTrue((root / notice).is_file(), notice)
        self.assertFalse((root / "SKILL.md").exists())

    def test_doctor_reports_without_raising(self) -> None:
        report = bt_diagram.doctor()
        self.assertEqual(report["types"], list(bt_diagram.TYPES))
        self.assertIn("ready", report)


@unittest.skipUnless(HAS_NODE, "node is not installed")
class RenderTests(DiagramCase):
    def test_five_types_validate_render_and_publish_standalone(self) -> None:
        for diagram_type, fixture in FIVE.items():
            with self.subTest(type=diagram_type):
                result = bt_diagram.publish(self.project, f"{diagram_type}-one", diagram_type, FIXTURES / fixture)
                html = Path(result["html"])
                self.assertTrue(html.is_file())
                self.assertGreater(html.stat().st_size, 2000)
                text = html.read_text(encoding="utf-8")
                self.assertEqual(bt_diagram.external_references(text), [])
                art = self.project / "artifacts"
                self.assertTrue((art / f"diagram-{diagram_type}-one.ir.json").is_file())
                provenance = json.loads((art / f"diagram-{diagram_type}-one.provenance.json").read_text())
                self.assertEqual(provenance["type"], diagram_type)
                self.assertEqual(provenance["renderer"]["commit"], bt_diagram.pin()["commit"])
                self.assertEqual(provenance["ir_sha256"],
                                 __import__("hashlib").sha256((FIXTURES / fixture).read_bytes()).hexdigest())

    def test_invalid_ir_never_replaces_a_valid_artifact(self) -> None:
        good = bt_diagram.publish(self.project, "keep", "architecture", FIXTURES / FIVE["architecture"])
        before = Path(good["html"]).read_bytes()
        broken = self.tmp / "broken.json"
        broken.write_text(json.dumps({"meta": {}, "nodes": "not-a-list"}))
        with self.assertRaises(bt_diagram.DiagramError) as caught:
            bt_diagram.publish(self.project, "keep", "architecture", broken)
        self.assertIn(caught.exception.code, ("INVALID_IR", "RENDER_FAILED", "RENDERER_FAILED"))
        self.assertEqual(Path(good["html"]).read_bytes(), before)
        self.assertEqual(sorted(p.name for p in (self.project / "artifacts").iterdir() if p.is_dir()), [])

    def test_oversized_not_json_and_bad_names_are_rejected_before_rendering(self) -> None:
        huge = self.tmp / "huge.json"
        huge.write_text('{"x": "' + "a" * (bt_diagram.MAX_IR_BYTES + 10) + '"}')
        notjson = self.tmp / "nope.json"
        notjson.write_text("{truncated")
        for path, code in ((huge, "IR_TOO_LARGE"), (notjson, "IR_NOT_JSON")):
            with self.subTest(code=code), self.assertRaises(bt_diagram.DiagramError) as caught:
                bt_diagram.publish(self.project, "ok", "workflow", path)
            self.assertEqual(caught.exception.code, code)
        for name in ("../escape", "Has Space", "", "a" * 80, "-lead"):
            with self.subTest(name=name), self.assertRaises(bt_diagram.DiagramError) as caught:
                bt_diagram.publish(self.project, name, "workflow", FIXTURES / FIVE["workflow"])
            self.assertEqual(caught.exception.code, "BAD_NAME")
        with self.assertRaises(bt_diagram.DiagramError) as caught:
            bt_diagram.publish(self.project, "ok", "erd", FIXTURES / FIVE["workflow"])
        self.assertEqual(caught.exception.code, "BAD_TYPE")
        self.assertFalse((self.project / "artifacts" / "diagram-ok.html").exists())

    def test_script_injection_in_labels_is_escaped_or_rejected(self) -> None:
        payload = "</title><script>window.__pwned=1</script>"
        data = json.loads((FIXTURES / FIVE["workflow"]).read_text())

        def taint(node):
            if isinstance(node, dict):
                return {k: (payload if k in ("title", "label") and isinstance(v, str) else taint(v))
                        for k, v in node.items()}
            if isinstance(node, list):
                return [taint(v) for v in node]
            return node

        evil = self.tmp / "evil.json"
        evil.write_text(json.dumps(taint(data)))
        try:
            result = bt_diagram.publish(self.project, "evil", "workflow", evil)
        except bt_diagram.DiagramError:
            return  # rejected by validation: also acceptable
        text = Path(result["html"]).read_text(encoding="utf-8")
        self.assertNotIn("<script>window.__pwned=1</script>", text)

    def test_architecture_compare_publishes_a_before_after_page(self) -> None:
        result = bt_diagram.compare(self.project, "checkout-change", FIXTURES / "checkout-platform.base.architecture.json",
                                    FIXTURES / "checkout-platform.head.architecture.json")
        html = Path(result["html"])
        self.assertTrue(html.name.endswith(".compare.html"))
        self.assertEqual(bt_diagram.external_references(html.read_text(encoding="utf-8")), [])

    def test_a_renderer_that_hangs_is_killed_at_the_deadline(self) -> None:
        original = bt_diagram.DEADLINE_SEC
        self.addCleanup(setattr, bt_diagram, "DEADLINE_SEC", original)
        with self.assertRaises(bt_diagram.DiagramError) as caught:
            bt_diagram._run(["validate", "architecture", str(FIXTURES / FIVE["architecture"]), "--json"],
                            timeout=0.001)
        self.assertEqual(caught.exception.code, "TIMEOUT")


class ReferenceScanTests(unittest.TestCase):
    def test_fetches_are_flagged_and_plain_navigation_is_not(self) -> None:
        html = ('<a href="https://example.com/about">credit</a><img src="https://cdn.example/x.png">'
                '<link rel="stylesheet" href="https://fonts.example/f.css"><style>@import url(https://x.example/a.css);'
                'b{background:url("https://y.example/i.png")}</style><form action="https://z.example/post"></form>')
        self.assertEqual(bt_diagram.external_references(html), [
            "https://cdn.example/x.png", "https://fonts.example/f.css", "https://x.example/a.css",
            "https://y.example/i.png", "https://z.example/post"])
        self.assertEqual(bt_diagram.external_references('<a href="https://a.example">x</a>'), [])


@unittest.skipUnless(HAS_NODE, "node is not installed")
class CliAndWebTests(DiagramCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        env = {"PATH": os.environ["PATH"], "HOME": str(self.tmp), "BITACORA_ROOT": str(self.tmp / "bit"),
               "PYTHONDONTWRITEBYTECODE": "1"}
        return subprocess.run([sys.executable, str(REPO / "skill" / "scripts" / "bitacora.py"), "--project", "demo",
                               *args], capture_output=True, text=True, env=env, cwd=self.tmp, timeout=120,
                              check=False)

    def test_cli_publishes_lists_and_reports_failures_with_exit_codes(self) -> None:
        self.assertEqual(self.run_cli("init").returncode, 0)
        done = self.run_cli("diagram", "publish", "architecture-map", "architecture",
                            str(FIXTURES / FIVE["architecture"]), "--title", "Map")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["type"], "architecture")
        listing = json.loads(self.run_cli("diagram", "list").stdout)
        self.assertEqual(listing, ["diagram-architecture-map.html"])
        bad = self.tmp / "bad.json"
        bad.write_text("{nope")
        failed = self.run_cli("diagram", "publish", "bad", "architecture", str(bad))
        self.assertEqual(failed.returncode, 1)
        self.assertIn("IR_NOT_JSON", failed.stderr)
        self.assertEqual(json.loads(self.run_cli("diagram", "doctor").stdout)["ready"], True)

    def test_dashboard_serves_diagram_pages_in_a_sandbox(self) -> None:
        import socket
        import subprocess
        import time
        import urllib.request
        self.run_cli("init")
        self.run_cli("diagram", "publish", "flow", "workflow", str(FIXTURES / FIVE["workflow"]))
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        env = {"PATH": os.environ["PATH"], "HOME": str(self.tmp), "BITACORA_ROOT": str(self.tmp / "bit"),
               "BITACORA_PORT": str(port), "PYTHONDONTWRITEBYTECODE": "1"}
        server = subprocess.Popen([sys.executable, str(REPO / "skill" / "scripts" / "bitacora.py"), "serve"],
                                  env=env, cwd=self.tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.addCleanup(server.wait)
        self.addCleanup(server.terminate)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            with socket.socket() as client:
                client.settimeout(0.2)
                if client.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.1)
        url = f"http://127.0.0.1:{port}/p/demo/artifacts/diagram-flow.html"
        with urllib.request.urlopen(url, timeout=10) as response:
            policy = response.headers.get("Content-Security-Policy", "")
        self.assertIn("sandbox", policy)
        self.assertIn("default-src 'none'", policy)


@unittest.skipUnless(HAS_NODE and shutil.which("chromium"), "node or chromium is not installed")
class VisualCheckTests(DiagramCase):
    def test_republished_page_gets_new_visual_evidence_without_removing_old_receipts(self) -> None:
        source = self.tmp / "source.json"
        data = json.loads((FIXTURES / FIVE["architecture"]).read_text())
        source.write_text(json.dumps(data))
        result = bt_diagram.publish(self.project, "revised", "architecture", source)
        first = bt_diagram.visual_check(Path(result["html"]))
        self.assertTrue(first["ok"], first)
        data["meta"]["title"] = "Revised architecture"
        source.write_text(json.dumps(data))
        bt_diagram.publish(self.project, "revised", "architecture", source)
        second = bt_diagram.visual_check(Path(result["html"]))
        self.assertTrue(second["ok"], second)
        self.assertNotEqual(first["evidence"]["receipt"], second["evidence"]["receipt"])
        self.assertTrue(Path(first["evidence"]["receipt"]).is_file())

    def test_published_page_passes_the_automated_light_dark_capture(self) -> None:
        result = bt_diagram.publish(self.project, "visual", "architecture", FIXTURES / FIVE["architecture"])
        report = bt_diagram.visual_check(Path(result["html"]))
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["checks"]["themeStates"], "pass")
        themes = {shot["resolvedTheme"] for shot in report["evidence"]["screenshots"]}
        self.assertEqual(themes, {"light", "dark"})
        self.assertEqual(report["visualReview"], "pending")  # a person still has to look


class NodeMissingTests(DiagramCase):
    def test_missing_node_gives_an_actionable_error_and_doctor_still_works(self) -> None:
        saved = os.environ.get("PATH", "")
        os.environ["PATH"] = str(self.tmp)  # a directory with no node
        try:
            with self.assertRaises(bt_diagram.DiagramError) as caught:
                bt_diagram.publish(self.project, "x", "architecture", FIXTURES / FIVE["architecture"])
            self.assertEqual(caught.exception.code, "NODE_MISSING")
            self.assertIn("Node.js", caught.exception.message)
            self.assertFalse(bt_diagram.doctor()["ready"])
        finally:
            os.environ["PATH"] = saved


if __name__ == "__main__":
    unittest.main()
