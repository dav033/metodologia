"""Stable actionable explanations of M6 integration and check failures."""
from __future__ import annotations

import re

from . import failure_lines

UNRESOLVED = "merge conflict markers left in: "

REVERTED = "files changed back to an older version than the base they started from: "

def _unresolved_note(clash: str) -> str:
    return (f"Your result still contains unresolved merge conflict markers ({clash.removeprefix(UNRESOLVED)}). Your tree "
            "started as a merge in progress: open every file with `<<<<<<<` / `=======` / `>>>>>>>` lines, combine both "
            "sides' behaviour, delete the markers, and run the tests again.")

def _reverted_note(clash: str) -> str:
    return (f"Your result puts these files back to an OLDER version of themselves than the one your work started from "
            f"({clash.removeprefix(REVERTED)}). That undoes what an earlier task fixed, and every task built after you "
            "inherits the regression. Restore each of them to the version in your starting tree (`git checkout <start> -- "
            "<file>`; the start is the first parent of your worktree's HEAD) unless the task really owns the file, then run the "
            "tests of the module again.")

_NOISE_LINE = failure_lines._NOISE_LINE

# kept for the importers of the adapter's old names; the digest itself uses `failure_lines`
_ERROR_LINE = re.compile(r"\b(?:error|TS\d{4}|Traceback|AssertionError|Cannot find|not defined|is not a function)\b|✖|\bFAIL", re.IGNORECASE)

def _without_noise(text: str) -> str:
    """The output without lines that never explain a failure (`npm notice ...`, `npm warn ...`) and blank runs."""
    return failure_lines.without_noise(text, structured_logs=False)

_PACKAGE_ADVICE = ("A check cannot find the package {names}: that is a dependency problem, not a code problem. Install the locked "
                   "dependencies in your worktree with the package manager (for npm: `npm ci --offline`) and run the check "
                   "yourself; do not edit configuration to avoid the import.")
_SOURCE_ADVICE = ("A check loads {names}, but a source file the check imports does not exist in your final files: create it "
                  "(and commit/keep it in the worktree) or fix the import path; this is not a dependency problem, so do not "
                  "install or declare packages for it.")
_UNNAMED_ADVICE = ("A check cannot load a module. If it is a package, install the locked dependencies (for npm: `npm ci "
                   "--offline`); if it is a file of the repository, create it in your final files or fix the import path.")

def _missing_module_note(text: str, known=()) -> str:
    """The advice for a check that cannot load a module: a missing PACKAGE is a dependency problem, a missing SOURCE file
    (relative, absolute, `/workspace/...`, a declared path of the plan) is the work's own (REQ-021 T3.11 att-0093: the agent was
    told to reinstall dependencies for a script it never created). '' when no module is missing."""
    found = failure_lines.missing_modules(text, known)
    if not found and not failure_lines.mentions_missing_module(text):
        return ""
    def names(kind: str) -> str:
        return ", ".join([f"`{name}`" for name, k in found if k == kind][:3])
    parts = [advice.format(names=names(kind)) for kind, advice in (("source", _SOURCE_ADVICE), ("package", _PACKAGE_ADVICE))
             if names(kind)]
    return "\n\n".join(parts or [_UNNAMED_ADVICE]) + "\n\n"

def _resource_note(text: str) -> str:
    """The advice when the sandbox itself ran out of memory or processes (REQ-021 att-0088: Node's heap was exhausted during
    `next build`): an environment limit, never a reason to change product code. '' when the output does not show one."""
    kind, line = failure_lines.resource_limit(text)
    if kind == "memory":
        return (f"The verifier sandbox exhausted its memory while running a check (`{line[:160]}`). That is a limit of the "
                "verification environment, not a defect of your code: do not change product code for it. Only if the plan "
                "allows changing the check's script may you set an explicit `NODE_OPTIONS=--max-old-space-size=<MB>` in that "
                "script; otherwise say so at the top of your final report.\n\n")
    if kind == "processes":
        return (f"The verifier sandbox could not start another process or thread while running a check (`{line[:160]}`). That is "
                "a limit of the verification environment, not a defect of your code: do not change product code for it. Only "
                "if the plan allows changing the check's script may you lower its parallelism (fewer workers); otherwise say "
                "so at the top of your final report.\n\n")
    return ""

def _integration_note(clash: str) -> str:
    return ("Your result passed its checks but cannot be combined with work that was already accepted: "
            f"{clash}. Tasks that come after it, or were built on an earlier result of this one, would collide with it. "
            "Redo it as a small change on top of the result you started from: keep every file and function it already "
            "has, edit only what the task and the audit notes require, and do not rewrite or delete working code.")

def _give_way_note(task_id: str, clash: str) -> str:
    return (f"{task_id} was changed after this task was built (an audit finding needed it), and the two touch the same "
            f"code: {clash}. Your tree now contains the new {task_id}. Redo this task on top of it: keep what your earlier "
            "result did that is still right, adapt it to the new code instead of overwriting it, and do not delete working "
            "code.")
