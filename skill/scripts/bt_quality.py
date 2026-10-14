"""Quality by defects: audit findings attributed to the builder attempts they judged, and rework before acceptance.

Findings come only from independent audits that reported `task done --findings N`; an audit that did not report it is
unknown (null), never 0. The auditor is never judged on its own findings. Rows go to
<root>/.state/events/defects-YYYY-MM.jsonl (append-only, idempotent per audit attempt). Recording never raises:
telemetry must not stop a marathon.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import bt_events

SEVERITIES = ("high", "med", "low")
ACCEPTED = ("done", "verified")
# Same class as bt_events.summary's "failed"; rework also counts an escalation, which summary files under "other".
FAILED_RESULTS = ("failed", "verify_failed", "timeout", "partial")
REWORK_RESULTS = FAILED_RESULTS + ("escalated",)


def result_for(row: dict, task_id: str) -> str | None:
    """The task's own result in a (possibly batch) attempt: a milestone session settles each task separately."""
    return (row.get("task_results") or {}).get(task_id, row.get("result"))


def parse_findings(findings: int | None, severity: str | None) -> tuple[int | None, dict | None]:
    """Validate the audit's report. (None, None) = not reported. Exits with a message on invalid input."""
    if findings is None:
        if severity:
            raise SystemExit("--severity needs --findings N")
        return None, None
    if isinstance(findings, bool) or not isinstance(findings, int) or findings < 0:
        raise SystemExit("--findings must be an integer >= 0")
    if not severity:
        return findings, ({k: 0 for k in SEVERITIES} if findings == 0 else None)
    parsed: dict[str, int] = {}
    for part in str(severity).split(","):
        key, _, raw = part.strip().partition("=")
        raw = raw.strip()
        if key not in SEVERITIES or not (raw.isascii() and raw.isdigit()):
            raise SystemExit(f"--severity expects high=N,med=N,low=N with N >= 0 (got {part.strip()!r})")
        if key in parsed:
            raise SystemExit(f"--severity names {key} twice")
        parsed[key] = int(raw)
    parsed = {k: parsed.get(k, 0) for k in SEVERITIES}
    if sum(parsed.values()) != findings:
        raise SystemExit(f"--severity sums to {sum(parsed.values())} but --findings is {findings}")
    return findings, parsed


def _path(when: dt.datetime) -> Path:
    return bt_events.STATE / "events" / f"defects-{when:%Y-%m}.jsonl"


def _task_ids(row: dict) -> list[str]:
    return list(row.get("tasks") or ([row["task"]] if row.get("task") else []))


def _history(rows: list[dict]) -> dict[tuple, list[dict]]:
    out: dict[tuple, list[dict]] = {}
    for r in rows:
        for tid in _task_ids(r):
            out.setdefault((r.get("project"), r.get("req"), tid), []).append(r)
    for rs in out.values():
        rs.sort(key=lambda r: r.get("session") or 0)
    return out


def _accepted_index(history: list[dict], task_id: str) -> int | None:
    idx = [i for i, r in enumerate(history) if result_for(r, task_id) in ACCEPTED]
    return idx[-1] if idx else None


def rework_events(rows: list[dict]) -> list[tuple[str, bool]]:
    """One (event_id, judged) per task attempt that failed before that task's accepted attempt; `judged` = its
    result is in summary's failed class (escalated is rework but not a judged failure)."""
    out = []
    for (_, _, tid), history in _history(rows).items():
        accepted = _accepted_index(history, tid)
        if accepted is None:
            continue
        out += [(r["event_id"], result_for(r, tid) in FAILED_RESULTS) for r in history[:accepted]
                if result_for(r, tid) in REWORK_RESULTS and r.get("event_id")]
    return out


def attribution(rows: list[dict], project: str, req: str, tasks: list[dict]) -> tuple[list[str], int]:
    """(builder event_ids, earlier failed task attempts) for the done non-audit tasks of one milestone: only each
    task's last accepted attempt is attributed; the failed ones before it count as rework, per task."""
    histories = _history([r for r in rows if r.get("project") == project and r.get("req") == req])
    ids: list[str] = []
    rework = 0
    for t in tasks:
        if t.get("status") != "done" or t.get("kind") == "audit" or t.get("synthetic"):
            continue
        history = histories.get((project, req, t["id"]), [])
        accepted = _accepted_index(history, t["id"])
        if accepted is None or history[accepted].get("kind") == "audit":
            continue
        if history[accepted]["event_id"] not in ids:
            ids.append(history[accepted]["event_id"])
        rework += sum(1 for r in history[:accepted] if result_for(r, t["id"]) in REWORK_RESULTS)
    return ids, rework


