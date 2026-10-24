"""Create-time validation of producer contract paths and composition gate order."""
from __future__ import annotations

from collections.abc import Mapping

from bt_scheduler_owner_errors import CompositionRuntimeError


def validate_contract_paths(plan) -> None:
    task_ids = {getattr(task, "id", None) for task in plan.tasks}
    for subplan in getattr(plan, "subplans", ()):
        for contract in getattr(subplan, "produces", ()):
            producer_id = contract.get("defined_by") if isinstance(contract, Mapping) else None
            producer = plan.task(producer_id) if producer_id in task_ids else None
            paths = tuple(producer.expected_paths) if producer is not None else ()
            if subplan.ui is not None and contract.get("contract") == subplan.ui.contract:
                paths = (f"design/contracts/{subplan.ui.contract}@v{subplan.ui.version}.md",)
            if not paths or any(not _exact_file_path(path) for path in paths):
                raise CompositionRuntimeError(
                    f"OWNER_COMPOSITION_DEFINED_BY_PATHS_NOT_EXACT_FILES: {subplan.id}:{contract.get('contract', '')}")


def _exact_file_path(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or path.endswith("/"):
        return False
    if any(char in path for char in "*?[]") or "\\" in path or "\x00" in path:
        return False
    return all(part not in {"", ".", ".."} for part in path.split("/"))


def validate_gate_chain(plan) -> None:
    gates = getattr(plan, "composition_gates", ())
    if not gates:
        return
    order = [subplan.id for subplan in plan.subplans]
    previous: tuple[str, ...] = ()
    for gate in gates:
        members = tuple(gate.subplans)
        expected = tuple(item for item in order if item in set(members))
        if (not members or members != expected or members[:len(previous)] != previous
                or len(members) <= len(previous)):
            raise CompositionRuntimeError("OWNER_COMPOSITION_GATE_CHAIN_UNSUPPORTED")
        previous = members
