"""A gitless check can bind evidence to M6's exact captured snapshot (D-208)."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality.engine import QualityEngine
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.runner import CommandOutcome
from bt_scheduler_quality.store import QualityStore
from test_snapshot import _make_snapshot

CONTEXT = "/run/bt-m6/snapshot.json"
FIXTURE = Path(__file__).parent / "fixtures" / "verify-order-pass.json"


class SnapshotContext(unittest.TestCase):
    def test_trusted_identity_matches_captured_files_and_not_repository_head(self):
        seen = []

        class Reader:
            def run(self, check, snapshot_root, *, timeout_seconds=None, mounts=()):
                mount = next((item for item in mounts if item.target == CONTEXT), None)
                assert mount is not None, "M6 must supply read-only candidate context to a gitless check"
                data = json.loads(Path(mount.source).read_text())
                seen.append(data)
                assert not (snapshot_root / ".git").exists()
                for name, entry in data["files"].items():
                    if entry["kind"] == "file":
                        assert hashlib.sha256((snapshot_root / name).read_bytes()).hexdigest() == entry["sha256"]
                return CommandOutcome("pass", 0, 1, b"context verified", b"", None, True)

        with tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
            _, source, base, snapshot = _make_snapshot(Path(temporary))
            self.assertNotEqual(base, snapshot)
            result = QualityEngine(QualityPolicy(), store, runner=Reader()).verify(json.loads(FIXTURE.read_text()), source)
            self.assertEqual(result["status"], "PASS")
            data = seen[0]
            self.assertEqual(data["schema"], "m6.snapshot-context/1")
            self.assertEqual((data["snapshot_sha"], data["base_sha"]), (snapshot, base))
            self.assertEqual(data["manifest_sha256"], hashlib.sha256(source.manifest_path.read_bytes()).hexdigest())
            self.assertEqual(data["files"]["tracked.txt"]["sha256"], hashlib.sha256(b"dirty tracked data\n").hexdigest())
            serialized = json.dumps(data["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            self.assertEqual(data["content_sha256"], hashlib.sha256(serialized).hexdigest())

    @unittest.skipUnless(shutil.which("bwrap"), "requires bubblewrap")
    def test_real_sandbox_cannot_replace_context_or_confuse_it_with_workspace_input(self):
        check = '''import hashlib, json, pathlib
p = pathlib.Path("/run/bt-m6/snapshot.json")
d = json.loads(p.read_text())
assert d["schema"] == "m6.snapshot-context/1"
assert d["snapshot_sha"] != d["base_sha"]
assert d["files"]["tracked.txt"]["sha256"] == hashlib.sha256(pathlib.Path("tracked.txt").read_bytes()).hexdigest()
assert not pathlib.Path(".git").exists()
try:
    p.write_text("{}")
except OSError:
    pass
else:
    raise AssertionError("trusted context was writable")
print("read-only snapshot context verified")
'''
        with tempfile.TemporaryDirectory() as temporary, QualityStore(":memory:") as store:
            _, source, _, _ = _make_snapshot(Path(temporary), files={
                "check_context.py": check, "run/bt-m6/snapshot.json": '{"snapshot_sha":"untrusted"}',
            })
            order = json.loads(FIXTURE.read_text())
            order["verification"][0]["value"] = "python3 check_context.py"
            result = QualityEngine(QualityPolicy(toolchain=False), store).verify(order, source)
            self.assertEqual(result["status"], "PASS", result)
            self.assertIn(b"read-only snapshot context verified", store.get_artifact(result["checks"][0]["stdout_ref"]))


if __name__ == "__main__":
    unittest.main()