def record_audit_verdict(project: str, state: dict, audit_task: dict, session: int, info: dict) -> Path | None:
    """One row per accepted audit: the findings it reported and the builder attempts they are attributed to."""
    try:
        if not (audit_task.get("synthetic") and audit_task.get("kind") == "audit" and audit_task.get("status") == "done"):
            return None
        now = dt.datetime.now().astimezone()
        event_id = bt_events.event_id_for(project, state.get("req"), session)
        path = _path(now)
        if bt_events._seen(path, event_id):
            return None
        milestone = audit_task.get("milestone")
        members = [t for t in state.get("tasks", []) if t.get("milestone") == milestone]
        builders, rework = attribution(bt_events.read_all(), project, state.get("req"), members)
        findings = audit_task.get("findings")
        row = {"schema": 1, "event_id": event_id, "ts": now.isoformat(timespec="seconds"), "project": project,
               "req": state.get("req"), "milestone": milestone, "audit_task": audit_task.get("id"),
               "audit_event_id": event_id, "auditor": {"agent": info.get("agent") or state.get("agent"),
                                                       "model": info.get("model"), "effort": info.get("effort")},
               "findings": findings if isinstance(findings, int) else None,
               "severity": audit_task.get("severity") if isinstance(findings, int) else None,
               "builder_attempts": builders, "rework_attempts": rework}
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path
    except Exception as exc:  # telemetry never stops a marathon
        print(f"[events] defects not recorded: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def read_defects() -> list[dict]:
    rows = []
    for path in sorted((bt_events.STATE / "events").glob("defects-*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def empty_quality() -> dict:
    return {"audited": 0, "findings": None, "findings_per_audited_task": None, "high_findings": None,
            "clean_audited": 0, "clean_tokens": None, "rework_attempts": 0, "rework_judged": 0}


def _tidy(value: float) -> float | int:
    value = round(value, 2)
    return int(value) if value == int(value) else value


def group_quality(rows: list[dict], defects: list[dict], by: tuple) -> dict[tuple, dict]:
    """Per summary group key: audit findings over the builder attempts audited with a known count, and the rework
    attempts that group's runs caused. An audit's findings (and each severity bucket) are split into equal shares
    across the builder attempts it is attributed to, so group totals add up to the audits' true totals."""
    def key_of(r: dict) -> tuple:
        return tuple(r.get(k) if k != "kind" else (r.get(k) or "implement") for k in by)
    by_id = {r["event_id"]: r for r in rows if r.get("event_id")}
    verdict: dict[str, dict] = {}
    for d in defects:  # the latest audit verdict of an attempt wins
        if isinstance(d.get("findings"), int) and not isinstance(d["findings"], bool):
            for bid in d.get("builder_attempts") or []:
                verdict[bid] = d
    raw: dict[tuple, dict] = {}
    for bid, d in verdict.items():
        r = by_id.get(bid)
        if r is None or (r.get("kind") or "implement") == "audit":
            continue
        n = len(d["builder_attempts"])
        q = raw.setdefault(key_of(r), {**empty_quality(), "findings": 0.0})
        sev = d.get("severity") if isinstance(d.get("severity"), dict) else None
        q["audited"] += 1
        q["findings"] += d["findings"] / n
        if sev is not None:
            q["high_findings"] = (q["high_findings"] or 0.0) + (sev.get("high") or 0) / n
            if not sev.get("high"):
                tokens = bt_events._tokens(r.get("usage") or {})
                q["clean_audited"] += 1
                if tokens is None:  # a clean attempt without a token count: the ratio is not computable
                    q["clean_unmeasured"] = True
                q["clean_tokens"] = (q["clean_tokens"] or 0) + (tokens or 0)
    out: dict[tuple, dict] = {}
    for key, q in raw.items():
        unmeasured = q.pop("clean_unmeasured", False)
        out[key] = {**q, "findings_per_audited_task": round(q["findings"] / q["audited"], 2),
                    "findings": _tidy(q["findings"]),
                    "high_findings": None if q["high_findings"] is None else _tidy(q["high_findings"]),
                    "clean_tokens": None if unmeasured else q["clean_tokens"]}
    for rid, judged in rework_events(rows):
        q = out.setdefault(key_of(by_id[rid]), empty_quality())
        q["rework_attempts"] += 1
        q["rework_judged"] += judged
    return out
