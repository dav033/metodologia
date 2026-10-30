"""Methodology boundary: real object-only Git operations for `bt_composition`."""
from __future__ import annotations

import hashlib
import os
import re
import json
import subprocess
import tempfile
from pathlib import Path
from collections.abc import Mapping, Sequence

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

    def _run_bytes(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(self._command(*arguments), env=self._environment(),
                                capture_output=True, text=False, check=False)
        if check and result.returncode:
            detail = result.stderr.decode("utf-8", "replace").strip().splitlines()
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
        body = self._run_bytes("cat-file", "blob", fields[2], check=False)
        if body.returncode:
            return None
        return hashlib.sha256(body.stdout).hexdigest()

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
        tree = lines[0].strip()
        if conflicts:
            tree, conflicts = self._merge_manifests(tree, base, ours, theirs, conflicts)
        if conflicts:
            tree, conflicts = self._merge_subsumed(tree, base, ours, theirs, conflicts)
        if conflicts:
            tree, conflicts = self._recorded(tree, base, ours, theirs, conflicts)
        return GitResult(tree, conflicts)

    def _merge_subsumed(self, tree: str, base: str, ours: str, theirs: str,
                        conflicts: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
        """A text file whose every conflicting hunk is one side's change plus additions takes the larger side there
        (`merge_subsumed`). pictures REQ-021 r25: gate T95 and SP-8's line both had the new TABLAS_TRABAJO_CUENTA line
        and SP-8 also added `anonimizarGastoCuenta` after it; the same text conflict came back on every retry (D-172)."""
        blobs: dict[str, str] = {}
        for path in conflicts:
            texts = [self._text_at(revision, path) for revision in (base, ours, theirs)]
            if texts[1] is None or texts[2] is None:
                continue
            merged = merge_subsumed(texts[0] or "", texts[1], texts[2])
            if merged is not None:
                blobs[path] = self._run_input(merged, "hash-object", "-w", "--stdin").stdout.strip()
        if not blobs:
            return tree, conflicts
        return self._with_blobs(tree, blobs), tuple(path for path in conflicts if path not in blobs)

    def _text_at(self, revision: str, path: str) -> str | None:
        """The file at `revision` as text; None when it is missing or not UTF-8 text."""
        shown = self._run_bytes("show", f"{revision}:{path}", check=False)
        if shown.returncode or b"\0" in shown.stdout:
            return None
        try:
            return shown.stdout.decode("utf-8")
        except UnicodeDecodeError:
            return None

    resolutions: Path | None = None             # create_engine: <store folder>/resolutions; None leaves conflicts as they are

    def _recorded(self, tree: str, base: str, ours: str, theirs: str,
                  conflicts: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
        """A conflict resolved once is resolved the same way whenever the same three versions of the file meet again (like
        git rerere): its context waits in `<resolutions>/<key>.diff3` and `.json`; writing `<key>.resolved` (the file's
        final content) settles it, for this gate and every later one composing the same members (pictures REQ-021: SP-4
        and SP-5 both edited TABLAS_TRABAJO_CUENTA, and every gate after them was rejected). A member that changes the
        file gets a new key and asks again."""
        if self.resolutions is None:
            return tree, conflicts
        folder = Path(self.resolutions)
        blobs: dict[str, str] = {}
        for path in conflicts:
            ids = [self._blob_id(revision, path) for revision in (base, ours, theirs)]
            key = hashlib.sha256("\0".join((path, *ids)).encode()).hexdigest()[:32]
            resolved = folder / f"{key}.resolved"
            if resolved.is_file():
                blobs[path] = self._run_input(resolved.read_text(encoding="utf-8"), "hash-object", "-w", "--stdin").stdout.strip()
                continue
            context = folder / f"{key}.json"
            if not context.exists():
                folder.mkdir(parents=True, exist_ok=True)
                (folder / f"{key}.diff3").write_text(self._diff3(path, ids), encoding="utf-8")
                context.write_text(json.dumps({"path": path, "blobs": dict(zip(("base", "ours", "theirs"), ids)),
                                               "commits": {"base": base, "ours": ours, "theirs": theirs},
                                               "resolve": f"write the final content of {path} to {resolved}"},
                                              indent=1) + "\n", encoding="utf-8")
        if not blobs:
            return tree, conflicts
        return self._with_blobs(tree, blobs), tuple(path for path in conflicts if path not in blobs)

    def _blob_id(self, revision: str, path: str) -> str:
        found = self._run("rev-parse", f"{revision}:{path}", check=False)
        return found.stdout.strip() if found.returncode == 0 else "-"

    def _diff3(self, path: str, ids: list[str]) -> str:
        with tempfile.TemporaryDirectory(prefix="bt-compose-diff3-") as scratch:
            files = []
            for name, blob in zip(("base", "ours", "theirs"), ids):
                target = Path(scratch) / name
                target.write_bytes(self._run_bytes("cat-file", "blob", blob).stdout if blob != "-" else b"")
                files.append(str(target))
            merged = subprocess.run(["git", "merge-file", "-p", "--diff3", "-L", f"ours ({path})", "-L", "base",
                                     "-L", "theirs", files[1], files[0], files[2]], capture_output=True, check=False)
            return merged.stdout.decode("utf-8", "replace")

    def _merge_manifests(self, tree: str, base: str, ours: str, theirs: str,
                         conflicts: tuple[str, ...]) -> tuple[str, tuple[str, ...]]:
        """A `package.json` both sides changed is merged by key: each subplan appends its npm scripts at the end of
        "scripts", a text conflict every time (pictures REQ-021: SP-3 needed the owner's hand, r19 rejected three gates).
        Only a value both sides changed differently stays a conflict. Returns the tree and the conflicts left."""
        blobs: dict[str, str] = {}
        for path in conflicts:
            if Path(path).name != "package.json":
                continue
            docs = [self._json_at(revision, path) for revision in (base, ours, theirs)]
            if docs[1] is None or docs[2] is None:
                continue
            merged, clashes = merge_json(docs[0] if docs[0] is not None else {}, docs[1], docs[2])
            if clashes:
                continue
            text = json.dumps(merged, indent=_json_indent(self._run("show", f"{ours}:{path}").stdout), ensure_ascii=False)
            blobs[path] = self._run_input(text + "\n", "hash-object", "-w", "--stdin").stdout.strip()
        if not blobs:
            return tree, conflicts
        return self._with_blobs(tree, blobs), tuple(path for path in conflicts if path not in blobs)

    def _json_at(self, revision: str, path: str) -> object | None:
        shown = self._run("show", f"{revision}:{path}", check=False)
        if shown.returncode:
            return None
        try:
            return json.loads(shown.stdout)
        except ValueError:
            return None

    def _run_input(self, text: str, *arguments: str, extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(self._command(*arguments), env={**self._environment(), **(extra or {})}, input=text,
                                capture_output=True, text=True, check=False)
        if result.returncode:
            detail = result.stderr.strip().splitlines()
            raise GitCommandError(detail[-1] if detail else "git_command_failed")
        return result

    def _with_blobs(self, tree: str, blobs: Mapping[str, str]) -> str:
        """`tree` with each path's blob replaced, through a throwaway index (the repository's own index is never used)."""
        with tempfile.TemporaryDirectory(prefix="bt-compose-index-") as scratch:
            index = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
            self._run_input("", "read-tree", tree, extra=index)
            for path, blob in blobs.items():
                listed = self._run("ls-tree", tree, "--", path).stdout.split()
                mode = listed[0] if listed else "100644"
                self._run_input("", "update-index", "--add", "--cacheinfo", f"{mode},{blob},{path}", extra=index)
            return self._run_input("", "write-tree", extra=index).stdout.strip()

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
    git.resolutions = state_path.parent / "resolutions"
    store = Store(store_path)
    return CompositionEngine(git, store, workspace_root), store


def propagate(change: PropagationChange, consumers: Sequence[dict[str, object]],
              evidence: Sequence[dict[str, object]]) -> tuple[Action, ...]:
    """Public owner boundary for the composition engine's explicit consumer actions."""
    return _propagate(change, consumers, evidence)


def get_candidate(store: Store, candidate_id: str):
    """Load a durable candidate reservation by its manifest identity."""
    return store.get_candidate(candidate_id)


__all__ = ["Action", "EvidenceKey", "GitCommandError", "GitSubprocessPort", "PropagationChange", "VerdictProof",
           "create_engine", "get_candidate", "merge_subsumed", "propagate"]


def merge_json(base: object, ours: object, theirs: object, path: str = "") -> tuple[object, list[str]]:
    """Three-way merge of two JSON documents by key: what one side changed wins, what both changed alike is kept, a value
    both changed differently is a clash. Objects merge key by key (ours' order, then the keys only theirs added); any
    other value is atomic. Returns (merged, clash paths)."""
    clashes: list[str] = []
    if isinstance(ours, dict) and isinstance(theirs, dict):
        base = base if isinstance(base, dict) else {}
        merged: dict = {}
        for key in [*ours, *(k for k in theirs if k not in ours)]:
            at = f"{path}.{key}"
            if key in ours and key in theirs:
                merged[key], found = merge_json(base.get(key), ours[key], theirs[key], at)
                clashes += found
            elif key in ours:                                   # theirs lacks it: added by ours, or deleted by theirs
                if key not in base:
                    merged[key] = ours[key]
                elif base[key] != ours[key]:
                    clashes.append(at)
            else:
                if key not in base:
                    merged[key] = theirs[key]
                elif base[key] != theirs[key]:
                    clashes.append(at)
        return merged, clashes
    if ours == theirs or base == theirs:
        return ours, clashes
    if base == ours:
        return theirs, clashes
    return ours, [path or "."]


MARK = 31                                       # wider than any conflict marker a file of the repository may contain


def merge_subsumed(base: str, ours: str, theirs: str) -> str | None:
    """Three-way text merge that settles a conflicting hunk when one side is the other side's lines plus additions, in
    order, and none of the added lines was in the base there (taking it would bring back what the other side removed).
    Blank lines do not count as added content. Returns the merged text, or None when any hunk is a real conflict."""
    with tempfile.TemporaryDirectory(prefix="bt-compose-subsumed-") as scratch:
        files = []
        for name, text in (("ours", ours), ("base", base), ("theirs", theirs)):
            (Path(scratch) / name).write_text(text, encoding="utf-8")
            files.append(str(Path(scratch) / name))
        done = subprocess.run(["git", "merge-file", "-p", "--diff3", f"--marker-size={MARK}", *files],
                              capture_output=True, text=True, check=False)
    if done.returncode < 0 or done.returncode > 127:
        return None
    if done.returncode == 0:
        return done.stdout
    out: list[str] = []
    block: dict[str, list[str]] = {}
    side = ""
    for line in done.stdout.splitlines(keepends=True):
        if not side and line.startswith("<" * MARK + " "):
            block, side = {"ours": [], "base": [], "theirs": []}, "ours"
        elif side and line.startswith("|" * MARK + " "):
            side = "base"
        elif side and line.rstrip("\r\n") == "=" * MARK:
            side = "theirs"
        elif side and line.startswith(">" * MARK + " "):
            pick = _superset(block["ours"], block["theirs"], block["base"])
            if pick is None:
                return None
            out.extend(pick)
            side = ""
        else:
            (block[side] if side else out).append(line)
    return None if side else "".join(out)


def _superset(ours: list[str], theirs: list[str], base: list[str]) -> list[str] | None:
    for big, small in ((ours, theirs), (theirs, ours)):
        rest = iter(big)
        if all(any(line == other for other in rest) for line in small):
            added = [line for line in big if line not in small and line.strip()]
            if not set(added) & set(base):
                return big
    return None


def _json_indent(text: str) -> int:
    for line in text.splitlines()[1:]:
        stripped = line.lstrip(" ")
        if stripped.startswith('"') and len(line) > len(stripped):
            return len(line) - len(stripped)
    return 2
