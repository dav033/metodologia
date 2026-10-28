import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_owner_proposal_store as store
from bt_owner_proposal import ProposalError


class ProposalStoreTests(unittest.TestCase):
    def test_recovers_after_approval_write_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            approval = {"propuestaSha256": "abc", "backings": [], "mesas": []}
            write = store._write

            def fail_approval(path, value):
                if path.name == store.APPROVAL:
                    raise OSError("simulated interruption")
                write(path, value)

            with store.locked(root), patch.object(store, "_write", side_effect=fail_approval), self.assertRaises(OSError):
                store.stage(root, "request", "attempt", approval)
            self.assertTrue((root / store.JOURNAL).exists())
            with store.locked(root):
                store.stage(root, "request", "attempt", approval)
                store.stage(root, "request", "attempt", approval)
            self.assertEqual(json.loads((root / store.APPROVAL).read_text()), approval)

    def test_concurrent_incompatible_decisions_have_one_winner(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            barrier = threading.Barrier(2)
            results = []

            def submit(value):
                barrier.wait()
                try:
                    with store.locked(root):
                        store.stage(root, "request", "attempt", {"backings": [value]})
                    results.append("accepted")
                except ProposalError:
                    results.append("conflict")

            threads = [threading.Thread(target=submit, args=(value,)) for value in ("one", "two")]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertCountEqual(results, ["accepted", "conflict"])
            self.assertEqual(json.loads((root / store.JOURNAL).read_text())["approval"],
                             json.loads((root / store.APPROVAL).read_text()))
