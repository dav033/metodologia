"""Shared helpers for the module tests: what a planner adds on top of the derived skeleton."""
from __future__ import annotations

import json


def classify(skeleton: dict) -> dict:
    """What a planner adds on top of the skeleton: the whole classification (the tooling never guesses it)."""
    plan = json.loads(json.dumps(skeleton))
    for m in plan["milestones"]:
        m["title"] = m["title"] or m["id"]
        m["acceptance_criteria"] = [f"{m['id']} delivered"]
    for t in plan["tasks"]:
        t.update({"objective": f"Do {t['title']}", "repository": t.get("repository", "backend"), "complexity": "low",
                  "scope": "small_change", "estimated_minutes": 30, "risk": "medium", "coupling": "low",
                  "confidence": "medium", "estimate_rationale": "Known pattern in the existing module",
                  "expected_paths": t.get("expected_paths", ["src/**"]), "shared_resources": [],
                  "acceptance_criteria": [f"{t['title']} works"]})
        if not t.get("verification"):
            t["verification"] = [{"type": "manual", "value": "read the diff", "purpose": "review",
                                  "expected": "change matches the objective"}]
    return plan
