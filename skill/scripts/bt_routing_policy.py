"""Router policy knobs: start tier by kind/complexity/risk, effort weights, bounded exploration and pressure buckets.

Routing defaults are configurable through `bitacora.py config` (routing.*). MAX_KIND_TIER is a hard budget:
docs never exceed tier 0, tests/research never exceed tier 1. Architecture and risk still lift implementation/audits.
"""
from __future__ import annotations

TOP = 2
MAX_KIND_TIER = {"docs": 0, "test": 1, "research": 1}
HIGH_PRESSURE = 85.0
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# Heuristic weights of the quota a model burns at an effort, relative to its default effort. Estimates, never
# observations (references/agents.md): replace them with measured tokens as soon as the telemetry carries them.
EFFORT_WEIGHT = {"low": 1.0, "medium": 1.0, "high": 1.5, "xhigh": 2.0, "max": 2.5}
UNKNOWN_PRESSURE = 50.0  # assumed % used when the subscription sample is missing or stale: neither empty nor full
PRESSURE_BUCKET = 10.0   # accounts within one bucket of each other are interchangeable for quota balancing
EXPENSIVE_COST = 6       # MODELS[...]["cost"] from which a route needs an exploration budget
EXPLORE_WINDOW_SEC = 7 * 86400
WILSON_Z = 1.2816        # one-sided 90 % lower bound: five lucky attempts are not evidence of quality


def config(key: str, default):
    try:
        import bt_config
        return bt_config.get(key, default)
    except Exception:
        return default


def cap_tier(tier: int, kind: str | None = None) -> int:
    """Hard budget ceiling shared by selection, saved tasks and retry escalation."""
    return max(0, min(int(tier or 0), MAX_KIND_TIER.get(kind, TOP)))


def start_tier(level: str | None, kind: str | None = None, complexity: str | None = None,
               risk: str | None = None) -> tuple[int, str]:
    tier, reason = _start_tier(level, kind, complexity, risk)
    capped = cap_tier(tier, kind)
    return capped, reason + (f"; {kind} ceiling {capped}" if capped < tier else "")


def _start_tier(level: str | None, kind: str | None = None, complexity: str | None = None,
               risk: str | None = None) -> tuple[int, str]:
    """(tier, reason) where a task starts on the ladder. Architecture-level work starts at the top whatever its kind;
    an audit starts at the standard tier; large complexity or high risk lift every other kind one tier (two when both
    hold for implementation); docs, tests and research otherwise start light."""
    level, kind = (level or "").strip().lower(), kind or "implement"
    complexity, risk = (complexity or "").upper(), (risk or "").lower()
    if level == "architecture":
        return TOP, "level: architecture"
    if kind == "audit":
        return 1, "audit budget"
    lifts = [name for name, on in (("complexity L", complexity == "L"), ("risk high", risk == "high")) if on]
    if not lifts:
        return 0, f"{kind} default"
    tier = min(TOP, 1 + (len(lifts) == 2 and kind == "implement"))
    return tier, f"{kind} lifted by " + " + ".join(lifts)


def effort_weight(effort: str | None) -> float:
    configured = config("routing.effort_weight", None)
    table = {**EFFORT_WEIGHT, **(configured if isinstance(configured, dict) else {})}
    try:
        return float(table.get(effort or "medium", 1.0))
    except (TypeError, ValueError):
        return 1.0


def wilson_lower(done: int, judged: int, z: float = WILSON_Z) -> float | None:
    """Lower confidence bound of a success rate: None without judged attempts."""
    if judged <= 0:
        return None
    p = done / judged
    denom = 1 + z * z / judged
    centre = p + z * z / (2 * judged)
    margin = z * ((p * (1 - p) + z * z / (4 * judged)) / judged) ** 0.5
    return max(0.0, (centre - margin) / denom)


def pressure_bucket(pressure: float | None) -> int:
    """Quota balancing key: unknown pressure is assumed mid-range, so a known 20 % account beats an unsampled one and
    an unsampled one beats a known 90 % account."""
    value = UNKNOWN_PRESSURE if pressure is None else float(pressure)
    return int(value // PRESSURE_BUCKET)


def subscription_blocked(row: object) -> bool:
    """Known sign-in/challenge failures rank behind healthy accounts, even with weekly pace penalties.
    Missing/stale samples keep neutral pressure; a blocked sample remains a fallback until a successful poll."""
    return isinstance(row, dict) and row.get("status") in {
        "invalid_credentials", "auth_unavailable", "manual_challenge", "http_401", "http_403"}


def is_critical(tier: int | None, risk: str | None, complexity: str | None, kind: str | None = None) -> bool:
    """Work whose failure is expensive: declared high risk, large complexity or the top tier (never an audit, whose
    order has its own rules). Critical work is protected from being routed by quota alone (quality_leads)."""
    if kind == "audit":
        return False
    return (risk or "").lower() == "high" or (complexity or "").upper() == "L" or int(tier or 0) >= TOP


def quality_mode() -> str:
    return str(config("routing.quality_protection", "critical")).lower()


def quality_leads(critical: bool) -> bool:
    """`routing.quality_protection`: "critical" (default) lets verified quality lead quota on critical work only,
    "always" on every task, "off" restores quota-first ordering everywhere (no quality gap either)."""
    mode = quality_mode()
    return mode == "always" or (mode == "critical" and critical)


def quality_gap() -> float:
    """`routing.quality_gap` (default 0.25): how far below the best proven route a route is "clearly inferior" for
    routine work; compared on lower confidence bounds, so only evidence-backed gaps count."""
    try:
        return float(config("routing.quality_gap", 0.25))
    except (TypeError, ValueError):
        return 0.25


def may_explore(cost: float, kind: str, risk: str | None, samples: int, recent_attempts: int,
                critical: bool = False) -> bool:
    """Cold start (under-sampled route): cheap routes explore on low-risk non-audit work; expensive ones only within
    the weekly exploration budget (routing.explore_budget_week, default 5) of ADMITTED explorations (bt_explore), not
    of ordinary attempts. Never on high-risk or critical work."""
    if kind == "audit" or critical or (risk or "").lower() == "high":
        return False
    if samples >= int(config("routing.min_samples", 5)):
        return False
    if cost < EXPENSIVE_COST:
        return True
    return recent_attempts < int(config("routing.explore_budget_week", 5))


PACE_MARGIN = 15.0   # points ahead of an even weekly burn before the account is deprioritised
PACE_PENALTY = 20.0  # pressure-equivalent points added to an account burning its week too fast


def weekly_pace_surplus(row: object, now: float) -> float | None:
    """Points of the seven-day window used beyond an even burn so far (`used - elapsed share of the window`). None
    without a fresh, well-formed seven-day sample: pacing then says nothing rather than inventing slack or debt."""
    try:
        window = row["windows"]["seven_day"]
        used, resets, minutes = float(window["used_percent"]), window["resets_at"], float(window["window_minutes"])
        if row.get("status") != "ok" or resets is None or minutes <= 0 or float(resets) <= now:
            return None
        elapsed = 1 - (float(resets) - now) / (minutes * 60)
        return used - 100 * min(1.0, max(0.0, elapsed))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def paced_pressure(pressure: float | None, surplus: float | None) -> float | None:
    """Pressure used to rank accounts: the bottleneck plus a penalty while the week is burning faster than evenly.
    Accounts with budget to spare are not pushed to spend it (no forced consumption): they only stop being penalised."""
    if pressure is None or surplus is None or surplus <= PACE_MARGIN:
        return pressure
    return min(100.0, pressure + PACE_PENALTY)
