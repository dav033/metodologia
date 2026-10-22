#!/usr/bin/env python3
"""Check the public gateway health, authentication boundary, and security headers."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(url: str, timeout: float) -> tuple[int, dict[str, str], bytes]:
    req = Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read(64 * 1024)
    except HTTPError as response:
        return response.code, {key.lower(): value for key, value in response.headers.items()}, response.read(64 * 1024)


def check(name: str, ok: bool, detail: str) -> bool:
    print(json.dumps({"check": name, "ok": ok, "detail": detail}, sort_keys=True))
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Public HTTPS origin of the gateway")
    parser.add_argument("--release-sha", required=True, help="Full Git SHA expected on /healthz")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if not base.startswith("https://") or len(args.release_sha) not in {40, 64}:
        parser.error("--base-url must use HTTPS and --release-sha must be a full Git SHA")

    try:
        status, headers, body = request(base + "/healthz", args.timeout)
    except (URLError, TimeoutError, OSError) as exc:
        check("public-health", False, f"health request failed: {type(exc).__name__}")
        return 1
    try:
        health = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        health = None
    health_ok = status == 200 and isinstance(health, dict) and health.get("status") == "ok" and health.get("release_sha") == args.release_sha
    all_ok = check("public-health", health_ok, f"HTTP {status}; release SHA {'matches' if health_ok else 'does not match'} expected value")

    for header, expected in (("strict-transport-security", "max-age=31536000"), ("x-content-type-options", "nosniff")):
        value = headers.get(header, "")
        ok = expected.lower() in value.lower()
        all_ok = check(f"header-{header}", ok, f"{'present' if ok else 'missing'} required value {expected}") and all_ok

    try:
        status, _, _ = request(base + "/api/remote/v1/snapshot", args.timeout)
    except (URLError, TimeoutError, OSError) as exc:
        check("unauthenticated-api", False, f"API request failed: {type(exc).__name__}")
        return 1
    api_ok = status == 401
    all_ok = check("unauthenticated-api", api_ok, f"HTTP {status}; expected 401") and all_ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
