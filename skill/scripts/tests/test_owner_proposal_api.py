import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_owner_proposal_api as api
import bt_plans_api as plans


class ProposalApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = b'{"backings":[{"id":"a"}],"mesas":[{"tipo":"b"}]}'
        self.digest = hashlib.sha256(self.raw).hexdigest()
        self.form = {"project": "pictures", "req": "REQ-021", "request": "r", "attempt": "att",
                     "sha256": self.digest, "option": "owner_proposal", "selection": '{"backings":[],"mesas":[]}'}
        self.patches = [patch.object(api.plans, "req_dir", return_value=self.root),
                        patch.object(api.proposal, "verified_proposal", return_value=(self.raw, {"request": "r", "attempt": "att"}))]
        for mocked in self.patches:
            mocked.start()
            self.addCleanup(mocked.stop)

    def test_empty_selection_and_repeat(self):
        api.decide(self.root, self.form)
        api.decide(self.root, self.form)
        saved = json.loads((self.root / "aprobacion-backing-mesas.json").read_text())
        self.assertEqual(saved["backings"], [])
        self.assertEqual(saved["mesas"], [])

    def test_stale_and_invalid_input_have_no_effect(self):
        for changes in ({"sha256": "old"}, {"request": "old"},
                        {"selection": '{"backings":["a","a"],"mesas":[]}'},
                        {"selection": '{"backings":["missing"],"mesas":[]}'}):
            with self.subTest(changes=changes), self.assertRaises(plans.PlanError):
                api.decide(self.root, {**self.form, **changes})
            self.assertFalse((self.root / "aprobacion-backing-mesas.json").exists())
