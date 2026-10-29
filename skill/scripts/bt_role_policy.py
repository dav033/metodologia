"""Owner-selected role models; quota ranking and account selection live in the router.

Options are preferences, not an escalation ladder. An explicit complexity label
changes selected roles; Implementer keeps Sonnet first when complex, Luna is the quota fallback.
Errors, risk, and inferred task difficulty do not change the options.
"""
from __future__ import annotations

ROLES = ("planner", "reviewer", "designer", "explorer", "implementer", "researcher", "runner", "antagonist")

_KINDS = {"implement": "implementer", "test": "runner", "audit": "reviewer", "research": "researcher",
          "design": "designer"}
_DEFAULTS = {
    "planner": (("codex", "gpt-6.1-sol", "high"), ("claude", "opus", "high")),   # planning: high, never xhigh by default
    "reviewer": (("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")),
    # owner 2026-10-29 (D-151): Opus 5.5 high first, kept while its account has quota; Codex Terra high only when not
    "designer": (("claude", "opus", "high"), ("codex", "gpt-6.1-terra", "high")),
    "explorer": (("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "medium")),
    "implementer": (("claude", "sonnet", "medium"), ("codex", "gpt-6-luna", "high")),
    "researcher": (("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "low")),
    "runner": (("codex", "gpt-6-luna", "high"), ("claude", "sonnet", "low")),
    "antagonist": (("claude", "sonnet", "medium"), ("claude", "opus", "high")),
}
_HIGH = {
    "planner": tuple(reversed(_DEFAULTS["planner"])),
    "implementer": _DEFAULTS["implementer"],
    "reviewer": (("codex", "gpt-6.1-sol", "high"), ("claude", "sonnet", "high")),
    "designer": _DEFAULTS["designer"],
    "explorer": (("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")),
    "researcher": tuple(reversed(_DEFAULTS["researcher"])),
    "runner": tuple(reversed(_DEFAULTS["runner"])),
    "antagonist": tuple(reversed(_DEFAULTS["antagonist"])),
}


# Roles whose owner order holds whenever the first choice's account has quota (below HIGH_PRESSURE and not blocked):
# the router then ranks by preference, not by which subscription has more headroom (D-151).
ORDERED_ROLES = frozenset({"designer"})


def high_complexity(complexity: str | None) -> bool:
    """Recognize only explicit supported high-complexity labels."""
    return isinstance(complexity, str) and complexity.strip().lower() in {"l", "high", "high_complexity"}


def role_for_kind(kind: str | None) -> str | None:
    """Map runtime task kinds to roles; docs retain their existing routing."""
    return _KINDS.get(kind)


def role_for_task(kind: str | None, review_axis: object = None) -> str | None:
    """Resolve the M2 role, including the optional visual-review task classification."""
    if kind == "audit" and review_axis == "visual":
        return "reviewer"
    return role_for_kind(kind)


# The one exception to "risk never changes the options": an audit that the plan or the run already escalated (high risk or
# architecture level reaches the audit as tier 2) is read by the strongest reviewer of each provider, at high.
_ESCALATED_AUDIT = (("codex", "gpt-6.1-sol", "high"), ("claude", "opus", "high"))
ESCALATED_AUDIT_TIER = 2


def escalated_audit(kind: str | None, tier: int | None) -> bool:
    return kind == "audit" and isinstance(tier, int) and not isinstance(tier, bool) and tier >= ESCALATED_AUDIT_TIER


def options(role: str | None, complexity: str | None = None, *, escalated: bool = False) -> list[tuple[str, str, str]]:
    """Return fresh, ordered allowed choices; unknown roles have no choices. `escalated` (see `escalated_audit`) only
    changes the reviewer role."""
    if escalated and role == "reviewer":
        return list(_ESCALATED_AUDIT)
    table = _HIGH if high_complexity(complexity) else {}
    return list(table.get(role, _DEFAULTS.get(role, ())))


def native_option(role: str | None, provider: str) -> tuple[str, str] | None:
    """Return the ordinary preferred model and effort for a provider, if allowed."""
    return next(((model, effort) for family, model, effort in options(role) if family == provider), None)
