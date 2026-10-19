"""Read-only validation and materialization of a captured M3 Git snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .contracts import QualityError
from .policy import QualityPolicy
from .snapshot_archive import SnapshotArchive
from .snapshot_git import run_git
from .snapshot_tree import SnapshotTreeVerifier

SHA_LENGTHS = frozenset({40, 64})
MANIFEST_LIMIT = 1_048_576


@dataclass(frozen=True)
class SnapshotSource:
    """Paths and SHAs read from the trusted M3 attempt description, not from agent-authored files."""

    attempt_id: str
    repository: Path
    artifact_root: Path
    manifest_path: Path
    base_sha: str
    snapshot_sha: str
    worktree: Path | None = None  # the attempt's own checkout (dependencies), derived from the trusted attempt layout


@dataclass(frozen=True)
class MaterializedSnapshot:
    directory: Path
    base_sha: str
    snapshot_sha: str
    manifest_sha256: str
    archive_sha256: str
    uncompressed_bytes: int
    file_count: int


class SnapshotResolver:
    """Validate M3 provenance and delegate bounded Git tree reconstruction."""

    def __init__(self, policy: QualityPolicy):
        self.policy = policy
        self.archive = SnapshotArchive(policy)
        self.tree = SnapshotTreeVerifier(policy)

    @contextmanager
    def materialize(self, source: SnapshotSource) -> Iterator[MaterializedSnapshot]:
        with tempfile.TemporaryDirectory(prefix="m6-snapshot-") as temporary:
            temp_root = Path(temporary)
            _manifest, manifest_hash, repo = self._validated_manifest(source)
            base_sha, snapshot_sha = self._validated_commits(repo, source)
            archive_path = temp_root / "snapshot.tar"
            archive_hash = self.archive.write_archive(repo, snapshot_sha, archive_path)
            checkout = temp_root / "snapshot"
            checkout.mkdir(mode=0o700)
            self.archive.extract(archive_path, checkout)
            expected = self.tree.tree_entries(repo, snapshot_sha)
            byte_count, file_count = self.tree.verify_tree(
                repo, expected, checkout, snapshot_sha
            )
            archive_path.unlink()
            yield MaterializedSnapshot(
                checkout,
                base_sha,
                snapshot_sha,
                manifest_hash,
                archive_hash,
                byte_count,
                file_count,
            )

    def _validated_manifest(
        self, source: SnapshotSource
    ) -> tuple[dict[str, object], str, Path]:
        if (
            not _valid_identity(source.attempt_id)
            or not _valid_sha(source.base_sha)
            or not _valid_sha(source.snapshot_sha)
        ):
            raise QualityError(
                "SNAPSHOT_INVALID",
                "M3 description contains invalid identity or commit IDs",
            )
        try:
            manifest_relative = source.manifest_path.relative_to(source.artifact_root)
            _reject_symlink_components(source.artifact_root, manifest_relative)
            repo = source.repository.resolve(strict=True)
            artifact_root = source.artifact_root.resolve(strict=True)
            manifest_path = source.manifest_path.resolve(strict=True)
            manifest_path.relative_to(artifact_root)
        except (OSError, ValueError) as error:
            raise QualityError(
                "HANDOFF_MISSING",
                "M3 repository or manifest is outside its trusted artifact root",
            ) from error
        if (
            not repo.is_dir()
            or not artifact_root.is_dir()
            or not manifest_path.is_file()
        ):
            raise QualityError(
                "HANDOFF_MISSING", "M3 repository or handoff manifest is unavailable"
            )
        raw = _read_private_manifest(manifest_path)
        try:
            manifest = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as error:
            raise QualityError(
                "HANDOFF_MISSING", "M3 handoff manifest is not valid JSON"
            ) from error
        if not isinstance(manifest, dict):
            raise QualityError(
                "HANDOFF_MISSING", "M3 handoff manifest must be an object"
            )
        if (
            type(manifest.get("schema")) is not int
            or manifest.get("schema") != 1
            or manifest.get("status") != "captured"
            or manifest.get("attempt_id") != source.attempt_id
        ):
            raise QualityError(
                "HANDOFF_MISSING",
                "M3 handoff identity or status does not match the order",
            )
        if not _same_repository(manifest.get("repository"), repo):
            raise QualityError(
                "HANDOFF_MISSING",
                "M3 handoff repository does not match the attempt description",
            )
        if (
            manifest.get("base_sha") != source.base_sha
            or manifest.get("snapshot_sha") != source.snapshot_sha
        ):
            raise QualityError(
                "HANDOFF_MISSING",
                "M3 handoff commit IDs disagree with the attempt description",
            )
        return manifest, hashlib.sha256(raw).hexdigest(), repo

    def _validated_commits(self, repo: Path, source: SnapshotSource) -> tuple[str, str]:
        base_sha = _resolve_commit(repo, source.base_sha)
        snapshot_sha = _resolve_commit(repo, source.snapshot_sha)
        ancestry = run_git(
            repo, "merge-base", "--is-ancestor", base_sha, snapshot_sha, check=False
        )
        if ancestry.returncode != 0 and not _published(repo, snapshot_sha):
            raise QualityError(
                "SNAPSHOT_INVALID", "M3 snapshot does not descend from its pinned base"
            )
        return base_sha, snapshot_sha


def _published(repo: Path, snapshot_sha: str) -> bool:
    """A publication task rebases its branch onto the remote main and pushes, so its snapshot no longer descends from
    the base it started from. A snapshot that is already part of `origin/main` is accepted without that ancestry: the
    archive and the tree check below still read exactly the snapshot commit."""
    return run_git(repo, "merge-base", "--is-ancestor", snapshot_sha, "origin/main", check=False).returncode == 0


def _read_private_manifest(path: Path) -> bytes:
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as error:
        raise QualityError(
            "HANDOFF_MISSING", f"M3 manifest is unavailable ({type(error).__name__})"
        ) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MANIFEST_LIMIT:
            raise QualityError(
                "HANDOFF_MISSING", "M3 manifest is not a bounded regular file"
            )
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(MANIFEST_LIMIT + 1)
    except OSError as error:
        raise QualityError(
            "HANDOFF_MISSING", f"M3 manifest cannot be read ({type(error).__name__})"
        ) from None
    finally:
        os.close(fd)
    if len(raw) > MANIFEST_LIMIT:
        raise QualityError("HANDOFF_MISSING", "M3 manifest exceeds its byte cap")
    return raw


def _same_repository(raw: object, repo: Path) -> bool:
    if not isinstance(raw, str) or not raw or len(raw) > 4096:
        return False
    try:
        return Path(raw).resolve(strict=True) == repo
    except (OSError, ValueError):
        return False


def _resolve_commit(repo: Path, sha: str) -> str:
    result = run_git(repo, "rev-parse", "--verify", f"{sha}^{{commit}}", check=False)
    resolved = result.stdout.strip()
    if result.returncode or resolved != sha:
        raise QualityError(
            "SNAPSHOT_INVALID",
            "M3 commit ID is absent or does not identify a full commit",
        )
    return resolved


def _valid_identity(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        return False
    try:
        return len(value.encode("utf-8")) <= 256
    except UnicodeEncodeError:
        return False


def _valid_sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) in SHA_LENGTHS
        and all(char in "0123456789abcdef" for char in value)
    )


def _reject_symlink_components(root: Path, relative: Path) -> None:
    if relative.is_absolute() or ".." in relative.parts:
        raise QualityError(
            "HANDOFF_MISSING", "M3 manifest path is not artifact-relative"
        )
    current = root
    for part in ("", *relative.parts):
        if part:
            current = current / part
        try:
            info = current.lstat()
        except OSError as error:
            raise QualityError(
                "HANDOFF_MISSING",
                f"M3 manifest path is unavailable ({type(error).__name__})",
            ) from None
        if stat.S_ISLNK(info.st_mode):
            raise QualityError(
                "HANDOFF_MISSING", "M3 manifest path contains a symbolic link"
            )
