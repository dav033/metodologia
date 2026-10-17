"""Verified work per unit of quota, from the attempt telemetry (`bt_events`), with the provenance of every number.

Rules that keep the figures honest:
- Success is what the supervisor verified, counted per TASK outcome (bt_outcomes): a session of three tasks with one
  failure is two verified tasks and one failure. A claim the verification then rejected (`verify_failed`) is counted
  separately as an unverified claim and never feeds a success rate. Synthetic rows (smoke tests, evals) are excluded.
- Consumption belongs to the SESSION and is counted once, however many tasks it carried: a multitask session is
  reported in `shared_sessions` and its cost is never attributed to each task. Dividing a group's cost by its verified
  tasks is a conserving average, labelled as such.
- Consumption is reported twice and never merged: `measured` (tokens the provider reported, normalized by bt_usage)
  and `estimated` (seconds x model cost x effort weight: a configurable heuristic in relative units, not tokens). Each
  carries its coverage. A per-verified figure exists only when EVERY session of the group is covered; otherwise it is
  null, `*_status` says `insufficient_coverage`, and the partial aggregates keep their own labelled fields.
- Groups are per account (`bt_agents.account_key` of the profile), provider, model, effort, kind and tier, so two
  accounts of one provider never mix. Every group states its sample size and a confidence label (lower bound of the
  verified success rate, 90 % one-sided).
"""
from __future__ import annotations

import json
import sys

import bt_outcomes
import bt_routing_policy as policy
import bt_usage

VERIFIED = ("done", "verified")
UNVERIFIED_CLAIM = ("verify_failed",)
FAILED = ("failed", "timeout", "partial")
GROUP = ("account", "agent", "model", "effort", "kind", "tier")
UNITS = {"seconds": "wall-clock seconds", "tokens": "provider tokens normalized by bt_usage (complete, comparable)",
         "estimated_units": "model cost x effort weight x seconds: relative heuristic units, not tokens"}


def _tokens(row: dict) -> int | None:
    """Final comparable tokens of a session (bt_usage): None for partial, total-only, contradictory or absent."""
    return bt_usage.comparable_total(row.get("usage"), row.get("agent"))


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


def _key(row: dict, by: tuple) -> tuple:
    import bt_agents
    out = []
    for k in by:
        if k == "account":
            out.append(bt_agents.account_key(row.get("profile"), row.get("agent")))
        elif k == "kind":
            out.append(row.get("kind") or "implement")
        else:
            out.append(row.get(k))
    return tuple(out)


def _ratio(total: float, count: int, covered: int, sessions: int) -> tuple[float | None, str]:
    if not count:
        return None, "no_verified_work"
    if not sessions or covered != sessions:
        return None, "insufficient_coverage"
    return total / count, "complete"


