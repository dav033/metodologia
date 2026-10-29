"""Conservative checks of the paths named by verification commands; repository facts come from the caller."""
from __future__ import annotations

import posixpath
import re
import shlex
from collections.abc import Callable

IgnoredPath = Callable[[str, str], bool | None]


def tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return []


def _path(word: str, directory: str) -> str | None:
    word = word.split("=", 1)[-1] if word.startswith("--") and "=" in word else word
    if word.startswith(("-", "$", "~")) or "://" in word or re.search(r"[*$?{}\[\]<>|;&]", word):
        return None
    if "/" not in word and "." not in word:
        return None
    path = posixpath.normpath(posixpath.join(directory, word))
    return path if path != ".." and not path.startswith("../") else None


def _reads(words: list[str], path: str, directory: str) -> bool:
    if not words:
        return False
    if words[0] in ("cat", "stat", "head", "tail", "wc", "diff", "cmp", "test", "[", "cp", "mv"):
        return True
    script = next((word for word in words[1:] if not word.startswith("-") and
                   re.search(r"\.(?:py|[cm]?[jt]sx?)$", word)), None)
    for index, word in enumerate(words):
        if _path(word, directory) != path:
            continue
        previous = words[index - 1] if index else ""
        if previous in ("--input", "--input-file") or word.startswith(("--input=", "--input-file=")):
            return True
        if index == 0 or (word == script and "-c" not in words and
                          words[0] in ("python", "python3", "node", "tsx", "npx")):
            return True
    return False


def input_findings(plan: dict, ignored: IgnoredPath | None) -> tuple[list[str], list[str]]:
    if ignored is None:
        return [], []
    errors, warnings = [], []
    tasks = plan.get("tasks")
    for task in tasks if isinstance(tasks, list) else ():
        if not isinstance(task, dict):
            continue
        produced: set[str] = set()
        checks = task.get("verification")
        for index, check in enumerate(checks if isinstance(checks, list) else ()):
            if not isinstance(check, dict) or check.get("type") != "command" or not isinstance(check.get("value"), str):
                continue
            words = tokens(check["value"])
            directory = ""
            if len(words) >= 3 and words[0] == "cd" and words[2] == "&&":
                directory, words = words[1], words[3:]
            outputs = set()
            inputs = set()
            for n, word in enumerate(words):
                path = _path(word, directory)
                if path is None:
                    continue
                previous = words[n - 1] if n else ""
                if previous in (">", ">>", "-o", "--output", "--out") or word.startswith(("--output=", "--out=")):
                    outputs.add(path)
                elif words and words[0] == "touch" and n > 0:
                    outputs.add(path)
                elif words and words[0] in ("cp", "mv") and n == len(words) - 1:
                    outputs.add(path)
                elif words and words[0] in ("echo", "printf"):
                    continue
                else:
                    inputs.add(path)
            for path in sorted(inputs - produced - outputs):
                if ignored(str(task.get("repository", "")), path) is True:
                    target = errors if _reads(words, path, directory) else warnings
                    target.append(f"{task.get('id')}.verification[{index}]: {path} is git-ignored and is not produced "
                                  "by an earlier command of this task; a clean verification snapshot cannot rely on it")
            produced.update(outputs)
    return errors, warnings


# Where a host keeps its people's files: never inside the verifier's sandbox, which holds only a copy of the repository.
HOST_PATH = re.compile(r"^(?:~|/(?:home|root|Users|mnt|media|run/media)/)")


def host_paths(plan: dict) -> list[dict[str, object]]:
    """Sandbox command checks that name a path on the host. The verifier runs them in a sandbox holding only a copy of the
    repository, so they fail on every attempt whatever the task did (pictures REQ-021 T4.1 compared its copy of a design
    contract with the bitácora's by absolute path: three attempts, then a stop for a person)."""
    found: list[dict[str, object]] = []
    tasks = plan.get("tasks")
    for task in tasks if isinstance(tasks, list) else ():
        checks = task.get("verification") if isinstance(task, dict) else None
        for index, check in enumerate(checks if isinstance(checks, list) else ()):
            if not isinstance(check, dict) or check.get("type") != "command" or not isinstance(check.get("value"), str) \
                    or check.get("environment", "sandbox") != "sandbox":
                continue
            for word in tokens(check["value"]):
                path = word.split("=", 1)[1] if "=" in word and not HOST_PATH.match(word) else word
                if HOST_PATH.match(path):
                    found.append({"task_id": task.get("id"), "verification_index": index, "path": path,
                                  "value": check["value"]})
                    break
    return found


def host_path_warnings(plan: dict) -> list[str]:
    return [f"{c['task_id']}.verification[{c['verification_index']}]: names {c['path']}, outside the repository; the "
            "verifier runs the check in a sandbox holding only a copy of the repository, so it fails on every attempt "
            "(use a repository path, or pin the content, e.g. its sha256 with `node -e`)" for c in host_paths(plan)]


def project_ledger_checks(plan: dict, ledger_command: str = "engine audit-ledger check") -> list[str]:
    warnings = []
    tasks = plan.get("tasks")
    expected = tokens(ledger_command)
    for task in tasks if isinstance(tasks, list) else ():
        if not isinstance(task, dict) or task.get("kind") != "audit":
            continue
        checks = task.get("verification")
        for index, check in enumerate(checks if isinstance(checks, list) else ()):
            if not isinstance(check, dict) or check.get("type") != "command":
                continue
            words = tokens(str(check.get("value", "")))
            segments: list[list[str]] = [[]]
            for word in words:
                if word in ("&&", "||", ";", "|", "&"):
                    segments.append([])
                else:
                    segments[-1].append(word)
            private = False
            for segment in segments:
                program = segment[1:] if segment and re.fullmatch(r"python(?:3(?:\.\d+)?)?", posixpath.basename(segment[0])) else segment
                normalized = [posixpath.basename(program[0]), *program[1:]] if program else []
                engine = len(normalized) > len(expected) and normalized[:len(expected)] == expected
                ledger = any(".findings.json" in word or "audit-findings" in word for word in segment)
                private |= ledger and not engine
            if private:
                paths = task.get("expected_paths") or []
                path = next((p for p in paths if isinstance(p, str) and p.endswith(".findings.json")), None)
                path = path or next((w for w in words if ".findings.json" in w), "<report>.findings.json")
                warnings.append(f"{task.get('id')}.verification[{index}]: project-specific audit ledger validator; "
                                f"replace with `{ledger_command} {shlex.quote(path)}`; "
                                "the engine owns the ledger contract")
    return warnings
