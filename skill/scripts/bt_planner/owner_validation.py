"""Pure composition constraints shared with the runtime owner."""
from __future__ import annotations

from collections.abc import Mapping, Sequence


def validate_owner_composition(subplans: Sequence[Mapping], gates: Sequence[Mapping],
                               tasks: Sequence[Mapping]) -> tuple[str, ...]:
    errors: list[str] = []
    order = [item.get("id") for item in subplans]
    previous: tuple[str, ...] = ()
    for gate in gates:
        raw_members = gate.get("subplans", ())
        if not isinstance(raw_members, (list, tuple)) or any(not isinstance(item, str) for item in raw_members):
            errors.append("OWNER_COMPOSITION_GATE_CHAIN_UNSUPPORTED")
            break
        members = tuple(raw_members)
        member_set = set(members)
        expected = tuple(item for item in order if item in member_set)
        if not members or members != expected or members[:len(previous)] != previous or len(members) <= len(previous):
            errors.append("OWNER_COMPOSITION_GATE_CHAIN_UNSUPPORTED")
            break
        previous = members
    by_id = {task.get("id"): task for task in tasks}
    repositories = {task.get("repository") for task in tasks if isinstance(task.get("repository"), str)}
    if subplans and len(repositories) > 1:
        errors.append("OWNER_COMPOSITION_SINGLE_REPOSITORY_REQUIRED")
    for subplan in subplans:
        contracts = subplan.get("produces", ())
        if not isinstance(contracts, (list, tuple)):
            continue
        for contract in contracts:
            if not isinstance(contract, Mapping):
                continue
            producer = by_id.get(contract.get("defined_by")) if isinstance(contract, Mapping) else None
            raw_paths = producer.get("expected_paths", ()) if producer else ()
            paths = tuple(raw_paths) if isinstance(raw_paths, (list, tuple)) else ()
            ui = subplan.get("ui")
            if (isinstance(ui, Mapping) and isinstance(contract, Mapping) and
                    contract.get("contract") == ui.get("contract") and
                    isinstance(ui.get("contract"), str) and type(ui.get("version")) is int):
                paths = (f"design/contracts/{ui['contract']}@v{ui['version']}.md",)
            if not paths or any(not _exact_file_path(path) for path in paths):
                errors.append(f"OWNER_COMPOSITION_DEFINED_BY_PATHS_NOT_EXACT_FILES:{subplan.get('id')}:{contract.get('contract', '')}")
    return tuple(errors)


def _exact_file_path(path: object) -> bool:
    if not isinstance(path, str) or not path or path.startswith("/") or path.endswith("/"):
        return False
    if any(char in path for char in "*?[]") or "\\" in path or "\x00" in path:
        return False
    return all(part not in {"", ".", ".."} for part in path.split("/"))
