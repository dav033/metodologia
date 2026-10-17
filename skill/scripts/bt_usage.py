"""Canonical token accounting: the one place that says what an attempt's `usage` record means.

Providers do not count the same thing under the same name (checked against what `bt_events.extract_usage` receives):
- Claude `result.usage`: `input_tokens` EXCLUDES cached input; cache reads and cache writes are separate counters, so the
  total is input + output + cache_read + cache_write. Thinking tokens are part of `output_tokens`.
- Codex `turn.completed.usage`: `input_tokens` INCLUDES `cached_input_tokens` (a subset), so the total is
  input + output and the cached count must never be added again. Reasoning is part of `output_tokens`.
- Antigravity: the stream reports a total whose composition is not documented: it is kept as the provider's own total,
  never recombined and never compared across providers.
- A bare total (`quality: total_only`) is a measurement of the whole session, not of its parts.

Rules: a missing counter is None, never 0 (R4); a partial measurement (stream cut before its final event, or a counter
the provider should have sent) keeps its lower-bound total labelled `partial` and is never a final consumption (R5);
an inconsistent record (cache larger than the input it is a subset of, reported total different from the parts) is
`contradictory` and not comparable (R7). Historical rows are only read through `normalize`, never rewritten.
"""
from __future__ import annotations

FIELDS = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "reasoning_tokens")
# stored quality -> what normalize() may conclude from it
COMPLETE, PARTIAL, TOTAL_ONLY, UNKNOWN, CONTRADICTORY = "complete", "partial", "total_only", "unknown", "contradictory"


def _count(value) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def provider_of(agent: str | None, usage: dict) -> str | None:
    """The provider whose convention the record follows: the row's agent, else the usage source."""
    name = (agent or "").lower()
    if name in ("claude", "codex", "antigravity"):
        return name
    source = str(usage.get("source") or "").lower()
    return "claude" if source.startswith("claude") else "codex" if source.startswith("codex") else \
        "antigravity" if source.startswith(("agy", "antigravity")) else None


def normalize(usage: object, agent: str | None = None) -> dict:
    """{parts..., reported_total, total, quality, coverage, comparable, source}. `total` is the normalized consumption
    or None; `comparable` says it means the same thing for every provider (false for provider-specific totals, partial,
    total-only and contradictory records)."""
    usage = usage if isinstance(usage, dict) else {}
    parts = {k: _count(usage.get(k)) for k in FIELDS}
    reported = _count(usage.get("total_tokens"))
    provider = provider_of(agent, usage)
    stored = str(usage.get("quality") or "")
    out = {**parts, "reported_total": reported, "total": None, "quality": UNKNOWN, "coverage": 0.0,
           "comparable": False, "source": usage.get("source"), "provider": provider}
    if provider == "claude":
        needed = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")
        known = [parts[k] for k in needed if parts[k] is not None]
        computed = sum(known) if known else None
    elif provider == "codex":
        needed = ("input_tokens", "output_tokens")
        known = [parts[k] for k in needed if parts[k] is not None]
        computed = sum(known) if known else None
        cache = parts["cache_read_tokens"]
        if cache is not None and parts["input_tokens"] is not None and cache > parts["input_tokens"]:
            return {**out, "quality": CONTRADICTORY, "total": reported}  # a subset cannot exceed its whole
    elif provider is None and parts["input_tokens"] is not None and parts["output_tokens"] is not None:
        # Provider unknown: input + output is all that can be said. With cache counters the convention (subset or
        # extra) is unknown, so the sum is only a lower bound; without them it is complete but not comparable.
        needed = ("input_tokens", "output_tokens")
        known = [parts[k] for k in needed]
        computed = sum(known)
        if parts["cache_read_tokens"] is not None or parts["cache_write_tokens"] is not None:
            return {**out, "quality": PARTIAL, "total": computed, "coverage": 0.5}
        if reported is None:
            return {**out, "quality": COMPLETE, "total": computed, "coverage": 1.0}
    else:  # antigravity: only the provider's own total is meaningful
        needed, known, computed = (), [], None
    out["coverage"] = round(len(known) / len(needed), 2) if needed else (1.0 if reported is not None else 0.0)
    if stored == "partial":
        return {**out, "quality": PARTIAL, "total": reported if reported is not None else computed}
    if needed and len(known) == len(needed):
        if reported is not None and reported != computed:
            return {**out, "quality": CONTRADICTORY, "total": reported}
        return {**out, "quality": COMPLETE, "total": computed, "comparable": True}
    if needed and known:  # a counter the provider should have sent is missing: a lower bound, not a measurement
        return {**out, "quality": PARTIAL, "total": computed}
    if reported is not None:
        return {**out, "quality": TOTAL_ONLY, "total": reported}
    return out


def measured_total(usage: object, agent: str | None = None) -> int | None:
    """The final, trustworthy token total of an attempt: None unless the measurement is complete or the provider's
    own whole-session total. Partial and contradictory records answer None (use `normalize` for their lower bound)."""
    n = normalize(usage, agent)
    return n["total"] if n["quality"] in (COMPLETE, TOTAL_ONLY) else None


def comparable_total(usage: object, agent: str | None = None) -> int | None:
    """A total that can be compared across providers (complete records only), else None."""
    n = normalize(usage, agent)
    return n["total"] if n["comparable"] else None
