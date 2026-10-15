"""Scaffolding for the whole-chain tests: a real requirement folder in an isolated bitácora, a PLAN.md pushed through the
real planner (`init` -> classify -> `check` -> `freeze`), then the real core, a real M2 decision ledger and the executor."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import bt_core
import bt_plan_adapter
import scheduler_executor_support as s

core = s.core
CLASS_KEYS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")


def plan_md(req: str, tasks: list[dict]) -> str:
    lines = [f"---\nreq: {req}\nstatus: approved\n---\n# Plan — {req} — chain\n", "## Tasks\n", "### M1 — Work"]
    for t in tasks:
        after = f" · after: {', '.join(t['after'])}" if t["after"] else ""
        lines.append(f"- [ ] {t['id']} — {t['title']} · repo: {t['repo']}{after} · verify: `python3 -c \"raise SystemExit(0)\"`")
    return "\n".join(lines) + "\n"


def classify(rdir: Path, tasks: list[dict], files: list[str]) -> None:
    """Fill the classification the planner never defaults. Every justification is the task's own text over real files."""
    path = rdir / "PLAN.json"
    plan = json.loads(path.read_text())
    plan["milestones"][0]["acceptance_criteria"] = ["every task of the chain is accepted"]
    by_id = {t["id"]: t for t in tasks}
    for i, task in enumerate(plan["tasks"]):
        spec = by_id[task["id"]]
        own = f"{task['id']}/**"
        ref = [f"file:{files[i % len(files)]}"]
        task.update(
            objective=f"{spec['title']} is delivered and its check passes", complexity=spec.get("complexity", "low"),
            scope="small_change", estimated_minutes=spec.get("minutes", 20), risk=spec.get("risk", "low"),
            coupling="low", confidence="high",
            estimate_rationale=f"{spec['title']} touches only its own folder and was read against {files[i % len(files)]}",
            expected_paths=[own], shared_resources=[], acceptance_criteria=[f"{task['id']} output exists and is correct"],
            verification=[{"type": "command", "value": "python3 -c \"raise SystemExit(0)\"", "purpose": f"smoke {task['id']}"}])
        words = {
            "complexity": f"{spec['title']} needs no design decision because its goal is one known change",
            "scope": f"{spec['title']} changes only the folder {task['id']} and nothing else in the repository",
            "duration": f"{spec['title']} is a short edit followed by one quick local check of {task['id']}",
            "risk": f"a mistake in {spec['title']} is local to {task['id']} and reversible by discarding its branch",
            "coupling": f"{spec['title']} owns the path {task['id']} so no other task of the plan edits it",
            "confidence": f"the files behind {spec['title']} were opened and the change is understood in full",
        }
        task["classification_evidence"] = {k: {"justification": words[k], "evidence": ref} for k in CLASS_KEYS}
    path.write_text(json.dumps(plan, indent=2))


class Pipeline:
    """Planner -> approved revision, inside an isolated bitácora layout (`<root>/<project>/requirements/REQ-NNN-x`)."""

    def __init__(self, world, project: str, req: str, tasks: list[dict], files: list[str]):
        self.world, self.project, self.req, self.tasks = world, project, req, tasks
        root = world.root
        (root / project / "requirements" / f"{req}-chain").mkdir(parents=True)
        (root / project / "project.json").write_text(json.dumps(
            {"work": False, "repos": {role: {"remote": "", "hint": str(path)} for role, path in world.repos.items()}}))
        self.rdir = root / project / "requirements" / f"{req}-chain"
        self.files = files

    def run(self) -> dict:
        (self.rdir / "SPEC.md").write_text("# spec\n")
        (self.rdir / "PLAN.md").write_text(plan_md(self.req, self.tasks))
        with patch.object(bt_core, "ROOT", self.world.root):
            self.step("init")
            classify(self.rdir, self.tasks, self.files)
            self.step("check")
            self.step("freeze")
            return bt_plan_adapter.run_state_fields(self.rdir)

    def step(self, action: str) -> None:
        out: list[str] = []
        code = bt_plan_adapter.run_cli(action, self.rdir, emit=out.append)
        if code != 0:
            raise AssertionError(f"plan-json {action} failed ({code}):\n" + "\n".join(out)[-3000:])


def real_candidate(**kw):
    """M2's test candidate, but with the account identity M2's methodology adapter would compute for that profile."""
    import dataclasses

    import bt_agents
    import bt_scheduler_decision as m2
    from bt_scheduler_decision.tests.support import candidate
    made = candidate(**kw)
    return dataclasses.replace(made, account_ref=m2.account_reference(bt_agents.account_key(made.profile, made.provider)))


class M2Port:
    """A test AssignmentPort built ONLY from M2's public API: each READY task becomes a DecisionRequest (task facts from the
    planner's classification carried by M1), the engine records a decision in a real decision ledger, and the executor
    reference of the selected route is what M1 hands to M3. (M2's own AssignmentPort wiring is M2's task.)"""

    def __init__(self, ledger_path: Path, route_table):
        import bt_scheduler_decision as m2
        self.m2 = m2
        self.ledger = m2.DecisionLedger(ledger_path)
        self.engine = m2.DecisionEngine(self.ledger)
        self.route_table = route_table          # callable(task_id) -> list of (provider, model, profile, effort), best first
        self.decisions: dict[str, object] = {}  # task_id -> last DecisionRecord

    def propose(self, request):
        import bt_scheduler_decision_adapter as adapter2
        candidate = real_candidate
        out = []
        for view in request.ready[:max(0, request.free_slots)]:
            facts, _, _ = adapter2.task_facts(view.id, view.meta, view.dependencies, view.acceptance_criteria,
                                              view.verification, view.shared_resources, view.expected_paths)
            candidates = tuple(candidate(provider=p, model=m, profile=prof, effort=e or None, rank=rank,
                                         observed_at=request.now - 1, valid_until=request.now + 3600)
                               for rank, (p, m, prof, e) in enumerate(self.route_table(view.id)))
            record = self.engine.decide(self.m2.DecisionRequest(
                request.plan_id, request.revision, request.plan_sha256, request.free_slots, request.now, facts,
                candidates, "m2-chain-test", None))
            self.decisions[view.id] = record
            if record.selected is not None:
                out.append(core.Assignment(view.id, "route:" + self.m2.executor_reference(record.decision_id,
                                                                                          record.selected.route_id), "m2"))
        return out


ROUTES = (("claude", "sonnet", "claude-personal", "low"), ("codex", "gpt-6-luna", "codex-1", "low"),
          ("antigravity", "gemini-3.8-flash-low", "agy-1", ""), ("claude", "haiku", "claude-personal", ""))


def rotating(offset: int = 0):
    """Route tables whose best choice rotates over the three providers, so every provider is used."""
    def table(task_id: str):
        n = int("".join(c for c in task_id if c.isdigit()) or 0) + offset
        order = [ROUTES[(n + i) % 3] for i in range(3)] + [ROUTES[3]]
        return order
    return table


def started_ref(world, tid: str):
    """The (provider, model) the fake provider binary was actually invoked with for a task, from its own record."""
    for rec in world.records():
        if f"/{tid}-" in rec["cwd"] or Path(rec["cwd"]).name.startswith(tid.lower()):
            return rec
    return None
