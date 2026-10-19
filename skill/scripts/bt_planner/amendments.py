"""Classification amendments: how a plan's estimate changes while it runs, without touching the approved plan.

An approved `PLAN.json` revision is immutable. What a task IS (its scope and criteria) only changes through a new
revision. How HARD it turned out to be (complexity, scope class, risk, coupling, confidence, estimate) is a finding of
the work itself, so it is recorded here, in the append-only `PLAN.amendments.jsonl` beside the plan:

    {seq, task, field, from, to, reason, evidence[], by, proposed_by, at, plan_ref: {plan_id, revision}}

An amendment never changes what to build and never names who runs it: a consumer reads `effective()` to learn the
classification in force. Rules (checked on append and again on read):
- only classification fields, with valid values, for a task of the plan revision the amendment is bound to;
- `from` must equal the value in force when it is written (a lost race is rejected, not silently overwritten);
- raising the level (harder, riskier, more coupled, less confident, longer) may be proposed by an agent with evidence;
  lowering needs `proposed_by == "owner"`; every amendment carries a reason.
Standard library only; the only file written is `PLAN.amendments.jsonl` (plus its lock file).
"""
from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

from . import contract as pc
from . import revisions as rev
from ._lock import exclusive

FILE = "PLAN.amendments.jsonl"
LOCK_NAME = ".amend.lock"
FIELDS = ("complexity", "scope", "risk", "coupling", "confidence", "estimated_minutes")
PROPOSERS = ("owner", "agent")
MAX_RECORDS = 10_000
# Order of each enum, easiest first. Confidence reads the other way round: LOWER confidence is the riskier direction.
_ORDER = {"complexity": pc.COMPLEXITY, "scope": pc.SCOPE, "risk": pc.LEVELS, "coupling": pc.LEVELS,
          "confidence": tuple(reversed(pc.LEVELS))}


class AmendmentError(pc.PlanContractError):
    """A refused or unreadable amendment; `code` is stable (see the raises below)."""


def path_of(directory: Path) -> Path:
    return Path(directory) / FILE


def _current_plan(directory: Path) -> dict:
    """The plan the amendments apply to: the latest frozen revision (what runs), else the working PLAN.json."""
    last = rev.latest(directory)
    if last:
        return rev.load_revision(directory, last["revision"])
    try:
        return pc.load(Path(directory) / "PLAN.json")
    except (OSError, ValueError) as exc:
        raise AmendmentError("AMEND_NO_PLAN", [f"{Path(directory).name}: no readable PLAN.json to amend"]) from exc


def _record_problem(record: object, plan: dict | None = None) -> str | None:
    if not isinstance(record, dict):
        return "not an object"
    for key in ("seq", "task", "field", "from", "to", "reason", "evidence", "by", "proposed_by", "at", "plan_ref"):
        if key not in record:
            return f"missing {key}"
    if record["field"] not in FIELDS:
        return f"field {record['field']!r} is not a classification field"
    problem = _value_problem(record["field"], record["to"]) or _value_problem(record["field"], record["from"])
    if problem:
        return problem
    if not isinstance(record["reason"], str) or not record["reason"].strip():
        return "empty reason"
    if not isinstance(record["evidence"], list) or not all(isinstance(e, str) and e.strip() for e in record["evidence"]):
        return "evidence must be a list of non-empty strings"
    if record["proposed_by"] not in PROPOSERS or not isinstance(record["by"], str) or not record["by"].strip():
        return "bad author"
    ref = record["plan_ref"]
    if not isinstance(ref, dict) or type(ref.get("revision")) is not int:
        return "bad plan_ref"
    if plan is not None and record["task"] not in {t.get("id") for t in plan.get("tasks", []) if isinstance(t, dict)}:
        return f"unknown task {record['task']!r}"
    return None


def _value_problem(field: str, value: object) -> str | None:
    if field == "estimated_minutes":
        ok = type(value) is int and 1 <= value <= pc.MAX_MINUTES
        return None if ok else f"estimated_minutes must be an integer between 1 and {pc.MAX_MINUTES}"
    allowed = _ORDER[field]
    return None if value in allowed else f"{field} must be one of {', '.join(allowed)}"


MAX_LINE = 65_536   # one amendment is a few hundred bytes; a longer line is not one


def read(directory: Path) -> list[dict]:
    """Every well-formed amendment, oldest first. A malformed or out-of-sequence line is skipped (never trusted).
    Reads at most MAX_RECORDS lines of at most MAX_LINE bytes, so a huge file cannot exhaust memory."""
    out: list[dict] = []
    try:
        with path_of(directory).open("rb") as handle:
            for _ in range(MAX_RECORDS):
                raw = handle.readline(MAX_LINE + 1)
                if not raw:
                    break
                if len(raw) > MAX_LINE:
                    break                                   # not a plausible record: stop rather than buffer it
                try:
                    record = json.loads(raw.decode("utf-8"))
                except (ValueError, UnicodeError):
                    continue
                if _record_problem(record) is None and record["seq"] == len(out) + 1:
                    out.append(record)
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise AmendmentError("AMEND_UNREADABLE", [f"{FILE}: {type(exc).__name__}"]) from exc
    return out


