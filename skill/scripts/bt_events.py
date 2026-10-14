"""Attempt telemetry: one JSON line per finished marathon session, appended to <root>/.state/events/attempts-YYYY-MM.jsonl.

Local and private (.state is not versioned). A measure the provider did not report is null, never 0. Token fields keep
each provider's own convention: Claude's input_tokens excludes cached input; Codex JSON includes cached input.
Each row says who ran (agent, profile, model, effort), what (kind, tier, tasks) and how it ended, so the router and
the owner can compare agents and effort levels on measured results. Recording never raises: telemetry must not stop
a marathon.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import bt_profiles
from bt_core import ROOT, STATE

SCHEMA = 2
GROUP_KEYS = ("agent", "profile", "model", "effort", "kind", "tier", "project", "complexity", "outcome")
# Why an attempt ended the way it did, in words that can be counted.
OUTCOMES = {"done": "verified", "verified": "verified", "claimed": "claimed_unverified",
            "verify_failed": "verify_failed", "timeout": "timeout", "usage_limit": "usage_limit",
            "limit_streak": "usage_limit", "blocked": "blocked_needs_human", "escalated": "escalated_by_agent",
            "skipped": "skipped_dependency", "partial": "partial", "stopped": "stopped_by_user"}
ORDER = {"S": 0, "M": 1, "L": 2}


def complexity_of(tasks: list[dict]) -> tuple[str, str]:
    """(S|M|L, declared|inferred). Declared on the PLAN line (`complexity: M`) wins: the largest of the session's
    tasks. Otherwise inferred, and said so: an architecture-level task is L, a session carrying three or more
    tasks is M, anything else S."""
    declared = [t.get("complexity") for t in tasks if t.get("complexity") in ORDER]
    if declared:
        return max(declared, key=ORDER.get), "declared"
    if any((t.get("level") or "") == "architecture" for t in tasks):
        return "L", "inferred"
    return ("M" if len(tasks) >= 3 else "S"), "inferred"


def outcome_of(result: str, why: str | None) -> str:
    if result == "failed":
        text = (why or "").lower()
        if "without task done/fail" in text:
            return "no_verdict"
        return "agent_reported_failure" if why else "failed"
    return OUTCOMES.get(result, result or "unknown")


def detail_for(tasks: list[dict], result: str, results: dict | None = None) -> dict:
    """What the attempt was and why it ended as it did, from the tasks as settled (bt_run, bt_delegate)."""
    complexity, source = complexity_of(tasks)
    bad = [t for t in tasks if (results or {}).get(t["id"], result) not in ("done", "verified", "skipped")]
    if bad:
        why = "; ".join(f"{t['id']}: {' '.join(str(t.get('last_error') or 'no reason recorded').split())[:220]}"
                        for t in bad[:3])
    else:
        why = "; ".join(f"{t['id']}: {' '.join(str(t.get('evidence') or 'verify passed').split())[:160]}"
                        for t in tasks[:3])
    try:  # error output and evidence are free text from agents and commands: never persist a secret in telemetry
        from bt_runtask import _safe_text
        why = _safe_text(why)
    except Exception:
        why = "[withheld: the secret filter could not run]"
    return {"complexity": complexity, "complexity_source": source,
            "attempt": max((t.get("attempts") or 0) for t in tasks) + (0 if bad else 1) if tasks else 1,
            "milestone": tasks[0].get("milestone") if tasks else None,
            "task_results": {t["id"]: (results or {}).get(t["id"], result) for t in tasks},
            "titles": [str(t.get("title") or "")[:90] for t in tasks][:6],
            "outcome": outcome_of(result, why if bad else None), "why": why[:700]}

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
    if agent == "antigravity":
        import bt_agy
        usage = bt_agy.usage_of(raw)
        if usage:
            out.update(source="agy-stream-json", quality="reported", input_tokens=_int(usage.get("input_tokens")),
                       output_tokens=_int(usage.get("output_tokens")),
                       cache_read_tokens=_int(usage.get("cache_read_tokens")),
                       reasoning_tokens=_int(usage.get("thinking_tokens")),
                       total_tokens=_int(usage.get("total_tokens")))
    elif agent == "codex":
        event = _last_event(raw, lambda o: o.get("type") == "turn.completed" and isinstance(o.get("usage"), dict))
        if event:
            usage = event["usage"]
            input_tokens, output_tokens = _int(usage.get("input_tokens")), _int(usage.get("output_tokens"))
            out.update(source="codex-exec-json", quality="reported", input_tokens=input_tokens,
                       output_tokens=output_tokens, cache_read_tokens=_int(usage.get("cached_input_tokens")),
                       total_tokens=input_tokens + output_tokens
                       if input_tokens is not None and output_tokens is not None else None)
            return out
        found = _CODEX_TOTAL.findall(raw or "")
        if found:
            digits = re.sub(r"\D", "", found[-1])
            if digits:
                out.update(source="codex-exec-text", quality="total_only", total_tokens=int(digits))
    else:  # claude stream-json
        event = _last_event(raw, lambda o: o.get("type") == "result")
        usage = (event or {}).get("usage")
        if not isinstance(usage, dict):  # a session cut by a limit or a kill has no result event: sum what was reported
            partial = _claude_partial_usage(raw)
            if partial:
                out.update(source="claude-stream-json-partial", quality="partial", **partial)
                return out
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


def _claude_partial_usage(raw: str) -> dict | None:
    """Tokens of the assistant messages seen so far (once per message id) in a Claude stream that ended without its
    final result event. A lower bound, labelled `partial`: the most expensive sessions are the ones that get cut."""
    seen: dict[str, dict] = {}
    for line in (raw or "").splitlines():
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        message = obj.get("message") if isinstance(obj, dict) and obj.get("type") == "assistant" else None
        usage = message.get("usage") if isinstance(message, dict) else None
        if isinstance(usage, dict):
            seen[str(message.get("id") or len(seen))] = usage  # later chunks of one message carry the final counts
    if not seen:
        return None
    total = {"input_tokens": 0, "output_tokens": 0, "cache_read_tokens": 0, "cache_write_tokens": 0}
    keys = {"input_tokens": "input_tokens", "output_tokens": "output_tokens",
            "cache_read_tokens": "cache_read_input_tokens", "cache_write_tokens": "cache_creation_input_tokens"}
    for usage in seen.values():
        for dst, src in keys.items():
            total[dst] += _int(usage.get(src)) or 0
    return {**total, "total_tokens": sum(total.values())}


_CREDITS_RE = re.compile(r"out of credits|add credits|credits? (?:are |is )?(?:exhausted|depleted)|insufficient credits|"
                         r"insufficient (?:quota|funds)", re.IGNORECASE)
_AUTH_RE = re.compile(r"not (?:logged|signed) in|please (?:sign|log) ?in|authentication (?:failed|required)|"
                      r"401 unauthorized|invalid api key|token (?:has )?expired", re.IGNORECASE)
_ERROR_LINE_RE = re.compile(r"\bERROR\b|error:|limit|credits|unauthori[sz]ed|failed", re.IGNORECASE)


def loss_of(result: str, raw: str) -> str | None:
    """Telemetry class for an attempt the PROVIDER cost us (quota, credits, sign-in), as opposed to one the model got
    wrong. It never changes how the supervisor settles the session: it only lets the metrics separate the two."""
    if result in ("usage_limit", "limit_streak"):
        return "usage_limit"
    if result in ("done", "verified", "claimed", "skipped", "stopped"):
        return None
    tail = (raw or "")[-6000:]
    if _CREDITS_RE.search(tail):
        return "out_of_credits"
    if _AUTH_RE.search(tail):
        return "auth"
    return None


def error_excerpt(raw: str) -> str | None:
    """The last error-looking line of the output (bounded, secrets filtered), so a failed attempt says why in the
    provider's words and not with a fragment of the prompt echo."""
    for line in reversed((raw or "")[-6000:].splitlines()):
        line = line.strip()
        if line and not line.startswith("{") and _ERROR_LINE_RE.search(line):
            line = " ".join(line.split())[:240]
            try:
                from bt_runtask import _safe_text
                return _safe_text(line)
            except Exception:  # noqa: BLE001 - a telemetry row is never lost to the filter failing
                return "[withheld: the secret filter could not run]"
    return None


