"""Version-gated recovery decisions for checkpointed task histories."""
from __future__ import annotations

from bt_contracts.failure import Budget, FailureReport, RecoveryDecision, Spent
from dbos import DBOS

from ..control import policy

PATCH_INTERRUPTED_REVERIFY = "bt-task-interrupted-reverify"


def decide(failure: FailureReport, used: Spent, budget: Budget, *, now: float, other_route: bool,
           reset_epoch: float | None = None, remediated: bool = False) -> RecoveryDecision:
    # An old history already escalated this interruption. Its next step must stay the owner wait; only a
    # history that records the patch may insert the existing bounded same-snapshot verification branch.
    interrupted_reverify = failure.code != "ENGINE_INTERRUPTED" or DBOS.patch(PATCH_INTERRUPTED_REVERIFY)
    return policy.decide(failure, used, budget, now=now, other_route=other_route, reset_epoch=reset_epoch,
                         remediated=remediated, interrupted_reverify=interrupted_reverify)
