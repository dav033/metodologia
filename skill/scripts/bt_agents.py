"""Agent catalog and router: which account, model and effort a piece of work runs with.

The catalog lists the models this toolkit drives (Claude Code and Codex CLIs). A *route* is (profile, agent, model,
effort). Work is described by a capability tier (0 light, 1 standard, 2 top: the escalation ladder) and a kind
(implement, test, docs, audit, research). With a pool of profiles the router picks, among the routes of that tier:
a profile that is allowed for the project and not cooling down after a usage limit, preferably another provider than
the one that just failed (or, for an audit, than the one that built the work), then the best measured success rate,
then the least used account in the current window. Without a pool the run's own profile is used, as before.

Quota state is machine-local (<root>/.state/quota.json): a profile that reported a usage limit is skipped until its
announced reset. Rules for agents: references/agents.md.
"""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import bt_profiles
from bt_core import STATE

PROVIDERS = ("claude", "codex")
KINDS = ("implement", "test", "docs", "audit", "research")
TOP = 2
EFFORTS = ("low", "medium", "high", "xhigh", "max")

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
}
# (model, effort) per provider and tier. Codex always gets an explicit effort: an account's config.toml default may
# name a level the model does not support.
LADDER: dict[str, tuple] = {
    "claude": (("haiku", None), ("sonnet", "xhigh"), ("opus", "xhigh")),
    "codex": (("gpt-6-luna", "medium"), ("gpt-6.1-sol", "high"), ("gpt-6.1-sol", "xhigh")),
}
KIND_TIER = {"audit": 1}  # an audit by a model weaker than the builder proves little
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
        if any(w in text for w in words):
            return kind
    return "implement"


def start_tier(level: str | None, kind: str | None = None, complexity: str | None = None) -> int:
    """Where a task starts on the ladder: architecture-level work at the top; an audit, and work declared large
    (`complexity: L`), at the standard tier; everything else at the light tier."""
    if (level or "").strip().lower() == "architecture":
        return TOP
    return max(KIND_TIER.get(kind or "", 0), 1 if complexity == "L" else 0)


def rank_of(model: str | None) -> int:
    name = (model or "").lower()
    if name in MODELS:
        return MODELS[name]["rank"]
    return 2 if "opus" in name else 1 if ("sonnet" in name or "sol" in name) else 0


def provider_of_model(model: str | None) -> str | None:
    name = (model or "").lower()
    if name in MODELS:
        return MODELS[name]["provider"]
    if any(w in name for w in ("opus", "sonnet", "haiku", "claude")):
        return "claude"
    return "codex" if name.startswith(("gpt", "codex", "o3", "o4")) else None


