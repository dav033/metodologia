"""Real inventory, escaped gallery and offline builder/browser integration."""
import collections
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_kit
import bt_kit_workspace as workspace
import bt_page_components as gallery


class Inventory(unittest.TestCase):
    def test_inventory_and_enhancements_match_the_source_contract(self):
        data = workspace.manifest()
        entries = data["entries"]
        self.assertEqual(collections.Counter(r["source"] for r in entries),
                         {"shadcn": 42, "animate-ui": 7, "bencho": 12, "react-bits": 32})
        self.assertEqual(len({r["id"] for r in entries}), 93)
        self.assertEqual(len(data["enhancements"]), 22)
        for row in entries + data["enhancements"]:
            self.assertIn(row["status"], ("done", "gap"))
            if row["status"] == "gap":
                self.assertTrue(row["reason"].strip(), row)
        for row in entries:
            for key in ("name", "version", "licence", "category", "priority", "type", "import", "contract"):
                self.assertTrue(row[key], (row["id"], key))
            self.assertTrue((workspace.REAL / row["demo"]).is_file(), row["id"])

    def test_real_gallery_filters_and_untrusted_text(self):
        data = bt_kit.real_manifest()
        row = data["entries"][0]
        row["name"] = '<img src=x onerror="alert(1)">'
        row["description"] = "<script>unsafe()</script>"
        with patch.object(bt_kit, "real_manifest", return_value=data):
            html = gallery.components_page()
        self.assertNotIn('<img src=x', html)
        self.assertNotIn('<script>unsafe()', html)
        self.assertIn('&lt;img src=x', html)
        for kind in ("source", "category", "priority", "status"):
            self.assertIn(f'data-filter="{kind}"', html)
        for r in data["entries"]:
            self.assertIn(f'id="c-{r["id"]}"', html)
        self.assertIn("Movimiento reducido", html)

    def test_published_picker_is_visible_but_does_not_claim_to_be_a_wheel(self):
        data = bt_kit.real_manifest()
        picker = next(r for r in data["entries"] if r["id"] == "picker-wheel")
        self.assertEqual(picker["status"], "gap")
        self.assertIn("no implementa la rueda", picker["reason"])
        if picker["built"]:
            html = gallery.components_page()
            self.assertIn('/components/live/picker-wheel?', html)
            self.assertIn("Brecha del contrato:", html)


@unittest.skipUnless((workspace.workspace() / "node_modules").is_dir(), "real kit workspace is not installed")
class OfflineBuild(unittest.TestCase):
    """The rendered checks build what they test from this checkout's source into a temporary dist: the shared
    workspace's dist is whatever was built last (2026-10-29 it predated runtime fixes), not the code under test."""

    def fresh_dist(self) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        out = Path(tmp.name)
        self.run_tool(["node", str(workspace.REAL / "build.mjs"), "gallery", "--out", str(out), "--only", "text-type",
                       "--ws", str(workspace.workspace())])
        self.run_tool(["node", str(workspace.REAL / "build.mjs"), "mockup", str(workspace.REAL / "reference/acceso.tsx"),
                       "--out", str(out / "reference/acceso.html"), "--ws", str(workspace.workspace())])
        return out

    def run_tool(self, argv, timeout=180):
        proc = subprocess.run(argv, cwd="/tmp", env={**os.environ, "UV_OFFLINE": "1"}, capture_output=True,
                              text=True, timeout=timeout, check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout[-3500:] + proc.stderr[-1500:])
        return proc.stdout

    def test_build_produces_self_contained_mockup_with_real_selectors(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "reference.html"
            self.run_tool(["node", str(workspace.REAL / "build.mjs"), "mockup",
                           str(workspace.REAL / "reference/acceso.tsx"), "--out", str(out),
                           "--ws", str(workspace.workspace())])
            text = out.read_text()
            self.assertIn('data-kit="real"', text)
            self.assertNotIn('<script src=', text)
            self.assertNotIn('<link rel="stylesheet"', text)
            self.assertGreater(len(text), 10000)

    @unittest.skipUnless(shutil.which("uv") and shutil.which("chromium"), "cached Playwright/Chromium unavailable")
    def test_built_reference_passes_rendered_audit(self):
        ref = self.fresh_dist() / "reference/acceso.html"
        output = self.run_tool(["uv", "run", "--offline", "--with", "playwright", "python",
                                str(bt_kit.KIT / "audit_mockup.py"), str(ref)])
        self.assertIn("RESULT: PASS", output)

    @unittest.skipUnless(shutil.which("uv") and shutil.which("chromium"), "cached Playwright/Chromium unavailable")
    def test_gallery_controls_reach_references_and_text_type_is_static_when_reduced(self):
        dist = self.fresh_dist()
        ref = dist / "reference/acceso.html"
        with tempfile.TemporaryDirectory() as tmp, patch.object(workspace, "dist", return_value=dist):
            demo = Path(tmp) / "text-type.html"
            demo.write_text(bt_kit.live_doc("text-type", "light", "expressive", "1"))
            script = '''
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=sys.argv[3])
    page = browser.new_page()
    page.goto(Path(sys.argv[1]).as_uri())
    page.wait_for_timeout(400)
    page.evaluate("window.postMessage({kit:'set',theme:'dark',motion:'subtle',reduced:false},'*')")
    page.wait_for_function("document.documentElement.dataset.theme==='dark' && document.documentElement.dataset.motion==='subtle'")
    page.select_option('#motion','expressive')
    page.select_option('#view','activar')
    page.wait_for_timeout(50)
    page.locator('input[type=email]').fill('david@example.test')
    page.evaluate("window.fixtureAnimation=document.querySelector('#app h1, #app h2, #app button').animate([{opacity:.5},{opacity:1}],{duration:5000,fill:'forwards'})")
    assert page.evaluate("window.fixtureAnimation.playState")=='running'
    page.evaluate("window.postMessage({kit:'set',reduced:true},'*')")
    page.wait_for_function("document.documentElement.hasAttribute('data-reduced-motion')")
    page.wait_for_timeout(60)
    assert page.evaluate("document.getAnimations().filter(a=>a.playState==='running').length")==0
    assert page.evaluate("window.fixtureAnimation.playState")=='finished'
    assert page.locator('input[type=email]').input_value()=='david@example.test'
    page.goto(Path(sys.argv[2]).as_uri()+'?rm=1')
    page.wait_for_timeout(200)
    before=page.locator('#root').inner_text()
    assert 'Eventos corporativos' in before and 'sin estrés' in before
    page.wait_for_timeout(1000)
    assert page.locator('#root').inner_text()==before
    browser.close()
print('controls and reduced-motion: PASS')
'''
            output = self.run_tool(["uv", "run", "--offline", "--with", "playwright", "python", "-c", script,
                                    str(ref), str(demo), shutil.which("chromium")])
            self.assertIn("controls and reduced-motion: PASS", output)


if __name__ == "__main__":
    unittest.main()
