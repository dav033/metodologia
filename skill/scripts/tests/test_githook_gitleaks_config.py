"""The repo's pre-commit hook scans with the bitácora's gitleaks config, so its allowlist (hex task/trigger keys in
solver files) applies at commit time and nowhere else."""
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
DIGEST = hashlib.md5(b"fixture").hexdigest()  # computed: a literal hex key would trip the very scan under test
KEYS = ('{\n "a": {\n   "key": "pictures:REQ-021:r32:resolution:' + DIGEST + '",\n   "other": 1\n },\n'
        ' "b": {\n   "key": "' + DIGEST + '"\n }\n}\n')


@unittest.skipUnless(shutil.which("gitleaks"), "gitleaks not installed")
class HookConfigTests(unittest.TestCase):
    def _commit(self, relpath: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run = lambda *a: subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *a], cwd=root,
                                            capture_output=True, text=True)
            run("init", "-q")
            (root / "bitacora").mkdir()
            shutil.copy(REPO / "bitacora" / ".gitleaks.toml", root / "bitacora" / ".gitleaks.toml")
            hook = root / ".git" / "hooks" / "pre-commit"
            shutil.copy(REPO / "skill" / "githooks" / "pre-commit", hook)
            hook.chmod(0o755)
            target = root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(KEYS)
            run("add", "-A")
            return run("commit", "-q", "-m", "t")

    def test_solver_keys_are_allowed(self):
        res = self._commit("bitacora/p/requirements/REQ-1/RUN.solver/20261031-1/triggers.json")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)

    def test_same_keys_elsewhere_are_still_refused(self):
        res = self._commit("bitacora/p/notes/triggers.json")
        self.assertNotEqual(res.returncode, 0)


if __name__ == "__main__":
    unittest.main()