def origin_of(env: dict | None = None) -> str:
    """`real` (default) or `synthetic` (BITACORA_ORIGIN=synthetic: smoke tests, matrix checks, evals), so rankings can
    leave out measurements that were never real work."""
    import os
    value = ((env if env is not None else os.environ).get("BITACORA_ORIGIN") or "").strip().lower()
    return "synthetic" if value == "synthetic" else "real"


def _path(when: dt.datetime) -> Path:
    return STATE / "events" / f"attempts-{when:%Y-%m}.jsonl"


def _seen(path: Path, event_id: str) -> bool:
    try:
        with path.open(encoding="utf-8") as fh:
            return any(event_id in line for line in fh)
    except OSError:
        return False


def event_id_for(project: str, req, session: int) -> str:
    return hashlib.sha1(f"{project}|{req}|{session}".encode()).hexdigest()[:16]


def record_attempt(project: str, state: dict, task_id: str, session: int, info: dict, result: str,
                   detail: dict | None = None) -> Path | None:
    """Append the attempt; idempotent per (project, run, session). Returns the file, or None when nothing was written.
    `detail` (detail_for): complexity, attempt number, the outcome class and why it ended that way."""
    try:
        now = dt.datetime.now().astimezone()
        agent = info.get("agent") or state.get("agent")  # the session's route, not the run's default
        profile = info.get("profile") if info.get("agent") else state.get("profile")
        event_id = event_id_for(project, state.get("req"), session)
        row = {
            "schema": SCHEMA, "event_id": event_id, "ts": now.isoformat(timespec="seconds"),
            "project": project, "work": bt_profiles.is_work_project(project), "req": state.get("req"),
            "task": task_id, "session": session, "agent": agent, "profile": profile,
            "model": info.get("model"), "requested_model": info.get("model"), "reported_model": None,
            "identity_source": "requested", "effort": info.get("effort"), "kind": info.get("kind") or "implement",
            "tier": info.get("tier"), "tasks": info.get("tasks") or [task_id], "seconds": info.get("seconds"),
            "rc": info.get("rc"), "timed_out": bool(info.get("timed_out")), "stopped": bool(info.get("stopped")),
            "early_exit": bool(info.get("early_exit")), "recovered": bool(info.get("recovered")), "result": result,
            "usage": extract_usage(agent, info.get("text") or ""),
            "route_why": info.get("why"),
            "loss": loss_of(result, info.get("text") or ""),
            "error_excerpt": None if result in ("done", "verified") else error_excerpt(info.get("text") or ""),
            "change_size": info.get("change_size") if isinstance(info.get("change_size"), dict) else None,
            "origin": origin_of(),
            **{k: (detail or {}).get(k) for k in ("complexity", "complexity_source", "attempt", "milestone", "task_results", "titles",
                                                   "outcome", "why")},
        }
        row["outcome"] = row["outcome"] or outcome_of(result, None)
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


