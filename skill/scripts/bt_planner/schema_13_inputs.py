"""Normalize graph-bearing schema 1.3 fields before semantic traversal."""
from __future__ import annotations


def graph_inputs(plan: dict) -> tuple[dict, list[str]]:
    """Return a bounded graph view and diagnostics for malformed graph containers."""
    normalized = dict(plan)
    errors: list[str] = []
    subplans = plan.get("subplans", [])
    if not isinstance(subplans, list) or len(subplans) > 64:
        errors.append("SUBPLAN_INVALID: subplans: must be a list with at most 64 entries")
        subplans = subplans if isinstance(subplans, list) else []
    safe_subplans = []
    for index, value in enumerate(subplans[:64]):
        if not isinstance(value, dict):
            errors.append(f"SUBPLAN_INVALID: subplans[{index}]: must be an object")
            continue
        subplan = dict(value)
        if not isinstance(subplan.get("id"), str):
            errors.append(f"SUBPLAN_INVALID: subplans[{index}]: id must be unique and match SP-n")
            continue
        for field in ("produces", "consumes", "checkpoints"):
            if field in subplan and not isinstance(subplan[field], list):
                errors.append(f"SUBPLAN_INVALID: {subplan['id']}.{field}: must be a list")
                subplan[field] = []
        if not isinstance(subplan.get("audit_task"), str):
            subplan["audit_task"] = None
        if not isinstance(subplan.get("integration_test_task"), str):
            subplan["integration_test_task"] = None
        subplan["produces"] = [_normalize_producer(item) for item in subplan.get("produces", [])]
        subplan["consumes"] = [_normalize_consumer(item) for item in subplan.get("consumes", [])]
        subplan["checkpoints"] = [_normalize_checkpoint(item) for item in subplan.get("checkpoints", [])]
        if isinstance(subplan.get("ui"), dict):
            ui = dict(subplan["ui"])
            for field in ("design_task", "visual_review_task"):
                if not isinstance(ui.get(field), str):
                    ui[field] = None
            subplan["ui"] = ui
        safe_subplans.append(subplan)
    normalized["subplans"] = safe_subplans

    gates = plan.get("composition_gates", [])
    if not isinstance(gates, list) or len(gates) > 32:
        errors.append("COMPOSITION_INVALID: composition_gates: must be a list with at most 32 entries")
        gates = gates if isinstance(gates, list) else []
    safe_gates = []
    for index, gate in enumerate(gates[:32]):
        if not isinstance(gate, dict):
            errors.append(f"COMPOSITION_INVALID: composition_gates[{index}]: must be an object")
            continue
        safe_gates.append(dict(gate))
    normalized["composition_gates"] = safe_gates
    return normalized, errors


def _normalize_producer(value: object) -> object:
    if not isinstance(value, dict):
        return value
    producer = dict(value)
    if "defined_by" in producer and not isinstance(producer["defined_by"], str):
        producer["defined_by"] = None
    return producer


def _normalize_consumer(value: object) -> object:
    if not isinstance(value, dict):
        return value
    consumer = dict(value)
    if "from" in consumer and not isinstance(consumer["from"], str):
        consumer["from"] = None
    if isinstance(consumer.get("verified_by"), list):
        consumer["verified_by"] = [task_id if isinstance(task_id, str) else None
                                   for task_id in consumer["verified_by"]]
    return consumer


def _normalize_checkpoint(value: object) -> object:
    if not isinstance(value, dict):
        return value
    checkpoint = dict(value)
    if "task" in checkpoint and not isinstance(checkpoint["task"], str):
        checkpoint["task"] = None
    return checkpoint
