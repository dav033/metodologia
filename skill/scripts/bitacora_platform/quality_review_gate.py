"""Apply a negative audit finding without treating missing manual evidence as a pass."""
from __future__ import annotations

from collections.abc import Mapping

from bt_scheduler_quality.contracts import QualityError, VerifyRequest

VERIFIER = "m6-audit-gate"


def advance(port) -> None:
    for review in port.store.list_reviews():
        result = port.store.get_result(review["request_key"])
        if not isinstance(result, Mapping) or result.get("status") != "NEEDS_REVIEW":
            continue
        identity = result.get("identity", {})
        plan = port.core.plan
        if identity.get("plan_id") != plan.plan_id or identity.get("revision") != plan.revision:
            continue
        task_id, attempt_id = identity.get("task_id"), identity.get("attempt_id")
        if task_id not in plan.ids() or plan.task(task_id).meta.get("kind") != "audit":
            continue
        token = identity.get("token")
        live = port.core.read(lambda ctx, aid=attempt_id, tid=task_id, token=token: bool((attempt := ctx.state.attempts.get(aid))
            and attempt.task_id == tid and attempt.token == token
            and attempt.state in ("verifying", "uncertain")))
        if not live:
            continue
        task = plan.task(task_id)
        order = VerifyRequest.from_mapping({"idempotency_key": review["request_key"], **identity,
            "acceptance_criteria": list(task.acceptance_criteria), "verification": list(task.verification)})
        if order.input_hash != result.get("input", {}).get("order_sha256"):
            continue
        key = (review["request_key"], result.get("evidence_manifest"))
        with port._active_lock:
            if key in port._audit_review_seen:
                continue
            port._audit_review_seen.add(key)
        try:
            gate = port._audit_gate(order, evaluate_gate=True, check_status="NEEDS_REVIEW")
            if gate is not None and not gate.ok:
                reason = (f"Engine audit gate found {len(gate.blocking)} blocking findings and {len(gate.problems)} contract problems; "
                          "missing manual evidence is still unaccepted.")
                port.store.resolve_review(review["request_key"], VERIFIER, "FAIL", reason)
        except QualityError as error:
            if error.code not in {"REVIEW_ALREADY_RESOLVED", "REVIEW_NOT_FOUND"}:
                with port._active_lock:
                    port._audit_review_seen.discard(key)
                raise
        except Exception:
            with port._active_lock:
                port._audit_review_seen.discard(key)
            raise
