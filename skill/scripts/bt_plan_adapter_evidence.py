"""Offline validation of executable and script targets cited as planner evidence."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import shlex
import shutil


def _file_target_exists(base: Path | None, value: str) -> bool | None:
    if base is None:
        return None
    if value == "-":
        return None  # stdin is not a repository script we can inspect
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    try:
        return path.resolve(strict=True).is_file()
    except (OSError, RuntimeError, ValueError):
        return False


def _package_scripts(base: Path | None) -> set[str]:
    if base is None or not base.is_dir():
        return set()
    found: set[str] = set()
    for pattern in ("package.json", "*/package.json", "*/*/package.json"):
        for manifest in base.glob(pattern):
            if "node_modules" in manifest.parts:
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
                scripts = data.get("scripts") if isinstance(data, dict) else None
                if isinstance(scripts, dict):
                    found.update(key for key in scripts if isinstance(key, str))
            except (OSError, ValueError, UnicodeError, AttributeError):
                continue
    return found


def _python_target_exists(args: list[str], base: Path | None) -> bool | None:
    takes_value = {"-W", "-X", "--check-hash-based-pycs"}
    no_value = {"-b", "-bb", "-B", "-d", "-E", "-i", "-I", "-O", "-OO", "-P", "-q", "-s", "-S",
                "-u", "-v", "-vv", "-vvv"}
    index = 0
    while index < len(args):
        argument = args[index]
        if argument == "--":
            return _file_target_exists(base, args[index + 1]) if index + 1 < len(args) else False
        if argument in ("-m", "-c"):
            if index + 1 == len(args) or not args[index + 1].strip():
                return False
            if argument == "-c":
                return True  # the inline program is the script
            try:
                return importlib.util.find_spec(args[index + 1]) is not None
            except (ImportError, ModuleNotFoundError, ValueError):
                return False
        if argument in ("--help", "--version", "-V"):
            return True
        if argument in takes_value:
            if index + 1 >= len(args):
                return False
            index += 2
            continue
        if argument.startswith("-W") or argument.startswith("-X"):
            index += 1
            continue
        if argument in no_value:
            index += 1
            continue
        if argument.startswith("-"):
            return False  # an unknown option cannot prove which script the interpreter runs
        return _file_target_exists(base, argument)
    return False


def _npm_target_exists(args: list[str], base: Path | None) -> bool | None:
    working_dir = base
    index = 0
    value_options = {"--prefix", "-C", "--workspace", "-w", "--package", "--script-shell", "--cache",
                     "--registry", "--tag"}
    while index < len(args):
        argument = args[index]
        if argument in value_options:
            if index + 1 >= len(args):
                return False
            value = args[index + 1]
            if argument in ("--prefix", "-C"):
                if working_dir is None:
                    return None
                working_dir = Path(value) if Path(value).is_absolute() else working_dir / value
                if not working_dir.is_dir():
                    return False
            index += 2
            continue
        if argument.startswith("--prefix="):
            if working_dir is None:
                return None
            value = argument.partition("=")[2]
            working_dir = Path(value) if Path(value).is_absolute() else working_dir / value
            if not working_dir.is_dir():
                return False
            index += 1
            continue
        if argument.startswith("-"):
            index += 1
            continue
        command = argument
        rest = args[index + 1:]
        scripts = _package_scripts(working_dir)
        if command in ("run", "run-script"):
            return bool(rest and rest[0] in scripts)
        if command in ("test", "start"):
            return command in scripts
        if command in ("exec", "install", "ci", "init", "pack", "publish"):
            return True  # the package-manager command itself exists; its package result is not guessed
        return None
    return False


def _command_segments(value: str) -> list[list[str]] | None:
    try:
        lexer = shlex.shlex(value, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        tokens = list(lexer)
    except ValueError:
        return None
    if not tokens:
        return []
    separators = {"&&", "||", ";", "|"}
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in separators:
            if not current:
                return None
            segments.append(current)
            current = []
        elif set(token) <= set(";&|"):
            return None
        else:
            current.append(token)
    if not current:
        return None
    segments.append(current)
    return segments


def _verify_simple_command(words: list[str], base: Path | None, depth: int) -> bool | None:
    if not words or depth > 5:
        return False
    program, args = words[0], words[1:]
    name = Path(program).name
    if name == "env":
        index = 0
        working_dir = base
        while index < len(args):
            argument = args[index]
            if argument in ("-i", "--ignore-environment", "-0", "--null"):
                index += 1
                continue
            if argument in ("-u", "--unset"):
                index += 2
                continue
            if argument in ("-C", "--chdir"):
                if index + 1 >= len(args):
                    return False
                value = Path(args[index + 1])
                working_dir = value if value.is_absolute() else ((working_dir or Path.cwd()) / value)
                if not working_dir.is_dir():
                    return False
                index += 2
                continue
            if argument.startswith("--chdir="):
                value = Path(argument.partition("=")[2])
                working_dir = value if value.is_absolute() else ((working_dir or Path.cwd()) / value)
                if not working_dir.is_dir():
                    return False
                index += 1
                continue
            if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", argument):
                index += 1
                continue
            if argument.startswith("-"):
                return False
            return _verify_simple_command(args[index:], working_dir, depth + 1)
        return False
    if name in ("sh", "bash", "dash", "zsh", "fish"):
        for index, argument in enumerate(args):
            if argument == "-c" or (argument.startswith("-") and "c" in argument[1:]):
                if index + 1 >= len(args):
                    return False
                return _verify_command(args[index + 1], base, depth + 1)
        return False
    if name in ("time", "exec"):
        return _verify_simple_command(args, base, depth + 1)
    if name in ("source", "."):
        return _file_target_exists(base, args[0]) if args else False
    if re.fullmatch(r"python(?:[0-9]+(?:\.[0-9]+)*)?", name):
        return _python_target_exists(args, base)
    if name in ("npm", "pnpm", "yarn", "bun"):
        return _npm_target_exists(args, base)
    if name == "npx":
        index = 0
        while index < len(args):
            if args[index] in ("-p", "--package"):
                index += 2
                continue
            if args[index].startswith("-"):
                index += 1
                continue
            if index + 1 < len(args) and re.search(r"\.(js|mjs|cjs|ts|tsx)$", args[index + 1]):
                return _file_target_exists(base, args[index + 1])
            return None  # a package fetched by npx cannot be verified offline
        return False
    if name in ("node", "tsx", "deno", "ruby", "perl"):
        for index, argument in enumerate(args):
            if argument in ("-e", "-p", "-c", "--eval"):
                return index + 1 < len(args) and bool(args[index + 1].strip())
            if argument == "--":
                return _file_target_exists(base, args[index + 1]) if index + 1 < len(args) else False
            if not argument.startswith("-"):
                return _file_target_exists(base, argument)
        return False
    if "/" in program:
        return _file_target_exists(base, program)
    return shutil.which(program) is not None


def _verify_command(value: str, base: Path | None, depth: int = 0) -> bool | None:
    if depth > 5:
        return False
    segments = _command_segments(value)
    if segments is None or not segments:
        return False
    working_dir = base
    ran_command = False
    unverifiable = False
    for segment in segments:
        while segment and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[0]):
            segment = segment[1:]
        if not segment:
            return False
        if segment[0] == "cd":
            if len(segment) != 2 or working_dir is None:
                return False
            target = Path(segment[1])
            target = target if target.is_absolute() else working_dir / target
            try:
                target = target.resolve(strict=True)
            except (OSError, RuntimeError, ValueError):
                return False
            if not target.is_dir():
                return False
            working_dir = target
            continue
        result = _verify_simple_command(segment, working_dir, depth)
        if result is False:
            return False
        if result is None:
            unverifiable = True
        ran_command = True
    if not ran_command:
        return False
    return None if unverifiable else True


def verify_command(value: str, base: Path | None) -> bool | None:
    """Return False for missing executable/script targets and None when the target cannot be inspected offline."""
    return _verify_command(value, base)
