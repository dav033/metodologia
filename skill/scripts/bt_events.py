"""Attempt telemetry: one JSON line per finished marathon session, appended to <root>/.state/events/attempts-YYYY-MM.jsonl.

Local and private (.state is not versioned). A measure the provider did not report is null, never 0. Token fields keep
each provider's own convention: Claude's input_tokens excludes cached input; Codex only prints a grand total.
Each row says who ran (agent, profile, model, effort), what (kind, tier, tasks) and how it ended, so the router and
the owner can compare agents and effort levels on measured results. Recording never raises: telemetry must not stop
a marathon.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

import bt_profiles
from bt_core import ROOT, STATE

SCHEMA = 2
GROUP_KEYS = ("agent", "profile", "model", "effort", "kind", "tier", "project")
DEFAULT_BY = ("agent", "profile", "model", "effort")
_CODEX_TOTAL = re.compile(r"tokens used\s*\n\s*([\d,\.]+)\s*$", re.I | re.M)


def _int(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def _last_event(raw: str, match) -> dict | None:
    for line in reversed((raw or "").splitlines()):
        if line.startswith("{"):
            try:
                obj = json.loads(line)
            except ValueError:
                continue
            if isinstance(obj, dict) and match(obj):
                return obj
    return None


def extract_usage(agent: str | None, raw: str) -> dict:
    """{source, quality, input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, reasoning_tokens,
    total_tokens, cost_usd_reported}; every field null when the output does not carry it."""
    out = {"source": None, "quality": "unknown", "input_tokens": None, "output_tokens": None,
           "cache_read_tokens": None, "cache_write_tokens": None, "reasoning_tokens": None, "total_tokens": None,
           "cost_usd_reported": None}
    if agent == "codex":
        found = _CODEX_TOTAL.findall(raw or "")
        if found:
            digits = re.sub(r"\D", "", found[-1])
            if digits:
                out.update(source="codex-exec-text", quality="total_only", total_tokens=int(digits))
    else:  # claude stream-json
        event = _last_event(raw, lambda o: o.get("type") == "result")
        usage = (event or {}).get("usage")
        if isinstance(usage, dict):
            details = usage.get("output_tokens_details") if isinstance(usage.get("output_tokens_details"), dict) else {}
            out.update(source="claude-stream-json", quality="reported", input_tokens=_int(usage.get("input_tokens")),
                       output_tokens=_int(usage.get("output_tokens")),
                       cache_read_tokens=_int(usage.get("cache_read_input_tokens")),
                       cache_write_tokens=_int(usage.get("cache_creation_input_tokens")),
                       reasoning_tokens=_int(details.get("thinking_tokens")))
            cost = event.get("total_cost_usd")
            out["cost_usd_reported"] = cost if isinstance(cost, (int, float)) else None
    return out


def _path(when: dt.datetime) -> Path:
    return STATE / "events" / f"attempts-{when:%Y-%m}.jsonl"


def _seen(path: Path, event_id: str) -> bool:
    try:
        with path.open(encoding="utf-8") as fh:
            return any(event_id in line for line in fh)
    except OSError:
        return False


def record_attempt(project: str, state: dict, task_id: str, session: int, info: dict, result: str) -> Path | None:
    """Append the attempt; idempotent per (project, run, session). Returns the file, or None when nothing was written."""
    try:
        now = dt.datetime.now().astimezone()
        agent = info.get("agent") or state.get("agent")  # the session's route, not the run's default
        profile = info.get("profile") if info.get("agent") else state.get("profile")
        event_id = hashlib.sha1(f"{project}|{state.get('req')}|{session}".encode()).hexdigest()[:16]
        row = {
            "schema": SCHEMA, "event_id": event_id, "ts": now.isoformat(timespec="seconds"),
            "project": project, "work": bt_profiles.is_work_project(project), "req": state.get("req"),
            "task": task_id, "session": session, "agent": agent, "profile": profile,
            "model": info.get("model"), "effort": info.get("effort"), "kind": info.get("kind") or "implement",
            "tier": info.get("tier"), "tasks": info.get("tasks") or [task_id], "seconds": info.get("seconds"),
            "rc": info.get("rc"), "timed_out": bool(info.get("timed_out")), "stopped": bool(info.get("stopped")),
            "early_exit": bool(info.get("early_exit")), "recovered": bool(info.get("recovered")), "result": result,
            "usage": extract_usage(agent, info.get("text") or ""),
        }
        path = _path(now)
        if _seen(path, event_id):
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path
    except Exception as exc:  # telemetry never stops a marathon
        print(f"[events] attempt not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def read_all() -> list[dict]:
    rows = []
    for path in sorted((STATE / "events").glob("attempts-*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except ValueError:
                continue
    return rows


def _tokens(usage: dict) -> int | None:
    total = usage.get("total_tokens")
    if total is None and usage.get("input_tokens") is not None and usage.get("output_tokens") is not None:
        total = usage["input_tokens"] + usage["output_tokens"] + (usage.get("cache_read_tokens") or 0) + \
            (usage.get("cache_write_tokens") or 0)
    return total


def summary(rows: list[dict], by: tuple | list | None = None) -> list[dict]:
    """Per group (default agent, profile, model, effort; any of GROUP_KEYS): attempts, outcomes, success rate over
    attempts that had a verdict (usage limits and stops are not the agent's failure), time, and token/cost totals over
    the attempts that reported them."""
    by = tuple(k for k in (by or DEFAULT_BY) if k in GROUP_KEYS) or DEFAULT_BY
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = tuple(r.get(k) if k != "kind" else (r.get(k) or "implement") for k in by)
        g = groups.setdefault(key, {**dict(zip(by, key)), "attempts": 0, "done": 0, "failed": 0, "other": 0,
                                    "seconds": 0, "measured": 0, "tokens_measured": 0, "cost_usd_reported": 0.0,
                                    "cost_measured": 0})
        g["attempts"] += 1
        res = r.get("result")
        g["done" if res in ("done", "verified") else
          "failed" if res in ("failed", "verify_failed", "timeout", "partial") else "other"] += 1
        g["seconds"] += r.get("seconds") or 0
        u = r.get("usage") or {}
        total = _tokens(u)
        if total is not None:
            g["measured"] += 1
            g["tokens_measured"] += total
        if isinstance(u.get("cost_usd_reported"), (int, float)):
            g["cost_measured"] += 1
            g["cost_usd_reported"] += u["cost_usd_reported"]
    for g in groups.values():
        judged = g["done"] + g["failed"]
        g["success_rate"] = round(g["done"] / judged, 2) if judged else None
        g["avg_seconds"] = round(g["seconds"] / g["attempts"]) if g["attempts"] else None
        g["coverage"] = round(g["measured"] / g["attempts"], 2) if g["attempts"] else None
        g["tokens_per_done"] = round(g["tokens_measured"] / g["done"]) if g["done"] and g["measured"] == g["attempts"] \
            else None
        g["cost_usd_reported"] = round(g["cost_usd_reported"], 4) if g["cost_measured"] else None
    return sorted(groups.values(), key=lambda g: tuple(str(g[k]) for k in by))


def advice(rows: list[dict], min_samples: int = 5) -> list[str]:
    """Plain-language observations to decide with: only from groups with enough judged attempts."""
    out = []
    table = [g for g in summary(rows, ("agent", "model", "effort", "kind")) if g["done"] + g["failed"] >= min_samples]
    by_kind: dict[str, list[dict]] = {}
    for g in table:
        by_kind.setdefault(g["kind"], []).append(g)
    for kind, groups in sorted(by_kind.items()):
        groups.sort(key=lambda g: (-g["success_rate"], g["avg_seconds"] or 0))
        best = groups[0]
        out.append(f"{kind}: best measured is {best['agent']}/{best['model']}"
                   f"{' · ' + best['effort'] if best['effort'] else ''} ({best['success_rate']:.0%} of "
                   f"{best['done'] + best['failed']}, {best['avg_seconds']}s avg)")
        for g in groups[1:]:
            if best["success_rate"] - g["success_rate"] >= 0.25:
                out.append(f"{kind}: {g['agent']}/{g['model']}{' · ' + g['effort'] if g['effort'] else ''} succeeds "
                           f"{g['success_rate']:.0%} of {g['done'] + g['failed']}: consider starting it one tier up")
    if not out:
        out.append(f"not enough data yet: a group needs {min_samples} judged attempts before it is compared")
    return out
