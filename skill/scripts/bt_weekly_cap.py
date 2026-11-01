"""The owner's weekly cap (D-279): an account at or above `routing.weekly_cap_percent` (default 90) of its WEEKLY quota
is not used by metodologia any more, whoever "owns" the work.

Owner, 2026-10-31: «cuando una cuenta tenga 90% de la cuota semanal no se tenga en cuenta ni se use más en metodologia
sin importar que una tarea tenga dicha cuenta como la propietaria, se debe rutear».

The weekly number is the account-wide seven-day window (`windows.seven_day.used_percent`) of the readings metodologia
already keeps: the hourly/route-time samples in `<state>/subscription-usage.json` (`bt_subscriptions.load`, keyed by
`bt_agents.account_key`) and the live rows of `bt_quota_live` (globalusage, the durable `LiveQuota`). Nothing here
contacts a provider: every caller hands in a row it already read.

A reading counts while its window has not reset: within one seven-day window usage only grows, so an older reading of
that same window is a lower bound of the account's use now. A reading whose window already reset, a window the API did
not give a reset for that is no longer fresh, a missing or malformed seven-day window or no sample at all is UNKNOWN:
never excluded (missing data must not stop work), logged once per process and account.

Only Claude and Codex accounts are capped (Antigravity's Google pool has its own capacity rules in `bt_agy`).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import math
import os
import time
from dataclasses import dataclass
from pathlib import Path

LOG = logging.getLogger("bt_weekly_cap")
DEFAULT_PERCENT = 90.0
CAPPED_PROVIDERS = ("claude", "codex")
FRESH_SECONDS = 7200          # a window without a reset time is believed this long (bt_subscriptions.MAX_AGE_SECONDS)
UNKNOWN_RESET_RETRY = 3600    # a capped account whose reset is unknown is looked at again after the next hourly poll
RECORD_EVERY = 3600           # the same exclusion, in the same place, to the same account, is written once an hour
_noted: set[tuple[str, str]] = set()
_recorded: dict[tuple, float] = {}


def threshold() -> float:
    """`routing.weekly_cap_percent` (default 90). A value above 100 can never be reached: the cap is then off. A
    missing, non-numeric or non-positive value keeps the default."""
    try:
        import bt_config
        value = bt_config.get("routing.weekly_cap_percent", DEFAULT_PERCENT)
    except Exception:  # noqa: BLE001 - no configuration readable: the owner's default
        return DEFAULT_PERCENT
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return DEFAULT_PERCENT
    return float(value)


@dataclass(frozen=True)
class Cap:
    """One account's weekly-cap verdict. `state`: capped | under | unknown. `resets_at`: when the capped week ends (None
    when the API did not say). `why`: what made an unknown verdict unknown."""
    state: str
    used_percent: float | None = None
    resets_at: float | None = None
    threshold: float = DEFAULT_PERCENT
    why: str = ""

    @property
    def capped(self) -> bool:
        return self.state == "capped"

    def until(self, now: float | None = None) -> float:
        """When to look at this account again: its weekly reset, else after the next poll."""
        now = time.time() if now is None else now
        return self.resets_at if self.resets_at and self.resets_at > now else now + UNKNOWN_RESET_RETRY


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def check(row: object, now: float | None = None, limit: float | None = None) -> Cap:
    """The verdict for one reading (a `subscription-usage.json` account row or a `bt_quota_live` row)."""
    now = time.time() if now is None else now
    limit = threshold() if limit is None else float(limit)
    if not isinstance(row, dict):
        return Cap("unknown", threshold=limit, why="no_sample")
    windows = row.get("windows")
    week = windows.get("seven_day") if isinstance(windows, dict) else None
    if not isinstance(week, dict):
        return Cap("unknown", threshold=limit, why="no_weekly_window")
    used = _number(week.get("used_percent"))
    if used is None or not 0 <= used <= 100:
        return Cap("unknown", threshold=limit, why="invalid_weekly_window")
    reset = week.get("resets_at")
    if reset is not None:
        reset = _number(reset)
        if reset is None:
            return Cap("unknown", used, threshold=limit, why="invalid_weekly_window")
        if reset <= now:
            return Cap("unknown", used, threshold=limit, why="weekly_window_reset_since_reading")
    else:
        observed = _number(row.get("observed_at"))
        if row.get("status") != "ok" or observed is None or not 0 <= now - observed <= FRESH_SECONDS:
            return Cap("unknown", used, threshold=limit, why="stale_reading_without_reset")
    return Cap("capped" if used >= limit else "under", used, reset, limit)


def note_unknown(account: str, cap: Cap) -> None:
    """Unknown weekly usage is never a reason to exclude; it is logged once per process and account."""
    if cap.state != "unknown" or (account, cap.why) in _noted:
        return
    _noted.add((account, cap.why))
    LOG.info("weekly usage of %s unknown (%s): not excluded by the weekly cap", account, cap.why)


def live_row(profile: str | None) -> dict | None:
    """The profile's row in the live cache `globalusage` and the durable engine write (`bt_quota_live`), read from disk
    only: no provider call. None when there is no such cache or row."""
    if not profile:
        return None
    try:
        from bt_core import STATE
        rows = json.loads((Path(STATE) / "globalusage-cache.json").read_text(encoding="utf-8")).get("rows")
    except (OSError, ValueError, AttributeError):
        return None
    found = next((r for r in rows or () if isinstance(r, dict) and r.get("profile") == profile), None)
    return found


def newest(*caps: Cap) -> Cap:
    """Several readings of one account: usage only grows within a week, so the highest known one is the truest."""
    known = [c for c in caps if c.state != "unknown"]
    return max(known, key=lambda c: c.used_percent or 0.0) if known else caps[0]


def for_account(samples: dict, key: str, now: float | None = None, limit: float | None = None,
                profile: str | None = None) -> Cap:
    """The verdict for the account stored under `key` in `subscription-usage.json` (already loaded by the caller) and,
    with `profile`, its row in the live cache: the stored sample can lag when its hourly poll keeps failing."""
    cap = check(samples.get(key) if hasattr(samples, "get") else None, now, limit)
    if profile:
        cap = newest(cap, check(live_row(profile), now, cap.threshold))
    note_unknown(key, cap)
    return cap


def for_profile(profile: str | None, provider: str | None = None, samples: dict | None = None,
                now: float | None = None) -> Cap:
    """The verdict for a profile's account, from the stored samples (read here when not given)."""
    import bt_agents
    import bt_profiles
    if provider is None:
        try:
            provider = bt_profiles.provider_of(profile) if profile else "claude"
        except SystemExit:
            return Cap("unknown", threshold=threshold(), why="unknown_profile")
    if provider not in CAPPED_PROVIDERS:
        return Cap("unknown", threshold=threshold(), why="provider_not_capped")
    if samples is None:
        import bt_subscriptions
        samples = bt_subscriptions.load(bt_agents.STATE)
    return for_account(samples, bt_agents.account_key(profile, provider), now, profile=profile or provider)


