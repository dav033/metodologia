"""Read model of every attempt of a Scheduler run: who ran it, for how long, with how many tokens.

M1 cannot name models (its boundary is tested), so the per-attempt record is assembled here from three read-only
sources: the M1 state document (attempt number/state/timing and the opaque `executor` reference), the M2 ledger
(`executor` -> provider/model/profile/effort) and the M4 store (provider-reported tokens, observed model, last stream
activity). Nothing is written or created, and nothing is invented: what a source did not report is None, never 0.

    attempt_facts(rdir, now=None) -> {task_id: [AttemptFacts, ...]}   # oldest attempt first
    AttemptFacts = {attempt, task, number, state, live, started_at, ended_at, duration_s, last_activity_at,
        route: {provider, model, effort, profile, account_ref, source}, model_reported,
        tokens: {input, output, total, source} | None, cost_usd, failure, verdict, verifier}
"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

import bt_run_stores
import bt_scheduler_adapter as scheduler_
import bt_scheduler_monitor_adapter as monitor_

TERMINAL = ("accepted", "failed", "rejected", "cancelled")
LIVE = ("running", "verifying")


def iso(epoch: Any) -> str | None:
    if isinstance(epoch, bool) or not isinstance(epoch, (int, float)) or epoch <= 0:
        return None
    return dt.datetime.fromtimestamp(epoch, dt.UTC).isoformat(timespec="seconds")


def _epoch(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if value > 0 else None
    try:
        return dt.datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def core_document(db: Path) -> dict[str, Any]:
    """The M1 state document through a `mode=ro` connection; {} when unreadable (locked, absent, corrupt)."""
    try:
        conn = sqlite3.connect(f"{Path(db).resolve().as_uri()}?mode=ro", uri=True, timeout=0.2)
        try:
            row = conn.execute("SELECT doc FROM state WHERE id = 1").fetchone()
        finally:
            conn.close()
        doc = json.loads(row[0]) if row else {}
    except (sqlite3.Error, OSError, ValueError):
        return {}
    return doc if isinstance(doc, dict) else {}


_routes: dict[tuple[str, str], dict[str, Any]] = {}     # (M2 ledger, reference) -> route: a recorded decision never changes
ROUTES_MAX = 4096


def _route(ledger: Path | None, reference: Any) -> dict[str, Any]:
    blank = {"provider": None, "model": None, "effort": None, "profile": None, "account_ref": None, "source": None}
    if ledger is None or not isinstance(reference, str) or not reference:
        return blank
    key = (str(ledger), reference)
    if key in _routes:
        return dict(_routes[key])
    try:
        raw = scheduler_.resolve_m2_route(ledger, reference)
    except Exception:                                   # a missing/locked/foreign ledger only blanks the route
        return blank
    if not raw:
        return blank                                    # not cached: the decision may not be written yet
    route = {"provider": raw.get("provider") or None, "model": raw.get("model") or None,
             "effort": raw.get("effort") or None, "profile": raw.get("profile") or None,
             "account_ref": raw.get("account_ref") or None, "source": "m2-ledger"}
    if len(_routes) >= ROUTES_MAX:
        _routes.clear()
    _routes[key] = route
    return dict(route)


def _observed_fallback(route: dict[str, Any], seen: dict[str, Any]) -> dict[str, Any]:
    """With no resolvable M2 reference, say what M4 saw instead of nothing (effort stays unknown: M4 never sees it)."""
    if route["source"] or not (seen.get("provider") or seen.get("model")):
        return route
    return {**route, "provider": seen.get("provider") or None, "model": seen.get("model") or None,
            "profile": seen.get("profile_id") or None, "source": "m4-observed"}


def _tokens(usage: dict[str, Any] | None) -> dict[str, Any] | None:
    """What the provider reported, as reported. A total is never computed here: providers disagree on what it contains
    (Claude excludes cache reads, Codex's input includes them), so `total` is None unless M4 saw a total metric."""
    by_metric = (usage or {}).get("tokens_by_metric") or {}
    tin, tout, total = (by_metric.get(k) for k in ("input_tokens", "output_tokens", "total_tokens"))
    if tin is None and tout is None and total is None:
        return None
    return {"input": tin, "output": tout, "total": total, "source": "provider_reported"}


_usage: dict[tuple[str, int], tuple[int, dict[str, dict[str, Any]]]] = {}   # (M4 path, inode) -> (rowid, totals)
_usage_lock = threading.Lock()


def _fold_usage(into: dict[str, dict[str, Any]], new: dict[str, dict[str, Any]]) -> None:
    """Add a later window of M4 rows to the per-attempt totals already held (same shape as `attempt_summaries`)."""
    for aid, item in new.items():
        held = into.get(aid)
        if held is None:
            into[aid] = {**item, "tokens_by_metric": dict(item.get("tokens_by_metric") or {})}
            continue
        held["events"] = int(held.get("events") or 0) + int(item.get("events") or 0)
        held["token_samples"] = int(held.get("token_samples") or 0) + int(item.get("token_samples") or 0)
        for name in ("provider", "profile_id", "model", "last_received_at"):
            if item.get(name):
                held[name] = item[name]
        if item.get("tokens_total") is not None:
            held["tokens_total"] = int(held.get("tokens_total") or 0) + int(item["tokens_total"])
        for metric, value in (item.get("tokens_by_metric") or {}).items():
            held["tokens_by_metric"][metric] = int(held["tokens_by_metric"].get(metric, 0)) + int(value)


def usage_by_attempt(rdir: Path) -> dict[str, dict[str, Any]]:
    """Per-attempt usage from M4, read incrementally: a long run's stream is decoded once, then only its new rows."""
    m4 = bt_run_stores.paths(rdir).get("m4")
    if m4 is None or not Path(m4).exists():
        return {}
    try:
        key = (str(Path(m4).resolve()), Path(m4).stat().st_ino)
        with _usage_lock:                               # held only to copy and to store: decoding runs unlocked
            cursor, totals = _usage.get(key, (0, {}))
            totals = {aid: {**item, "tokens_by_metric": dict(item["tokens_by_metric"])} for aid, item in totals.items()}
        while True:
            window = monitor_.attempt_usage(m4, since_rowid=cursor)
            _fold_usage(totals, dict(window.get("attempts") or {}))
            cursor = int(window.get("cursor") or cursor)
            if not window.get("truncated"):
                break
        with _usage_lock:
            if cursor >= _usage.get(key, (0, {}))[0]:   # two readers raced: the further one wins
                _usage[key] = (cursor, totals)
        return {aid: {**item, "tokens_by_metric": dict(item["tokens_by_metric"])} for aid, item in totals.items()}
    except Exception:                                   # M4 is an observer: if it is unreadable, report no usage
        return {}


def build(doc: dict[str, Any], ledger: Path | None, usage: dict[str, dict[str, Any]],
          now: float | None = None) -> dict[str, list[dict[str, Any]]]:
    now = time.time() if now is None else now
    attempts, tasks = doc.get("attempts"), doc.get("tasks")
    if not isinstance(attempts, dict) or not isinstance(tasks, dict):
        return {}
    out: dict[str, list[dict[str, Any]]] = {}
    for tid, rec in tasks.items():
        if not isinstance(rec, dict):
            continue
        rows = []
        for aid in rec.get("attempts") or []:
            a = attempts.get(aid)
            if not isinstance(a, dict):
                continue
            seen = usage.get(aid) or {}
            started, state = _epoch(a.get("created_at")), a.get("state")
            ended = _epoch(a.get("updated_at")) if state in TERMINAL else None
            if started is None:
                duration = None
            else:
                duration = round(max(0.0, (ended if ended is not None else now) - started), 1)
            beat = [t for t in (_epoch(a.get("last_event_at")), _epoch(seen.get("last_received_at"))) if t]
            verdict = state if state in ("accepted", "rejected") else None
            rows.append({
                "attempt": aid, "task": tid, "number": a.get("number"), "state": state, "live": state in LIVE,
                "started_at": iso(started), "ended_at": iso(ended), "duration_s": duration,
                "last_activity_at": iso(max(beat)) if beat else None,
                "route": _observed_fallback(_route(ledger, a.get("executor")), seen), "model_reported": seen.get("model") or None,
                "tokens": _tokens(seen), "cost_usd": None, "failure": a.get("failure") or "",
                "verdict": verdict or None, "verifier": a.get("verifier") or ""})
        rows.sort(key=lambda r: (r["number"] if isinstance(r["number"], int) else 0))
        out[tid] = rows
    return out


def attempt_facts(rdir: Path, now: float | None = None) -> dict[str, list[dict[str, Any]]]:
    paths = bt_run_stores.paths(Path(rdir))
    doc = core_document(paths["m1"])
    return build(doc, paths.get("m2"), usage_by_attempt(Path(rdir)), now)
