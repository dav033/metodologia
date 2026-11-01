"""Version-gated recovery decisions for checkpointed task histories."""
from __future__ import annotations

from bt_contracts.failure import Budget, FailureReport, RecoveryDecision, Spent
from dbos import DBOS

from ..control import policy

PATCH_INTERRUPTED_REVERIFY = "bt-task-interrupted-reverify"
# D-269 (pictures REQ-021 r32 T3.91): after an answered decision the attempts are counted from that answer
PATCH_ANSWER_WINDOW = "bt-task-answer-opens-attempt-window"


def decide(failure: FailureReport, used: Spent, budget: Budget, *, now: float, other_route: bool,
           reset_epoch: float | None = None, remediated: bool = False,
           window: tuple[Spent, Budget] | None = None) -> RecoveryDecision:
    # An old history already escalated this interruption. Its next step must stay the owner wait; only a
    # history that records the patch may insert the existing bounded same-snapshot verification branch.
    interrupted_reverify = failure.code != "ENGINE_INTERRUPTED" or DBOS.patch(PATCH_INTERRUPTED_REVERIFY)
    # `window`: what the task spent since its last answered decision and that window's budget (D-269). A history that
    # decided under the whole-task count replays it (the patch returns False where it recorded bt.emit_decision); the
    # patch sits right before that plain step, and is asked only after an answer, which every replay reproduces.
    if window is not None and DBOS.patch(PATCH_ANSWER_WINDOW):
        used, budget = window
    return policy.decide(failure, used, budget, now=now, other_route=other_route, reset_epoch=reset_epoch,
                         remediated=remediated, interrupted_reverify=interrupted_reverify)
