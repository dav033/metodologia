"""Attempt telemetry: one JSON line per finished marathon session, appended to <root>/.state/events/attempts-YYYY-MM.jsonl.

Local and private (.state is not versioned). A measure the provider did not report is null, never 0. Token fields keep
each provider's own convention: Claude's input_tokens excludes cached input; Antigravity's usage is the conversation
total (one conversation per session, so the last result event is the session); Codex only prints a grand total.
recording never raises: telemetry must not stop a marathon.
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

SCHEMA = 1
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
    if agent == "antigravity":
        event = _last_event(raw, lambda o: o.get("event") == "result")
        usage = ((event or {}).get("result") or {}).get("usage")
        if isinstance(usage, dict):
            out.update(source="agy-stream-json", quality="reported", input_tokens=_int(usage.get("input_tokens")),
                       output_tokens=_int(usage.get("output_tokens")),
                       cache_read_tokens=_int(usage.get("cache_read_tokens")),
                       reasoning_tokens=_int(usage.get("thinking_tokens")),
                       total_tokens=_int(usage.get("total_tokens")))
    elif agent == "codex":
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
        agent = state.get("agent")
        profile = state.get("profile")
        event_id = hashlib.sha1(f"{project}|{state.get('req')}|{session}".encode()).hexdigest()[:16]
        row = {
            "schema": SCHEMA, "event_id": event_id, "ts": now.isoformat(timespec="seconds"),
            "project": project, "work": bt_profiles.is_work_project(project), "req": state.get("req"),
            "task": task_id, "session": session, "agent": agent, "profile": profile,
            "model": info.get("model"), "effort": info.get("effort"), "seconds": info.get("seconds"),
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


def summary(rows: list[dict]) -> list[dict]:
    """Per (agent, profile, model): attempts, verified rate, and token totals over attempts that reported them."""
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r.get("agent"), r.get("profile"), r.get("model"))
        g = groups.setdefault(key, {"agent": key[0], "profile": key[1], "model": key[2], "attempts": 0, "done": 0,
                                    "failed": 0, "other": 0, "seconds": 0, "measured": 0,
                                    "tokens_measured": 0})
        g["attempts"] += 1
        res = r.get("result")
        g["done" if res == "done" else "failed" if res in ("failed", "verify_failed", "timeout") else "other"] += 1
        g["seconds"] += r.get("seconds") or 0
        u = r.get("usage") or {}
        total = u.get("total_tokens")
        if total is None and u.get("input_tokens") is not None and u.get("output_tokens") is not None:
            total = u["input_tokens"] + u["output_tokens"] + (u.get("cache_read_tokens") or 0) + \
                (u.get("cache_write_tokens") or 0)
        if total is not None:
            g["measured"] += 1
            g["tokens_measured"] += total
    for g in groups.values():
        g["coverage"] = round(g["measured"] / g["attempts"], 2) if g["attempts"] else None
    return sorted(groups.values(), key=lambda g: (str(g["agent"]), str(g["profile"]), str(g["model"])))
