"""Member-specific precondition state for remote round and decision answers."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def answerable_state(rdir: Path, command: str, params: dict[str, Any]) -> dict[str, Any] | None:
    """Read the open round or decision request that an answer targets."""
    if command == "answer-round":
        import bt_rounds

        number = params.get("round")
        if not isinstance(number, int) or isinstance(number, bool) or number < 1:
            return None
        try:
            data = bt_rounds.load(rdir / "rounds" / f"round-{number:02d}.json")
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("round") != number or data.get("status") != "open":
            return None
        return {"state": "open", "revision": data.get("revision"), "updatedAt": data.get("updated_at")}

    request_id = params.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        return None
    import bt_scheduler_decisions as decisions

    request = next((item for item in decisions.open_requests(rdir) if item.get("id") == request_id), None)
    if request is None:
        return None
    state: dict[str, Any] = {"state": "open"}
    if isinstance(request.get("revision"), int) and not isinstance(request.get("revision"), bool):
        state["revision"] = request["revision"]
    if isinstance(request.get("created_at"), str):
        state["updatedAt"] = request["created_at"]
    return state
