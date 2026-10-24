"""Account router and quota/history ranking. Model catalog: bt_agent_models.

Public catalog/selection names remain re-exported here for existing callers.
Quota state is machine-local (<root>/.state/quota.json); see references/agents.md.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

import bt_profiles
import bt_routing_policy
from bt_core import STATE

from bt_agent_models import (  # public compatibility surface
    PROVIDERS, KINDS, TOP, EFFORTS, MODELS, LADDER, KIND_TIER, AUDIT_LADDER, MAX_KIND_TIER,
    infer_kind, start_tier, rank_of, provider_of_model, model_for, legacy_model_for, apply_explicit_effort,
)

_DEFAULT_ACCOUNT_DIRECTORIES = {"CLAUDE_CONFIG_DIR": ".claude", "CODEX_HOME": ".codex"}
LOAD_WINDOW_SEC = 5 * 3600
LOAD_BUCKET_SEC = 1800
MIN_SAMPLES = 5

# ---------------------------------------------------------------- quota

def _quota_path() -> Path:
    return STATE / "quota.json"

def _quota_load() -> dict:
    try:
        data = json.loads(_quota_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}

def quota_mark(profile: str | None, agent: str | None, until_epoch: int | float, reason: str = "",
               model: str | None = None, default_min: int | None = None) -> float:
    """Record that an account hit a usage limit. `until_epoch` 0/unknown -> a default cooldown that doubles with each
    consecutive hit (capped at 4 h). Returns the epoch it cools until."""
    from bt_lock import central_lock
    key = account_key(profile, agent)
    with central_lock("quota"):
        data = _quota_load()
        prev = data.get(key) if isinstance(data.get(key), dict) else {}
        now = time.time()
        streak = int(prev.get("streak") or 0) + 1 if now - float(prev.get("at") or 0) < 6 * 3600 else 1
        if not until_epoch or until_epoch <= now:
            if default_min is None:
                default_min = _config("quota.default_cooldown_min", 30)
            until_epoch = now + min(default_min * 60 * 2 ** (streak - 1), 4 * 3600)
        data[key] = {"until": float(until_epoch), "at": now, "streak": streak, "model": model,
                     "reason": " ".join((reason or "").split())[:200]}
        path = _quota_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
        tmp.replace(path)
    return float(until_epoch)

def quota_clear(profile: str | None, agent: str | None = None) -> bool:
    from bt_lock import central_lock
    with central_lock("quota"):
        data = _quota_load()
        if data.pop(account_key(profile, agent), None) is None:
            return False
        _quota_path().write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    return True

def cooling_until(profile: str | None, agent: str | None = None) -> float | None:
    """Epoch until which the account must not be used, None when it is free."""
    row = _quota_load().get(account_key(profile, agent))
    until = float(row.get("until") or 0) if isinstance(row, dict) else 0
    return until if until > time.time() else None

def account_key(profile: str | None, agent: str | None = None) -> str:
    """Return the stable legacy quota-cache key encoded from this profile's environment overlay."""
    if not profile:
        return f"{agent or 'claude'}:default"
    try:
        spec = bt_profiles.get(profile)
    except SystemExit:
        return profile
    env = sorted((spec.get("env") or {}).items())
    return f"{spec['provider']}:" + (",".join(f"{k}={v}" for k, v in env) if env else "default")

def _pool_account_identity(profile: str, spec: dict) -> tuple[str, tuple[tuple[str, str | None], ...]]:
    """Identify the effective account for in-memory pool deduplication without changing persisted quota keys."""
    provider = spec["provider"]
    env = bt_profiles.env_of(profile)
    selectors = []
    for key in bt_profiles.ACCOUNT_VARS.get(provider, ()):
        value = env.get(key)
        if value is None:
            default_directory = _DEFAULT_ACCOUNT_DIRECTORIES.get(key)
            value = str(Path.home() / default_directory) if default_directory else None
        if value:
            value = os.path.normpath(value)
        selectors.append((key, value))
    return provider, tuple(selectors)

