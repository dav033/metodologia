"""T7 (events): technical events map to M1's vocabulary, are deterministic, persisted write-ahead and carry the facts."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import model as m
from support import World, order


class Events(unittest.TestCase):
    def test_the_vocabulary_is_the_one_the_scheduler_core_ingests(self):
        self.assertEqual(set(ex.EVENT_KINDS), {"execution_started", "execution_finished", "execution_failed",
                                              "execution_cancelled", "heartbeat"})

    def test_the_terminal_event_is_persisted_in_the_same_transaction_as_the_terminal_state(self):
        w = World(self)
        w.sink.fail = True                                    # delivery impossible: the ledger alone must hold the truth
        w.x.start(order(1, "ok"))
        self.assertEqual(w.x.wait_state("att-0001", m.TERMINAL, 30), m.FINISHED)
        kinds = [e["kind"] for e in w.x.ledger.events("att-0001")]
        self.assertEqual(kinds, [m.EV_STARTED, m.EV_FINISHED])
        self.assertTrue(all(not e["delivered"] for e in w.x.ledger.events("att-0001")))

    def test_the_failed_event_carries_cause_handoff_and_artifact_paths(self):
        w = World(self)
        w.x.start(order(1, "quota:1893456000"))
        w.finish("att-0001")
        p = w.sink.of("att-0001", m.EV_FAILED)[0].payload
        self.assertEqual((p["outcome"], p["cause"], p["reset_epoch"], p["returncode"]), ("failed", "quota_exhausted", 1893456000, 1))
        h = p["handoff"]
        self.assertEqual((h["status"], h["dirty"], h["has_commits"]), ("captured", True, False))
        self.assertTrue(Path(h["manifest"]).exists() and Path(h["brief"]).exists())
        self.assertTrue(Path(p["artifacts"]["output"]).exists())
        self.assertEqual((p["provider"], p["model"], p["profile"]), ("fake", "quota:1893456000", "acct-1"))

    def test_a_clean_event_reports_usage_cost_and_output_sizes_as_the_provider_gave_them(self):
        class Rich(support.FakeDriver):
            def classify(self, route, raw, returncode, **kw):
                return ex.Classification("completed", terminal_event=True, usage={"total_tokens": 42}, cost_usd=0.01)
        w = World(self, driver=Rich())
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        p = w.sink.of("att-0001", m.EV_FINISHED)[0].payload
        self.assertEqual((p["usage"], p["cost_usd"]), ({"total_tokens": 42}, 0.01))
        self.assertGreater(p["output"]["bytes"], 0)

    def test_events_are_plain_json_and_carry_no_environment(self):
        w = World(self)
        w.x.start(order(1, "env:PROFILE_TOKEN"))
        w.finish("att-0001")
        text = json.dumps([e.to_dict() for e in w.sink.events])
        self.assertNotIn("secret-for", text)

    def test_the_agents_report_is_labelled_a_claim_in_the_event(self):
        class Claims(support.FakeDriver):
            def prepare(self, route, prompt, workspace, timeout):
                report = prompt.split("Optionally write `")[1].split("`")[0]
                code = f"import json; json.dump({{'status': 'done', 'summary': 'I did it'}}, open({report!r}, 'w'))"
                return ex.Launch(argv=(sys.executable, "-c", code + "; print('TERMINAL-EVENT')"))
        w = World(self, driver=Claims())
        w.x.start(order(1, "ok"))
        w.finish("att-0001")
        claim = w.sink.of("att-0001", m.EV_FINISHED)[0].payload["claim"]
        self.assertEqual(claim, {"status": "done", "summary": "I did it", "claimed": True})

    def test_events_are_delivered_in_ledger_order_per_attempt_even_across_many_attempts(self):
        w = World(self, config=ex.Config(poll_seconds=0.02, max_running=4, grace_seconds=1, timeout_seconds=60))
        for n in range(1, 9):
            w.x.start(order(n, "marker:m"))
        w.x.wait_idle(60)
        for n in range(1, 9):
            kinds = w.sink.kinds(f"att-{n:04d}")
            self.assertEqual(kinds, [m.EV_STARTED, m.EV_FINISHED], n)


if __name__ == "__main__":
    unittest.main()
