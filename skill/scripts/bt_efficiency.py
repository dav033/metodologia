"""Verified work per unit of quota, from the attempt telemetry (`bt_events`), with the provenance of every number.

Three rules keep the figures honest:
- Success is what the supervisor verified (`result` done/verified). A claim the verify then rejected (`verify_failed`)
  is counted separately as an unverified claim and never feeds a success rate.
- Consumption is reported twice and never merged: `measured` (tokens or cost the provider reported) and `estimated`
  (seconds x model cost x effort weight, a configurable heuristic). Each carries how many attempts back it.
- Every group states its sample size and a confidence label (lower bound of the success rate, 90 % one-sided).
"""
from __future__ import annotations

import json
import sys

import bt_routing_policy as policy

VERIFIED = ("done", "verified")
UNVERIFIED_CLAIM = ("verify_failed",)
FAILED = ("failed", "timeout", "partial")
JUDGED = VERIFIED + UNVERIFIED_CLAIM + FAILED
GROUP = ("agent", "model", "effort", "kind", "tier")


def _tokens(row: dict) -> int | None:
    usage = row.get("usage") or {}
    parts = [usage.get(k) for k in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens")]
    parts = [p for p in parts if isinstance(p, int) and not isinstance(p, bool)]
    return sum(parts) if parts else None


def _estimated_units(row: dict) -> float | None:
    import bt_agents
    seconds = row.get("seconds")
    if not isinstance(seconds, (int, float)) or isinstance(seconds, bool):
        return None
    cost = bt_agents.MODELS.get(str(row.get("model")), {}).get("cost", 2)
    return seconds * cost * policy.effort_weight(row.get("effort"))


def confidence(done: int, judged: int) -> str:
    lower = policy.wilson_lower(done, judged)
    if lower is None or judged < 5:
        return "insufficient"
    return "high" if judged >= 20 and lower >= 0.6 else "medium" if judged >= 10 else "low"


def summarize(rows: list[dict], by: tuple = GROUP) -> list[dict]:
    """One entry per group of real (non-synthetic) attempts."""
    groups: dict[tuple, dict] = {}
    for row in rows:
        if row.get("origin") == "synthetic" or not isinstance(row.get("result"), str):
            continue
        key = tuple(row.get(k) if k != "kind" else (row.get(k) or "implement") for k in by)
        g = groups.setdefault(key, {**dict(zip(by, key)), "attempts": 0, "verified": 0, "unverified_claims": 0,
                                    "failed": 0, "other": 0, "escalated": 0, "timeouts": 0, "recovered": 0,
                                    "seconds": 0, "tokens_measured": 0, "attempts_with_tokens": 0,
                                    "estimated_units": 0.0, "attempts_with_estimate": 0})
        g["attempts"] += 1
        result = row["result"]
        g["verified" if result in VERIFIED else "unverified_claims" if result in UNVERIFIED_CLAIM else
          "failed" if result in FAILED else "other"] += 1
        g["escalated"] += result == "escalated"
        g["timeouts"] += bool(row.get("timed_out")) or result == "timeout"
        g["recovered"] += bool(row.get("recovered"))
        g["seconds"] += row.get("seconds") or 0
        tokens = _tokens(row)
        if tokens is not None:
            g["tokens_measured"] += tokens
            g["attempts_with_tokens"] += 1
        units = _estimated_units(row)
        if units is not None:
            g["estimated_units"] += units
            g["attempts_with_estimate"] += 1
    out = []
    for g in groups.values():
        judged = g["verified"] + g["unverified_claims"] + g["failed"]
        done = g["verified"]
        g.update(
            judged=judged,
            verified_success_rate=done / judged if judged else None,
            success_lower_bound=policy.wilson_lower(done, judged),
            confidence=confidence(done, judged),
            claim_precision=done / (done + g["unverified_claims"]) if done + g["unverified_claims"] else None,
            attempts_per_verified=g["attempts"] / done if done else None,
            seconds_per_verified=g["seconds"] / done if done else None,
            # measured and estimated are separate columns: the first is only valid when every attempt reported it
            measured_tokens_per_verified=(g["tokens_measured"] / done if done and g["attempts_with_tokens"] == g["attempts"]
                                          else None),
            estimated_units_per_verified=(g["estimated_units"] / done if done and g["attempts_with_estimate"] else None),
            consumption_provenance={"measured_attempts": g["attempts_with_tokens"],
                                    "estimated_attempts": g["attempts_with_estimate"], "of": g["attempts"]})
        out.append(g)
    return sorted(out, key=lambda g: tuple(str(g.get(k)) for k in by))


def main(argv: list[str] | None = None) -> int:
    import bt_events
    json.dump(summarize(bt_events.read_all()), sys.stdout, indent=1, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