def _config(key: str, default):
    try:
        import bt_config
        return bt_config.get(key, default)
    except Exception:
        return default

# ---------------------------------------------------------------- pool and routing

def pool_for(project: str, requested: list[str] | None = None) -> list[str]:
    """Profile ids that may run `project`, one per account, in preference order. `requested` (run --pool a,b or the
    routing.pool setting) restricts and orders them; unknown ids are refused. Work-only profiles are dropped for
    projects not marked work; the accounts of the profiles in the project's `exclude_profiles` are dropped; a named profile wins over
    the generic one of the same account; a profile whose CLI or account directory is missing is skipped."""
    profiles = bt_profiles.load()
    excluded = {_pool_account_identity(pid, profiles[pid])
                for pid in bt_profiles.excluded_profiles(project) if pid in profiles}  # aliases share the account
    wanted = [p for p in (requested or []) if p]
    for pid in wanted:
        if pid not in profiles:
            raise bt_profiles.ProfileError(f"Unknown profile '{pid}'. Known: {', '.join(sorted(profiles))}")
    ids = wanted or sorted(profiles, key=lambda p: (p in bt_profiles.DEFAULTS, p))
    out, seen = [], set()
    for pid in ids:
        spec = profiles[pid]
        if spec["provider"] not in PROVIDERS:
            continue
        identity = _pool_account_identity(pid, spec)
        if identity in seen:
            continue
        if spec.get("work_only") and not bt_profiles.is_work_project(project):
            continue
        if identity in excluded:
            continue
        if not shutil.which(spec.get("bin") or spec["provider"]):
            continue
        env = bt_profiles.env_of(pid)
        if any(k in env and not Path(env[k]).is_dir() for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME")):
            continue
        if spec["provider"] == "antigravity" and not (
                Path.home() / ".gemini" / "antigravity-cli" / "antigravity-oauth-token").exists():
            continue  # not signed in: `agy` would ask for a browser login in the middle of a run
        seen.add(identity)
        out.append(pid)
    return out

class _Rates(dict):
    """Success rates by (agent, model, effort, kind) with enough samples; `.samples` holds every judged-attempt count, so a
    provider with 1-4 attempts is known to be under-sampled instead of looking the same as an unseen one."""

    samples: dict = {}
    lower: dict = {}   # lower confidence bound of each rate: what the quality band ranks by
    recent: dict = {}  # admitted explorations in the last 7 days by (agent, model): the exploration budget's counter
    recent_total: int = 0
    pooled: dict = {}  # (agent, model, kind): outcomes of every effort together, with the per-effort split

def _stats() -> tuple[dict, dict]:
    """(success rate by (agent, model, kind) with enough samples, seconds used per account in the load window)."""
    try:
        import bt_events
        rows = bt_events.read_all()
    except OSError:
        print("[events] attempt history unreadable; routing without historical measurements", file=sys.stderr)
        return {}, {}
    import datetime as dt
    load: dict[str, float] = {}
    now = time.time()
    for r in rows:
        try:
            age = now - dt.datetime.fromisoformat(r["ts"]).timestamp()
        except (KeyError, ValueError, TypeError):
            continue
        if 0 <= age <= LOAD_WINDOW_SEC:
            acc = account_key(r.get("profile"), r.get("agent"))
            cost = MODELS.get(str(r.get("model")), {}).get("cost", 2) * bt_routing_policy.effort_weight(r.get("effort"))
            load[acc] = load.get(acc, 0) + (r.get("seconds") or 0) * cost
    # Quality learns from TASK outcomes (bt_outcomes), not from session aggregates: a session of three tasks with one
    # failure is two verified tasks and one failed, not a failed session. Provider losses, skips and unjudged results
    # never enter a rate. Consumption (`load`, above) stays per session: a session is paid once.
    import bt_explore
    import bt_outcomes
    # Identity of a measured configuration: (agent, model, effort, kind). Another effort of the same model is a
    # different configuration: its outcomes are kept apart and only ever surface as labelled AGGREGATE evidence.
    direct_counts = bt_outcomes.counts(rows, ("agent", "model", "effort", "kind"))
    counts = {k: (g["judged"], g["verified"]) for k, g in direct_counts.items()}
    min_samples = int(_config("routing.min_samples", MIN_SAMPLES))
    rates = _Rates({k: done / judged for k, (judged, done) in counts.items() if judged >= min_samples})
    rates.samples = {k: judged for k, (judged, _) in counts.items()}
    # The band uses the lower confidence bound: a short lucky streak must not read as a proven route.
    rates.lower = {k: bt_routing_policy.wilson_lower(done, judged) for k, (judged, done) in counts.items()
                   if judged >= min_samples}
    rates.pooled = {}
    for (agent, model, effort, kind), (judged, done) in counts.items():
        pooled = rates.pooled.setdefault((agent, model, kind), {"judged": 0, "verified": 0, "efforts": {}})
        pooled["judged"] += judged
        pooled["verified"] += done
        pooled["efforts"][effort] = (judged, done)
    # Only admitted explorations (the ledger) spend the exploration budget: ordinary attempts never do.
    rates.recent, rates.recent_total = bt_explore.used(now)
    return rates, load

def _quality_order(agent: str, kind: str, rate: float | None, pressure: float | None, samples: int = 0,
                   explore: bool = False, critical: bool = False, best: float | None = None,
                   point: float | None = None) -> tuple:
    """Sort-key part after the provider rules (busy, avoided builder provider, `_role_rank`, which already put the
    preferred auditor first). `rate` is the lower confidence bound of the verified task success rate, so a small sample
    never looks more precise than it is; quota headroom is in 10-point buckets (unknown pressure counts as mid-range).

    Routine work: quota balancing leads, but a route whose proven quality is clearly below the best admissible one
    (more than `routing.quality_gap`, default 0.25, under it) goes behind, so spare quota is never spent on a route
    that mostly fails. Critical work (risk high, complexity L, top tier; `routing.quality_protection` "critical" by
    default, "always" or "off"): the verified quality band leads and quota only breaks ties. An unproven route has no
    lower bound and is never "clearly inferior", so missing history blocks nothing.
    Audits within one role rank: measured quality first, then the audit budget order (Codex Sol is the last fallback
    after Claude Sonnet and Flash, agents.md rule 4), and only then headroom.

    Cold start: a route with fewer than `routing.min_samples` judged outcomes of this kind takes the top measured band
    only when `explore` is set (bt_routing_policy.may_explore: cheap model or weekly budget left, low-risk non-audit,
    non-critical work). Otherwise it ranks as an unproven route, below every route whose lower bound is at least 0.1."""
    band = -(round(rate * 5) if rate is not None else 1)  # unproven ranks below any route with a positive bound
    if rate is None and explore:
        band = -6
    headroom = bt_routing_policy.pressure_bucket(pressure)
    if kind == "audit":
        return band, agent == "codex", headroom
    if bt_routing_policy.quality_leads(critical):
        return band, headroom
    # "Clearly inferior" compares this route's observed rate with the best route's PROVEN (lower-bound) rate, so a small
    # sample is not punished twice and a route is relegated only by an evidence-backed gap.
    inferior = (point is not None and best is not None and bt_routing_policy.quality_mode() != "off"
                and best - point > bt_routing_policy.quality_gap())
    return int(inferior), headroom, band

def candidates(project: str, pool: list[str], tier: int, kind: str = "implement", configured: str | None = None,
               avoid_providers: set | None = None, busy: set | None = None, risk: str | None = None,
               complexity: str | None = None, allow_explore: bool = True, effort: str | None = None, role: str | None = None,
               escalated: bool = False
               ) -> tuple[list[dict], float | None]:
    """(routes of `tier` ordered best first, earliest epoch a cooling account frees up when none is available).
    `busy`: account keys already taken by sessions being started in the same batch (they go last). `risk` and
    `complexity` of the work make it critical (bt_routing_policy.is_critical): quality leads quota and cold-start
    exploration stays away. Routes that would be explorations carry `exploring`; route() admits them against the
    persistent budget (bt_explore) and asks again with `allow_explore=False` when the budget is spent. `effort`: an effort
    the work asked for explicitly: it is applied BEFORE the routes are compared, so the quality evidence consulted is the
    one of the effort that will really run."""
    if role:
        from bt_role_routing import candidates as role_candidates
        return role_candidates(project, pool, tier, kind, role, configured, avoid_providers, busy, complexity, effort,
                               escalated)
    from bt_subscriptions import capacity
    from bt_subscriptions import load as load_usage
    samples = load_usage(STATE)
    tier = bt_routing_policy.cap_tier(tier, kind)
    rates, load = _stats()
    profiles = bt_profiles.load()
    critical = bt_routing_policy.is_critical(tier, risk, complexity, kind)
    asked_effort, effort = effort, None
    routes, soonest, staged = [], None, []
    for index, pid in enumerate(pool):
        spec = profiles.get(pid)
        if not spec or spec["provider"] not in PROVIDERS:
            continue
        agent = spec["provider"]
        if spec.get("work_only") and not bt_profiles.is_work_project(project):
            continue  # a pool saved while the project was work must not outlive that flag
        model, ladder_effort = model_for(agent, tier, configured, kind)
        effort = apply_explicit_effort(agent, model, ladder_effort, asked_effort, kind)
        pressure, exhausted = capacity(samples.get(account_key(pid, agent)), model)
        if agent == "antigravity":  # Google's own quota report, refreshed by the supervisor (bt_agy)
            import bt_agy
            pressure, exhausted = bt_agy.capacity()
        ranked_pressure = bt_routing_policy.paced_pressure(
            pressure, bt_routing_policy.weekly_pace_surplus(samples.get(account_key(pid, agent)), time.time()))
        deadlines = [value for value in (cooling_until(pid, agent), exhausted) if value is not None]
        until = max(deadlines) if deadlines else None
        if until:
            soonest = until if soonest is None else min(soonest, until)
            continue
        evidence, rate, lower = evidence_for(rates, agent, model, effort, kind)
        seen = evidence["samples"] if evidence["kind"] != "aggregate" else evidence["direct_samples"]
        explore = allow_explore and rate is None and not evidence.get("poor") and bt_routing_policy.may_explore(
            MODELS.get(model, {}).get("cost", 2), kind, risk, seen, getattr(rates, "recent", {}).get((agent, model), 0),
            critical)
        staged.append((index, pid, agent, model, effort, pressure, ranked_pressure, rate, seen, explore, lower,
                       evidence))
    best = max((row[10] for row in staged if row[10] is not None), default=None)
    for index, pid, agent, model, effort, pressure, ranked_pressure, rate, seen, explore, lower, evidence in staged:
        acc = account_key(pid, agent)
        cost = MODELS.get(model, {}).get("cost", 2) * bt_routing_policy.effort_weight(effort)
        routes.append({"profile": pid, "agent": agent, "model": model, "effort": effort, "tier": tier, "kind": kind,
                       "exploring": explore, "account": acc, "evidence": evidence,
                       "_key": (bt_routing_policy.subscription_blocked(samples.get(acc)), acc in (busy or ()),
                                agent in (avoid_providers or ()),
                                _role_rank(agent, kind, pressure),
                                agent in ("claude", "codex") and pressure is not None and
                                pressure >= bt_routing_policy.HIGH_PRESSURE,
                                *_quality_order(agent, kind, lower, ranked_pressure, seen, explore, critical, best, rate),
                                int(cost / max(lower if lower is not None else 0.5, 0.1)),  # expected cost per verified task
                                int(load.get(acc, 0) // (LOAD_BUCKET_SEC * 2)), index),
                       "why": (("audit budget: Sonnet medium / Opus high; " if agent == "claude" else
                                "audit fallback: Sol medium / high; ") if kind == "audit" else "") +
                              ("critical work: verified quality before quota; " if critical and kind != "audit" else "") +
                              _why(agent, avoid_providers, rate, load.get(acc, 0), lower, seen, evidence) +
                              (f"; subscription bottleneck {pressure:g}% used" if pressure is not None else
                               "; subscription usage unknown/stale")})
    # The rate is compared in 20-point bands on purpose: a few points of difference over a handful of attempts is
    # noise, and a tie hands the choice to quota balancing (load, then pool order).
    routes.sort(key=lambda r: r["_key"])
    for r in routes:
        r.pop("_key")
    return routes, soonest

AGY_BUSY_PERCENT = 85  # above this, Flash stops being the preferred auditor and is kept as a reserve

def _role_rank(agent: str, kind: str, pressure: float | None) -> int:
    """0 = preferred for this kind of work, 1 = otherwise. Audits prefer the configured auditor provider (default
    antigravity: Gemini 3.8 Flash low) while its quota has room; everything else ranks Flash behind the other
    providers (it is the slowest), so it builds only when they are exhausted or avoided."""
    if kind == "audit":
        preferred = _config("audit.provider", "antigravity")
        if agent == preferred:
            return 0 if pressure is None or pressure < AGY_BUSY_PERCENT else 2  # busy: behind the others
        return 1
    return 1 if agent == "antigravity" else 0

AGGREGATE_DISCOUNT = 0.2  # indirect evidence ranks one 20-point band below what it would show if it were direct
POOR_AGGREGATE = 0.3      # other efforts of this model measured below this lower bound: do not spend exploration on it



def evidence_for(rates, agent: str, model: str, effort: str | None, kind: str) -> tuple[dict, float | None, float | None]:
    """(evidence, direct rate, ranking quality) of one configuration. `direct`: verified outcomes of exactly
    (agent, model, effort, kind), at least `routing.min_samples`. `aggregate`: only OTHER efforts of the same model have
    enough outcomes; they inform the ranking (lower bound minus one band) and the exploration priority, are labelled, and
    NEVER become this effort's measured success rate. `none`: nothing usable, which blocks nothing."""
    key = (agent, model, effort, kind)
    samples = getattr(rates, "samples", {}).get(key, 0)
    rate = rates.get(key)
    if rate is not None:
        lower = getattr(rates, "lower", {}).get(key, rate)
        return {"kind": "direct", "samples": samples, "rate": rate, "lower": lower}, rate, lower
    pooled = getattr(rates, "pooled", {}).get((agent, model, kind))
    others = {e: v for e, v in (pooled or {"efforts": {}})["efforts"].items() if e != effort}
    judged, done = sum(j for j, _ in others.values()), sum(d for _, d in others.values())
    if judged >= int(_config("routing.min_samples", MIN_SAMPLES)):
        # this effort's own outcomes, below the direct threshold, still count (a few direct failures are not hidden by
        # a strong neighbour) and a direct majority of failures marks the route poor
        own_judged, own_done = (pooled["efforts"].get(effort) or (0, 0)) if pooled else (0, 0)
        judged, done = judged + own_judged, done + own_done
        agg_lower = bt_routing_policy.wilson_lower(done, judged) or 0.0
        return ({"kind": "aggregate", "samples": judged, "direct_samples": samples, "rate": None,
                 "aggregate_rate": done / judged, "lower": max(0.0, agg_lower - AGGREGATE_DISCOUNT),
                 "from_efforts": sorted(str(e) for e in others),
                 "poor": agg_lower < POOR_AGGREGATE or own_judged - own_done > own_done},
                None, max(0.0, agg_lower - AGGREGATE_DISCOUNT))
    return {"kind": "none", "samples": samples, "rate": None, "lower": None}, None, None

def _why(agent, avoid, rate, load, lower=None, seen: int = 0, evidence: dict | None = None) -> str:
    bits = []
    if avoid:
        bits.append("other provider than " + "/".join(sorted(avoid)) if agent not in avoid else "same provider")
    kind = (evidence or {}).get("kind")
    if kind == "aggregate":
        bits.append(f"INDIRECT evidence only: other efforts of this model {evidence['aggregate_rate']:.0%} over "
                    f"{evidence['samples']} judged (ranked at lower bound minus one band; not this effort's success)")
    else:
        bits.append(f"direct verified task success {rate:.0%} (lower bound {lower:.0%}, {seen} judged)"
                    if rate is not None else f"no proven history yet ({seen} judged)")
    bits.append(f"load {int(load // 60)} weighted-min in the last 5 h")
    return "; ".join(bits)

class NoRoute(Exception):
    """Every account of the pool is cooling down; `until` is the earliest reset epoch."""

    def __init__(self, until: float | None):
        super().__init__(f"every account is cooling down until {until}")
        self.until = until or (time.time() + 1800)

def route(project: str, state: dict, tier: int, kind: str = "implement", avoid_providers: set | None = None,
          busy: set | None = None, risk: str | None = None, complexity: str | None = None,
          allow_explore: bool = True, effort: str | None = None, decision_key: str | None = None, role: str | None = None) -> dict:
    """The route of one session. Fixed mode (no pool): the run's own agent/profile at the tier's model. Pool mode:
    the best available candidate; raises NoRoute when all accounts are cooling down. The route carries its `decision`
    (bt_explore): exploit, explore (admitted against the persistent budget), fallback (an account was cooling),
    escalation (a failure moved the work) or explicit (a pinned agent)."""
    import bt_explore
    import bt_role_policy
    explicit_role = role or state.get("role")
    role = explicit_role or bt_role_policy.role_for_kind(kind)
    tier = bt_routing_policy.cap_tier(tier, kind)
    # an audit the run escalated (tier 2) is read by the strongest reviewer, unless the caller pinned a role explicitly
    escalated = not explicit_role and bt_role_policy.escalated_audit(kind, tier)
    pool = state.get("pool") or []
    if not pool:
        asked_effort = effort
        agent = state.get("agent") or "claude"
        model, effort = (model_for(agent, tier, kind=kind) if kind == "audit" or kind in MAX_KIND_TIER
                         else legacy_model_for(state, tier))
        if role:
            choices = [(m, e) for p, m, e in bt_role_policy.options(
                role, complexity, escalated=escalated) if p == agent]
            configured = state.get("model") if kind != "audit" or state.get("role") else None
            if choices:
                model = configured or choices[0][0]
                effort = next((e for m, e in choices if m == model), None if model == "haiku" else choices[0][1])
        effort = asked_effort or effort
        return {"profile": state.get("profile"), "agent": agent, "model": model, "effort": effort, "tier": tier,
                "kind": kind, "role": role, "why": "fixed (no pool)",
                "decision": bt_explore.decision_for("explicit", "the run is pinned to one agent (no pool)")}
    from bt_subscriptions import ensure_fresh
    ensure_fresh(pool, project=project)
    if not role:
        _refresh_google_quota(pool)
    configured = state.get("model")
    if (role and configured == "haiku" and not state.get("model_pinned")) or (kind == "audit" and not state.get("role")):
        configured = None
    args = (project, pool, tier, kind, configured, avoid_providers, busy, risk, complexity)
    routes, soonest = candidates(*args, allow_explore=allow_explore, effort=effort, role=role, escalated=escalated)
    if not routes:
        if soonest is None:  # nothing is cooling: no account of the pool may run this project any more
            raise bt_profiles.ProfileError(f"No account of the pool ({', '.join(pool)}) may run '{project}'. "
                                           f"Check: bitacora.py --project {project} agents")
        raise NoRoute(soonest)
    chosen, record = routes[0], None
    # An exploration is a real choice between routes: a lone candidate is forced, not explored.
    if chosen.get("exploring") and len(routes) > 1:
        cost = MODELS.get(chosen["model"], {}).get("cost", 2)
        limit = int(_config("routing.explore_budget_week", 5)) if cost >= bt_routing_policy.EXPENSIVE_COST else -1
        global_limit = _config("routing.explore_global_budget_week", None)
        record = bt_explore.reserve(
            chosen, project, state.get("req"),
            f"cold start: {chosen['agent']}/{chosen['model']} has fewer than routing.min_samples judged {kind} outcomes "
            f"and {len(routes) - 1} other admissible route(s) exist",
            limit, int(global_limit or 0) or None, key=decision_key)
        if record is None:  # the weekly budget is spent (possibly by a concurrent supervisor): rank it as unproven
            routes, soonest = candidates(*args, allow_explore=False, effort=effort, role=role, escalated=escalated)
            chosen = routes[0]
    if record:
        decision = bt_explore.decision_for("explore", record["reason"], record)
    elif avoid_providers and kind != "audit" and not role:
        decision = bt_explore.decision_for("escalation", "a failed attempt moved the work to another provider: "
                                           + "/".join(sorted(avoid_providers)) + " avoided")
    elif soonest is not None:
        decision = bt_explore.decision_for("fallback", "an account of the pool is cooling down or exhausted; best "
                                           "admissible route chosen")
    else:
        decision = bt_explore.decision_for("exploit", chosen["why"])
    decision["evidence"] = chosen.get("evidence")  # what the choice rested on: direct, aggregate or none
    chosen = {k: v for k, v in chosen.items() if k != "exploring"}
    return {**chosen, "decision": decision}

def _refresh_google_quota(pool: list[str]) -> None:
    """Antigravity reports its quota through its own CLI (`agy --print=/usage`, no model turn). Done here, once per
    route and at most every 15 minutes, so candidates() itself stays free of I/O. Never raises."""
    try:
        profiles = bt_profiles.load()
        if any(profiles.get(p, {}).get("provider") == "antigravity" for p in pool):
            import bt_agy
            bt_agy.refresh()
    except Exception:
        pass



# ---------------------------------------------------------------- views

def catalog(project: str | None = None) -> dict:
    """Everything an agent needs to choose a route: models, the ladder, accounts and their availability."""
    profiles = bt_profiles.load()
    accounts = []
    for pid in sorted(profiles, key=lambda p: (p in bt_profiles.DEFAULTS, p)):
        spec = profiles[pid]
        if spec["provider"] not in PROVIDERS:
            continue
        until = cooling_until(pid, spec["provider"])
        allowed = not (spec.get("work_only") and not (project and bt_profiles.is_work_project(project)))
        accounts.append({"profile": pid, "provider": spec["provider"], "work_only": bool(spec.get("work_only")),
                         "allowed_here": allowed if project else None,
                         "installed": bool(shutil.which(spec.get("bin") or spec["provider"])),
                         "cooling_until": time.strftime("%Y-%m-%d %H:%M", time.localtime(until)) if until else None})
    import bt_role_policy
    return {"roles": {role: bt_role_policy.options(role) for role in bt_role_policy.ROLES},
            "models": [{"id": k, **v} for k, v in MODELS.items()],
            "ladder": {p: [{"tier": i, "model": m, "effort": e} for i, (m, e) in enumerate(rungs)]
                       for p, rungs in LADDER.items()},
            "kinds": list(KINDS), "accounts": accounts,
            "pool": pool_for(project) if project else None}

from bt_agent_views import brief as _catalog_brief

def brief(project: str | None = None) -> str:
    return _catalog_brief(project) + (
        "\n\nDesigner authors UI contracts in `design/contracts/`; UI implementation follows the "
        "owner-approved contract. Optional preview uses `design.preview`.")