def _valid_row(row) -> bool:
    if not isinstance(row, dict) or not isinstance(row.get("result"), str):
        return False
    if any(row.get(k) is not None and not isinstance(row[k], str)
           for k in tuple(k for k in GROUP_KEYS if k != "tier") + ("ts", "event_id", "req", "task")):
        return False
    if any(row.get(k) is not None and _int(row[k]) is None for k in ("tier", "session")):
        return False
    seconds = row.get("seconds")
    if seconds is not None and (isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or
                                not math.isfinite(seconds) or seconds < 0):
        return False
    usage = row.get("usage", {})
    if not isinstance(usage, dict) or any(v is not None and _int(v) is None
                                        for k, v in usage.items() if k.endswith("_tokens")):
        return False
    cost = usage.get("cost_usd_reported")
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, (int, float)) or
                             not math.isfinite(cost) or cost < 0):
        return False
    return all(row.get(k) is None or isinstance(row[k], dict) for k in ("task_results",)) and all(
        row.get(k) is None or isinstance(row[k], list) and all(isinstance(v, str) for v in row[k])
        for k in ("tasks", "titles"))


def read_all() -> list[dict]:
    rows = []
    for path in sorted((STATE / "events").glob("attempts-*.jsonl")):
        invalid = 0
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except ValueError:
                invalid += 1
                continue
            if not _valid_row(row):
                invalid += 1
                continue
            rows.append(row)
        if invalid:
            print(f"[events] ignored {invalid} invalid attempt rows in {path.name}", file=sys.stderr)
    return rows


def _tokens(usage: dict) -> int | None:
    total = usage.get("total_tokens")
    if total is None and usage.get("input_tokens") is not None and usage.get("output_tokens") is not None:
        total = usage["input_tokens"] + usage["output_tokens"] + (usage.get("cache_read_tokens") or 0) + \
            (usage.get("cache_write_tokens") or 0)
    return total


