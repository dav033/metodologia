from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from bt_scheduler_quality import QualityError
from bt_scheduler_quality.policy import QualityPolicy
from bt_scheduler_quality.snapshot import SnapshotResolver, SnapshotSource


class SnapshotResolverTests(unittest.TestCase):
    def test_materializes_dirty_and_untracked_snapshot_without_mutating_source_or_manifest(
        self,
    ):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, source, base_sha, snapshot_sha = _make_snapshot(root)
            manifest_bytes = source.manifest_path.read_bytes()
            refs_before = _git(repo, "show-ref")
            head_before = _git(repo, "rev-parse", "HEAD")

            with SnapshotResolver(QualityPolicy()).materialize(source) as snapshot:
                checkout = snapshot.directory
                self.assertEqual(
                    (checkout / "tracked.txt").read_text(encoding="utf-8"),
                    "dirty tracked data\n",
                )
                self.assertEqual(
                    (checkout / "untracked.txt").read_text(encoding="utf-8"),
                    "untracked data\n",
                )
                self.assertEqual(snapshot.base_sha, base_sha)
                self.assertEqual(snapshot.snapshot_sha, snapshot_sha)
                self.assertEqual(len(snapshot.archive_sha256), 64)
                self.assertEqual(
                    snapshot.uncompressed_bytes,
                    len("dirty tracked data\nuntracked data\n"),
                )
                self.assertEqual(snapshot.file_count, 2)
                self.assertFalse((checkout / ".git").exists())

            self.assertFalse(checkout.exists())
            self.assertEqual(_git(repo, "show-ref"), refs_before)
            self.assertEqual(_git(repo, "rev-parse", "HEAD"), head_before)
            self.assertEqual(source.manifest_path.read_bytes(), manifest_bytes)

    def test_rejects_manifest_for_a_different_attempt_before_archiving(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _repo, source, _, _ = _make_snapshot(root)
            data = json.loads(source.manifest_path.read_text(encoding="utf-8"))
            data["attempt_id"] = "att-replaced"
            source.manifest_path.write_text(json.dumps(data), encoding="utf-8")

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy()).materialize(source),
            ):
                self.fail("invalid manifest must not produce a checkout")

        self.assertEqual(raised.exception.code, "HANDOFF_MISSING")

    def test_requires_the_m3_base_to_be_an_ancestor_of_the_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, source, _, snapshot_sha = _make_snapshot(root)
            tree = _git(repo, "rev-parse", f"{snapshot_sha}^{{tree}}")
            unrelated = _git(repo, "commit-tree", tree, "-m", "unrelated root")
            source = SnapshotSource(
                source.attempt_id,
                source.repository,
                source.artifact_root,
                source.manifest_path,
                unrelated,
                source.snapshot_sha,
            )
            data = json.loads(source.manifest_path.read_text(encoding="utf-8"))
            data["base_sha"] = unrelated
            source.manifest_path.write_text(json.dumps(data), encoding="utf-8")

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy()).materialize(source),
            ):
                self.fail(
                    "a snapshot based on an unrelated commit must not be materialized"
                )

        self.assertEqual(raised.exception.code, "SNAPSHOT_INVALID")

    def test_a_snapshot_already_published_to_origin_main_need_not_descend_from_its_base(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo, source, _, snapshot_sha = _make_snapshot(root)
            tree = _git(repo, "rev-parse", f"{snapshot_sha}^{{tree}}")
            unrelated = _git(repo, "commit-tree", tree, "-m", "base before the rebase")
            source = SnapshotSource(
                source.attempt_id, source.repository, source.artifact_root, source.manifest_path,
                unrelated, source.snapshot_sha,
            )
            data = json.loads(source.manifest_path.read_text(encoding="utf-8"))
            data["base_sha"] = unrelated
            source.manifest_path.write_text(json.dumps(data), encoding="utf-8")
            _git(repo, "update-ref", "refs/remotes/origin/main", snapshot_sha)

            with SnapshotResolver(QualityPolicy()).materialize(source) as materialized:
                self.assertEqual(materialized.snapshot_sha, snapshot_sha)

    def test_refuses_manifest_symlink_before_following_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _repo, source, _, _ = _make_snapshot(root)
            external = root / "outside-manifest.json"
            external.write_text(
                source.manifest_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            source.manifest_path.unlink()
            source.manifest_path.symlink_to(external)

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy()).materialize(source),
            ):
                self.fail("a symlinked handoff manifest must not be read")

        self.assertEqual(raised.exception.code, "HANDOFF_MISSING")

    def test_enforces_snapshot_file_cap(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, source, _, _ = _make_snapshot(root)

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy(max_snapshot_files=1)).materialize(
                    source
                ),
            ):
                self.fail("snapshot with two files must exceed a one-file cap")

        self.assertEqual(raised.exception.code, "SNAPSHOT_INVALID")

    def test_rejects_archive_symlink_escaping_the_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, source, _, _ = _make_snapshot(root, unsafe_link=True)

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy()).materialize(source),
            ):
                self.fail("an escaping symlink must not be materialized")

        self.assertEqual(raised.exception.code, "SNAPSHOT_INVALID")

    def test_rejects_git_archive_export_ignore_omitting_snapshot_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, source, _, _ = _make_snapshot(root, export_ignore=True)

            with (
                self.assertRaises(QualityError) as raised,
                SnapshotResolver(QualityPolicy()).materialize(source),
            ):
                self.fail("export-ignore must not silently remove a snapshot file")

        self.assertEqual(raised.exception.code, "SNAPSHOT_INVALID")

    def test_export_subst_files_are_restored_to_the_exact_captured_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, source, _, _ = _make_snapshot(root, export_subst=True)

            with SnapshotResolver(QualityPolicy()).materialize(source) as snapshot:
                self.assertEqual(
                    (snapshot.directory / "substituted.txt").read_text(encoding="utf-8"),
                    "captured $Format:%H$ text\n",
                )
                self.assertEqual(
                    (snapshot.directory / "tracked.txt").read_text(encoding="utf-8"),
                    "dirty tracked data\n",
                )

    def test_other_byte_differences_are_still_rejected(self):
        from bt_scheduler_quality import snapshot_tree

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, source, _, _ = _make_snapshot(root, export_subst=True)
            original = snapshot_tree._has_export_subst
            snapshot_tree._has_export_subst = lambda *args: False
            try:
                with (
                    self.assertRaises(QualityError) as raised,
                    SnapshotResolver(QualityPolicy()).materialize(source),
                ):
                    self.fail("a changed file without export-subst must be rejected")
            finally:
                snapshot_tree._has_export_subst = original

        self.assertEqual(raised.exception.code, "SNAPSHOT_INVALID")


