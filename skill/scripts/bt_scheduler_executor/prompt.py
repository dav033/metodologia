"""The agent prompt: the frozen plan's task plus the rules of the isolated worktree. Task text only, never secrets."""
from __future__ import annotations

import re
import shutil
from functools import lru_cache

from .model import Brief, StartRequest


# A whole-repository suite (npm test / npm run gate, unittest discovery without a pattern, bare pytest, cargo test).
_WHOLE_SUITE = re.compile(r"(unittest\s+discover\b[^&|;]*$)|(\bnpm\s+(run\s+)?(test|gate)\s*$)|(\bpytest\s*$)|(\bcargo\s+test\s*$)")


def whole_suites(verification) -> list[str]:
    """The whole-suite commands among the brief's checks (entries read `purpose: command`)."""
    found = []
    for entry in verification or ():
        command = str(entry).split(": ", 1)[-1].strip()
        if _WHOLE_SUITE.search(command.rsplit("&&", 1)[-1].strip()) and command not in found:
            found.append(command)
    return found


@lru_cache(maxsize=1)
def _rtk_available() -> bool:
    try:
        return shutil.which("rtk") is not None
    except OSError:
        return False


def build_prompt(brief: Brief, request: StartRequest, *, workdir: str, branch: str, report_path: str,
                 handoff_mode: str = "snapshot", rtk: bool = True) -> str:
    def bullets(items) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "- (none stated)"

    parts = [
        "You are executing ONE task of an approved plan, headless, in your own isolated git worktree.",
        f"\n## Task {request.task_id}: {brief.title}",
    ]
    if brief.objective:
        parts.append(f"\n## Objective\n{brief.objective}")
    design = _design_context(brief)
    if brief.review_axis == "visual":
        parts.append("\n## Reviewer axis\nvisual")
    if design:
        parts.append("\n## Design contract\n" + "\n".join(f"- {line}" for line in _design_instructions(brief, design)))
    parts.append(f"\n## Acceptance criteria\n{bullets(brief.acceptance_criteria or request.acceptance_criteria)}")
    if brief.verification:
        parts.append(f"\n## How the work will be checked (by someone else)\n{bullets(brief.verification)}\n\n"
                     "The checks run from a clean copy of your final worktree: tracked and untracked files, nothing git-ignored "
                     "(so no `.env` and none of your shell's variables), with network access but no running server of yours. A script or test that these commands name and the repository does not "
                     "have yet is yours to create, and every command must pass on your final files. Installed dependencies "
                     "(`node_modules`) are mounted in a throwaway overlay: tools may write inside it (a vite/vitest config "
                     "bundle, caches) but nothing reaches your worktree, and `npm install`/`npm ci` there fails (no registry). "
                     "If the project has a lockfile, install it in your worktree first (for npm: "
                     "`npm ci --offline`) so you can run the checks. Run each one yourself before you finish and say "
                     "which you could not run.")
        suites = whole_suites(brief.verification)
        if suites:
            # REQ-020 T15.1: the agent ran `npm run gate` (~10 min) and then the verifier ran it again on the same files
            parts.append("\nThe verifier runs the whole-suite checks (" + ", ".join(f"`{c}`" for c in suites) + ") itself on your final files "
                         "and they take minutes: do NOT run them yourself; run the focused tests of what you changed, and say that the "
                         "whole suites were left to the verifier.")
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
    elif brief.remote_actions:
        parts.append("""
## Remote actions (approved by the owner with this plan)
This task's own objective asks you to create its repository on the host and/or push to it. You have the authenticated `gh` and
`git` of the owner for exactly that: inspect first (`gh repo view <owner>/<name>`), create the repository with the visibility the task
names only if it does not exist, set `origin` to it, and push what the task asks for (your commit, to the repository's default
branch when it is empty). Never use `--force` or `--force-with-lease`, never delete anything, never touch any other repository, and
report what you created and pushed in your summary.""")
        scope_rule = ("- Do not merge other branches, force anything, or touch other worktrees. The only remote actions allowed are the "
                      "ones above, on this task's own repository.")
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
    if rtk and _rtk_available():
        parts.append("""
## Noisy inspection output
For your own noisy inspection, prefer supported RTK commands: `rtk git status`, `rtk git log`, `rtk git diff`,
`rtk grep <pattern> <path>`, `rtk read <path>`, or `rtk test <command>` / `rtk next build` for exploratory diagnostics.
Keep inspections read-only; tests/builds may write local artifacts and need the task's authorization. Inspect `rtk <cmd> --help`.
Condensed output is a reading aid. Recover missing failure details from the emitted record with `rtk recall <hash> --full`
or its saved path; do not repeat side effects to recover output. Preserve exit codes. Read exact code before editing.
Run the task's own verification commands exactly as written, with RAW output: never wrap them in RTK or filter evidence.
Do not install/configure RTK or add a second prefix if a hook already wraps the command.
""")
    return "\n".join(parts)

def _design_context(brief: Brief) -> dict:
    """Contract facts from the owner's brief notes (`Design contract:` lines), else from optional brief attributes."""
    facts = {}
    for line in (brief.notes or "").splitlines():
        key, sep, value = line.partition(":")
        key = {"kind": "task kind"}.get(key.strip().lower(), key.strip().lower())
        if sep and key in ("design contract", "task kind", "ui task", "approval", "sha-256"):
            facts.setdefault(key, value.strip())
    path = facts.get("design contract") or getattr(brief, "contract_path", "") or ""
    if not path:
        return {}
    return {"path": path, "version": getattr(brief, "contract_version", None),
            "kind": (facts.get("task kind") or getattr(brief, "task_kind", "") or "").lower(),
            "ui": facts.get("ui task", "").lower() == "true" or bool(getattr(brief, "ui_task", False)),
            "approval": facts.get("approval", ""), "sha256": facts.get("sha-256", "")}


def _design_instructions(brief: Brief, design: dict) -> list[str]:
    contract = f"`{design['path']}`" + (f" (version {design['version']})" if design["version"] is not None else "")
    if design["kind"] == "design":
        return [f"Author the contract at {contract}; read any existing file there first.",
                "Write only within `design/` (keep contract changes within `design/`); use `design/preview` only when the preview "
                "is enabled in configuration.",
                "The Designer authors the contract and must never approve its own contract: the owner approves each version "
                "before UI work starts."]
    if brief.review_axis == "visual":
        return [f"Judge the rendered UI against {contract}.",
                "Request Runner screenshots for each breakpoint and each state the contract declares, and base the review on "
                "that evidence."]
    lines = [f"Read {contract} before making changes. Read it before implementing, follow it and report conformance."]
    if design["ui"]:
        lines.append(f"Owner approval: `{design['approval'] or 'unknown'}`, SHA-256 `{design['sha256'] or 'none'}`. "
                     "Proceed only with approval status `approved` and a file matching the approved SHA-256; otherwise stop and "
                     "report the task as blocked without changing UI code.")
    return lines
