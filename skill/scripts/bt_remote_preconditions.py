"""Precondition readers for ephemeral owner decisions and planning rounds."""
from __future__ import annotations

from pathlib import Path


def planning_target_state(rdir: Path, command: str | None, params: dict | None) -> dict | None:
    """Return the live state of the decision or round a command will consume."""
    values = params or {}
    if command == "answer-decision":
        request_id = values.get("request_id")
        if not isinstance(request_id, str) or not request_id:
            return None
        import bt_scheduler_decisions as decisions

        request = next((item for item in decisions.open_requests(rdir) if item.get("id") == request_id), None)
        if request is None:
            return {"state": "closed"}
        current = {"state": request.get("state") or "open"}
        if isinstance(request.get("revision"), int):
            current["revision"] = request["revision"]
        return current
    if command == "answer-round":
        round_number = values.get("round")
        if not isinstance(round_number, int) or isinstance(round_number, bool) or round_number < 1:
            return None
        import bt_rounds

        try:
            round_data = bt_rounds.load(rdir / "rounds" / f"round-{round_number:02d}.json")
        except (OSError, ValueError):
            return None
        if round_data.get("status") != "open" or round_data.get("round") != round_number:
            return None
        current = {"state": round_data["status"]}
        if isinstance(round_data.get("revision"), int):
            current["revision"] = round_data["revision"]
        return current
    return None
