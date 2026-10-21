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
    missing_steps = sorted(REQUIRED_STEPS - seen_steps.keys())
    if missing_steps:
        raise ReceiptError("missing required steps: " + ", ".join(missing_steps))

    checks = receipt.get("checks")
    if not isinstance(checks, dict):
        raise ReceiptError("checks must be an object keyed by check name")
    missing_checks = sorted(REQUIRED_CHECKS - checks.keys())
    if missing_checks:
        raise ReceiptError("missing required checks: " + ", ".join(missing_checks))
    for name, check in checks.items():
        if not isinstance(check, dict):
            raise ReceiptError(f"check {name} must be an object")
        if check.get("ok") is not True:
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
            print(f"{args.check}: ok — {check['detail']}")
        else:
            print(f"receipt {receipt['name']}: valid")
        return 0
    except (OSError, json.JSONDecodeError, ReceiptError, KeyError) as exc:
        print(f"receipt invalid: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
