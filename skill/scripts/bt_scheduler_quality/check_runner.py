"""Bounded check execution, pass reuse and flaky-result handling for M6."""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Callable
from pathlib import Path

from . import reuse
from .contracts import VerifyRequest
from .policy import CheckSpec, QualityPolicy
from .runner import CommandOutcome, SandboxRunner
from .sandbox_mounts import attempt_mounts
from .store import QualityStore


class CheckExecutor:
    def __init__(self, policy: QualityPolicy, store: QualityStore, runner: SandboxRunner):
        self.policy, self.store, self.runner = policy, store, runner

    def run(self, specs: tuple[CheckSpec, ...], snapshot_root: Path, started: float,
            worktree: Path | None = None, repository: Path | None = None,
            tree: str | None = None, tree_for: Callable[[CheckSpec], str | None] | None = None,
            order: VerifyRequest | None = None) -> tuple[dict[str, CommandOutcome], list[str]]:
        outcomes: dict[str, CommandOutcome] = {}
        issue_codes: list[str] = []
        mounts = attempt_mounts(self.policy, worktree, repository, snapshot_root)
        done: dict[tuple[tuple[str, ...], str], CommandOutcome] = {}
        fingerprint = reuse.bound_environment_fingerprint(
            self.policy, order.contract_identities if order else (),
            order.environment_fingerprint if order else None,
        )
        failed = False
        for spec in self._cheap_first(specs):
            if spec.kind == "manual":
                outcomes[spec.id] = _unknown("CHECK_MANUAL")
                continue
            remaining = self.policy.max_total_seconds - int(time.monotonic() - started)
            if remaining <= 0:
                outcomes[spec.id] = _unknown("CHECK_NOT_RUN")
                issue_codes.append("CHECK_NOT_RUN")
                continue
            same = (spec.argv, spec.cwd)
            outcome = done.get(same)
            if outcome is None:
                if failed and self.policy.defer_expensive and self._is_expensive(spec):
                    outcome = dataclasses.replace(_unknown("CHECK_DEFERRED"), stderr=(
                        b"[M6] not run: a cheaper check of this task failed first. Fix that one and this check runs "
                        b"again with the next attempt.\n"))
                    issue_codes.append("CHECK_DEFERRED")
                else:
                    outcome = self._run_or_reuse(spec, snapshot_root, remaining, mounts, started,
                                                 tree_for(spec) if tree_for else tree, fingerprint)
                done[same] = outcome
            outcomes[spec.id] = outcome
            failed = failed or outcome.status == "fail"
            if outcome.issue_code and outcome.issue_code != "CHECK_DEFERRED":
                issue_codes.append(outcome.issue_code)
        return _complete_outcomes(specs, outcomes, issue_codes)

    def _is_expensive(self, spec: CheckSpec) -> bool:
        return reuse.is_expensive(spec, self.store.last_check_ms(reuse.command_key(spec)), self.policy)

    def _cheap_first(self, specs: tuple[CheckSpec, ...]) -> list[CheckSpec]:
        if not self.policy.defer_expensive:
            return list(specs)
        costly = {spec.id for spec in specs if spec.kind != "manual" and self._is_expensive(spec)}
        return [spec for spec in specs if spec.id not in costly] + [spec for spec in specs if spec.id in costly]

    def _run_or_reuse(self, spec, snapshot_root, remaining, mounts, started, tree, fingerprint) -> CommandOutcome:
        key = reuse.pass_key(tree, spec, fingerprint) if tree else None
        if key:
            hit = self.store.cached_pass(key, self.policy.cache_seconds, time.time())
            if hit is not None:
                note = (f"[M6] not run again: this exact tree already passed this check {int(time.time() - hit['created_at'])} "
                        "seconds ago (same command, same environment); its recorded output follows\n").encode()
                return CommandOutcome("pass", hit["exit_code"], 0, hit["stdout"], note + hit["stderr"], None, True)
        outcome = self.runner.run(spec, snapshot_root, timeout_seconds=min(self.policy.max_command_seconds, remaining),
                                  mounts=mounts)
        if key and outcome.status == "fail":
            self.store.record_check_outcome(key, "fail", time.time())
        outcome = self._rerun_if_flaky(spec, snapshot_root, outcome, remaining, mounts, started)
        if key and outcome.status == "pass":
            follows_failure = self.store.record_check_outcome(key, "pass", time.time())
            if follows_failure and outcome.issue_code != "FLAKY_SUSPECTED":
                note = b"[M6] this evidence key failed on an earlier verification and passed now; result is flaky, not a clean pass\n"
                outcome = dataclasses.replace(outcome, stderr=note + outcome.stderr, issue_code="FLAKY_SUSPECTED")
        elif key and outcome.status == "fail":
            self.store.record_check_outcome(key, "fail", time.time())
        if outcome.status in ("pass", "fail") and outcome.sandboxed:
            self.store.record_check_ms(reuse.command_key(spec), outcome.duration_ms, time.time())
        if key and outcome.status == "pass" and outcome.sandboxed and not outcome.output_truncated \
                and outcome.issue_code != "FLAKY_SUSPECTED":
            self.store.remember_pass(key, outcome.exit_code, outcome.duration_ms, outcome.stdout, outcome.stderr, time.time())
        return outcome

    def _rerun_if_flaky(self, spec, snapshot_root, outcome, remaining, mounts, started):
        for _ in range(self.policy.rerun_failed_checks):
            if outcome.status != "fail":
                break
            remaining = self.policy.max_total_seconds - int(time.monotonic() - started)
            if remaining <= 0:
                break
            again = self.runner.run(spec, snapshot_root, timeout_seconds=min(self.policy.max_command_seconds, remaining),
                                    mounts=mounts)
            if again.status == "pass":
                note = (f"[M6] this check failed once (exit {outcome.exit_code}) and passed when run again; "
                        "flaky under load, not a defect of the code\n").encode()
                return dataclasses.replace(again, stderr=note + again.stderr, issue_code="FLAKY_SUSPECTED")
            outcome = again
        return outcome


def _unknown(code: str) -> CommandOutcome:
    return CommandOutcome("unknown", None, 0, b"", b"", code, False)


def _complete_outcomes(specs, outcomes, issue_codes):
    if len(outcomes) != len(specs):
        for spec in specs:
            outcomes.setdefault(spec.id, _unknown("CHECK_NOT_RUN"))
            if outcomes[spec.id].issue_code == "CHECK_NOT_RUN":
                issue_codes.append("CHECK_NOT_RUN")
    return outcomes, issue_codes
