"""An owner launched concurrently with an operator hold must not open M6."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bt_scheduler_ops as ops
import bt_scheduler_run as runtime


class OwnerHoldAdmissionTests(unittest.TestCase):
    def test_owner_rechecks_the_hold_after_acquiring_its_ownership_lock(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory) / "REQ-001-x"
            rdir.mkdir()
            with ops.hold(rdir, "attestation mutation"):
                with patch("bt_requirements_gate.require_ready") as gate:
                    with self.assertRaises(runtime.RuntimeErrorCode) as caught:
                        runtime.run("p", "REQ-001", rdir, resume=True, no_autostart=True)
                self.assertEqual(caught.exception.code, "OWNER_HELD")
                gate.assert_not_called()
