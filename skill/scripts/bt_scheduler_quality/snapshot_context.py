"""Read-only, versioned identity input for commands that run without Git metadata."""
from __future__ import annotations

import hashlib
import json

from .sandbox_mounts import Mount
from .snapshot import MaterializedSnapshot

SCHEMA = "m6.snapshot-context/1"
TARGET = "/run/bt-m6/snapshot.json"


def mounts(snapshot: MaterializedSnapshot) -> tuple[Mount, ...]:
    """Publish only a validated materialization's identity, outside its writable workspace."""
    files: dict[str, dict[str, str]] = {}
    for path in sorted(snapshot.directory.rglob("*")):
        name = path.relative_to(snapshot.directory).as_posix()
        if path.is_symlink():
            files[name] = {"kind": "symlink", "target": path.readlink().as_posix()}
        elif path.is_file():
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            files[name] = {"kind": "file", "sha256": digest}
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    data = {"schema": SCHEMA, "snapshot_sha": snapshot.snapshot_sha, "base_sha": snapshot.base_sha,
            "manifest_sha256": snapshot.manifest_sha256, "content_sha256": hashlib.sha256(canonical).hexdigest(),
            "files": files}
    context = snapshot.directory.parent / "verification-context.json"
    context.write_text(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    context.chmod(0o400)
    return (Mount(str(context), TARGET),)
