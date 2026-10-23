"""Content provenance for audit evidence; git reads never change the repository or its index."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bt_audit_gate import Gate

REPORT = re.compile(r"\.(?:md|json|txt|log|csv|html)$")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def evidence_outputs(tasks: Iterable[dict], repository: str, evidence_files: Iterable[str] = ()) -> tuple[str, ...]:
    """Same bounded report exclusions as quality reuse. All producers/auditors share one scope, frozen in the plan."""
    tasks = list(tasks)
    declared_evidence = set(evidence_files)
    for task in tasks:
        if task.get("repository") == repository and task.get("kind") == "audit":
            declared_evidence.update(evidence_paths({}, task))
    reports = {path for task in tasks if task.get("repository") == repository
                         and task.get("kind") in ("test", "audit") for path in task.get("expected_paths", ())
                         if isinstance(path, str) and REPORT.search(path) and not any(c in path for c in "*?[")
                         and safe_path(path)}
    reports.update(path for task in tasks if task.get("repository") == repository for path in task.get("expected_paths", ())
                   if path in declared_evidence and safe_path(path) and REPORT.search(path) and not any(c in path for c in "*?["))
    return tuple(sorted(reports))


def safe_path(path: object) -> bool:
    return (isinstance(path, str) and bool(path) and not PurePosixPath(path).is_absolute()
            and ".." not in PurePosixPath(path).parts and "\x00" not in path)


def tree_digest(repository: Path, revision: str, outputs: Iterable[str] = ()) -> str:
    """Hash sorted tracked entries (path, mode, blob/submodule oid), excluding only exact report paths."""
    try:
        done = subprocess.run(["git", "-C", str(repository), "ls-tree", "-rz", "--full-tree", "--end-of-options", revision],
                              capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError) as error:
        raise RuntimeError("audit source tree is unavailable") from error
    if done.returncode:
        raise RuntimeError("audit source tree is unavailable")
    ignored = {path.encode("utf-8") for path in outputs}
    entries = sorted(entry for entry in done.stdout.split(b"\0") if entry and entry.split(b"\t", 1)[1] not in ignored)
    return "sha256:" + hashlib.sha256(b"\0".join(entries)).hexdigest()


def evidence_paths(data: dict, task: dict) -> list[str]:
    """Explicit provenance wins; old frozen audits often name evidence only in their checker arguments."""
    if "integration_evidence" in data:
        paths = data["integration_evidence"]
        if not isinstance(paths, list) or len(paths) > 200 or not all(safe_path(p) for p in paths):
            raise ValueError("integration_evidence must be a list of relative evidence paths")
        return list(dict.fromkeys(paths))
    import shlex

    paths = []
    for check in task.get("verification", ()):
        try:
            words = shlex.split(str(check.get("value", "")))
        except ValueError:
            continue
        for index, word in enumerate(words):
            path = word.split("=", 1)[1] if word.startswith("--integration-results=") else (
                words[index + 1] if word == "--integration-results" and index + 1 < len(words) else None)
            if path is not None:
                if not safe_path(path):
                    raise ValueError("integration evidence must be a relative path")
                if path not in paths:
                    paths.append(path)
    return paths


def evidence_gate(data: dict, tasks: Iterable[dict], audit_id: str, current_digest: str,
                  read: Callable[[str], bytes | str | None], *,
                  digest_at: Callable[[str], str] | None = None) -> Gate:
    """Return a gate naming producers to rerun. Legacy revisions resolve to content, never compare as strings."""
    from bt_audit_gate import Gate, MAX_BYTES

    tasks = list(tasks)
    audit = next(t for t in tasks if t["id"] == audit_id)
    problems, blocking, rework = [], [], []
    if "tree_digest" in data and (not isinstance(data["tree_digest"], str)
                                  or not DIGEST.fullmatch(data["tree_digest"]) or data["tree_digest"] != current_digest):
        problems.append("the audit tree_digest does not match the audited source tree; regenerate the ledger")
    try:
        paths = evidence_paths(data, audit)
    except ValueError as error:
        return Gate(False, (str(error),), (), ())
    for index, path in enumerate(paths):
        owners = [t["id"] for t in tasks if t["id"] != audit_id and t.get("repository") == audit.get("repository")
                  and path in t.get("expected_paths", ())]
        if not owners:
            problems.append(f"integration evidence {path} has no producer in this repository's expected_paths")
            continue
        raw = read(path)
        try:
            evidence = json.loads(raw) if raw is not None and len(raw) <= MAX_BYTES else None
        except (ValueError, UnicodeError, RecursionError):
            evidence = None
        recorded = evidence.get("tree_digest") if isinstance(evidence, dict) else None
        legacy_revision = evidence.get("revision") if isinstance(evidence, dict) else None
        if (recorded is None and isinstance(legacy_revision, str)
                and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", legacy_revision) and digest_at):
            try:
                recorded = digest_at(legacy_revision)
            except RuntimeError:
                recorded = None
        if recorded == current_digest:
            continue
        summary = f"STALE evidence {path}: sources changed or provenance is unavailable; regenerate with {', '.join(owners)}"
        blocking.append({"id": f"STALE-EVIDENCE-{index + 1}", "severity": "high", "code": "STALE_EVIDENCE",
                         "summary": summary, "tasks": owners, "evidence": f"expected tree_digest {current_digest}; recorded {recorded}"})
        rework.extend(owner for owner in owners if owner not in rework)
    return Gate(not problems and not blocking, tuple(problems), tuple(blocking), tuple(rework))
