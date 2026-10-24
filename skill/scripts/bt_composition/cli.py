"""Offline CLI for checking canonical composition manifest fingerprints."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bt-composition")
    commands = parser.add_subparsers(dest="command", required=True)
    fingerprint = commands.add_parser("manifest-sha256", help="print a canonical JSON manifest SHA-256")
    fingerprint.add_argument("manifest", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        value = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError
        canonical = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        sys.stdout.write(hashlib.sha256(canonical).hexdigest() + "\n")
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        sys.stderr.write('{"error":"invalid manifest","code":"INVALID_MANIFEST"}\n')
        return 2


__all__ = ["main"]
