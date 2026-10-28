import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import bt_core
from bitacora_platform.quality_owner_approval import compare
from bitacora_platform.quality_owner_approval import run as run_owner_check


class OwnerApprovalEvidenceTests(unittest.TestCase):
    def test_exact_owner_bytes_are_compared_and_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir, snapshot = root / "requirement", root / "snapshot"
            rdir.mkdir()
            (snapshot / "docs/req021").mkdir(parents=True)
            proposal = b'{"version":1}'
            (snapshot / "docs/req021/propuesta-backing-mesas.json").write_bytes(proposal)
            approval = {"propuestaSha256": hashlib.sha256(proposal).hexdigest(), "aprobadoPor": "owner", "fecha": "2026-10-28", "backings": [], "mesas": []}
            raw = (json.dumps(approval) + "\n").encode()
            host = rdir / "aprobacion-backing-mesas.json"
            host.write_bytes(raw)
            (rdir / "RUN.owner-proposal.json").write_text(json.dumps({"schema": 1, "request": "REQ-021:r13:att-0059:verify", "attempt": "att-0059", "approval": approval}))
            target = snapshot / "docs/req021/aprobacion-backing-mesas.json"
            target.write_bytes(raw)
            spec = SimpleNamespace(argv=("cmp", "--", "docs/req021/aprobacion-backing-mesas.json", str(host)), cwd=".")
            order = SimpleNamespace(plan_id="REQ-021", task_id="T3.4")
            self.assertEqual(compare(order, spec, snapshot, rdir).status, "pass")
            alias = root / "requirement-alias"
            alias.symlink_to(rdir, target_is_directory=True)
            alias_spec = SimpleNamespace(argv=("cmp", "--", "docs/req021/aprobacion-backing-mesas.json", str(alias / host.name)), cwd=".")
            self.assertEqual(compare(order, alias_spec, snapshot, rdir).status, "pass")
            with patch.object(bt_core, "find_req", return_value=alias):
                self.assertEqual(run_owner_check(order, alias_spec, snapshot).status, "pass")
            self.assertFalse(compare(order, spec, snapshot, rdir).sandboxed)
            self.assertIsNone(compare(SimpleNamespace(plan_id="REQ-021", task_id="T2.6"), spec, snapshot, rdir))
            (snapshot / "docs/req021/propuesta-backing-mesas.json").write_bytes(b"changed")
            self.assertEqual(compare(order, spec, snapshot, rdir).status, "unknown")
            (snapshot / "docs/req021/propuesta-backing-mesas.json").write_bytes(proposal)
            target.write_bytes(raw + b" ")
            self.assertEqual(compare(order, spec, snapshot, rdir).status, "fail")
            host.write_bytes(b"{}")
            self.assertEqual(compare(order, spec, snapshot, rdir).status, "unknown")
