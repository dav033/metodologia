"""Runtime settings of the durable engine (REQ-030 M2/M4), validated once at launch.

`execution.backend` in the machine config (`bt_config`) selects `legacy` (default) or `dbos` for NEW runs; the
settings below only apply to runs owned by the DBOS backend.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from bt_contracts.failure import Budget


class Settings(BaseModel):
    """Per-run knobs passed to every workflow (part of the workflow input, so a recovered run keeps its settings)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_parallel: int = Field(default=2, ge=1, le=16)
    poll_seconds: float = Field(default=15.0, ge=0.2, le=600)        # agent process observation interval
    run_poll_seconds: float = Field(default=300.0, ge=1, le=3600)    # how long the run loop waits for news
    owner_wait_seconds: float = Field(default=24 * 3600, ge=1)       # one recv window while a decision is open
    budget: Budget = Field(default_factory=Budget)
    agent_limits: dict = Field(default_factory=lambda: {"memory_max_bytes": 8 << 30, "tasks_max": 4096,
                                                        "runtime_max_seconds": 2 * 3600})
    max_agent_memory_bytes: int = Field(default=16 << 30, ge=1 << 28)   # ceiling for the AGENT_OOM repair


class EngineConfig(BaseModel):
    """Process-level DBOS configuration (not part of any workflow input)."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(default="metodologia", pattern=r"^[a-z0-9_-]{3,64}$")
    system_database_url: str
    executor_id: str = Field(default="local", min_length=1, max_length=64)
    state_dir: Path
    agent_concurrency: int = Field(default=2, ge=1, le=16)          # agents running at once on this machine
    verify_concurrency: int = Field(default=1, ge=1, le=8)          # sandboxed verifications at once
    max_executor_threads: int = Field(default=64, ge=8, le=512)


def default_database_url(state_dir: Path) -> str:
    """SQLite under the state dir unless the operator configured PostgreSQL (`execution.database_url`)."""
    return f"sqlite:///{(state_dir / 'dbos.sqlite3').resolve()}"
