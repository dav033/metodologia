#!/usr/bin/env python3
"""Validate a deployment receipt without contacting the deployed host."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

RECEIPT_DIR = Path(__file__).resolve().parent / "receipts"
REQUIRED_STEPS = {
    "snapshot-before",
    "caddy-backup",
    "service-layout",
    "systemd-verify",
    "caddy-validate",
    "caddy-reload",
    "other-hosts-check",
    "rollback-rehearsal",
}
REQUIRED_CHECKS = {
    "snapshot-before",
    "service-layout",
    "other-hosts-unchanged",
    "rollback-rehearsed",
}
GATEWAY_RELEASE_STEPS = {
    "snapshot-before",
    "release-archive",
    "hash-locked-install",
    "database-migration",
    "atomic-current-switch",
    "services-enabled-active",
    "tunnel-replacement",
    "public-smoke",
    "rollback-rehearsal",
    "other-hosts-check",
}
GATEWAY_RELEASE_CHECKS = {
    "release-active",
    "listeners-and-tunnel",
    "public-health",
    "rollback-rehearsed",
    "other-hosts-unchanged",
}
LIVE_SMOKE_CHECKS = {
    "signin-start",
    "negative-paths",
    "sse",
    "telegram-delivery",
    "manual-handover",
}
VERCEL_FRONTEND_STEPS = {
    "project-create-or-link",
    "project-settings",
    "environment-variables",
    "production-deploy",
    "deployment-ready",
    "rewrite-probe",
}
VERCEL_FRONTEND_CHECKS = {
    "project-linked",
    "env-names",
    "deployment-ready",
    "rewrite-reaches-caddy",
}
IDENTITY_CHECKS = {"oauth-app", "telegram", "generated-keys", "secrets-placement"}
SENSITIVE_NAME = re.compile(r"(?:secret|token|password|passwd|private.?key|api.?key|credential)", re.I)
SENSITIVE_ASSIGNMENT = re.compile(
    r"\b(?:[A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE_KEY|API_KEY|CREDENTIAL)[A-Z0-9_]*)"
    r"\s*=\s*([^\s,;]+)",
    re.I,
)
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bBearer\s+(?!<redacted>)[A-Za-z0-9._~+/=-]{12,}", re.I),
    re.compile(r"https?://[^/@\s:]+:[^/@\s]+@", re.I),
)
REDACTED_VALUES = {"", "<redacted>", "[redacted]", "redacted", "<secret>", "[secret]", "${redacted}"}


class ReceiptError(ValueError):
    """The receipt is incomplete, unsafe, or inconsistent with this checkout."""


def _secret_findings(value: Any, location: str = "receipt") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            if SENSITIVE_NAME.search(key_text) and isinstance(child, str) and child.strip().lower() not in REDACTED_VALUES:
                # `deployed_git_sha` and other metadata names contain no sensitive-name match.
                findings.append(f"{location}.{key_text} contains a value under a sensitive field")
            findings.extend(_secret_findings(child, f"{location}.{key_text}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_secret_findings(child, f"{location}[{index}]"))
    elif isinstance(value, str):
        for match in SENSITIVE_ASSIGNMENT.finditer(value):
            if match.group(1).strip("'\" ").lower() not in REDACTED_VALUES:
                findings.append(f"{location} contains a non-redacted sensitive assignment")
                break
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                findings.append(f"{location} resembles a credential or private key")
                break
    return findings


def _required_text(obj: dict[str, Any], key: str, where: str) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ReceiptError(f"{where}.{key} must be a non-empty string")
    return value


def validate_receipt(receipt: Any) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ReceiptError("receipt root must be a JSON object")
    if receipt.get("schema_version") != 1:
        raise ReceiptError("schema_version must be 1")
    _required_text(receipt, "name", "receipt")

    identity_receipt = receipt["name"] == "identity"
    if identity_receipt:
        required_steps = set()
        required_checks = IDENTITY_CHECKS
        if receipt.get("status") not in {"blocked", "complete"}:
            raise ReceiptError("identity receipt status must be blocked or complete")
        if receipt["status"] == "complete" and any(
            check.get("ok") is not True
            for check in receipt.get("checks", {}).values()
            if isinstance(check, dict)
        ):
            raise ReceiptError("a complete identity receipt cannot contain failed checks")
    elif receipt["name"] == "vercel-frontend":
        required_steps = VERCEL_FRONTEND_STEPS
        required_checks = VERCEL_FRONTEND_CHECKS
        project = receipt.get("project")
        if not isinstance(project, dict):
            raise ReceiptError("project must be an object")
        for key, expected in {
            "name": "flow-remote",
            "team": "dav033s-projects",
            "root_directory": "remote/web",
            "framework": "nextjs",
        }.items():
            if project.get(key) != expected:
                raise ReceiptError(f"project.{key} must be {expected}")
        deployment = receipt.get("deployment")
        if not isinstance(deployment, dict):
            raise ReceiptError("deployment must be an object")
        for key in ("url", "id", "status", "target"):
            _required_text(deployment, key, "deployment")
        if deployment["status"].lower() != "ready" or deployment["target"].lower() != "production":
            raise ReceiptError("deployment must be Ready and target production")
        if not re.fullmatch(r"https://[a-z0-9-]+\.vercel\.app", deployment["url"]):
            raise ReceiptError("deployment.url must be a production *.vercel.app URL")
        env_names = receipt.get("environment_variable_names")
        if not isinstance(env_names, list) or not all(isinstance(name, str) for name in env_names):
            raise ReceiptError("environment_variable_names must be an array of names")
        if env_names != ["GATEWAY_ORIGIN"]:
            raise ReceiptError("only GATEWAY_ORIGIN may be configured")
    elif receipt["name"] == "gateway-release":
        required_steps = GATEWAY_RELEASE_STEPS
        required_checks = GATEWAY_RELEASE_CHECKS
    elif receipt["name"] == "live-smoke":
        required_steps = {"live-probes"}
        required_checks = LIVE_SMOKE_CHECKS
        if receipt.get("status") not in {"partial", "complete", "blocked"}:
            raise ReceiptError("live-smoke status must be partial, complete, or blocked")
    else:
        required_steps = REQUIRED_STEPS
        required_checks = REQUIRED_CHECKS

    sha = _required_text(receipt, "deployed_git_sha", "receipt")
    if not re.fullmatch(r"[0-9a-fA-F]{40}|[0-9a-fA-F]{64}", sha):
        raise ReceiptError("deployed_git_sha must be a full Git commit SHA")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
        capture_output=True,
        text=True,
    )
    if ancestor.returncode != 0:
        raise ReceiptError("deployed_git_sha is not an ancestor commit of HEAD")

    steps = receipt.get("steps")
    if not isinstance(steps, list):
        raise ReceiptError("steps must be an array")
    seen_steps: dict[str, dict[str, Any]] = {}
    for index, step in enumerate(steps):
        where = f"steps[{index}]"
        if not isinstance(step, dict):
            raise ReceiptError(f"{where} must be an object")
        name = _required_text(step, "name", where)
        if name in seen_steps:
            raise ReceiptError(f"duplicate step: {name}")
        seen_steps[name] = step
        _required_text(step, "command", where)
        code = step.get("exit_code")
        if not isinstance(code, int) or isinstance(code, bool):
            raise ReceiptError(f"{where}.exit_code must be an integer")
        if code != 0:
            raise ReceiptError(f"step {name} failed with exit code {code}")
    missing_steps = sorted(required_steps - seen_steps.keys())
    if missing_steps:
        raise ReceiptError("missing required steps: " + ", ".join(missing_steps))

    checks = receipt.get("checks")
    if not isinstance(checks, dict):
        raise ReceiptError("checks must be an object keyed by check name")
    missing_checks = sorted(required_checks - checks.keys())
    if missing_checks:
        raise ReceiptError("missing required checks: " + ", ".join(missing_checks))
    for name, check in checks.items():
        if not isinstance(check, dict):
            raise ReceiptError(f"check {name} must be an object")
        if not isinstance(check.get("ok"), bool):
            raise ReceiptError(f"check {name}.ok must be a boolean")
        if not identity_receipt and receipt["name"] != "live-smoke" and check.get("ok") is not True:
            raise ReceiptError(f"check {name} did not pass")
        _required_text(check, "detail", f"checks.{name}")

    findings = _secret_findings(receipt)
    if findings:
        raise ReceiptError("possible secret/credential value; redact it before recording: " + "; ".join(findings))
    return receipt


def resolve_receipt(selector: str) -> Path:
    path = Path(selector)
    if path.is_file():
        return path
    if Path(selector).name != selector or selector in {".", ".."}:
        raise ReceiptError(f"receipt file does not exist: {selector}")
    candidate = RECEIPT_DIR / f"{selector}.json"
    if not candidate.is_file():
        raise ReceiptError(f"receipt not found: {candidate}")
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", help="receipt name in receipts/ or a JSON file path")
    parser.add_argument("--check", help="require and report a specific named check")
    args = parser.parse_args(argv)
    try:
        path = resolve_receipt(args.receipt)
        receipt = json.loads(path.read_text(encoding="utf-8"))
        validate_receipt(receipt)
        if args.check:
            check = receipt["checks"].get(args.check)
            if check is None:
                raise ReceiptError(f"check not found: {args.check}")
            if check["ok"] is not True:
                raise ReceiptError(f"{args.check} did not pass: {check['detail']}")
            print(f"{args.check}: ok — {check['detail']}")
        else:
            if receipt["name"] == "identity" and receipt["status"] == "blocked":
                raise ReceiptError("identity setup is blocked; run a named check for details")
            print(f"receipt {receipt['name']}: valid")
        return 0
    except (OSError, json.JSONDecodeError, ReceiptError, KeyError) as exc:
        print(f"receipt invalid: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
