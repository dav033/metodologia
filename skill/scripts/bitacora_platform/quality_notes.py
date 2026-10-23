"""Stable actionable explanations of M6 integration and check failures."""
from __future__ import annotations

import re

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

_NOISE_LINE = re.compile(r"^\s*npm (?:notice|warn(?:ing)?)\b", re.IGNORECASE)

_ERROR_LINE = re.compile(r"\b(?:error|TS\d{4}|Traceback|AssertionError|Cannot find|not defined|is not a function)\b|✖|\bFAIL", re.IGNORECASE)

def _without_noise(text: str) -> str:
    """The output without lines that never explain a failure (`npm notice ...`, `npm warn ...`) and blank runs."""
    kept = [line for line in text.splitlines() if not _NOISE_LINE.match(line)]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()

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
