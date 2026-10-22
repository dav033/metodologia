"""Scheduler task metadata rules shared by plan loading and dispatch overlays."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

RECOVERY_OWNED_META_KEYS = frozenset({
    "recovery_task", "recovery_case_id", "recovery_owner_tasks", "bootstrap",
})


def effective_task_meta(task_id: str, meta: Any,
                        classification_overlay: Callable[[], dict[str, dict[str, object]]] | None) -> Any:
    """Apply classification amendments without allowing them to replace recovery-owned metadata."""
    if classification_overlay is None or not isinstance(meta, dict):
        return meta
    try:
        changed = classification_overlay().get(task_id) or {}
    except Exception:  # noqa: BLE001 - an unreadable overlay never blocks assignment
        return meta
    if not changed:
        return meta
    amendments = {key: value for key, value in changed.items() if key not in RECOVERY_OWNED_META_KEYS}
    return {**meta, **amendments} if amendments else meta
