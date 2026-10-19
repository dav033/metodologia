"""CLI surface for invoking the methodology Planner through an explicit local AI profile."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bt_profiles
from bt_core import find_req
from bt_planner_runtime import PlannerRequest, PlannerRuntimeError, invoke


def register(subparsers) -> None:
    parser = subparsers.add_parser("planner", help="invoke the canonical Planner through a selected local AI profile")
    actions = parser.add_subparsers(dest="planner_action", required=True)
    launch = actions.add_parser("invoke", help="read the planning request from stdin and invoke one selected profile")
    launch.add_argument("--provider", choices=bt_profiles.LAUNCHABLE)
    launch.add_argument("--profile", help="account profile from `bitacora profiles list`")
    launch.add_argument("--model", help="exact model id or alias to pass to the selected provider")
    launch.add_argument("--effort", help="exact effort selector; omit to retain the provider's configured default")
    launch.add_argument("--complexity", choices=["S", "M", "L"])
    launch.add_argument("--timeout", type=int, default=900, help="provider deadline in seconds (1–86400)")
    launch.add_argument("--req", help="REQ-NNN in the selected project; supplies its requirement directory")
    launch.add_argument("--repo", action="append", default=[], metavar="ROLE=PATH",
                        help="workspace repository mapping; repeat once per repository role")


def dispatch(args: argparse.Namespace, project: str, cwd: Path, root: Path) -> int:
    prompt = sys.stdin.read()
    if not prompt.strip():
        print("planner invoke needs a non-empty request on stdin; nothing was sent", file=sys.stderr)
        return 2
    try:
        requirement_dir = find_req(root / project, args.req) if args.req else None
        repositories: dict[str, Path] = {}
        for value in args.repo:
            role, separator, repository_path = value.partition("=")
            if not separator or not role or not repository_path or role in repositories:
                raise PlannerRuntimeError("--repo values must be unique ROLE=PATH mappings")
            repositories[role] = Path(repository_path)
        if not args.profile and not args.provider:
            import bt_delegate
            route = bt_delegate.auto_route(project, "implement", None, role="planner",
                                           complexity=getattr(args, "complexity", None),
                                           model=args.model, effort=args.effort)
            args.provider, args.profile, args.model, args.effort = (
                route["agent"], route["profile"], route["model"], route["effort"])
        elif not args.profile:
            raise PlannerRuntimeError("A pinned --provider requires --profile; omit both for quota-aware selection")
        elif not args.provider or not args.model:
            import bt_role_policy
            provider = bt_profiles.provider_of(args.profile)
            if args.provider and args.provider != provider:
                raise PlannerRuntimeError("--provider and --profile must select the same provider")
            args.provider = provider
            choice = next(((m, e) for p, m, e in bt_role_policy.options(
                "planner", getattr(args, "complexity", None)) if p == provider), None)
            if not args.model and not choice:
                raise PlannerRuntimeError("No approved Planner model for this provider; specify --model explicitly")
            args.model = args.model or choice[0]
            args.effort = args.effort or (choice[1] if choice else None)
        if not args.effort:
            import bt_role_policy
            args.effort = next((e for p, m, e in bt_role_policy.options(
                "planner", getattr(args, "complexity", None)) if p == args.provider and m == args.model), None)
        request = PlannerRequest(project=project, provider=args.provider, profile=args.profile,
                                 model=args.model, effort=args.effort, prompt=prompt, cwd=cwd,
                                 timeout_seconds=args.timeout, requirement_dir=requirement_dir,
                                 repositories=repositories)
    except SystemExit as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except PlannerRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    try:
        result = invoke(request)
    except PlannerRuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if result.stderr:
        print(result.stderr, end="" if result.stderr.endswith("\n") else "\n", file=sys.stderr)
    if result.response:
        print(result.response, end="" if result.response.endswith("\n") else "\n")
    if result.returncode:
        return result.returncode
    if not result.response.strip():
        print("Planner runtime returned no response", file=sys.stderr)
        return 1
    return 0
