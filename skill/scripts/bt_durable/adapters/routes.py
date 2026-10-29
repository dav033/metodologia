"""Router ports over the operator's allowed routes (`execution.routes`, in preference order).

`M2Router` (the default) asks the M2 decision engine, through its one methodology door (`bt_scheduler_decision_adapter`,
reached via `bt_durable.legacy`), to rank the allowed routes for each task: M2's hard filters (authorization, runtime,
authentication, capacity, cooldown), its route policy and its per-account matching. `LiveQuota` stays the capacity
signal. `StaticRouter` is the fallback (`execution.router = static`, or when M2 cannot be built): the ordered list
with the same capacity callback.

Both answer inside the `bt.route` step, so a decision is checkpointed by DBOS and replayed, never recomputed, for a
recovered workflow; the workflow's step sequence is the same whichever router is wired.
"""
from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass

from bt_contracts.execution import Route, RouteDecision, RunRef

from ..legacy import TaskSpec

LOG = logging.getLogger("bt_durable.routes")

Capacity = Callable[[Route], tuple[float | None, float | None]]   # (remaining or None if unknown, reset epoch)
Emit = Callable[..., None]                                        # Telemetry.emit
# M2 reasons that only say "we do not know": with `allow_unknown` such a route may still run, after every route whose
# capacity is known; a known refusal (exhausted, cooling down, unauthorized, signed out, no runtime) never runs
UNKNOWN_ONLY = frozenset({"quota_unknown", "quota_stale", "auth_unknown", "capacity_unknown"})
# reasons that pass with time: only a route refused for these alone makes its reset or cooldown end worth waiting for
TEMPORARY = UNKNOWN_ONLY | {"quota_exhausted", "capacity_exhausted", "route_cooling_down", "cooldown_active",
                            "source_temporarily_unavailable"}


def key(route: Route) -> str:
    return f"{route.provider}:{route.profile}:{route.model}"


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


@dataclass(frozen=True)
class Reading:
    """One capacity reading of a route's account. `state`: available | exhausted | unknown. `reset_at`: when an
    exhausted account frees up (None when unknown). `status`: the reading's own status code (`ok`, `http_429`,
    `invalid_credentials`, `no_profile`, ...), which tells an expired sign-in apart from a reading that failed."""
    state: str
    used_percent: float | None = None
    observed_at: float | None = None
    reset_at: float | None = None
    status: str = "no_reading"


class LiveQuota:
    """Capacity from the subscription readings `globalusage` uses (bt_quota_live: read-only, cached 60 s, no model
    calls). A window at or above `ceiling` percent means no capacity until its reset; an account that cannot be read
    is unknown, never invented — neither as full nor as free."""

    def __init__(self, ceiling: float = 95.0, reader=None):
        self.ceiling = ceiling
        self.reader = reader

    def reading(self, route: Route, now: float | None = None) -> Reading:
        if not route.profile:
            return Reading("unknown", status="no_profile")
        try:
            rows = self.reader() if self.reader else __import__("bt_quota_live").read_all_live()
        except Exception as error:  # noqa: BLE001 - a failed reading is "unknown", not "full"
            return Reading("unknown", status=f"read_failed:{type(error).__name__}"[:80])
        row = next((r for r in rows if isinstance(r, dict) and r.get("profile") == route.profile), None)
        if not row:
            return Reading("unknown")
        observed = _number(row.get("observed_at"))
        if row.get("status") != "ok":
            return Reading("unknown", observed_at=observed, status=str(row.get("status"))[:80])
        windows = [w for w in (row.get("windows") or {}).values()
                   if isinstance(w, dict) and _number(w.get("used_percent")) is not None]
        if not windows:
            return Reading("unknown", observed_at=observed, status="no_windows")
        used = max(_number(w.get("used_percent")) for w in windows)
        full = [w for w in windows if _number(w.get("used_percent")) >= self.ceiling]
        if not full:
            return Reading("available", used, observed, None, "ok")
        resets = [r for w in full if (r := _number(w.get("resets_at")))]
        if resets and max(resets) <= (time.time() if now is None else now):
            # the full window has already reset: the reading is older than the account's state, so it says nothing
            return Reading("unknown", used, observed, None, "reset_passed")
        return Reading("exhausted", used, observed, max(resets) if resets else None, "ok")

    def __call__(self, route: Route) -> tuple[float | None, float | None]:
        """The `Capacity` callback of the static router."""
        found = self.reading(route)
        if found.state == "available":
            return 100.0 - (found.used_percent or 0.0), None
        if found.state == "exhausted":
            return 0.0, found.reset_at
        return None, None


