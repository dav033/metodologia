"""Validation and canonical forms for knowledge-delta/1."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import PurePosixPath


KINDS = {"repo", "package", "module", "file", "symbol", "api", "schema", "event", "contract",
         "subplan", "requirement", "task", "test", "fixture", "entrypoint", "screen", "component", "flow"}
RELATIONS = {"IMPORTS", "CALLS", "IMPLEMENTS", "PUBLISHES", "CONSUMES", "PRODUCES", "CONFIGURES", "TESTS",
             "DEPENDS_ON", "DEFINES", "EXPOSES", "CONTAINS", "OWNS", "REFERENCES"}
STATUSES = {"observed", "inferred", "proposed", "unknown"}
SHA = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
ENTITY = re.compile(r"^([a-z]+):([^\s:]+)$")
LINE_REF = re.compile(r"^(.+?):([1-9][0-9]*)(?:-([1-9][0-9]*))?$")
SECRET_SHAPES = (
    re.compile(r"AKIA[0-9A-Z]{16}"), re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"), re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"xox[bp]-[A-Za-z0-9-]{10,}"),
)


class KnowledgeError(ValueError):
    """A stable, safe-to-display contract or storage error."""

    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")


def _secret_scan(value: object) -> None:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True)
    if any(pattern.search(encoded) for pattern in SECRET_SHAPES):
        raise KnowledgeError("SECRET_SHAPE", "delta contains a value matching a secret pattern")


def entity(value: object) -> str:
    if not isinstance(value, str) or not (match := ENTITY.fullmatch(value)) or match.group(1) not in KINDS:
        raise KnowledgeError("INVALID_ENTITY", "entity ids must use a supported kind:name form")
    return value


def safe_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or path.is_absolute() or "\\" in value or any(p in ("", ".", "..") for p in value.split("/")):
        raise KnowledgeError("UNSAFE_PATH", "evidence paths must be safe relative paths")
    parts = [part.lower() for part in path.parts]
    name = parts[-1]
    if any(part.startswith(".env") for part in parts) or name.endswith((".pem", ".key")) or name.startswith(
            ("id_rsa", "credentials", "secrets")):
        raise KnowledgeError("SENSITIVE_PATH", "evidence points to a sensitive path")
    return path.as_posix()


def evidence_ref(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise KnowledgeError("INVALID_EVIDENCE", "evidence refs must be non-empty strings")
    if value.startswith(("symbol:", "test:")):
        prefix, target = value.split(":", 1)
        if prefix not in ("symbol", "test"):
            raise KnowledgeError("INVALID_EVIDENCE", "unsupported evidence ref")
        entity(target if ":" in target else f"{prefix}:{target}")
        return value
    match = LINE_REF.fullmatch(value)
    path_value = match.group(1) if match else value
    path = safe_path(path_value)
    if match and match.group(3) and int(match.group(3)) < int(match.group(2)):
        raise KnowledgeError("INVALID_EVIDENCE", "evidence line ranges must be ascending")
    return f"{path}:{match.group(2)}{('-' + match.group(3)) if match and match.group(3) else ''}" if match else path


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(identity: tuple[str, ...], ref: str, commit: str) -> str:
    payload = canonical_json({"identity": identity, "evidence": ref, "observed_commit": commit})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_delta(raw: object) -> dict:
    try:
        _secret_scan(raw)
    except KnowledgeError:
        raise
    except (TypeError, ValueError):
        raise KnowledgeError("INVALID_DELTA", "delta contains a value that is not JSON-compatible") from None
    if not isinstance(raw, dict):
        raise KnowledgeError("INVALID_DELTA", "delta must be a JSON object")
    required = {"schema", "project", "repository", "observed_commit", "contributor", "observations"}
    if not required <= raw.keys() or raw.get("schema") != "knowledge-delta/1":
        raise KnowledgeError("INVALID_DELTA", "expected schema knowledge-delta/1 and its required fields")
    for key in ("project", "repository", "contributor"):
        value = raw.get(key)
        if not isinstance(value, str) or not value or any(c.isspace() for c in value):
            raise KnowledgeError("INVALID_DELTA", f"{key} must be a non-empty token")
    if not isinstance(raw.get("observed_commit"), str) or not SHA.fullmatch(raw["observed_commit"]):
        raise KnowledgeError("INVALID_COMMIT", "observed_commit must be a full 40-hex commit")
    normalized = dict(raw)
    normalized["observed_commit"] = raw["observed_commit"].lower()
    for collection in ("observations", "contradictions", "stale"):
        rows = raw.get(collection, [] if collection != "observations" else None)
        if not isinstance(rows, list):
            raise KnowledgeError("INVALID_DELTA", f"{collection} must be an array")
        result = []
        for row in rows:
            if not isinstance(row, dict):
                raise KnowledgeError("INVALID_DELTA", f"{collection} entries must be objects")
            if collection == "observations":
                if not {"subject", "relation", "object", "status", "evidence"} <= row.keys():
                    raise KnowledgeError("INVALID_DELTA", "observation is missing a required field")
                if not isinstance(row["status"], str) or row["status"] not in STATUSES:
                    raise KnowledgeError("INVALID_STATUS", "status must be observed, inferred, proposed or unknown")
                if not isinstance(row["evidence"], list) or not row["evidence"]:
                    raise KnowledgeError("INVALID_EVIDENCE", "observations need at least one evidence ref")
                item = {k: entity(row[k]) for k in ("subject", "object")}
                item["relation"] = row["relation"]
                item["status"] = row["status"]
                item["evidence"] = sorted({evidence_ref(ref) for ref in row["evidence"]})
            else:
                if not {"subject", "relation", "object", "evidence", "reason"} <= row.keys() and collection == "contradictions":
                    raise KnowledgeError("INVALID_DELTA", "contradiction is missing a required field")
                if not {"subject", "relation", "object", "reason"} <= row.keys() and collection == "stale":
                    raise KnowledgeError("INVALID_DELTA", "stale entry is missing a required field")
                item = {k: entity(row[k]) for k in ("subject", "object")}
                item["relation"] = row["relation"]
                if not isinstance(row["reason"], str) or not row["reason"]:
                    raise KnowledgeError("INVALID_DELTA", "reason must be non-empty")
                item["reason"] = row["reason"]
                if collection == "contradictions":
                    if not isinstance(row["relation"], str) or row["relation"] not in RELATIONS or not isinstance(
                            row["evidence"], list) or not row["evidence"]:
                        raise KnowledgeError("INVALID_EVIDENCE", "contradictions need a supported relation and evidence")
                    item["evidence"] = sorted({evidence_ref(ref) for ref in row["evidence"]})
            if not isinstance(item["relation"], str) or item["relation"] not in RELATIONS:
                raise KnowledgeError("INVALID_RELATION", "relation is not in the supported closed set")
            result.append(item)
        normalized[collection] = result
    return normalized
