"""One rule for how much adversarial review a supervised task gets before a commit.

With the independent milestone audit active, that audit is the milestone's adversarial review: per-commit Antagonist
passes would repeat it at the price of an extra top-tier session per commit. Tests, linters, the task's `verify` and
the security rules stay mandatory either way. Without a milestone audit the per-commit gate is the only review left and
stays on. Both prompt builders (legacy `_rules` and the orchestrator package) take their wording from here, so the two
paths cannot drift apart. Reference: references/subagents.md §The antagonist gate.
"""
from __future__ import annotations

GATE = ("Follow references/engineering.md of the `metodologia` skill and run the antagonist review "
        "(references/subagents.md) before EVERY commit.")
WITH_AUDIT = ("Follow references/engineering.md of the `metodologia` skill. Run the task's verify, tests and linters "
              "before every commit. Do NOT run the antagonist per commit: the independent milestone audit reviews "
              "the consolidated milestone diff at the end. Invoking the antagonist subagent (Opus / Codex High) "
              "on individual commits is forbidden while this audit covers the work, including high-risk and "
              "architecture tasks. Keep all security checks mandatory.")


def milestone_audit_active(state: dict | None, unit: list[dict] | None = None) -> bool:
    """True when an independent audit of the unit's own milestone is still to run (todo or in progress). Without a
    unit: any pending audit. A task outside a milestone is never audited, so it keeps the per-commit gate."""
    milestones = {t.get("milestone") for t in unit or ()}
    if unit is not None and (not milestones or None in milestones):
        return False
    return any(t.get("synthetic") and t.get("kind") == "audit" and t.get("status") in ("todo", "in_progress")
               and (not milestones or t.get("milestone") in milestones)
               for t in (state or {}).get("tasks", []))


def commit_review_rule(state: dict | None, unit: list[dict] | None = None) -> str:
    """The prompt line that tells a builder how much review to run before a commit."""
    if not milestone_audit_active(state, unit if unit else None):
        return GATE
    return WITH_AUDIT
