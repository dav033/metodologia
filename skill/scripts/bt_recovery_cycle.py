"""Bounded diagnostic-recovery cycle: durable ledger, trigger precedence and strategy identity (no M5 import).

Pure policy over plain mappings. RecoveryAdapter owns the M5 types and the case journal; this module owns the one
persisted cycle token per run/audit lineage, so restarts and duplicate triggers cannot add cycles.
"""
from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path

POLICY = {"schema_version": "diagnostic-policy/1", "cycles_per_lineage": 1, "max_corrective_tasks": 8,
          "diagnosis_invocations": 1, "supplemental_audit_attempts": 1, "no_progress_observations": 2}
PHASES = ("diagnose", "validate", "prepare", "apply", "execute", "integrate", "audit", "assess")
CONFLICT_SOURCES = ("start_conflict", "integration_gate")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                                     allow_nan=False).encode()).hexdigest()


def strategy_identity(strategy: dict, evidence: dict) -> str:
    """Structure plus semantic digests only: word choice (names, prose) never changes the identity."""
    return digest({"dag": sorted(map(list, strategy.get("dag", ()))),
                   "owner_paths": sorted(strategy.get("owner_paths", ())),
                   "outcomes": sorted(strategy.get("outcomes", ())), "checks": sorted(strategy.get("checks", ())),
                   "semantic": evidence.get("semantic_digest"), "source": evidence.get("source_digest"),
                   "check": evidence.get("check_digest")})


def unchanged_loop(observations: list) -> bool:
    """Two consecutive VERIFIED observations with equal semantic/source/check digests. Verdict ids are ignored and an
    unverified one (provider outage, missing evidence) is not no-progress."""
    last = [o for o in observations[-2:] if isinstance(o, dict)]
    if len(last) < POLICY["no_progress_observations"] or not all(o.get("verified") is True for o in last):
        return False
    keys = ("semantic_digest", "source_digest", "check_digest")
    return all(isinstance(last[0].get(k), str) and last[0].get(k) for k in keys) and \
        all(last[0].get(k) == last[1].get(k) for k in keys)


def trigger_reason(obs: dict) -> str | None:
    if obs.get("source") in CONFLICT_SOURCES:
        return "integration_conflict"           # structural, recognized before any generic verification retry
    if obs.get("ordinary_exhausted") is True:
        return "ordinary_exhausted"
    if unchanged_loop(obs.get("observations") or []):
        return "unchanged_evidence"
    return None


def validate_route(route: object, live: dict) -> str:
    """'' when the Planner-role route is present, current and authorized; otherwise the rejection code."""
    if not isinstance(route, dict) or not route:
        return "route_absent"
    if route.get("role") != "planner":
        return "route_not_planner"
    if (route.get("run_identity"), route.get("plan_sha256"), route.get("revision")) != \
            (live.get("run_identity"), live.get("plan_sha256"), live.get("revision")):
        return "route_stale"
    if route.get("authorized") is not True or not route.get("authorization_ref") or not route.get("decision_ref"):
        return "route_unauthorized"
    return ""


class Ledger:
    """Atomic JSON file guarded by flock: the source of truth for cycle tokens, activation and corrective budgets."""

    def __init__(self, path: Path | str):
        self.path = Path(path)

    @contextlib.contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix(".lock").open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            data = self.read()
            before = json.dumps(data, sort_keys=True)
            yield data
            if json.dumps(data, sort_keys=True) != before:
                tmp = self.path.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
                os.chmod(tmp, 0o600)
                os.replace(tmp, self.path)

    def read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if not isinstance(data, dict):
            data = {}
        data.setdefault("schema_version", "recovery-cycles/1")
        data.setdefault("cycles", {})
        data.setdefault("aliases", {})
        data.setdefault("enabled", None)
        return data


def resolve_cycle(data: dict, run_identity: str, aliases: list[str]) -> tuple[str, bool]:
    """Token of the cycle owning any alias (audit and conflict lineages share one), else a new deterministic token."""
    aliases = sorted({a for a in aliases if isinstance(a, str) and a})
    known = sorted({data["aliases"][a] for a in aliases if a in data["aliases"]},
                   key=lambda t: (data["cycles"].get(t, {}).get("created_at", 0), t))
    token, created = (known[0], False) if known else ("cycle-" + digest([run_identity, aliases[:1]])[:32], True)
    cycle = data["cycles"].get(token)
    if cycle is not None:
        created = False
    for alias in aliases:
        data["aliases"].setdefault(alias, token)
        if cycle is not None and alias not in cycle["aliases"]:
            cycle["aliases"].append(alias)
    return token, created


def new_cycle(token: str, aliases: list[str], reason: str, now: float, evidence: dict) -> dict:
    return {"token": token, "aliases": sorted(set(aliases)), "created_at": now, "state": "open", "phase": "diagnose",
            "trigger": reason, "evidence": evidence, "route": None, "diagnosis_invocations": 0,
            "corrective_tasks": 0, "supplemental_audits": {}, "strategies": [], "blocker": None,
            "escalated": False, "progress": None}


def block(cycle: dict, code: str, detail: str = "") -> bool:
    """Record the exact blocker once; True when it is new (the caller escalates)."""
    if cycle["blocker"] is not None:
        return False
    cycle.update(blocker={"code": code, "detail": detail[:200]}, state="failed")
    return True


def summary(cycle: dict) -> dict:
    keep = ("token", "state", "phase", "trigger", "diagnosis_invocations", "corrective_tasks", "supplemental_audits",
            "blocker", "escalated", "aliases")
    return {k: cycle[k] for k in keep}
