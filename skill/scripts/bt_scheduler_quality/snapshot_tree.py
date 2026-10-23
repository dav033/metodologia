"""Git tree parsing and content verification for materialized M3 snapshots."""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import time
from pathlib import Path, PurePosixPath

from .contracts import QualityError
from .policy import QualityPolicy
from .snapshot_git import (
    GIT_TIMEOUT_SECONDS,
    read_bounded_stream,
    run_git,
    start_git_stream,
    stop_process,
    wait_git_process,
)
from .snapshot_paths import safe_snapshot_path


class SnapshotTreeVerifier:
    """Read the exact committed tree and verify every extracted path and blob."""

    def __init__(self, policy: QualityPolicy):
        self.policy = policy

    def tree_entries(self, repo: Path, snapshot_sha: str) -> dict[str, tuple[str, str]]:
        output = self._read_tree_listing(repo, snapshot_sha)
        return _parse_tree_entries(output, self.policy.max_snapshot_files)

    def _read_tree_listing(self, repo: Path, snapshot_sha: str) -> bytes:
        maximum = self.policy.max_snapshot_files * 4096 + 1_048_576
        command = [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "gc.auto=0",
            "ls-tree",
            "-r",
            "-z",
            "--full-tree",
            snapshot_sha,
        ]
        process = start_git_stream(repo, command, "git tree listing")
        if process.stdout is None:
            stop_process(process)
            raise QualityError(
                "SNAPSHOT_INVALID", "git tree listing did not provide a stream"
            )
        deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
        try:
            output = read_bounded_stream(
                process.stdout,
                maximum,
                deadline,
                timeout_message="git tree listing did not exit before its deadline",
                limit_message="snapshot tree listing exceeds its byte cap",
            )
            wait_git_process(
                process,
                deadline,
                timeout_message="git tree listing did not exit before its deadline",
                failure_message="git could not list the validated snapshot tree",
            )
            return output
        except (OSError, subprocess.SubprocessError) as error:
            stop_process(process)
            raise QualityError(
                "SNAPSHOT_INVALID", f"git tree listing failed ({type(error).__name__})"
            ) from None
        except QualityError:
            stop_process(process)
            raise
        finally:
            process.stdout.close()

    def verify_tree(
        self, repo: Path, expected: dict[str, tuple[str, str]], checkout: Path
    ) -> tuple[int, int]:
        object_format = _git_object_format(repo)
        actual = {
            path.relative_to(checkout).as_posix()
            for path in checkout.rglob("*")
            if path.is_symlink() or not path.is_dir()
        }
        _validate_tree_paths(actual, set(expected))
        byte_count = 0
        for relative, (mode, oid) in expected.items():
            path = checkout.joinpath(*PurePosixPath(relative).parts)
            byte_count += _verify_tree_entry(object_format, path, mode, oid)
            if byte_count > self.policy.max_snapshot_bytes:
                raise QualityError(
                    "SNAPSHOT_INVALID", "snapshot exceeds its uncompressed byte cap"
                )
        return byte_count, len(expected)


def _git_object_format(repo: Path) -> str:
    result = run_git(repo, "rev-parse", "--show-object-format")
    object_format = result.stdout.strip()
    if object_format not in {"sha1", "sha256"}:
        raise QualityError(
            "SNAPSHOT_INVALID", "repository uses an unsupported Git object format"
        )
    return object_format


def _parse_tree_entries(
    output: bytes, maximum_files: int
) -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        path, mode_text, oid_text, object_type = _parse_tree_record(record)
        if (
            object_type != b"blob"
            or mode_text not in {"100644", "100755", "120000"}
            or not safe_snapshot_path(path)
            or len(oid_text) not in {40, 64}
            or any(char not in "0123456789abcdef" for char in oid_text)
            or path in entries
        ):
            raise QualityError(
                "SNAPSHOT_INVALID", "git tree contains an unsupported entry"
            )
        entries[path] = (mode_text, oid_text)
        if len(entries) > maximum_files:
            raise QualityError(
                "SNAPSHOT_INVALID", "snapshot exceeds its file-count cap"
            )
    return entries


def _parse_tree_record(record: bytes) -> tuple[str, str, str, bytes]:
    try:
        metadata, raw_path = record.split(b"\t", 1)
        mode, object_type, oid = metadata.split(b" ")
        return (
            raw_path.decode("utf-8", errors="strict"),
            mode.decode("ascii"),
            oid.decode("ascii"),
            object_type,
        )
    except (UnicodeDecodeError, ValueError) as error:
        raise QualityError(
            "SNAPSHOT_INVALID", "git tree listing is malformed"
        ) from error


def _validate_tree_paths(actual: set[str], expected: set[str]) -> None:
    if actual != expected:
        raise QualityError(
            "SNAPSHOT_INVALID",
            "materialized snapshot does not match the pinned Git tree",
        )


def _verify_tree_entry(object_format: str, path: Path, mode: str, oid: str) -> int:
    try:
        info = path.lstat()
    except OSError as error:
        raise QualityError(
            "SNAPSHOT_INVALID",
            f"snapshot entry is unavailable ({type(error).__name__})",
        ) from None
    if mode == "120000":
        if not stat.S_ISLNK(info.st_mode):
            raise QualityError(
                "SNAPSHOT_INVALID", "snapshot symlink differs from the Git tree"
            )
        content = os.fsencode(os.readlink(path))
        size = len(content)
        actual_oid = _git_blob_digest(object_format, content)
    else:
        if not stat.S_ISREG(info.st_mode):
            raise QualityError(
                "SNAPSHOT_INVALID", "snapshot file type differs from the Git tree"
            )
        if bool(info.st_mode & 0o111) != (mode == "100755"):
            raise QualityError(
                "SNAPSHOT_INVALID", "snapshot executable bit differs from the Git tree"
            )
        size = info.st_size
        actual_oid = _git_blob_file_digest(object_format, path, size)
    if actual_oid != oid:
        raise QualityError(
            "SNAPSHOT_INVALID", "snapshot file bytes differ from the Git tree"
        )
    return size


def _git_blob_digest(object_format: str, content: bytes) -> str:
    digest = hashlib.new(object_format)
    digest.update(f"blob {len(content)}\0".encode("ascii"))
    digest.update(content)
    return digest.hexdigest()


def _git_blob_file_digest(object_format: str, path: Path, size: int) -> str:
    digest = hashlib.new(object_format)
    digest.update(f"blob {size}\0".encode("ascii"))
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(65_536):
                digest.update(chunk)
    except OSError as error:
        raise QualityError(
            "SNAPSHOT_INVALID",
            f"snapshot file cannot be verified ({type(error).__name__})",
        ) from None
    return digest.hexdigest()
