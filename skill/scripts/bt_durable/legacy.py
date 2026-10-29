"""The durable runtime's one door to the legacy core, executor and decision packages (their boundary rule: only
`bt_scheduler_adapter` reaches `bt_scheduler_core`, only `bt_scheduler_executor_adapter` reaches the executor, only
`bt_scheduler_decision_adapter` reaches the M2 decision engine).

What is reused through here is domain logic the M0 matrix keeps: plan loading and validation, resource claims,
the brief/prompt/workspace/handoff pieces of the executor, M2's route ranking, and the notes the legacy owner
puts in a brief (owner indications, audit findings, attempt history, failure analysis, last verification failure,
design contract)."""
from __future__ import annotations

import bt_attempt_history as _history
import bt_attestation as _attestation
import bt_composition_adapter as _composition
import bt_config as _config
import bt_design_approval as _design_approval
import bt_design_drafts as _design_drafts
import bt_integration_line as _line
import bt_scheduler_adapter as _sched
import bt_scheduler_decision_adapter as _m2
import bt_scheduler_decisions as _decisions
import bt_scheduler_executor_adapter as _exec
import bt_scheduler_executor_wiring as _wiring

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

# the brief's notes, exactly as the legacy owner composes them (bt_scheduler_executor_wiring)
owner_notes = _wiring.owner_notes
contract_notes = _wiring.contract_notes
joined_notes = _wiring.joined_notes
check_design_approval = _design_approval.check_tree
design_execution_notes = _design_drafts.execution_notes
legacy_attempts_doc = _decisions._state                  # the M1 document of a legacy (or migrated) run
with_recorded_history = _history.with_recorded
record_history = _history.record
write_verify_notes = _decisions.write_verify_notes

# coordinator receipts for manual checks, exactly as the legacy owner hands them to M6 (bt_attestation)
manual_checks = _attestation.manual_checks
mint_attestation = _attestation.mint


def attestations(rdir):
    return _attestation.lookup(rdir, bind_attempt=_config.get("gates.attestation_bind_attempt", True) is True)

# plan 1.3.0 subplans and composition gates: scopes as the legacy subplan lines define them, candidates built by the
# composition engine through its one methodology door (bt_composition_adapter)
scoped_task_ids = _line.scoped_task_ids
create_composition_engine = _composition.create_engine

decision = _m2                      # durable_route_ranking: M2's ranking of the durable runtime's allowed routes
