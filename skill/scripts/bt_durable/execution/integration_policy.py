"""Replay-compatible identity for integrating a reverified snapshot."""
from dbos import DBOS

PATCH_REINTEGRATE = "bt-task-reverify-reintegrates"


def workflow_id(attempt_key: str, profile: str) -> str:
    key = f"bt:{attempt_key}:integrate"
    # A completed child also caches conflicts. A new verification needs another integration
    # observation; replay of that verification must still reuse its own child (pictures T2.55).
    if profile != "standard" and DBOS.patch(PATCH_REINTEGRATE):
        return f"{key}:{profile}"
    return key
