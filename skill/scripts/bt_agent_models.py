"""Provider model catalog and selection; re-exported by bt_agents for compatibility."""
from __future__ import annotations

import re
from bt_routing_policy import MAX_KIND_TIER, cap_tier

PROVIDERS = ("claude", "codex", "antigravity")
KINDS = ("implement", "test", "docs", "audit", "research")
TOP = 2
EFFORTS = ("low", "medium", "high", "xhigh", "max")

# rank: the lowest tier the model is a sensible default for. cost: relative weight on its subscription's quota.
MODELS: dict[str, dict] = {
    "gpt-6-astra": {"provider": "codex", "label": "GPT-6 Astra", "rank": 2, "cost": 10,
                    "use": "owner-selected Planner"},
    "haiku": {"provider": "claude", "label": "Haiku 5.5", "rank": 0, "cost": 1,
              "use": "mechanical edits, docs, small well-specified tasks, running and reading tests"},
    "sonnet": {"provider": "claude", "label": "Sonnet 5.5", "rank": 1, "cost": 3,
               "use": "everyday implementation, debugging, reviews"},
    "opus": {"provider": "claude", "label": "Opus 5.5", "rank": 2, "cost": 8,
             "use": "architecture, hard debugging, audits of risky changes"},
    "gpt-6-luna": {"provider": "codex", "label": "GPT-6 Luna", "rank": 0, "cost": 1,
                   "use": "fast subagent work: well-specified modules, tests, docs, exploration"},
    "gpt-6.1-sol": {"provider": "codex", "label": "GPT-6.1 Sol", "rank": 1, "cost": 6,
                    "use": "implementation that needs judgment, independent audits, architecture at xhigh"},
    # Gemini 3.8 Flash (Antigravity CLI, Google AI Pro): the effort is part of the id. Measured 3-6x slower than the
    # others and high effort only costs time (D-004): low is the working level.
    "gemini-3.8-flash-low": {"provider": "antigravity", "label": "Gemini 3.8 Flash low", "rank": 0, "cost": 2,
                             "use": "default AUDITOR (spec/security review, no false positives measured); reserve "
                                    "builder when Claude and Codex are exhausted; not for interactive or urgent work"},
    "gemini-3.8-flash-medium": {"provider": "antigravity", "label": "Gemini 3.8 Flash medium", "rank": 1, "cost": 4,
                                "use": "long-horizon agentic work only (not measured); 2.5x slower than low"},
    "gemini-3.8-flash-high": {"provider": "antigravity", "label": "Gemini 3.8 Flash high", "rank": 2, "cost": 5,
                              "use": "avoid: timed out twice on a task low solved"},
}
# (model, effort) per provider and tier. Codex always gets an explicit effort: an account's config.toml default may
# name a level the model does not support.
LADDER: dict[str, tuple] = {
    # No rung climbs to xhigh by itself: xhigh is an explicit per-task `effort:` choice (bt_routing_policy).
    "claude": (("haiku", None), ("sonnet", "medium"), ("opus", "high")),
    "codex": (("gpt-6-luna", "medium"), ("gpt-6.1-sol", "medium"), ("gpt-6.1-sol", "high")),
    # Flash never goes to `high` automatically: a failure moves the work to another provider instead (router rule).
    "antigravity": (("gemini-3.8-flash-low", None), ("gemini-3.8-flash-low", None), ("gemini-3.8-flash-medium", None)),
}
KIND_TIER = {"audit": 1}  # audits start with the standard budget, independently of the builder's model
AUDIT_LADDER = {
    "claude": (("sonnet", "medium"), ("sonnet", "medium"), ("opus", "high")),
    "codex": (("gpt-6.1-sol", "medium"), ("gpt-6.1-sol", "medium"), ("gpt-6.1-sol", "high")),
    "antigravity": (("gemini-3.8-flash-low", None), ("gemini-3.8-flash-low", None), ("gemini-3.8-flash-medium", None)),
}
_KIND_WORDS = (("audit", ("audit", "review", "revis", "auditor")),
               ("docs", ("docs", "documentation", "readme", "document", "changelog", "skill.md")),
               ("test", ("test", "e2e", "coverage", "prueba")),
               ("research", ("research", "investigate", "compare", "spike")))


