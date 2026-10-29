#!/usr/bin/env python3
"""PostToolUse hook (Claude Code Edit|Write|MultiEdit|Bash, Codex apply_patch and shell): warn the agent when a
source file passes the size limit. Also the pure snapshot check the durable runtime runs at capture time.

Never blocks; it adds a note to the agent's context so it splits the file by responsibility.

- An edit tool names its file, so that file is checked on every edit (unchanged behaviour).
- A shell command names nothing reliably, so after one the hook asks git (`git status`, no optional locks) which
  files the work tree changed and compares each changed source file with HEAD. Reported once per session: `new`
  (absent at HEAD, over the limit now), `crossed` (within the limit at HEAD, over it now) and `grew` (already over
  it at HEAD and longer now: adding to a giant file is what the rule is about). A file already over the limit that
  did not grow is left alone. Outside a git work tree it says nothing: without a baseline it would only guess.
- `snapshot_findings(repo, base, snapshot)` applies the same rule between two commits, whatever tool wrote them.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath

LIMIT = 500
SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".astro", ".vue", ".svelte",
              ".cs", ".java", ".kt", ".go", ".rs", ".rb", ".php", ".css", ".scss", ".sql"}
SKIP_PARTS = {"node_modules", "dist", "build", ".next", "migrations", "generated", "__generated__", "vendor",
              "third_party", ".venv", "site-packages"}
EXEMPT_SUFFIXES = (".d.ts", ".min.js", ".test.ts", ".spec.ts", ".test.tsx", "_test.py", "_pb2.py", ".pb.go")
GENERATED_MARKS = (b"@generated", b"DO NOT EDIT")       # looked for in the first KiB (protoc, Go, Relay, ...)
SHELL_TOOLS = {"Bash", "PowerShell", "shell", "local_shell", "exec_command", "unified_exec"}
MAX_BYTES = 4 << 20                 # larger than this is data or a bundle, not a file someone writes by hand
MAX_CANDIDATES = 400                # changed source files examined per repository and command
MAX_REPOS = 4
GIT_SECONDS = 3.0
BUDGET_SECONDS = 6.0                # the whole shell scan; the installed hook timeout is 10 s
STATE_DAYS = 14
_ABS_PATH = re.compile(r"""(?:^|[\s'"=:(])((?:~|/)[^\s'"`;|&<>()$]*)""")


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
        if isinstance(data, dict):
            run(data)
    except Exception:  # noqa: BLE001 - a hook never breaks the session on its own errors
        return


def run(data: dict) -> None:
    inp = data.get("tool_input") or {}
    # Claude Code edits carry file_path; Codex apply_patch carries "*** Update File: <path>" lines
    paths = [inp["file_path"]] if isinstance(inp, dict) and inp.get("file_path") else re.findall(
        r"\*\*\* (?:Update|Add) File: (.+)", json.dumps(inp).replace("\\n", "\n"))
    cwd = Path(data.get("cwd") or ".")
    notes, reported = [], {}
    for path in paths:
        p = cwd / path.strip().strip('"')
        n = edited_lines(p)
        if n is not None:
            notes.append(edit_message(p.name, n))
            reported[os.path.realpath(p)] = n
    state_file = _state_file(str(data.get("session_id") or ""))
    if data.get("tool_name") in SHELL_TOOLS:
        seen = set(_load(state_file)) | set(reported)
        workdir = inp.get("workdir") if isinstance(inp, dict) else None   # Codex runs a command in its own workdir
        start = cwd / workdir if isinstance(workdir, str) and workdir else cwd
        findings = shell_findings(start, _command_text(inp), seen)
        if findings:
            notes.append(shell_message(findings))
            reported.update({f["abs"]: f["lines"] for f in findings})
    if reported:
        _remember(state_file, reported)
    if notes:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                                 "additionalContext": "\n\n".join(notes)}}))


# ------------------------------------------------------------------------------------------------------- rules

def is_source(path: str | Path) -> bool:
    """Hand-written source by name: generated, vendored, lock, data and test files are not."""
    p = PurePosixPath(str(path).replace("\\", "/"))
    name = p.name.lower()
    if p.suffix.lower() not in SOURCE_EXT or SKIP_PARTS & {x.lower() for x in p.parts}:
        return False
    return not (name.endswith(EXEMPT_SUFFIXES) or ".generated." in name or "_generated." in name)


