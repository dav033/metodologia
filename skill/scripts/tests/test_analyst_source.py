"""The analyst reads the captured revision rather than an empty temp directory or mutable checkout."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from bitacora_platform import analyst_source


class AnalystSourceTests(unittest.TestCase):
    def test_materialized_source_is_the_exact_snapshot_and_has_no_local_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "checker.py").write_text("captured checker\n")
            subprocess.run(["git", "-C", str(repo), "add", "checker.py"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@t", "commit", "-qm", "snapshot"], check=True)
            sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            (repo / "checker.py").write_text("mutable checkout differs\n")
            (repo / ".env.local").write_text("PRIVATE=not-for-the-analyst\n")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"repository": str(repo), "snapshot_sha": sha, "attempt_id": "att-1"}))
            result = analyst_source.materialize(manifest, root / "analysis")
            self.assertEqual((Path(result["source_directory"]) / "checker.py").read_text(), "captured checker\n")
            self.assertFalse((Path(result["source_directory"]) / ".env.local").exists())
            self.assertEqual(result["source_snapshot"], sha)

    def test_an_invalid_snapshot_is_an_explicit_context_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"repository": str(root), "snapshot_sha": "bad", "attempt_id": "att-1"}))
            with self.assertRaises(ValueError):
                analyst_source.materialize(manifest, root / "analysis")
