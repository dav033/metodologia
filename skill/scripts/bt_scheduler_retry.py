"""Verified same-task snapshot continuation at the methodology execution boundary.

Reads M1/M3 public views and git objects. It never changes task state, signals a process, edits a worktree or integrates
failed work into another task. The next authorised StartOrder is the sole trigger for reusing a snapshot.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path

import bt_scheduler_integrator as integration

SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
TERMINAL = frozenset({"failed", "finished", "cancelled", "rejected"})


def _process_may_live(identity: object) -> bool:
    if not isinstance(identity, Mapping) or identity.get("pid") is None:
        return True  # an unreadable shim record cannot prove that its writer stopped
    pid = identity.get("pid")
    ticks = identity.get("start_ticks")
    boot = identity.get("host_boot_id")
    if type(pid) is not int or pid <= 0 or type(ticks) is not int or not isinstance(boot, str):
        return True
    try:
        if Path("/proc/sys/kernel/random/boot_id").read_text().strip() != boot:
            return False
        raw = Path(f"/proc/{pid}/stat").read_text()
        fields = raw[raw.rindex(")") + 2:].split()
        return int(fields[19]) == ticks and fields[0] != "Z"
    except FileNotFoundError:
        return False
    except (OSError, ValueError, IndexError):
        return True



def _sent_back(attempt) -> bool:
    """An attempt whose work an audit sent back: accepted before the rework, or cancelled by it while verifying."""
    return attempt.state == "accepted" or (attempt.state == "cancelled"
                                            and str(getattr(attempt, "failure", "")).startswith("superseded_by_rework"))


def _continuable(attempt) -> bool:
    return attempt.state in {"failed", "rejected"} or _sent_back(attempt)

class RetryContinuation:
    def __init__(self, scheduler, executor, repo_of, fallback, *, default_repository=""):
        self.scheduler, self.executor, self.repo_of = scheduler, executor, repo_of
        self.fallback, self.default_repository = fallback, default_repository

    def _snapshot_verified(self, row, sha):
        if not isinstance(sha, str) or SHA.fullmatch(sha) is None:
            return False
        request = row.get("request", {})
        workspace = row.get("workspace") or {}
        repo = self.repo_of(request.get("repository") or self.default_repository)
        if repo is None or Path(workspace.get("repo", "")).resolve() != Path(repo).resolve():
            return False
        env = {k: v for k, v in os.environ.items() if k not in integration.LOCATION_VARS}
        try:
            done = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", "cat-file", "-e", f"{sha}^{{commit}}"],
                                  cwd=repo, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  timeout=5, check=False)
        except (OSError, subprocess.SubprocessError):
            return False
        return done.returncode == 0

    def describe(self, attempt_id):
        row = self.executor.ledger.get(attempt_id)
        if row is None:
            return None
        description = self.executor.describe(attempt_id) or {}
        request = row.get("request") or {}
        outcome = row.get("outcome") or {}
        handoff = row.get("handoff") or {}
        stream = description.get("stream") or {}
        live = _process_may_live(stream.get("process_identity"))
        return {"schema_version": "m5.executor-facts/1",
                "request": {key: request.get(key) for key in
                            ("plan_id", "plan_sha256", "revision", "task_id", "attempt_id", "token")},
                "state": "running" if live else row.get("state", "unknown"),
                "outcome": {"cause": outcome.get("cause", "unknown"), "reset_epoch": outcome.get("reset_epoch")},
                "handoff": {"status": handoff.get("status"), "snapshot_sha": handoff.get("snapshot_sha")},
                "snapshot_verified": row.get("state") in TERMINAL and not live
                    and handoff.get("status") == "captured" and self._snapshot_verified(row, handoff.get("snapshot_sha")),
                "cancel_requested": row.get("cancel_requested", False), "updated": row.get("updated")}

    def _previous(self, task_id):
        def read(ctx):
            rec = ctx.state.tasks[task_id]
            if len(rec.attempts) < 2:
                return None
            current, old = (ctx.state.attempts[rec.attempts[i]] for i in (-1, -2))
            if not old.key.startswith(f"{ctx.state.plan_id}:r{ctx.state.revision}:"):
                return None  # an attempt of an earlier plan revision (the run was rebased): this one starts fresh
            if (rec.state != "active" or current.state not in {"reserved", "dispatched", "running"}
                    or not _continuable(old) or ctx.state.cancel_requested):
                raise integration.IntegrationError("PREDECESSOR_HANDOFF_MISSING", "retry is not authorised")
            return {"plan_id": ctx.state.plan_id, "plan_sha256": ctx.state.plan_sha256,
                    "revision": ctx.state.revision, "task_id": task_id,
                    "attempt_id": old.id, "token": old.token}
        return self.scheduler.read(read)

    def _reworked(self, task_id) -> bool:
        """True when the previous attempt's work was sent back by an audit (accepted earlier, or superseded while it
        waited for its verdict) instead of failing: the redo continues from it with the audit's findings."""
        def read(ctx):
            rec = ctx.state.tasks[task_id]
            return len(rec.attempts) >= 2 and _sent_back(ctx.state.attempts[rec.attempts[-2]])
        return self.scheduler.read(read)

    def _handoff(self, task_id):
        prior = self._previous(task_id)
        if prior is None:
            return None
        facts = self.describe(prior["attempt_id"])
        if facts is None:
            return None  # the executor never accepted that start (it was rejected): there is no work to continue
        if (not facts or facts["request"] != prior or facts["state"] not in {"failed", "finished"}
                or facts["cancel_requested"] or not facts["snapshot_verified"]):
            raise integration.IntegrationError("PREDECESSOR_HANDOFF_MISSING", "retry snapshot is missing or unsettled")
        return facts["handoff"]["snapshot_sha"]

    def base_ref(self, task_id):
        snapshot = self._handoff(task_id)
        if snapshot is not None:
            return snapshot
        return self.fallback(task_id) if callable(self.fallback) else self.fallback

    def notes(self, request):
        snapshot = self._handoff(request.task_id)
        if snapshot is None:
            return ""
        if request.base_ref != snapshot:
            raise integration.IntegrationError("PREDECESSOR_HANDOFF_MISSING", "retry base does not match its snapshot")
        if self._reworked(request.task_id):
            return (f"Continue the preserved files from this task's previous attempt, snapshot {snapshot}. "
                    "That work was accepted or finished, and an independent audit then sent it back: fix what the audit "
                    "notes above say is wrong, keep what is correct, and recheck the complete frozen acceptance and "
                    "verification instructions. No private conversation or agent reasoning is transferred.")
        return (f"Continue the preserved files from this task's previous attempt, snapshot {snapshot}. "
                "The previous attempt failed or was rejected by independent verification. Its output is unaccepted. "
                "Recheck the complete frozen acceptance and verification instructions; preserve useful partial changes. "
                "No private conversation or agent reasoning is transferred.")
