import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bt_owner_proposal_delivery as delivery
import bt_owner_proposal_store as durable
from bt_owner_proposal import ProposalError
from bt_scheduler_quality.store import QualityStore


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = b'{"backings":[{"id":"b"}],"mesas":[{"tipo":"m"}]}'
        self.approval = {"propuestaSha256": hashlib.sha256(self.raw).hexdigest(), "aprobadoPor": "owner",
                         "fecha": "2026-10-28", "backings": ["b"], "mesas": []}
        with durable.locked(self.root):
            durable.stage(self.root, "req", "att", self.approval)
        self.store = QualityStore(":memory:")
        self.addCleanup(self.store.close)
        snap = SimpleNamespace(tasks={"T3.2": {"attempt": "att", "attempt_state": "verifying"}}, revision=13)
        self.scheduler = SimpleNamespace(snapshot=lambda: snap, plan=object())
        handoff = {"status": "captured", "snapshot_sha": "sha", "repository": "/repo",
                   "refs": {"snapshot": "refs/m3/handoff/test"}}
        executor = SimpleNamespace(describe=lambda attempt: {"handoff": handoff})
        self.wiring = SimpleNamespace(scheduler=self.scheduler, executor=executor, verification_store=self.store)
        self.result = {"status": "NEEDS_REVIEW", "reason_code": "NOT_RUN",
                       "checks": [{"issue_code": "CHECK_MANUAL", "status": "unknown"}],
                       "issues": [{"code": "CRITERION_MANUAL"}],
                       "identity": {"attempt_id": "att", "task_id": "T3.2", "revision": 13},
                       "input": {"snapshot_sha": "sha", "tree_digest": "tree"}}

    def test_queues_once_and_recovers_after_retry(self):
        def run(command, **kwargs):
            output = b"sha\n" if command[-1] == "refs/m3/handoff/test" else b"tree\n" \
                if command[-1] == "sha^{tree}" else self.raw
            return SimpleNamespace(stdout=output)
        with patch.object(self.store, "get_result", return_value=self.result), \
             patch.object(self.store, "open_reviews_of", return_value=("req",)), \
             patch.object(self.store, "retry_attested") as retry, \
             patch.object(delivery.bt_attestation, "manual_checks", return_value=[{"purpose": "p", "value": "v", "expected": "e"}]), \
             patch.object(delivery.bt_attestation, "mint") as mint, patch.object(delivery.subprocess, "run", side_effect=run):
            self.assertTrue(delivery.deliver("pictures", "REQ-021", self.root, self.wiring))
            retry.assert_called_once()
            mint.assert_called_once()
            reason = retry.call_args.args[2]
            self.store._connection.execute("INSERT INTO requests(idempotency_key,input_hash,request_json,state,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                                           ("req", "hash", "{}", "queued", "now", "now"))
            self.store._connection.execute("INSERT INTO verification_retries(request_key,operator,reason,created_at,previous_result_json) VALUES(?,?,?,?,?)",
                                           ("req", "owner", reason, "now", "{}"))
            self.assertFalse(delivery.deliver("pictures", "REQ-021", self.root, self.wiring))
            retry.assert_called_once()

    def test_changed_attempt_does_not_attest(self):
        self.scheduler.snapshot().tasks["T3.2"]["attempt"] = "new"
        with patch.object(delivery.bt_attestation, "mint") as mint, self.assertRaises(ProposalError):
            delivery.deliver("pictures", "REQ-021", self.root, self.wiring)
        mint.assert_not_called()

    def test_real_m6_store_requeues_once_after_receipt(self):
        result = self.result
        raw = json.dumps(result)
        self.store._connection.execute(
            "INSERT INTO requests(idempotency_key,input_hash,request_json,state,result_json,result_hash,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
            ("req", "hash", json.dumps({"task_id": "T3.2"}), "needs_review", raw,
             hashlib.sha256(raw.encode()).hexdigest(), "now", "now"))
        self.store._connection.execute("INSERT INTO reviews(request_key,state,created_at) VALUES(?,?,?)", ("req", "open", "now"))

        def run(command, **kwargs):
            value = b"sha\n" if command[-1] == "refs/m3/handoff/test" else b"tree\n" \
                if command[-1] == "sha^{tree}" else self.raw
            return SimpleNamespace(stdout=value)

        with patch.object(delivery.bt_attestation, "manual_checks", return_value=[{"purpose": "p", "value": "v", "expected": "e"}]), \
             patch.object(delivery.bt_attestation, "mint", side_effect=[OSError("interrupted"), None]) as mint, \
             patch.object(delivery.subprocess, "run", side_effect=run):
            with self.assertRaises(OSError):
                delivery.deliver("pictures", "REQ-021", self.root, self.wiring)
            self.assertTrue((self.root / durable.APPROVAL).exists())
            self.assertEqual(self.store.open_reviews_of("T3.2"), ("req",))
            self.assertTrue(delivery.deliver("pictures", "REQ-021", self.root, self.wiring))
            self.assertEqual(self.store.queued_requests(1)[0][0], "req")
            self.assertFalse(delivery.deliver("pictures", "REQ-021", self.root, self.wiring))
            self.assertEqual(mint.call_count, 2)