def reading_of(capacity, route: Route, now: float) -> Reading:
    """A `Reading` from any capacity source: `LiveQuota` answers one directly; a plain callback's (remaining, reset)
    is translated (a positive remaining is an observation made now)."""
    if capacity is None:
        return Reading("unknown", status="no_capacity_source")
    if hasattr(capacity, "reading"):
        return capacity.reading(route, now)
    try:
        remaining, reset = capacity(route)
    except Exception as error:  # noqa: BLE001 - as LiveQuota: a failed reading is unknown
        return Reading("unknown", status=f"read_failed:{type(error).__name__}"[:80])
    if remaining is None:
        return Reading("unknown")
    if remaining > 0:
        return Reading("available", max(0.0, min(99.0, 100.0 - remaining)), now, None, "ok")
    return Reading("exhausted", 100.0, now, reset if reset and reset > now else None, "ok")


class StaticRouter:
    def __init__(self, routes: Sequence[Route], capacity: Capacity | None = None):
        if not routes:
            raise ValueError("at least one allowed route is required")
        self.routes = tuple(routes)
        self.capacity = capacity

    def _allowed(self, exclude: tuple[str, ...]) -> list[Route]:
        return [r for r in self.routes if key(r) not in exclude]

    def decide(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...], now: float) -> RouteDecision:
        allowed = self._allowed(exclude)
        if not allowed:
            return RouteDecision(kind="unavailable", reason="every allowed route was excluded for this task")
        resets = []
        for route in allowed:
            remaining, reset = self.capacity(route) if self.capacity else (None, None)
            if remaining is None or remaining > 0:
                return RouteDecision(kind="run", route=route)
            if reset:
                resets.append(reset)
        if resets:
            return RouteDecision(kind="wait", not_before=min(resets), reason="no allowed route has capacity now")
        return RouteDecision(kind="unavailable", reason="no allowed route has capacity and no reset time is known")

    def alternatives(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...]) -> int:
        return len(self._allowed(exclude))