def profiles_for_home(provider: str, home: str | None) -> list[str]:
    """Profiles whose account is the config directory / Codex home `home` ("" = the provider's default directory)."""
    import bt_agents
    import bt_profiles
    default = {"claude": ".claude", "codex": ".codex"}.get(provider)
    if not default:
        return []
    target = os.path.normpath(os.path.expanduser(home)) if home else os.path.normpath(str(Path.home() / default))
    found = []
    for pid, spec in bt_profiles.load().items():
        if spec.get("provider") != provider:
            continue
        try:
            _, selectors = bt_agents._pool_account_identity(pid, spec)
        except SystemExit:
            continue
        if any(value == target for _, value in selectors):
            found.append(pid)
    return sorted(found, key=lambda p: (p in bt_profiles.DEFAULTS, p))


def for_home(provider: str, home: str | None, samples: dict | None = None, now: float | None = None
             ) -> tuple[Cap, str]:
    """(verdict, profile name) for an account given by its directory, as long-lived sessions and pins name it. Several
    profiles of one account: the highest known weekly use counts. No profile describes it: unknown."""
    profiles = profiles_for_home(provider, home)
    best, name = Cap("unknown", threshold=threshold(), why="no_profile_for_account"), home or provider
    for pid in profiles:
        cap = for_profile(pid, provider, samples, now)
        if cap.state != "unknown" and (best.state == "unknown" or (cap.used_percent or 0) > (best.used_percent or 0)):
            best, name = cap, pid
        elif best.state == "unknown" and name == (home or provider):
            name = pid
    return best, name


def percent(cap: Cap) -> str:
    value = cap.used_percent or 0.0
    return f"{value:.0f}" if float(value).is_integer() or value >= 10 else f"{value:.1f}"


def line(account: str, cap: Cap, rerouted_to: str | None) -> str:
    """The activity/telemetry line the owner reads (Spanish, as the panel)."""
    where = f"se ruteó a {rerouted_to}" if rerouted_to else "ninguna otra cuenta disponible"
    return f"{account} excluida: {percent(cap)} % de la cuota semanal; {where}"


def entry(account: str, cap: Cap, profile: str | None = None) -> dict:
    return {"account": account, "profile": profile or account, "used_percent": cap.used_percent,
            "resets_at": cap.resets_at, "threshold": cap.threshold}


