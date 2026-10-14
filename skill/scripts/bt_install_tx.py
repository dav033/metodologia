"""Small filesystem transaction engine for installer operations."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


class TransactionError(RuntimeError):
    """An operation cannot be safely planned or applied."""


@dataclass(frozen=True)
class Operation:
    kind: str
    path: Path
    values: dict[str, Any]


@dataclass(frozen=True)
class Plan:
    operations: tuple[Operation, ...]
    allowed_roots: tuple[Path, ...]


def write_file(path: str | Path, content: str | bytes, mode: int = 0o644) -> Operation:
    """Create or replace a regular file with the requested content and mode."""
    data = content.encode("utf-8") if isinstance(content, str) else bytes(content)
    return Operation("write_file", Path(path), {"content": data, "mode": mode})


def symlink(path: str | Path, target: str | Path) -> Operation:
    """Create or replace a symbolic link."""
    return Operation("symlink", Path(path), {"target": os.fspath(target)})


def json_merge(path: str | Path, merge_fn: Callable[[dict[str, Any]], dict[str, Any]],
               owner_marker: str = "metodologia",
               is_owned: Callable[[Any], bool] | None = None) -> Operation:
    """Merge JSON while retaining unrelated keys and unowned list entries."""
    return Operation("json_merge", Path(path), {"merge_fn": merge_fn, "owner_marker": owner_marker,
                                                  "is_owned": is_owned})


def ensure_block(path: str | Path, block: str, marker: str = "metodologia") -> Operation:
    """Ensure one text block exists between stable marker comments."""
    return Operation("ensure_block", Path(path), {"block": block, "marker": marker})


def plan(ops: list[Operation] | tuple[Operation, ...],
         allowed_roots: tuple[str | Path, ...] | None = None) -> Plan:
    """Freeze operations and reject duplicate target paths."""
    operations = tuple(ops)
    paths = [op.path.absolute() for op in operations]
    if len(set(paths)) != len(paths):
        raise TransactionError("A plan cannot target the same path more than once")
    if any(op.kind not in {"write_file", "symlink", "json_merge", "ensure_block"} for op in operations):
        raise TransactionError("Unknown operation kind")
    if allowed_roots is None:
        roots = (Path(os.path.commonpath([str(op.path.absolute().parent) for op in operations]))
                 if operations else Path.cwd(),)
    else:
        roots = tuple(Path(root).absolute() for root in allowed_roots)
    return Plan(operations, roots)


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _current(path: Path) -> tuple[str, bytes | str | None, int | None, str | None]:
    if not path.is_symlink() and not path.exists():
        return "missing", None, None, None
    if path.is_symlink():
        target = os.readlink(path)
        return "symlink", target, None, _digest(os.fsencode(target))
    if not path.is_file():
        return "other", None, stat.S_IMODE(path.stat().st_mode), None
    data = path.read_bytes()
    return "file", data, stat.S_IMODE(path.stat().st_mode), _digest(data)


def _marker_pair(marker: str) -> tuple[str, str]:
    if marker.endswith(":start -->"):
        return marker, marker.replace(":start -->", ":end -->")
    return f"<!-- {marker}:start -->", f"<!-- {marker}:end -->"


def _json_value(op: Operation, current: bytes | None) -> bytes:
    try:
        original = json.loads(current.decode("utf-8")) if current is not None else {}
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TransactionError(f"Invalid JSON at {op.path}") from exc
    if not isinstance(original, dict):
        raise TransactionError(f"JSON root at {op.path} must be an object")
    def default_owned(item: Any) -> bool:
        if not isinstance(item, dict) or not isinstance(item.get("command"), str):
            return False
        parts = item["command"].replace("\\", "/").split("/")
        return any(parts[index:index + 2] in (["skills", "metodologia"], ["metodologia", "skill"])
                   for index in range(max(0, len(parts) - 1)))
    ownership = op.values.get("is_owned") or default_owned

    def strip_owned(value: Any) -> Any:
        if isinstance(value, dict):
            return {key: strip_owned(item) for key, item in value.items()}
        if isinstance(value, list):
            return [strip_owned(item) for item in value if not ownership(item)]
        return copy.deepcopy(value)

    base = strip_owned(original)
    desired = op.values["merge_fn"](copy.deepcopy(base))
    if not isinstance(desired, dict):
        raise TransactionError("json_merge callback must return an object")

    def merge(old: Any, new: Any) -> Any:
        if isinstance(old, dict) and isinstance(new, dict):
            result = copy.deepcopy(old)
            for key, value in new.items():
                result[key] = merge(result[key], value) if key in result else copy.deepcopy(value)
            return result
        if isinstance(old, list) and isinstance(new, list):
            kept = [item for item in old if not ownership(item)]
            added, seen = [], set()
            for item in new:
                if not ownership(item):
                    continue
                encoded = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if encoded not in seen:
                    added.append(item)
                    seen.add(encoded)
            return kept + added
        return copy.deepcopy(new)

    return (json.dumps(merge(base, desired), indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _desired(op: Operation, current: tuple[str, bytes | str | None, int | None, str | None]
             ) -> tuple[str, bytes | str | None, int | None, str | None]:
    kind, value, mode, digest = current
    if kind not in ("missing", "file", "symlink"):
        raise TransactionError(f"Target is not a file or symlink: {op.path}")
    if op.kind == "symlink":
        target = op.values["target"]
        return "symlink", target, None, _digest(os.fsencode(target))
    if kind == "symlink":
        raise TransactionError(f"Refusing to replace symlink with a file: {op.path}")
    if op.kind == "write_file":
        content = op.values["content"]
        return "file", content, op.values["mode"], _digest(content)
    if op.kind == "json_merge":
        content = _json_value(op, value if kind == "file" else None)
        return "file", content, mode or 0o644, _digest(content)
    if op.kind == "ensure_block":
        text = (value or b"").decode("utf-8")
        start, end = _marker_pair(op.values["marker"])
        block = op.values["block"].strip("\n")
        if start in text or end in text:
            if start not in text or end not in text or text.index(start) > text.index(end):
                raise TransactionError(f"Unpaired block marker at {op.path}")
            before, rest = text.split(start, 1)
            _, after = rest.split(end, 1)
            text = before.rstrip("\n") + "\n" + start + "\n" + block + "\n" + end + after
        else:
            text = text.rstrip("\n") + "\n" + start + "\n" + block + "\n" + end + "\n"
        content = text.encode("utf-8")
        return "file", content, mode or 0o644, _digest(content)
    raise TransactionError(f"Unknown operation kind: {op.kind}")


def dry_run(transaction: Plan) -> dict[str, Any]:
    """Describe each operation without creating directories or writing files."""
    results = []
    for op in transaction.operations:
        current = _current(op.path)
        try:
            desired = _desired(op, current)
            if desired[0] == current[0] and desired[3] == current[3] and desired[2] == current[2]:
                action = "unchanged"
            else:
                action = "create" if current[0] == "missing" else "update"
        except TransactionError as exc:
            action = "conflict"
            results.append({"path": str(op.path), "kind": op.kind, "action": action, "reason": str(exc)})
            continue
        results.append({"path": str(op.path), "kind": op.kind, "action": action})
    return {"operations": results, "changed": any(row["action"] in ("create", "update") for row in results)}


def _snapshot(path: Path, backup_dir: Path, index: int) -> dict[str, Any]:
    kind, value, mode, digest = _current(path)
    row: dict[str, Any] = {"path": str(path.absolute()), "exists": kind != "missing", "kind": kind,
                           "sha256": digest, "mode": mode}
    if kind == "symlink":
        row["target"] = value
    elif kind == "file":
        backup = backup_dir / f"preimage-{index:04d}-{digest}"
        fd = os.open(backup, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        row["backup"] = str(backup)
    return row


def _append(journal: Path, row: dict[str, Any]) -> None:
    with journal.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _replace_file(path: Path, data: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _validate_target(path: Path, roots: tuple[Path, ...]) -> None:
    absolute = path.absolute()
    if ".." in path.parts or not absolute.is_absolute():
        raise TransactionError(f"Unsafe transaction path: {path}")
    root = next((candidate for candidate in roots if absolute.is_relative_to(candidate)), None)
    if root is None:
        raise TransactionError(f"Transaction path is outside allowed roots: {path}")
    cursor = absolute.parent
    while cursor != cursor.parent and cursor.is_relative_to(root):
        if cursor.is_symlink() and not cursor.resolve(strict=False).is_relative_to(root.resolve(strict=False)):
            raise TransactionError(f"Refusing symlinked parent outside plan root: {cursor}")
        cursor = cursor.parent


def _read_rows(journal: Path) -> tuple[list[dict[str, Any]], bool]:
    content = journal.read_text(encoding="utf-8")
    lines = content.splitlines()
    torn = bool(content and not content.endswith("\n"))
    rows = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if index == len(lines) - 1 and torn:
                return rows, True
            raise
    return rows, torn


def _apply_one(op: Operation, desired: tuple[str, bytes | str | None, int | None, str | None]) -> None:
    kind, value, mode, _ = desired
    if kind == "symlink":
        op.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = op.path.with_name(f".{op.path.name}.tx-{os.getpid()}")
        if os.path.lexists(temporary):
            temporary.unlink()
        temporary.symlink_to(value)
        os.replace(temporary, op.path)
    else:
        _replace_file(op.path, value, mode or 0o644)


def apply(transaction: Plan, backup_dir: str | Path, fail_after: int | None = None) -> dict[str, Any]:
    """Capture preimages, then journal and apply operations one at a time."""
    backup = Path(backup_dir)
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup.chmod(0o700)
    journal = backup / "journal.jsonl"
    if fail_after == 0:
        raise InjectedFailure("Injected failure after 0 operations")
    for op in transaction.operations:
        _validate_target(op.path, transaction.allowed_roots)
    existing_rows = []
    if journal.exists():
        try:
            existing_rows, torn = _read_rows(journal)
            if torn:
                content = journal.read_bytes()
                boundary = content.rfind(b"\n") + 1
                with journal.open("wb") as stream:
                    stream.write(content[:boundary])
                    stream.flush()
                    os.fsync(stream.fileno())
        except (OSError, json.JSONDecodeError) as exc:
            raise TransactionError(f"Invalid journal: {journal}") from exc
    offset = max((row.get("index", -1) for row in existing_rows), default=-1) + 1
    if not existing_rows:
        _append(journal, {"event": "header", "allowed_roots": [str(root) for root in transaction.allowed_roots],
                          "backup_root": str(backup.absolute())})
    preimages = [_snapshot(op.path, backup, offset + i) for i, op in enumerate(transaction.operations)]
    results = []
    completed = 0
    for index, (op, preimage) in enumerate(zip(transaction.operations, preimages), start=offset):
        current = _current(op.path)
        try:
            desired = _desired(op, current)
        except TransactionError as exc:
            raise TransactionError(f"Conflict at {op.path}: {exc}") from exc
        unchanged = desired[0] == current[0] and desired[3] == current[3] and desired[2] == current[2]
        created_dirs = []
        parent = op.path.absolute().parent
        cursor = parent
        while not cursor.exists():
            created_dirs.append(str(cursor))
            cursor = cursor.parent
        begin = {"event": "begin", "index": index, "preimage": preimage,
                 "postimage_sha256": current[3] if unchanged else desired[3],
                 "created_dirs": created_dirs, "unchanged": unchanged}
        _append(journal, begin)
        if not unchanged:
            _apply_one(op, desired)
        _append(journal, {"event": "done", "index": index, "postimage_sha256": desired[3]})
        completed += 1
        results.append({"path": str(op.path), "action": "unchanged" if unchanged else
                        "create" if preimage["kind"] == "missing" else "update"})
        if fail_after is not None and completed >= fail_after:
            raise InjectedFailure(f"Injected failure after {completed} operations")
    return {"operations": results, "changed": any(row["action"] != "unchanged" for row in results),
            "journal": str(journal)}


class InjectedFailure(RuntimeError):
    """Test-only interruption raised after a configured number of completed operations."""


def rollback(journal_path: str | Path) -> dict[str, Any]:
    """Restore a transaction's preimages only while its postimage is still present."""
    journal = Path(journal_path)
    try:
        rows, torn = _read_rows(journal)
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError(f"Invalid journal: {journal}") from exc
    begins = {row["index"]: row for row in rows if row.get("event") == "begin"}
    header = next((row for row in rows if row.get("event") == "header"), None)
    if not header:
        raise TransactionError("Journal has no allowed-roots header")
    roots = tuple(Path(root) for root in header.get("allowed_roots", []))
    backup_root = Path(header.get("backup_root", ""))
    if not roots or not backup_root.is_absolute():
        raise TransactionError("Journal header has invalid roots")
    restored, conflicts = [], []
    for index in sorted(begins, reverse=True):
        row = begins[index]
        preimage = row["preimage"]
        path = Path(preimage["path"])
        if not path.is_absolute() or ".." in path.parts or not any(path.is_relative_to(root) for root in roots):
            raise TransactionError(f"Unsafe path in journal: {path}")
        _validate_target(path, roots)
        current = _current(path)
        if current[3] != row["postimage_sha256"]:
            if current[3] == preimage.get("sha256"):
                continue
            conflicts.append(str(path))
            continue
        if preimage["kind"] == "missing":
            if path.is_symlink() or path.is_file():
                path.unlink()
        elif preimage["kind"] == "file":
            backup_path = Path(preimage["backup"])
            if (not backup_path.is_absolute() or ".." in backup_path.parts or
                    not backup_path.is_relative_to(backup_root)):
                raise TransactionError(f"Unsafe backup path in journal: {backup_path}")
            data = backup_path.read_bytes()
            if _digest(data) != preimage.get("sha256"):
                conflicts.append(str(path))
                continue
            _replace_file(path, data, preimage["mode"] or 0o600)
        elif preimage["kind"] == "symlink":
            path.unlink(missing_ok=True)
            path.symlink_to(preimage["target"])
        restored.append(str(path))
        for directory in row.get("created_dirs", []):
            directory_path = Path(directory)
            if (not directory_path.is_absolute() or ".." in directory_path.parts or
                    not any(directory_path.is_relative_to(root) for root in roots)):
                raise TransactionError(f"Unsafe created directory in journal: {directory_path}")
            try:
                directory_path.rmdir()
            except OSError:
                pass
    return {"restored": restored, "conflicts": conflicts,
            "warnings": ["torn_trailing_line"] if torn else []}
