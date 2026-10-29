"""Cross-task interface validation extension for PLAN.json schema 1.2.0."""
from __future__ import annotations

import re
from collections.abc import Mapping

from . import evidence as ev

_INTERFACE_ID_RE = re.compile(r"IF-[1-9][0-9]*")
_TEXT_LIST_FIELDS = ("inputs", "outputs", "invariants", "integration_criteria")


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _interface_text_findings(where: str, interface: dict) -> list[str]:
    findings: list[str] = []
    fields: list[tuple[str, object]] = [("title", interface.get("title")), ("owner", interface.get("owner"))]
    for field in _TEXT_LIST_FIELDS:
        values = interface.get(field)
        if isinstance(values, list):
            fields.extend((f"{field}[{index}]", value) for index, value in enumerate(values))
    for field, value in fields:
        if isinstance(value, str):
            match = ev.PARALLEL_CLAIM_RE.search(value)
            if match:
                findings.append(f"{where}.{field}: {match.group(0)!r} promises parallel safety; interface text cannot "
                                "make scheduling guarantees")
    return findings


def check(plan: object, ancestors: Mapping[str, set[str]]) -> tuple[list[str], list[str]]:
    """Validate declared cross-task interfaces using the plan's transitive dependency map."""
    if not isinstance(plan, dict):
        return [], []

    errors: list[str] = []
    warnings: list[str] = []
    task_items = plan.get("tasks")
    task_ids = {task["id"] for task in task_items if isinstance(task, dict) and isinstance(task.get("id"), str)} \
        if isinstance(task_items, list) else set()
    interfaces = plan.get("interfaces", [])
    if not isinstance(interfaces, list):
        return ["interfaces: must be a list when provided"], warnings

    task_subplan = {task["id"]: task.get("subplan_id") for task in task_items
                    if isinstance(task, dict) and isinstance(task.get("id"), str)} if isinstance(task_items, list) else {}
    subplan_ids = {item.get("id") for item in plan.get("subplans") or [] if isinstance(item, dict)}
    gate_tasks = {gate.get("task") for gate in plan.get("composition_gates") or [] if isinstance(gate, dict)}
    seen_ids: set[str] = set()
    for index, interface in enumerate(interfaces):
        where = f"interfaces[{index}]"
        if not isinstance(interface, dict):
            errors.append(f"{where}: must be an object")
            continue

        interface_id = interface.get("id")
        if not isinstance(interface_id, str) or _INTERFACE_ID_RE.fullmatch(interface_id) is None:
            errors.append(f"{where}.id: {interface_id!r} must look like IF-1")
        elif interface_id in seen_ids:
            errors.append(f"{where}.id: duplicate interface ID {interface_id}")
        else:
            seen_ids.add(interface_id)

        for field in ("title", "owner"):
            if not _nonempty_text(interface.get(field)):
                errors.append(f"{where}.{field}: required non-empty text")
        for field in _TEXT_LIST_FIELDS:
            values = interface.get(field)
            if not isinstance(values, list) or not values:
                errors.append(f"{where}.{field}: must be a non-empty list of text")
                continue
            for item_index, value in enumerate(values):
                if not _nonempty_text(value):
                    errors.append(f"{where}.{field}[{item_index}]: required non-empty text")

        errors.extend(_interface_text_findings(where, interface))

        producer = interface.get("producer_task")
        producer_valid = isinstance(producer, str) and producer in task_ids
        if not isinstance(producer, str) or not producer:
            errors.append(f"{where}.producer_task: required task ID")
        elif producer not in task_ids:
            errors.append(f"{where}.producer_task: task {producer!r} does not exist")

        consumers = interface.get("consumer_tasks")
        if not isinstance(consumers, list) or not consumers:
            errors.append(f"{where}.consumer_tasks: must be a non-empty list of task IDs")
            consumers = []
        valid_consumers: list[tuple[int, str]] = []
        seen_consumers: set[str] = set()
        for consumer_index, consumer in enumerate(consumers):
            if not isinstance(consumer, str) or not consumer:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: required task ID")
                continue
            if consumer in seen_consumers:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: duplicate task {consumer}")
                continue
            seen_consumers.add(consumer)
            if consumer not in task_ids:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: task {consumer!r} does not exist")
                continue
            valid_consumers.append((consumer_index, consumer))
            if producer == consumer:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: producer and consumer must differ")

        integration_present = "integration_task" in interface
        integration = interface.get("integration_task")
        integration_valid = False
        if integration_present:
            if not isinstance(integration, str) or not integration:
                errors.append(f"{where}.integration_task: must be a task ID when provided")
            elif integration not in task_ids:
                errors.append(f"{where}.integration_task: task {integration!r} does not exist")
            elif integration in seen_consumers:
                errors.append(f"{where}.integration_task: cannot be one of the consumer tasks")
            else:
                integration_valid = True

        for consumer_index, consumer in valid_consumers:
            if consumer == producer or not producer_valid:
                continue
            prerequisites = ancestors.get(consumer, set())
            if producer in prerequisites:
                continue
            if not integration_present:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: producer {producer} is not an ancestor and "
                              "integration_task is required")
                continue
            if not integration_valid:
                errors.append(f"{where}.consumer_tasks[{consumer_index}]: producer {producer} is not an ancestor and "
                              "integration_task is invalid")
                continue
            integration_ancestors = ancestors.get(integration, set())
            if producer not in integration_ancestors or consumer not in integration_ancestors:
                missing = [task_id for task_id in (producer, consumer) if task_id not in integration_ancestors]
                errors.append(f"{where}.integration_task: {integration} must depend on producer and unordered consumer "
                              f"{', '.join(missing)}")

        errors.extend(_foreign_consumers(where, interface, valid_consumers, ancestors, task_subplan, subplan_ids,
                                         gate_tasks, integration if integration_valid else None))

    return errors, warnings


def _foreign_consumers(where: str, interface: dict, consumers: list[tuple[int, str]], ancestors: Mapping[str, set[str]],
                       task_subplan: Mapping[str, object], subplan_ids: set, gate_tasks: set,
                       integration: str | None) -> list[str]:
    """A consumer in another subplan than the interface's owner relies on the behaviour the owner proves end to end at
    the interface's integration task, not only on the producer's contract: it must depend on that task (D-165). pictures
    REQ-021 T7.4 asserted that every call lands in the usage ledger (IF-3, owner SP-6); it depended on the table's
    producer T6.2 but not on T6.3/T6.5, which wire and prove the capture, and failed four attempts on a line without it.
    An integration task that is a composition gate task composes its consumers itself and is left out."""
    owner = interface.get("owner")
    if integration is None or owner not in subplan_ids or integration in gate_tasks:
        return []
    found = []
    for consumer_index, consumer in consumers:
        home = task_subplan.get(consumer)
        if home in (None, owner) or consumer in gate_tasks or integration in ancestors.get(consumer, set()):
            continue
        found.append(f"{where}.consumer_tasks[{consumer_index}]: {consumer} ({home}) relies on {interface.get('id')} of "
                     f"{owner}; it must depend on {integration}, the task that proves it end to end, or on a composition "
                     "gate after it")
    return found


def report(plan: object) -> list[dict[str, object]]:
    """Project declared interface contracts without presenting them as completed integration evidence."""
    if not isinstance(plan, dict) or not isinstance(plan.get("interfaces"), list):
        return []
    fields = ("id", "title", "owner", "producer_task", "consumer_tasks", "integration_task", "inputs", "outputs",
              "invariants", "integration_criteria")
    return [{key: interface[key] for key in fields if key in interface}
            for interface in plan["interfaces"] if isinstance(interface, dict)]
