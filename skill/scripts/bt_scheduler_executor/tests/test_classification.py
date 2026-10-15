"""T8: how the end of a process becomes a cause class (facts, never decisions)."""
from __future__ import annotations

import os
import signal
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import classify
from bt_scheduler_executor import model as m
from support import World, order, wait_for


class Causes(unittest.TestCase):
    def run_one(self, scenario, **kw):
        w = kw.pop("world", None) or World(self)
        w.x.start(order(1, scenario, **kw))
        return w, w.finish("att-0001")

    def test_a_clean_exit_with_end_of_turn_evidence(self):
        _, d = self.run_one("ok")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("finished", "clean"))
        self.assertTrue(d["outcome"]["terminal_event"])

    def test_quota_exhaustion_carries_the_reset_epoch_the_provider_gave(self):
        w, d = self.run_one("quota:1893456000")
        self.assertEqual((d["state"], d["outcome"]["cause"], d["outcome"]["reset_epoch"]), ("failed", "quota_exhausted", 1893456000))
        payload = w.sink.of("att-0001", m.EV_FAILED)[0].payload
        self.assertEqual((payload["cause"], payload["reset_epoch"]), ("quota_exhausted", 1893456000))

    def test_a_limit_without_a_reset_time_has_none_never_a_guess(self):
        class NoReset(support.FakeDriver):
            def classify(self, route, raw, returncode, **kw):
                return ex.Classification("limit", reset_epoch=None)
        _, d = self.run_one("quota", world=World(self, driver=NoReset()))
        self.assertEqual((d["outcome"]["cause"], d["outcome"]["reset_epoch"]), ("quota_exhausted", None))

    def test_quota_exhaustion_still_preserves_the_half_done_work(self):
        _, d = self.run_one("quota")
        self.assertTrue(d["handoff"]["dirty"])
        self.assertEqual(d["handoff"]["status"], "captured")
        self.assertIn("partial.txt", "".join(d["handoff"]["changed"] if "changed" in d["handoff"] else
                                             [str(p) for p in Path(d["handoff"]["worktree"]).iterdir()]))

    def test_a_dropped_connection_is_reported_as_connection_lost_and_keeps_the_work(self):
        _, d = self.run_one("net")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "connection_lost"))
        self.assertTrue(d["handoff"]["dirty"])

    def test_connection_words_in_the_output_of_a_successful_run_are_not_a_failure(self):
        _, d = self.run_one("nettext")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("finished", "clean"))

    def test_a_plain_agent_error(self):
        _, d = self.run_one("crash")
        self.assertEqual((d["state"], d["outcome"]["cause"], d["outcome"]["returncode"]), ("failed", "agent_error", 3))

    def test_a_clean_exit_without_end_of_turn_evidence_is_never_finished(self):
        w, d = self.run_one("partial")
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "incomplete_output"))
        self.assertEqual(w.sink.kinds("att-0001"), [m.EV_STARTED, m.EV_FAILED])

    def test_a_process_killed_by_a_signal_from_outside_is_killed_not_cancelled(self):
        w = World(self)
        w.x.start(order(1, "sleep:60"))
        self.assertTrue(wait_for(lambda: (Path(w.x.describe("att-0001")["artifacts"]["dir"]) / "shim.json").exists()))
        shim = __import__("json").loads((Path(w.x.describe("att-0001")["artifacts"]["dir"]) / "shim.json").read_text())
        self.assertTrue(wait_for(lambda: __import__("json").loads((Path(w.x.describe("att-0001")["artifacts"]["dir"]) / "shim.json").read_text()).get("child_pid")))
        shim = __import__("json").loads((Path(w.x.describe("att-0001")["artifacts"]["dir"]) / "shim.json").read_text())
        os.killpg(shim["child_pid"], signal.SIGKILL)
        d = w.finish("att-0001")
        self.assertEqual((d["state"], d["outcome"]["cause"], d["outcome"]["signal"]), ("failed", "killed", "SIGKILL"))
        self.assertEqual(w.x.query("att-0001").cause, "killed")

    def test_a_timeout_is_a_timeout(self):
        _, d = self.run_one("sleep:60", timeout=1)
        self.assertEqual(d["outcome"]["cause"], "timeout")

    def test_a_classifier_that_raises_cannot_hide_the_exit(self):
        class Boom(support.FakeDriver):
            def classify(self, route, raw, returncode, **kw):
                raise RuntimeError("bug")
        _, d = self.run_one("ok", world=World(self, driver=Boom()))
        self.assertEqual((d["state"], d["outcome"]["cause"]), ("failed", "agent_error"))
        self.assertIn("classifier error", d["outcome"]["detail"])

    def test_quota_text_at_the_end_of_a_huge_output_is_still_seen_through_the_tail(self):
        class Big(support.FakeDriver):
            def prepare(self, route, prompt, workspace, timeout):
                return ex.Launch(argv=(sys.executable, "-c",
                                       "import sys\nfor i in range(40000): print('x' * 90)\n"
                                       "print('usage limit reached|1893456000')\nsys.exit(1)"))
        cfg = ex.Config(poll_seconds=0.05, grace_seconds=1, timeout_seconds=60, output_head_bytes=50_000,
                        output_tail_bytes=10_000, classify_head_bytes=1000)
        w = World(self, driver=Big(), config=cfg)
        w.x.start(order(1, "big"))
        d = w.finish("att-0001")
        self.assertEqual((d["outcome"]["cause"], d["outcome"]["reset_epoch"]), ("quota_exhausted", 1893456000))
        self.assertGreater(d["outcome"]["output"]["dropped"], 3_000_000)
        self.assertEqual(d["outcome"]["output"]["bytes"], 40000 * 91 + len("usage limit reached|1893456000\n"))

    def test_output_that_fits_is_classified_whole(self):
        import tempfile

        from bt_scheduler_executor import artifacts
        with tempfile.TemporaryDirectory() as t:
            d = Path(t)
            (d / "output.log").write_bytes(b"A" * 10)
            (d / "output.tail").write_bytes(b"A" * 10)
            text, total, dropped = artifacts.read_output(d, {"output_bytes": 10}, ex.Config())
            self.assertEqual((text, total, dropped), ("A" * 10, 10, 0))
            (d / "output.log").write_bytes(b"HEAD")
            (d / "output.tail").write_bytes(b"xxTAIL")
            text, total, dropped = artifacts.read_output(d, {"output_bytes": 8}, ex.Config())
            self.assertEqual((text, dropped), ("HEADTAIL", 0))
            text, total, dropped = artifacts.read_output(d, {"output_bytes": 100}, ex.Config())
            self.assertEqual(dropped, 100 - 4 - 6)
            self.assertTrue(text.startswith("HEAD") and text.endswith("xxTAIL"))
            self.assertIn("dropped", text)


class ConnectionPatterns(unittest.TestCase):
    def test_known_connection_failures_match(self):
        for text in ("read ECONNRESET", "connect ECONNREFUSED 1.2.3.4:443", "getaddrinfo ENOTFOUND api.example.com",
                     "socket hang up", "TypeError: fetch failed", "Connection reset by peer", "Network is unreachable",
                     "stream disconnected before completion", "Could not resolve host: x"):
            self.assertTrue(classify.looks_like_connection_loss(text), text)

    def test_ordinary_errors_do_not_match(self):
        for text in ("SyntaxError: invalid syntax", "AssertionError: 3 != 4", "usage: tool [-h]", "permission denied",
                     "the network layer is documented in README", "timeout of the test suite is 5s"):
            self.assertFalse(classify.looks_like_connection_loss(text), text)

    def test_only_the_tail_of_the_output_counts(self):
        text = "ECONNRESET\n" + "ok line\n" * 5000
        self.assertFalse(classify.looks_like_connection_loss(text))


if __name__ == "__main__":
    unittest.main()
