"""Bounded, immutable source capture for repeated-audit recovery diagnosis."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

SCHEMA = "recovery-evidence/1"
MAX_DOCUMENT_BYTES = 16 * 1024 * 1024
MAX_LEDGER_FILES = 20_000
MAX_LEDGER_BYTES = 512 * 1024 * 1024


class EvidenceError(ValueError):
    """A required source cannot be authenticated as complete historical evidence."""


def _read_json(path: Path, root: Path, *, expected_digest: str | None = None) -> tuple[dict[str, Any], str]:
    relative = path.relative_to(root)
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise EvidenceError(f"symlink source: {relative.as_posix()}")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError as error:
        raise EvidenceError(f"missing source: {relative.as_posix()}") from error
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_DOCUMENT_BYTES:
            raise EvidenceError(f"invalid source file: {relative.as_posix()}")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(MAX_DOCUMENT_BYTES + 1)
    finally:
        os.close(fd)
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise EvidenceError(f"oversized source: {relative.as_posix()}")
    digest = hashlib.sha256(raw).hexdigest()
    if expected_digest is not None and digest != expected_digest:
        raise EvidenceError(f"source digest mismatch: {relative.as_posix()}")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceError(f"malformed source: {relative.as_posix()}") from error
    if not isinstance(value, dict):
        raise EvidenceError(f"source must be an object: {relative.as_posix()}")
    return value, digest


def _safe_relative(value: object) -> PurePosixPath:
    if not isinstance(value, str):
        raise EvidenceError("invalid snapshot path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in ("", ".", "..") for part in path.parts):
        raise EvidenceError("invalid snapshot path")
    return path


def _snapshot_ledger(repository: Path, base_sha: str, snapshot_sha: str) -> dict[str, Any]:
    if not _valid_commit(base_sha) or not _valid_commit(snapshot_sha):
        raise EvidenceError("invalid M3 commit identity")
    verify = subprocess.run(["git", "-C", str(repository), "rev-parse", "--verify", f"{snapshot_sha}^{{commit}}"],
                            capture_output=True, text=True, timeout=30, check=False)
    if verify.returncode or verify.stdout.strip() != snapshot_sha:
        raise EvidenceError("M3 snapshot commit is unavailable")
    base = subprocess.run(["git", "-C", str(repository), "merge-base", "--is-ancestor", base_sha, snapshot_sha],
                          capture_output=True, timeout=30, check=False)
    published = subprocess.run(["git", "-C", str(repository), "merge-base", "--is-ancestor", snapshot_sha,
                                "origin/main"], capture_output=True, timeout=30, check=False)
    if base.returncode and published.returncode:
        raise EvidenceError("M3 snapshot does not descend from its declared base")
    names = subprocess.run(["git", "-C", str(repository), "ls-tree", "-r", "-z", "--full-tree", snapshot_sha],
                           capture_output=True, timeout=30, check=False)
    if names.returncode:
        raise EvidenceError("M3 snapshot ledger is unavailable")
    rows = []
    total = 0
    for raw in names.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, _, name_raw = raw.partition(b"\t")
        fields = metadata.split()
        if len(fields) != 3:
            raise EvidenceError("malformed M3 tree entry")
        mode, kind, object_id = (item.decode("ascii", "strict") for item in fields)
        name = name_raw.decode("utf-8", "strict")
        rel = _safe_relative(name)
        if kind != "blob" or mode == "120000":
            raise EvidenceError(f"unsupported snapshot entry: {rel.as_posix()}")
        body = subprocess.run(["git", "-C", str(repository), "cat-file", "blob", object_id], capture_output=True,
                              timeout=30, check=False)
        if body.returncode:
            raise EvidenceError("M3 snapshot blob is unavailable")
        total += len(body.stdout)
        if len(rows) >= MAX_LEDGER_FILES or total > MAX_LEDGER_BYTES:
            raise EvidenceError("M3 snapshot ledger exceeds its bound")
        rows.append({"path": rel.as_posix(), "mode": mode, "blob": object_id,
                     "sha256": hashlib.sha256(body.stdout).hexdigest(), "size": len(body.stdout)})
    return {"base_sha": base_sha, "snapshot_sha": snapshot_sha, "files": rows,
            "file_count": len(rows), "total_bytes": total}


def _valid_commit(value: str) -> bool:
    return isinstance(value, str) and len(value) in (40, 64) and all(c in "0123456789abcdef" for c in value)


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def collect_recovery_evidence(rdir: Path | str, audit: object, attempt: object, *,
                              states: tuple[str, ...] = ("failed", "rejected")) -> dict[str, Any]:
    """Return a complete recovery-evidence/1 record; invalid sources remain explicit and non-diagnosable.

    ``states`` are the terminal M1 states the attempt may be in: a failed audit by default, ``accepted`` for the evidence of an
    accepted side of an integration conflict. ``audit`` and ``attempt`` are official M1 descriptors. They identify source files with relative paths and
    SHA-256 digests; snapshot content always comes from the pinned M3 Git commits, never the current worktree.
    """
    evidence: dict[str, Any] = {"schema_version": SCHEMA, "diagnosable": False, "identity": {},
                                "sources": {}, "snapshot_ledger": None, "validation_problems": [],
                                "not_run": []}
    try:
        root = Path(rdir).resolve(strict=True)
        if not isinstance(audit, dict) or not isinstance(attempt, dict):
            raise EvidenceError("audit and attempt descriptors must be objects")
        required = ("m1_path", "m1_sha256", "plan_path", "plan_sha256", "m6_path", "m6_sha256",
                    "remediation_path", "remediation_sha256")
        for key in required:
            if key not in audit:
                raise EvidenceError(f"missing declared source identity: {key}")
        docs: dict[str, dict[str, Any]] = {}
        digests: dict[str, str] = {}
        for name, path_key, digest_key in (("m1", "m1_path", "m1_sha256"), ("plan", "plan_path", "plan_sha256"),
                                           ("m6", "m6_path", "m6_sha256"),
                                           ("remediation", "remediation_path", "remediation_sha256")):
            relative = _safe_relative(audit[path_key])
            docs[name], digests[name] = _read_json(root / Path(*relative.parts), root,
                                                   expected_digest=audit[digest_key])
        plan_sha = digests["plan"]
        m1_doc, plan_doc, m6_doc, remediation_doc = (docs[name] for name in ("m1", "plan", "m6", "remediation"))
        if (plan_doc.get("plan_id") != audit.get("plan_id") or plan_doc.get("revision") != audit.get("revision")
                or not isinstance(plan_doc.get("tasks"), list)
                or not any(isinstance(item, dict) and item.get("id") == audit.get("task_id")
                           for item in plan_doc["tasks"])):
            raise EvidenceError("frozen plan identity or audit task mismatch")
        official_attempts = m1_doc.get("attempts")
        m1_attempt = next((item for item in official_attempts if isinstance(item, dict)
                           and item.get("id") == attempt.get("attempt_id")), None) \
            if isinstance(official_attempts, list) else None
        if (m1_doc.get("plan_id") != audit.get("plan_id") or m1_doc.get("revision") != audit.get("revision")
                or m1_doc.get("plan_sha256") != plan_sha or not isinstance(m1_attempt, dict)
                or m1_attempt.get("task_id") != audit.get("task_id")
                or m1_attempt.get("state") not in set(states)
                or ("token" in attempt and m1_attempt.get("token") != attempt.get("token"))):
            raise EvidenceError("M1 attempt identity or terminal state mismatch")
        if not isinstance(m6_doc.get("checks"), list) or not isinstance(remediation_doc.get("events"), list):
            raise EvidenceError("M6 command results or remediation history is malformed")
        identity = {"plan_id": audit.get("plan_id"), "revision": audit.get("revision"),
                    "plan_sha256": plan_sha, "audit_task_id": audit.get("task_id"),
                    "attempt_id": attempt.get("attempt_id")}
        m6_identity = m6_doc.get("identity")
        if not isinstance(m6_identity, dict) or m6_identity.get("plan_sha256") != plan_sha:
            raise EvidenceError("M6 identity or frozen plan hash mismatch")
        if (m6_identity.get("plan_id") != identity["plan_id"] or m6_identity.get("revision") != identity["revision"]
                or m6_identity.get("task_id") != identity["audit_task_id"]
                or m6_identity.get("attempt_id") != identity["attempt_id"]
                or ("token" in attempt and m6_identity.get("token") != attempt.get("token"))):
            raise EvidenceError("M6 source identity mismatch")
        manifest_path = _safe_relative(attempt.get("manifest_path"))
        if not _valid_sha256(attempt.get("manifest_sha256")):
            raise EvidenceError("M3 manifest digest identity is invalid")
        manifest, manifest_digest = _read_json(root / Path(*manifest_path.parts), root,
                                               expected_digest=attempt.get("manifest_sha256"))
        base_sha, snapshot_sha = manifest.get("base_sha"), manifest.get("snapshot_sha")
        if (manifest.get("schema") != 1 or manifest.get("status") != "captured"
                or manifest.get("attempt_id") != identity["attempt_id"]):
            raise EvidenceError("M3 manifest identity mismatch")
        if attempt.get("base_sha") != base_sha or attempt.get("snapshot_sha") != snapshot_sha:
            raise EvidenceError("M3 manifest base or snapshot differs from the official attempt")
        repo_raw = attempt.get("repository")
        if not isinstance(repo_raw, str):
            raise EvidenceError("M3 repository identity missing")
        repository = Path(repo_raw).resolve(strict=True)
        if not repository.is_dir():
            raise EvidenceError("M3 repository is unavailable")
        manifest_repository = manifest.get("repository")
        if not isinstance(manifest_repository, str) or Path(manifest_repository).resolve(strict=True) != repository:
            raise EvidenceError("M3 manifest repository identity mismatch")
        ledger = _snapshot_ledger(repository, base_sha, snapshot_sha)
        evidence["identity"] = identity
        evidence["sources"] = {name: {"sha256": digests[name], "document": doc}
                                for name, doc in docs.items()}
        evidence["sources"]["m3_manifest"] = {"sha256": manifest_digest, "document": manifest}
        evidence["snapshot_ledger"] = ledger
        evidence["diagnosable"] = True
        if audit.get("prerequisite_status") == "fail":
            evidence["not_run"] = ["audit_gate_evaluation"]
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        evidence["validation_problems"] = [str(error)[:500]]
        evidence["not_run"] = ["audit_gate_evaluation", "recovery_diagnosis"]
    return evidence


def validate_recovery_verification_map(changed_paths: tuple[str, ...], raw: object, plan: object,
                                       checks: object, verdict_identity: str,
                                       source_digests: Mapping[str, str] | None = None) -> tuple[str, ...]:
    """Require exact changed-path coverage by owner-scoped checks that M6 actually executed and passed."""
    problems = []
    if (not isinstance(raw, dict) or set(raw) != {"schema_version", "changed_paths", "checks",
                                                 "existing_owner_commands", "uncovered_paths", "uncovered_checks"}
            or raw.get("schema_version") != "recovery-verification-map/1"):
        return ("recovery verification map is missing or malformed",)
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), list) or not isinstance(checks, list):
        return ("official plan or M6 checks are unavailable",)
    tasks = {item.get("id"): item for item in plan["tasks"] if isinstance(item, dict) and isinstance(item.get("id"), str)}
    mapped = raw.get("changed_paths")
    declared = raw.get("checks")
    owner_commands = raw.get("existing_owner_commands")
    uncovered_paths = raw.get("uncovered_paths", [])
    uncovered_checks = raw.get("uncovered_checks", [])
    if (not isinstance(mapped, list) or not isinstance(declared, list) or not isinstance(owner_commands, list)
            or not isinstance(uncovered_paths, list) or not isinstance(uncovered_checks, list)):
        return ("recovery verification map has invalid collections",)
    if any(not isinstance(item, dict) for item in (*mapped, *declared)):
        return ("recovery verification map contains malformed path or check records",)
    if uncovered_paths or uncovered_checks:
        problems.append("recovery verification map contains uncovered paths or checks")
    mapped_paths = [item.get("path") for item in mapped]
    if (not all(isinstance(path, str) for path in mapped_paths) or len(mapped_paths) != len(set(mapped_paths))
            or set(mapped_paths) != set(changed_paths)):
        problems.append("recovery verification map does not match exact changed paths")
    command_rows = {(row["id"], row["command"], row["status"], row["exit_code"])
                    for row in checks if isinstance(row, dict) and isinstance(row.get("id"), str)
                    and isinstance(row.get("command"), str) and isinstance(row.get("status"), str)
                    and type(row.get("exit_code")) is int}
    check_ids = [row.get("check_id") for row in declared]
    if not all(isinstance(item, str) and item for item in check_ids) or len(check_ids) != len(set(check_ids)):
        problems.append("recovery verification map has duplicate or malformed check identifiers")
    declared_checks = {row.get("check_id"): row for row in declared if isinstance(row.get("check_id"), str)}
    known_commands = set()
    for item in declared:
        if not isinstance(item, dict):
            continue
        check_id, command, symptom, identity = (item.get(key) for key in
                                                  ("check_id", "command", "symptom", "verdict_identity"))
        if (not isinstance(check_id, str) or not check_id or not isinstance(command, str) or not command.strip()
                or not isinstance(symptom, str) or not symptom or not isinstance(identity, str)
                or not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}:[a-f0-9]{64}", identity)):
            problems.append("recovery verification map contains a malformed check")
        if isinstance(command, str):
            known_commands.add(command)
    if any(not isinstance(command, str) or not command.strip() for command in owner_commands):
        problems.append("recovery verification map contains an invalid owner command")
    if any(command not in owner_commands for command in known_commands) and not uncovered_checks:
        problems.append("verification map check is absent from existing owner commands")
    for path_row in mapped:
        if not isinstance(path_row, dict):
            continue
        path, owner_id = path_row.get("path"), path_row.get("owner_task_id")
        source_digest = path_row.get("source_digest")
        if (not isinstance(path, str) or path.startswith("/") or "\\" in path
                or any(part in ("", ".", "..") for part in path.split("/"))
                or not _valid_sha256(source_digest)
                or (source_digests is not None and source_digests.get(path) != source_digest)):
            problems.append(f"changed path source identity is invalid: {path}")
            continue
        owner = tasks.get(owner_id)
        scopes = owner.get("expected_paths", []) if isinstance(owner, dict) else []
        if not isinstance(path, str) or not isinstance(owner_id, str) or not isinstance(scopes, list) or not any(
                isinstance(scope, str) and (path == scope or path.startswith(scope.rstrip("/") + "/")) for scope in scopes):
            problems.append(f"changed path has no inherited owner scope: {path}")
            continue
        owner_checks = [row for row in declared_checks.values() if row.get("owner_task_id") == owner_id]
        owner_commands = {item.get("value") for item in owner.get("verification", []) if isinstance(item, dict)}
        covered = any(row.get("command") in owner_commands and row.get("command") in raw.get("existing_owner_commands", [])
                      and row.get("verdict_identity") == verdict_identity
                      and (row.get("check_id"), row.get("command"), "pass", 0) in command_rows
                      for row in owner_checks)
        if not covered:
            problems.append(f"changed path lacks an executed independent owner check: {path}")
    return tuple(problems)


def validate_snapshot_coverage(source: object, resolver: object, changed_paths: tuple[str, ...], plan: object,
                               checks: object, verdict_identity: str) -> tuple[str, ...]:
    """Derive a versioned map from pinned paths, frozen owner scopes and checks M6 actually ran."""
    try:
        with resolver.materialize(source) as snapshot:
            source_digests = {}
            for changed in changed_paths:
                rel = _safe_relative(changed)
                target = snapshot.directory.joinpath(*rel.parts)
                if target.is_symlink() or not target.is_file():
                    return (f"changed recovery path is unavailable: {changed}",)
                source_digests[changed] = hashlib.sha256(target.read_bytes()).hexdigest()
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return ("recovery snapshot paths are unavailable or malformed",)
    raw = _build_recovery_verification_map(changed_paths, plan, checks, verdict_identity, source_digests)
    return validate_recovery_verification_map(changed_paths, raw, plan, checks, verdict_identity, source_digests)


def _build_recovery_verification_map(changed_paths: tuple[str, ...], plan: object, checks: object,
                                     verdict_identity: str, source_digests: Mapping[str, str]) -> dict[str, Any]:
    planned = plan.get("tasks", []) if isinstance(plan, Mapping) else []
    task_rows = [row for row in planned if isinstance(row, dict)] if isinstance(planned, list) else []
    check_rows = [row for row in checks if isinstance(row, dict)] if isinstance(checks, list) else []
    changed_records, checks_mapped, owner_commands, uncovered_paths, uncovered_checks = [], [], set(), [], []
    for changed in changed_paths:
        candidates = []
        for task in task_rows:
            scopes = task.get("expected_paths", [])
            if isinstance(scopes, list) and any(isinstance(scope, str)
                    and (changed == scope or changed.startswith(scope.rstrip("/") + "/")) for scope in scopes):
                candidates.append(task)
        owner = candidates[0] if len(candidates) == 1 else None
        owner_id = owner.get("id") if isinstance(owner, dict) else "unknown"
        changed_records.append({"path": changed, "source_digest": source_digests.get(changed, "0" * 64),
                                "owner_task_id": owner_id})
        if owner is None:
            uncovered_paths.append(changed)
            continue
        verification = owner.get("verification", [])
        declared = {item.get("value") for item in verification if isinstance(item, dict)
                    and isinstance(item.get("value"), str)} if isinstance(verification, list) else set()
        owner_commands.update(declared)
        covered = False
        for check in check_rows:
            command = check.get("command")
            check_id = check.get("id")
            if (not isinstance(command, str) or command not in declared or not isinstance(check_id, str)
                    or check.get("status") != "pass" or type(check.get("exit_code")) is not int
                    or check["exit_code"] != 0 or not _command_covers_path(changed, command)):
                continue
            if not any(item["check_id"] == check_id and item["owner_task_id"] == owner_id for item in checks_mapped):
                checks_mapped.append({"check_id": check_id, "owner_task_id": owner_id, "command": command,
                                      "symptom": _path_symptom(changed), "verdict_identity": verdict_identity})
            covered = True
        if not covered:
            uncovered_paths.append(changed)
    return {"schema_version": "recovery-verification-map/1", "changed_paths": changed_records,
            "checks": checks_mapped, "existing_owner_commands": sorted(owner_commands),
            "uncovered_paths": sorted(set(uncovered_paths)), "uncovered_checks": sorted(set(uncovered_checks))}


def _path_symptom(path: str) -> str:
    top = path.split("/", 1)[0].lower()
    token = re.sub(r"[^a-z0-9_-]", "_", top).strip("_") or "root"
    return "surface_" + token[:110]


_INERT = frozenset({"echo", "printf", "true", "false", ":", "cat", "ls", "test", "sleep", "pwd", "type", "exit"})


def _command_covers_path(path: str, command: str) -> bool:
    """Require a command that RUNS something over the surface: an inert command (`echo web/`) never covers a path, and a surface
    name counts only as a path argument (`web/`, `./web/x`), not as a substring of another word."""
    words = re.split(r"\s+", command.strip())
    first = next((w for w in words if "=" not in w.split("/")[0] or w.startswith(("./", "/"))), "")
    segments = [seg.strip().split(" ")[0] for seg in re.split(r"&&|\|\||;", command) if seg.strip()]
    if all(Path(seg).name.lower() in _INERT for seg in segments if seg):
        return False
    if Path(first).name.lower() in _INERT and len(segments) == 1:
        return False
    top = path.split("/", 1)[0].lower()
    lowered = command.lower()
    web_path = top in {"web", "frontend", "client", "app", "apps"} or path.endswith((".tsx", ".jsx", ".css"))
    # a web file under a generic root (`src/ui/Foo.tsx`) is covered by a command over ITS package (`src/ui/`), not over `src/`
    parts = path.lower().split("/")
    scope = top if top in {"web", "frontend", "client", "app", "apps"} or len(parts) < 3 or not web_path else "/".join(parts[:2])
    as_arg = re.search(rf"(?:^|[\s='\":]|\./){re.escape(scope)}/", lowered) is not None
    if web_path:
        return as_arg or any(token in lowered for token in
                             ("npm run typecheck", "tsc --noemit", "npm run lint", "npm run build"))
    return as_arg or Path(path).name.lower() in lowered or Path(path).stem.lower() in lowered


def recovery_coverage_problems(core: object, order: object, result: object, resolver: object,
                               snapshot_source: object, changed_paths: object) -> tuple[str, ...] | None:
    """Return None for a first attempt, otherwise the coverage failures from its pinned snapshot."""
    previous = core.read(lambda ctx: tuple(ctx.state.attempts[attempt_id] for attempt_id in
                                           ctx.state.tasks[order.task_id].attempts[:-1]))
    audit_recovery = any("audit-gate" in str(getattr(item, "failure", ""))
                         or "verification_replan" in str(getattr(item, "failure", "")) for item in previous)
    if not audit_recovery:
        return None
    source = snapshot_source(order)
    if source is None:
        return ("recovery evidence has no validated M3 snapshot",)
    changed = changed_paths(order)
    plan = {"tasks": [{"id": spec.id, "expected_paths": list(spec.expected_paths),
                       "verification": [dict(item) for item in spec.verification]}
                      for spec in core.plan.tasks]}
    manifest = result.get("evidence_manifest") if isinstance(result, Mapping) else None
    identity = "m6:" + manifest.rsplit("/", 1)[-1] if isinstance(manifest, str) and manifest.startswith(
        "m6://result/") else None
    return validate_snapshot_coverage(source, resolver, changed, plan,
                                      result.get("checks") if isinstance(result, Mapping) else None, identity)


def build_audit_observation(order: object, source: object, raw_ledger: bytes | str, findings: object,
                            *, gate_status: str) -> dict[str, Any]:
    """Build the complete structured observation before any display summary is shortened."""
    body = raw_ledger if isinstance(raw_ledger, bytes) else raw_ledger.encode("utf-8")
    return {"schema_version": "audit-observation/1", "plan_id": order.plan_id,
            "revision": order.revision, "audit_task_id": order.task_id, "attempt_id": order.attempt_id,
            "snapshot_sha": getattr(source, "snapshot_sha", None),
            "ledger_sha256": hashlib.sha256(body).hexdigest(), "findings": findings,
            "gate_status": gate_status,
            "not_run_checks": [] if gate_status == "evaluated" else ["audit_gate_evaluation"]}


def audit_observation_from_ledger(order: object, source: object, raw_ledger: bytes | str,
                                 *, gate_status: str) -> dict[str, Any]:
    text = raw_ledger.decode("utf-8") if isinstance(raw_ledger, bytes) else raw_ledger
    ledger = json.loads(text)
    if not isinstance(ledger, dict) or not isinstance(ledger.get("findings"), list):
        raise EvidenceError("validated audit ledger has no findings list")
    return build_audit_observation(order, source, raw_ledger, ledger["findings"], gate_status=gate_status)
