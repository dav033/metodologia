"""Owner composition identities and supported repository topology."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bt_scheduler_owner_composition import CompositionRuntimeError, OwnerCompositionRuntime, composition_store_path


class OwnerCompositionRuntimeTests(unittest.TestCase):
    def _repo(self, path: Path) -> Path:
        path.mkdir()
        subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(path), "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "--allow-empty", "-qm", "base"], check=True)
        return path

    def _plan(self, roles=("main",)):
        return SimpleNamespace(schema_version="1.3.0", subplans=(object(),), plan_id="REQ-1", revision=1,
                               sha256="a" * 64,
                               tasks=tuple(SimpleNamespace(repository=role) for role in roles))

    def test_store_path_uses_dedicated_project_requirement_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            rdir = Path(directory) / "bitacora" / "metodologia" / "requirements" / "REQ-123-sample"
            self.assertEqual(composition_store_path(rdir, "metodologia", "REQ-123"),
                             Path(directory) / "bitacora" / ".state" / "composition" / "metodologia-REQ-123.db")

    def test_multi_repository_plan_is_refused_with_exact_topology_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = self._repo(Path(directory) / "repo")
            with self.assertRaisesRegex(CompositionRuntimeError,
                                        "OWNER_COMPOSITION_MULTI_REPOSITORY_UNSUPPORTED.*main, web"):
                OwnerCompositionRuntime.create(rdir=Path(directory) / "bitacora", project="p", req="REQ-1",
                                               plan=self._plan(("main", "web")), repositories={"main": repo},
                                               verifier_id="m6")

    def test_same_run_revision_cannot_rebind_composition_store_to_another_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = self._repo(root / "repo-one")
            second = self._repo(root / "repo-two")
            rdir = root / "bitacora" / "p" / "requirements" / "REQ-1-name"
            args = dict(rdir=rdir, project="p", req="REQ-1", plan=self._plan(),
                        verifier_id="m6")
            owner = OwnerCompositionRuntime.create(**args, repositories={"main": first})
            scheduler = SimpleNamespace(snapshot=lambda: SimpleNamespace(revision=1, plan_sha256="a" * 64),
                                        audit_log=lambda: [])
            owner.bind_scheduler(scheduler)
            owner.close()
            other = OwnerCompositionRuntime.create(**args, repositories={"main": second})
            with self.assertRaisesRegex(CompositionRuntimeError, "OWNER_COMPOSITION_STORE_IDENTITY_MISMATCH"):
                other.bind_scheduler(scheduler)
            other.close()


if __name__ == "__main__":
    unittest.main()
