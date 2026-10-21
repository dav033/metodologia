"""Project guards: checks that keep a repository's architecture rules from being broken by any task.

A rule such as «only the recovery adapter imports the M5 package» lives in a test of its own, outside the tests a task
writes for itself. Tasks verify only their own tests, so the violation is found by the final regression task (which only
runs checks and cannot repair), after the task that broke it was accepted (REQ-029: five boundary failures at T7). The
project lists those checks in `project.json` under `guards`:

    "guards": [{"repo": "skill", "command": "cd skill/scripts && python3 -m unittest tests.test_plan_boundary",
                "why": "module boundaries"},
               {"repo": "skill", "paths": ["skill/scripts/bt_scheduler_quality*"], "command": "...",
                "why": "the module's own tests"}]

and every `implement` task of that repository carries them among its verification, so the task that breaks a rule is
the one told, with the failing output, to repair it. A guard with `paths` (globs) applies only to a task that declares
a matching path in `expected_paths`: «a task that changes a module runs that module's tests» (REQ-029 T4 changed the
M6 adapter and broke four of its tests, found by the final regression). The plan check warns about a task without them.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path


def load(project_dir: Path) -> list[dict]:
    """The valid guards of a project (`repo`, `command`, optional `why`); [] when none or the file is unreadable."""
    try:
        data = json.loads((Path(project_dir) / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    items = data.get("guards") if isinstance(data, dict) else None
    return [item for item in items or [] if isinstance(item, dict) and isinstance(item.get("repo"), str)
            and isinstance(item.get("command"), str) and item["command"].strip()]


def warnings(plan: dict, guards: list[dict]) -> list[str]:
    """One warning per `implement` task that lacks a guard of its repository among its command verifications."""
    out = []
    for task in plan.get("tasks") or []:
        if not isinstance(task, dict) or task.get("kind", "implement") != "implement":
            continue
        have = {v.get("value", "").strip() for v in task.get("verification") or [] if isinstance(v, dict)}
        declared = [x for x in task.get("expected_paths") or [] if isinstance(x, str)]
        for guard in guards:
            globs = guard.get("paths")
            if isinstance(globs, list) and globs and not any(fnmatch.fnmatch(x, g) for x in declared for g in globs
                                                              if isinstance(g, str)):
                continue                        # a guard for one module does not apply to a task that leaves it alone
            if guard["repo"] == task.get("repository") and guard["command"].strip() not in have:
                why = f" ({guard['why']})" if guard.get("why") else ""
                out.append(f"{task.get('id')}.verification: missing the project guard `{guard['command'][:100]}`{why}; "
                           "without it a rule this task breaks is found only by the final regression, which cannot repair it")
    return out
