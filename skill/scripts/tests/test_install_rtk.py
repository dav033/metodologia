import hashlib
import importlib.util
import io
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import install_rtk


class RtkInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="metodologia-rtk-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.binary = b"known verified test binary"
        archive = io.BytesIO()
        with tarfile.open(fileobj=archive, mode="w:gz") as bundle:
            info = tarfile.TarInfo("release/rtk")
            info.size = len(self.binary)
            bundle.addfile(info, io.BytesIO(self.binary))
        self.archive = archive.getvalue()
        self.patches = [
            patch.object(install_rtk, "ARCHIVE_SHA256", hashlib.sha256(self.archive).hexdigest()),
            patch.object(install_rtk, "BINARY_SHA256", hashlib.sha256(self.binary).hexdigest()),
            patch.object(install_rtk.platform, "system", return_value="Linux"),
            patch.object(install_rtk.platform, "machine", return_value="x86_64"),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def test_rejects_wrong_archive_checksum(self):
        with self.assertRaisesRegex(ValueError, "archive checksum"):
            install_rtk.verified_binary(b"untrusted")

    def test_extracts_only_the_digest_pinned_binary(self):
        self.assertEqual(install_rtk.verified_binary(self.archive), self.binary)

    def test_download_verifies_then_installs_user_binary(self):
        destination = self.root / ".local/bin/rtk"
        response = io.BytesIO(self.archive)
        with patch.object(install_rtk.urllib.request, "urlopen", return_value=response):
            self.assertEqual(install_rtk.install(destination), destination)
        self.assertEqual(destination.read_bytes(), self.binary)
        self.assertEqual(destination.stat().st_mode & 0o777, 0o755)

    def test_is_idempotent_for_same_verified_binary(self):
        destination = self.root / "rtk"
        destination.write_bytes(self.binary)
        destination.chmod(0o755)
        with patch.object(install_rtk.urllib.request, "urlopen", side_effect=AssertionError("network used")):
            self.assertEqual(install_rtk.install(destination), destination)

    def test_preserves_unrelated_existing_file(self):
        destination = self.root / "rtk"
        destination.write_bytes(b"user binary")
        with self.assertRaisesRegex(FileExistsError, "preserved"):
            install_rtk.install(destination)
        self.assertEqual(destination.read_bytes(), b"user binary")

    def test_removes_temporary_binary_after_atomic_publish_failure(self):
        destination = self.root / "rtk"
        response = io.BytesIO(self.archive)
        with patch.object(install_rtk.urllib.request, "urlopen", return_value=response), \
                patch.object(install_rtk.os, "link", side_effect=FileExistsError("concurrent install")):
            with self.assertRaises(FileExistsError):
                install_rtk.install(destination)
        self.assertFalse(destination.exists())
        self.assertEqual(list(self.root.glob(".rtk-*")), [])

    @unittest.skipIf(os.name == "nt", "symlink test requires POSIX user permissions")
    def test_preserves_symlink_destination(self):
        target = self.root / "target"
        target.write_bytes(b"user binary")
        destination = self.root / "rtk"
        destination.symlink_to(target)
        with self.assertRaisesRegex(FileExistsError, "symlink"):
            install_rtk.install(destination)
        self.assertTrue(destination.is_symlink())

    def test_rejects_unverified_platform_before_download(self):
        with patch.object(install_rtk.platform, "machine", return_value="aarch64"), \
                patch.object(install_rtk.urllib.request, "urlopen", side_effect=AssertionError("network used")):
            with self.assertRaisesRegex(RuntimeError, "Linux x86_64"):
                install_rtk.install(self.root / "rtk")

    def test_rtk_only_cli_does_not_run_framework_setup(self):
        install_path = Path(__file__).resolve().parents[3] / "install.py"
        spec = importlib.util.spec_from_file_location("metodologia_install", install_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(install_rtk, "install", return_value=self.root / "rtk"), \
                patch.object(module, "link", side_effect=AssertionError("framework setup ran")), \
                patch.object(module, "claude_hooks", side_effect=AssertionError("hooks changed")), \
                patch.object(module, "codex_hooks", side_effect=AssertionError("hooks changed")):
            module.main(["--rtk-only"])
