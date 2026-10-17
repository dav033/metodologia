"""Exploration ledger: the real, persistent budget of cold-start exploration, kept apart from ordinary work.

Only a decision the router took BECAUSE a route was under-sampled (and that had a real alternative) is an exploration.
Ordinary attempts, forced fallbacks, escalations after a failure and explicit assignments never spend it. A reservation
is written under a machine-wide lock before the session starts, so concurrent supervisors share one balance; it survives
restarts (`<root>/.state/explore.jsonl`, append-only: `reserve` rows, then a `settle` row with the result). Historical
attempts carry no decision record and are never read as explorations.

Decision kinds (`decision.kind` on the route and on the attempt row): exploit, explore, fallback, escalation, explicit.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from bt_core import STATE

KINDS = ("exploit", "explore", "fallback", "escalation", "explicit")
WINDOW_SEC = 7 * 86400


def _path() -> Path:
    return STATE / "explore.jsonl"


def _rows() -> list[dict]:
    out = []
    try:
        for line in _path().read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                out.append(row)
    except OSError:
        pass
    return out


def used(now: float | None = None, window: float = WINDOW_SEC) -> tuple[dict, int]:
    """({(agent, model): admitted explorations in the window}, total in the window)."""
    now = time.time() if now is None else now
    per: dict[tuple, int] = {}
    total = 0
    for row in _rows():
        if row.get("type") == "reserve" and now - float(row.get("at") or 0) <= window:
            key = (row.get("agent"), row.get("model"))
            per[key] = per.get(key, 0) + 1
            total += 1
    return per, total


def decision_id(project: str | None, req: object, agent: str, model: str, at: float, nonce: int) -> str:
    return hashlib.sha1(f"{project}|{req}|{agent}|{model}|{at}|{nonce}".encode()).hexdigest()[:16]


def reserve(route: dict, project: str, req: object, reason: str, route_limit: int, global_limit: int | None,
            now: float | None = None) -> dict | None:
    """Atomically admit one exploration of `route` against the budgets and record it. Returns the decision record, or
    None when the route's weekly budget (`route_limit`, counted per agent+model) or the optional global one is spent."""
    from bt_lock import central_lock
    now = time.time() if now is None else now
    key = (route.get("agent"), route.get("model"))
    with central_lock("explore"):
        per, total = used(now)
        route_used = per.get(key, 0)
        if route_limit >= 0 and route_used >= route_limit:
            return None
        if global_limit is not None and total >= global_limit:
            return None
        did = decision_id(project, req, str(key[0]), str(key[1]), now, total)
        record = {"type": "reserve", "decision_id": did, "at": now,
                  "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)), "project": project, "req": req,
                  "profile": route.get("profile"), "account": route.get("account"), "agent": key[0], "model": key[1],
                  "kind": route.get("kind"), "tier": route.get("tier"), "effort": route.get("effort"),
                  "reason": reason, "budget_before": {"route_used": route_used, "route_limit": route_limit,
                                                      "global_used": total, "global_limit": global_limit}}
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def settle(did: str | None, result: str, verified: bool | None) -> None:
    """Record what the exploration produced (result, verification state). Never raises."""
    if not did:
        return
    try:
        from bt_lock import central_lock
        with central_lock("explore"):
            with _path().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"type": "settle", "decision_id": did, "at": time.time(), "result": result,
                                     "verified": verified}) + "\n")
    except Exception:  # noqa: BLE001 - the ledger never stops a marathon
        pass


def decision_for(kind: str, why: str, record: dict | None = None, **extra) -> dict:
    """The decision attached to a route and then to its attempt row."""
    assert kind in KINDS
    out = {"kind": kind, "why": why, **extra}
    if record:
        out.update(decision_id=record["decision_id"], budget_before=record["budget_before"])
    return out
