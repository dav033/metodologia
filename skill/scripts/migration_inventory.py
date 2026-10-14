#!/usr/bin/env python3
"""Private preservation copies, not transactional backups or process checkpoints.

POSIX only: directory descriptors and O_NOFOLLOW prevent symlink traversal.
Three observations (inventory, copy, inventory) must agree. Writers can still
change data after observation; drain/reconcile them separately before cutover.
Failed operations retain private partial data without a success manifest.
Restore checks the destination, builds a `.partial` sibling and renames it: a directory another process creates
in between is replaced only if it is empty (POSIX rename); the operator chooses a fresh root, single-user.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import time
from pathlib import Path, PurePosixPath

CACHE_NAMES = frozenset({"__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache"})
SOURCE_EXCLUSIONS = CACHE_NAMES | {".git"}  # `.git` only at the root of the source tree: history goes in a bundle
DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)


class InventoryError(Exception):
    """A stable error code; never includes file contents or credentials."""


class Budget:
    def __init__(self, max_bytes: int, max_entries: int, seconds: float) -> None:
        if max_bytes <= 0 or max_entries <= 0 or not 0 < seconds < float("inf"):
            raise InventoryError("INVALID_LIMIT")
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self.deadline = time.monotonic() + seconds
        self.bytes = self.entries = 0

    def check(self, size: int = 0, entries: int = 0) -> None:
        self.bytes += size
        self.entries += entries
        if (self.bytes > self.max_bytes or self.entries > self.max_entries
                or time.monotonic() > self.deadline):
            raise InventoryError("LIMIT_EXCEEDED")


def fingerprint(info: os.stat_result) -> list[int]:
    return [info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns]


def new_private_directory(path: Path) -> None:
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        raise InventoryError("DESTINATION_EXISTS") from None


def read_file(fd: int, budget: Budget, target: Path | None = None) -> tuple[str, int]:
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode):
        raise InventoryError("UNSUPPORTED_FILE")
    digest, size = hashlib.sha256(), 0
    output = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600) if target else None
    try:
        while data := os.read(fd, 1024 * 1024):
            budget.check(len(data))
            digest.update(data)
            size += len(data)
            if output is not None:
                view = memoryview(data)
                while view:
                    written = os.write(output, view)
                    if written <= 0:
                        raise InventoryError("WRITE_FAILED")
                    view = view[written:]
        if output is not None:
            os.fsync(output)
        if fingerprint(before) != fingerprint(os.fstat(fd)):
            raise InventoryError("SOURCE_CHANGED")
    finally:
        if output is not None:
            os.close(output)
    return digest.hexdigest(), size


def scan(fd: int, budget: Budget, exclusions: frozenset[str],
         target: Path | None = None, relative: str = "", depth: int = 0,
         skip_paths: frozenset[str] = frozenset(), root_only: frozenset[str] = frozenset()) -> tuple[dict, list]:
    budget.check(entries=1)
    if depth > 128:
        raise InventoryError("LIMIT_DEPTH")
    before = fingerprint(os.fstat(fd))
    entries, excluded = {}, []
    with os.scandir(fd) as children:
        names = []
        for child in children:
            budget.check(entries=1)
            names.append(child.name)
    for name in sorted(names):
        path = f"{relative}/{name}" if relative else name
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if path in skip_paths:
            excluded.append({"path": path, "reason": "captured-separately-as-state"})
            continue
        if name in exclusions or (depth == 0 and name in root_only):
            excluded.append({"path": path, "reason": "git-internals-or-cache"})
            continue
        entry = {"fingerprint": fingerprint(info), "mode": stat.S_IMODE(info.st_mode)}
        destination = target / name if target else None
        if stat.S_ISLNK(info.st_mode):
            entry.update(kind="symlink", link=os.readlink(name, dir_fd=fd))
        elif stat.S_ISDIR(info.st_mode):
            entry["kind"] = "directory"
            if destination:
                new_private_directory(destination)
            nested = os.open(name, DIRECTORY_FLAGS, dir_fd=fd)
            try:
                if fingerprint(os.fstat(nested)) != fingerprint(info):
                    raise InventoryError("SOURCE_CHANGED")
                descendants, omitted = scan(nested, budget, exclusions, destination, path, depth + 1, skip_paths,
                                            root_only)
                entries.update(descendants)
                excluded.extend(omitted)
            finally:
                os.close(nested)
        elif stat.S_ISREG(info.st_mode):
            stream = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                if fingerprint(os.fstat(stream)) != fingerprint(info):
                    raise InventoryError("SOURCE_CHANGED")
                digest, size = read_file(stream, budget, destination)
                entry.update(kind="file", sha256=digest, size=size)
            finally:
                os.close(stream)
        else:
            raise InventoryError("UNSUPPORTED_FILE")
        if fingerprint(os.stat(name, dir_fd=fd, follow_symlinks=False)) != fingerprint(info):
            raise InventoryError("SOURCE_CHANGED")
        entries[path] = entry
    if before != fingerprint(os.fstat(fd)):
        raise InventoryError("SOURCE_CHANGED")
    return entries, excluded


def capture(source: Path, state: Path, destination: Path, *, max_bytes: int = 10 * 1024**3,
            max_entries: int = 200_000, seconds: float = 120) -> dict:
    if os.name != "posix" or not hasattr(os, "O_NOFOLLOW"):
        raise InventoryError("UNSUPPORTED_PLATFORM")
    roots = {"source": source.resolve(strict=True), "state": state.resolve(strict=True)}
    destination = destination.absolute()
    resolved_destination = destination.resolve()
    if any(resolved_destination == p or resolved_destination.is_relative_to(p)
           or p.is_relative_to(resolved_destination) for p in roots.values()):
        raise InventoryError("DESTINATION_OVERLAP")
    budget = Budget(max_bytes * 3, max_entries * 3, seconds)
    skip = frozenset()  # a state root that lives inside the source tree is captured once, as state
    if roots["state"].is_relative_to(roots["source"]) and roots["state"] != roots["source"]:
        skip = frozenset({roots["state"].relative_to(roots["source"]).as_posix()})
    new_private_directory(destination)
    payload = destination / "payload"
    new_private_directory(payload)
    descriptors = {}
    manifest = {"version": 1, "transaction_consistent": False,
                "consistency": "three-matching-observations; not a process checkpoint",
                "roots": {}, "entries": {}, "excluded": {}}
    try:
        for label, path in roots.items():
            descriptors[label] = os.open(path, DIRECTORY_FLAGS)
            manifest["roots"][label] = {"path": str(path), "kind": "preservation-source"
                                        if label == "source" else "live-state",
                                        "fingerprint": fingerprint(os.fstat(descriptors[label]))}
        for phase in range(3):
            for label, fd in descriptors.items():
                target = payload / label if phase == 1 else None
                if target:
                    new_private_directory(target)
                is_source = label == "source"
                entries, excluded = scan(fd, budget, CACHE_NAMES if is_source else frozenset(), target,
                                         skip_paths=skip if is_source else frozenset(),
                                         root_only=frozenset({".git"}) if is_source else frozenset())
                if phase == 0:
                    manifest["entries"][label], manifest["excluded"][label] = entries, excluded
                elif (entries != manifest["entries"][label]
                      or excluded != manifest["excluded"][label]):
                    raise InventoryError("SOURCE_CHANGED")
                if fingerprint(roots[label].stat()) != manifest["roots"][label]["fingerprint"]:
                    raise InventoryError("SOURCE_CHANGED")
        manifest["exclusion_policy"] = {"source": sorted(CACHE_NAMES) + [".git (root only)"], "state": [],
                                        "skipped_paths": sorted(skip)}
        with os.fdopen(os.open(destination / "manifest.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                               0o600), "w", encoding="utf-8") as output:
            json.dump(manifest, output, ensure_ascii=True, indent=2)
            output.flush()
            os.fsync(output.fileno())
        return manifest
    except OSError:
        raise InventoryError("CAPTURE_IO_ERROR_OR_SOURCE_CHANGED") from None
    finally:
        for fd in descriptors.values():
            os.close(fd)


def validate_manifest(value: object) -> dict:
    if not isinstance(value, dict) or value.get("version") != 1:
        raise InventoryError("INVALID_MANIFEST_VERSION")
    groups = value.get("entries")
    if not isinstance(groups, dict) or set(groups) != {"source", "state"}:
        raise InventoryError("INVALID_MANIFEST")
    for entries in groups.values():
        if not isinstance(entries, dict):
            raise InventoryError("INVALID_MANIFEST")
        if any(not isinstance(entry, dict) for entry in entries.values()):
            raise InventoryError("INVALID_MANIFEST")
        for path, entry in entries.items():
            if not isinstance(path, str):
                raise InventoryError("INVALID_MANIFEST_PATH")
            parsed = PurePosixPath(path)
            if (not path or parsed.is_absolute() or str(parsed) != path
                    or any(part in {"..", "."} for part in parsed.parts) or "\x00" in path
                    or not isinstance(entry, dict)):
                raise InventoryError("INVALID_MANIFEST_PATH")
            kind = entry.get("kind")
            if kind not in {"file", "directory", "symlink"}:
                raise InventoryError("INVALID_MANIFEST_KIND")
            if kind == "symlink" and (not isinstance(entry.get("link"), str)
                                      or "\x00" in entry["link"] or not entry["link"]):
                raise InventoryError("INVALID_MANIFEST_LINK")
            if kind == "file" and (not isinstance(entry.get("sha256"), str)
                                   or len(entry["sha256"]) != 64
                                   or type(entry.get("size")) is not int or entry["size"] < 0):
                raise InventoryError("INVALID_MANIFEST_HASH")
            if type(entry.get("mode")) is not int or not 0 <= entry["mode"] <= 0o7777:
                raise InventoryError("INVALID_MANIFEST_MODE")
            for parent in parsed.parents:
                if str(parent) != "." and entries.get(str(parent), {}).get("kind") != "directory":
                    raise InventoryError("INVALID_MANIFEST_PARENT")
    return value


def open_relative(root_fd: int, relative: str) -> int:
    current = os.dup(root_fd)
    try:
        parts = PurePosixPath(relative).parts
        for part in parts[:-1]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=current)
            os.close(current)
            current = child
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=current)
    finally:
        os.close(current)


def restore(backup: Path, destination: Path, *, max_bytes: int = 10 * 1024**3,
            max_entries: int = 200_000, seconds: float = 120) -> None:
    budget = Budget(max_bytes, max_entries, seconds)
    if destination.exists() or destination.is_symlink():
        raise InventoryError("DESTINATION_EXISTS")
    if destination.resolve().is_relative_to(backup.resolve()):
        raise InventoryError("DESTINATION_OVERLAP")
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists() or partial.is_symlink():
        raise InventoryError("DESTINATION_EXISTS")
    root_fd = os.open(backup, DIRECTORY_FLAGS)
    try:
        manifest_fd = open_relative(root_fd, "manifest.json")
        with os.fdopen(manifest_fd, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise InventoryError("INVALID_MANIFEST")
            raw = stream.read(64 * 1024**2 + 1)
            if len(raw) > 64 * 1024**2:
                raise InventoryError("LIMIT_MANIFEST")
        manifest = validate_manifest(json.loads(raw))
        new_private_directory(partial)  # a failed restore never leaves a tree that looks complete
        try:
            _materialize(manifest, root_fd, partial, budget)
            os.rename(partial, destination)
        except BaseException:
            shutil.rmtree(partial, ignore_errors=True)  # we created it a moment ago; nothing else lives there
            raise
    except InventoryError:
        raise
    except (OSError, ValueError, TypeError, AttributeError, RecursionError):
        raise InventoryError("RESTORE_IO_OR_MANIFEST_ERROR") from None
    finally:
        os.close(root_fd)


def _materialize(manifest: dict, root_fd: int, base_root: Path, budget: Budget) -> None:
    for label, entries in manifest["entries"].items():
        base = base_root / label
        new_private_directory(base)
        # Links are created last; no write can traverse a restored external link.
        ordered = sorted(entries, key=lambda p: (entries[p]["kind"] == "symlink", len(PurePosixPath(p).parts), p))
        for relative in ordered:
            budget.check(entries=1)
            entry, target = entries[relative], base / relative
            if entry["kind"] == "directory":
                new_private_directory(target)
            elif entry["kind"] == "symlink":
                target.symlink_to(entry["link"])
            else:
                fd = open_relative(root_fd, f"payload/{label}/{relative}")
                try:
                    digest, size = read_file(fd, budget, target)
                finally:
                    os.close(fd)
                if digest != entry["sha256"] or size != entry["size"]:
                    raise InventoryError("RESTORE_HASH_MISMATCH")
                target.chmod(0o600 | (entry["mode"] & 0o100))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture")
    capture_parser.add_argument("--source", type=Path, required=True)
    capture_parser.add_argument("--state", type=Path, required=True)
    restore_parser = commands.add_parser("restore")
    restore_parser.add_argument("--backup", type=Path, required=True)
    for command in (capture_parser, restore_parser):
        command.add_argument("--destination", type=Path, required=True)
        command.add_argument("--max-bytes", type=int, default=10 * 1024**3)
        command.add_argument("--max-entries", type=int, default=200_000)
        command.add_argument("--seconds", type=float, default=120)
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        (capture if command == "capture" else restore)(**args)
    except (InventoryError, OSError) as error:
        print(str(error) if isinstance(error, InventoryError) else "FILESYSTEM_ERROR", file=sys.stderr)
        return 1
    print("PRESERVATION_CAPTURED_NON_TRANSACTIONAL" if command == "capture" else "RESTORED_TO_NEW_ROOT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
