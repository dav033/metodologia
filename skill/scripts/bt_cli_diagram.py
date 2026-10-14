"""CLI for the native diagram capability: `bitacora.py --project P diagram doctor|validate|publish|compare|list`."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def register(sub) -> None:
    p = sub.add_parser("diagram", help="architecture/workflow/sequence/dataflow/lifecycle diagrams (pinned Archify, "
                       "standalone HTML + source IR in the project's artifacts)")
    p.add_argument("action", choices=["doctor", "validate", "publish", "compare", "list", "check"])
    p.add_argument("args", nargs="*", help="validate: TYPE IR.json; publish: NAME TYPE IR.json; "
                   "compare: NAME BASE.json HEAD.json; check: NAME")
    p.add_argument("--title", help="publish: human title kept in the provenance record")


def dispatch(a, project: str | None, root: Path) -> int:
    import bt_diagram
    try:
        if a.action == "doctor":
            print(json.dumps(bt_diagram.doctor(), indent=1))
            return 0
        if a.action == "validate":
            if len(a.args) != 2:
                sys.exit("usage: diagram validate TYPE IR.json")
            report = bt_diagram.validate(a.args[0], Path(a.args[1]))
            print(json.dumps(report, indent=1))
            return 0 if report["ok"] else 1
        if not project:
            sys.exit("No project resolved; pass --project <name>.")
        pdir = root / project
        if a.action == "list":
            found = sorted(p.name for p in (pdir / "artifacts").glob("diagram-*.html")) if (pdir / "artifacts").exists() else []
            print(json.dumps(found, indent=1))
            return 0
        if a.action == "check":
            if len(a.args) != 1:
                sys.exit("usage: diagram check NAME")
            page = pdir / "artifacts" / f"diagram-{a.args[0]}.html"
            if not page.is_file():
                sys.exit(f"no published diagram '{a.args[0]}' in {project}")
            report = bt_diagram.visual_check(page)
            print(json.dumps({k: report.get(k) for k in ("ok", "status", "checks", "visualReview", "evidence")}, indent=1))
            return 0 if report.get("ok") else 1
        if a.action == "publish":
            if len(a.args) != 3:
                sys.exit("usage: diagram publish NAME TYPE IR.json [--title T]")
            print(json.dumps(bt_diagram.publish(pdir, a.args[0], a.args[1], Path(a.args[2]), title=a.title), indent=1))
            return 0
        if len(a.args) != 3:
            sys.exit("usage: diagram compare NAME BASE.json HEAD.json")
        print(json.dumps(bt_diagram.compare(pdir, a.args[0], Path(a.args[1]), Path(a.args[2])), indent=1))
        return 0
    except bt_diagram.DiagramError as error:
        print(f"diagram: {error}", file=sys.stderr)
        return 1
