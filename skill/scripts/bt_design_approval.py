"""Durable owner approvals for versioned UI contracts.

Once a requirement has an executor run, the approved digest is read from that run's subplan line in the design task's
repository. Before a run exists, approval uses HEAD so a contract can be reviewed before launch.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FILE = "design-approvals.json"
_REF = re.compile(r"(?P<contract>[a-z0-9][a-z0-9-]{0,63})@v(?P<version>[1-9][0-9]{0,5})\Z")
_PATH = re.compile(r"design/contracts/[a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5}\.md\Z")
_FALLBACK_LOCK = threading.RLock()


class DesignApprovalError(ValueError):
    """A rejected approval transition or an invalid contract reference."""


def parse_ref(value: str) -> tuple[str, int]:
    match = _REF.fullmatch(value or "")
    if match is None:
        raise DesignApprovalError("Contract must be <contract>@v<N>, for example checkout@v1")
    return match.group("contract"), int(match.group("version"))


def contract_path(value: str) -> str:
    contract, version = parse_ref(value)
    return f"design/contracts/{contract}@v{version}.md"


def revision_for_contract(root: Path, project: str, rdir: Path, ref: str, repo: Path) -> str:
    """Resolve the digest source to the newest executor run's exact design subplan line, else HEAD.

    `executor_root` supplies the requirement-specific root convention. Its identity suffix is the run identity used by
    scheduler wiring, while `Line.ref` supplies the integration-line ref format and role/subplan escaping.
    """
    contract, version = parse_ref(ref)
    try:
        plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
        subplan = next(item for item in plan["subplans"] if isinstance(item, dict) and
                       isinstance(item.get("ui"), dict) and item["ui"].get("contract") == contract and
                       item["ui"].get("version") == version)
        design_id = subplan["ui"]["design_task"]
        task = next(item for item in plan["tasks"] if isinstance(item, dict) and item.get("id") == design_id)
        role = task.get("repository") or ""
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, StopIteration):
        raise DesignApprovalError(f"Cannot resolve design task and repository for {ref}") from None

    import bt_integration_line
    import bt_scheduler_executor_adapter

    if not role:
        import bt_workspace
        role = next((name for name, path in bt_workspace.repos(Path(root), project).items()
                     if Path(path).resolve() == Path(repo).resolve()), "")
    if not role:
        raise DesignApprovalError(f"Cannot resolve design repository role for {ref}")
    base = bt_scheduler_executor_adapter.executor_root(Path(rdir))
    candidates = [path for path in base.parent.glob(base.name + "-*") if path.is_dir() and not path.is_symlink()]
    if not candidates:
        return "HEAD"
    newest = max(candidates, key=lambda path: path.stat().st_mtime_ns)
    identity = newest.name[len(base.name) + 1:]
    if not identity:
        raise DesignApprovalError(f"Cannot resolve the active Scheduler run identity for {ref}")
    line = bt_integration_line.Line(
        plan=None, accepted=lambda: {}, snapshot_of=lambda _attempt: None, repo_of=lambda _role: repo,
        default_repository=role, identity=identity, scope_id=subplan["id"])
    return line.ref(role)


def contract_snapshot_for(root: Path, project: str, rdir: Path, ref: str, repo: Path) -> tuple[str, str] | None:
    """Return the current run-scoped contract text and digest, or the pre-run HEAD snapshot."""
    return contract_snapshot(repo, contract_path(ref), revision_for_contract(root, project, rdir, ref, repo))


def _read_blob(repo: Path, revision: str, path: str) -> bytes | None:
    if not _PATH.fullmatch(path) or path.startswith("-"):
        return None
    try:
        resolved = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "--end-of-options",
                                   f"{revision}^{{commit}}"], cwd=repo, capture_output=True, check=True,
                                  timeout=5).stdout.strip().decode("ascii")
        if not re.fullmatch(r"[0-9a-f]{40,64}", resolved):
            return None
        entry = subprocess.run(["git", "ls-tree", "--end-of-options", resolved, "--", path], cwd=repo,
                               capture_output=True, check=True, timeout=5).stdout
        if not (entry.startswith(b"100644 blob ") or entry.startswith(b"100755 blob ")):
            return None
        output = subprocess.run(["git", "show", f"{resolved}:{path}"], cwd=repo, capture_output=True,
                                check=True, timeout=5)
        return output.stdout
    except (OSError, subprocess.SubprocessError, UnicodeError):
        return None


def _load(rdir: Path) -> dict[str, Any]:
    path = Path(rdir) / FILE
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "approvals": {}}
    except (OSError, UnicodeError, ValueError) as exc:
        raise DesignApprovalError(f"Cannot read {path.name}: {exc}") from None
    if not isinstance(value, dict) or value.get("schema_version") != 1 or not isinstance(value.get("approvals"), dict):
        raise DesignApprovalError(f"Invalid {path.name} schema")
    return value


def _write(rdir: Path, data: dict[str, Any]) -> None:
    target = Path(rdir) / FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{FILE}.", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=1, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, target)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def approvals(rdir: Path) -> dict[str, dict[str, Any]]:
    return _load(rdir)["approvals"]


def decide(rdir: Path, repo: Path, ref: str, approve: bool, comments: str, who: str, via: str,
           *, revision: str | None = None, submitted_sha256: str | None = None) -> dict[str, Any]:
    if revision is None:
        rdir = Path(rdir)
        if rdir.parent.name == "requirements":
            project_dir = rdir.parent.parent
            revision = revision_for_contract(project_dir.parent, project_dir.name, rdir, ref, repo)
        else:
            revision = "HEAD"
    with _decision_lock(Path(rdir)):
        return _decide_locked(rdir, repo, ref, approve, comments, who, via, revision, submitted_sha256)


@contextmanager
def _decision_lock(rdir: Path):
    """Serialize read-check-write transitions across threaded dashboard requests (POSIX)."""
    lock = None
    fallback = False
    try:
        import fcntl
        target = Path(rdir) / f".{FILE}.lock"
        target.parent.mkdir(parents=True, exist_ok=True)
        lock = target.open("a+b")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
    except (ImportError, OSError):  # non-POSIX or unavailable lock storage: preserve existing behavior
        if lock:
            lock.close()
        lock = None
        _FALLBACK_LOCK.acquire()
        fallback = True
    try:
        yield
    finally:
        if lock:
            try:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            finally:
                lock.close()
        elif fallback:
            _FALLBACK_LOCK.release()


def _decide_locked(rdir: Path, repo: Path, ref: str, approve: bool, comments: str, who: str, via: str,
                   revision: str, submitted_sha256: str | None) -> dict[str, Any]:
    path = contract_path(ref)
    data = _load(rdir)
    prior = data["approvals"].get(ref)
    if isinstance(prior, dict) and prior.get("status") == "approved":
        raise DesignApprovalError(f"{ref} is already approved; approvals are immutable")
    file = Path(repo) / path
    if approve and file.is_symlink():
        raise DesignApprovalError(f"Cannot approve {ref}: contract working tree path is a symlink")
    blob = _read_blob(Path(repo), revision, path)
    if approve and blob is None:
        raise DesignApprovalError(f"Cannot approve {ref}: {path} is absent from {revision} in {repo}")
    if approve:
        try:
            status = subprocess.run(["git", "status", "--porcelain", "--", path], cwd=repo,
                                    capture_output=True, check=True, timeout=5).stdout
        except (OSError, subprocess.SubprocessError) as exc:
            raise DesignApprovalError(f"Cannot check contract working tree: {exc}") from None
        if status:
            raise DesignApprovalError(f"Cannot approve {ref}: contract working tree is dirty")
    digest = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if approve and via == "web" and not submitted_sha256:
        raise DesignApprovalError(f"Cannot approve {ref}: reload the contract page to submit its SHA256")
    if approve and submitted_sha256 is not None and submitted_sha256 != digest:
        raise DesignApprovalError(f"Cannot approve {ref}: contract changed since this page was rendered; reload")
    record = {"contract": ref, "path": path, "status": "approved" if approve else "changes-requested",
              "sha256": digest,
              "who": who, "via": via, "when": datetime.now(UTC).isoformat(timespec="seconds"),
              "comments": comments.strip()}
    data["approvals"][ref] = record
    _write(rdir, data)
    return record


def contract_snapshot(repo: Path, path: str, revision: str = "HEAD") -> tuple[str, str] | None:
    """Text and digest of the regular-file blob that the approval gate will inspect."""
    blob = _read_blob(Path(repo), revision, path)
    if blob is None:
        return None
    return blob.decode("utf-8"), hashlib.sha256(blob).hexdigest()


def check_tree(rdir: Path, repo: Path, base: str, path: str) -> dict[str, Any]:
    """Return a gate state using the exact base tree blob (`approved`, `unapproved`, or `hash-mismatch`)."""
    match = re.fullmatch(r"design/contracts/([a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5})\.md", path or "")
    if match is None:
        return {"state": "unapproved", "approval": None, "sha256": None}
    ref = match.group(1)
    approval = approvals(rdir).get(ref)
    blob = _read_blob(Path(repo), base, path)
    digest = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if not isinstance(approval, dict) or approval.get("status") != "approved":
        return {"state": "unapproved", "approval": approval, "sha256": digest}
    state = "approved" if digest == approval.get("sha256") else "hash-mismatch"
    return {"state": state, "approval": approval, "sha256": digest}


def ui_contracts(rdir: Path, project: str, task_states: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Project UI subplans with their design-task state and per-version approval."""
    try:
        plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return []
    if not isinstance(plan, dict) or not isinstance(plan.get("subplans"), list):
        return []
    if task_states is None:
        import bt_planstatus
        status = bt_planstatus.plan_status(project, Path(rdir))
        task_states = {task["id"]: task.get("state") for milestone in status["milestones"]
                       for task in milestone["tasks"]}
    saved = approvals(rdir)
    rows = []
    for subplan in plan["subplans"]:
        ui = subplan.get("ui") if isinstance(subplan, dict) else None
        if not isinstance(ui, dict) or not isinstance(ui.get("contract"), str) or type(ui.get("version")) is not int:
            continue
        ref = f"{ui['contract']}@v{ui['version']}"
        design_task = ui.get("design_task")
        record = saved.get(ref)
        rows.append({"subplan_id": subplan.get("id"), "title": subplan.get("title", ""), "contract": ref,
                     "path": contract_path(ref), "design_task": design_task,
                     "design_state": task_states.get(design_task, "pending"),
                     "approval": record if isinstance(record, dict) else None})
    return rows


