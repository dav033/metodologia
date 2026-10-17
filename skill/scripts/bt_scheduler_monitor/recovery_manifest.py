"""Bounded M4 archive manifests and read-only SQLite integrity evidence."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from .storage_limits import WRITE_RESERVE_BYTES
from .store import SCHEMA_VERSION

MANIFEST_VERSION = 1
MAX_MANIFEST_BYTES = 16 * 1024
_REQUIRED_TABLES = (
    "schema_meta", "store_limits", "normalized_events", "source_cursors", "stream_gaps",
    "incidents", "incident_evidence_refs", "m1_outbox",
)
_OPTIONAL_TABLES = ("m4_extension_meta", "metric_samples", "daily_metric_aggregates", "m4_retention_health")
_MANIFEST_FIELDS = frozenset(("manifest_version", "artifact_type", "created_at", "database",
                             "integrity_check", "evidence"))
_DATABASE_FIELDS = frozenset(("size_bytes", "sha256"))
_RECOVERY_FIELDS = frozenset(("source_archive_sha256", "retention"))
_RETENTION_FIELDS = frozenset(("deleted_events", "deleted_incidents", "compacted_samples", "deleted_aggregates",
                               "measured_bytes_before_vacuum", "vacuumed_bytes", "storage_pressure"))


class RecoveryError(RuntimeError):
    """An archive or recovery candidate could not be prepared safely."""


def database_evidence(path: Path) -> dict[str, object]:
    connection = _database_connection(path)
    try:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise RecoveryError("SQLite integrity_check failed")
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if set(_REQUIRED_TABLES) - tables:
            raise RecoveryError("artifact is missing required M4 tables")
        versions = connection.execute("SELECT version FROM schema_meta").fetchall()
        if len(versions) != 1 or versions[0][0] != SCHEMA_VERSION:
            raise RecoveryError("artifact has an unsupported M4 schema identity")
        limits = connection.execute("SELECT max_store_bytes FROM store_limits WHERE singleton=1").fetchall()
        if len(limits) != 1 or type(limits[0][0]) is not int or limits[0][0] <= 0:
            raise RecoveryError("artifact has an invalid active-store limit")
        extension_version: int | None = None
        if "m4_extension_meta" in tables:
            row = connection.execute("SELECT version FROM m4_extension_meta WHERE name='metrics'").fetchone()
            extension_version = None if row is None else row[0]
            if extension_version not in (None, 1, 2):
                raise RecoveryError("artifact has an unsupported M4 metric extension identity")
        counts: dict[str, int | None] = {}
        for table in (*_REQUIRED_TABLES, *_OPTIONAL_TABLES):
            counts[table] = (int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
                             if table in tables else None)
        protected = {
            "open_incidents": _digest_rows(connection,
                "SELECT incident_id,resolution_state,body FROM incidents WHERE resolution_state='open' "
                "ORDER BY incident_id"),
            "open_incident_evidence_refs": _digest_rows(connection,
                "SELECT refs.incident_id,refs.evidence_ref FROM incident_evidence_refs AS refs "
                "JOIN incidents ON incidents.incident_id=refs.incident_id "
                "WHERE incidents.resolution_state='open' ORDER BY refs.incident_id,refs.evidence_ref"),
            "undelivered_outbox": _digest_rows(connection,
                "SELECT idempotency_key,incident_id,body,state,claim_token,lease_until,attempts,last_error "
                "FROM m1_outbox WHERE state!='acked' ORDER BY idempotency_key"),
        }
        return {"schema_version": SCHEMA_VERSION, "configured_max_store_bytes": limits[0][0],
                "metric_extension_version": extension_version, "table_counts": counts, "protected": protected}
    except sqlite3.Error as exc:
        raise RecoveryError(f"SQLite artifact verification failed: {exc}") from exc
    finally:
        connection.close()


def make_manifest(path: Path, artifact_type: str, evidence: dict[str, object], *,
                  recovery: dict[str, object] | None = None) -> dict[str, object]:
    body: dict[str, object] = {
        "manifest_version": MANIFEST_VERSION,
        "artifact_type": artifact_type,
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "database": {"size_bytes": path.stat().st_size, "sha256": hash_file(path)},
        "integrity_check": "ok",
        "evidence": evidence,
    }
    if recovery is not None:
        body["recovery"] = recovery
    if len(json_bytes(body)) > MAX_MANIFEST_BYTES:
        raise RecoveryError("recovery manifest exceeded its bounded size")
    return body


def verify_artifact(path_value: str | Path, manifest_value: str | Path,
                    *, expected_type: str) -> dict[str, object]:
    path = Path(path_value).expanduser().absolute()
    manifest_path = Path(manifest_value).expanduser().absolute()
    body = read_manifest(manifest_path)
    expected_fields = _MANIFEST_FIELDS | ({"recovery"} if expected_type == "candidate" else set())
    if (set(body) != expected_fields or type(body.get("manifest_version")) is not int
            or body.get("manifest_version") != MANIFEST_VERSION or body.get("artifact_type") != expected_type
            or body.get("integrity_check") != "ok"):
        raise RecoveryError("recovery manifest identity is invalid")
    created_at = body.get("created_at")
    if not isinstance(created_at, str):
        raise RecoveryError("recovery manifest timestamp is invalid")
    try:
        parsed = datetime.fromisoformat(created_at[:-1] + "+00:00" if created_at.endswith("Z") else created_at)
    except ValueError as exc:
        raise RecoveryError("recovery manifest timestamp is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RecoveryError("recovery manifest timestamp must include a timezone")
    database = body.get("database")
    if not isinstance(database, dict) or set(database) != _DATABASE_FIELDS:
        raise RecoveryError("recovery manifest database evidence is invalid")
    size_bytes = database.get("size_bytes")
    digest = database.get("sha256")
    if type(size_bytes) is not int or size_bytes <= 0 or not _is_sha256(digest):
        raise RecoveryError("recovery manifest database evidence is invalid")
    if hash_file(path) != digest:
        raise RecoveryError("archive SHA-256 does not match its manifest")
    if path.stat().st_size != size_bytes:
        raise RecoveryError("archive size does not match its manifest")
    evidence = database_evidence(path)
    if json_bytes(body.get("evidence")) != json_bytes(evidence):
        raise RecoveryError("archive schema or manifest evidence does not match the database")
    recovery = body.get("recovery")
    if expected_type == "candidate":
        store_cap = evidence["configured_max_store_bytes"]
        if type(store_cap) is not int or size_bytes + WRITE_RESERVE_BYTES > store_cap:
            raise RecoveryError("candidate does not meet its configured active-store cap")
        if not isinstance(recovery, dict) or set(recovery) != _RECOVERY_FIELDS:
            raise RecoveryError("candidate recovery provenance is invalid")
        if not _is_sha256(recovery.get("source_archive_sha256")):
            raise RecoveryError("candidate recovery provenance is invalid")
        retention = recovery.get("retention")
        if not isinstance(retention, dict) or set(retention) != _RETENTION_FIELDS:
            raise RecoveryError("candidate retention evidence is invalid")
        for field in _RETENTION_FIELDS - {"storage_pressure"}:
            if type(retention.get(field)) is not int or retention[field] < 0:
                raise RecoveryError("candidate retention evidence is invalid")
        if type(retention.get("storage_pressure")) is not bool:
            raise RecoveryError("candidate retention evidence is invalid")
    return {"ok": True, "artifact_type": expected_type, "path": str(path),
            "manifest": str(manifest_path), "sha256": digest, "size_bytes": size_bytes,
            "schema_version": evidence["schema_version"], "evidence": evidence,
            "recovery": recovery}


def read_manifest(path: Path) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise RecoveryError("manifest is missing or not a regular file")
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise RecoveryError("manifest exceeds its size limit")
        body = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise RecoveryError("manifest JSON is invalid") from exc
    if not isinstance(body, dict):
        raise RecoveryError("manifest root must be an object")
    return body


def _database_connection(path: Path) -> sqlite3.Connection:
    if path.is_symlink() or not path.is_file():
        raise RecoveryError("artifact must be an existing regular SQLite file")
    wal_path = Path(str(path) + "-wal")
    if wal_path.exists() and wal_path.stat().st_size:
        raise RecoveryError("artifact is not a standalone SQLite database")
    connection = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def _digest_rows(connection: sqlite3.Connection, sql: str) -> dict[str, object]:
    digest = hashlib.sha256()
    count = 0
    for row in connection.execute(sql):
        body = json.dumps(list(row), ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        digest.update(len(body).to_bytes(4, "big"))
        digest.update(body)
        count += 1
    return {"count": count, "sha256": digest.hexdigest()}


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value: object) -> bytes:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return (encoded + "\n").encode("utf-8")


__all__ = ["MAX_MANIFEST_BYTES", "RecoveryError", "database_evidence", "hash_file", "json_bytes",
           "make_manifest", "verify_artifact"]
