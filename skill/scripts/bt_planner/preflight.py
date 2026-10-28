"""Plan pre-flight (REQ-030 M6): structural defects found before a plan is frozen or dispatched, not by an agent.

Each finding names a check a run would fail for reasons no attempt can fix, so it is caught before any quota is
spent. The checks are conservative: a file or script a task (or one of its predecessors) declares it will produce is
legitimate even though it does not exist yet — only what is neither present at the base nor declared is reported.

- PREFLIGHT_INPUT_MISSING   a check runs a repository script (`python3 x.py`, `npx tsx x.ts`, `node x.js`) that is
                            neither in the repository at the base nor an expected path of the task or a predecessor
                            (REQ-021 T3.11: the test file was never declared, so nothing guaranteed it would exist).
- PREFLIGHT_SCRIPT_MISSING  (warning unless strict) `npm run <s>` / `npm test` with no such script in package.json at
                            the base, and package.json not an expected path of the task or a predecessor. A warning
                            by default: on pictures REQ-021 r15 all 96 such checks run scripts that earlier tasks add
                            to package.json without declaring it — a plan smell, not a plan that cannot run.
- PREFLIGHT_ENV_MISSING     a check `requires` a variable no configured source provides
                            (REQ-021 T2.6 att-0068/0071: the database URL was missing; found by two agent attempts).
- PREFLIGHT_PATHS_UNORDERED (warning) two tasks with no ordering between them declare overlapping paths in the
                            same repository: they will be serialized at runtime, which the plan may not expect.

Stdlib only: the legacy approval gate runs it under the system interpreter.
"""
from __future__ import annotations

import fnmatch
import json
import posixpath
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field

from .command_checks import tokens

_RUNNERS = {"python", "python3", "node", "tsx", "bun", "deno", "ts-node", "bash", "sh"}
_SCRIPT = re.compile(r"\.(?:py|[cm]?[jt]sx?|sh)$")
EnvAvailable = Callable[[str], bool]
Exists = Callable[[str, str], bool | None]          # (repository role, path) -> present at the base? None = unknown
ReadFile = Callable[[str, str], bytes | None]       # (repository role, path) -> content at the base, None if absent


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _declared(path: str, patterns: Iterable[str]) -> bool:
    for pattern in patterns:
        pattern = str(pattern).strip().lstrip("./")
        if not pattern:
            continue
        if fnmatch.fnmatch(path, pattern) or path == pattern.rstrip("/") or \
                (pattern.endswith("/**") and path.startswith(pattern[:-3].rstrip("/") + "/")):
            return True
    return False


def _prefix(pattern: str) -> str:
    pattern = str(pattern).strip().lstrip("./")
    cut = min((pattern.find(ch) for ch in "*?[{" if ch in pattern), default=len(pattern))
    return pattern[:cut].rstrip("/")


def _overlap(a: str, b: str) -> bool:
    """Same rule as the runtime's path claims: one static prefix contains the other."""
    pa, pb = _prefix(a), _prefix(b)
    return not pa or not pb or pa == pb or pa.startswith(pb + "/") or pb.startswith(pa + "/")


def _ancestors(tasks: Mapping[str, dict], task_id: str) -> set[str]:
    seen: set[str] = set()
    stack = list(tasks.get(task_id, {}).get("after") or [])
    while stack:
        dep = stack.pop()
        if dep in seen or dep not in tasks:
            continue
        seen.add(dep)
        stack.extend(tasks[dep].get("after") or [])
    return seen


def _segments(command: str) -> list[tuple[str, list[str]]]:
    """(working directory, argv) per `&&`-joined segment; a leading `cd <dir> &&` sets the directory."""
    out: list[tuple[str, list[str]]] = []
    directory, current = "", []
    for word in [*tokens(command), "&&"]:
        if word in ("&&", "||", ";", "|"):
            if len(current) == 2 and current[0] == "cd":
                directory = posixpath.normpath(posixpath.join(directory, current[1]))
            elif current:
                out.append((directory, current))
            current = []
        else:
            current.append(word)
    return out


