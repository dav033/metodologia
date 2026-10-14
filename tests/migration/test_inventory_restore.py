"""Preservation drills use disposable source, state, backup and restore roots."""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill" / "scripts"))

import migration_inventory as inventory  # noqa: E402


class InventoryRestoreTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="migration-preservation-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source"
        self.state = self.root / "live"
        self.source.mkdir()
        self.state.mkdir()
        self.backup = self.root / "backup"
        self.restored = self.root / "restored"

    def capture(self, **kwargs: object) -> dict:
        return inventory.capture(self.source, self.state, self.backup, **kwargs)

    def test_restores_dirty_untracked_binary_and_dot_state_exactly(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.source)], check=True)
        tracked = self.source / "tracked.py"
        tracked.write_bytes(b"old\n")
        subprocess.run(["git", "-C", str(self.source), "add", "."], check=True)
        tracked.write_bytes(b"dirty\x00\xff\n")
        (self.source / "untracked.py").write_bytes(b"new\r\n")
        (self.source / ".hidden").write_bytes(b"hidden")
        (self.source / "empty").mkdir()
        (self.state / ".state").mkdir()
        payload = b'{"id":99,"unknown":{"keep":true}}\n'
        (self.state / ".state" / "ids.json").write_bytes(payload)
        manifest = self.capture()
        inventory.restore(self.backup, self.restored)
        for relative in ("tracked.py", "untracked.py", ".hidden"):
            self.assertEqual((self.restored / "source" / relative).read_bytes(),
                             (self.source / relative).read_bytes())
        self.assertEqual((self.restored / "state/.state/ids.json").read_bytes(), payload)
        self.assertTrue((self.restored / "source/empty").is_dir())
        self.assertFalse((self.restored / "source/.git").exists())
        self.assertFalse(manifest["transaction_consistent"])
        self.assertEqual(manifest["roots"]["state"]["kind"], "live-state")
        self.assertIn(".git", [item["path"] for item in manifest["excluded"]["source"]])
        for path in [self.backup, *self.backup.rglob("*")]:
            self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0)

    def test_preserves_external_and_broken_symlinks_without_reading_targets(self) -> None:
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "secret").write_bytes(b"never copied")
        (self.source / "escape").symlink_to(outside, target_is_directory=True)
        (self.source / "broken").symlink_to("missing")
        self.capture()
        inventory.restore(self.backup, self.restored)
        self.assertEqual(os.readlink(self.restored / "source/escape"), str(outside))
        self.assertEqual(os.readlink(self.restored / "source/broken"), "missing")
        self.assertFalse(any(b"never copied" in p.read_bytes()
                             for p in self.backup.rglob("*") if p.is_file()))

    def test_mutation_of_previously_read_file_rejects_capture(self) -> None:
        changed = self.source / "a"
        changed.write_bytes(b"before")
        (self.source / "z").write_bytes(b"later")
        original = os.read

        def mutate(fd: int, size: int) -> bytes:
            data = original(fd, size)
            if data == b"later":
                changed.write_bytes(b"after!")
            return data

        with patch.object(os, "read", side_effect=mutate):
            with self.assertRaisesRegex(inventory.InventoryError, "CHANGED"):
                self.capture()
        self.assertFalse((self.backup / "manifest.json").exists())

    def test_existing_restore_or_backup_destination_is_never_overwritten(self) -> None:
        self.capture()
        self.restored.mkdir()
        marker = self.restored / "owned"
        marker.write_bytes(b"keep")
        with self.assertRaisesRegex(inventory.InventoryError, "DESTINATION"):
            inventory.restore(self.backup, self.restored)
        with self.assertRaisesRegex(inventory.InventoryError, "DESTINATION"):
            self.capture()
        self.assertEqual(marker.read_bytes(), b"keep")

    def test_nested_backup_and_special_files_are_rejected(self) -> None:
        with self.assertRaisesRegex(inventory.InventoryError, "OVERLAP"):
            inventory.capture(self.source, self.state, self.source / "backup")
        os.mkfifo(self.source / "fifo")
        with self.assertRaisesRegex(inventory.InventoryError, "UNSUPPORTED"):
            self.capture()

    def test_corrupt_payload_and_traversal_manifest_are_rejected(self) -> None:
        (self.source / "file").write_bytes(b"original")
        manifest = self.capture()
        blob = self.backup / "payload/source/file"
        blob.write_bytes(b"corrupt")
        with self.assertRaisesRegex(inventory.InventoryError, "HASH"):
            inventory.restore(self.backup, self.restored)
        manifest["entries"]["source"]["../outside"] = manifest["entries"]["source"]["file"]
        (self.backup / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(inventory.InventoryError, "MANIFEST"):
            inventory.restore(self.backup, self.root / "other")
        self.assertFalse((self.root / "outside").exists())

    def test_limits_fail_without_success_manifest(self) -> None:
        (self.source / "large").write_bytes(b"123456789")
        with self.assertRaisesRegex(inventory.InventoryError, "LIMIT"):
            self.capture(max_bytes=4)
        self.assertFalse((self.backup / "manifest.json").exists())


    def test_nested_git_is_preserved_but_root_git_and_caches_are_not(self) -> None:
        (self.source / ".git").mkdir()
        (self.source / ".git" / "HEAD").write_bytes(b"root history is in the bundle")
        nested = self.source / "vendor" / "lib" / ".git"
        nested.mkdir(parents=True)
        (nested / "HEAD").write_bytes(b"nested repository")
        (self.source / "vendor" / "__pycache__").mkdir()
        (self.source / "vendor" / "__pycache__" / "x.pyc").write_bytes(b"cache")
        self.capture()
        inventory.restore(self.backup, self.restored)
        self.assertFalse((self.restored / "source/.git").exists())
        self.assertEqual((self.restored / "source/vendor/lib/.git/HEAD").read_bytes(), b"nested repository")
        self.assertFalse((self.restored / "source/vendor/__pycache__").exists())

    def test_state_inside_source_is_captured_once_as_state(self) -> None:
        inner = self.source / "bitacora" / ".state"
        inner.mkdir(parents=True)
        (inner / "ids.json").write_bytes(b"{}")
        (self.source / "code.py").write_bytes(b"x")
        manifest = inventory.capture(self.source, inner, self.backup)
        self.assertNotIn("bitacora/.state/ids.json", manifest["entries"]["source"])
        self.assertIn("ids.json", manifest["entries"]["state"])
        self.assertIn({"path": "bitacora/.state", "reason": "captured-separately-as-state"},
                      manifest["excluded"]["source"])

    def test_failed_restore_leaves_no_partial_tree_and_can_be_retried(self) -> None:
        (self.source / "file").write_bytes(b"original")
        self.capture()
        blob = self.backup / "payload/source/file"
        good = blob.read_bytes()
        blob.write_bytes(b"corrupt!")
        with self.assertRaisesRegex(inventory.InventoryError, "HASH"):
            inventory.restore(self.backup, self.restored)
        self.assertFalse(self.restored.exists())
        self.assertFalse(self.restored.with_name("restored.partial").exists())
        blob.write_bytes(good)
        inventory.restore(self.backup, self.restored)
        self.assertEqual((self.restored / "source/file").read_bytes(), b"original")

    def test_hostile_manifests_raise_inventory_errors_not_tracebacks(self) -> None:
        (self.source / "a").mkdir()
        (self.source / "a" / "b").write_bytes(b"x")
        manifest = self.capture()
        good = json.dumps(manifest)
        hostile = {"non-dict parent": json.loads(good), "deep": None}
        hostile["non-dict parent"]["entries"]["source"] = {"a/b": manifest["entries"]["source"]["a/b"], "a": 5}
        for label, value in hostile.items():
            with self.subTest(label=label):
                text = json.dumps(value) if value is not None else "[" * 100000
                (self.backup / "manifest.json").write_text(text)
                with self.assertRaises(inventory.InventoryError):
                    inventory.restore(self.backup, self.root / f"out-{label[:3]}")

    def test_entry_limit_and_restore_budget_are_enforced(self) -> None:
        for index in range(5):
            (self.source / f"f{index}").write_bytes(b"x")
        with self.assertRaisesRegex(inventory.InventoryError, "LIMIT"):
            self.capture(max_entries=3)
        self.assertFalse((self.backup / "manifest.json").exists())
        self.backup = self.root / "backup2"
        self.capture()
        with self.assertRaisesRegex(inventory.InventoryError, "LIMIT"):
            inventory.restore(self.backup, self.restored, max_entries=2)
        self.assertFalse(self.restored.exists())

    def test_restored_tree_is_private(self) -> None:
        (self.source / "dir").mkdir()
        (self.source / "dir" / "run.sh").write_bytes(b"#!/bin/sh\n")
        os.chmod(self.source / "dir" / "run.sh", 0o755)
        self.capture()
        inventory.restore(self.backup, self.restored)
        for path in [self.restored, *self.restored.rglob("*")]:
            if not path.is_symlink():
                self.assertEqual(stat.S_IMODE(path.stat().st_mode) & 0o077, 0, path)
        self.assertTrue(stat.S_IMODE((self.restored / "source/dir/run.sh").stat().st_mode) & 0o100)


if __name__ == "__main__":
    unittest.main()
