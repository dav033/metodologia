"""Owner commands to the durable runtime (REQ-030 M5/M7): answers to open decisions and run-level commands.

Every command carries the id of what it answers (`request_id` of the open decision) or a unique command id, so a
command sent from a stale screen, or delivered twice, cannot change a newer state: the workflow refuses an answer
whose request id is not the open one and applies a run command id at most once.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .execution import TaskId


class OwnerAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str = Field(min_length=3, max_length=120)
    # reverify: verify the same snapshot again (after the coordinator attested its manual checks); no agent attempt
    action: Literal["retry", "retry_with_note", "retry_other_route", "reverify", "stop"]
    note: str = Field(default="", max_length=6000)
    extra_attempts: int = Field(default=1, ge=1, le=10)
    by: str = Field(default="owner", min_length=1, max_length=80)


class RunCommand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["pause", "resume", "retry_task"]
    request_id: str = Field(min_length=8, max_length=120)
    task_id: TaskId | None = None
    note: str = Field(default="", max_length=6000)
    by: str = Field(default="owner", min_length=1, max_length=80)
