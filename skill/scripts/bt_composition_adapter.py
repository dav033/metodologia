"""Methodology boundary: real object-only Git operations for `bt_composition`."""
from __future__ import annotations

import hashlib
import subprocess
import tempfile
from pathlib import Path
from collections.abc import Sequence

from bt_composition import CompositionEngine, GitResult, Store


class GitCommandError(RuntimeError):
    """Git failed without changing the caller's branch or checkout."""


class GitSubprocessPort:
    def __init__(self, repository: str | Path, workspace_root: str | Path):
        self.repository = Path(repository).resolve()
        self.workspace_root = Path(workspace_root).resolve()
        if self.workspace_root == self.repository or self.repository in self.workspace_root.parents:
            raise ValueError("WORKSPACE_ROOT_INSIDE_REPOSITORY")
        result = self._run("rev-parse", "--show-object-format")
        self.zero = "0" * (64 if result.stdout.strip() == "sha256" else 40)

    def _run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(["git", "-C", str(self.repository), *arguments],
                                capture_output=True, text=True, check=False)
        if check and result.returncode:
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_command_failed")
        return result

    def rev_parse(self, revision: str) -> str | None:
        result = self._run("rev-parse", "--verify", f"{revision}^{{commit}}", check=False)
        return result.stdout.strip() if result.returncode == 0 else None

    def merge_tree(self, base: str, ours: str, theirs: str) -> GitResult:
        result = self._run("merge-tree", "--write-tree", "--name-only", "--no-messages",
                           f"--merge-base={base}", ours, theirs, check=False)
        if result.returncode not in (0, 1):
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_merge_tree_failed")
        lines = result.stdout.splitlines()
        if not lines or len(lines[0].strip()) not in (40, 64):
            raise GitCommandError("git_merge_tree_output_invalid")
        conflicts = tuple(sorted({line.strip() for line in lines[1:] if line.strip()})) if result.returncode else ()
        return GitResult(lines[0].strip(), conflicts)

    def commit_tree(self, tree: str, parents: Sequence[str], message: str) -> str:
        args = ["commit-tree", tree]
        for parent in parents:
            args.extend(("-p", parent))
        args.extend(("-m", message))
        return self._run(*args).stdout.strip()

    def update_refs(self, updates: Sequence[tuple[str, str | None, str | None]]) -> None:
        commands = ["start"]
        for ref, new, expected in updates:
            if not (ref.startswith("refs/subplans/") or ref.startswith("refs/compositions/")):
                raise ValueError("COMPOSITION_REF_OUTSIDE_NAMESPACE")
            old = self.zero if expected is None else expected
            if new is None:
                commands.append(f"delete {ref} {old}")
            else:
                commands.append(f"update {ref} {new} {old}")
        commands.extend(("prepare", "commit", ""))
        result = subprocess.run(["git", "-C", str(self.repository), "update-ref", "--stdin"],
                                input="\n".join(commands), capture_output=True, text=True, check=False)
        if result.returncode:
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_ref_transaction_failed")

    def tree_digest(self, commit: str, paths: Sequence[str]) -> str:
        entries: list[str] = []
        for path in sorted(set(paths)):
            if path.startswith("/") or ".." in Path(path).parts:
                raise ValueError("INVALID_RELEVANT_PATH")
            result = self._run("ls-tree", "-r", commit, "--", path)
            entries.extend(line for line in result.stdout.splitlines() if line)
        return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()

    def diff_paths(self, a: str, b: str) -> tuple[str, ...]:
        output = self._run("diff", "--name-only", "--no-renames", a, b, "--").stdout
        return tuple(sorted({line for line in output.splitlines() if line}))

    def add_worktree(self, commit: str, parent: str | Path) -> str:
        root = Path(parent).resolve()
        if root != self.workspace_root and self.workspace_root not in root.parents:
            raise ValueError("WORKTREE_PATH_OUTSIDE_ROOT")
        root.mkdir(parents=True, exist_ok=True)
        path = Path(tempfile.mkdtemp(prefix="composition-", dir=root))
        path.rmdir()
        self._run("worktree", "add", "--detach", str(path), commit)
        return str(path)

    def remove_worktree(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        if self.workspace_root not in resolved.parents:
            raise ValueError("WORKTREE_PATH_OUTSIDE_ROOT")
        self._run("worktree", "remove", "--force", str(resolved))


def create_engine(repository: str | Path, store_path: str | Path,
                  workspace_root: str | Path) -> tuple[CompositionEngine, Store]:
    repo = Path(repository).resolve()
    state_path = Path(store_path).resolve()
    if state_path == repo or repo in state_path.parents:
        raise ValueError("STORE_PATH_INSIDE_REPOSITORY")
    git = GitSubprocessPort(repository, workspace_root)
    store = Store(store_path)
    return CompositionEngine(git, store, workspace_root), store


__all__ = ["GitCommandError", "GitSubprocessPort", "create_engine"]
