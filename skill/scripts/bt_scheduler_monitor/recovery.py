"""Offline, no-overwrite archive and candidate preparation for M4 stores."""
from __future__ import annotations

import os
import shutil
import sqlite3
import stat
import tempfile
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path

from .recovery_manifest import (
    MAX_MANIFEST_BYTES,
    RecoveryError,
    database_evidence,
    hash_file,
    json_bytes,
    make_manifest,
    verify_artifact,
)
from .retention import apply_retention, vacuum_for_recovery
from .storage_limits import (
    MAX_STORE_BYTES,
    WRITE_RESERVE_BYTES,
    StoreError,
    measured_store_bytes,
)
from .store import MonitorStore


def export_archive(source: str | Path, archive: str | Path, manifest: str | Path, *,
                   max_store_bytes: int = MAX_STORE_BYTES) -> dict[str, object]:
    """Export a consistent, standalone SQLite backup without opening the source database."""
    source_path = _source_path(source)
    archive_path, manifest_path = _output_paths(archive, manifest)
    _validate_cap(max_store_bytes)
    if source_path in (archive_path.resolve(strict=False), manifest_path.resolve(strict=False)):
        raise RecoveryError("source and archive outputs must be different paths")
    _require_absent(archive_path, manifest_path)
    before = _source_signature(source_path)
    source_bytes = measured_store_bytes(source_path)
    if source_bytes > max_store_bytes:
        raise StoreError(f"storage_pressure: source_bytes={source_bytes} limit_bytes={max_store_bytes}")
    sidecar_bytes = sum(item["size_bytes"] for item in before.values() if item["exists"])
    _require_free_space(archive_path.parent, sidecar_bytes + source_bytes + 2 * WRITE_RESERVE_BYTES)

    archive_stage: Path | None = None
    manifest_stage: Path | None = None
    published = False
    with tempfile.TemporaryDirectory(prefix=".m4-archive-", dir=archive_path.parent) as workspace:
        scratch = Path(workspace) / "source.sqlite3"
        archive_stage = Path(workspace) / "archive.sqlite3"
        _copy_source_bundle(source_path, scratch, before)
        _backup(scratch, archive_stage)
        if before != _source_signature(source_path):
            raise RecoveryError("source changed during offline archive; no archive was published")
        evidence = database_evidence(archive_stage)
        archive_size = archive_stage.stat().st_size
        if archive_size > max_store_bytes:
            raise StoreError(f"storage_pressure: archive_bytes={archive_size} limit_bytes={max_store_bytes}")
        body = make_manifest(archive_stage, "archive", evidence)
        manifest_stage = _stage_manifest(manifest_path, body)
        _publish_no_replace(archive_stage, archive_path)
        published = True
        try:
            _publish_no_replace(manifest_stage, manifest_path)
        except BaseException:
            _unlink_if_owned(archive_path, archive_stage)
            published = False
            raise
        _sync_directory(archive_path.parent)
        if manifest_path.parent != archive_path.parent:
            _sync_directory(manifest_path.parent)
        if before != _source_signature(source_path):
            if published and archive_stage is not None:
                _unlink_if_owned(archive_path, archive_stage)
                _unlink_if_owned(manifest_path, manifest_stage)
                published = False
            raise RecoveryError("source changed during offline archive; published output was rolled back")
    if not published:
        raise RecoveryError("archive publication did not complete")
    return _summary(archive_path, manifest_path, body)


def verify_archive(archive: str | Path, manifest: str | Path) -> dict[str, object]:
    return verify_artifact(archive, manifest, expected_type="archive")


def verify_candidate(candidate: str | Path, manifest: str | Path) -> dict[str, object]:
    return verify_artifact(candidate, manifest, expected_type="candidate")


