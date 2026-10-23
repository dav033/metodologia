"""Publish structural conflict evidence or preserve a known plain rejection."""
from __future__ import annotations

import re

from bt_scheduler_recovery.conflict_delivery import EvidenceUnavailable


def publish(recovery, plan, order, clash: str, refusal: str, detail: str) -> str | None:
    if recovery is None:
        return None      # structural recovery is off: the plain refusal text is the evidence, the task goes back as before
    match = re.search(r"conflict evidence: (conflict:[0-9a-f]{64})", clash)
    if match is None and " vs line for " in clash:
        return None      # a clash found by the integration line has no M5 observation: the plain text goes back with the task
    if match is None:
        raise EvidenceUnavailable("evidence_unavailable: M5 did not retain full conflict evidence")
    observation = recovery.read_conflict_observation(match.group(1))
    if observation is None:
        raise EvidenceUnavailable("evidence_unavailable: M5 conflict evidence is missing or invalid")
    identity = (observation.get("plan_id"), observation.get("revision"), observation.get("task_id"),
                observation.get("attempt_id"), observation.get("plan_sha256"))
    expected = (order.plan_id, order.revision, order.task_id, order.attempt_id, plan.sha256)
    if identity != expected or observation.get("ordinary_rework_refusal_detail") != detail:
        raise EvidenceUnavailable("evidence_unavailable: M6 conflict evidence identity is stale")
    return match.group(1)
