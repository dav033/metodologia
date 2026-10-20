"""Owner-selected role models; quota ranking and account selection live in the router.

Options are preferences, not an escalation ladder. An explicit complexity label
changes selected roles; Implementer keeps Sonnet first when complex, Luna is the quota fallback.
Errors, risk, and inferred task difficulty do not change the options.
"""
from __future__ import annotations

ROLES = ("planner", "reviewer", "explorer", "implementer", "researcher", "runner", "antagonist")

_KINDS = {"implement": "implementer", "test": "runner", "audit": "reviewer", "research": "researcher"}
_DEFAULTS = {
    "planner": (("codex", "gpt-6.1-sol", "high"), ("claude", "opus", "high")),   # planning: high, never xhigh by default
    "reviewer": (("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")),
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
    "explorer": (("codex", "gpt-6.1-sol", "medium"), ("claude", "sonnet", "medium")),
    "researcher": tuple(reversed(_DEFAULTS["researcher"])),
    "runner": tuple(reversed(_DEFAULTS["runner"])),
    "antagonist": tuple(reversed(_DEFAULTS["antagonist"])),
}


def high_complexity(complexity: str | None) -> bool:
    """Recognize only explicit supported high-complexity labels."""
    return isinstance(complexity, str) and complexity.strip().lower() in {"l", "high", "high_complexity"}


def role_for_kind(kind: str | None) -> str | None:
    """Map runtime task kinds to roles; docs retain their existing routing."""
    return _KINDS.get(kind)


def options(role: str | None, complexity: str | None = None) -> list[tuple[str, str, str]]:
    """Return fresh, ordered allowed choices; unknown roles have no choices."""
    table = _HIGH if high_complexity(complexity) else {}
    return list(table.get(role, _DEFAULTS.get(role, ())))


def native_option(role: str | None, provider: str) -> tuple[str, str] | None:
    """Return the ordinary preferred model and effort for a provider, if allowed."""
    return next(((model, effort) for family, model, effort in options(role) if family == provider), None)
