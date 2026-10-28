"""Optional prompt reductions; unique evidence is never cut to meet a size budget."""
from __future__ import annotations

import re
from itertools import groupby

import bt_config
from bitacora_platform import failure_lines


def concise() -> bool:
    return bt_config.get("prompts.concise", True) is True


def compact(text: str, line_limit: int = 80) -> str:
    """Cap redundant lines, keeping their exact text and count. Unique lines may exceed the budget."""
    if not concise() or len(text.splitlines()) <= line_limit:
        return text
    out = []
    for line, group in groupby(text.splitlines()):
        count = sum(1 for _ in group)
        marker = f"[identical line ×{count}]"
        if count > 1 and len(line) + len(marker) + 1 < count * (len(line) + 1):
            out.extend((line, marker))
        else:
            out.extend([line] * count)
    return "\n".join(out)


def instruction(original: str, shorter: str) -> str:
    return shorter if concise() else original


_SIGNAL = re.compile(r"FAIL|ERROR|Error|error|Expected|Assertion|!==|not ok|✖|✗|Cannot|cannot|Traceback|Exception")


def repair_excerpt(text: str, limit: int = 700) -> str:
    """What failed, for the objective of a repair task: the commands that RAN and failed (a numeric exit code; a check that never ran
    says `None` and is not this task's to fix) with the few lines that say why. A real note carries pages of server logs; the planner
    refuses an objective that repeats the same words, and an agent does not need the logs to know what to fix."""
    if concise():
        return _concise_excerpt(str(text or ""))
    blocks = re.split(r"(?m)^(?=\$ )", str(text or ""))
    out: list[str] = []
    for block in blocks:
        head, _, body = block.partition("\n")
        code = re.match(r"exit code (-?\d+)\b", body.lstrip())
        if not head.startswith("$ ") or not code or code.group(1) == "0":
            continue
        # six lines: the decisive ones first (a Playwright timeout has none of _SIGNAL's words), shown in their order
        picked: dict[str, tuple[bool, int]] = {}
        for n, line in enumerate(body.splitlines()[1:]):
            decisive = failure_lines.is_decisive(line)
            if (decisive or _SIGNAL.search(line)) and not failure_lines.noise(line) and not line.lstrip().startswith("{"):
                picked.setdefault(line.strip()[:160], (not decisive, n))
        lines = sorted(sorted(picked, key=picked.__getitem__)[:6], key=lambda line: picked[line][1])
        out.append(head[:200] + f"\nexit code {code.group(1)}" + "".join("\n" + line for line in lines))
    return "\n".join(out)[:limit] or str(text or "")[:min(limit, 400)]


def _concise_excerpt(text: str) -> str:
    out = []
    for block in re.split(r"(?m)^(?=\$ )", text):
        head, _, body = block.partition("\n")
        code = re.match(r"exit code (-?\d+)\b", body.lstrip())
        if not head.startswith("$ ") or not code or code.group(1) == "0":
            continue
        output_lines = list(dict.fromkeys(body.splitlines()[1:]))
        out.append("\n".join([head, f"exit code {code.group(1)}", *output_lines]))
    return "\n".join(dict.fromkeys(out)) or text
