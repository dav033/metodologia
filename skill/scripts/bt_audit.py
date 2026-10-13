"""Read-only inventory for an architecture audit.

This module only reads workspace metadata and Git administrative markers. It never
opens product source files, invokes Git, or updates the local workspace index.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import bt_workspace as ws


MAX_CANDIDATE_DEPTH = 8


def _read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _is_git_repo(path: Path) -> bool:
    marker = path / ".git"
    return marker.is_dir() or marker.is_file()


def _remote_of(path: Path) -> str:
    """Read only the origin URL from the repository's Git config."""
    config = path / ".git" / "config"
    if (path / ".git").is_file():
        # Worktree .git files point at a common directory. Do not follow that
        # pointer or read outside the configured workspace root.
        return ""
    return _safe_remote(ws.remote_of(path))


def _safe_remote(remote: str) -> str:
    """Remove embedded credentials before exposing a configured Git remote."""
    value = remote.strip()
    if "@" in value and ":" in value and not value.startswith(("http://", "https://", "ssh://")):
        # SCP-style remotes have no standard URL parser; remove any user prefix.
        value = re.sub(r"^[^@]+@", "", value)
        return value
    try:
        parsed = urlsplit(value)
        if parsed.scheme and parsed.hostname:
            host = parsed.hostname
            if parsed.port:
                host = f"{host}:{parsed.port}"
            return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    except ValueError:
        pass
    return value


def _resolve_registered(root: Path, project: str, role: str, spec: object, local: dict) -> dict:
    if isinstance(spec, str):
        configured_remote = ""
        hinted = Path(spec).expanduser()
    elif isinstance(spec, dict):
        configured_remote = str(spec.get("remote", "") or "")
        hint = str(spec.get("hint", "") or "")
        hinted = ws.from_hint(hint) if hint else None
    else:
        configured_remote = ""
        hinted = None

    stored = local.get(f"{project}/{role}")
    stored_path = Path(stored).expanduser() if isinstance(stored, str) and stored else None
    selected = stored_path if stored_path is not None and stored_path.exists() else hinted
    selected_exists = selected is not None and selected.exists()
    if selected is None:
        selected = Path("<unresolved>")
    selected_is_repo = selected_exists and selected.is_dir() and _is_git_repo(selected)
    actual_remote = _remote_of(selected) if selected_is_repo else ""
    expected_normalized = ws.norm_remote(configured_remote)
    actual_normalized = ws.norm_remote(actual_remote)

    if stored_path is not None and not stored_path.exists() and hinted.exists():
        status = "stale"
        reason = "stored local path is missing; configured hint exists"
    elif not selected_exists:
        status = "missing"
        reason = "registered local path and configured hint are missing"
    elif not selected_is_repo:
        status = "stale"
        reason = "registered path exists but is not a Git repository"
    elif expected_normalized and actual_normalized and actual_normalized != expected_normalized:
        status = "remote_mismatch"
        reason = "repository origin differs from the registered remote"
    elif expected_normalized and not actual_normalized:
        status = "present"
        reason = "registered repository is accessible; origin could not be verified"
    else:
        status = "present"
        reason = "registered repository is accessible"

    return {
        "role": role,
        "registered_remote": _safe_remote(configured_remote),
        "registered_hint": str(spec.get("hint", "") or "") if isinstance(spec, dict) else "",
        "stored_local_path": stored_path.as_posix() if stored_path is not None else None,
        "path": selected.resolve().as_posix() if selected_exists else selected.as_posix(),
        "actual_remote": actual_remote,
        "status": status,
        "reason": reason,
    }


