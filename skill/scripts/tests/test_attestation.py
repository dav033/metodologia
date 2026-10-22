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

    def test_a_receipt_bound_to_an_attempt_does_not_cover_the_redone_task(self):
        args = ("T9", "voice works on a phone", "open it on a phone", "it renders")
        att.mint(self.rdir, *args, EVIDENCE, "coordinator", attempt="att-1", key_file=self.key)
        self.assertTrue(att.verify(self.rdir, *args, attempt="att-1", key_file=self.key).startswith("sha256:"))
        self.assertIsNone(att.verify(self.rdir, *args, attempt="att-2", key_file=self.key))    # the task was redone
        self.assertIsNone(att.verify(self.rdir, *args, key_file=self.key))                      # and it is not an unbound receipt
        find = att.lookup(self.rdir, bind_attempt=True, key_file=self.key)
        spec = SimpleNamespace(purpose=args[1], command=args[2], expected=args[3])
        self.assertIsNotNone(find(SimpleNamespace(task_id="T9", attempt_id="att-1"), spec))
        self.assertIsNone(find(SimpleNamespace(task_id="T9", attempt_id="att-2"), spec))

    def test_an_unbound_receipt_is_not_accepted_when_the_gate_binds_attempts(self):
        self.mint()                                                       # the original, task-and-check-only receipt
        spec = SimpleNamespace(purpose="voice works on a phone", command="open it on a phone", expected="it renders")
        order = SimpleNamespace(task_id="T9", attempt_id="att-1")
        self.assertIsNotNone(att.lookup(self.rdir, key_file=self.key)(order, spec))                   # gate off: as before
        self.assertIsNone(att.lookup(self.rdir, bind_attempt=True, key_file=self.key)(order, spec))   # gate on: needs the attempt


class Rotation(Receipt):
    def test_a_rotation_keeps_the_receipts_of_one_generation_and_a_second_drops_them(self):
        self.mint()
        self.assertIsNotNone(self.verify())
        att.rotate(self.key)
        self.assertIsNotNone(self.verify())                      # sealed under the previous key
        self.assertEqual(oct(self.key.stat().st_mode & 0o777), "0o600")
        att.rotate(self.key)
        self.assertIsNone(self.verify())                         # two generations back: the check is asked again
        self.mint()
        self.assertIsNotNone(self.verify())                      # a new receipt is sealed under the new key

    def test_status_names_both_keys_and_a_damaged_one_is_not_used(self):
        att.rotate(self.key)
        att.rotate(self.key)
        self.assertEqual(len(att.key_status(self.key)), 2)
        self.assertTrue(all("valid" in line for line in att.key_status(self.key)))
        self.key.write_bytes(b"short")
        self.assertIn("DAMAGED", att.key_status(self.key)[0])
        self.assertEqual(len(att._keys(self.key)), 1)


class Operator(unittest.TestCase):
    def test_attest_writes_a_receipt_per_manual_check_and_requeues_the_open_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            rdir = Path(tmp) / "REQ-1"
            rdir.mkdir()
            task = SimpleNamespace(verification=[{"type": "command", "value": "true", "purpose": "a"},
                                                 {"type": "manual", "value": "phone", "purpose": "voice works", "expected": "ok"},
                                                 {"type": "manual", "value": "prod", "purpose": "deployed", "expected": ""}])
            plan = SimpleNamespace(task=lambda t: task)
            store = SimpleNamespace(open_reviews_of=lambda t: ("key-1",), open_review_attempts=lambda t: ("att-1",),
                                    retried=[], closed=False)
            store.retry_attested = lambda key, by, why: store.retried.append((key, by))
            store.close = lambda: setattr(store, "closed", True)
            key = Path(tmp) / "state" / "attestation.key"
            real_mint = att.mint
            with patch.object(ops, "bound_plan", return_value=plan), patch.object(ops, "stop_owner", return_value=1), \
                    patch("bt_scheduler_quality.store.QualityStore", return_value=store), \
                    patch("bt_run_stores.paths", return_value={"m6": Path(tmp) / "m6.sqlite3"}), \
                    patch.object(att, "mint", lambda *a, **k: real_mint(*a, **{**k, "key_file": key})):
                lines = ops.attest("p", "REQ-001", rdir, "T9", "", EVIDENCE)
                self.assertEqual(sum(1 for line in lines if line.startswith("attested T9@att-1")), 2)
                self.assertEqual(store.retried, [("key-1", "coordinator")])
                self.assertTrue(store.closed)
                self.assertTrue(any("requeued" in line for line in lines))
                only = ops.attest("p", "REQ-001", rdir, "T9", "2", EVIDENCE)                   # one check, by number
                self.assertEqual(sum(1 for line in only if line.startswith("attested")), 1)
                with self.assertRaises(adapter.core.SchedulerError):
                    ops.attest("p", "REQ-001", rdir, "T9", "nothing like this", EVIDENCE)
                store.open_review_attempts = lambda t: ()                       # nothing is waiting: no attempt to bind to
                with self.assertRaises(adapter.core.SchedulerError):
                    ops.attest("p", "REQ-001", rdir, "T9", "", EVIDENCE)
                with self.assertRaises(adapter.core.SchedulerError):
                    ops.attest("p", "REQ-001", rdir, "T9", "", "too short")


if __name__ == "__main__":
    unittest.main()
