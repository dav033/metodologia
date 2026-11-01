"""Argument plumbing for per-subplan verification (bt_verification): status, open a version locally, approve, reject,
and the version's test servers for an agent that reproduces a rejection (serve, stop-servers, storage-state)."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from bt_core import find_req


def register(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("verify", help="try each finished subplan on its own: status, open, approve, reject")
    parser.add_argument("action", choices=("status", "open", "close", "discard", "keep", "approve", "reject",
                                           "revert-command", "serve", "stop-servers", "storage-state"),
                        help="discard/keep: the owner's choice for a copy with edits at an older commit of its version "
                             "(drop them, or move the copy aside), then open the published commit (D-278)")
    parser.add_argument("req", help="REQ-NNN")
    parser.add_argument("subplan", nargs="?", help="SP-n (every action but status)")
    parser.add_argument("--note", default="", help="why it is rejected (required to reject)")
    parser.add_argument("--image", action="append", default=[], metavar="FILE",
                        help="reject: an image the owner attached (PNG, JPEG, WebP or GIF; repeat for several, D-258)")
    parser.add_argument("--by", choices=("owner", "planner"),
                        help="approve/reject record the owner's decision: an agent passes `owner` only to relay the "
                             "owner's explicit words, never on its own judgment")
    parser.add_argument("--login", action="store_true", help="serve: start it as in production (accounts and roles), "
                                                             "not signed in as the local administrator")
    parser.add_argument("--timeout", type=int, default=900, help="serve: seconds to wait for every server to answer")
    parser.add_argument("--account", default="", help="storage-state: the test account (default: the recipe's)")
    parser.add_argument("--out", default="", help="storage-state: the Playwright storage-state file to write (0600)")


def dispatch(args: argparse.Namespace, root: Path, project: str) -> int:
    import bt_verification as verification
    rdir = find_req(root / project, args.req)
    if args.action == "status":
        st = verification.state(rdir)
        for row in st["subplans"]:
            row["state_es"] = verification.STATES_ES[row["state"]]
        st["blocking"] = verification.gate(rdir)
        print(json.dumps(st, indent=1, ensure_ascii=False))
        return 0
    if not args.subplan:
        raise SystemExit(f"verify {args.action} needs SP-n")
    if args.action in ("approve", "reject") and args.by != "owner":
        raise SystemExit(f"verify {args.action} records the owner's decision: pass --by owner, and only when the "
                         "owner said so")
    if args.action == "discard" and args.by != "owner":
        raise SystemExit("verify discard deletes the owner's edits in the copy: pass --by owner, and only when the owner "
                         "said so")
    if args.action == "open":
        target, msg = verification.open_local(root, project, rdir, args.subplan)
        print(msg)
        return 0 if target else 1
    if args.action in ("serve", "stop-servers", "storage-state"):
        return servers(args, root, project, rdir)
    if args.action in ("discard", "keep"):
        import bt_verify_copy
        print((bt_verify_copy.discard if args.action == "discard" else bt_verify_copy.keep_aside)(
            root, project, rdir, args.subplan))
    elif args.action == "close":
        print(verification.close_local(root, project, rdir, args.subplan))
    elif args.action == "revert-command":
        print(verification.revert_command(root, project, rdir, args.subplan) or "no revert range found")
    else:
        rejecting = args.action == "reject"
        print(verification.decide(project, rdir, args.subplan, "rejected" if rejecting else "approved",
                                  args.note, "owner", via="conversation",
                                  attachments=list(getattr(args, "image", None) or []) if rejecting else None))
    return 0


def servers(args: argparse.Namespace, root: Path, project: str, rdir: Path, sleep=time.sleep) -> int:
    """The «Probar» test servers of a subplan version from a terminal: what the Solucionador uses to reproduce the
    owner's rejection on exactly the commit he tried (bt_durable.rejections)."""
    import bt_verify_servers as vs
    if args.action == "stop-servers":
        print(vs.stop(root, project, rdir, args.subplan))
        return 0
    if args.action == "serve":
        started = vs.start(root, project, rdir, args.subplan, login=args.login)
        print(started["message"])
        if not started["ok"]:
            return 1
        deadline = time.monotonic() + max(0, args.timeout)
        while True:
            now = vs.status(root, project, rdir, args.subplan)
            if now["state"] in ("ready", "failed") or time.monotonic() >= deadline:
                break
            sleep(3)
        print(json.dumps({k: now.get(k) for k in ("state", "step", "url", "ports", "servers", "login", "log")},
                         ensure_ascii=False, indent=1))
        return 0 if now["state"] == "ready" else 1
    if not args.out:
        raise SystemExit("verify storage-state needs --out <file>")
    minted = vs.mint_session(root, project, rdir, args.subplan, args.account)
    if not minted["ok"]:
        print(minted["message"])
        return 1
    cookies = [{"name": minted["cookie"], "value": minted["token"], "domain": host, "path": "/", "expires": -1,
                "httpOnly": True, "secure": False, "sameSite": "Lax"} for host in ("localhost", "127.0.0.1")]
    target = Path(args.out).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump({"cookies": cookies, "origins": []}, stream)
    os.chmod(target, 0o600)
    print(f"Sesión de {minted['account']} en {minted['url']} guardada en {target} (storage state de Playwright; no "
          "imprimas su contenido).")
    return 0