def _candidates(workspace_root: Path) -> tuple[list[dict], bool]:
    """Find unregistered repositories under the configured root, without following symlinks."""
    if not workspace_root.is_dir():
        return [], False

    candidates: list[dict] = []
    stack: list[tuple[Path, int]] = [(workspace_root, 0)]
    truncated = False
    while stack:
        directory, depth = stack.pop()
        if _is_git_repo(directory):
            candidates.append({"path": directory.resolve().as_posix(), "remote": _remote_of(directory)})
            continue
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name.casefold(), reverse=True)
        except OSError:
            continue
        for entry in entries:
            if entry.name.lower() in ws.SCAN_SKIP or entry.name.startswith("."):
                continue
            try:
                if not entry.is_dir(follow_symlinks=False):
                    continue
            except OSError:
                continue
            candidate = Path(entry.path)
            if _is_git_repo(candidate):
                candidates.append({"path": candidate.resolve().as_posix(), "remote": _remote_of(candidate)})
                continue
            if depth >= MAX_CANDIDATE_DEPTH:
                truncated = True
                continue
            stack.append((candidate, depth + 1))
    candidates.sort(key=lambda item: item["path"].casefold())
    return candidates, truncated


def inventory(bitacora_root: Path, project: str) -> dict:
    """Return a deterministic workspace registry and bounded candidate inventory."""
    bitacora_root = Path(bitacora_root).expanduser()
    project_dir = bitacora_root / project
    metadata = _read_json(project_dir / "project.json")
    repo_specs = metadata.get("repos", {})
    if not isinstance(repo_specs, dict) and isinstance(metadata.get("repo"), str):
        legacy = Path(metadata["repo"])
        repo_specs = {legacy.name: str(legacy)}
    if not isinstance(repo_specs, dict):
        repo_specs = {}

    local = _read_json(bitacora_root / ".state" / "paths.json")
    registered = [
        _resolve_registered(bitacora_root, project, role, repo_specs[role], local)
        for role in sorted(repo_specs, key=str.casefold)
    ]

    configured_root = str(metadata.get("root", "") or "")
    workspace_root = ws.from_hint(configured_root).expanduser() if configured_root else None
    candidates, truncated = _candidates(workspace_root) if workspace_root else ([], False)
    registered_keys = {ws._key(item["path"]) for item in registered if item["status"] in {"present", "remote_mismatch"}}
    candidates = [item for item in candidates if ws._key(item["path"]) not in registered_keys]

    return {
        "project": project,
        "project_dir": project_dir.resolve().as_posix(),
        "workspace_root": workspace_root.resolve().as_posix() if workspace_root else None,
        "workspace_root_configured": workspace_root is not None,
        "registered_repositories": registered,
        "candidate_repositories": candidates,
        "candidate_scan_truncated": truncated,
        "read_only": True,
        "source_content_read": False,
    }


def project_for_cwd(bitacora_root: Path, cwd: Path) -> str | None:
    """Resolve a project from recorded paths without triggering index rebuilding."""
    bitacora_root = Path(bitacora_root).expanduser()
    cwd = Path(cwd).resolve()
    try:
        relative = cwd.relative_to(bitacora_root.resolve())
    except ValueError:
        relative = None
    if relative is not None and relative.parts and not relative.parts[0].startswith("."):
        return relative.parts[0]

    best_project = None
    best_length = -1
    paths = _read_json(bitacora_root / ".state" / "paths.json")
    for key, value in paths.items():
        if not isinstance(value, str) or "/" not in key:
            continue
        registered = Path(value).expanduser()
        try:
            cwd.relative_to(registered.resolve())
        except (OSError, ValueError):
            continue
        if len(str(registered)) > best_length:
            best_project = key.split("/", 1)[0]
            best_length = len(str(registered))

    if best_project:
        return best_project
    # A configured workspace root is another read-only way to associate a cwd.
    for project_dir in sorted(bitacora_root.iterdir(), key=lambda path: path.name.casefold()) if bitacora_root.is_dir() else []:
        if not project_dir.is_dir() or project_dir.name.startswith("."):
            continue
        data = _read_json(project_dir / "project.json")
        hint = str(data.get("root", "") or "")
        if not hint:
            continue
        root = ws.from_hint(hint)
        try:
            cwd.relative_to(root.resolve())
        except (OSError, ValueError):
            continue
        return project_dir.name
    return None