def _script_of(argv: list[str]) -> str | None:
    words = [w for w in argv if not re.fullmatch(r"[A-Z_][A-Z0-9_]*=.*", w)]       # leading VAR=value assignments
    if words and words[0] == "npx":
        words = words[1:]
        while words and words[0].startswith("-"):
            words = words[1:]
    if not words or posixpath.basename(words[0]) not in _RUNNERS and words[0] not in _RUNNERS:
        return None
    if "-c" in words or "-e" in words or "-m" in words:
        return None
    return next((w for w in words[1:] if not w.startswith("-") and _SCRIPT.search(w)), None)


def check(plan: Mapping, *, exists: Exists, read: ReadFile, env_available: EnvAvailable | None = None,
          strict: bool = False, base: str = "the base") -> Report:
    """Repository facts come from the caller (`exists`, `read`): the planner package touches no files or processes."""
    report = Report()
    tasks = {t["id"]: t for t in plan.get("tasks") or () if isinstance(t, dict) and isinstance(t.get("id"), str)}
    for task_id, task in tasks.items():
        role = str(task.get("repository") or "")
        declared = list(task.get("expected_paths") or [])
        for dep in _ancestors(tasks, task_id):
            if tasks[dep].get("repository") == task.get("repository"):
                declared += list(tasks[dep].get("expected_paths") or [])
        for index, verification in enumerate(task.get("verification") or ()):
            if not isinstance(verification, dict) or verification.get("type") != "command":
                continue
            where = f"{task_id}.verification[{index}]"
            for name in verification.get("requires") or ():
                if isinstance(name, str) and not name.startswith("service:") and env_available is not None \
                        and not env_available(name):
                    report.errors.append(f"PREFLIGHT_ENV_MISSING: {where} requires {name}, which no configured "
                                         "verifier environment or secret file provides")
            if exists(role, ".") is None:
                continue                                     # an unresolvable repository proves nothing
            for directory, argv in _segments(str(verification.get("value") or "")):
                script = _script_of(argv)
                if script:
                    path = posixpath.normpath(posixpath.join(directory, script))
                    if not path.startswith("..") and exists(role, path) is False and not _declared(path, declared):
                        report.errors.append(
                            f"PREFLIGHT_INPUT_MISSING: {where} runs {path}, which is not in the repository at "
                            f"{base} and no expected path of {task_id} or its predecessors declares it")
                if argv[:2] == ["npm", "run"] and len(argv) > 2 or argv[:2] == ["npm", "test"]:
                    name = argv[2] if argv[1] == "run" else "test"
                    package = posixpath.normpath(posixpath.join(directory, "package.json"))
                    if _declared(package, declared):
                        continue
                    raw = read(role, package)
                    try:
                        scripts = (json.loads(raw) if raw else {}).get("scripts") or {}
                    except ValueError:
                        scripts = {}
                    if name not in scripts:
                        (report.errors if strict else report.warnings).append(f"PREFLIGHT_SCRIPT_MISSING: {where} runs `npm {argv[1]} "
                                             f"{name if argv[1] == 'run' else ''}`".rstrip() +
                                             f" but {package} at {base} has no `{name}` script and no task "
                                             "declares that it changes package.json")
    ids = list(tasks)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if tasks[a].get("repository") != tasks[b].get("repository"):
                continue
            if a in _ancestors(tasks, b) or b in _ancestors(tasks, a):
                continue
            shared = [p for p in tasks[a].get("expected_paths") or ()
                      if any(_overlap(p, q) for q in tasks[b].get("expected_paths") or ())]
            if shared:
                report.warnings.append(f"PREFLIGHT_PATHS_UNORDERED: {a} and {b} both declare {shared[0]} without an "
                                       "order between them; they will run one after the other")
    return report