def record(excluded: list[dict], rerouted_to: str | None, context: str, **fields) -> list[str]:
    """Record a decision the cap changed: one line per excluded account in the log and in
    `<state>/events/weekly-cap-YYYY-MM.jsonl`. Returns the lines. Never raises: telemetry never changes a decision."""
    lines = []
    for item in excluded:
        cap = Cap("capped", item.get("used_percent"), item.get("resets_at"), item.get("threshold") or DEFAULT_PERCENT)
        lines.append(line(str(item.get("profile") or item.get("account")), cap, rerouted_to))
    if not lines:
        return lines
    now = time.time()
    fresh = [(item, text) for item, text in zip(excluded, lines)
             if now - _recorded.get((context, text), 0.0) >= RECORD_EVERY]
    if not fresh:
        return lines
    for item, text in fresh:
        _recorded[(context, text)] = now
        LOG.warning("%s (%s)", text, context)
    try:
        from bt_core import STATE
        folder = Path(STATE) / "events"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"weekly-cap-{dt.datetime.now(dt.UTC):%Y-%m}.jsonl"
        stamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        with path.open("a", encoding="utf-8") as stream:
            for item, text in fresh:
                stream.write(json.dumps({"ts": stamp, "context": context, "rerouted_to": rerouted_to, **item,
                                         "line": text, **fields}, ensure_ascii=False) + "\n")
    except Exception as error:  # noqa: BLE001 - best effort
        LOG.debug("weekly cap event not written: %s", error)
    return lines


def reason(excluded: list[dict]) -> str:
    """Why nothing could run when every account is capped (English, as NoRoute and route reasons)."""
    names = ", ".join(f"{item.get('profile') or item.get('account')} {percent(Cap('capped', item.get('used_percent')))}%"
                      for item in excluded)
    limit = excluded[0].get("threshold") if excluded else DEFAULT_PERCENT
    return f"weekly cap: {names} at or above {float(limit or DEFAULT_PERCENT):g}% of the weekly quota (D-279)"


# ------------------------------------------------------------------ applying it where an account is picked

class Routes(list):
    """The ranked routes of `bt_agents.candidates`, plus `weekly_capped`: the accounts the cap left out (`entry` rows),
    so the caller that takes the decision can say where the work went instead."""

    def __init__(self, rows=(), weekly_capped: list | None = None):
        super().__init__(rows)
        self.weekly_capped = list(weekly_capped or [])


class Exclusions:
    """The cap inside one candidates() pass: `skip` says whether an account is left out (and until when)."""

    def __init__(self, samples: dict, now: float | None = None):
        self.samples, self.now, self.limit, self.capped = samples, time.time() if now is None else now, threshold(), []

    def skip(self, profile: str, provider: str, key: str, counted: bool = True) -> float | None:
        """None when the account may be a candidate; else the epoch to look at it again (its weekly reset)."""
        if provider not in CAPPED_PROVIDERS:
            return None
        cap = for_account(self.samples, key, self.now, self.limit, profile)
        if not cap.capped:
            return None
        if counted:
            self.capped.append(entry(key, cap, profile))
        return cap.until(self.now)

    def routes(self, rows: list) -> Routes:
        return Routes(rows, self.capped)


def no_route(capped: list[dict], context: str) -> str:
    """NoRoute's reason when the cap left accounts out of a pool that has no route ("" otherwise); recorded."""
    if not capped:
        return ""
    record(capped, None, context)
    return reason(capped)


def annotate(chosen: dict, decision: dict, capped: list[dict], context: str) -> None:
    """A route chosen while the cap left accounts out: the decision and the route's `why` say where the work went."""
    if not capped:
        return
    lines = record(capped, chosen.get("profile") or chosen.get("agent"), context)
    decision["weekly_cap"] = capped
    decision["why"] = "; ".join([*lines, str(decision.get("why") or "")]).strip("; ")
    chosen["why"] = "; ".join([*lines, str(chosen.get("why") or "")]).strip("; ")


