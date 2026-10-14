"""Provider driver contract against streams captured from the real CLIs (REQ-007 T7).

The fixtures under fixtures/providers were produced by one minimal real turn per provider ("reply PONG", no tools) on
2026-10-14 and stripped of environment, hook output, tool catalogues, paths and identifiers. They pin the parsing
of what each CLI actually prints; the fake-CLI scenarios in test_driver_contracts.py pin the failure shapes.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "skill" / "scripts"
SAMPLES = HERE / "fixtures" / "providers"

PROBE = """
import json, sys
sys.path.insert(0, {scripts!r})
import bt_driver
raw = open({path!r}, encoding="utf-8").read()
out = bt_driver.driver_for({provider!r}).normalize(raw, {rc})
print(json.dumps(out.as_dict()))
"""


class RealSampleTests(unittest.TestCase):
    def normalize(self, provider: str, name: str, rc: int = 0) -> dict:
        with tempfile.TemporaryDirectory(prefix="driver-real-") as tmp:
            env = {"PATH": "/usr/bin:/bin", "HOME": tmp, "BITACORA_ROOT": str(Path(tmp) / "bit"),
                   "PYTHONDONTWRITEBYTECODE": "1"}
            code = PROBE.format(scripts=str(SCRIPTS), path=str(SAMPLES / name), provider=provider, rc=rc)
            done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True, env=env,
                                  timeout=60, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_claude_stream_is_completed_with_reported_cost_and_usage(self) -> None:
        out = self.normalize("claude", "claude-pong.jsonl")
        self.assertEqual((out["status"], out["text"], out["terminal_event"], out["is_error"]),
                         ("completed", "PONG", True, False))
        self.assertGreater(out["cost_usd"], 0)
        self.assertEqual(out["usage"]["output_tokens"], 5)

    def test_antigravity_stream_is_completed_with_reported_usage(self) -> None:
        out = self.normalize("antigravity", "antigravity-pong.jsonl")
        self.assertEqual((out["status"], out["text"].strip(), out["terminal_event"]), ("completed", "PONG", True))
        self.assertEqual(out["usage"]["total_tokens"], 11933)
        self.assertIsNone(out["cost_usd"])  # no price is reported, so none is invented

    def test_codex_text_is_completed_best_effort_with_total_tokens_only(self) -> None:
        out = self.normalize("codex", "codex-pong.txt")
        self.assertEqual((out["status"], out["terminal_event"]), ("completed", True))
        self.assertEqual(out["usage"], {"total_tokens": 14254})

    def test_the_same_samples_are_never_completed_after_a_failed_exit_or_a_cut(self) -> None:
        for provider, name in (("claude", "claude-pong.jsonl"), ("antigravity", "antigravity-pong.jsonl"),
                               ("codex", "codex-pong.txt")):
            with self.subTest(provider=provider):
                self.assertEqual(self.normalize(provider, name, rc=1)["status"], "failed")

    def test_cut_streams_are_partial(self) -> None:
        for provider, name in (("claude", "claude-pong.jsonl"), ("antigravity", "antigravity-pong.jsonl")):
            with self.subTest(provider=provider):
                lines = (SAMPLES / name).read_text(encoding="utf-8").splitlines()[:-1]  # drop the terminal event
                with tempfile.TemporaryDirectory(prefix="driver-cut-") as tmp:
                    cut = Path(tmp) / "cut.jsonl"
                    cut.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    code = PROBE.format(scripts=str(SCRIPTS), path=str(cut), provider=provider, rc=0)
                    env = {"PATH": "/usr/bin:/bin", "HOME": tmp, "BITACORA_ROOT": str(Path(tmp) / "bit"),
                           "PYTHONDONTWRITEBYTECODE": "1"}
                    done = subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, text=True,
                                          env=env, timeout=60, check=False)
                self.assertEqual(done.returncode, 0, done.stderr)
                self.assertEqual(json.loads(done.stdout)["status"], "partial")


if __name__ == "__main__":
    unittest.main()
