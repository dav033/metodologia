"""bt_scheduler_executor — M3, the agent executor of the Scheduler. See README.md."""
from __future__ import annotations

from .config import Config
from .errors import CODES, ExecutorError
from .executor import AgentExecutor
from .model import (
                    CAUSES,
                    EVENT_KINDS,
                    AttemptStatus,
                    Brief,
                    Classification,
                    Launch,
                    Receipt,
                    Route,
                    StartRequest,
                    TechnicalEvent,
                    Workspace,
)
from .ports import AgentDriver, BriefSource, EventSink, RouteResolver, WorkspaceManager
from .workspace import GitWorkspaces

CONTRACT_VERSION = "1.0.0"
# 1.3.0: subplan integration lines, the Designer base-tree gate and the composition_base seam (accepted F4-5).
PLAN_SCHEMA_CAPABILITIES = frozenset({"1.0.0", "1.1.0", "1.2.0", "1.3.0"})

__all__ = ["AgentDriver", "AgentExecutor", "AttemptStatus", "Brief", "BriefSource", "CAUSES", "CODES",
           "CONTRACT_VERSION", "Classification", "PLAN_SCHEMA_CAPABILITIES", "Config", "EVENT_KINDS", "EventSink", "ExecutorError", "GitWorkspaces",
           "Launch", "Receipt", "Route", "RouteResolver", "StartRequest", "TechnicalEvent", "Workspace",
           "WorkspaceManager"]
