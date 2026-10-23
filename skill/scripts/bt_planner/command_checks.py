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
