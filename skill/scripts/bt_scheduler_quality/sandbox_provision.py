"""Locked dependencies for a check whose attempt installed none.

An agent that never ran the package manager leaves no `node_modules`, and every check that needs one fails the same way
(`Cannot find package ...`), attempt after attempt; the agent then edits configuration to dodge the import instead of
installing (REQ-027, T18.1). The verifier provisions what the lockfile pins: `npm ci --offline --ignore-scripts` in a
scratch directory holding only `package.json` and `package-lock.json`, cached per content hash, then mounted read-only like
any other dependency tree. Offline, so nothing is fetched; without install scripts, so no package code runs on the host.
Failure is not an error: the check then fails on its own and says why.
"""
from __future__ import annotations

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

LOGGER = logging.getLogger(__name__)
TIMEOUT_SECONDS = 600
CACHE_ENV = "M6_DEPS_CACHE"
READY = ".m6-ready"
KEPT_ENV = ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR")


def cache_root() -> Path:
    configured = os.environ.get(CACHE_ENV)
    return Path(configured) if configured else Path(os.environ.get("HOME", "/tmp")) / ".cache" / "m6-deps"


def key_of(package_root: Path) -> str | None:
    """Content hash of the manifest and lockfile, or None when the package cannot be installed from a lock."""
    try:
        manifest = (package_root / "package.json").read_bytes()
        lock = (package_root / "package-lock.json").read_bytes()
    except OSError:
        return None
    return hashlib.sha256(len(manifest).to_bytes(8, "big") + manifest + lock).hexdigest()[:32]


def provision(package_root: Path, *, root: Path | None = None, run=subprocess.run) -> Path | None:
    """The `node_modules` directory the lockfile of `package_root` pins (built once, then reused), or None."""
    key = key_of(package_root)
    npm = shutil.which("npm")
    if key is None or npm is None:
        return None
    base = Path(root) if root is not None else cache_root()
    target = base / key
    if (target / READY).is_file() and (target / "node_modules").is_dir():
        return (target / "node_modules").resolve()
    try:
        base.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=f"{key}.", dir=base))
    except OSError:
        return None
    try:
        for name in ("package.json", "package-lock.json"):
            shutil.copy2(package_root / name, scratch / name)
        env = {name: os.environ[name] for name in KEPT_ENV if name in os.environ}
        env["npm_config_update_notifier"] = "false"
        done = run([npm, "ci", "--offline", "--ignore-scripts", "--no-audit", "--no-fund"], cwd=scratch, env=env,
                   stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)
        if done.returncode or not (scratch / "node_modules").is_dir():
            LOGGER.warning("dependencies not provisioned (npm ci exit %s): %s", done.returncode,
                           (done.stderr or "").strip()[-300:])
            return None
        (scratch / READY).write_text(key + "\n", encoding="utf-8")
        try:
            scratch.rename(target)
        except OSError:                                   # another verification built it first
            if not (target / READY).is_file():
                return None
        return (target / "node_modules").resolve()
    except (OSError, subprocess.SubprocessError) as error:
        LOGGER.warning("dependencies not provisioned (%s)", type(error).__name__)
        return None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
