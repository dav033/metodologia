"""The durable runtime's one door to the legacy core, executor and decision packages (their boundary rule: only
`bt_scheduler_adapter` reaches `bt_scheduler_core`, only `bt_scheduler_executor_adapter` reaches the executor, only
`bt_scheduler_decision_adapter` reaches the M2 decision engine).

What is reused through here is domain logic the M0 matrix keeps: plan loading and validation, resource claims,
the brief/prompt/workspace/handoff pieces of the executor, and M2's route ranking."""
from __future__ import annotations

import bt_scheduler_adapter as _sched
import bt_scheduler_decision_adapter as _m2
import bt_scheduler_executor_adapter as _exec

core = _sched.core
Plan = core.plan.Plan
TaskSpec = core.plan.TaskSpec
load_plan = core.plan.load_plan
Config = core.config.Config
claims_for = core.resources.claims_for
conflict = core.resources.conflict

m3 = _exec.m3
handoff = m3.handoff
build_prompt = m3.prompt.build_prompt
GitWorkspaces = m3.workspace.GitWorkspaces
MethodologyDriver = _exec.MethodologyDriver
PlanBriefs = _exec.PlanBriefs
repositories = _exec.repositories

decision = _m2                      # durable_route_ranking: M2's ranking of the durable runtime's allowed routes
