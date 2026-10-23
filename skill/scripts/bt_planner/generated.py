"""Declarations of tracked build outputs; commands are metadata, never executed by the planner."""
from __future__ import annotations

import fnmatch
import re

MAX_PATHS = 256
MAX_PATH_LENGTH = 1024
MAX_COMMAND_LENGTH = 4096


def matches(path: str, patterns: list[str] | tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _patterns(plan: dict) -> list[str]:
    paths = plan.get("generated_paths")
    return [p for p in paths if isinstance(p, str)] if isinstance(paths, list) else []


def declared_pair(first: str, second: str, plan: dict) -> bool:
    patterns = _patterns(plan)
    return matches(first, patterns) and matches(second, patterns)


def errors(plan: dict) -> list[str]:
    out = []
    if "generated_paths" in plan:
        paths = plan["generated_paths"]
        if not isinstance(paths, list) or len(paths) > MAX_PATHS or any(
            not isinstance(p, str) or not 1 <= len(p) <= MAX_PATH_LENGTH or p != p.strip()
            or p.startswith("/") or "\\" in p or ":" in p or any(ord(c) < 32 for c in p)
            or any(part in ("", ".", "..") for part in p.split("/")) for p in paths
        ):
            out.append("plan.generated_paths: at most 256 relative paths/globs of 1..1024 characters; "
                       "no absolute paths, empty components, '.', '..', backslashes, colons or control characters")
    if "generated_command" in plan:
        command = plan["generated_command"]
        commands = list(command.values()) if isinstance(command, dict) else [command]
        valid_roles = not isinstance(command, dict) or (0 < len(command) <= 256 and all(
            isinstance(role, str) and re.fullmatch(r"[A-Za-z0-9._-]{1,128}", role) for role in command))
        if not valid_roles or not all(isinstance(c, str) and c.strip() and len(c) <= MAX_COMMAND_LENGTH
                                     and "\0" not in c for c in commands):
            out.append("plan.generated_command: non-empty command of at most 4096 characters, "
                       "or a non-empty map of at most 256 repository roles to commands")
    return out


def looks_generated(path: str) -> bool:
    parts = path.split("/")
    name = parts[-1]
    return (name == "registry.json" or name.endswith((".lock", ".snap")) or name.startswith("resolved.")
            or "generated" in parts or "dist" in parts)


def advice(plan: dict, ancestors: dict[str, set[str]]) -> list[str]:
    tasks = {t["id"]: t for t in plan.get("tasks", []) if isinstance(t, dict) and isinstance(t.get("id"), str)}
    order = list(ancestors)
    if len(order) > 1500:  # the same pairwise lint bound as path coupling checks
        return []
    patterns = _patterns(plan)
    out = []
    for i, a in enumerate(order):
        for b in order[i + 1:]:
            if a in ancestors[b] or b in ancestors[a] or tasks[a].get("repository") != tasks[b].get("repository"):
                continue
            paths = []
            for row in (tasks[a], tasks[b]):
                entries = row.get("expected_paths")
                paths.append({p for p in entries if isinstance(p, str)} if isinstance(entries, list) else set())
            for path in sorted(paths[0] & paths[1]):
                if looks_generated(path) and not matches(path, patterns):
                    out.append(f"{a} and {b}: unordered writers of likely generated path {path!r}; "
                               "declare it in generated_paths if it is a tracked build output")
    return out
