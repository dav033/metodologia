"""Immutable approved revisions of PLAN.json and the small reference an executor can keep to one.

Layout inside the plan directory: `plan-revisions/PLAN.r<N>.json` (canonical text, read-only, created exclusively)
and `plan-revisions/MANIFEST.json` (revision, sha256, frozen_at). Changing the scope of an approved plan means a new
revision (N+1); a revision that something executed stays recoverable. Only files under `plan-revisions/` are written.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from . import contract as pc
from ._lock import exclusive

DIR = "plan-revisions"
MANIFEST = "MANIFEST.json"
LOCK_NAME = ".freeze.lock"
HASH_RE = re.compile(r"[0-9a-f]{64}")
FILE_RE = re.compile(r"PLAN\.r([0-9]+)\.json")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest(directory: Path) -> dict:
    folder = Path(directory) / DIR
    path = folder / MANIFEST
    if folder.is_symlink():
        raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"{folder}: revision store must not be a symlink"])
    if folder.exists() and not folder.is_dir():
        raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"{folder}: revision store must be a directory"])
    if path.is_symlink():
        raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"{path}: manifest must not be a symlink"])
    if path.exists() and not path.is_file():
        raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"{path}: manifest must be a regular file"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema": 1, "revisions": []}
    except (OSError, ValueError, RecursionError) as exc:
        raise pc.PlanContractError("REVISION_STORE_UNREADABLE", [f"{path}: {type(exc).__name__}"]) from exc
    entries = data.get("revisions") if isinstance(data, dict) else None
    numbers = [e.get("revision") for e in entries if isinstance(e, dict)] if isinstance(entries, list) else None
    if (numbers is None or len(numbers) != len(entries)
            or any(not (isinstance(n, int) and not isinstance(n, bool) and 1 <= n <= pc.MAX_REVISION) for n in numbers)
            or len(set(numbers)) != len(numbers)
            or any(not (isinstance(e.get("sha256"), str) and HASH_RE.fullmatch(e["sha256"])) for e in entries)):
        raise pc.PlanContractError("REVISION_STORE_UNREADABLE", [f"{path}: unexpected structure"])
    return data


def list_revisions(directory: Path) -> list[dict]:
    return sorted(_manifest(directory)["revisions"], key=lambda item: item["revision"])


def latest(directory: Path) -> dict | None:
    found = list_revisions(directory)
    return found[-1] if found else None


def revision_path(directory: Path, revision: int) -> Path:
    return Path(directory) / DIR / f"PLAN.r{revision}.json"


def load_revision(directory: Path, revision: int) -> dict:
    """The frozen plan of a revision (what a run executed), validated against the manifest hash."""
    entry = next((item for item in list_revisions(directory) if item["revision"] == revision), None)
    if entry is None:
        raise pc.PlanContractError("REVISION_UNKNOWN", [f"revision {revision} was never frozen"])
    path = revision_path(directory, revision)
    if path.is_symlink() or not path.is_file():
        raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"PLAN.r{revision}.json is not a regular file"])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise pc.PlanContractError("REVISION_STORE_UNREADABLE", [
            f"PLAN.r{revision}.json: {type(exc).__name__}"]) from exc
    if sha256(text) != entry["sha256"]:
        raise pc.PlanContractError("REVISION_TAMPERED", [f"PLAN.r{revision}.json does not match its recorded hash"])
    try:
        return json.loads(text)
    except (ValueError, RecursionError) as exc:
        raise pc.PlanContractError("REVISION_STORE_UNREADABLE", [
            f"PLAN.r{revision}.json: {type(exc).__name__}"]) from exc


def orphans(directory: Path) -> list[int]:
    """Revision files on disk that the manifest does not know (a freeze that died between the two writes)."""
    known = {item["revision"] for item in list_revisions(directory)}
    folder = Path(directory) / DIR
    found = [int(m.group(1)) for p in folder.glob("PLAN.r*.json") if (m := FILE_RE.fullmatch(p.name))] \
        if folder.is_dir() else []
    return sorted(n for n in found if n not in known)


def verify_store(directory: Path, tolerate: int | None = None) -> list[str]:
    """Problems with frozen revisions (missing file, hash drift, gaps, orphan files); [] when intact. `tolerate` is a
    revision number whose orphan file freeze() will adopt or reject by itself."""
    problems = [f"PLAN.r{n}.json: file exists but is not in the manifest (interrupted freeze)"
                for n in orphans(directory) if n != tolerate]
    previous = 0
    for item in list_revisions(directory):
        if item["revision"] != previous + 1:
            problems.append(f"revisions: gap before r{item['revision']} (previous r{previous})")
        previous = item["revision"]
        path = revision_path(directory, item["revision"])
        if path.is_symlink():
            problems.append(f"PLAN.r{item['revision']}.json: revision file must not be a symlink")
            continue
        if not path.is_file():
            problems.append(f"PLAN.r{item['revision']}.json: file missing or not a regular file")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            problems.append(f"PLAN.r{item['revision']}.json: unreadable ({type(exc).__name__})")
            continue
        if sha256(text) != item["sha256"]:
            problems.append(f"PLAN.r{item['revision']}.json: content changed after it was frozen")
    return problems


def _write_manifest(folder: Path, data: dict) -> None:
    fd, name = tempfile.mkstemp(dir=folder, prefix=MANIFEST + ".", suffix=".tmp")  # unique: no shared tmp name
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data, indent=1) + "\n")
    os.replace(name, folder / MANIFEST)


def _write_revision(folder: Path, target: Path, text: str) -> None:
    """Install complete bytes atomically and exclusively; a failed write never leaves a partial revision path."""
    fd, name = tempfile.mkstemp(dir=folder, prefix=target.name + ".", suffix=".tmp")
    temporary = Path(name)
    installed = False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o444)
        os.link(temporary, target)
        installed = True
    except OSError:
        if installed:
            target.unlink(missing_ok=True)
        raise
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            if installed:
                target.unlink(missing_ok=True)
            raise


def freeze(directory: Path, plan: dict, source: str = "approval", narrative: str | None = None) -> dict:
    """Freeze a validated plan as its revision. Idempotent for identical content; a different content under an already
    frozen revision number is refused (create revision N+1 instead); gaps are refused. Serialised by a lock; a file
    left by an interrupted freeze is adopted when its content is identical and refused otherwise. `source` is recorded in
    the manifest (not hashed): `approval` (the approval act froze it) or `launch-forced` (the owner's explicit
    --force of a plan that was never approved)."""
    report = pc.validate(plan)
    if not report.ok:
        raise pc.PlanContractError("PLAN_INVALID", report.errors)
    text = pc.dumps(plan)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # lone surrogates: refuse before anything is written
        raise pc.PlanContractError("PLAN_NOT_SERIALISABLE", ["plan contains characters that are not valid Unicode "
                                                              "(lone surrogates)"]) from exc
    number = plan["revision"]
    with exclusive(Path(directory) / DIR / LOCK_NAME):
        last = latest(directory)
        problems = verify_store(directory, tolerate=(last["revision"] + 1) if last else 1)
        if problems:
            raise pc.PlanContractError("REVISION_STORE_DAMAGED", problems)
        if last and number == last["revision"]:
            if sha256(text) == last["sha256"]:
                return last
            raise pc.PlanContractError("REVISION_FROZEN", [
                f"revision {number} is already frozen with different content; set revision to {number + 1} and "
                "freeze again"])
        expected = (last["revision"] + 1) if last else 1
        if number != expected:
            raise pc.PlanContractError("REVISION_ORDER", [f"next revision must be {expected}, got {number}"])
        folder = Path(directory) / DIR
        if folder.is_symlink():  # revisions live inside the requirement folder, never behind a link
            raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"{DIR} must be a real directory, not a symlink"])
        target = revision_path(directory, number)
        target_created = False
        try:
            folder.mkdir(exist_ok=True)
            if target.is_symlink():
                raise pc.PlanContractError("REVISION_STORE_UNSAFE", [f"PLAN.r{number}.json must not be a symlink"])
            if target.exists():
                if not target.is_file():
                    raise pc.PlanContractError("REVISION_STORE_UNSAFE", [
                        f"PLAN.r{number}.json must be a regular file"])
                try:
                    existing_text = target.read_text(encoding="utf-8")
                except (OSError, UnicodeError) as exc:
                    raise pc.PlanContractError("REVISION_STORE_DAMAGED", [
                        f"PLAN.r{number}.json is unreadable ({type(exc).__name__})"]) from exc
                if sha256(existing_text) != sha256(text):
                    raise pc.PlanContractError("REVISION_STORE_DAMAGED", [
                        f"PLAN.r{number}.json exists from an interrupted freeze with different content; "
                        "inspect and remove it"])
                os.chmod(target, 0o444)
            else:
                _write_revision(folder, target, text)
                target_created = True
            entry = {"revision": number, "sha256": sha256(text),
                     "frozen_at": dt.datetime.now().isoformat(timespec="seconds"), "source": source}
            if narrative:
                entry["plan_md_sha256"] = narrative  # not part of the revision hash: prose may carry log lines
            data = _manifest(directory)
            data["revisions"].append(entry)
            _write_manifest(folder, data)
        except OSError as exc:
            if target_created:
                try:
                    target.unlink(missing_ok=True)
                except OSError as cleanup_error:
                    raise pc.PlanContractError("REVISION_STORE_UNWRITABLE", [
                        f"{type(exc).__name__}: cannot write {DIR} for revision {number}; "
                        f"rollback failed ({type(cleanup_error).__name__})"]) from cleanup_error
            raise pc.PlanContractError("REVISION_STORE_UNWRITABLE",
                                       [f"{type(exc).__name__}: cannot write {DIR} for revision {number}"]) from exc
        return entry


def plan_ref(directory: Path) -> dict | None:
    """What a run records about the plan it executes: {plan_id, revision, sha256} of the latest frozen revision."""
    last = latest(directory)
    if not last:
        return None
    return {"plan_id": load_revision(directory, last["revision"])["plan_id"], "revision": last["revision"],
            "sha256": last["sha256"]}


def run_reference(directory: Path) -> dict:
    """Fields an executor may merge into its own new state: `{plan_ref}` when a revision is frozen, `{plan_ref_error}`
    (a stable code) when the store is damaged, `{}` when there is nothing to reference. Never raises for store damage:
    the caller decides; the damage is also reported by `check`."""
    try:
        ref = plan_ref(directory)
    except (pc.PlanContractError, OSError, ValueError, KeyError, TypeError) as exc:
        return {"plan_ref_error": getattr(exc, "code", type(exc).__name__)}
    return {"plan_ref": ref} if ref else {}
