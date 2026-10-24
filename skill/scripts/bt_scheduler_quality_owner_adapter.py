"""Validated M6 adapter API used by the owner runtime and M5 recovery wiring."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import bt_audit_gate

MAX_AUDIT_LEDGERS = 64


def evaluate_audit_ledgers(raw_ledgers, plan_task_ids, audit_task_id: str,
                           policy: bt_audit_gate.Policy | None = None) -> bt_audit_gate.Gate:
    """Combine independent ledgers; matching fingerprints retain all evidence and distinct defects."""
    if not isinstance(raw_ledgers, (tuple, list)) or not 1 <= len(raw_ledgers) <= MAX_AUDIT_LEDGERS:
        return bt_audit_gate.Gate(False, ("audit ledgers are malformed or exceed the bounded input count",), (), ())
    for raw in raw_ledgers:
        if raw is None:
            continue
        if not isinstance(raw, (bytes, str)):
            return bt_audit_gate.Gate(False, ("audit ledger is not text or bytes",), (), ())
        try:
            size = len(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
        except UnicodeEncodeError:
            size = bt_audit_gate.MAX_BYTES + 1
        if size > bt_audit_gate.MAX_BYTES:
            return bt_audit_gate.Gate(False, ("audit ledger exceeds the bounded input size",), (), ())
    if (not isinstance(audit_task_id, str) or not audit_task_id
            or not isinstance(plan_task_ids, (tuple, list))
            or any(not isinstance(task_id, str) or not task_id for task_id in plan_task_ids)):
        return bt_audit_gate.Gate(False, ("audit task identity is malformed",), (), ())
    return bt_audit_gate.evaluate_many(raw_ledgers, plan_task_ids, audit_task_id, policy or bt_audit_gate.Policy())


def combined_audit_ledger(raw_ledgers: tuple[bytes | str | None, ...]) -> bytes | None:
    """Canonical observation payload retaining all finding and evidence fields."""
    findings = []
    for raw in raw_ledgers:
        if raw is None:
            return None
        try:
            data = json.loads(raw.decode("utf-8") if isinstance(raw, bytes) else raw)
        except (UnicodeDecodeError, ValueError):
            return None
        if not isinstance(data, Mapping) or not isinstance(data.get("findings"), list):
            return None
        findings.extend(data["findings"])
    return json.dumps({"schema": bt_audit_gate.SCHEMA, "findings": findings}, sort_keys=True,
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def read_result_manifest(store_path: Path | str, reference: str) -> bytes | None:
    """Read bounded M6 result evidence through its public store API for the M5 recovery adapter."""
    if not isinstance(reference, str) or not reference.startswith("m6://result/"):
        return None
    from bt_scheduler_quality.store import QualityStore

    store = QualityStore(store_path)
    try:
        encoded = store.get_result_manifest(reference)
        return encoded if isinstance(encoded, bytes) and len(encoded) <= 1024 * 1024 else None
    finally:
        store.close()


def expected_environment_fingerprint(policy, contract_identities: Mapping[str, str],
                                     environment_identity: str) -> str:
    """Reproduce M6's public environment binding for a specific immutable order identity."""
    from bt_scheduler_quality.reuse import bound_environment_fingerprint

    contracts = tuple(sorted(contract_identities.items()))
    return bound_environment_fingerprint(policy, contracts, environment_identity)
