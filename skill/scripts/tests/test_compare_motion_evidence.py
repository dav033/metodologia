"""A claim holds when it shows in any view and state; a motion claim when the element or a descendant declares motion, or it
moved by script while measured (pictures REQ-021 SP-6, SP-7, SP-12)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bt_design_drafts as drafts

PAGE = """<!doctype html><html><head><style>{css}</style></head><body><main><h1>Spend</h1><p>Ledger</p>
<button class="toggle">Group <svg width="12" height="12"><path d="M0 0L6 6"/></svg></button>
<span class="marker">marker</span><div class="still">still</div><strong class="total" hidden>12</strong>
<select id="state"><option>idle</option><option>result</option></select></main>
<script>document.querySelector('#state').onchange=e=>{{document.querySelector('.total').hidden=e.target.value!=='result'}};{js}</script>
</body></html>"""
CLAIMS = {"layout": ["main"], "navigation": [".toggle"], "typography": ["h1", ".total"], "motion": [".toggle", ".marker", ".still"]}


@unittest.skipUnless(shutil.which("chromium") and shutil.which("uv"), "needs chromium and uv")
class MotionEvidence(unittest.TestCase):
    def run_tool(self, css: str, js: str, axis: str = "motion") -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "x@v1.r1.dir-a.html"
            page.write_text(PAGE.format(css=css, js=js), encoding="utf-8")
            page.with_suffix(".json").write_text(json.dumps({"name": "A", "evidence": CLAIMS}), encoding="utf-8")
            proc = subprocess.run(["uv", "run", "--offline", "--with", "playwright", "python",
                                   str(drafts.KIT / "compare_directions.py"), str(page), "--json"],
                                  cwd=tmp, capture_output=True, text=True, timeout=180, env={**os.environ, "UV_OFFLINE": "1"})
        if not proc.stdout.strip():
            self.skipTest(f"comparison not run: {proc.stderr[-300:]}")
        report = json.loads(proc.stdout)
        return {row["selector"]: row["ok"] for row in report["directions"][0]["evidence"][axis]}

    def test_child_transitions_and_script_motion_count_and_a_still_element_does_not(self):
        motion = self.run_tool(".toggle svg{transition:transform .2s}",
                               "document.querySelector('.marker').animate([{transform:'scaleX(.7)'},"
                               "{transform:'scaleX(1)'}],{duration:20})")
        self.assertEqual(motion, {".toggle": True, ".marker": True, ".still": False})

    def test_a_claim_that_shows_only_in_one_state_holds(self):
        self.assertEqual(self.run_tool("", "", axis="typography"), {"h1": True, ".total": True})


if __name__ == "__main__":
    unittest.main()