def prepare_candidate(archive: str | Path, archive_manifest: str | Path,
                      candidate: str | Path, candidate_manifest: str | Path, *,
                      sqlite_temp_dirs: Iterable[str | Path],
                      max_store_bytes: int = MAX_STORE_BYTES,
                      now: datetime | None = None) -> dict[str, object]:
    """Prepare a compact candidate from a verified archive; never write the archive or source."""
    archive_path, archive_manifest_path = _output_paths(archive, archive_manifest)
    candidate_path, candidate_manifest_path = _output_paths(candidate, candidate_manifest)
    _validate_cap(max_store_bytes)
    temp_dirs = _validate_temp_dirs(sqlite_temp_dirs)
    if not temp_dirs:
        raise StoreError("recovery_vacuum_space_unavailable: pass every sqlite_temp_dirs path explicitly")
    if candidate_path.resolve(strict=False) in (archive_path.resolve(strict=False),
                                                archive_manifest_path.resolve(strict=False)):
        raise RecoveryError("candidate outputs must be separate from the verified archive")
    if candidate_manifest_path.resolve(strict=False) in (archive_path.resolve(strict=False),
                                                         archive_manifest_path.resolve(strict=False)):
        raise RecoveryError("candidate outputs must be separate from the verified archive")
    _require_absent(candidate_path, candidate_manifest_path)
    verified = verify_archive(archive_path, archive_manifest_path)
    archive_hash = str(verified["sha256"])
    archive_size = archive_path.stat().st_size
    if measured_store_bytes(archive_path) > max_store_bytes:
        raise StoreError(f"storage_pressure: archive_bytes={archive_size} limit_bytes={max_store_bytes}")
    current = now or datetime.now(UTC)
    if current.tzinfo is None or current.utcoffset() is None:
        raise ValueError("now must include a timezone")
    current = current.astimezone(UTC)

    candidate_stage: Path | None = None
    manifest_stage: Path | None = None
    published = False
    try:
        with tempfile.TemporaryDirectory(prefix=".m4-candidate-", dir=candidate_path.parent) as workspace:
            candidate_stage = Path(workspace) / "candidate.sqlite3"
            _backup(archive_path, candidate_stage)
            working_cap = max_store_bytes + 4 * WRITE_RESERVE_BYTES
            retention = apply_retention(candidate_stage, now=current, max_store_bytes=working_cap)
            # apply_retention receives no implicit SQLite temp path; this is the sole recovery VACUUM
            # and receives the complete list supplied by the owner.
            vacuum_size = vacuum_for_recovery(candidate_stage, sqlite_temp_dirs=temp_dirs)
            if vacuum_size + WRITE_RESERVE_BYTES > max_store_bytes:
                raise StoreError(
                    f"storage_pressure: compacted_candidate_bytes={vacuum_size} "
                    f"limit_bytes={max_store_bytes} reserve_bytes={WRITE_RESERVE_BYTES}"
                )

            # Put the active cap into the candidate itself, then refresh its persisted health measurement.
            MonitorStore(candidate_stage, max_store_bytes=max_store_bytes)
            apply_retention(candidate_stage, now=current, max_store_bytes=max_store_bytes)
            _checkpoint(candidate_stage)
            final_size = measured_store_bytes(candidate_stage)
            if final_size + WRITE_RESERVE_BYTES > max_store_bytes:
                raise StoreError(
                    f"storage_pressure: candidate_bytes={final_size} limit_bytes={max_store_bytes} "
                    f"reserve_bytes={WRITE_RESERVE_BYTES}"
                )
            if hash_file(archive_path) != archive_hash:
                raise RecoveryError("verified archive changed during candidate preparation")
            evidence = database_evidence(candidate_stage)
            source_evidence = verified["evidence"]
            if not isinstance(source_evidence, dict):
                raise RecoveryError("verified archive evidence is malformed")
            if evidence["protected"] != source_evidence["protected"]:
                raise RecoveryError("candidate does not preserve open incidents and undelivered outbox records")
            body = make_manifest(candidate_stage, "candidate", evidence, recovery={
                "source_archive_sha256": archive_hash,
                "retention": {
                    "deleted_events": retention.deleted_events,
                    "deleted_incidents": retention.deleted_incidents,
                    "compacted_samples": retention.compacted_samples,
                    "deleted_aggregates": retention.deleted_aggregates,
                    "measured_bytes_before_vacuum": retention.measured_bytes,
                    "vacuumed_bytes": vacuum_size,
                    "storage_pressure": retention.storage_pressure,
                },
            })
            manifest_stage = _stage_manifest(candidate_manifest_path, body)
            _publish_no_replace(candidate_stage, candidate_path)
            published = True
            try:
                _publish_no_replace(manifest_stage, candidate_manifest_path)
            except BaseException:
                _unlink_if_owned(candidate_path, candidate_stage)
                published = False
                raise
            _sync_directory(candidate_path.parent)
            if candidate_manifest_path.parent != candidate_path.parent:
                _sync_directory(candidate_manifest_path.parent)
            result = verify_candidate(candidate_path, candidate_manifest_path)
    except BaseException:
        if published and candidate_stage is not None:
            _unlink_if_owned(candidate_path, candidate_stage)
            _unlink_if_owned(candidate_manifest_path, manifest_stage)
        raise
    return result


def _source_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_symlink() or not path.is_file():
        raise RecoveryError("source must be an existing regular SQLite file")
    return path.resolve(strict=True)


def _output_paths(*values: str | Path) -> tuple[Path, ...]:
    result: list[Path] = []
    for value in values:
        path = Path(value).expanduser().absolute()
        path.parent.mkdir(parents=True, exist_ok=True)
        result.append(path)
    if len({str(path.resolve(strict=False)) for path in result}) != len(result):
        raise RecoveryError("database and manifest paths must be different")
    return tuple(result)