def _make_snapshot(
    root: Path,
    *,
    unsafe_link: bool = False,
    export_ignore: bool = False,
    export_subst: bool = False,
    files: dict[str, str] | None = None,
) -> tuple[Path, SnapshotSource, str, str]:
    repo = root / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "M6 fixture")
    _git(repo, "config", "user.email", "m6-fixture@example.invalid")
    (repo / "tracked.txt").write_text("base data\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-q", "-m", "base")
    base_sha = _git(repo, "rev-parse", "HEAD")
    (repo / "tracked.txt").write_text("dirty tracked data\n", encoding="utf-8")
    (repo / "untracked.txt").write_text("untracked data\n", encoding="utf-8")
    for relative, content in (files or {}).items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    if unsafe_link:
        (repo / "unsafe-link").symlink_to("../../outside-secret")
    attributes = []
    if export_ignore:
        attributes.append("ignored.txt export-ignore")
        (repo / "ignored.txt").write_text(
            "must remain in the snapshot\n", encoding="utf-8"
        )
    if export_subst:
        attributes.append("substituted.txt export-subst")
        (repo / "substituted.txt").write_text(
            "captured $Format:%H$ text\n", encoding="utf-8"
        )
    if attributes:
        (repo / ".gitattributes").write_text(
            "\n".join(attributes) + "\n", encoding="utf-8"
        )
    index = root / "snapshot.index"
    env = {
        "GIT_INDEX_FILE": str(index),
        "GIT_AUTHOR_NAME": "M3 fixture",
        "GIT_AUTHOR_EMAIL": "m3@example.invalid",
        "GIT_COMMITTER_NAME": "M3 fixture",
        "GIT_COMMITTER_EMAIL": "m3@example.invalid",
        "GIT_AUTHOR_DATE": "1970-01-01T00:00:00+0000",
        "GIT_COMMITTER_DATE": "1970-01-01T00:00:00+0000",
    }
    _git(repo, "read-tree", base_sha, env=env)
    _git(repo, "add", "-A", env=env)
    tree = _git(repo, "write-tree", env=env)
    snapshot_sha = _git(
        repo, "commit-tree", tree, "-p", base_sha, "-m", "M3 snapshot", env=env
    )
    artifact_root = root / "m3-artifacts"
    artifact_root.mkdir()
    manifest_path = artifact_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema": 1,
                "attempt_id": "att-001",
                "repository": str(repo),
                "base_sha": base_sha,
                "snapshot_sha": snapshot_sha,
                "status": "captured",
            }
        ),
        encoding="utf-8",
    )
    source = SnapshotSource(
        "att-001", repo, artifact_root, manifest_path, base_sha, snapshot_sha
    )
    return repo, source, base_sha, snapshot_sha


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> str:
    clean_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    clean_env.update(env or {})
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if result.returncode and not (args[0] == "show-ref" and result.returncode == 1):
        raise AssertionError(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout.strip()


if __name__ == "__main__":
    unittest.main()
