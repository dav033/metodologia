"""bt_planner: the planner module of the methodology.

Describes and classifies work as a validated, versioned `PLAN.json` next to a human `PLAN.md`; freezes approved
revisions; never chooses who executes the work and never touches execution state. Standard library only; imports
nothing outside this package (enforced by tests/test_boundaries.py). Public API below; see README.md.
"""
from . import amendments
from .contract import (COMPLEXITY, LATEST_SCHEMA_VERSION, LEVELS, SCHEMA_VERSION, SCOPE, PlanContractError, Report, canonicalize, dumps, load,
                       loads, validate)
from .resources import example_text, schema_text
from .revisions import latest, list_revisions, load_revision, plan_ref, run_reference, verify_store
from .sync import (APPROVED_STATES, PLAN_JSON, approve_freeze, bind_approved, check, compat, consistency, default_plan_id, freeze_if_present,
                   plan_status, skeleton, write_skeleton)

__all__ = ["amendments", "PLAN_JSON", "COMPLEXITY", "LATEST_SCHEMA_VERSION", "LEVELS", "SCHEMA_VERSION", "SCOPE", "APPROVED_STATES", "PlanContractError", "Report",
           "approve_freeze", "bind_approved", "canonicalize", "check", "compat", "consistency", "default_plan_id", "dumps",
           "example_text", "freeze_if_present", "latest", "list_revisions", "load", "load_revision", "loads", "plan_ref",
           "plan_status",
           "run_reference", "schema_text", "skeleton", "validate", "verify_store", "write_skeleton"]
