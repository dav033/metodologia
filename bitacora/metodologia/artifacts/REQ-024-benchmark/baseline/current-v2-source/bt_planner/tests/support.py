"""Shared helpers for the module tests: what a planner adds on top of the derived skeleton."""
from __future__ import annotations

import json

DIMENSIONS = ("complexity", "scope", "duration", "risk", "coupling", "confidence")


def evidence_for(task_id: str, text: str = "") -> dict:
    """A well-formed evidence block: each dimension argued in its own words and backed by a spec reference."""
    why = {"complexity": "the change follows a pattern already present in the module so little reasoning is needed",
           "scope": "one small localized change confined to a single component of the repository",
           "duration": "comparable to similar edits in this module including running its local tests",
           "risk": "a mistake is local reversible and caught by the task verification command",
           "coupling": "no other task edits the same files or depends on a shared contract",
           "confidence": "the affected code was read and a precedent for this exact change exists"}
    return {d: {"justification": f"{task_id}: {sentence}{(' ' + text) if text else ''}",
                "evidence": ["spec:SPEC.md", "precedent:REQ-001"]} for d, sentence in why.items()}


def classify(skeleton: dict) -> dict:
    """What a planner adds on top of the skeleton: the whole classification (the tooling never guesses it)."""
    plan = json.loads(json.dumps(skeleton))
    for m in plan["milestones"]:
        m["title"] = m["title"] or m["id"]
        m["acceptance_criteria"] = [f"{m['id']} delivered and verified"]
    for t in plan["tasks"]:
        t.update({"objective": f"Deliver the behaviour described by {t['title']} and keep tests passing",
                  "repository": t.get("repository", "backend"), "complexity": "low",
                  "scope": "small_change", "estimated_minutes": 30, "risk": "medium", "coupling": "low",
                  "confidence": "medium", "estimate_rationale": "Known pattern in the existing module",
                  "classification_evidence": evidence_for(t["id"]),
                  "expected_paths": t.get("expected_paths", [f"src/{t['id'].lower()}/**"]), "shared_resources": [],
                  "acceptance_criteria": [f"{t['title']} works as described"]})
        if not t.get("verification"):
            t["verification"] = [{"type": "manual", "value": "read the diff", "purpose": "review",
                                  "expected": "change matches the objective"}]
    return plan


# ---- a plan directory on disk, for the tests that go through sync.* -------------------------------------------
import tempfile  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402

PLAN_MD = """---
req: REQ-042
status: {status}
---
# Plan — demo

### M1 — Base
- [ ] T1 — Fix validation · repo: backend · files: src/auth/**, tests/auth/** · verify: `pytest tests/auth -q`
- [ ] T2 — Add tests · after: T1 · repo: backend · files: tests/new/**

### M2 — Next
- [ ] T3 — Wire it · after: T1, T2 · repo: backend · verify: `pytest -q`
"""


class PlanDir(unittest.TestCase):
    """REQ-042-demo/ with SPEC.md and an approved PLAN.md; `good()` writes a fully classified PLAN.json."""

    def setUp(self):
        from bt_planner import sync
        self.sync = sync
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.rdir = self.root / "REQ-042-demo"
        self.rdir.mkdir()
        (self.rdir / "SPEC.md").write_text("# spec\n## security\n## contract\n", encoding="utf-8")
        self.md("approved")

    def md(self, status: str = "approved", text: str | None = None) -> None:
        body = PLAN_MD.format(status=status) if text is None else text
        (self.rdir / "PLAN.md").write_text(body, encoding="utf-8")

    def write(self, plan: dict) -> None:
        from bt_planner import contract as pc
        (self.rdir / "PLAN.json").write_text(pc.dumps(plan), encoding="utf-8")

    def good(self) -> dict:
        plan = classify(self.sync.skeleton(self.rdir))
        self.write(plan)
        return plan

    def errors(self, **kw) -> str:
        return "\n".join(self.sync.check(self.rdir, **kw).errors)