def count_lines(data: bytes) -> int:
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def generated(data: bytes) -> bool:
    head = data[:1024]
    return any(mark in head for mark in GENERATED_MARKS)


def classify(lines: int, base_lines: int | None, limit: int = LIMIT) -> str | None:
    """`new`, `crossed`, `grew`, or None when the change is not a size regression."""
    if lines <= limit:
        return None
    if base_lines is None:
        return "new"
    if base_lines <= limit:
        return "crossed"
    return "grew" if lines > base_lines else None


def edited_lines(p: Path) -> int | None:
    """Line count of an edited source file over the limit, else None."""
    if not is_source(p):
        return None
    try:
        data = p.read_bytes()
    except OSError:
        return None
    n = count_lines(data)
    return n if n > LIMIT and not generated(data) else None


def edit_message(name: str, n: int) -> str:
    return (f"[metodologia] {name} now has {n} lines (> {LIMIT}). The user strongly dislikes giant files. You just "
            f"edited it, so splitting it IS in scope: before finishing, move the code you added (and the part it "
            f"belongs to) into its own module by responsibility (single responsibility, feature modules, atomic "
            f"components), keep behavior identical, and re-run the tests. Only if you didn't add lines (a one-line "
            f"fix) may you leave the split as a Proposal + PENDING.md item instead.")


def describe(finding: dict) -> str:
    path, lines, base = finding["path"], finding["lines"], finding.get("base_lines")
    if finding["kind"] == "new":
        return f"{path} (new, {lines} lines)"
    if finding["kind"] == "grew":
        return f"{path} ({base} -> {lines} lines; it was already over the limit and grew)"
    return f"{path} ({base} -> {lines} lines)"


def _listing(findings: list[dict], shown: int = 15) -> str:
    more = f"; and {len(findings) - shown} more" if len(findings) > shown else ""
    return "; ".join(describe(f) for f in findings[:shown]) + more


def shell_message(findings: list[dict]) -> str:
    return (f"[metodologia] After that shell command git shows source files over {LIMIT} lines that were not like that "
            f"at HEAD: {_listing(findings)}. The user strongly dislikes giant files. Splitting "
            f"them IS in scope: before finishing, move the code you added (and the part it belongs to) into its own "
            f"module by responsibility, keep behavior identical, and re-run the tests. Only a one-line fix may leave "
            f"the split as a Proposal + PENDING.md item. Edit code with the Edit/Write tools so each change is checked.")


def findings_note(findings: list[dict]) -> str:
    """The same advice for an agent's next attempt or review, from `snapshot_findings` results."""
    if not findings:
        return ""
    return (f"File size guard: your snapshot left source files over {LIMIT} lines: "
            f"{_listing(findings)}. Split each by responsibility (move the code you added and "
            f"the part it belongs to into its own module), keep behavior identical and re-run the checks.")


# ------------------------------------------------------------------------------------------------------- git

def _git(cwd: str | Path, *args: str, stdin: bytes | None = None, timeout: float = GIT_SECONDS) -> bytes | None:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    try:
        done = subprocess.run(["git", *args], cwd=str(cwd), input=stdin, capture_output=True, timeout=timeout,
                              env=env, check=False)
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return done.stdout if done.returncode == 0 else None


def _objects(cwd: str | Path, specs: list[str], *, contents: bool, timeout: float = GIT_SECONDS) -> dict | None:
    """`git cat-file --batch[-check]` for many `<rev>:<path>` specs in one process: spec -> blob bytes (or size),
    None for a missing or non-blob object. None overall when git itself failed."""
    specs = [s for s in dict.fromkeys(specs) if "\n" not in s]
    if not specs:
        return {}
    out = _git(cwd, "cat-file", "--batch" if contents else "--batch-check",
               stdin="".join(f"{s}\n" for s in specs).encode("utf-8", "surrogateescape"), timeout=timeout)
    if out is None:
        return None
    found: dict = {}
    pos = 0
    for spec in specs:
        end = out.find(b"\n", pos)
        if end < 0:
            return None
        parts, pos = out[pos:end].rsplit(b" ", 2), end + 1
        if len(parts) != 3 or not parts[2].isdigit():          # "<spec> missing" / "<spec> ambiguous"
            found[spec] = None
            continue
        size, blob = int(parts[2]), parts[1] == b"blob"
        if contents:
            found[spec] = out[pos:pos + size] if blob else None
            pos += size + 1
        else:
            found[spec] = size if blob else None
    return found


