"""Validation for command fields the gateway must check before relaying."""

from __future__ import annotations

import re
from typing import Any

COMMAND_TYPES = frozenset({
    "pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
    "launch", "answer-decision", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note",
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
