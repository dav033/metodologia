"""Run a model-authored oracle command on a captured commit, in the verifier's own sandbox (REQ-029 R12/R13: the red step).

A convergence plan is only compiled when its symptom oracle is FALSIFIED on captured source: the red command must fail on one of the
accepted sides, and fail the way a test fails (it ran and exited non-zero), not because the sandbox was missing, busy or timed out.
That is what `failure_kind: "symptom"` in the oracle's provenance means, and it is decided here from the sandbox's own outcome,
never from what the model says about its command.

The commit is exported with `git archive` into a private directory (no `.git`, like every verification) and the command goes through
`QualityPolicy` / `SandboxRunner`: the same compile rules (one argv, no shell syntax), the same isolation (no host home, no network
unless `verifier.network`), the same environment the owner configured for the project's verifier.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Any

TAIL = 1200


class OracleError(RuntimeError):
    """The command could not be run as a check at all (unsupported syntax, no sandbox, commit not exportable)."""


def policy_for(project: str):
    """The verifier policy the project's runs use (`verifier.*` settings and its environment file)."""
    import bt_config
    import bt_verifier_env
    from bt_scheduler_quality.policy import QualityPolicy

    configured = {key: bt_config.get(f"verifier.{key}", True) for key in ("network", "allow_production_actions")}
    megabytes = bt_config.get("verifier.max_workspace_mb", 2048)
    if isinstance(megabytes, int) and not isinstance(megabytes, bool) and megabytes >= 64:
        configured["max_workspace_bytes"] = megabytes << 20
    environment, secrets = bt_verifier_env.load(bt_verifier_env.path_for(bt_config.get("verifier.env_file", ""), project))
    return QualityPolicy(**{**{k: v for k, v in configured.items() if isinstance(v, (bool, int))},
                            **({"environment": environment, "secret_values": secrets} if environment else {})})


def run(repository: str | Path, commit: str, command: str, policy, *, timeout_seconds: int = 300) -> dict[str, Any]:
    """`{status: pass|fail|unknown, exit_code, kind: symptom|infrastructure, stdout, stderr}` of `command` on `commit`."""
    from bt_scheduler_quality.contracts import QualityError
    from bt_scheduler_quality.policy import CheckSpec, _parse_command
    from bt_scheduler_quality.runner import SandboxRunner

    with tempfile.TemporaryDirectory(prefix="bt-oracle-") as work:
        root = Path(work) / "tree"
        root.mkdir()
        archive = subprocess.run(["git", "-C", str(repository), "archive", "--format=tar", commit], capture_output=True, timeout=120,
                                 check=False)
        if archive.returncode:
            raise OracleError(f"git archive {commit[:12]}: {archive.stderr.decode('utf-8', 'replace')[:160]}")
        unpacked = subprocess.run(["tar", "-x", "-C", str(root)], input=archive.stdout, capture_output=True, timeout=120, check=False)
        if unpacked.returncode:
            raise OracleError(f"tar: {unpacked.stderr.decode('utf-8', 'replace')[:160]}")
        try:
            argv, cwd = _parse_command(command, root, policy.allow_production_actions)
        except QualityError as error:
            raise OracleError(f"{error.code}: {error}") from error
        spec = CheckSpec("ORACLE-1", "command", command, argv, cwd, "oracle")
        outcome = SandboxRunner(policy).run(spec, root, timeout_seconds=timeout_seconds)
    symptom = outcome.status in ("pass", "fail") and outcome.exit_code is not None
    return {"status": outcome.status, "exit_code": outcome.exit_code, "sandboxed": outcome.sandboxed,
            "kind": "symptom" if symptom else "infrastructure", "issue": outcome.issue_code,
            "stdout": outcome.stdout[-TAIL:].decode("utf-8", "replace"), "stderr": outcome.stderr[-TAIL:].decode("utf-8", "replace")}