def snapshot_findings(repo: str | Path, base: str, snapshot: str, *, limit: int = LIMIT,
                      timeout: float = 30.0) -> list[dict]:
    """Source files a commit range left over `limit` lines, by the hook's rule: [{path, lines, base_lines, kind}].
    Reads git objects only (no work tree), so it sees every write whatever tool made it. Raises RuntimeError when
    git cannot read the range."""
    if base.startswith("-") or snapshot.startswith("-"):
        raise ValueError("base and snapshot must be revisions, not options")
    out = _git(repo, "diff", "--name-status", "-z", "-M", "--no-ext-diff", "--no-relative", base, snapshot,
               timeout=timeout)
    if out is None:
        raise RuntimeError(f"git diff {base[:12]}..{snapshot[:12]} failed in {repo}")
    fields, changed, i = out.split(b"\0"), [], 0
    while i < len(fields) and fields[i]:
        status = fields[i].decode("ascii", "replace")
        if status[:1] in ("R", "C"):
            old, new, i = fields[i + 1], fields[i + 2], i + 3
            before = old if status[0] == "R" else None
        else:
            new, i = fields[i + 1], i + 2
            before = None if status[:1] == "A" else new
        path = new.decode("utf-8", "surrogateescape")
        if status[:1] != "D" and is_source(path):
            changed.append((path, before.decode("utf-8", "surrogateescape") if before is not None else None))
    changed = changed[:MAX_CANDIDATES * 5]
    sizes = _objects(repo, [f"{snapshot}:{p}" for p, _ in changed], contents=False, timeout=timeout)
    if sizes is None:
        raise RuntimeError(f"git cat-file failed in {repo}")
    big = [(p, b) for p, b in changed if limit < (sizes.get(f"{snapshot}:{p}") or 0) <= MAX_BYTES]
    blobs = _objects(repo, [f"{snapshot}:{p}" for p, _ in big] + [f"{base}:{b}" for _, b in big if b is not None],
                     contents=True, timeout=timeout)
    if blobs is None:
        raise RuntimeError(f"git cat-file failed in {repo}")
    findings = []
    for path, before in big:
        data = blobs.get(f"{snapshot}:{path}")
        if data is None or generated(data):
            continue
        old = blobs.get(f"{base}:{before}") if before is not None else None
        lines, base_lines = count_lines(data), count_lines(old) if old is not None else None
        kind = classify(lines, base_lines, limit)
        if kind:
            findings.append({"path": path, "lines": lines, "base_lines": base_lines, "kind": kind})
    return sorted(findings, key=lambda f: f["path"])


# ------------------------------------------------------------------------------------------------ shell scan

def _command_text(inp: object) -> str:
    command = inp.get("command") if isinstance(inp, dict) else None
    if isinstance(command, list):
        return " ".join(str(part) for part in command)
    return command if isinstance(command, str) else ""


def _top(directory: Path) -> Path | None:
    out = _git(directory, "rev-parse", "--show-toplevel", timeout=1.0)
    return Path(out.decode("utf-8", "surrogateescape").strip()) if out else None


def _work_trees(cwd: Path, command: str) -> tuple[Path | None, list[Path]]:
    """The session's work tree (None outside git) and every tree to scan: that one plus those of absolute paths
    the command names (agents often write by absolute path into another checkout or worktree). Only existing
    directories are asked; at most MAX_REPOS trees."""
    dirs: list[Path] = []
    for raw in _ABS_PATH.findall(command)[:32]:
        p = Path(os.path.expanduser(raw))
        for _ in range(4):                       # a path the command is about to create: walk up to what exists
            if p.is_dir() or p == p.parent:
                break
            p = p.parent
        if p.is_dir() and p != p.parent and p not in dirs and p != cwd:
            dirs.append(p)
    home = _top(cwd)
    tops = [home] if home else []
    for directory in dirs[:12]:
        if len(tops) >= MAX_REPOS:
            break
        top = _top(directory)
        if top and top not in tops:
            tops.append(top)
    return home, tops


def shell_findings(cwd: Path, command: str, seen: set[str]) -> list[dict]:
    deadline = time.monotonic() + BUDGET_SECONDS
    findings: list[dict] = []
    home, tops = _work_trees(cwd, command)
    for top in tops:
        if time.monotonic() > deadline:
            break
        findings += _scan(top, seen, deadline, absolute=top != home)
    return findings


