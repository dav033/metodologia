"""PLAN 1.3.0 subplan contracts and their derived runtime views."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from .errors import SchedulerError
from .model import RunState
from .states import TaskState as T

if TYPE_CHECKING:
    from .plan import Plan

_ID = re.compile(r"SP-[1-9][0-9]*\Z")
_GATE_ID = re.compile(r"CG-[1-9][0-9]*\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40,64}\Z")
_SLUG = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")


def _extension_entries_valid(item: dict[str, Any], where: str) -> dict[str, tuple[MappingProxyType, ...]]:
    result = {}
    for key in ("produces", "consumes", "checkpoints"):
        entries = item.get(key, [])
        if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
            raise SchedulerError("PLAN_INVALID", f"{where}.{key} must be a list of objects")
        for entry in entries:
            if key == "produces":
                valid = (isinstance(entry.get("contract"), str) and bool(_SLUG.fullmatch(entry["contract"])) and
                         type(entry.get("version")) is int and 1 <= entry["version"] <= 1000 and
                         isinstance(entry.get("defined_by"), str) and entry["defined_by"].strip() and
                         ("interfaces" not in entry or _strings(entry["interfaces"])))
            elif key == "consumes":
                valid = (isinstance(entry.get("contract"), str) and bool(_SLUG.fullmatch(entry["contract"])) and
                         type(entry.get("version")) is int and 1 <= entry["version"] <= 1000 and
                         isinstance(entry.get("from"), str) and entry["from"].strip() and
                         isinstance(entry.get("dependency"), str) and
                         entry["dependency"] in {"contract", "implementation", "publication"} and
                         ("verified_by" not in entry or _strings(entry["verified_by"])))
            else:
                valid = (isinstance(entry.get("task"), str) and entry["task"].strip() and
                         isinstance(entry.get("purpose"), str) and entry["purpose"].strip())
            if not valid:
                raise SchedulerError("PLAN_INVALID", f"{where}.{key} contains a malformed entry")
        result[key] = tuple(_freeze(entry) for entry in entries)
    return result


@dataclass(frozen=True)
class SubplanUI:
    contract: str
    version: int
    design_task: str
    visual_review_task: str


@dataclass(frozen=True)
class SubplanSpec:
    id: str
    milestone_id: str
    title: str
    outcome: str
    covers: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    integration_test_task: str
    audit_task: str
    ui: SubplanUI | None = None
    produces: tuple[MappingProxyType, ...] = ()
    consumes: tuple[MappingProxyType, ...] = ()
    checkpoints: tuple[MappingProxyType, ...] = ()


@dataclass(frozen=True)
class CompositionGateSpec:
    id: str
    subplans: tuple[str, ...]
    task: str
    audit_task: str | None = None
    criteria: tuple[str, ...] = ()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _strings(value: object, *, nonempty: bool = False) -> bool:
    return (isinstance(value, list) and (not nonempty or bool(value)) and
            all(isinstance(item, str) and bool(item.strip()) for item in value))


def _accepted_attempt(state: RunState, task_id: str) -> str | None:
    rec = state.tasks.get(task_id)
    if rec is None or rec.state != T.COMPLETED.value or not rec.attempts:
        return None
    attempt_id = rec.attempts[-1]
    attempt = state.attempts.get(attempt_id)
    return attempt_id if attempt is not None and attempt.state == "accepted" else None


def _accepted_identity(plan: Plan, state: RunState, subplan: SubplanSpec) -> dict[str, str] | None:
    """Bind publication to the accepted audit and all accepted member attempts."""
    audit_attempt = _accepted_attempt(state, subplan.audit_task)
    members = sorted(spec.id for spec in plan.tasks if spec.meta.get("subplan_id") == subplan.id)
    accepted = {task_id: _accepted_attempt(state, task_id) for task_id in members}
    if audit_attempt is None or any(attempt_id is None for attempt_id in accepted.values()):
        return None
    work_digest = hashlib.sha256(json.dumps(accepted, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"audit_attempt_id": audit_attempt, "work_digest": work_digest}


def _fact_is_current(plan: Plan, state: RunState, subplan: SubplanSpec) -> bool:
    fact = state.subplan_versions.get(subplan.id, {})
    identity = _accepted_identity(plan, state, subplan)
    return (identity is not None and fact.get("plan_id") == state.plan_id and
            fact.get("revision") == state.revision and
            {key: fact.get(key) for key in identity} == identity)


def stale_subplan_members(plan: Plan, state: RunState, task_id: str) -> tuple[tuple[str, str], ...]:
    """Return missing or stale publications required by this gate, with an attention reason per member."""
    gates = [gate for gate in plan.composition_gates if gate.task == task_id]
    by_id = {subplan.id: subplan for subplan in plan.subplans}
    waiting = []
    for gate in gates:
        for member in gate.subplans:
            fact = state.subplan_versions.get(member)
            if fact is None:
                waiting.append((member, "unpublished_subplan_version"))
            elif not _fact_is_current(plan, state, by_id[member]):
                waiting.append((member, "stale_subplan_version"))
    return tuple(waiting)


def parse_plan_extensions(data: dict[str, Any], task_ids: set[str]) -> tuple[tuple[SubplanSpec, ...], tuple[CompositionGateSpec, ...]]:
    raw_subplans = data.get("subplans", [])
    raw_gates = data.get("composition_gates", [])
    if (not isinstance(raw_subplans, list) or len(raw_subplans) > 64 or
            not isinstance(raw_gates, list) or len(raw_gates) > 32):
        raise SchedulerError("PLAN_INVALID", "subplans/composition_gates must be bounded lists")
    subplans: list[SubplanSpec] = []
    seen: set[str] = set()
    for index, item in enumerate(raw_subplans):
        where = f"subplans[{index}]"
        if not isinstance(item, dict):
            raise SchedulerError("PLAN_INVALID", f"{where} must be an object")
        sid, milestone, title, outcome = (item.get(k) for k in ("id", "milestone_id", "title", "outcome"))
        covers, criteria = item.get("covers"), item.get("acceptance_criteria")
        integration, audit = item.get("integration_test_task"), item.get("audit_task")
        if (not isinstance(sid, str) or not _ID.fullmatch(sid) or sid in seen or
                not all(isinstance(v, str) and v.strip() for v in (milestone, title, outcome, integration, audit)) or
                not _strings(covers, nonempty=True) or not _strings(criteria, nonempty=True) or
                integration not in task_ids or audit not in task_ids):
            raise SchedulerError("PLAN_INVALID", f"{where} has malformed required fields")
        seen.add(sid)
        ui = None
        if "ui" in item:
            value = item["ui"]
            if (not isinstance(value, dict) or not isinstance(value.get("contract"), str) or
                    not _SLUG.fullmatch(value["contract"]) or type(value.get("version")) is not int or
                    not 1 <= value["version"] <= 1000 or
                    value["version"] < 1 or not all(isinstance(value.get(k), str) and value[k].strip()
                                                    for k in ("design_task", "visual_review_task")) or
                    value.get("design_task") not in task_ids or value.get("visual_review_task") not in task_ids):
                raise SchedulerError("PLAN_INVALID", f"{where}.ui is malformed")
            ui = SubplanUI(value["contract"], value["version"], value["design_task"], value["visual_review_task"])
        extension_values = _extension_entries_valid(item, where)
        subplans.append(SubplanSpec(sid, milestone, title, outcome, tuple(covers), tuple(criteria), integration, audit,
                                    ui, extension_values["produces"], extension_values["consumes"],
                                    extension_values["checkpoints"]))
    gates: list[CompositionGateSpec] = []
    seen_gates: set[str] = set()
    subplan_ids = {item.id for item in subplans}
    for index, item in enumerate(raw_gates):
        where = f"composition_gates[{index}]"
        if not isinstance(item, dict):
            raise SchedulerError("PLAN_INVALID", f"{where} must be an object")
        gid, members, task_id = item.get("id"), item.get("subplans"), item.get("task")
        audit_task, criteria = item.get("audit_task"), item.get("criteria")
        if (not isinstance(gid, str) or not _GATE_ID.fullmatch(gid) or gid in seen_gates or
                not _strings(members, nonempty=True) or len(members) != len(set(members)) or
                any(member not in subplan_ids for member in members) or not isinstance(task_id, str) or
                task_id not in task_ids or
                (audit_task is not None and (not isinstance(audit_task, str) or audit_task not in task_ids)) or
                not _strings(criteria, nonempty=True)):
            raise SchedulerError("PLAN_INVALID", f"{where} has malformed fields")
        seen_gates.add(gid)
        gates.append(CompositionGateSpec(gid, tuple(members), task_id, audit_task, tuple(criteria)))
    return tuple(subplans), tuple(gates)


def subplan_status(plan: Plan, state: RunState) -> dict[str, str]:
    statuses = {}
    for subplan in plan.subplans:
        if _fact_is_current(plan, state, subplan):
            status = "published"
        else:
            audit_state = state.tasks[subplan.audit_task].state
            if audit_state == T.COMPLETED.value:
                status = "accepted"
            elif audit_state in {T.READY.value, T.ACTIVE.value, T.RECOVERING.value}:
                status = "auditing"
            else:
                status = "open"
        statuses[subplan.id] = status
    return statuses


def gate_ready(plan: Plan, state: RunState, task_id: str) -> bool:
    return not stale_subplan_members(plan, state, task_id)


def gate_waiting(plan: Plan, state: RunState, task_id: str) -> bool:
    return bool(stale_subplan_members(plan, state, task_id))


def validate_subplan_version(subplan_id: object, version: object, commit: object, digest: object) -> bool:
    return (isinstance(subplan_id, str) and bool(_ID.fullmatch(subplan_id)) and
            type(version) is int and version >= 1 and isinstance(commit, str) and bool(_COMMIT.fullmatch(commit)) and
            isinstance(digest, str) and bool(_SHA.fullmatch(digest)))


def validate_composition(state: object, composition_id: object, members: object, digest: object,
                         reason: object = "") -> bool:
    return (isinstance(state, str) and state in {"candidate", "published", "rejected"} and
            isinstance(composition_id, str) and
            1 <= len(composition_id) <= 128 and isinstance(members, dict) and 1 <= len(members) <= 64 and
            all(isinstance(key, str) and bool(_ID.fullmatch(key)) and type(value) is int and value >= 1
                for key, value in members.items()) and isinstance(digest, str) and bool(_SHA.fullmatch(digest)) and
            isinstance(reason, str) and len(reason) <= 500)


def record_subplan_version_fact(plan: Plan, state: RunState, ctx: Any, subplan_id: str, version: int,
                                commit: str, manifest_sha256: str) -> None:
    if not validate_subplan_version(subplan_id, version, commit, manifest_sha256):
        raise SchedulerError("CONTRACT_VIOLATION", "subplan version fact is malformed")
    if plan.schema_version != "1.3.0" or subplan_id not in {item.id for item in plan.subplans}:
        raise SchedulerError("NOT_ALLOWED", "subplan version facts require a declared 1.3.0 subplan")
    subplan = next(item for item in plan.subplans if item.id == subplan_id)
    identity = _accepted_identity(plan, state, subplan)
    if identity is None:
        raise SchedulerError("NOT_ALLOWED", "subplan publication requires all member work and its audit to be accepted")
    current = state.subplan_versions.get(subplan_id)
    fact = {"plan_id": state.plan_id, "revision": state.revision, "version": version,
            "commit": commit, "manifest_sha256": manifest_sha256, **identity}
    if current == fact:
        return
    if (current is not None and current.get("version") == version and current.get("commit") == commit and
            current.get("manifest_sha256") == manifest_sha256 and
            {key: current.get(key) for key in identity} == identity and current.get("plan_id") == state.plan_id):
        state.subplan_versions[subplan_id] = fact
        ctx.audit("subplan_version_published", subplan_id=subplan_id, version=version, rebound=True,
                  from_revision=current.get("revision"), to_revision=state.revision,
                  commit=commit, manifest_sha256=manifest_sha256)
        return
    expected = 1 if current is None else current["version"] + 1
    if version != expected:
        raise SchedulerError("NOT_ALLOWED", f"subplan version must advance from {expected - 1} to {expected}")
    state.subplan_versions[subplan_id] = fact
    ctx.audit("subplan_version_published", subplan_id=subplan_id, version=version,
              commit=commit, manifest_sha256=manifest_sha256)


def record_composition_fact(plan: Plan, state: RunState, ctx: Any, fact_state: str, composition_id: str,
                            members: dict[str, int], manifest_sha256: str, reason: str = "") -> None:
    if not validate_composition(fact_state, composition_id, members, manifest_sha256, reason):
        raise SchedulerError("CONTRACT_VIOLATION", "composition fact is malformed")
    declared = {item.id for item in plan.subplans}
    if plan.schema_version != "1.3.0" or not members or not set(members).issubset(declared):
        raise SchedulerError("NOT_ALLOWED", "composition facts require declared 1.3.0 subplans")
    specs = {subplan.id: subplan for subplan in plan.subplans}
    if fact_state == "published" and any(
            state.subplan_versions.get(sid, {}).get("version") != version or
            not _fact_is_current(plan, state, specs[sid]) for sid, version in members.items()):
        raise SchedulerError("NOT_ALLOWED", "published composition members need matching published versions")
    fact = {"plan_id": state.plan_id, "revision": state.revision, "state": fact_state,
            "members": dict(members), "manifest_sha256": manifest_sha256, "reason": reason}
    current = state.compositions.get(composition_id)
    if current == fact:
        return
    if (current is not None and current["state"] == "candidate" and
            current["manifest_sha256"] != manifest_sha256):
        raise SchedulerError("NOT_ALLOWED", "composition candidates are immutable under the same id; use a new candidate id")
    if current is not None and (current["state"] != "candidate" or fact_state == "candidate"):
        raise SchedulerError("NOT_ALLOWED", "composition facts are terminal after publication or rejection")
    state.compositions[composition_id] = fact
    detail = {"composition_id": composition_id, "members": members, "manifest_sha256": manifest_sha256, "reason": reason}
    if fact_state == "published":
        ctx.audit("composition_published", **detail)
    elif fact_state == "rejected":
        ctx.audit("composition_rejected", **detail)
    else:
        ctx.audit("composition_candidate", **detail)


def adapter_record_subplan_version(scheduler: Any, subplan_id: str, version: int, commit: str,
                                  manifest_sha256: str) -> None:
    """Callable surface the methodology adapter forwards while preserving the one-way boundary."""
    scheduler.record_subplan_version(subplan_id, version, commit, manifest_sha256)


def adapter_record_composition(scheduler: Any, state: str, composition_id: str, members: dict[str, int],
                               manifest_sha256: str, reason: str = "") -> None:
    scheduler.record_composition(state, composition_id, members, manifest_sha256, reason)