def effective(plan: dict, amendments: list[dict]) -> dict[str, dict[str, object]]:
    """{task id: {field: value in force}} for every classification field: the plan's own values with the amendments
    bound to this plan's revision applied in order. Pure."""
    revision = plan.get("revision")
    result: dict[str, dict[str, object]] = {}
    for task in plan.get("tasks", []):
        if isinstance(task, dict) and isinstance(task.get("id"), str):
            result[task["id"]] = {name: task.get(name) for name in FIELDS}
    for record in amendments:
        if record["plan_ref"].get("revision") != revision or record["task"] not in result:
            continue
        if result[record["task"]].get(record["field"]) == record["from"]:      # a stale `from` is ignored, not applied
            result[record["task"]][record["field"]] = record["to"]
    return result


def history(plan: dict, amendments: list[dict], task: str) -> list[dict]:
    """The amendments of one task that apply to this plan revision, oldest first."""
    return [r for r in amendments if r["task"] == task and r["plan_ref"].get("revision") == plan.get("revision")]


def direction(field: str, old: object, new: object) -> str:
    """`raise` | `lower` | `same`: which way an amendment moves the classification (harder is a raise)."""
    if old == new:
        return "same"
    if field == "estimated_minutes":
        return "raise" if new > old else "lower"
    order = _ORDER[field]
    return "raise" if order.index(new) > order.index(old) else "lower"


def append(directory: Path, task: str, field: str, to: object, *, reason: str, evidence: list[str] | None = None,
           by: str, proposed_by: str, now: dt.datetime | None = None) -> dict:
    """Validate and append one amendment; returns the record written. The plan the amendment binds to is read UNDER the
    amendment lock and, when revisions exist, under the freeze lock too, so a freeze cannot slip in between."""
    directory = Path(directory)
    if field not in FIELDS:
        raise AmendmentError("AMEND_FIELD", [f"{field!r} is not a classification field ({', '.join(FIELDS)})"])
    if proposed_by not in PROPOSERS:
        raise AmendmentError("AMEND_AUTHOR", [f"proposed_by must be one of {', '.join(PROPOSERS)}"])
    if not isinstance(by, str) or not by.strip():
        raise AmendmentError("AMEND_AUTHOR", ["`by` names who or what made the change"])
    if not isinstance(reason, str) or not reason.strip():
        raise AmendmentError("AMEND_REASON", ["an amendment needs a reason"])
    problem = _value_problem(field, to)
    if problem:
        raise AmendmentError("AMEND_VALUE", [problem])
    evidence = [e for e in (evidence or []) if isinstance(e, str) and e.strip()]
    with exclusive(directory / LOCK_NAME):
        if (directory / rev.DIR).is_dir():
            with exclusive(directory / rev.DIR / rev.LOCK_NAME):
                return _append_locked(directory, task, field, to, reason, evidence, by, proposed_by, now)
        return _append_locked(directory, task, field, to, reason, evidence, by, proposed_by, now)


def _append_locked(directory: Path, task: str, field: str, to: object, reason: str, evidence: list[str], by: str,
                   proposed_by: str, now: dt.datetime | None) -> dict:
    plan = _current_plan(directory)
    records = read(directory)
    in_force = effective(plan, records)
    if task not in in_force:
        raise AmendmentError("AMEND_TASK", [f"{task}: not a task of revision {plan.get('revision')}"])
    old = in_force[task][field]
    move = direction(field, old, to)
    if move == "same":
        raise AmendmentError("AMEND_NOOP", [f"{task}.{field} is already {to!r}"])
    if move == "lower" and proposed_by != "owner":
        raise AmendmentError("AMEND_LOWER_NEEDS_OWNER", [
            f"{task}.{field}: lowering {old!r} → {to!r} is the owner's call; an agent may only raise"])
    if proposed_by == "agent" and not evidence:
        raise AmendmentError("AMEND_EVIDENCE", [f"{task}.{field}: an agent's proposal needs evidence"])
    if len(records) >= MAX_RECORDS:
        raise AmendmentError("AMEND_FULL", [f"{FILE} holds {MAX_RECORDS} amendments"])
    stamp = (now or dt.datetime.now(dt.UTC)).astimezone(dt.UTC).isoformat(timespec="seconds")
    record = {"seq": len(records) + 1, "task": task, "field": field, "from": old, "to": to, "reason": reason.strip(),
              "evidence": evidence, "by": by.strip(), "proposed_by": proposed_by, "at": stamp,
              "plan_ref": {"plan_id": plan.get("plan_id"), "revision": plan.get("revision")}}
    with path_of(directory).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return record