def model_for(provider: str, tier: int, configured: str | None = None, kind: str | None = None
              ) -> tuple[str | None, str | None]:
    """(model, effort) of `provider` at `tier`. A configured model of the same provider that is at least as strong as
    the tier's is kept (only the effort follows the ladder). Documentation never needs more than low effort at tier 0."""
    tier = max(0, min(TOP, int(tier or 0)))
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
    """Accounts are what quotas belong to: two profile ids selecting the same account share one key."""
    if not profile:
        return f"{agent or 'claude'}:default"
    try:
        spec = bt_profiles.get(profile)
    except SystemExit:
        return profile
    env = sorted((spec.get("env") or {}).items())
    return f"{spec['provider']}:" + (",".join(f"{k}={v}" for k, v in env) if env else "default")


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
        if spec["provider"] not in PROVIDERS or account_key(pid) in seen:
            continue
        if spec.get("work_only") and not bt_profiles.is_work_project(project):
            continue
        if not shutil.which(spec.get("bin") or spec["provider"]):
            continue
        env = bt_profiles.env_of(pid)
        if any(k in env and not Path(env[k]).is_dir() for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME")):
            continue
        seen.add(account_key(pid))
        out.append(pid)
    return out


def _stats() -> tuple[dict, dict]:
    """(success rate by (agent, model, kind) with enough samples, seconds used per account in the load window)."""
    try:
        import bt_events
        rows = bt_events.read_all()
    except Exception:
        return {}, {}
    import datetime as dt
    counts: dict[tuple, list[int]] = {}
    load: dict[str, float] = {}
    now = time.time()
    for r in rows:
        res = r.get("result")
        if res in ("usage_limit", "limit_streak", "stopped", "skipped"):
            continue
        key = (r.get("agent"), r.get("model"), r.get("kind") or "implement")
        c = counts.setdefault(key, [0, 0])
        c[0] += 1
        c[1] += res in ("done", "verified")
        try:
            age = now - dt.datetime.fromisoformat(r["ts"]).timestamp()
        except (KeyError, ValueError, TypeError):
            continue
        if 0 <= age <= LOAD_WINDOW_SEC:
            acc = account_key(r.get("profile"), r.get("agent"))
            cost = MODELS.get(str(r.get("model")), {}).get("cost", 2)
            load[acc] = load.get(acc, 0) + (r.get("seconds") or 0) * cost
    rates = {k: c[1] / c[0] for k, c in counts.items() if c[0] >= MIN_SAMPLES}
    return rates, load


def candidates(project: str, pool: list[str], tier: int, kind: str = "implement", configured: str | None = None,
               avoid_providers: set | None = None, busy: set | None = None) -> tuple[list[dict], float | None]:
    """(routes of `tier` ordered best first, earliest epoch a cooling account frees up when none is available).
    `busy`: account keys already taken by sessions being started in the same batch (they go last)."""
    rates, load = _stats()
    profiles = bt_profiles.load()
    routes, soonest = [], None
    for index, pid in enumerate(pool):
        spec = profiles.get(pid)
        if not spec or spec["provider"] not in PROVIDERS:
            continue
        agent = spec["provider"]
        if spec.get("work_only") and not bt_profiles.is_work_project(project):
            continue  # a pool saved while the project was work must not outlive that flag
        until = cooling_until(pid, agent)
        if until:
            soonest = until if soonest is None else min(soonest, until)
            continue
        model, effort = model_for(agent, tier, configured, kind)
        rate = rates.get((agent, model, kind))
        routes.append({"profile": pid, "agent": agent, "model": model, "effort": effort, "tier": tier, "kind": kind,
                       "_key": (account_key(pid, agent) in (busy or ()), agent in (avoid_providers or ()),
                                -(round(rate * 5) if rate is not None else 3),
                                int(load.get(account_key(pid, agent), 0) // (LOAD_BUCKET_SEC * 2)), index),
                       "why": _why(agent, avoid_providers, rate, load.get(account_key(pid, agent), 0))})
    # The rate is compared in 20-point bands on purpose: a few points of difference over a handful of attempts is
    # noise, and a tie hands the choice to quota balancing (load, then pool order).
    routes.sort(key=lambda r: r["_key"])
    for r in routes:
        r.pop("_key")
    return routes, soonest


def _why(agent, avoid, rate, load) -> str:
    bits = []
    if avoid:
        bits.append("other provider than " + "/".join(sorted(avoid)) if agent not in avoid else "same provider (no alternative)")
    bits.append(f"success {rate:.0%}" if rate is not None else "no history yet")
    bits.append(f"load {int(load // 60)} weighted-min in the last 5 h")
    return "; ".join(bits)


class NoRoute(Exception):
    """Every account of the pool is cooling down; `until` is the earliest reset epoch."""

    def __init__(self, until: float | None):
        super().__init__(f"every account is cooling down until {until}")
        self.until = until or (time.time() + 1800)


def route(project: str, state: dict, tier: int, kind: str = "implement", avoid_providers: set | None = None,
          busy: set | None = None) -> dict:
    """The route of one session. Fixed mode (no pool): the run's own agent/profile at the tier's model. Pool mode:
    the best available candidate; raises NoRoute when all accounts are cooling down."""
    pool = state.get("pool") or []
    if not pool:
        agent = state.get("agent") or "claude"
        model, effort = legacy_model_for(state, tier)
        return {"profile": state.get("profile"), "agent": agent, "model": model, "effort": effort, "tier": tier,
                "kind": kind, "why": "fixed (no pool)"}
    routes, soonest = candidates(project, pool, tier, kind, state.get("model"), avoid_providers, busy)
    if not routes:
        if soonest is None:  # nothing is cooling: no account of the pool may run this project any more
            raise bt_profiles.ProfileError(f"No account of the pool ({', '.join(pool)}) may run '{project}'. "
                                           f"Check: bitacora.py --project {project} agents")
        raise NoRoute(soonest)
    return routes[0]


def legacy_model_for(state: dict, tier: int) -> tuple[str | None, str | None]:
    """A run pinned to one agent. Claude: the configured model at tier 0 (haiku by default), the ladder above it.
    Codex: a configured Codex model is kept and only the effort rises (xhigh from tier 1); with no Codex model
    configured the CLI's own default model runs."""
    agent, configured = state.get("agent") or "claude", state.get("model")
    if agent == "codex":
        model = configured if configured and provider_of_model(configured) != "claude" else None
        return model, ("xhigh" if tier >= 1 else None)
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
    return "\n".join(lines)