def summary(rows: list[dict], by: tuple | list | None = None, defects: list[dict] | None = None) -> list[dict]:
    """Per group (default agent, profile, model, effort; any of GROUP_KEYS): attempts, outcomes, success rate over
    attempts that had a verdict (usage limits and stops are not the agent's failure), time, and token/cost totals over
    the attempts that reported them. Quality fields (findings, rework) come from bt_quality; `defects` are the audit
    verdict rows (read_defects): without them the findings fields are null."""
    by = tuple(k for k in (by or DEFAULT_BY) if k in GROUP_KEYS) or DEFAULT_BY
    reported_audits = {d.get("audit_event_id") for d in (defects or [])
                       if isinstance(d.get("findings"), int) and not isinstance(d.get("findings"), bool)}
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = tuple(r.get(k) if k != "kind" else (r.get(k) or "implement") for k in by)
        g = groups.setdefault(key, {**dict(zip(by, key)), "attempts": 0, "done": 0, "failed": 0, "other": 0,
                                    "seconds": 0, "seconds_measured": 0, "measured": 0,
                                    "tokens_measured": 0, "cost_usd_reported": 0.0,
                                    "cost_measured": 0, "provider_loss": 0, "failed_by_loss": 0,
                                    "audits_done": 0, "audits_unreported": 0})
        g["attempts"] += 1
        res = r.get("result")
        bucket = ("done" if res in ("done", "verified") else
                  "failed" if res in ("failed", "verify_failed", "timeout", "partial") else "other")
        g[bucket] += 1
        if r.get("loss"):  # quota, credits or sign-in: the provider's loss, kept visible next to the model's results
            g["provider_loss"] += 1
            g["failed_by_loss"] += bucket == "failed"
        # Only supervised runs (REQ-NNN) can report findings: a one-off delegated audit has no verdict row by design.
        if (r.get("kind") or "implement") == "audit" and bucket == "done" and re.match(r"REQ-\d+", str(r.get("req"))):
            g["audits_done"] += 1
            if defects is not None and r.get("event_id") not in reported_audits:
                g["audits_unreported"] += 1
        if r.get("seconds") is not None:
            g["seconds"] += r["seconds"]
            g["seconds_measured"] += 1
        u = r.get("usage") or {}
        total = _tokens(u)
        if total is not None:
            g["measured"] += 1
            g["tokens_measured"] += total
        if isinstance(u.get("cost_usd_reported"), (int, float)):
            g["cost_measured"] += 1
            g["cost_usd_reported"] += u["cost_usd_reported"]
    import bt_quality
    quality = bt_quality.group_quality(rows, defects or [], by)
    for key, g in groups.items():
        g.update(quality.get(key) or bt_quality.empty_quality())
    for g in groups.values():
        judged = g["done"] + g["failed"]
        g["success_rate"] = round(g["done"] / judged, 2) if judged else None
        judged_model = judged - g["failed_by_loss"]  # same rate without the failures the provider caused
        g["success_rate_excl_loss"] = round(g["done"] / judged_model, 2) if judged_model > 0 else None
        if defects is None:
            g["audits_unreported"] = None
        g["avg_seconds"] = round(g["seconds"] / g["seconds_measured"]) if g["seconds_measured"] else None
        g["seconds_coverage"] = round(g["seconds_measured"] / g["attempts"], 2) if g["attempts"] else None
        if not g["seconds_measured"]:
            g["seconds"] = None
        g["coverage"] = round(g["measured"] / g["attempts"], 2) if g["attempts"] else None
        g["tokens_per_done"] = round(g["tokens_measured"] / g["done"]) if g["done"] and g["measured"] == g["attempts"] \
            else None
        g["cost_usd_reported"] = round(g["cost_usd_reported"], 4) if g["cost_measured"] else None
        g["rework_rate"] = round(g["rework_judged"] / judged, 2) if judged else None
        g["tokens_per_clean_task"] = round(g["clean_tokens"] / g["clean_audited"]) \
            if g["clean_audited"] and g["clean_tokens"] is not None else None
    return sorted(groups.values(), key=lambda g: tuple(str(g[k]) for k in by))


def advice(rows: list[dict], min_samples: int = 5, defects: list[dict] | None = None) -> list[str]:
    """Plain-language observations to decide with: only from groups with enough judged attempts."""
    out = []
    table = [g for g in summary(rows, ("agent", "model", "effort", "kind")) if g["done"] + g["failed"] >= min_samples]
    by_kind: dict[str, list[dict]] = {}
    for g in table:
        by_kind.setdefault(g["kind"], []).append(g)
    for kind, groups in sorted(by_kind.items()):
        compare_seconds = all(g["seconds_measured"] >= min_samples for g in groups)
        groups.sort(key=lambda g: (-g["success_rate"], g["avg_seconds"] if compare_seconds else 0))
        best = groups[0]
        duration = (f"{best['avg_seconds']}s avg" if best["seconds_measured"] >= min_samples else
                    f"duration needs {min_samples} measured attempts")
        out.append(f"{kind}: best measured is {best['agent']}/{best['model']}"
                   f"{' · ' + best['effort'] if best['effort'] else ''} ({best['success_rate']:.0%} of "
                   f"{best['done'] + best['failed']}, {duration})")
        for g in groups[1:]:
            if best["success_rate"] - g["success_rate"] >= 0.25:
                out.append(f"{kind}: {g['agent']}/{g['model']}{' · ' + g['effort'] if g['effort'] else ''} succeeds "
                           f"{g['success_rate']:.0%} of {g['done'] + g['failed']}: consider starting it one tier up")
    quality = [g for g in summary(rows, ("agent", "model", "effort", "kind"), defects)
               if g["audited"] >= min_samples and g["findings_per_audited_task"] is not None]
    for g in sorted(quality, key=lambda g: (g["kind"], g["findings_per_audited_task"])):
        out.append(f"quality {g['kind']}: {g['agent']}/{g['model']}{' · ' + g['effort'] if g['effort'] else ''} has "
                   f"{g['findings_per_audited_task']} audit findings per audited task over {g['audited']} audited "
                   f"(audits that reported findings only)")
    if not out:
        out.append(f"not enough data yet: a group needs {min_samples} judged attempts before it is compared")
    return out


