"""REQ-030 step 4: a coordinator's receipt settles a manual check without asking a person, and cannot be stretched to
anything else."""
from __future__ import annotations

import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bt_attestation as att
import bt_scheduler_adapter as adapter
import bt_scheduler_ops as ops

EVIDENCE = "Opened /asesor on an iPhone 14, sent a voice note and saw the transcript appear in under 3 seconds"


class Receipt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.rdir, self.key = Path(self.tmp.name) / "REQ-1", Path(self.tmp.name) / "state" / "attestation.key"
        self.rdir.mkdir()

    def mint(self, **over):
        args = dict(task_id="T9", purpose="voice works on a phone", value="open it on a phone", expected="it renders",
                    evidence=EVIDENCE, by="david")
        args.update(over)
        return att.mint(self.rdir, args.pop("task_id"), args.pop("purpose"), args.pop("value"), args.pop("expected"),
                        args.pop("evidence"), args.pop("by"), key_file=self.key)

    def verify(self, **over):
        args = dict(task_id="T9", purpose="voice works on a phone", value="open it on a phone", expected="it renders")
        args.update(over)
        return att.verify(self.rdir, args.pop("task_id"), args.pop("purpose"), args.pop("value"), args.pop("expected"),
                          key_file=self.key)

    def test_a_receipt_verifies_for_exactly_the_check_it_was_minted_for(self):
        self.assertIsNone(self.verify())                                                   # nothing yet
        path = self.mint()
        self.assertTrue(self.verify().startswith("sha256:"))
        self.assertEqual(stat.S_IMODE(self.key.stat().st_mode), 0o600)                      # the key is private
        self.assertEqual(json.loads(path.read_text())["by"], "david")
        for other in ({"task_id": "T8"}, {"purpose": "voice works on a laptop"}, {"value": "open it on a tablet"},
                      {"expected": "it renders fast"}):
            self.assertIsNone(self.verify(**other), other)                                  # change the check: no receipt

    def test_an_edited_or_foreign_receipt_does_not_verify(self):
        path = self.mint()
        body = json.loads(path.read_text())
        path.write_text(json.dumps({**body, "evidence": EVIDENCE + " (and a second device)"}))   # edited after the seal
        self.assertIsNone(self.verify())
        path.write_text(json.dumps({**body, "seal": "0" * 64}))
        self.assertIsNone(self.verify())
        path.write_text("not json")
        self.assertIsNone(self.verify())
        self.mint()
        self.key.write_bytes(b"another machine's key" * 2)                                    # sealed under a different key
        self.assertIsNone(self.verify())

    def test_the_evidence_has_to_be_in_words(self):
        for short in ("", "ok", "done"):
            with self.assertRaises(att.AttestationError):
                self.mint(evidence=short)
        with self.assertRaises(att.AttestationError):
            self.mint(by=" ")
        self.assertFalse((self.rdir / att.DIR).exists())

    def test_the_verifier_port_reads_the_spec_the_engine_hands_it(self):
        self.mint()
        find = att.lookup(self.rdir, key_file=self.key)
        spec = SimpleNamespace(purpose="voice works on a phone", command="open it on a phone", expected="it renders")
        self.assertTrue(find(SimpleNamespace(task_id="T9"), spec).startswith("sha256:"))
        self.assertIsNone(find(SimpleNamespace(task_id="T3"), spec))


class Operator(unittest.TestCase):
    def test_attest_writes_a_receipt_per_manual_check_and_requeues_the_open_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "REQ-1"
            rdir.mkdir()
            task = SimpleNamespace(verification=[{"type": "command", "value": "true", "purpose": "a"},
                                                 {"type": "manual", "value": "phone", "purpose": "voice works", "expected": "ok"},
                                                 {"type": "manual", "value": "prod", "purpose": "deployed", "expected": ""}])
            plan = SimpleNamespace(task=lambda t: task)
            store = SimpleNamespace(open_reviews_of=lambda t: ("key-1",), retried=[], closed=False)
            store.retry_attested = lambda key, by, why: store.retried.append((key, by))
            store.close = lambda: setattr(store, "closed", True)
            key = Path(tmp) / "state" / "attestation.key"
            real_mint = att.mint
            with patch.object(ops, "bound_plan", return_value=plan), patch.object(ops, "stop_owner", return_value=1), \
                    patch("bt_scheduler_quality.store.QualityStore", return_value=store), \
                    patch("bt_run_stores.paths", return_value={"m6": Path(tmp) / "m6.sqlite3"}), \
                    patch.object(att, "mint", lambda *a, **k: real_mint(*a, **{**k, "key_file": key})):
                lines = ops.attest("p", "REQ-001", rdir, "T9", "", EVIDENCE)
                self.assertEqual(sum(1 for line in lines if line.startswith("attested T9")), 2)
                self.assertEqual(store.retried, [("key-1", "coordinator")])
                self.assertTrue(store.closed)
                self.assertTrue(any("requeued" in line for line in lines))
                only = ops.attest("p", "REQ-001", rdir, "T9", "2", EVIDENCE)                   # one check, by number
                self.assertEqual(sum(1 for line in only if line.startswith("attested")), 1)
                with self.assertRaises(adapter.core.SchedulerError):
                    ops.attest("p", "REQ-001", rdir, "T9", "nothing like this", EVIDENCE)
                with self.assertRaises(adapter.core.SchedulerError):
                    ops.attest("p", "REQ-001", rdir, "T9", "", "too short")


if __name__ == "__main__":
    unittest.main()
