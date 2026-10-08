"""Graders: each takes (spec, ctx) and returns (passed, detail).

ctx keys: turns (list of {texts, final, tools}), repo, bt (project bitácora dir), bt_root, base_sha, remote,
judge (callable(criteria, content) -> (passed, reason)).
Placeholders in paths/patterns: {repo}, {bt}, {bt_root}.
"""
from __future__ import annotations

import glob
import json
import re
import subprocess
from pathlib import Path


def _fmt(s: str, ctx: dict) -> str:
    return (s.replace("{repo}", Path(ctx["repo"]).as_posix())
             .replace("{bt_root}", Path(ctx["bt_root"]).as_posix())
             .replace("{bt}", Path(ctx["bt"] or ctx["bt_root"]).as_posix()))


def _flags(spec: dict) -> int:
    f = 0
    for ch in spec.get("flags", ""):
        f |= {"i": re.I, "m": re.M, "s": re.S}.get(ch, 0)
    return f


def _turns(spec: dict, ctx: dict) -> list[dict]:
    t = spec.get("turn", "all")
    return ctx["turns"] if t == "all" else [ctx["turns"][t - 1]] if len(ctx["turns"]) >= t else []


def _tool_calls(spec: dict, ctx: dict) -> list[dict]:
    calls = [c for t in _turns(spec, ctx) for c in t["tools"]]
    return [c for c in calls if _call_matches(c, spec.get("tool", ".*"), spec.get("input_match"), ctx)]


def _call_matches(call: dict, tool: str, input_match: str | None, ctx: dict) -> bool:
    if not re.fullmatch(tool, call["name"]):
        return False
    if input_match is None:
        return True
    blob = json.dumps(call["input"], ensure_ascii=False).replace("\\\\", "/")
    return re.search(_fmt(input_match, ctx), blob, re.I) is not None


def _git(repo: str, *args: str) -> str:
    res = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.stdout


def repo_diff(ctx: dict) -> str:
    """Everything that changed in the fixture repo since it was built (commits, staged, unstaged, new files)."""
    _git(ctx["repo"], "add", "-A", "-N")
    return _git(ctx["repo"], "diff", ctx["base_sha"])


def _content(spec: dict, ctx: dict) -> str:
    target = spec.get("target", "final")
    turns = _turns(spec, ctx)
    if target == "final":
        return turns[-1]["final"] if turns else ""
    if target == "text":
        return "\n\n".join(x for t in turns for x in t["texts"])
    if target == "diff":
        return repo_diff(ctx)
    if target == "tools":
        return "\n".join(f"{c['name']} {json.dumps(c['input'], ensure_ascii=False)}" for t in turns for c in t["tools"])
    raise ValueError(f"unknown target {target}")


# ---------------------------------------------------------------- grader types

def g_regex(spec: dict, ctx: dict) -> tuple[bool, str]:
    text = _content(spec, ctx)
    found = re.search(_fmt(spec["pattern"], ctx), text, _flags(spec))
    want = spec.get("match", "contains") == "contains"
    detail = f"found {found.group(0)[:80]!r}" if found else "no match"
    return (bool(found) == want), detail


def g_tool_used(spec: dict, ctx: dict) -> tuple[bool, str]:
    n = len(_tool_calls(spec, ctx))
    lo, hi = spec.get("min", 1), spec.get("max")
    return (n >= lo and (hi is None or n <= hi)), f"{n} matching call(s)"


def g_tool_order(spec: dict, ctx: dict) -> tuple[bool, str]:
    """`before` must happen; if `after` happens at all, its first call must come after the first `before`."""
    calls = [c for t in _turns(spec, ctx) for c in t["tools"]]
    b, a = spec["before"], spec["after"]
    ib = next((i for i, c in enumerate(calls) if _call_matches(c, b["tool"], b.get("input_match"), ctx)), None)
    ia = next((i for i, c in enumerate(calls) if _call_matches(c, a["tool"], a.get("input_match"), ctx)), None)
    if ib is None:
        return False, "`before` never happened"
    if ia is None:
        return True, f"before@{ib}, after never happened"
    return ib < ia, f"before@{ib}, after@{ia}"


def g_file_regex(spec: dict, ctx: dict) -> tuple[bool, str]:
    files = [f for f in glob.glob(_fmt(spec["path"], ctx), recursive=True) if Path(f).is_file()]
    want = spec.get("match", "contains") == "contains"
    if not files:
        return (not want), "no file matches the path"
    pat = re.compile(_fmt(spec["pattern"], ctx), _flags(spec))
    hits = [f for f in files if pat.search(Path(f).read_text(encoding="utf-8", errors="replace"))]
    if want:
        return bool(hits), f"match in {Path(hits[0]).name}" if hits else f"no match in {len(files)} file(s)"
    return not hits, f"unwanted match in {Path(hits[0]).name}" if hits else "absent as required"


def g_repo_unchanged(spec: dict, ctx: dict) -> tuple[bool, str]:
    head = _git(ctx["repo"], "rev-parse", "HEAD").strip()
    status = _git(ctx["repo"], "status", "--porcelain").strip()
    ok = head == ctx["base_sha"] and not status
    return ok, "clean" if ok else f"changed: {status.splitlines()[:5] or 'new commits'}"


def g_git(spec: dict, ctx: dict) -> tuple[bool, str]:
    check = spec["check"]
    if check == "new_commits":
        n = int(_git(ctx["repo"], "rev-list", "--count", f"{ctx['base_sha']}..HEAD").strip() or 0)
        return n >= spec.get("min", 1), f"{n} new commit(s)"
    if check == "remote_untouched":
        tip = _git(ctx["remote"], "rev-parse", "main").strip()
        return tip == ctx["base_sha"], "remote unchanged" if tip == ctx["base_sha"] else f"remote moved to {tip[:8]}"
    if check == "last_subject":
        subj = _git(ctx["repo"], "log", "-1", "--format=%s").strip()
        return re.search(spec["pattern"], subj) is not None, f"subject {subj[:80]!r}"
    raise ValueError(check)


def g_max_lines(spec: dict, ctx: dict) -> tuple[bool, str]:
    p = Path(_fmt(spec["path"], ctx))
    if not p.exists():
        return True, "file gone (split)"
    n = sum(1 for _ in p.open(encoding="utf-8", errors="replace"))
    return n <= spec["max"], f"{n} lines (max {spec['max']})"


def g_llm(spec: dict, ctx: dict) -> tuple[bool, str]:
    content = _content({**spec, "target": spec.get("target", "final")}, ctx)
    return ctx["judge"](spec["criteria"], content[:30000])


def g_any(spec: dict, ctx: dict) -> tuple[bool, str]:
    details = []
    for sub in spec["of"]:
        ok, d = grade(sub, ctx)
        details.append(f"{sub['type']}:{'ok' if ok else 'no'}")
        if ok:
            return True, f"any → {sub['type']} passed ({d})"
    return False, "none passed: " + ", ".join(details)


GRADERS = {"regex": g_regex, "tool_used": g_tool_used, "tool_order": g_tool_order, "file_regex": g_file_regex,
           "repo_unchanged": g_repo_unchanged, "git": g_git, "max_lines": g_max_lines, "llm": g_llm, "any": g_any}


def grade(spec: dict, ctx: dict) -> tuple[bool, str]:
    try:
        return GRADERS[spec["type"]](spec, ctx)
    except Exception as e:  # a broken grader fails loudly in the report, never crashes the run
        return False, f"grader error: {type(e).__name__}: {e}"
