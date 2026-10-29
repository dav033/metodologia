"""Quota-first routing restricted to the owner's selected role configurations."""
from __future__ import annotations

import contextlib
import datetime as dt
import json
import sqlite3
import time

import bt_role_policy as policy
import bt_routing_policy as quota_policy

LOAD_WINDOW_SECONDS = 5 * 3600  # one quota window: sessions older than this no longer weigh on the account
LOAD_POINTS = 4.0  # pressure-equivalent points one recent session adds when ranking, so a plan's sessions spread out
LOAD_CAP = 40.0


def recent_sessions(now: float) -> dict[str, int]:
    """Sessions started in the last quota window per account key, from the attempt log and from every scheduler
    executor ledger (running sessions included). Quota is account-wide, so every project counts. Never raises: no
    history, no spread."""
    import bt_agents
    import bt_events

    counts: dict[str, int] = {}
    keys: dict[tuple, str] = {}

    def add(profile, provider) -> None:
        if not profile:
            return
        ident = (profile, provider)
        if ident not in keys:
            keys[ident] = bt_agents.account_key(*ident)
        counts[keys[ident]] = counts.get(keys[ident], 0) + 1

    try:
        for row in bt_events.read_all():
            at = dt.datetime.fromisoformat(str(row.get('ts')))
            if row.get('origin') != 'synthetic' and now - at.timestamp() <= LOAD_WINDOW_SECONDS:
                add(row.get('profile'), row.get('agent'))
    except (OSError, ValueError, TypeError):
        pass
    # Scheduler runs keep their sessions in the executor ledgers, running ones included.
    try:
        ledgers = sorted((bt_agents.STATE / 'executor').glob('*/ledger.db'))
    except OSError:
        ledgers = []
    for ledger in ledgers:
        try:
            with contextlib.closing(sqlite3.connect(f'{ledger.resolve().as_uri()}?mode=ro', uri=True, timeout=0.2)) as db:
                rows = db.execute('SELECT route FROM attempts WHERE created >= ? AND rejection IS NULL',
                                  (now - LOAD_WINDOW_SECONDS,)).fetchall()
            for (raw,) in rows:
                route = json.loads(raw) if raw else {}
                if isinstance(route, dict):
                    add(route.get('profile'), route.get('provider'))
        except (sqlite3.Error, OSError, ValueError, TypeError):
            continue
    return counts


def candidates(project, pool, tier, kind, role, configured=None, avoid_providers=None,
               busy=None, complexity=None, effort=None, escalated=False):
    import bt_agents as agents
    import bt_profiles
    import bt_subscriptions

    choices = policy.options(role, complexity, escalated=escalated)
    if configured:
        provider = agents.provider_of_model(configured)
        choices = [(p, configured, effort or e) for p, _, e in choices if p == provider]
    samples = bt_subscriptions.load(agents.STATE)
    profiles = bt_profiles.load()
    rows, seen, soonest = [], set(), None
    now = time.time()
    load = recent_sessions(now)
    for index, pid in enumerate(pool):
        spec = profiles.get(pid)
        if not spec or spec.get('work_only') and not bt_profiles.is_work_project(project):
            continue
        identity = agents._pool_account_identity(pid, spec)
        if identity in seen:
            continue
        seen.add(identity)
        provider = spec['provider']
        for priority, (candidate_provider, model, selected_effort) in enumerate(choices):
            if candidate_provider != provider:
                continue
            acc = agents.account_key(pid, provider)
            pressure, exhausted = bt_subscriptions.capacity(samples.get(acc), model)
            deadlines = [d for d in (agents.cooling_until(pid, provider), exhausted) if d is not None]
            if deadlines:
                until = max(deadlines)
                soonest = until if soonest is None else min(soonest, until)
                continue
            ranked = quota_policy.paced_pressure(
                pressure, quota_policy.weekly_pace_surplus(samples.get(acc), now))
            used = load.get(acc, 0)
            effective = min(100.0, (quota_policy.UNKNOWN_PRESSURE if ranked is None else ranked) +
                            min(LOAD_CAP, LOAD_POINTS * used))
            rows.append({'profile': pid, 'agent': provider, 'model': model,
                         'effort': effort or selected_effort, 'tier': tier, 'kind': kind, 'role': role,
                         'account': acc, 'exploring': False, 'evidence': {'kind': 'none', 'samples': 0},
                         '_pressure': ranked, '_effective': effective, '_load': used,
                         '_priority': priority, '_index': index,
                         '_blocked': quota_policy.subscription_blocked(samples.get(acc)),
                         '_busy': acc in (busy or ()),
                         '_avoid': provider in (avoid_providers or ()) and (kind == 'audit' or role in ('reviewer', 'antagonist')),
                         'why': f'owner role {role}; ' + ('high complexity; ' if policy.high_complexity(complexity) else '') +
                         (f'subscription bottleneck {pressure:g}% used' if pressure is not None else
                          'subscription usage unknown/stale')})
    # A family is as available as its best eligible account. Multiple aliases never add headroom.
    family = {}
    for row in rows:
        value = (row['_blocked'], row['_busy'], row['_effective'])
        family[row['agent']] = min(family.get(row['agent'], value), value)
    def key(row):
        score = family[row['agent']]
        high_pressure = score[2] >= quota_policy.HIGH_PRESSURE
        # High complexity, and the roles the owner ordered (Designer: Opus first, D-151), follow the owner's order for
        # the role while quota allows it (Implementer: Sonnet first when complex)
        ordered = policy.high_complexity(complexity) or role in policy.ORDERED_ROLES
        complexity_priority = row['_priority'] if ordered else 0
        return (row['_blocked'], row['_busy'], row['_avoid'],
                row['_pressure'] is not None and row['_pressure'] >= quota_policy.HIGH_PRESSURE,
                score[0], score[1], high_pressure,
                complexity_priority, quota_policy.pressure_bucket(score[2]),
                quota_policy.pressure_bucket(row['_effective']), row['_load'], row['_priority'], row['_index'])
    rows.sort(key=key)
    for row in rows:
        for name in list(row):
            if name.startswith('_'):
                del row[name]
    return rows, soonest
