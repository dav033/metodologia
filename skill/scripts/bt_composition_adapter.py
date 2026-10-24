"""Methodology boundary: real object-only Git operations for `bt_composition`."""
from __future__ import annotations

import hashlib
import os
import re
import json
import subprocess
import tempfile
from pathlib import Path
from collections.abc import Sequence

from bt_composition import (Action, CompositionEngine, EvidenceKey, GitResult, PropagationChange, Store,
                            VerdictProof, propagate as _propagate)


class GitCommandError(RuntimeError):
    """Git failed without changing the caller's branch or checkout."""


class GitSubprocessPort:
    LOCATION_VARS = frozenset({"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_OBJECT_DIRECTORY",
                               "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE", "GIT_PREFIX"})
    IDENTITY = {"GIT_AUTHOR_NAME": "composition-engine", "GIT_AUTHOR_EMAIL": "composition@localhost",
                "GIT_COMMITTER_NAME": "composition-engine", "GIT_COMMITTER_EMAIL": "composition@localhost",
                "GIT_AUTHOR_DATE": "1970-01-01T00:00:00+0000", "GIT_COMMITTER_DATE": "1970-01-01T00:00:00+0000"}

    def __init__(self, repository: str | Path, workspace_root: str | Path):
        self.repository = Path(repository).resolve()
        self.workspace_root = Path(workspace_root).resolve()
        if (self.workspace_root == self.repository or self.repository in self.workspace_root.parents
                or self.workspace_root in self.repository.parents):
            raise ValueError("WORKSPACE_ROOT_OVERLAPS_REPOSITORY")
        result = self._run("rev-parse", "--show-object-format")
        self.zero = "0" * (64 if result.stdout.strip() == "sha256" else 40)

    def _run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(self._command(*arguments), env=self._environment(),
                                capture_output=True, text=True, check=False)
        if check and result.returncode:
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_command_failed")
        return result

    def _command(self, *arguments: str) -> list[str]:
        return ["git", "-c", "core.hooksPath=/dev/null", "-c", "gc.auto=0", "-c", "commit.gpgSign=false",
                "-C", str(self.repository), *arguments]

    @classmethod
    def _environment(cls) -> dict[str, str]:
        environment = {key: value for key, value in os.environ.items() if key not in cls.LOCATION_VARS}
        environment.update(cls.IDENTITY)
        environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
                            "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"})
        return environment

    def rev_parse(self, revision: str) -> str | None:
        if not isinstance(revision, str) or not revision or any(char.isspace() for char in revision):
            return None
        result = self._run("rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}", check=False)
        if result.returncode:
            return None
        oid = result.stdout.strip()
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
            raise GitCommandError("git_commit_oid_invalid")
        return oid

    def tree_oid(self, commit: str) -> str | None:
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
            return None
        result = self._run("rev-parse", "--verify", "--end-of-options", f"{commit}^{{tree}}", check=False)
        if result.returncode:
            return None
        oid = result.stdout.strip()
        return oid if re.fullmatch(rf"[0-9a-f]{{{len(self.zero)}}}", oid) else None

    def blob_sha256(self, commit: str, path: str) -> str | None:
        """Hash a regular-file blob from an immutable tree; paths and content never enter logs."""
        if (not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts
                or "\n" in path or "\r" in path):
            return None
        entry = self._run("ls-tree", "--full-tree", commit, "--", path, check=False)
        if entry.returncode or not entry.stdout:
            return None
        fields = entry.stdout.rstrip("\n").split("\t", 1)[0].split()
        if len(fields) != 3 or fields[0] not in {"100644", "100755"} or fields[1] != "blob":
            return None
        body = self._run("cat-file", "blob", fields[2], check=False)
        if body.returncode:
            return None
        return hashlib.sha256(body.stdout.encode("utf-8")).hexdigest()

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
        commands = ["start", "option no-deref"]
        for ref, new, expected in updates:
            if (not isinstance(ref, str) or any(char.isspace() for char in ref)
                    or not (ref.startswith("refs/subplans/") or ref.startswith("refs/compositions/"))
                    or self._run("check-ref-format", ref, check=False).returncode):
                raise ValueError("COMPOSITION_REF_OUTSIDE_NAMESPACE")
            old = self.zero if expected is None else expected
            oid_pattern = rf"(?:[0-9a-f]{{{len(self.zero)}}})"
            if not re.fullmatch(oid_pattern, old) or (new is not None and not re.fullmatch(oid_pattern, new)):
                raise ValueError("INVALID_REF_OID")
            if new is None:
                commands.extend(("option no-deref", f"delete {ref} {old}"))
            else:
                commands.extend(("option no-deref", f"update {ref} {new} {old}"))
        commands.extend(("prepare", "commit", ""))
        result = subprocess.run(self._command("update-ref", "--stdin"), env=self._environment(),
                                input="\n".join(commands), capture_output=True, text=True, check=False)
        if result.returncode:
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_ref_transaction_failed")

    def tree_digest(self, commit: str, paths: Sequence[str]) -> str:
        if not paths:
            raise ValueError("EMPTY_RELEVANT_PATHS")
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", commit):
            raise ValueError("INVALID_TREE_COMMIT")
        entries: list[str] = []
        missing: list[str] = []
        for path in sorted(set(paths)):
            if (not path or path.startswith("/") or ".." in Path(path).parts
                    or "\n" in path or "\r" in path):
                raise ValueError("INVALID_RELEVANT_PATH")
            result = self._run("ls-tree", "-r", "--full-tree", "--end-of-options", commit, "--", path)
            found = [line for line in result.stdout.splitlines() if line]
            if found:
                entries.extend(found)
            else:
                missing.append(path)
        if missing:
            raise ValueError("TREE_PATHS_MISSING: " + ", ".join(missing))
        return hashlib.sha256("\n".join((*sorted(set(paths)), *sorted(entries))).encode("utf-8")).hexdigest()

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
        marker = {"owner_pid": os.getpid(), "path": str(path)}
        (self.workspace_root / f"{path.name}.composition-owner.json").write_text(json.dumps(marker), encoding="utf-8")
        return str(path)

    def remove_worktree(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        if self.workspace_root not in resolved.parents:
            raise ValueError("WORKTREE_PATH_OUTSIDE_ROOT")
        marker_path = self.workspace_root / f"{resolved.name}.composition-owner.json"
        try:
            marker = json.loads(marker_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError("WORKTREE_OWNERSHIP_UNVERIFIED") from error
        if (not isinstance(marker, dict) or marker.get("path") != str(resolved)
                or marker.get("owner_pid") != os.getpid()):
            raise ValueError("WORKTREE_OWNERSHIP_UNVERIFIED")
        self._run("worktree", "remove", "--force", str(resolved))
        marker_path.unlink()

    def prune_workspaces(self) -> tuple[str, ...]:
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        output = self._run("worktree", "list", "--porcelain").stdout
        removed: list[str] = []
        records = [record.splitlines() for record in output.strip().split("\n\n") if record.strip()]
        for record in records:
            worktree_line = next((line for line in record if line.startswith("worktree ")), None)
            if worktree_line is None or any(line == "locked" or line.startswith("locked ") for line in record):
                continue
            path = Path(worktree_line.removeprefix("worktree ")).resolve()
            if path == self.workspace_root or self.workspace_root not in path.parents:
                continue
            marker_path = self.workspace_root / f"{path.name}.composition-owner.json"
            try:
                marker = json.loads(marker_path.read_text(encoding="utf-8"))
                owner_pid = marker["owner_pid"]
                if marker["path"] != str(path) or type(owner_pid) is not int:
                    continue
                os.kill(owner_pid, 0)
            except ProcessLookupError:
                pass
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue
            else:
                continue
            result = self._run("worktree", "remove", "--force", str(path), check=False)
            if result.returncode:
                detail = result.stderr.strip().splitlines()
                raise GitCommandError(detail[-1] if detail else "git_worktree_remove_failed")
            marker_path.unlink()
            removed.append(str(path))
        return tuple(removed)


def create_engine(repository: str | Path, store_path: str | Path,
                  workspace_root: str | Path, *, allow_owner_state: bool = False) -> tuple[CompositionEngine, Store]:
    repo = Path(repository).resolve()
    state_path = Path(store_path).resolve()
    owner_state = (allow_owner_state is True and repo in state_path.parents and
                   state_path.parent.name == "composition" and state_path.parent.parent.name == ".state")
    if (state_path == repo or repo in state_path.parents) and not owner_state:
        raise ValueError("STORE_PATH_INSIDE_REPOSITORY")
    git = GitSubprocessPort(repository, workspace_root)
    store = Store(store_path)
    return CompositionEngine(git, store, workspace_root), store


def propagate(change: PropagationChange, consumers: Sequence[dict[str, object]],
              evidence: Sequence[dict[str, object]]) -> tuple[Action, ...]:
    """Public owner boundary for the composition engine's explicit consumer actions."""
    return _propagate(change, consumers, evidence)


__all__ = ["Action", "EvidenceKey", "GitCommandError", "GitSubprocessPort", "PropagationChange", "VerdictProof",
           "create_engine", "propagate"]
