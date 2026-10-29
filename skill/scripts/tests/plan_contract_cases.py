"""Structural defects of a PLAN.json, each built from a valid plan of its schema version (REQ-030 item 7).

Shared by `test_plan_contract_models`: every case must be refused by the Pydantic plan contract, and its verdict from
the stdlib readers (planner, runtime loader) is pinned so a reader that starts or stops seeing a defect is noticed.
The bases are the planner's own checked-in fixtures (one per schema version), minus their deliberate extension keys.
"""
from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
PLANNER_TESTS = SCRIPTS / ("bt_" + "planner") / "tests"
BASE_FILES = {"1.0.0": "golden/input-1.0.0.json", "1.1.0": "golden/input-1.1.0.json",
              "1.2.0": "golden/input-1.2.0.json", "1.3.0": "fixtures/P-177-schema-1.3.0.json"}


def base(version: str) -> dict:
    """The planner fixture of `version` without the extension keys it carries to pin canonical serialisation
    (`extension`, `legacy_extension`, extra `scope_exception` fields, null `subplan_id`)."""
    plan = json.loads((PLANNER_TESTS / BASE_FILES[version]).read_text(encoding="utf-8"))
    plan.pop("extension", None)
    for task in plan["tasks"]:
        task.pop("legacy_extension", None)
        if isinstance(task.get("scope_exception"), dict):
            task["scope_exception"] = {"reason": task["scope_exception"]["reason"]}
        if "subplan_id" in task and task["subplan_id"] is None:
            del task["subplan_id"]
    if len(plan["tasks"]) == 1:              # the 1.0.0/1.1.0 fixtures hold one task: add a dependent one
        follow = copy.deepcopy(plan["tasks"][0])
        follow.update(id="T2", after=["T1"], title=follow["title"] + " (follow-up)")
        plan["tasks"].append(follow)
    return plan


def _task(plan: dict, task_id: str) -> dict:
    return next(task for task in plan["tasks"] if task["id"] == task_id)


def _subplan(plan: dict, subplan_id: str) -> dict:
    return next(item for item in plan["subplans"] if item["id"] == subplan_id)


@dataclass(frozen=True)
class Case:
    name: str
    family: str             # the acceptance item it reproduces
    version: str
    mutate: Callable[[dict], None]
    expect: str             # a fragment of the contract's issue that names the defect
    planner: bool           # the planner refuses it too
    runtime: bool           # the runtime loader (both runtimes read plans through it) refuses it too

    def plan(self) -> dict:
        plan = copy.deepcopy(base(self.version))
        self.mutate(plan)
        return plan


def _rename(obj: dict, old: str, new: str) -> None:
    obj[new] = obj.pop(old)


def _set(path: Callable[[dict], dict], key: str, value) -> Callable[[dict], None]:
    return lambda plan: path(plan).__setitem__(key, value)


def _first(plan: dict) -> dict:
    return plan["tasks"][0]


def _second(plan: dict) -> dict:
    return plan["tasks"][1]


