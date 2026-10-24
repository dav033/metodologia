"""Operator-owned external verification policy probes."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_verification_authority import owner_verification_authority


class VerificationAuthorityTests(unittest.TestCase):
    def _paths(self, root: Path):
        rdir = root / "bitacora" / "demo" / "requirements" / "REQ-001-sample"
        rdir.mkdir(parents=True)
        secrets = root / "secrets.env"
        secrets.write_text("export DB_URL=discarded\n# COMMENT=ignored\ninvalid line\n", encoding="utf-8")
        return rdir, secrets, root / "bitacora" / "demo" / "verification-policy.json"

    def test_resources_check_names_only_in_environment_and_secrets_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, _ = self._paths(Path(temporary))
            authority = owner_verification_authority(rdir, "demo", environ={"TOKEN": "unused"},
                                                     secrets_file=secrets)
            self.assertTrue(authority.resource_available("TOKEN"))
            self.assertTrue(authority.resource_available("DB_URL"))
            self.assertFalse(authority.resource_available("UNKNOWN"))
            self.assertFalse(authority.resource_available("DB_URL=discarded"))

    def test_sandbox_is_permitted_and_external_environments_need_operator_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, policy = self._paths(Path(temporary))
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertTrue(authority.authorize_environment("sandbox", None))
            self.assertFalse(authority.authorize_environment("staging", "owner approved"))
            self.assertFalse(authority.authorize_environment("production", "owner approved"))
            policy.write_text(json.dumps({"allow": [{"environment": "staging", "operator": "owner"}]}),
                              encoding="utf-8")
            self.assertTrue(authority.authorize_environment("staging", "owner approved"))
            self.assertFalse(authority.authorize_environment("production", "owner approved"))
            policy.write_text("not json", encoding="utf-8")
            self.assertFalse(authority.authorize_environment("staging", "owner approved"))

    def test_policy_requires_the_matching_environment_and_refuses_unknown_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, policy = self._paths(Path(temporary))
            policy.write_text(json.dumps({"allow": [{"environment": "production"}]}), encoding="utf-8")
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertTrue(authority.authorize_environment("production", None))
            self.assertFalse(authority.authorize_environment("external_authorized", None))
            policy.write_text(json.dumps({"allow": "production"}), encoding="utf-8")
            self.assertFalse(authority.authorize_environment("production", None))


if __name__ == "__main__":
    unittest.main()
