"""The step a fresh checkout needs before its checks: build the workspace packages whose output git ignores.

A snapshot holds tracked and untracked files, never ignored build output, so `packages/*/dist` is missing and anything
importing a workspace package fails. The step runs inside the sandbox right before each check, in the same
isolation, from the repository's own `build` scripts.

Every check gets its own fresh copy of the captured files (a new tmpfs per check, the snapshot bound read-only), so
what one check or its preparation writes never reaches another check. What a check does see that the attempt's own
worktree may lack is the preparation's ignored output: `next typegen` writes `next-env.d.ts` and `.next/types/**`,
which a tsconfig including them type-checks against (Next's global `NodeJS.ProcessEnv` requires `NODE_ENV`). A
failing prepared check's stdout therefore ends with `prepare_note`, so the builder can reproduce it (D-273).
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


def prepare_note(steps: tuple[tuple[str, ...], ...]) -> str:
    """The line a failing prepared check ends with: which steps ran first and the ignored files they left (D-273)."""
    if not steps:
        return ""
    commands = " and ".join(f"`{' '.join(step)}`" for step in steps)
    outputs = ", ".join(dict.fromkeys(filter(None, map(_output_of, steps))))
    left = f" They write git-ignored files the check then sees ({outputs})." if outputs else ""
    return (f"[M6] This check ran in a fresh copy of your captured files (nothing from other checks) after the "
            f"verifier ran {commands} in it.{left} Run them in your worktree first to reproduce.\n")


def _output_of(step: tuple[str, ...]) -> str | None:
    if step == BUILD_WORKSPACES:
        return "the workspace packages' build output"
    if step == NEXT_TYPEGEN:
        return "next-env.d.ts and .next/types/**"
    return None


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
