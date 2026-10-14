"""Command-line wiring for independent interactive code review."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def register(sub: argparse._SubParsersAction) -> None:
    parser = sub.add_parser("review", help="independently review current changes in a detached worktree")
    parser.add_argument("--base", help="commit/ref to compare against (default: merge-base with default branch)")
    parser.add_argument("--focus", help="review focus")
    parser.add_argument("--provider", choices=["claude", "codex", "antigravity"])
    parser.add_argument("--agent-cmd", help="tests: command template with {prompt_file} {workdir} {result} {id}")


def dispatch(args: argparse.Namespace, project: str | None) -> None:
    import bt_code_review
    result = bt_code_review.review(Path(args.cwd), args.base, args.focus, args.provider, project, args.agent_cmd)
    print(json.dumps(result, indent=1, ensure_ascii=False))
