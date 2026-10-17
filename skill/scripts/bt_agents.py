"""Agent catalog and router: which account, model and effort a piece of work runs with.

The catalog lists the models this toolkit drives (Claude Code and Codex CLIs). A *route* is (profile, agent, model,
effort). Work is described by a capability tier (0 light, 1 standard, 2 top: the escalation ladder) and a kind
(implement, test, docs, audit, research). With a pool of profiles the router picks, among the routes of that tier:
a profile that is allowed for the project and not cooling down after a usage limit, preferably another provider than
the one that just failed (or, for an audit, than the one that built the work), then the best measured success rate,
then the least used account in the current window. No provider is preferred because it is the one hosting the
current session: the best measured route for the kind wins. Without a pool the run's own profile is used, as before.

Quota state is machine-local (<root>/.state/quota.json): a profile that reported a usage limit is skipped until its
announced reset. Rules for agents: references/agents.md.
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

PROVIDERS = ("claude", "codex", "antigravity")
KINDS = ("implement", "test", "docs", "audit", "research")
TOP = 2
EFFORTS = ("low", "medium", "high", "xhigh", "max")
_DEFAULT_ACCOUNT_DIRECTORIES = {"CLAUDE_CONFIG_DIR": ".claude", "CODEX_HOME": ".codex"}

# rank: the lowest tier the model is a sensible default for. cost: relative weight on its subscription's quota.
MODELS: dict[str, dict] = {
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
LOAD_WINDOW_SEC = 5 * 3600
LOAD_BUCKET_SEC = 1800
MIN_SAMPLES = 5
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
    everything else at the light tier. A floor, never a ceiling: escalation can still raise it."""
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
    tier = max(0, min(TOP, int(tier or 0)))
    if kind == "audit":
        # A builder's configured model must not inflate the independent audit's budget.
        return AUDIT_LADDER.get(provider, AUDIT_LADDER["claude"])[tier]
    model, effort = LADDER.get(provider, LADDER["claude"])[tier]
    if configured and provider_of_model(configured) == provider and (tier == 0 or rank_of(configured) >= rank_of(model)):
        model = configured
    if provider == "codex" and tier == 0 and kind == "docs":
        effort = "low"
    return model, effort


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
    projects not marked work; a named profile wins over the generic one of the same account; a profile whose CLI or
    account directory is missing is skipped."""
    profiles = bt_profiles.load()
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
    """Success rates by (agent, model, kind) with enough samples; `.samples` holds every judged-attempt count, so a
    provider with 1-4 attempts is known to be under-sampled instead of looking the same as an unseen one."""

    samples: dict = {}
    lower: dict = {}   # lower confidence bound of each rate: what the quality band ranks by
    recent: dict = {}  # admitted explorations in the last 7 days by (agent, model): the exploration budget's counter
    recent_total: int = 0


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
    counts = {k: (g["judged"], g["verified"]) for k, g in bt_outcomes.counts(rows, ("agent", "model", "kind")).items()}
    min_samples = int(_config("routing.min_samples", MIN_SAMPLES))
    rates = _Rates({k: done / judged for k, (judged, done) in counts.items() if judged >= min_samples})
    rates.samples = {k: judged for k, (judged, _) in counts.items()}
    # The band uses the lower confidence bound: a short lucky streak must not read as a proven route.
    rates.lower = {k: bt_routing_policy.wilson_lower(done, judged) for k, (judged, done) in counts.items()
                   if judged >= min_samples}
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
               complexity: str | None = None, allow_explore: bool = True) -> tuple[list[dict], float | None]:
    """(routes of `tier` ordered best first, earliest epoch a cooling account frees up when none is available).
    `busy`: account keys already taken by sessions being started in the same batch (they go last). `risk` and
    `complexity` of the work make it critical (bt_routing_policy.is_critical): quality leads quota and cold-start
    exploration stays away. Routes that would be explorations carry `exploring`; route() admits them against the
    persistent budget (bt_explore) and asks again with `allow_explore=False` when the budget is spent."""
    from bt_subscriptions import capacity
    from bt_subscriptions import load as load_usage
    samples = load_usage(STATE)
    rates, load = _stats()
    profiles = bt_profiles.load()
    critical = bt_routing_policy.is_critical(tier, risk, complexity, kind)
    routes, soonest, staged = [], None, []
    for index, pid in enumerate(pool):
        spec = profiles.get(pid)
        if not spec or spec["provider"] not in PROVIDERS:
            continue
        agent = spec["provider"]
        if spec.get("work_only") and not bt_profiles.is_work_project(project):
            continue  # a pool saved while the project was work must not outlive that flag
        model, effort = model_for(agent, tier, configured, kind)
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
        rate = rates.get((agent, model, kind))
        seen = getattr(rates, "samples", {}).get((agent, model, kind), 0)
        explore = allow_explore and rate is None and bt_routing_policy.may_explore(
            MODELS.get(model, {}).get("cost", 2), kind, risk, seen, getattr(rates, "recent", {}).get((agent, model), 0),
            critical)
        lower = getattr(rates, "lower", {}).get((agent, model, kind), rate)
        staged.append((index, pid, agent, model, effort, pressure, ranked_pressure, rate, seen, explore, lower))
    best = max((row[10] for row in staged if row[10] is not None), default=None)
    for index, pid, agent, model, effort, pressure, ranked_pressure, rate, seen, explore, lower in staged:
        acc = account_key(pid, agent)
        cost = MODELS.get(model, {}).get("cost", 2) * bt_routing_policy.effort_weight(effort)
        routes.append({"profile": pid, "agent": agent, "model": model, "effort": effort, "tier": tier, "kind": kind,
                       "exploring": explore, "account": acc,
                       "_key": (acc in (busy or ()),
                                agent in (avoid_providers or ()),
                                _role_rank(agent, kind, pressure),
                                *_quality_order(agent, kind, lower, ranked_pressure, seen, explore, critical, best, rate),
                                int(cost / max(lower if lower is not None else 0.5, 0.1)),  # expected cost per verified task
                                int(load.get(acc, 0) // (LOAD_BUCKET_SEC * 2)), index),
                       "why": (("audit budget: Sonnet medium / Opus high; " if agent == "claude" else
                                "audit fallback: Sol medium / high; ") if kind == "audit" else "") +
                              ("critical work: verified quality before quota; " if critical and kind != "audit" else "") +
                              _why(agent, avoid_providers, rate, load.get(acc, 0), lower, seen) +
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


def _why(agent, avoid, rate, load, lower=None, seen: int = 0) -> str:
    bits = []
    if avoid:
        bits.append("other provider than " + "/".join(sorted(avoid)) if agent not in avoid else "same provider")
    bits.append(f"verified task success {rate:.0%} (lower bound {lower:.0%}, {seen} judged)" if rate is not None
                else f"no proven history yet ({seen} judged)")
    bits.append(f"load {int(load // 60)} weighted-min in the last 5 h")
    return "; ".join(bits)


class NoRoute(Exception):
    """Every account of the pool is cooling down; `until` is the earliest reset epoch."""

    def __init__(self, until: float | None):
        super().__init__(f"every account is cooling down until {until}")
        self.until = until or (time.time() + 1800)


def route(project: str, state: dict, tier: int, kind: str = "implement", avoid_providers: set | None = None,
          busy: set | None = None, risk: str | None = None, complexity: str | None = None,
          allow_explore: bool = True) -> dict:
    """The route of one session. Fixed mode (no pool): the run's own agent/profile at the tier's model. Pool mode:
    the best available candidate; raises NoRoute when all accounts are cooling down. The route carries its `decision`
    (bt_explore): exploit, explore (admitted against the persistent budget), fallback (an account was cooling),
    escalation (a failure moved the work) or explicit (a pinned agent)."""
    import bt_explore
    pool = state.get("pool") or []
    if not pool:
        agent = state.get("agent") or "claude"
        model, effort = model_for(agent, tier, kind=kind) if kind == "audit" else legacy_model_for(state, tier)
        return {"profile": state.get("profile"), "agent": agent, "model": model, "effort": effort, "tier": tier,
                "kind": kind, "why": "fixed (no pool)",
                "decision": bt_explore.decision_for("explicit", "the run is pinned to one agent (no pool)")}
    _refresh_google_quota(pool)
    args = (project, pool, tier, kind, state.get("model"), avoid_providers, busy, risk, complexity)
    routes, soonest = candidates(*args, allow_explore=allow_explore)
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
            limit, int(global_limit or 0) or None)
        if record is None:  # the weekly budget is spent (possibly by a concurrent supervisor): rank it as unproven
            routes, soonest = candidates(*args, allow_explore=False)
            chosen = routes[0]
    if record:
        decision = bt_explore.decision_for("explore", record["reason"], record)
    elif avoid_providers and kind != "audit":
        decision = bt_explore.decision_for("escalation", "a failed attempt moved the work to another provider: "
                                           + "/".join(sorted(avoid_providers)) + " avoided")
    elif soonest is not None:
        decision = bt_explore.decision_for("fallback", "an account of the pool is cooling down or exhausted; best "
                                           "admissible route chosen")
    else:
        decision = bt_explore.decision_for("exploit", chosen["why"])
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
    return {"models": [{"id": k, **v} for k, v in MODELS.items()],
            "ladder": {p: [{"tier": i, "model": m, "effort": e} for i, (m, e) in enumerate(rungs)]
                       for p, rungs in LADDER.items()},
            "kinds": list(KINDS), "accounts": accounts,
            "pool": pool_for(project) if project else None}


def brief(project: str | None = None) -> str:
    """Compact markdown of the catalog for prompts and `bitacora.py context`."""
    cat = catalog(project)
    lines = ["### Agents available (any session may delegate to any of them)",
             "| model | provider | tier | use it for |", "|---|---|---|---|"]
    tiers = {}
    for provider, rungs in LADDER.items():
        for i, (m, e) in enumerate(rungs):
            tiers.setdefault(m, []).append(f"{i}{'·' + e if e else ''}")
    for m in cat["models"]:
        lines.append(f"| `{m['id']}` ({m['label']}) | {m['provider']} | {', '.join(tiers.get(m['id'], []))} | {m['use']} |")
    acc = []
    for a in cat["accounts"]:
        if a["profile"] in bt_profiles.DEFAULTS and any(
                account_key(a["profile"]) == account_key(b["profile"]) for b in cat["accounts"] if b is not a):
            continue
        flags = [f for f, on in (("work projects only", a["work_only"]), ("NOT allowed for this project", a["allowed_here"] is False),
                                 (f"usage limit until {a['cooling_until']}", a["cooling_until"]),
                                 ("CLI missing", not a["installed"])) if on]
        acc.append(f"`{a['profile']}` ({a['provider']}{'; ' + '; '.join(flags) if flags else ''})")
    lines.append("Accounts: " + ", ".join(acc) + ".")
    lines.append("Audits: Gemini 3.8 Flash low first (D-004, config audit.provider); fallback Sonnet 5.5 medium; Opus "
                 "5.5 high for demonstrated difficulty/high risk; Codex fallback GPT-6.1 Sol medium. No xhigh/max by "
                 "default; Flash high and medium are not used automatically.")
    return "\n".join(lines)
