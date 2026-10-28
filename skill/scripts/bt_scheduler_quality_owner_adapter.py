"""Validated M6 adapter API used by the owner runtime and M5 recovery wiring."""
from __future__ import annotations

import json
import re
import logging
from collections.abc import Mapping
from pathlib import Path

import bt_audit_gate
from bt_scheduler_quality.contracts import QualityError

MAX_AUDIT_LEDGERS = 64
LOGGER = logging.getLogger(__name__)


def handoff_needs_review(runtime, request_key: str, identity: Mapping[str, object], result: Mapping[str, object]) -> None:
    """Call the owner supplied M1/M5 bridge and execute M6's bounded same-attempt resume when advised."""
    outcome = runtime.needs_review_handoff(identity, result)
    if outcome == "resumed":
        try:
            runtime.store.retry_m5_transient(request_key)
        except QualityError as error:
            if error.code != "RETRY_EXHAUSTED":
                raise
            runtime.core.block_exhausted_needs_review_resume(identity)
        else:
            runtime._wake.set()


def resume_needs_review_handoffs(runtime) -> int:
    """Replay open durable M6 reviews into M1 after owner restart; M1 holds make this idempotent."""
    if runtime.needs_review_handoff is None:
        return 0
    sent = 0
    for review in runtime.store.list_reviews():
        result = runtime.store.get_result(review["request_key"])
        if not isinstance(result, Mapping) or result.get("status") != "NEEDS_REVIEW":
            continue
        identity = result.get("identity")
        if not isinstance(identity, Mapping):
            continue
        try:
            handoff_needs_review(runtime, review["request_key"], identity, result)
        except Exception as error:  # noqa: BLE001 - durable hold is retried on the next restart
            LOGGER.warning("M1 NEEDS_REVIEW restart handoff remains held (%s)", type(error).__name__)
        else:
            sent += 1
    return sent


def retry_interrupted_reviews(runtime) -> int:
    """Retry only M6 reviews whose sole cause was an owner restart, once per request."""
    retried = 0
    for review in runtime.store.list_reviews():
        try:
            runtime.store.retry_interrupted(review["request_key"], "owner-restart",
                                            "verification interrupted by a restart of the owner; rerun it")
            retried += 1
        except QualityError:
            continue
    return retried


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


def environment_fingerprint_matches(policy, contract_identities: Mapping[str, str],
                                    environment_identity: object, observed: object) -> bool:
    """Compare M6's recorded fingerprint with the value M6 derives from this verification identity."""
    if policy is None or not isinstance(observed, str) or not observed or len(observed) > 128:
        return False
    return (observed == expected_environment_fingerprint(policy, contract_identities, environment_identity)
            or observed in getattr(policy, "accepted_environment_fingerprints", ()))


def verified_result_identity(store, reference: str, *, plan_id: str, revision: int, task_id: str,
                             attempt_id: str, token: int, policy) -> dict[str, str] | None:
    """Validate accepted M6 result identity and return its own tree and environment fingerprint."""
    if not isinstance(reference, str) or not reference.startswith("m6://result/"):
        return None
    raw = store.get_result_manifest(reference)
    if not isinstance(raw, bytes) or len(raw) > 1024 * 1024:
        return None
    try:
        manifest = json.loads(raw)
        request, evidence = manifest["request"], manifest["input"]
        tree, environment = evidence.get("tree_digest"), evidence.get("environment_fingerprint")
        if ((request["plan_id"], request["task_id"], request["attempt_id"], request["token"])
                != (plan_id, task_id, attempt_id, token)
                or type(request["revision"]) is not int or not 1 <= request["revision"] <= revision
                or manifest.get("reason_code") != "PASS"
                or not isinstance(tree, str) or re.fullmatch(r"[0-9a-f]{40,64}", tree) is None
                or not environment_fingerprint_matches(policy, {}, request.get("environment_fingerprint"),
                                                       environment)):
            return None
        return {"tree_digest": tree, "environment": environment}
    except (KeyError, TypeError, ValueError):
        return None