def read_defects() -> list[dict]:
    import bt_quality
    return bt_quality.read_defects()


def key_values(row: dict) -> list[tuple[str, str]]:
    """One attempt as an ordered key/value table (CLI `metrics --attempts`, the /metrics page)."""
    u = row.get("usage") or {}
    tokens = _tokens(u)

    def show(value) -> str:
        return "—" if value is None or value == "" or value == [] else str(value)
    pairs = [
        ("when", str(row.get("ts") or "")[:19].replace("T", " ")), ("project", row.get("project")),
        ("run / task", f"{row.get('req')} / {row.get('task')}"), ("tasks", ", ".join(row.get("tasks") or []) or None),
        ("what", "; ".join(row.get("titles") or []) or None), ("kind of work", row.get("kind")),
        ("complexity", f"{row.get('complexity')} ({row.get('complexity_source')})" if row.get("complexity") else None),
        ("tier", row.get("tier")), ("attempt", row.get("attempt")),
        ("agent", row.get("agent")), ("account", row.get("profile")), ("model", row.get("model")),
        ("effort", row.get("effort") or "CLI default"), ("routed because", row.get("route_why")),
        ("result", row.get("result")),
        ("outcome", row.get("outcome") or outcome_of(str(row.get("result")), None)), ("why", row.get("why")),
        ("duration", f"{row.get('seconds')} s" if row.get("seconds") is not None else None),
        ("tokens (measured)", f"{tokens:,}" if tokens is not None else None),
        ("  input / output", f"{u.get('input_tokens')} / {u.get('output_tokens')}"
         if u.get("input_tokens") is not None else None),
        ("  cache read / write", f"{u.get('cache_read_tokens')} / {u.get('cache_write_tokens')}"
         if u.get("cache_read_tokens") is not None else None),
        ("cost reported (USD)", u.get("cost_usd_reported")),
        ("usage source", f"{u.get('source')} ({u.get('quality')})" if u.get("source") else "not reported by the CLI"),
        ("provider loss", row.get("loss")), ("error (provider words)", row.get("error_excerpt")),
        ("change size", ", ".join(f"{k}={v}" for k, v in (row.get("change_size") or {}).items()) or None),
        ("origin", row.get("origin") or "real (not tagged)"),
    ]
    return [(k, show(v)) for k, v in pairs]


def reasons(rows: list[dict], top: int = 3) -> list[dict]:
    """Per (agent, model, effort, kind, complexity): how attempts ended and the most frequent reasons, for failures
    and for successes."""
    groups: dict[tuple, dict] = {}
    for r in rows:
        key = (r.get("agent"), r.get("model"), r.get("effort"), r.get("kind") or "implement", r.get("complexity"))
        g = groups.setdefault(key, {"agent": key[0], "model": key[1], "effort": key[2], "kind": key[3],
                                    "complexity": key[4], "attempts": 0, "outcomes": {}, "_bad": [], "_good": []})
        g["attempts"] += 1
        outcome = r.get("outcome") or outcome_of(str(r.get("result")), None)
        g["outcomes"][outcome] = g["outcomes"].get(outcome, 0) + 1
        if r.get("why"):
            (g["_good"] if outcome == "verified" else g["_bad"]).append(str(r["why"]))
    out = []
    for g in groups.values():
        g["failed_because"] = g.pop("_bad")[-top:]
        g["worked_because"] = g.pop("_good")[-top:]
        out.append(g)
    return sorted(out, key=lambda g: tuple(str(g[k]) for k in ("kind", "complexity", "agent", "model", "effort")))
