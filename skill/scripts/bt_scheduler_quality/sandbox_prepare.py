"""The step a fresh checkout needs before its checks: build the workspace packages whose output git ignores.

A snapshot holds tracked and untracked files, never ignored build output, so `packages/*/dist` is missing and anything
importing a workspace package fails. The step runs inside the sandbox right before each check, in the same
isolation, from the repository's own `build` scripts.
"""

from __future__ import annotations

import json
from pathlib import Path

from .policy import QualityPolicy

BUILD_WORKSPACES = ("npm", "run", "build", "--workspaces", "--if-present")
NEXT_TYPEGEN = ("npx", "--no-install", "next", "typegen")  # route types (LayoutProps, PageProps) live in ignored output


def prepare_steps(policy: QualityPolicy, root: Path, mounts=()) -> tuple[tuple[str, ...], ...]:
    """Steps this snapshot needs before a check. Without installed dependencies there is nothing to run them with."""
    if not policy.toolchain or not any(m.target.endswith("/node_modules") for m in mounts):
        return ()
    try:
        manifest = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ()
    if not isinstance(manifest, dict):
        return ()
    steps = []
    if _has_buildable_workspace(root, manifest):
        steps.append(BUILD_WORKSPACES)
    dependencies = {**_mapping(manifest.get("dependencies")), **_mapping(manifest.get("devDependencies"))}
    if "next" in dependencies:
        steps.append(NEXT_TYPEGEN)
    return tuple(steps)


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _has_buildable_workspace(root: Path, manifest: dict) -> bool:
    patterns = manifest.get("workspaces")
    if isinstance(patterns, dict):
        patterns = patterns.get("packages")
    if not isinstance(patterns, list):
        return False
    for pattern in patterns:
        if not isinstance(pattern, str) or pattern.startswith("/") or ".." in Path(pattern).parts:
            continue
        for package in root.glob(pattern):
            try:       # a directory the glob matches without a readable package.json is not a workspace: npm skips it
                scripts = json.loads((package / "package.json").read_text(encoding="utf-8")).get("scripts")
            except (OSError, ValueError, AttributeError):
                continue
            if isinstance(scripts, dict) and "build" in scripts:
                return True
    return False
