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
        parts.append(f"\n## How the work will be checked (by someone else)\n{bullets(brief.verification)}\n\n"
                     "The checks run from a clean copy of your final worktree: tracked and untracked files, nothing git-ignored, "
                     "no network, no running server. A script or test that these commands name and the repository does not "
                     "have yet is yours to create, and every command must pass on your final files. Installed dependencies "
                     "(`node_modules`) are mounted read-only: a check or test that runs `npm install`/`npm ci` or writes "
                     "inside `node_modules` fails there, so a test must use what is installed and write build output "
                     "elsewhere. Run each one yourself before you finish and say which you could not run.")
    if brief.expected_paths:
        parts.append(f"\n## Expected paths (guidance, not a limit)\n{bullets(brief.expected_paths)}")
    if brief.notes:
        parts.append(f"\n## Notes\n{brief.notes}")
    if handoff_mode == "snapshot":
        commit_rule = "You may commit there."
    else:
        commit_rule = "Do not create commits; the executor preserves the working tree as a patch artifact."
    if brief.publishes:
        parts.append("""
## Publication (approved by the owner with this plan)
This is the plan's publication step: its approved check requires your HEAD to be on `origin/main`. Fetch `origin`,
rebase your branch onto `origin/main` (resolve conflicts keeping both sides' intent), run the checks above, commit,
then publish once with `git push origin HEAD:main`, fast-forward only. If the push is rejected because `main` moved,
fetch and rebase once more and retry once. Never use `--force` or `--force-with-lease`, never push any other branch or
tag, and never change remotes. Report the pushed commit in your summary.""")
        scope_rule = ("- Do not merge other branches, force anything, or touch other worktrees. The only remote action allowed is "
                      "the publication above.")
    else:
        scope_rule = "- Do not push, merge, rebase onto other branches, force anything, or touch other worktrees or remotes."
    parts.append(f"""
## Rules
- Work only inside `{workdir}`: it is your own git worktree on branch `{branch}`. {commit_rule}
{scope_rule}
- Do not read, print or write secrets or credentials.
- Do not declare the task verified: an independent check decides. Say plainly what you did and what is left.
- Optionally write `{report_path}` as JSON {{"status": "done|partial|blocked", "summary": "<=3 sentences"}}. It is a claim, not a verdict.
""")
    return "\n".join(parts)
