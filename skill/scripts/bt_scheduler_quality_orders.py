"""Translate approved M1 verification orders to the unchanged M6 contract."""

from collections.abc import Mapping

import bt_scheduler_adapter as scheduler_adapter
from bt_scheduler_quality.contracts import QualityError, VerifyRequest

m1 = scheduler_adapter.core


def _verification_mapping(item: object) -> object:
    if not isinstance(item, Mapping):
        return item
    result = dict(item)
    # Older remediation revisions included a redundant command expectation.
    # Only this exact shape is equivalent to M6's mandatory zero exit status.
    # Retain until those frozen revisions no longer need resume/replay support.
    if result.get("type") == "command" and result.get("expected") == "pass":
        result.pop("expected")
    return result


def order_mapping(order: m1.VerifyOrder) -> dict[str, object]:
    if not isinstance(order, m1.VerifyOrder):
        raise QualityError("ORDER_INVALID", "M1 supplied an invalid VerifyOrder instance")
    return {
        "idempotency_key": order.idempotency_key,
        "plan_id": order.plan_id,
        "revision": order.revision,
        "task_id": order.task_id,
        "attempt_id": order.attempt_id,
        "token": order.token,
        "acceptance_criteria": list(order.acceptance_criteria),
        "verification": [_verification_mapping(item) for item in order.verification],
    }


def to_m1_order(order: VerifyRequest) -> m1.VerifyOrder:
    return m1.VerifyOrder(
        order.idempotency_key, order.plan_id, order.revision, order.task_id,
        order.attempt_id, order.token, order.acceptance_criteria,
        tuple(item.to_dict() for item in order.verification),
    )


def matches_approved_plan(
    core: m1.SchedulerCore, order: m1.VerifyOrder, parsed: VerifyRequest
) -> bool:
    plan = core.plan
    if order.plan_id != plan.plan_id or order.revision != plan.revision:
        return False
    try:
        task = plan.task(order.task_id)
        expected = VerifyRequest.from_mapping({
            **order_mapping(order),
            "acceptance_criteria": list(task.acceptance_criteria),
            "verification": [_verification_mapping(item) for item in task.verification],
        })
    except (QualityError, ValueError, TypeError):
        return False
    return (parsed.acceptance_criteria == expected.acceptance_criteria
            and parsed.verification == expected.verification)
