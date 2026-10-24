"""M3 start gates over frozen 1.3.0 plan metadata and the selected Git tree."""
from __future__ import annotations

import re

from . import gitutil

_CONTRACT = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")


def composition_task(plan, task_id: str) -> bool:
    return plan.schema_version == "1.3.0" and bool(plan.subplans) and not plan.task(task_id).meta.get("subplan_id")


def contract_path(plan, task_id: str) -> str | None:
    task = plan.task(task_id)
    if task.meta.get("ui") is not True:
        return None
    subplan_id = task.meta.get("subplan_id")
    subplan = next((item for item in plan.subplans if item.id == subplan_id), None)
    ui = subplan.ui if subplan else None
    if ui is None or not _CONTRACT.fullmatch(ui.contract) or type(ui.version) is not int:
        return ""  # frozen-plan inconsistency: fail closed at the same gate
    return f"design/contracts/{ui.contract}@v{ui.version}.md"


def has_blob(repo, revision: str, path: str) -> bool:
    """Check the exact contract path as a blob in the selected base commit's tree."""
    if not path or path.startswith("-") or ".." in path.split("/"):
        return False
    resolved = gitutil.run(repo, ["rev-parse", "--verify", "--quiet", "--end-of-options",
                                  f"{revision}^{{commit}}"], check=False)
    if not re.fullmatch(r"[0-9a-f]{40,64}", resolved):
        return False
    entry = gitutil.run(repo, ["ls-tree", "--end-of-options", resolved, "--", path], check=False)
    mode, _, rest = entry.partition(" ")
    # A regular file only: a symlink (120000) is also a blob, but it is link text, not the contract.
    return mode in ("100644", "100755") and rest.startswith("blob ") and "\n" not in entry


def approval_problem(state: str) -> str | None:
    """Map the owner approval read model to a stable blocked-environment reason."""
    if state == "approved":
        return None
    if state == "hash-mismatch":
        return "DESIGN_CONTRACT_HASH_MISMATCH"
    return "DESIGN_CONTRACT_UNAPPROVED"
