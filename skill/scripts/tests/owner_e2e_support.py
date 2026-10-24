"""Small, isolated helpers for owner-level scheduler regression tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


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
    git(path, "add", "README.md")
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
    raw = json.dumps(plan, indent=2, sort_keys=True) + "\n"
    folder = rdir / "plan-revisions"
    folder.mkdir(parents=True, exist_ok=True)
    revision = plan["revision"]
    (folder / f"PLAN.r{revision}.json").write_text(raw, encoding="utf-8")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    manifest = {"schema": 1, "revisions": [{
        "revision": revision, "sha256": digest, "frozen_at": "2026-10-24T00:00:00+00:00",
    }]}
    (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return digest


def plan_task(task_id: str, title: str, *, subplan: str | None, kind: str = "test",
              after: tuple[str, ...] = (), ui: bool = False) -> dict:
    task = {
        "id": task_id, "milestone_id": "M1", "title": title, "objective": title,
        "repository": "app", "after": list(after), "expected_paths": [f"{task_id.lower()}/**"],
        "shared_resources": [], "acceptance_criteria": [f"{task_id} is accepted"], "kind": kind,
        "verification": [{"type": "command", "value": "true", "purpose": "owner e2e",
                           "category": "integration" if kind == "test" else "functional"}],
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
    for index, subplan_id in enumerate(("SP-1", "SP-2", "SP-3"), start=1):
        is_ui = index == 2
        design_id = f"T{index}D"
        build_id = f"T{index}B"
        test_id = f"T{index}T"
        visual_id = f"T{index}V"
        audit_id = f"T{index}A"
        if is_ui:
            if include_designer_contract:
                tasks.append(plan_task(design_id, "Author UI contract", subplan=subplan_id, kind="design"))
            tasks.append(plan_task(build_id, "Implement UI", subplan=subplan_id, kind="implement",
                                   after=(design_id,) if include_designer_contract else (), ui=True))
            tasks.append(plan_task(test_id, "Exercise UI integration", subplan=subplan_id, after=(build_id,)))
            tasks.append(plan_task(visual_id, "Review UI visually", subplan=subplan_id, kind="audit", after=(test_id,)))
            tasks.append(plan_task(audit_id, "Audit UI subplan", subplan=subplan_id, kind="audit", after=(visual_id,)))
            ui = {"contract": "interface", "version": 1, "design_task": design_id,
                  "visual_review_task": visual_id}
            produces = [{"contract": "interface", "version": 1, "defined_by": design_id}]
        else:
            tasks.extend((plan_task(build_id, "Implement subplan", subplan=subplan_id, kind="implement"),
                          plan_task(test_id, "Exercise subplan integration", subplan=subplan_id, after=(build_id,)),
                          plan_task(audit_id, "Audit subplan", subplan=subplan_id, kind="audit", after=(test_id,))))
            ui, produces = None, [{"contract": f"contract-{index}", "version": 1, "defined_by": build_id}]
        subplan = {
            "id": subplan_id, "milestone_id": "M1", "title": f"Subplan {index}",
            "covers": [f"R{index}"], "acceptance_criteria": [f"{build_id} is accepted"],
            "produces": produces, "consumes": [], "checkpoints": [{"task": test_id, "purpose": "integration"}],
            "integration_test_task": test_id, "audit_task": audit_id,
        }
        if ui is not None:
            subplan["ui"] = ui
        subplans.append(subplan)
    gate_task = plan_task("TC1", "Verify composed subplans", subplan=None, after=("T1A", "T2A", "T3A"))
    tasks.append(gate_task)
    tasks.append(plan_task("TA1", "Audit composition", subplan=None, kind="audit", after=("TC1",)))
    return {
        "schema_version": "1.3.0", "plan_id": "REQ-900", "revision": revision,
        "milestones": [{"id": "M1", "title": "Owner E2E"}],
        "requirements": [{"id": f"R{index}", "text": f"Requirement {index}"} for index in range(1, 4)],
        "tasks": tasks, "subplans": subplans,
        "composition_gates": [{"id": "CG-1", "subplans": ["SP-1", "SP-2", "SP-3"],
                                "task": "TC1", "audit_task": "TA1", "criteria": ["TC1 is accepted"]}],
    }
