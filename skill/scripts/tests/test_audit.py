"""Read-only architecture audit inventory contracts."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# bt_core resolves ROOT at import time; isolate the process before importing any
# bitácora modules so this suite can never write into the user's real bitácora.
SAFE_ROOT = Path(tempfile.mkdtemp(prefix="metodologia-audit-root-")) / "bitacora"
os.environ["BITACORA_ROOT"] = str(SAFE_ROOT)
import bt_audit


class AuditInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="metodologia-audit-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bitacora_root = self.base / "bitacora"
        self.bitacora_root.mkdir()
        self.workspace = self.base / "product-workspace"
        self.workspace.mkdir()
        self.project_dir = self.bitacora_root / "demo"
        self.project_dir.mkdir()

    def _repo(self, path: Path, remote: str) -> Path:
        git = path / ".git"
        git.mkdir(parents=True)
        (git / "config").write_text(
            '[remote "origin"]\n\turl = ' + remote + "\n", encoding="utf-8"
        )
        (path / "source.py").write_text("SECRET_SOURCE_MUST_NOT_BE_READ", encoding="utf-8")
        return path

    def _metadata(self, repos, root=None):
        data = {"repos": repos}
        if root is not None:
            data["root"] = root.as_posix()
        (self.project_dir / "project.json").write_text(json.dumps(data), encoding="utf-8")

    def test_inventory_reports_registered_statuses_and_candidates_inside_root(self):
        frontend = self._repo(self.base / "frontend", "https://github.com/example/frontend.git")
        mismatch = self._repo(self.base / "wrong-backend", "https://github.com/example/other.git")
        stale = self.base / "not-a-repository"
        stale.mkdir()
        missing = self.base / "missing-backend"
        registered_inside_root = self._repo(self.workspace / "frontend", "https://github.com/example/frontend.git")
        candidate = self._repo(self.workspace / "unregistered-api", "git@github.com:example/api.git")
        self._repo(self.workspace / "node_modules" / "ignored", "https://github.com/example/ignored.git")
        sibling_candidate = self._repo(self.base / "sibling" / "outside", "https://github.com/example/outside.git")
        self._metadata({
            "frontend": {"remote": "https://github.com/example/frontend", "hint": frontend.as_posix()},
            "backend": {"remote": "https://github.com/example/backend", "hint": mismatch.as_posix()},
            "stale": {"remote": "", "hint": stale.as_posix()},
            "missing": {"remote": "https://github.com/example/missing", "hint": missing.as_posix()},
            "registered-root-child": {"remote": "https://github.com/example/frontend", "hint": registered_inside_root.as_posix()},
        }, self.workspace)
        paths_file = self.bitacora_root / ".state" / "paths.json"
        paths_file.parent.mkdir()
        paths_file.write_text(json.dumps({"demo/frontend": frontend.as_posix()}), encoding="utf-8")
        project_before = (self.project_dir / "project.json").read_bytes()
        paths_before = paths_file.read_bytes()
        original_read_text = Path.read_text

        def reject_product_source(path, *args, **kwargs):
            if path.name == "source.py":
                raise AssertionError("audit inventory must not read product source")
            return original_read_text(path, *args, **kwargs)

        with patch.object(Path, "read_text", reject_product_source):
            result = bt_audit.inventory(self.bitacora_root, "demo")

        statuses = {repo["role"]: repo["status"] for repo in result["registered_repositories"]}
        self.assertEqual(statuses, {
            "backend": "remote_mismatch",
            "frontend": "present",
            "missing": "missing",
            "registered-root-child": "present",
            "stale": "stale",
        })
        self.assertEqual([repo["path"] for repo in result["candidate_repositories"]], [candidate.resolve().as_posix()])
        self.assertNotIn(sibling_candidate.resolve().as_posix(), [r["path"] for r in result["candidate_repositories"]])
        self.assertFalse(result["candidate_scan_truncated"])
        self.assertTrue(result["read_only"])
        self.assertFalse(result["source_content_read"])
        self.assertEqual((self.project_dir / "project.json").read_bytes(), project_before)
        self.assertEqual(paths_file.read_bytes(), paths_before)
        self.assertFalse((self.bitacora_root / ".state" / "repos.json").exists())

    def test_registered_local_path_falls_back_to_hint_and_marks_stale_state(self):
        hinted = self._repo(self.base / "hinted", "https://github.com/example/repo.git")
        self._metadata({"main": {"remote": "https://github.com/example/repo", "hint": hinted.as_posix()}})
        state = self.bitacora_root / ".state"
        state.mkdir()
        (state / "paths.json").write_text(json.dumps({"demo/main": str(self.base / "deleted")}), encoding="utf-8")

        repo = bt_audit.inventory(self.bitacora_root, "demo")["registered_repositories"][0]

        self.assertEqual(repo["status"], "stale")
        self.assertEqual(repo["path"], hinted.resolve().as_posix())
        self.assertIn("stored local path is missing", repo["reason"])

    def test_cli_audit_prints_inventory_without_project_initialization(self):
        import bitacora

        self._metadata({}, self.workspace)
        output = io.StringIO()
        with patch.object(bitacora, "ROOT", self.bitacora_root), \
                patch.object(sys, "argv", ["bitacora.py", "--project", "demo", "audit"]), \
                patch.object(bitacora, "ensure_project", side_effect=AssertionError("must remain read-only")), \
                contextlib.redirect_stdout(output):
            bitacora.main()

        result = json.loads(output.getvalue())
        self.assertEqual(result["project"], "demo")
        self.assertEqual(result["workspace_root"], self.workspace.resolve().as_posix())
        self.assertFalse((self.project_dir / "SUMMARY.md").exists())

    def test_project_resolution_from_cwd_does_not_rebuild_missing_index(self):
        repo = self.base / "registered"
        repo.mkdir()
        state = self.bitacora_root / ".state"
        state.mkdir()
        (state / "paths.json").write_text(json.dumps({"demo/backend": repo.as_posix()}), encoding="utf-8")

        self.assertEqual(bt_audit.project_for_cwd(self.bitacora_root, repo), "demo")
        self.assertFalse((state / "repos.json").exists())

    def test_inventory_redacts_credentials_from_remote_urls(self):
        repo = self._repo(self.base / "credentialed", "https://user:secret@example.com/org/repo.git")
        self._metadata({"main": {
            "remote": "https://token:topsecret@example.com/org/repo.git",
            "hint": repo.as_posix(),
        }})

        result = bt_audit.inventory(self.bitacora_root, "demo")

        registered = result["registered_repositories"][0]
        self.assertEqual(registered["registered_remote"], "https://example.com/org/repo.git")
        self.assertEqual(registered["actual_remote"], "https://example.com/org/repo.git")
        self.assertNotIn("secret", json.dumps(result))
        self.assertNotIn("topsecret", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
