"""What a verification does not have to repeat (REQ-030 step 4): a passing check on a tree it already passed on, and the
order in which checks of very different cost run.

- **Pass cache.** Same tree + same command + same operator environment = same verdict, so a check that passed is not run
  again (a verification repeated after a restart, an audit or regression task over a tree an earlier task already
  proved). Only PASSES are reused: a failing check may be fixed by the environment, and a retry of a rejected task is a
  different tree anyway. Entries older than `policy.cache_seconds` are ignored (toolchain upgrades, network services).
- **Expensive checks last.** A check that took longer than `policy.expensive_check_seconds` the last time, or that looks
  like a whole suite, runs after the cheaper ones and is not started at all when one of them already failed: the verdict
  is FAIL either way, and the agent fixes the cheap failures before paying minutes for the suite again.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

from .policy import CheckSpec, QualityPolicy

# A whole suite: unittest discovery without a pattern or test name, npm test / npm run gate, bare pytest, cargo test.
FULL_SUITE = re.compile(
    r"(unittest\s+discover\s+(-s\s+\S+\s*|-t\s+\S+\s*)*$)|(\bnpm\s+(run\s+)?(test|gate)\s*$)|(\bpytest\s*$)|(\bcargo\s+test\s*$)")


def looks_like_full_suite(command: str) -> bool:
    tail = command.strip().rsplit("&&", 1)[-1].strip()
    return bool(FULL_SUITE.search(tail))


REPORT_FILE = re.compile(r"\.(?:md|json|txt|log|csv|html)$")


def own_outputs(kind: str | None, expected_paths) -> tuple[str, ...]:
    """The report files a task of kind `test` or `audit` writes: they change at every attempt and the suites the task's checks run do
    not read them. REQ-020's T14a rewrote `docs/req-020/integration-results.json` each time, so its 10-minute `npm run gate` never hit
    the cache and was paid again at every one of 16 attempts. An implementing task's paths are the code under check: never ignored."""
    if kind not in ("test", "audit"):
        return ()
    return tuple(sorted({str(p) for p in expected_paths or () if isinstance(p, str) and REPORT_FILE.search(p)
                         and not any(c in p for c in "*?[")}))


def tree_id(repository: Path | None, snapshot_sha: str | None, ignore: tuple[str, ...] = ()) -> str | None:
    """The git tree of the snapshot commit (content-addressed: equal trees are equal files), or None. With `ignore`, the tree WITHOUT
    those paths (a temporary index: nothing in the repository changes but unreferenced objects)."""
    if repository is None or not snapshot_sha:
        return None
    try:
        done = subprocess.run(["git", "-C", str(repository), "rev-parse", "--verify", "--quiet", f"{snapshot_sha}^{{tree}}"],
                              capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    tree = done.stdout.strip()
    if done.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", tree):
        return None
    if not ignore:
        return tree
    import os
    import tempfile

    with tempfile.TemporaryDirectory(prefix="m6-tree-") as work:
        env = {**os.environ, "GIT_INDEX_FILE": str(Path(work) / "index")}
        try:
            for args in (["read-tree", tree], ["update-index", "--force-remove", "--", *ignore], ["write-tree"]):
                step = subprocess.run(["git", "-C", str(repository), *args], capture_output=True, text=True, timeout=60,
                                      check=False, env=env)
                if step.returncode:
                    return tree                                   # cannot tell: the whole tree is the safe key
        except (OSError, subprocess.SubprocessError):
            return tree
    pruned = step.stdout.strip()
    return pruned if re.fullmatch(r"[0-9a-f]{40,64}", pruned) else tree


def environment_fingerprint(policy: QualityPolicy) -> str:
    """Everything of the operator's policy that can change what a command prints or whether it passes. Environment values
    are hashed, never stored."""
    body = {"network": policy.network, "production": policy.allow_production_actions, "toolchain": policy.toolchain,
            "provision": policy.provision_dependencies,
            "environment": [[name, hashlib.sha256(value.encode()).hexdigest()] for name, value in policy.environment]}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:24]


def command_key(spec: CheckSpec) -> str:
    return hashlib.sha256(json.dumps([list(spec.argv), spec.cwd]).encode()).hexdigest()


def pass_key(tree: str, spec: CheckSpec, fingerprint: str) -> str:
    return hashlib.sha256(f"{tree}\0{command_key(spec)}\0{fingerprint}".encode()).hexdigest()


def is_expensive(spec: CheckSpec, last_ms: int | None, policy: QualityPolicy) -> bool:
    if last_ms is not None:
        return last_ms >= policy.expensive_check_seconds * 1000
    return looks_like_full_suite(spec.command)
