"""Small, isolated helpers for owner-level scheduler regression tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import bt_plan_adapter as plan_adapter


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=Owner E2E", "-c", "user.email=owner-e2e@example.invalid", *args],
        cwd=cwd, capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise AssertionError(f"git {args!r} failed: {result.stderr}")
    return result.stdout.strip()


def make_repository(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-q", "-b", "main")
    (path / "README.md").write_text("owner e2e base\n", encoding="utf-8")
    (path / "src").mkdir()
    (path / "docs").mkdir()
    for number in range(1, 17):
        (path / "src" / f"T{number}_check.py").write_text(
            "from pathlib import Path\nassert Path('README.md').read_text(encoding='utf-8').startswith('owner e2e')\n",
            encoding="utf-8")
        (path / "docs" / f"T{number}.findings.json").write_text(
            '{"schema":"audit-findings/1","findings":[]}\n', encoding="utf-8")
    git(path, "add", "README.md", "src", "docs")
    git(path, "commit", "-q", "-m", "owner e2e base")
    return path


def add_designer_contract(repository: Path) -> Path:
    """Add the UI contract to the committed base tree used by the composition fixture."""
    contract = repository / "design" / "contracts" / "interface@v1.md"
    contract.parent.mkdir(parents=True)
    contract.write_text("# Interface contract v1\n\nBase-tree fixture for the owner E2E.\n", encoding="utf-8")
    git(repository, "add", str(contract.relative_to(repository)))
    git(repository, "commit", "-q", "-m", "Add Designer contract to base tree")
    return contract


def freeze_plan(rdir: Path, plan: dict) -> str:
    """Persist a frozen plan using the same file and digest manifest as the owner adapter."""
    report = plan_adapter.planner.validate(plan, strict_publication=True)
    if report.errors:
        raise AssertionError("invalid frozen fixture: " + "; ".join(report.errors))
    raw = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    folder = rdir / "plan-revisions"
    folder.mkdir(parents=True, exist_ok=True)
    revision = plan["revision"]
    (rdir / "PLAN.json").write_text(raw, encoding="utf-8")
    (folder / f"PLAN.r{revision}.json").write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    try:
        manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
    except FileNotFoundError:
        manifest = {"schema": 1, "revisions": []}
    manifest["revisions"] = [item for item in manifest["revisions"] if item["revision"] != revision]
    manifest["revisions"].append({
        "revision": revision, "sha256": digest, "frozen_at": "2026-10-24T00:00:00+00:00",
    })
    (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return digest


def plan_task(task_id: str, title: str, *, subplan: str | None, kind: str = "test",
              after: tuple[str, ...] = (), ui: bool = False) -> dict:
    path = (f"docs/{task_id}.findings.json" if kind == "audit" else
            "design/contracts/interface@v1.md" if kind == "design" else f"src/{task_id.lower()}.txt")
    criterion = f"{task_id} produces the required outcome"
    verification = [{"type": "command", "value": f"python3 src/{task_id}_check.py",
                     "purpose": criterion,
                     "category": "integration" if kind == "test" else "static" if kind == "audit" else "functional"}]
    task = {
        "id": task_id, "milestone_id": "M1", "title": title, "objective": f"{title} produces an accepted outcome",
        "repository": "app", "after": list(after), "expected_paths": [path],
        "shared_resources": [], "acceptance_criteria": [criterion], "kind": kind,
        "verification": verification, "covers": ["R1" if subplan == "SP-1" else "R2" if subplan == "SP-2" else "R3" if subplan == "SP-3" else "R4"],
        "complexity": "low", "scope": "isolated_fix", "estimated_minutes": 20,
        "risk": "low", "coupling": "low", "confidence": "high",
        "estimate_rationale": f"{title} is a bounded fixture task with one observable result",
        "classification_evidence": {
            "complexity": {"justification": f"{title} follows a defined fixture behavior with no design fork",
                           "evidence": ["file:README.md"]},
            "scope": {"justification": f"{title} changes only its declared fixture output path",
                      "evidence": ["file:README.md"]},
            "duration": {"justification": f"{title} needs one bounded action and a local check",
                         "evidence": [f"command:python3 src/{task_id}_check.py -> verifies the committed fixture input"]},
            "risk": {"justification": f"A mistake in {title} is isolated to a disposable test repository",
                     "evidence": ["file:README.md"]},
            "coupling": {"justification": f"{title} owns only its declared output and has no shared fixture path",
                         "evidence": ["file:README.md"]},
            "confidence": {"justification": f"{title} uses a committed fixture input and a deterministic check",
                           "evidence": ["file:README.md"]},
        },
    }
    if subplan is not None:
        task["subplan_id"] = subplan
    if ui:
        task["ui"] = True
    return task


def three_subplan_plan(*, revision: int = 1, include_designer_contract: bool = True) -> dict:
    """Return the shared three-member composition fixture, including one UI contract when requested."""
    tasks = []
    subplans = []
    task_number = 1
    for index, subplan_id in enumerate(("SP-1", "SP-2", "SP-3"), start=1):
        is_ui = index == 2
        if is_ui:
            design_id = f"T{task_number}"
            build_id, test_id, visual_id, audit_id = (f"T{task_number + offset}" for offset in range(1, 5))
            tasks.append(plan_task(design_id, "Author UI contract", subplan=subplan_id, kind="design"))
            tasks.append(plan_task(build_id, "Implement UI", subplan=subplan_id, kind="implement",
                                   after=(design_id,), ui=True))
            tasks.append(plan_task(test_id, "Exercise UI integration", subplan=subplan_id, after=(build_id,)))
            tasks.append(plan_task(visual_id, "Review UI visually", subplan=subplan_id, kind="audit", after=(test_id,)))
            tasks.append(plan_task(audit_id, "Audit UI subplan", subplan=subplan_id, kind="audit", after=(visual_id,)))
            task_number += 5
            ui = {"contract": "interface", "version": 1, "design_task": design_id,
                  "visual_review_task": visual_id}
            produces = [{"contract": "interface", "version": 1, "defined_by": design_id}]
        else:
            build_id, test_id, audit_id = (f"T{task_number + offset}" for offset in range(3))
            tasks.extend((plan_task(build_id, "Implement subplan", subplan=subplan_id, kind="implement"),
                          plan_task(test_id, "Exercise subplan integration", subplan=subplan_id, after=(build_id,)),
                          plan_task(audit_id, "Audit subplan", subplan=subplan_id, kind="audit", after=(test_id,))))
            task_number += 3
            ui, produces = None, [{"contract": f"contract-{index}", "version": 1, "defined_by": build_id}]
        subplan = {
            "id": subplan_id, "milestone_id": "M1", "title": f"Subplan {index}",
            "covers": [f"R{index}"], "outcome": f"Subplan {index} delivers its verified contract outcome",
            "acceptance_criteria": [f"{build_id} produces the required outcome"],
            "produces": produces, "consumes": [], "checkpoints": [{"task": test_id, "purpose": "integration"}],
            "integration_test_task": test_id, "audit_task": audit_id,
        }
        if ui is not None:
            subplan["ui"] = ui
        subplans.append(subplan)
    gate_task = plan_task(f"T{task_number}", "Verify composed subplans", subplan=None,
                          after=tuple(item["audit_task"] for item in subplans))
    gate_id = gate_task["id"]
    gate_criterion = "All owner scenarios preserve their durable invariants"
    gate_task["acceptance_criteria"] = [gate_criterion]
    gate_task["covers"] = ["R4"]
    tasks.append(gate_task)
    task_number += 1
    composition_audit = plan_task(f"T{task_number}", "Audit composition", subplan=None,
                                  kind="audit", after=(gate_id,))
    tasks.append(composition_audit)
    requirement_ids = [f"R{index}" for index in range(1, 4)] + ["R4"]
    plan = {
        "schema_version": "1.3.0", "plan_id": "REQ-900", "spec_ref": "SPEC.md", "revision": revision,
        "milestones": [{"id": "M1", "title": "Owner E2E", "acceptance_criteria": ["All owner scenarios preserve their durable invariants"]}],
        "requirements": requirement_ids,
        "tasks": tasks, "subplans": subplans,
        "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2", "SP-3"],
                                "task": gate_id, "audit_task": composition_audit["id"],
                                "criteria": [gate_criterion]}],
    }
    report = plan_adapter.planner.validate(plan, strict_publication=True)
    if report.errors:
        raise AssertionError("invalid 1.3.0 fixture: " + "; ".join(report.errors))
    return plan


def legacy_plan(*, revision: int = 1) -> dict:
    """Return one strict-publication 1.2.0 fixture task without 1.3-only fields."""
    plan = three_subplan_plan(revision=revision)
    task = next(item for item in plan["tasks"] if item["id"] == "T1")
    task.pop("subplan_id")
    task.pop("ui", None)
    plan.update(schema_version="1.2.0", requirements=["R1"], tasks=[task])
    plan.pop("subplans")
    plan.pop("composition_gates")
    report = plan_adapter.planner.validate(plan, strict_publication=True)
    if report.errors:
        raise AssertionError("invalid legacy fixture: " + "; ".join(report.errors))
    return plan