def _validate_cap(value: int) -> None:
    if type(value) is not int or value <= WRITE_RESERVE_BYTES:
        raise ValueError(f"max_store_bytes must be greater than {WRITE_RESERVE_BYTES}")


def _validate_temp_dirs(values: Iterable[str | Path]) -> tuple[Path, ...]:
    if isinstance(values, (str, bytes, Path)):
        raise TypeError("sqlite_temp_dirs must be an iterable of directory paths")
    try:
        return tuple(Path(value).expanduser().absolute() for value in values)
    except (TypeError, ValueError) as exc:
        raise ValueError("sqlite_temp_dirs must contain valid directory paths") from exc


def _require_absent(*paths: Path) -> None:
    for path in paths:
        if os.path.lexists(path):
            raise RecoveryError(f"destination already exists: {path}")


def _source_signature(path: Path) -> dict[str, dict[str, object]]:
    signature: dict[str, dict[str, object]] = {}
    for suffix in ("", "-wal", "-shm"):
        sidecar = Path(str(path) + suffix)
        if sidecar.is_symlink():
            raise RecoveryError("source database sidecars must not be symbolic links")
        exists = sidecar.exists()
        signature[suffix or "database"] = {
            "exists": exists,
            "size_bytes": sidecar.stat().st_size if exists else 0,
            "sha256": hash_file(sidecar) if exists else None,
        }
    return signature


def _copy_source_bundle(source: Path, destination: Path,
                        signature: Mapping[str, Mapping[str, object]]) -> None:
    for key, suffix in (("database", ""), ("-wal", "-wal"), ("-shm", "-shm")):
        if signature[key]["exists"]:
            shutil.copyfile(Path(str(source) + suffix), Path(str(destination) + suffix))


def _backup(source: Path, destination: Path) -> None:
    source_connection: sqlite3.Connection | None = None
    destination_connection: sqlite3.Connection | None = None
    try:
        source_connection = sqlite3.connect(source, timeout=5.0)
        destination_connection = sqlite3.connect(destination, timeout=5.0)
        source_connection.backup(destination_connection, pages=256, sleep=0.01)
        destination_connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error as exc:
        raise RecoveryError(f"SQLite backup failed: {exc}") from exc
    finally:
        if destination_connection is not None:
            destination_connection.close()
        if source_connection is not None:
            source_connection.close()


















def _stage_manifest(destination: Path, body: dict[str, object]) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".stage",
                                        dir=destination.parent)
    stage = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json_bytes(body))
            stream.flush()
            os.fsync(stream.fileno())
        return stage
    except BaseException:
        stage.unlink(missing_ok=True)
        raise


def _publish_no_replace(stage: Path, destination: Path) -> None:
    _restrict_permissions(stage)
    try:
        os.link(stage, destination)
    except FileExistsError as exc:
        raise RecoveryError(f"destination already exists: {destination}") from exc
    except OSError as exc:
        raise RecoveryError(f"cannot publish recovery artifact at {destination}: {exc}") from exc


def _restrict_permissions(path: Path) -> None:
    """Keep M4 databases and manifests readable and writable by the owner only."""
    try:
        os.chmod(path, 0o600)
        mode = stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
    except OSError as exc:
        raise RecoveryError(f"cannot secure recovery artifact permissions: {exc}") from exc
    if mode != 0o600:
        raise RecoveryError("recovery artifacts must have mode 0600")


def _unlink_if_owned(destination: Path, stage: Path | None) -> None:
    if stage is None:
        return
    try:
        if destination.stat().st_ino == stage.stat().st_ino and destination.stat().st_dev == stage.stat().st_dev:
            destination.unlink()
    except FileNotFoundError:
        return


def _checkpoint(path: Path) -> None:
    connection = sqlite3.connect(path, timeout=5.0)
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except sqlite3.Error as exc:
        raise RecoveryError(f"SQLite checkpoint failed: {exc}") from exc
    finally:
        connection.close()








def _require_free_space(directory: Path, required: int) -> None:
    if shutil.disk_usage(directory).free < required:
        raise StoreError(f"recovery_space_unavailable: need_bytes={required}")


def _sync_directory(directory: Path) -> None:
    descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _summary(path: Path, manifest_path: Path, body: dict[str, object]) -> dict[str, object]:
    database = body["database"]
    return {"ok": True, "artifact_type": body["artifact_type"], "path": str(path),
            "manifest": str(manifest_path), "sha256": database["sha256"],
            "size_bytes": database["size_bytes"], "evidence": body["evidence"],
            "recovery": body.get("recovery")}


__all__ = ["MAX_MANIFEST_BYTES", "RecoveryError", "export_archive", "prepare_candidate",
           "verify_archive", "verify_candidate"]