class M2Router:
    """The allowed routes ranked by M2 for each task.

    - M2's choice runs: the best eligible route by its route policy, one candidate per account.
    - A route M2 refuses for a known reason (exhausted, cooling down, not authorized, signed out, no runtime) is
      never chosen, so no attempt is spent on it.
    - With `allow_unknown`, a route whose capacity simply cannot be read runs only when no route has known capacity,
      in the operator's order (the static list's behaviour for unknown capacity; the agent's own usage-limit answer is
      then classified QUOTA and waited for durably). Without it, unknown counts as unusable.
    - Otherwise: `wait` until the earliest known reset or cooldown end, or `unavailable` when none is known.

    Every decision — chosen route, ranked candidates, rejected ones with M2's reasons, capacity readings, the batch
    identity — is emitted to the telemetry callable injected at wiring.
    """

    def __init__(self, routes: Sequence[Route], capacity=None, *, telemetry: Emit | None = None,
                 allow_unknown: bool = True, decision=None):
        if not routes:
            raise ValueError("at least one allowed route is required")
        if decision is None:
            from ..legacy import decision
        self.routes = tuple(routes)
        self.capacity = capacity
        self.telemetry = telemetry
        self.allow_unknown = allow_unknown
        self.decision = decision
        # prove M2 accepts these routes now (identities, profiles), so a broken setup falls back at wiring, not mid-run
        self.decision.durable_route_ranking(
            "probe", plan_id="probe", revision=1, plan_sha256="0" * 64, task_id="probe", meta={},
            routes=[self._facts(route, Reading("unknown", status="probe")) for route in self.routes],
            now=time.time(), with_history=False)

    @staticmethod
    def _facts(route: Route, reading: Reading) -> dict:
        return {"provider": route.provider, "model": route.model, "profile": route.profile, "effort": route.effort,
                "capacity": reading.state, "used_percent": reading.used_percent, "observed_at": reading.observed_at,
                "status": reading.status}

    def _rank(self, run: RunRef, task: TaskSpec, allowed: list[Route], now: float, *, history: bool):
        readings = [reading_of(self.capacity, route, now) for route in allowed]
        ranking = self.decision.durable_route_ranking(
            run.project, plan_id=run.plan_id, revision=run.revision, plan_sha256=run.plan_sha256, task_id=task.id,
            meta=task.meta, dependencies=task.after, acceptance_criteria=task.acceptance_criteria,
            verification=task.verification, shared_resources=task.shared_resources,
            expected_paths=task.expected_paths, routes=[self._facts(r, x) for r, x in zip(allowed, readings)],
            now=now, with_history=history)
        return readings, ranking

    def _unknown_fallback(self, ranking: dict) -> int | None:
        if not self.allow_unknown:
            return None
        rejected = {item["index"]: set(item["reasons"]) for item in ranking["rejected"]}
        return next((i for i in sorted(rejected) if rejected[i] and rejected[i] <= UNKNOWN_ONLY), None)

    def decide(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...], now: float) -> RouteDecision:
        allowed = [r for r in self.routes if key(r) not in exclude]
        if not allowed:
            decision = RouteDecision(kind="unavailable", reason="every allowed route was excluded for this task")
            self._emit(run, task, exclude, decision, "none", [], [], None)
            return decision
        readings, ranking = self._rank(run, task, allowed, now, history=True)
        chosen, basis = ranking["selected"], "m2"
        if chosen is None:
            chosen, basis = self._unknown_fallback(ranking), "unknown_capacity"
        if chosen is not None:
            route = allowed[chosen].model_copy(update={"reference": self._reference(ranking, chosen, basis)})
            decision = RouteDecision(kind="run", route=route,
                                     reason=f"{basis}: {ranking['assignment_reason'] or 'only routes of unknown capacity'}")
        else:
            basis = "none"
            frees = []
            for item in ranking["rejected"]:
                if not set(item["reasons"]) <= TEMPORARY:
                    continue
                reading, cooling = readings[item["index"]], ranking["routes"][item["index"]]["cooldown_until"]
                if reading.state == "exhausted" and reading.reset_at and reading.reset_at > now:
                    frees.append(reading.reset_at)
                elif cooling and cooling > now:
                    frees.append(cooling)
            reasons = ", ".join(sorted({r for item in ranking["rejected"] for r in item["reasons"]}))
            if frees:
                decision = RouteDecision(kind="wait", not_before=min(frees),
                                         reason=f"no allowed route has capacity now ({reasons})"[:500])
            else:
                decision = RouteDecision(kind="unavailable",
                                         reason=f"no allowed route can run and no reset time is known ({reasons})"[:500])
        self._emit(run, task, exclude, decision, basis, allowed, readings, ranking)
        return decision

    def alternatives(self, run: RunRef, task: TaskSpec, *, exclude: tuple[str, ...]) -> int:
        """Routes, other than the excluded ones, that could run now: what makes switching routes worth an attempt."""
        allowed = [r for r in self.routes if key(r) not in exclude]
        if not allowed:
            return 0
        _, ranking = self._rank(run, task, allowed, time.time(), history=False)
        unknown = 0
        if self.allow_unknown:
            unknown = sum(1 for item in ranking["rejected"] if item["reasons"] and set(item["reasons"]) <= UNKNOWN_ONLY)
        return len(ranking["ranked"]) + unknown

    @staticmethod
    def _reference(ranking: dict, index: int, basis: str) -> str:
        route_id = ranking["routes"][index]["route_id"]
        return f"m2:{ranking['batch_id']}:{route_id}" if basis == "m2" else f"m2-unknown:{route_id}"

    def _emit(self, run: RunRef, task: TaskSpec, exclude, decision: RouteDecision, basis: str,
              allowed: list[Route], readings: list[Reading], ranking: dict | None) -> None:
        if self.telemetry is None:
            return
        ranking = ranking or {}
        described = ranking.get("routes") or []

        def entry(index: int) -> dict:
            return {"route": key(allowed[index]), "effort": allowed[index].effort,
                    "account_ref": described[index]["account_ref"] if index < len(described) else None}
        try:
            self.telemetry(
                "route_decision", router="m2", run_id=run.run_id, project=run.project, req=run.req,
                revision=run.revision, task_id=task.id, kind=decision.kind, basis=basis,
                route=key(decision.route) if decision.route else None,
                effort=decision.route.effort if decision.route else None, not_before=decision.not_before,
                reason=decision.reason, exclude=list(exclude),
                ranked=[entry(i) for i in ranking.get("ranked", [])],
                rejected=[{**entry(item["index"]), "reasons": item["reasons"]} for item in ranking.get("rejected", [])],
                capacity={key(route): {**asdict(reading),
                                       "cooldown_until": described[i].get("cooldown_until") if i < len(described) else None}
                          for i, (route, reading) in enumerate(zip(allowed, readings))},
                task_kind=ranking.get("task_kind"), preserve_baseline=ranking.get("preserve_baseline"),
                assignment_reason=ranking.get("assignment_reason"), unassigned_reason=ranking.get("unassigned_reason"),
                batch_id=ranking.get("batch_id"), input_sha256=ranking.get("input_sha256"),
                policy=ranking.get("policy_version"), route_policy=ranking.get("route_policy_version"),
                batch_policy=ranking.get("batch_policy_version"))
        except Exception as error:  # noqa: BLE001 - telemetry never changes a routing decision
            LOG.warning("route telemetry failed: %s", error)


def build_router(kind: str, routes: Sequence[Route], capacity=None, *, telemetry: Emit | None = None):
    """`execution.router`: `m2` (default) or `static`. When M2 cannot be built the static list runs and the reason is
    logged and emitted, so the engine starts either way and the operator sees why."""
    if kind == "static":
        return StaticRouter(routes, capacity)
    if kind != "m2":
        raise ValueError(f"execution.router must be 'm2' or 'static', not {kind!r}")
    try:
        return M2Router(routes, capacity, telemetry=telemetry)
    except Exception as error:  # noqa: BLE001 - any failure to build M2 falls back to the static list, visibly
        reason = f"{type(error).__name__}: {error}"[:500]
        LOG.warning("M2 router unavailable, using the static route list: %s", reason)
        if telemetry is not None:
            telemetry("router_fallback", router="static", reason=reason)
        return StaticRouter(routes, capacity)
