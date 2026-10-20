"""Exploration ledger: the real, persistent budget of cold-start exploration, kept apart from ordinary work.

Only a decision the router took BECAUSE a route was under-sampled (and that had a real alternative) is an exploration.
Ordinary attempts, forced fallbacks, escalations after a failure and explicit assignments never spend it. A reservation
is written under an exclusive inter-process lock before the session starts, so concurrent supervisors share one balance;
it survives restarts (`<root>/.state/explore.jsonl`, append-only: `reserve` rows, then a `settle` row with the result).
Historical attempts carry no decision record and are never read as explorations.

Guarantees (tests/test_harness_fix.py, real processes):
- The lock is `flock` on `explore.lock`: it excludes other processes and other threads, the kernel frees it when its
  holder dies (no stale lock to break, no deadlock), and it FAILS CLOSED: a lock that cannot be taken in `LOCK_WAIT_SEC`
  admits nothing (the route simply ranks as unproven) instead of risking an overspend. Platforms without `fcntl` fall back
  to the O_EXCL central lock.
- A torn line (a writer killed mid-write) is quarantined to `explore.corrupt.jsonl` under the lock and replaced by an
  explicit `orphan` reserve at the current time, attributed to the route it still names (else only to the GLOBAL cap),
  expiring with the window: corrupt data
  can only make the budget stricter, never looser, and the next append never glues onto it.
- A reservation with no `settle` (its process died) keeps counting until its 7-day window ends: the exploration may
  have spent quota, so the cap is never reopened early. `status()` lists such orphans after `ORPHAN_AFTER_SEC`.
- `reserve(key=...)` is idempotent: a restart that re-routes the same session reuses its reservation without spending
  twice. `settle` ignores a decision already settled.

Decision kinds (`decision.kind` on the route and on the attempt row): exploit, explore, fallback, escalation, explicit.
"""
from __future__ import annotations

import contextlib
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import bt_core

try:  # POSIX; elsewhere the O_EXCL central lock stands in
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None

KINDS = ("exploit", "explore", "fallback", "escalation", "explicit")
WINDOW_SEC = 7 * 86400
ORPHAN_AFTER_SEC = 6 * 3600
LOCK_WAIT_SEC = 10.0


class LockUnavailable(OSError):
    """The ledger lock could not be taken in time: nothing may be admitted."""


STATE: Path | None = None   # None follows `bt_core.STATE` at call time; a test or a relocated root may set it


def _path() -> Path:
    """Looked up at call time, never copied at import: a patched `bt_core.STATE` (the test roots) must not leave the
    exploration reservations in the real ledger, where they would eat the weekly budget of real runs."""
    return (STATE if STATE is not None else bt_core.STATE) / "explore.jsonl"


