"""The agent prompt: the frozen plan's task plus the rules of the isolated worktree. Task text only, never secrets."""
from __future__ import annotations

from .model import Brief, StartRequest


def build_prompt(brief: Brief, request: StartRequest, *, workdir: str, branch: str, report_path: str,
                 handoff_mode: str = "snapshot") -> str:
    def bullets(items) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "- (none stated)"

    parts = [
        "You are executing ONE task of an approved plan, headless, in your own isolated git worktree.",
        f"\n## Task {request.task_id}: {brief.title}",
    ]
    if brief.objective:
        parts.append(f"\n## Objective\n{brief.objective}")
    parts.append(f"\n## Acceptance criteria\n{bullets(brief.acceptance_criteria or request.acceptance_criteria)}")
    if brief.verification:
        parts.append(f"\n## How the work will be checked (by someone else)\n{bullets(brief.verification)}")
    if brief.expected_paths:
        parts.append(f"\n## Expected paths (guidance, not a limit)\n{bullets(brief.expected_paths)}")
    if brief.notes:
        parts.append(f"\n## Notes\n{brief.notes}")
    if handoff_mode == "snapshot":
        commit_rule = "You may commit there."
    else:
        commit_rule = "Do not create commits; the executor preserves the working tree as a patch artifact."
    parts.append(f"""
## Rules
- Work only inside `{workdir}`: it is your own git worktree on branch `{branch}`. {commit_rule}
- Do not push, merge, rebase onto other branches, force anything, or touch other worktrees or remotes.
- Do not read, print or write secrets or credentials.
- Do not declare the task verified: an independent check decides. Say plainly what you did and what is left.
- Optionally write `{report_path}` as JSON {{"status": "done|partial|blocked", "summary": "<=3 sentences"}}. It is a claim, not a verdict.
""")
    return "\n".join(parts)