def repository_for_contract(root: Path, project: str, rdir: Path, ref: str) -> Path | None:
    """Resolve the repository role assigned to this version's design task."""
    plan = json.loads((Path(rdir) / "PLAN.json").read_text(encoding="utf-8"))
    contract, version = parse_ref(ref)
    subplan = next((item for item in plan.get("subplans", []) if isinstance(item, dict) and
                    isinstance(item.get("ui"), dict) and item["ui"].get("contract") == contract and
                    item["ui"].get("version") == version), None)
    if subplan is None:
        return None
    task = next((item for item in plan.get("tasks", []) if isinstance(item, dict) and
                 item.get("id") == subplan["ui"].get("design_task")), {})
    from bt_workspace import repos
    workspaces = repos(Path(root), project)
    role = task.get("repository") or next(iter(workspaces), "")
    return workspaces.get(role)


def approve_planning_draft(rdir: Path, ref: str, blob: bytes, draft: str, who: str = "owner") -> dict[str, Any]:
    """Record the owner's plan approval of a planning-time draft; the run copies those exact bytes into the repo."""
    path = contract_path(ref)
    digest = hashlib.sha256(blob).hexdigest()
    with _decision_lock(Path(rdir)):
        data = _load(rdir)
        prior = data["approvals"].get(ref)
        if isinstance(prior, dict) and prior.get("status") == "approved":
            if prior.get("sha256") == digest:
                return prior
            raise DesignApprovalError(f"{ref} is already approved with another SHA256; approvals are immutable")
        record = {"contract": ref, "path": path, "status": "approved", "sha256": digest, "who": who, "via": "plan",
                  "when": datetime.now(UTC).isoformat(timespec="seconds"), "comments": "approved with the plan",
                  "draft": draft}
        data["approvals"][ref] = record
        _write(rdir, data)
        return record