@contextlib.contextmanager
def _exclusive(timeout: float | None = None):
    timeout = LOCK_WAIT_SEC if timeout is None else timeout
    path = _path().with_suffix(".lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    if fcntl is None:  # pragma: no cover
        from bt_lock import central_lock
        with central_lock("explore", timeout):
            yield
        return
    with path.open("a") as handle:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise LockUnavailable(f"explore ledger lock busy for {timeout:g}s") from None
                time.sleep(0.02)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _parse(text: str) -> tuple[list[dict], list[str]]:
    rows, bad = [], []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except ValueError:
            bad.append(line)
            continue
        (rows if isinstance(row, dict) else bad).append(row if isinstance(row, dict) else line)
    return rows, bad


def _read() -> tuple[list[dict], list[str]]:
    try:
        return _parse(_path().read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return [], []


def _heal_locked(now: float) -> None:
    """Under the lock: quarantine malformed lines, make the file end in a newline, and record each torn line as an
    unattributed reserve so the budget can only get stricter."""
    path = _path()
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return
    rows, bad = _parse(text)
    if not bad and (not text or text.endswith("\n")):
        return
    if bad:
        with path.with_suffix(".corrupt.jsonl").open("a", encoding="utf-8") as fh:
            fh.writelines(line + "\n" for line in bad)
        def field(line: str, name: str) -> str | None:  # a torn reserve usually still names its route
            found = re.search(rf'"{name}":\s*"([^"]+)"', line)
            return found.group(1) if found else None

        rows += [{"type": "reserve", "decision_id": "orphan-" + hashlib.sha1(line.encode()).hexdigest()[:12],
                  "at": now, "agent": field(line, "agent"), "model": field(line, "model"), "orphan": "corrupt_line"}
                 for line in bad]
        print(f"[explore] {len(bad)} malformed ledger line(s) quarantined and counted as reserved", file=sys.stderr)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    tmp.replace(path)


def _count(rows: list[dict], now: float, window: float) -> tuple[dict, int]:
    per: dict[tuple, int] = {}
    total = 0
    for row in rows:
        if row.get("type") == "reserve" and now - float(row.get("at") or 0) <= window:
            if row.get("agent") is not None:
                key = (row.get("agent"), row.get("model"))
                per[key] = per.get(key, 0) + 1
            total += 1
    return per, total


def used(now: float | None = None, window: float = WINDOW_SEC) -> tuple[dict, int]:
    """({(agent, model): admitted explorations in the window}, total in the window, orphans included). A malformed
    line not yet quarantined counts toward the total, so a read never understates the spend."""
    now = time.time() if now is None else now
    rows, bad = _read()
    per, total = _count(rows, now, window)
    return per, total + len(bad)


def status(now: float | None = None) -> dict:
    """Ledger health: admitted in the window, orphans (reserved, never settled, older than ORPHAN_AFTER_SEC), corrupt."""
    now = time.time() if now is None else now
    rows, bad = _read()
    settled = {r.get("decision_id") for r in rows if r.get("type") == "settle"}
    orphans = [r["decision_id"] for r in rows if r.get("type") == "reserve" and r.get("decision_id") not in settled
               and now - float(r.get("at") or 0) > ORPHAN_AFTER_SEC and now - float(r.get("at") or 0) <= WINDOW_SEC]
    return {"admitted": _count(rows, now, WINDOW_SEC)[1], "orphans": orphans, "corrupt_lines": len(bad)}


def decision_id(project: str | None, req: object, agent: str, model: str, at: float, nonce: int) -> str:
    return hashlib.sha1(f"{project}|{req}|{agent}|{model}|{at}|{nonce}".encode()).hexdigest()[:16]


def reserve(route: dict, project: str, req: object, reason: str, route_limit: int, global_limit: int | None,
            now: float | None = None, key: str | None = None) -> dict | None:
    """Atomically admit one exploration of `route` against the budgets and record it. Returns the decision record, or
    None when the route's weekly budget (`route_limit`, counted per agent+model; negative = none) or the optional global
    one is spent, or the ledger cannot be locked or written (fail closed). `key` makes it idempotent: the reservation of
    a decision already admitted for the same key is returned again, not charged again."""
    now = time.time() if now is None else now
    agent_model = (route.get("agent"), route.get("model"))
    try:
        with _exclusive():
            _heal_locked(now)
            rows, _ = _read()
            if key:
                for row in rows:
                    if row.get("type") == "reserve" and row.get("key") == key and \
                            (row.get("agent"), row.get("model")) == agent_model and \
                            now - float(row.get("at") or 0) <= WINDOW_SEC:
                        return row
            per, total = _count(rows, now, WINDOW_SEC)
            route_used = per.get(agent_model, 0)
            if route_limit >= 0 and route_used >= route_limit:
                return None
            if global_limit is not None and total >= global_limit:
                return None
            did = decision_id(project, req, str(agent_model[0]), str(agent_model[1]), now, total)
            record = {"type": "reserve", "decision_id": did, "key": key, "at": now,
                      "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)), "project": project, "req": req,
                      "profile": route.get("profile"), "account": route.get("account"), "agent": agent_model[0],
                      "model": agent_model[1], "kind": route.get("kind"), "tier": route.get("tier"),
                      "effort": route.get("effort"), "reason": reason,
                      "budget_before": {"route_used": route_used, "route_limit": route_limit,
                                        "global_used": total, "global_limit": global_limit}}
            with _path().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
                fh.flush()
            return record
    except OSError as exc:
        print(f"[explore] reservation refused (fail closed): {type(exc).__name__}: {exc}", file=sys.stderr)
        return None


def settle(did: str | None, result: str, verified: bool | None) -> None:
    """Record what the exploration produced (result, verification state), once per decision. Never raises."""
    if not did:
        return
    try:
        with _exclusive():
            _heal_locked(time.time())
            rows, _ = _read()
            if any(r.get("type") == "settle" and r.get("decision_id") == did for r in rows):
                return
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