CASES: tuple[Case, ...] = (
    # `req` versus `req_id`: a renamed key is refused, never ignored
    Case("plan carries req_id instead of plan_id", "req/req_id", "1.3.0",
         lambda p: _rename(p, "plan_id", "req_id"), "req_id: unknown field", True, True),
    Case("task carries req instead of covers", "req/req_id", "1.2.0",
         lambda p: _rename(_first(p), "covers", "req"), "tasks[0].req: unknown field", True, False),
    Case("test task carries subplan instead of subplan_id", "req/req_id", "1.3.0",
         lambda p: _rename(_task(p, "T8"), "subplan_id", "subplan"), "subplan: unknown field", True, False),
    Case("consumed contract names subplan instead of from", "req/req_id", "1.3.0",
         lambda p: _rename(_subplan(p, "SP-2")["consumes"][0], "from", "subplan"), "from: required field missing",
         True, True),
    Case("a 1.2.0 plan carries 1.3.0 subplans (a 1.2 reader would drop them)", "req/req_id", "1.2.0",
         lambda p: p.__setitem__("subplans", copy.deepcopy(base("1.3.0")["subplans"])), "subplans: unknown field",
         False, False),
    # arrays versus objects
    Case("classification_evidence is an array", "array/object", "1.2.0",
         lambda p: _first(p).__setitem__("classification_evidence", list(_first(p)["classification_evidence"].values())),
         "classification_evidence: Input should be", True, False),
    Case("verification is an object, not an array", "array/object", "1.0.0",
         lambda p: _first(p).__setitem__("verification", _first(p)["verification"][0]), "verification: Input should be",
         True, True),
    Case("milestones keyed by id (object instead of array)", "array/object", "1.2.0",
         lambda p: p.__setitem__("milestones", {m["id"]: m for m in p["milestones"]}), "milestones: Input should be",
         True, False),
    Case("stage is an array, not an object", "array/object", "1.3.0",
         lambda p: p.__setitem__("stage", [s["id"] for s in p["subplans"]]), "stage: Input should be", True, False),
    Case("after is a string, not an array", "array/object", "1.0.0",
         _set(_second, "after", "T1"), "tasks[1].after: Input should be a valid list", True, True),
    Case("gate subplans is an object", "array/object", "1.3.0",
         lambda p: p["composition_gates"][0].__setitem__("subplans", {"SP-1": 1}), "subplans: Input should be", True,
         True),
    # required fields omitted
    Case("task without estimated_minutes", "missing field", "1.2.0",
         lambda p: _first(p).pop("estimated_minutes"), "tasks[0].estimated_minutes: required field missing", True,
         False),
    Case("subplan without audit_task", "missing field", "1.3.0",
         lambda p: _subplan(p, "SP-1").pop("audit_task"), "subplans[0].audit_task: required field missing", True,
         True),
    Case("manual check without expected", "missing field", "1.0.0",
         _set(_first, "verification", [{"type": "manual", "value": "open the page", "purpose": "it renders"}]),
         "manual check must state the expected result", True, False),
    Case("1.2.0 task without kind", "missing field", "1.2.0",
         lambda p: _first(p).pop("kind"), "tasks[0].kind: required field missing", True, True),
    Case("plan without tasks", "missing field", "1.1.0",
         lambda p: p.pop("tasks"), "tasks: required field missing", True, True),
    # unknown states, kinds and types
    Case("unknown task kind", "unknown value", "1.3.0",
         _set(_first, "kind", "deploy"), "tasks[0].kind: Input should be", True, True),
    Case("design kind in a 1.2.0 plan", "unknown value", "1.2.0",
         _set(_first, "kind", "design"), "tasks[0].kind: Input should be", True, True),
    Case("kind is an array", "unknown value", "1.3.0",
         _set(_first, "kind", ["implement"]), "tasks[0].kind: Input should be", True, True),
    Case("unknown verification type", "unknown value", "1.0.0",
         lambda p: _first(p)["verification"][0].__setitem__("type", "script"), "verification[0].type: Input should be",
         True, False),
    Case("unknown verification category", "unknown value", "1.2.0",
         lambda p: _first(p)["verification"][0].__setitem__("category", "quality"),
         "verification[0].category: Input should be", True, True),
    Case("unknown complexity", "unknown value", "1.2.0",
         _set(_first, "complexity", "trivial"), "tasks[0].complexity: Input should be", True, False),
    Case("task carries an execution state", "unknown value", "1.3.0",
         _set(_first, "status", "done"), "tasks[0].status: unknown field", True, False),
    Case("unknown verification environment", "unknown value", "1.3.0",
         lambda p: _first(p)["verification"][0].__setitem__("environment", "staging"),
         "verification[0].environment: Input should be", True, False),
    Case("stage version is true, not 1", "unknown value", "1.3.0",
         lambda p: p.__setitem__("stage", {"version": True, "subplans": [s["id"] for s in p["subplans"]]}),
         "stage.version: Input should be a valid integer", True, False),
    Case("unknown schema version", "unknown value", "1.3.0",
         lambda p: p.__setitem__("schema_version", "1.4.0"), "schema_version: must be one of", False, False),
    # inconsistent identifiers
    Case("dependency on an unknown task", "identifiers", "1.0.0",
         _set(_second, "after", ["T99"]), "'T99' is not a task of this plan", True, True),
    Case("gate member is not a declared subplan", "identifiers", "1.3.0",
         lambda p: p["composition_gates"][0]["subplans"].append("SP-9"), "CG-1.subplans: SP-9 is not a subplan", True,
         True),
    Case("duplicate task id", "identifiers", "1.0.0",
         lambda p: _second(p).__setitem__("id", _first(p)["id"]), "duplicate task id", True, True),
    Case("duplicate subplan id", "identifiers", "1.3.0",
         lambda p: p["subplans"][1].__setitem__("id", "SP-1"), "duplicate subplan id SP-1", True, True),
    Case("task subplan_id names no subplan", "identifiers", "1.3.0",
         _set(_first, "subplan_id", "SP-7"), "subplan_id: 'SP-7' is not a subplan", True, True),
    Case("consumed contract is not produced by the subplan it names", "identifiers", "1.3.0",
         lambda p: _subplan(p, "SP-2")["consumes"][0].__setitem__("version", 2),
         "SP-1 does not produce feature-one-api@2", True, False),
    Case("created_by names no task", "identifiers", "1.0.0",
         lambda p: _first(p)["verification"][0].__setitem__("created_by", "T99"), "created_by: 'T99' is not a task",
         True, False),
    Case("covers an undeclared requirement", "identifiers", "1.2.0",
         _set(_first, "covers", ["R9"]), "R9 is not declared in requirements", True, False),
    Case("milestone_id names no milestone", "identifiers", "1.0.0",
         _set(_first, "milestone_id", "M9"), "'M9' is not a milestone", True, False),
    Case("stage lists an undeclared subplan", "identifiers", "1.3.0",
         lambda p: p.__setitem__("stage", {"version": 1, "subplans": [s["id"] for s in p["subplans"]] + ["SP-4"]}),
         "stage.subplans", True, False),
    Case("interface producer names no task", "identifiers", "1.3.0",
         lambda p: p["interfaces"][0].__setitem__("producer_task", "T99"), "IF-1.producer_task: 'T99'", True, False),
    Case("dependency cycle", "identifiers", "1.0.0",
         lambda p: _first(p).__setitem__("after", [p["tasks"][-1]["id"]]), "dependency cycle", True, True),
)
