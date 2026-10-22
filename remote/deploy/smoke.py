#!/usr/bin/env python3
"""Run public live probes and record a redacted live-smoke receipt."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

DEPLOY = Path(__file__).resolve().parent
RECEIPT_DIR = DEPLOY / "receipts"
TIMEOUT = 12.0


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_response(request: Request) -> tuple[int, object, bytes]:
    opener = build_opener(NoRedirect())
    try:
        response = opener.open(request, timeout=TIMEOUT)
    except HTTPError as error:
        response = error
    headers = response.headers
    body = response.read(64 * 1024)
    return response.code, headers, body


def json_file(name: str) -> dict:
    return json.loads((RECEIPT_DIR / f"{name}.json").read_text(encoding="utf-8"))


def cookie_attributes(set_cookie: str) -> set[str]:
    return {part.strip().lower() for part in set_cookie.split(";")[1:]}


def check(ok: bool, detail: str) -> dict[str, object]:
    result = {"ok": ok, "detail": detail}
    print(json.dumps({"ok": ok, "detail": detail}, sort_keys=True))
    return result


def live_smoke() -> int:
    gateway_receipt = json_file("gateway-release")
    frontend_receipt = json_file("vercel-frontend")
    gateway = "https://flow-api.185-147-157-25.sslip.io"
    frontend = frontend_receipt["deployment"]["production_alias"].rstrip("/")
    release_sha = gateway_receipt["deployed_git_sha"]
    checks: dict[str, dict[str, object]] = {}

    try:
        page_status, _, _ = open_response(Request(frontend + "/", headers={"Accept": "text/html"}))
        gateway_status, _, gateway_body = open_response(Request(gateway + "/healthz"))
        try:
            gateway_health = json.loads(gateway_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            gateway_health = None
        gateway_ok = (
            gateway_status == 200
            and isinstance(gateway_health, dict)
            and gateway_health.get("status") == "ok"
            and gateway_health.get("release_sha") == release_sha
        )
        login_status, login_headers, _ = open_response(Request(
            frontend + "/api/auth/login", headers={"Accept": "text/html"}
        ))
        location = login_headers.get("Location", "")
        parts = urlsplit(location)
        params = parse_qs(parts.query, keep_blank_values=True)
        state_cookies = [
            value for key, value in login_headers.items()
            if key.lower() == "set-cookie" and value.split("=", 1)[0].strip() == "flow_oauth_state"
        ]
        attrs = cookie_attributes(state_cookies[0]) if len(state_cookies) == 1 else set()
        start_ok = (
            page_status == 200
            and gateway_ok
            and login_status == 302
            and parts.scheme == "https"
            and parts.netloc == "github.com"
            and bool(params.get("client_id", [""])[0])
            and bool(params.get("state", [""])[0])
            and params.get("redirect_uri") == [frontend + "/api/auth/callback"]
            and {"secure", "httponly", "samesite=lax"}.issubset(attrs)
        )
        oauth_start_ok = start_ok
        # The deployed gateway revision is the source of truth for the session-cookie policy.
        deployed_server = subprocess.check_output(
            ["git", "show", f"{release_sha}:remote/gateway/server.py"],
            cwd=DEPLOY.parents[1], text=True,
        )
        session_policy_ok = "SameSite=Strict" in deployed_server and "SESSION_COOKIE}={token}" in deployed_server
        # A live session cookie is emitted only after owner sign-in, which this headless
        # run is not authorized to perform. Source inspection is not runtime evidence.
        session_cookie_observed = False
        start_ok = start_ok and session_policy_ok and session_cookie_observed
        checks["signin-start"] = check(
            start_ok,
            f"GET {frontend}/ returned HTTP {page_status}; gateway /healthz returned HTTP {gateway_status} "
            f"with {'matching' if gateway_ok else 'non-matching'} release SHA; OAuth start returned HTTP {login_status} to github.com; "
            f"OAuth client id, state, frontend callback and state-cookie attributes {'were' if oauth_start_ok else 'were not fully'} observed; "
            f"deployed source declares Secure, HttpOnly and SameSite=Strict for the session cookie: {session_policy_ok}; "
            "the session cookie emitted after owner sign-in was not observed because this run cannot use owner credentials.",
        )

        bad_state_status, _, _ = open_response(Request(
            frontend + "/api/auth/callback?code=smoke-invalid&state=wrong",
            headers={"Cookie": "flow_oauth_state=not-the-query-state"},
        ))
        unauth_status, _, _ = open_response(Request(frontend + "/api/remote/v1/snapshot"))
        post_status, _, _ = open_response(Request(
            frontend + "/api/remote/v1/commands",
            data=b"{}",
            headers={"Content-Type": "application/json", "Origin": frontend},
            method="POST",
        ))
        negatives_ok = bad_state_status == 400 and unauth_status == 401 and post_status == 403
        checks["negative-paths"] = check(
            negatives_ok,
            f"bad-state callback HTTP {bad_state_status} (expected 400); unauthenticated API HTTP {unauth_status} "
            "(expected 401); state-changing POST without X-Flow-Request "
            f"HTTP {post_status} (expected 403).",
        )

        try:
            stream_status, _, _ = open_response(Request(
                frontend + "/api/remote/v1/stream",
                headers={"Last-Event-ID": "live-smoke-resume-probe"},
            ))
        except (URLError, TimeoutError, OSError):
            stream_status = 0
        checks["sse"] = check(
            False,
            f"Vercel stream probe with Last-Event-ID returned HTTP {stream_status}; authenticated connect and "
            "reconnect require the owner's signed-in browser session, which this task's credential restriction "
            "does not permit the executor to obtain.",
        )
    except (URLError, TimeoutError, OSError, KeyError, json.JSONDecodeError) as exc:
        detail = f"public probe failed: {type(exc).__name__}; no response values or credentials recorded"
        for name in ("signin-start", "negative-paths", "sse"):
            checks.setdefault(name, check(False, detail))

    checks["telegram-delivery"] = check(
        False,
        "Not attempted: sending requires the owner's Telegram bot token and chat id; this task explicitly forbids "
        "reading or using credentials. No message was sent.",
    )
    checks["manual-handover"] = check(
        True,
        "Per the 2026-10-22 owner ruling, phone sign-in at 360 px and refusal of a foreign GitHub account remain "
        "manual handover steps and are not acceptance gates.",
    )

    accepted = all(checks[name]["ok"] is True for name in ("signin-start", "negative-paths", "sse", "telegram-delivery"))
    receipt = {
        "schema_version": 1,
        "name": "live-smoke",
        "status": "complete" if accepted else "partial",
        "deployed_git_sha": release_sha,
        "gateway_url": gateway,
        "frontend_url": frontend,
        "evidence_source": "Public production probes from smoke.py --live. No credentials were read or recorded.",
        "steps": [{
            "name": "live-probes",
            "command": "python remote/deploy/smoke.py --live (public HTTPS probes; credential-dependent checks recorded as blocked)",
            "exit_code": 0,
        }],
        "checks": checks,
        "rollback": "Follow remote/docs/runbook.md Step 7, then Steps 6 to 3 in order if sign-in or snapshot fail.",
    }
    target = RECEIPT_DIR / "live-smoke.json"
    target.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"receipt: {target.relative_to(DEPLOY.parents[1])}")
    print(f"gateway: {gateway}; frontend: {frontend}; release sha: {release_sha}")
    print("rollback: remote/docs/runbook.md — Step 7, then Steps 6 to 3 in order")
    print("manual handover: owner's phone sign-in at 360 px and foreign GitHub account refusal")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="probe the production frontend and gateway")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live is required")
    return live_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
