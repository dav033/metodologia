"""Validation for command fields the gateway must check before relaying."""

from __future__ import annotations

import re
from typing import Any

COMMAND_TYPES = frozenset({
    "pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
    "launch", "answer-round", "answer-decision", "cancel-plan", "delete-plan", "edit-brief", "note",
})
CONFIRMATION_REQUIRED_TYPES = frozenset({
    "revise", "approve", "launch", "cancel-plan", "delete-plan",
})
IDEMPOTENCY_KEY = re.compile(r"^[A-Za-z0-9._:-]{16,128}$")
REQ_ID = re.compile(r"^REQ-[0-9]{3,}$")


class CommandValidationError(ValueError):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


def validate_command(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CommandValidationError("INVALID_COMMAND", "Command must be a JSON object")
    command = value
    if command.get("schemaVersion") != 1 or not isinstance(command.get("idempotencyKey"), str) or not IDEMPOTENCY_KEY.fullmatch(command["idempotencyKey"]):
        raise CommandValidationError("INVALID_COMMAND", "Command version or idempotency key is invalid")
    command_type = command.get("type")
    if not isinstance(command_type, str) or command_type not in COMMAND_TYPES:
        raise CommandValidationError("INVALID_COMMAND", "Command type is invalid")
    target = command.get("target")
    precondition = command.get("precondition")
    if (not isinstance(target, dict) or target.get("kind") not in {"run", "attempt", "task", "plan", "round"}
            or not isinstance(target.get("project"), str) or not target["project"]
            or not isinstance(target.get("req"), str) or not REQ_ID.fullmatch(target["req"])
            or not isinstance(precondition, dict) or not isinstance(precondition.get("state"), str)
            or not precondition["state"]):
        raise CommandValidationError("INVALID_COMMAND", "Command target or precondition is invalid")

    if command_type in CONFIRMATION_REQUIRED_TYPES:
        confirmation = command.get("confirmation")
        challenge_id = confirmation.get("challengeId") if isinstance(confirmation, dict) else None
        typed_req = confirmation.get("typedReq") if isinstance(confirmation, dict) else None
        if (not isinstance(challenge_id, str) or not 16 <= len(challenge_id) <= 128
                or not isinstance(typed_req, str) or not REQ_ID.fullmatch(typed_req)):
            raise CommandValidationError("CONFIRMATION_REQUIRED", "A valid confirmation challenge is required", 409)
        if typed_req != target["req"]:
            raise CommandValidationError("CONFIRMATION_REQUIRED", "Confirmation must name the target request", 409)
    return command


def to_laptop_command(command: dict[str, Any], origin: str = "web") -> dict[str, Any]:
    """Translate the public v1 command into the laptop ledger's envelope (`bt_remote_commands.validate`)."""
    target = command["target"]
    params = {key: value for key, value in command.items()
              if key not in {"schemaVersion", "idempotencyKey", "type", "target", "precondition", "confirmation"}}
    # The public dialect is camelCase and sends one `answer`; the laptop ledger reads `request_id` and `answers`.
    if "requestId" in params:
        params["request_id"] = params.pop("requestId")
    if command["type"] == "answer-round" and "answer" in params:
        params["answers"] = params.pop("answer")
    # Keep target qualifiers (task, attempt, round) available to the laptop dispatcher.
    params["target"] = target
    for param, qualifier in (("task", "taskId"), ("attempt", "attemptId")):
        if isinstance(target.get(qualifier), str):
            params.setdefault(param, target[qualifier])
    envelope = {
        "idempotency_key": command["idempotencyKey"],
        "command": command["type"],
        "target": f"{target['project']}/{target['req']}",
        "origin": origin,
        "precondition": command["precondition"],
        "params": params,
    }
    if "confirmation" in command:
        envelope["confirmation"] = command["confirmation"]
    return envelope


def validate_challenge(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise CommandValidationError("INVALID_CHALLENGE", "Challenge must be a JSON object")
    target = value.get("target")
    typed_req = value.get("typedReq")
    if (not isinstance(target, str) or len(target) > 512 or target.count("/") != 1
            or not isinstance(typed_req, str) or not REQ_ID.fullmatch(typed_req)
            or target.rsplit("/", 1)[-1] != typed_req or not target.split("/", 1)[0]):
        raise CommandValidationError("INVALID_CHALLENGE", "Challenge target and typed request are invalid")
    return {"target": target, "typedReq": typed_req}