def _scan(top: Path, seen: set[str], deadline: float, *, absolute: bool = False) -> list[dict]:
    changed, deleted = _status(top, seen, deadline)
    over = []                                    # (path, HEAD path or None, lines, bytes)
    for path, before in changed[:MAX_CANDIDATES]:
        if time.monotonic() > deadline:
            break
        full = top / path
        try:
            if full.is_symlink() or not full.is_file() or not LIMIT < full.stat().st_size <= MAX_BYTES:
                continue
            data = full.read_bytes()
        except OSError:
            continue
        lines = count_lines(data)
        if lines > LIMIT and not generated(data):
            over.append((path, before, lines, data))
    moved = _moved_blobs(top, deleted, [data for _, before, _, data in over if before is None])
    heads = _objects(top, [f"HEAD:{b}" for _, b, _, _ in over if b is not None], contents=True)
    findings = []
    for path, before, lines, data in over:
        if before is None and data in moved:
            continue                             # a plain `mv` of a file HEAD already had: not new code
        if before is not None and heads is None:
            continue                             # tracked but HEAD unreadable: no baseline, no claim
        old = heads.get(f"HEAD:{before}") if before is not None and heads else None
        base_lines = count_lines(old) if old is not None else None
        kind = classify(lines, base_lines)
        if kind:
            findings.append({"path": str(top / path) if absolute else path, "abs": str(top / path), "lines": lines,
                             "base_lines": base_lines, "kind": kind})
    return findings


def _status(top: Path, seen: set[str], deadline: float) -> tuple[list[tuple[str, str | None]], list[str]]:
    """Changed source files not reported yet, with their HEAD path (None when HEAD has none), and the HEAD paths
    the work tree deleted. Porcelain paths are relative to the top; `-z` keeps them unquoted."""
    out = _git(top, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=all",
               timeout=max(0.5, min(GIT_SECONDS, deadline - time.monotonic())))
    entries, changed, deleted, i = (out or b"").split(b"\0"), [], [], 0
    while i < len(entries):
        entry, i = entries[i], i + 1
        if len(entry) < 4:
            continue
        xy, path = entry[:2].decode("ascii", "replace"), entry[3:].decode("utf-8", "surrogateescape")
        before = path
        if xy[0] in "RC":                        # porcelain -z: "XY to\0from\0"
            before, i = entries[i].decode("utf-8", "surrogateescape"), i + 1
        if "D" in xy:
            if xy[0] != "A":
                deleted.append(before)
        elif is_source(path) and str(top / path) not in seen:
            changed.append((path, None if xy == "??" or xy[0] in "AC" else before))
    return changed, deleted


def _moved_blobs(top: Path, deleted: list[str], new_files: list[bytes]) -> set[bytes]:
    """Contents of deleted HEAD files that reappear byte for byte as new files (a move git status cannot pair)."""
    if not deleted or not new_files:
        return set()
    sizes = _objects(top, [f"HEAD:{d}" for d in deleted[:MAX_CANDIDATES]], contents=False) or {}
    wanted = {len(data) for data in new_files}
    blobs = _objects(top, [spec for spec, size in sizes.items() if size in wanted], contents=True) or {}
    return {blob for blob in blobs.values() if blob is not None} & set(new_files)


# ----------------------------------------------------------------------------------------- per-session memory

def _state_file(session: str) -> Path:
    sid = re.sub(r"[^A-Za-z0-9._-]", "_", session)[:120].strip(".") or "default"
    root = Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")
    return root / "metodologia" / "file-guard" / f"{sid}.json"


def _load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    reported = data.get("reported") if isinstance(data, dict) else None
    return reported if isinstance(reported, dict) else {}


def _remember(path: Path, reported: dict) -> None:
    """Files already reported in this session (absolute path -> lines), so a shell scan does not repeat them."""
    fresh = not path.exists()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f".{path.name}.{os.getpid()}")
        tmp.write_text(json.dumps({"reported": {**_load(path), **reported}}), encoding="utf-8")
        os.replace(tmp, path)
        if fresh:                                # a new session: forget the ones nobody has touched in weeks
            cutoff = time.time() - STATE_DAYS * 86400
            for old in path.parent.glob("*.json"):
                if old.stat().st_mtime < cutoff:
                    old.unlink(missing_ok=True)
    except OSError:
        return


if __name__ == "__main__":
    main()