def infer_kind(title: str | None, explicit: str | None = None) -> str:
    """The task's kind: the PLAN line's `kind:` when valid, else guessed from the title, else implement."""
    if explicit and explicit.strip().lower() in KINDS:
        return explicit.strip().lower()
    text = (title or "").lower()
    for kind, words in _KIND_WORDS:
        if any(re.search(r"\b" + re.escape(w), text) for w in words):
            return kind
    return "implement"


def start_tier(level: str | None, kind: str | None = None, complexity: str | None = None,
               risk: str | None = None) -> int:
    """Where a task starts on the ladder (policy and reason: bt_routing_policy.start_tier): architecture-level work at
    the top; an audit, work declared large (`complexity: L`) or risky (`risk: high`) at the standard tier or above;
    everything else at the light tier. Docs/test/research remain bounded by MAX_KIND_TIER."""
    import bt_routing_policy
    return bt_routing_policy.start_tier(level, kind, complexity, risk)[0]


def rank_of(model: str | None) -> int:
    name = (model or "").lower()
    if name in MODELS:
        return MODELS[name]["rank"]
    return 2 if "opus" in name else 1 if ("sonnet" in name or "sol" in name) else 0


def provider_of_model(model: str | None) -> str | None:
    name = (model or "").lower()
    if name in MODELS:
        return MODELS[name]["provider"]
    if name.startswith("gemini"):
        return "antigravity"
    if any(w in name for w in ("opus", "sonnet", "haiku", "claude")):
        return "claude"
    return "codex" if name.startswith(("gpt", "codex", "o3", "o4")) else None


def model_for(provider: str, tier: int, configured: str | None = None, kind: str | None = None
              ) -> tuple[str | None, str | None]:
    """(model, effort) of `provider` at `tier`. A configured model of the same provider that is at least as strong as
    the tier's is kept (only the effort follows the ladder). Documentation never needs more than low effort at tier 0."""
    tier = cap_tier(tier, kind)
    if kind in MAX_KIND_TIER:
        configured = None  # pinned models cannot bypass a kind's hard budget
    if kind == "audit":
        # A builder's configured model must not inflate the independent audit's budget.
        return AUDIT_LADDER.get(provider, AUDIT_LADDER["claude"])[tier]
    model, effort = LADDER.get(provider, LADDER["claude"])[tier]
    if configured and provider_of_model(configured) == provider and (tier == 0 or rank_of(configured) >= rank_of(model)):
        model = configured
    if provider == "codex" and tier == 0 and kind == "docs":
        effort = "low"
    return model, effort


def apply_explicit_effort(agent: str, model: str | None, effort: str | None, asked: str | None,
                          kind: str | None = None) -> str | None:
    """The effort that really runs: a task may ask for a stronger one than its tier's (Claude and Codex, never Haiku),
    never a weaker one. Used by the router (so the evidence consulted is the executed effort's) and by the session."""
    if kind in MAX_KIND_TIER or asked not in EFFORTS or agent not in ("claude", "codex") or model == "haiku":
        return effort
    if effort in EFFORTS and EFFORTS.index(effort) >= EFFORTS.index(asked):
        return effort
    return asked


def legacy_model_for(state: dict, tier: int) -> tuple[str | None, str | None]:
    """A run pinned to one agent. Claude: the configured model at tier 0 (haiku by default), the ladder above it.
    Codex: a configured Codex model is kept and only the effort follows the ladder (medium at tier 1, high at tier 2;
    xhigh only when a task asks for it); with no Codex model configured the CLI's own default model runs."""
    agent, configured = state.get("agent") or "claude", state.get("model")
    if agent == "antigravity":
        return (configured if provider_of_model(configured) == "antigravity" else "gemini-3.8-flash-low"), None
    if agent == "codex":
        model = configured if configured and provider_of_model(configured) != "claude" else None
        return model, LADDER["codex"][min(TOP, max(0, tier))][1] if tier >= 1 else None
    if tier <= 0:
        return configured or "haiku", None
    tier = min(tier, TOP)
    ladder = LADDER["claude"][tier]
    return (configured if rank_of(configured) >= tier and provider_of_model(configured) == "claude" else ladder[0]), \
        ladder[1]
