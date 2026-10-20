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


def _left_no_work(attempt) -> bool:
    """An attempt that produced nothing to continue from: cancelled (by the owner or a pause) or a start the executor
    refused. A retry looks past it to the last attempt that did."""
    failure = str(getattr(attempt, "failure", ""))
    return (attempt.state == "cancelled" and not _sent_back(attempt)) or \
        (attempt.state == "failed" and failure.startswith("start rejected"))


def _earlier_attempt(ctx, rec):
    """The attempt a retry of the current one builds on: the newest earlier attempt that left work behind."""
    for aid in reversed(rec.attempts[:-1]):
        attempt = ctx.state.attempts[aid]
        if not _left_no_work(attempt):
            return attempt
    return None

class RetryContinuation:
    def __init__(self, scheduler, executor, repo_of, fallback, *, default_repository="", snapshot_of=None, run_dir=None):
        self.scheduler, self.executor, self.repo_of = scheduler, executor, repo_of
        self.fallback, self.default_repository = fallback, default_repository
        self.snapshot_of = snapshot_of          # attempt id -> snapshot sha, also for attempts of earlier plan revisions
        self.run_dir = Path(run_dir) if run_dir else None

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
            current = ctx.state.attempts[rec.attempts[-1]]
            old = _earlier_attempt(ctx, rec)
            if old is None:
                return None            # nothing earlier left work behind: this attempt starts fresh
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
            old = _earlier_attempt(ctx, rec) if len(rec.attempts) >= 2 else None
            return old is not None and _sent_back(old)
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

    def _previous_base(self, task_id):
        """The base commit the previous attempt of this task started from (from the executor ledger), or None."""
        prior = self._previous(task_id)
        row = self.executor.ledger.get(prior["attempt_id"]) if prior else None
        return (row or {}).get("base_sha")

    # ---------------------------------------------------------------------------------------- repository helpers
    def _repo(self, task_id):
        try:
            role = getattr(self.scheduler.plan.task(task_id), "repository", "") or self.default_repository
            path = self.repo_of(role)
        except (AttributeError, KeyError):
            return None
        return Path(path) if path else None

    def _git_ok(self, repo, *args) -> bool:
        try:
            return subprocess.run(["git", *args], cwd=repo, env={k: v for k, v in os.environ.items()
                                                                  if not k.startswith("GIT_")},
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10,
                                  check=False).returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def _commit_exists(self, task_id, sha) -> bool:
        repo = self._repo(task_id)
        return bool(repo and isinstance(sha, str) and SHA.fullmatch(sha)
                    and self._git_ok(repo, "cat-file", "-e", f"{sha}^{{commit}}"))

    def _same_base(self, task_id, previous_base) -> bool:
        """The previous result's base is still the base this task would start from today. A task with no prerequisites
        starts from the repository head, which only moves forward: the old base is then still part of it."""
        current = self.fallback(task_id) if callable(self.fallback) else self.fallback
        if current == previous_base:
            return True
        if not previous_base or SHA.fullmatch(str(current)):
            return False                                # an integration commit or a pin: only an exact match is safe
        repo = self._repo(task_id)
        return bool(repo and self._git_ok(repo, "merge-base", "--is-ancestor", previous_base, str(current)))

    def _earlier_revision_result(self, task_id):
        """For a task with no prerequisites: the newest result an audit sent back that belongs to an earlier plan
        revision (a rebase starts a new executor root, so the usual lookup cannot see it), as a snapshot sha."""
        try:
            if self.snapshot_of is None or self.scheduler.plan.task(task_id).after:
                return None
        except (AttributeError, KeyError):
            return None

        def read(ctx):
            rec = ctx.state.tasks[task_id]
            prefix = f"{ctx.state.plan_id}:r{ctx.state.revision}:"
            return [a for a in reversed(rec.attempts[:-1])
                    if not ctx.state.attempts[a].key.startswith(prefix) and ctx.state.attempts[a].state == "accepted"]
        for attempt in self.scheduler.read(read)[:1]:
            sha = self.snapshot_of(attempt)
            if self._commit_exists(task_id, sha):
                return sha
        return None

    def _directed(self, task_id):
        """The snapshot the owner told this task's next attempt to continue from (`scheduler-op REQ continue-from`)."""
        if self.run_dir is None or self.snapshot_of is None:
            return None
        try:
            import json
            entry = json.loads((self.run_dir / "RUN.continue.json").read_text(encoding="utf-8")).get(task_id)
            started = self.scheduler.read(lambda ctx: len(ctx.state.tasks[task_id].attempts))
            if not isinstance(entry, dict) or entry.get("attempts") != started - 1:
                return None                              # for the next start only: it applies to nothing else
            sha = self.snapshot_of(entry["attempt"])
            return sha if self._commit_exists(task_id, sha) else None
        except (OSError, ValueError, KeyError, TypeError):
            return None

    def _continue_from(self, task_id):
        """The snapshot a retry builds on. A failed or rejected attempt is always continued. Work an audit sent back is
        continued only when its base is still the one the redone prerequisites give today: otherwise it would diverge
        from them and conflict when the integrator combines the chain, so the redo starts on the new base and the old
        result stays available as a reference (see `notes`). The owner can direct the choice."""
        directed = self._directed(task_id)
        if directed is not None:
            return directed
        snapshot = self._handoff(task_id)
        if snapshot is None:
            return self._earlier_revision_result(task_id)
        if not self._reworked(task_id):
            return snapshot
        return snapshot if self._same_base(task_id, self._previous_base(task_id)) else None

    def base_ref(self, task_id):
        snapshot = self._continue_from(task_id)
        if snapshot is not None:
            return snapshot
        return self.fallback(task_id) if callable(self.fallback) else self.fallback

    def notes(self, request):
        snapshot = self._continue_from(request.task_id)
        if snapshot is None:
            try:
                earlier = self._handoff(request.task_id) if self._reworked(request.task_id) else None
            except integration.IntegrationError:
                earlier = None      # a reference only: a missing one must not stop the redo
            if earlier is None:
                return ""
            return ("An independent audit sent this task's earlier work back, and the prerequisites it builds on were "
                    f"redone since, so you start from their new result. The earlier result is kept read-only as snapshot "
                    f"{earlier} (inspect it with `git show {earlier}`): reuse what is still correct, do not copy it blindly.")
        if request.base_ref != snapshot:
            raise integration.IntegrationError("PREDECESSOR_HANDOFF_MISSING", "retry base does not match its snapshot")
        directed = self._directed(request.task_id) == snapshot
        if directed or self._handoff(request.task_id) is None:      # the owner's choice, or a result of an earlier revision
            return (f"Continue the preserved files of this task's accepted result, snapshot {snapshot}"
                    f"{' (chosen by the owner)' if directed else ''}. The tasks that come after it were built on that "
                    "result, so keep everything it contains, including files outside this task's own paths, and add only "
                    "the changes the audit notes above ask for. Recheck the complete frozen acceptance and verification "
                    "instructions. No private conversation or agent reasoning is transferred.")
        if self._reworked(request.task_id):
            return (f"Continue the preserved files from this task's previous attempt, snapshot {snapshot}. "
                    "That work was accepted or finished, and an independent audit then sent it back: fix what the audit "
                    "notes above say is wrong, keep what is correct, and recheck the complete frozen acceptance and "
                    "verification instructions. No private conversation or agent reasoning is transferred.")
        return (f"Continue the preserved files from this task's previous attempt, snapshot {snapshot}. "
                "The previous attempt failed or was rejected by independent verification. Its output is unaccepted. "
                "Recheck the complete frozen acceptance and verification instructions; preserve useful partial changes. "
                "No private conversation or agent reasoning is transferred.")