def summarize(rows: list[dict], by: tuple = GROUP) -> list[dict]:
    """One entry per group of real (non-synthetic) sessions and their task outcomes."""
    import bt_quality
    real = [r for r in rows if r.get("origin") != "synthetic" and isinstance(r.get("result"), str)]
    groups: dict[tuple, dict] = {}

    def group(row: dict) -> dict:
        key = _key(row, by)
        return groups.setdefault(key, {**dict(zip(by, key)), "units": UNITS, "sessions": 0, "shared_sessions": 0,
                                       "attempts": 0, "verified": 0, "unverified_claims": 0, "failed": 0, "other": 0,
                                       "skipped": 0, "retries": 0, "escalated": 0, "timeouts": 0, "recovered": 0,
                                       "seconds": 0, "sessions_with_seconds": 0, "tokens_measured": 0,
                                       "sessions_with_tokens": 0, "sessions_total_only": 0,
                                       "sessions_partial_tokens": 0, "estimated_units": 0.0,
                                       "sessions_with_estimate": 0, "rework": 0})

    for row in real:  # consumption: once per session
        g = group(row)
        g["sessions"] += 1
        g["shared_sessions"] += len(row.get("tasks") or []) > 1
        g["escalated"] += row["result"] == "escalated"
        g["timeouts"] += bool(row.get("timed_out")) or row["result"] == "timeout"
        g["recovered"] += bool(row.get("recovered"))
        if isinstance(row.get("seconds"), (int, float)) and not isinstance(row.get("seconds"), bool):
            g["seconds"] += row["seconds"]
            g["sessions_with_seconds"] += 1
        quality = bt_usage.normalize(row.get("usage"), row.get("agent"))["quality"]
        tokens = _tokens(row)
        if tokens is not None:
            g["tokens_measured"] += tokens
            g["sessions_with_tokens"] += 1
        elif quality == bt_usage.TOTAL_ONLY:
            g["sessions_total_only"] += 1
        elif quality in (bt_usage.PARTIAL, bt_usage.CONTRADICTORY):
            g["sessions_partial_tokens"] += 1
        units = _estimated_units(row)
        if units is not None:
            g["estimated_units"] += units
            g["sessions_with_estimate"] += 1
    for o in bt_outcomes.outcomes(real):  # quality: once per task outcome
        g = group(o["row"])
        result = o["result"]
        if o["verdict"] == "skipped":
            g["skipped"] += 1
            continue
        g["attempts"] += 1
        g["retries"] += o["retry"]
        g["verified" if result in VERIFIED else "unverified_claims" if result in UNVERIFIED_CLAIM else
          "failed" if o["verdict"] == "failed" else "other"] += 1
    rework = {eid for eid, _ in bt_quality.rework_events(real)}
    for row in real:
        if row.get("event_id") in rework:
            group(row)["rework"] += 1
    out = []
    for g in groups.values():
        judged = g["verified"] + g["unverified_claims"] + g["failed"]
        done, sessions = g["verified"], g["sessions"]
        per_tokens, tokens_status = _ratio(g["tokens_measured"], done, g["sessions_with_tokens"], sessions)
        per_units, units_status = _ratio(g["estimated_units"], done, g["sessions_with_estimate"], sessions)
        per_seconds, seconds_status = _ratio(g["seconds"], done, g["sessions_with_seconds"], sessions)
        g.update(
            judged=judged,
            verified_success_rate=done / judged if judged else None,
            success_lower_bound=policy.wilson_lower(done, judged),
            confidence=confidence(done, judged),
            claim_precision=done / (done + g["unverified_claims"]) if done + g["unverified_claims"] else None,
            retry_rate=g["retries"] / g["attempts"] if g["attempts"] else None,
            failure_rate=g["failed"] / judged if judged else None,
            rework_rate=g["rework"] / g["attempts"] if g["attempts"] and g["rework"] is not None else None,
            attempts_per_verified=g["attempts"] / done if done else None,
            seconds_per_verified=per_seconds, seconds_per_verified_status=seconds_status,
            # measured and estimated are separate columns; each is null unless every session of the group is covered
            measured_tokens_per_verified=per_tokens, measured_tokens_status=tokens_status,
            estimated_units_per_verified=per_units, estimated_units_status=units_status,
            token_coverage=g["sessions_with_tokens"] / sessions if sessions else None,
            estimate_coverage=g["sessions_with_estimate"] / sessions if sessions else None,
            consumption_provenance={"measured_attempts": g["sessions_with_tokens"],  # per session: its cost is paid once
                                    "estimated_attempts": g["sessions_with_estimate"], "of": sessions},
            token_quality={"complete": g["sessions_with_tokens"], "total_only": g["sessions_total_only"],
                           "partial_or_contradictory": g["sessions_partial_tokens"],
                           "unknown": sessions - g["sessions_with_tokens"] - g["sessions_total_only"]
                           - g["sessions_partial_tokens"]})
        out.append(g)
    return sorted(out, key=lambda g: tuple(str(g.get(k)) for k in by))


def main(argv: list[str] | None = None) -> int:
    import bt_events
    json.dump(summarize(bt_events.read_all()), sys.stdout, indent=1, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
