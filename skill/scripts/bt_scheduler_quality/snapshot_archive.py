"""Bounded `git archive` creation and safe tar extraction for M3 snapshots."""

from __future__ import annotations

import hashlib
import os
import selectors
import subprocess
import tarfile
import time
from pathlib import Path

from .contracts import QualityError
from .policy import QualityPolicy
from .snapshot_git import (
    GIT_TIMEOUT_SECONDS,
    start_git_stream,
    stop_process,
    wait_git_process,
)
from .snapshot_paths import safe_snapshot_path

ARCHIVE_OVERHEAD_PER_FILE = 1024


class SnapshotArchive:
    """Create an archive within configured limits and extract only safe members."""

    def __init__(self, policy: QualityPolicy):
        self.policy = policy

    def write_archive(self, repo: Path, snapshot_sha: str, archive: Path) -> str:
        maximum = (
            self.policy.max_snapshot_bytes
            + self.policy.max_snapshot_files * ARCHIVE_OVERHEAD_PER_FILE
            + 1_048_576
        )
        command = [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "gc.auto=0",
            "-c",
            "core.attributesFile=/dev/null",
            "archive",
            "--format=tar",
            snapshot_sha,
        ]
        process = start_git_stream(repo, command, "git archive")
        if process.stdout is None:
            stop_process(process)
            raise QualityError(
                "SNAPSHOT_INVALID", "git archive did not provide a stream"
            )
        deadline = time.monotonic() + GIT_TIMEOUT_SECONDS
        try:
            digest = _write_bounded_stream(process.stdout, archive, maximum, deadline)
            wait_git_process(
                process,
                deadline,
                timeout_message="git archive did not exit before its deadline",
                failure_message="git archive could not read the validated snapshot",
            )
            return digest
        except (OSError, subprocess.SubprocessError) as error:
            stop_process(process)
            raise QualityError(
                "SNAPSHOT_INVALID", f"git archive failed ({type(error).__name__})"
            ) from None
        except QualityError:
            stop_process(process)
            raise
        finally:
            process.stdout.close()

    def extract(self, archive: Path, destination: Path) -> tuple[int, int]:
        byte_count, file_count = 0, 0
        try:
            with tarfile.open(archive, mode="r:") as tar:
                for member in tar:
                    file_count += 1
                    if file_count > self.policy.max_snapshot_files:
                        raise QualityError(
                            "SNAPSHOT_INVALID", "snapshot exceeds its file-count cap"
                        )
                    _validate_member(member)
                    byte_count += member.size
                    if byte_count > self.policy.max_snapshot_bytes:
                        raise QualityError(
                            "SNAPSHOT_INVALID",
                            "snapshot exceeds its uncompressed byte cap",
                        )
                    _extract_member(tar, member, destination)
        except QualityError:
            raise
        except (OSError, tarfile.TarError, ValueError, RuntimeError) as error:
            raise QualityError(
                "SNAPSHOT_INVALID",
                f"snapshot archive could not be extracted ({type(error).__name__})",
            ) from None
        return byte_count, file_count


def _write_bounded_stream(
    stream, destination: Path, maximum: int, deadline: float
) -> str:
    digest = hashlib.sha256()
    total = 0
    with destination.open("xb") as output, selectors.DefaultSelector() as selector:
        os.set_blocking(stream.fileno(), False)
        selector.register(stream, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise QualityError(
                    "SNAPSHOT_INVALID", "git archive did not exit before its deadline"
                )
            if not selector.select(min(remaining, 1.0)):
                continue
            try:
                chunk = os.read(stream.fileno(), 65_536)
            except BlockingIOError:
                continue
            if not chunk:
                break
            total += len(chunk)
            if total > maximum:
                raise QualityError(
                    "SNAPSHOT_INVALID", "snapshot archive exceeds its byte cap"
                )
            output.write(chunk)
            digest.update(chunk)
    return digest.hexdigest()


def _extract_member(
    tar: tarfile.TarFile, member: tarfile.TarInfo, destination: Path
) -> None:
    safe = tarfile.data_filter(member, str(destination))
    if safe is None:
        raise QualityError(
            "SNAPSHOT_INVALID", "snapshot archive contains a refused file type"
        )
    tar.extract(safe, path=destination, filter="data")


def _validate_member(member: tarfile.TarInfo) -> None:
    if (
        not safe_snapshot_path(member.name)
        or member.islnk()
        or member.isdev()
        or member.isfifo()
    ):
        raise QualityError(
            "SNAPSHOT_INVALID", "snapshot archive contains an unsafe path or file type"
        )