def reroute_pin(project: str, state: dict, tier: int, kind: str, role: str | None, effort: str | None,
                complexity: str | None, escalated: bool) -> dict | None:
    """A run pinned to one account (`route` without a pool) whose account is over the cap: the work goes to the best
    eligible account of the project's pool (`routing.pool` or every allowed account). None when the pin is not capped;
    raises `bt_agents.NoRoute` naming the cap when no other account can take it."""
    import bt_agents
    import bt_explore
    import bt_profiles
    agent = state.get("agent") or "claude"
    if agent not in CAPPED_PROVIDERS:
        return None
    pinned = state.get("profile")
    cap = for_profile(pinned, agent)
    if not cap.capped:
        return None
    own = bt_agents.account_key(pinned, agent)
    try:
        pool = [p for p in bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
                if bt_agents.account_key(p) != own]
    except bt_profiles.ProfileError:
        pool = []
    routes, soonest = (bt_agents.candidates(project, pool, tier, kind, None, None, None, None, complexity,
                                            allow_explore=False, effort=effort, role=role, escalated=escalated)
                       if pool else (Routes(), None))
    excluded = [entry(own, cap, pinned or agent), *getattr(routes, "weekly_capped", [])]
    context = f"route {project} {kind} (pinned {pinned or agent})"
    if not routes:
        raise bt_agents.NoRoute(min(t for t in (soonest, cap.until()) if t), no_route(excluded, context))
    chosen = {k: v for k, v in routes[0].items() if k != "exploring"}
    decision = bt_explore.decision_for("fallback", "the run's pinned account is over the weekly cap")
    decision["evidence"] = chosen.get("evidence")
    annotate(chosen, decision, excluded, context)
    return {**chosen, "role": chosen.get("role") or role, "decision": decision}


def reroute_profile(project: str, profile: str, context: str) -> str:
    """A profile a caller is configured to use (`diagnosis.profile`: the block diagnosis, the attempt analyst, the manual
    reviewer, the recovery Planner) whose account is over the cap gives way to the first eligible account of the SAME
    provider in the project's pool (the configured model belongs to that provider). The profile itself when it is not
    capped; raises `bt_profiles.ProfileError` naming the cap when no other account can take it."""
    import bt_agents
    import bt_profiles
    import bt_subscriptions
    provider = bt_profiles.provider_of(profile)
    if provider not in CAPPED_PROVIDERS:
        return profile
    samples = bt_subscriptions.load(bt_agents.STATE)
    cap = for_profile(profile, provider, samples)
    if not cap.capped:
        return profile
    own = bt_agents.account_key(profile, provider)
    excluded = [entry(own, cap, profile)]
    try:
        pool = bt_agents.pool_for(project, bt_agents._config("routing.pool", []) or None)
    except bt_profiles.ProfileError:
        pool = []
    for pid in pool:
        key = bt_agents.account_key(pid, provider)
        if bt_profiles.provider_of(pid) != provider or key == own:
            continue
        other = for_profile(pid, provider, samples)
        if other.capped:
            excluded.append(entry(key, other, pid))
            continue
        record(excluded, pid, context)
        return pid
    raise bt_profiles.ProfileError(no_route(excluded, context))


def pinned(profile: str | None, agent: str | None) -> tuple[Cap, str] | None:
    """(verdict, profile) when the account a delegation is pinned to (`--profile`, or the ambient account of `--agent`)
    is over the cap, else None."""
    import bt_profiles
    try:
        provider = bt_profiles.provider_of(profile) if profile else agent
        if provider not in CAPPED_PROVIDERS:
            return None
        pid = profile or bt_profiles.ambient(provider)
        cap = for_profile(pid, provider) if pid else None
    except SystemExit:
        return None
    return (cap, pid) if cap is not None and cap.capped else None


def reroute_order(order: dict) -> str:
    """Before a delegation's attempt: its account crossed the cap. The order moves to the router's best eligible
    account (`order` updated in place, the move recorded) and "" is returned; when the cap leaves no account, its reason
    is returned and the caller ends the delegation like one whose accounts are all spent."""
    import bt_agents
    found = pinned(order.get("profile"), order.get("agent"))
    if found is None:
        return ""
    cap, pid = found
    own = bt_agents.account_key(pid)
    tier = order.get("tier") if order.get("tier") is not None else bt_agents.start_tier(None, order.get("kind"))
    pool = [p for p in bt_agents.pool_for(order["project"], bt_agents._config("routing.pool", []) or None)
            if bt_agents.account_key(p) != own]
    routes, _ = (bt_agents.candidates(order["project"], pool, tier, order.get("kind") or "implement",
                                      allow_explore=False, effort=order.get("requested_effort"),
                                      configured=order.get("requested_model"), role=order.get("role"),
                                      complexity=order.get("complexity")) if pool else (Routes(), None))
    excluded = [entry(own, cap, pid), *getattr(routes, "weekly_capped", [])]
    if not routes:
        return no_route(excluded, f"delegation {order['id']}")
    nxt = routes[0]
    lines = record(excluded, nxt.get("profile") or nxt["agent"], f"delegation {order['id']}")
    order.update(profile=nxt["profile"], agent=nxt["agent"], model=nxt["model"], effort=nxt["effort"], auto=True,
                 routed="; ".join([*lines, str(nxt.get("why") or "")]).strip("; "),
                 weekly_cap=[*order.get("weekly_cap", []), *lines])
    return ""
