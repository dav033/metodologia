"""Operator-owned external verification policy probes."""
from __future__ import annotations

import json
import os
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
            policy.write_text(json.dumps({"allow": [{"environment": "staging", "authorization": "owner approved"}]}),
                              encoding="utf-8")
            self.assertTrue(authority.authorize_environment("staging", "owner approved"))
            self.assertFalse(authority.authorize_environment("production", "owner approved"))
            policy.write_text("not json", encoding="utf-8")
            self.assertFalse(authority.authorize_environment("staging", "owner approved"))

    def test_policy_requires_the_matching_environment_and_refuses_unknown_classes(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, policy = self._paths(Path(temporary))
            policy.write_text(json.dumps({"allow": [{"environment": "production", "authorization": "approved"}]}), encoding="utf-8")
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertTrue(authority.authorize_environment("production", "approved"))
            self.assertFalse(authority.authorize_environment("external_authorized", "approved"))
            policy.write_text(json.dumps({"allow": "production"}), encoding="utf-8")
            self.assertFalse(authority.authorize_environment("production", "approved"))

    def test_external_authority_binds_environment_authorization_and_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, policy = self._paths(Path(temporary))
            policy.write_text(json.dumps({"allow": [{"environment": "staging", "authorization": "Owner approves staging",
                                                       "requirements": ["REQ-001"]}]}), encoding="utf-8")
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertTrue(authority.authorize_environment("staging", "Owner approves staging"))
            self.assertFalse(authority.authorize_environment("staging", "other"))
            self.assertFalse(authority.authorize_environment("staging", "Owner approves staging!"))

    def test_empty_environment_values_and_empty_secret_assignments_are_unavailable(self):
        with tempfile.TemporaryDirectory() as temporary:
            rdir, secrets, _ = self._paths(Path(temporary))
            secrets.write_text("EMPTY_SECRET=\n", encoding="utf-8")
            authority = owner_verification_authority(rdir, "demo", environ={"EMPTY_ENV": ""}, secrets_file=secrets)
            self.assertFalse(authority.resource_available("EMPTY_SECRET"))
            self.assertFalse(authority.resource_available("EMPTY_ENV"))

    def test_policy_and_secret_reads_refuse_symlinks_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rdir, secrets, policy = self._paths(root)
            policy.unlink(missing_ok=True)
            target = root / "policy-target"
            target.write_text(json.dumps({"allow": [{"environment": "production", "authorization": "ok"}]}))
            policy.symlink_to(target)
            secrets.unlink()
            secret_target = root / "secret-target"
            secret_target.write_text("TOKEN=value\n")
            secrets.symlink_to(secret_target)
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertFalse(authority.authorize_environment("production", "ok"))
            self.assertFalse(authority.resource_available("TOKEN"))

    def test_authority_reads_refuse_fifos_and_files_over_the_size_cap(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            rdir, secrets, policy = self._paths(root)
            os.mkfifo(policy)
            secrets.write_text("TOKEN=value\n" + ("# padding\n" * 8000), encoding="utf-8")
            authority = owner_verification_authority(rdir, "demo", environ={}, secrets_file=secrets)
            self.assertFalse(authority.authorize_environment("production", "approved"))
            self.assertFalse(authority.resource_available("TOKEN"))


if __name__ == "__main__":
    unittest.main()
