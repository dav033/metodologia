"""Durable owner approvals for versioned UI contracts.

The approved digest is SHA256 of `git show HEAD:<contract path>` in the repository assigned to the design task.
The M3 gate compares that digest with the contract blob in the selected base commit.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FILE = "design-approvals.json"
_REF = re.compile(r"(?P<contract>[a-z0-9][a-z0-9-]{0,63})@v(?P<version>[1-9][0-9]{0,5})\Z")
_PATH = re.compile(r"design/contracts/[a-z0-9][a-z0-9-]{0,63}@v[1-9][0-9]{0,5}\.md\Z")


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
           *, revision: str = "HEAD") -> dict[str, Any]:
    path = contract_path(ref)
    data = _load(rdir)
    prior = data["approvals"].get(ref)
    if isinstance(prior, dict) and prior.get("status") == "approved":
        raise DesignApprovalError(f"{ref} is already approved; approvals are immutable")
    blob = _read_blob(Path(repo), revision, path)
    if approve and blob is None:
        raise DesignApprovalError(f"Cannot approve {ref}: {path} is absent from {revision} in {repo}")
    record = {"contract": ref, "path": path, "status": "approved" if approve else "changes-requested",
              "sha256": hashlib.sha256(blob).hexdigest() if blob is not None else None,
              "who": who, "via": via, "when": datetime.now(UTC).isoformat(timespec="seconds"),
              "comments": comments.strip()}
    data["approvals"][ref] = record
    _write(rdir, data)
    return record


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
