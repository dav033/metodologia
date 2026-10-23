"""Give read-only failure analysts the sealed source they are reasoning about."""
from __future__ import annotations

import json
import re
import subprocess
import tarfile
from pathlib import Path

import bt_recovery_export as export


def materialize(manifest: Path, destination: Path) -> dict:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    revision = data.get("snapshot_sha")
    repository = data.get("repository")
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision) or not isinstance(repository, str):
        raise ValueError("snapshot identity unavailable")
    destination.mkdir(mode=0o700)
    archive = destination.parent / "analyst-source.tar"
    try:
        done = subprocess.run(["git", "-C", repository, "archive", "--format=tar", f"--output={archive}", revision],
                              capture_output=True, timeout=60, check=False)
        if done.returncode:
            raise ValueError("captured source cannot be archived")
        with tarfile.open(archive) as source:
            members = source.getmembers()
            if len(members) > 50000 or sum(member.size for member in members) > 256 * 1024 * 1024:
                raise ValueError("analyst source exceeds the bounded archive budget")
            members = [member for member in members if not any(
                part == ".env" or part.startswith(".env.") for part in Path(member.name).parts)]
            source.extractall(destination, members=members, filter="data")
    except (tarfile.TarError, subprocess.TimeoutExpired, OSError) as error:
        raise ValueError(f"captured source unavailable: {type(error).__name__}") from error
    finally:
        archive.unlink(missing_ok=True)
    return {"source_available": True, "source_directory": str(destination),
            "source_snapshot": revision, "source_attempt": data.get("attempt_id")}


def prepare(rdir: Path, task: str, doc: dict, work: Path) -> dict:
    for attempt in reversed(doc.get("tasks", {}).get(task, {}).get("attempts", [])):
        try:
            manifest = export._manifest_path(rdir, attempt)
            return materialize(manifest, work / "source")
        except (FileNotFoundError, export.ExportError):
            continue
        except (ValueError, OSError) as error:
            return {"source_available": False, "source_error": str(error)[:200]}
    return {"source_available": False, "source_error": "no sealed source snapshot is available"}
