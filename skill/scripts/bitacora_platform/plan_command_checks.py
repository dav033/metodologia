"""Repository facts for the planner's verification-command checks."""
from __future__ import annotations

import subprocess
from pathlib import Path
from collections.abc import Callable


def ignore_resolver(roots: dict[str, Path] | None = None) -> Callable[[str, str], bool | None]:
    cache: dict[tuple[str, str], bool | None] = {}

    def ignored(repository: str, path: str) -> bool | None:
        key = (repository, path)
        if key in cache:
            return cache[key]
        root = (roots or {}).get(repository)
        if root is None and Path(repository).is_absolute():
            root = Path(repository)
        result = None
        if root is not None and root.is_dir():
            candidate = Path(path)
            if candidate.is_absolute():
                try:
                    path = str(candidate.relative_to(root.resolve()))
                except ValueError:
                    return None
            try:
                process = subprocess.run(["git", "-C", str(root), "check-ignore", "--quiet", "--", path],
                                         capture_output=True, timeout=5, check=False)
                if process.returncode in (0, 1):
                    result = process.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                pass  # unavailable repository facts never invalidate a plan
        cache[key] = result
        return result

    return ignored
