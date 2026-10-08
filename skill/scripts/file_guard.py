#!/usr/bin/env python3
"""PostToolUse hook (Claude Code Edit|Write|MultiEdit, Codex apply_patch): warn the agent when a source file
passes the size limit.

Never blocks; it adds a note to the agent's context so it splits the file by responsibility.
"""
import json
import re
import sys
from pathlib import Path

LIMIT = 500
SOURCE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".astro", ".vue", ".svelte",
              ".cs", ".java", ".kt", ".go", ".rs", ".rb", ".php", ".css", ".scss", ".sql"}
SKIP_PARTS = {"node_modules", "dist", "build", ".next", "migrations", "generated", "__generated__", "vendor"}


def main() -> None:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return
    inp = data.get("tool_input") or {}
    # Claude Code edits carry file_path; Codex apply_patch carries "*** Update File: <path>" lines
    paths = [inp["file_path"]] if isinstance(inp, dict) and inp.get("file_path") else re.findall(
        r"\*\*\* (?:Update|Add) File: (.+)", json.dumps(inp).replace("\\n", "\n"))
    cwd = Path(data.get("cwd") or ".")
    for path in paths:
        check(cwd / path.strip().strip('"'))


def check(p: Path) -> None:
    if p.suffix.lower() not in SOURCE_EXT or SKIP_PARTS & {x.lower() for x in p.parts}:
        return
    if p.name.endswith((".d.ts", ".min.js", ".test.ts", ".spec.ts", ".test.tsx", "_test.py")):
        return
    try:
        n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
    except Exception:
        return
    if n <= LIMIT:
        return
    msg = (f"[metodologia] {p.name} now has {n} lines (> {LIMIT}): alert. The user strongly dislikes giant files. "
           f"If you're working on this file within the task's scope, split it by responsibility now (single "
           f"responsibility, feature modules, atomic components). If splitting is out of scope, add it to "
           f"PENDING.md and to the Proposals in your final report.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    main()
