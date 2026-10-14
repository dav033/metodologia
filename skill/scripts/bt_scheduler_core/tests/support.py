"""Shared test helpers: build approved plans and a harness around the core with fake ports and a manual clock."""
from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

import bt_scheduler_core as sc
from bt_scheduler_core.simulators import ManualClock


def plan_text(tasks: list[dict], plan_id: str = "REQ-T", revision: int = 1, **extra) -> str:
    return json.dumps({"schema_version": "1.0.0", "plan_id": plan_id, "revision": revision, "tasks": tasks, **extra})


def task(tid: str, after=(), repo: str = "", paths=(), resources=(), milestone: str = "M1", **meta) -> dict:
    out = {"id": tid, "milestone_id": milestone, "after": list(after), "shared_resources": list(resources),
           "expected_paths": list(paths), "acceptance_criteria": [f"{tid} works"],
           "verification": [{"type": "command", "value": "true"}], **meta}
    if repo:
        out["repository"] = repo
    return out


def indep(tid: str, after=(), **kw) -> dict:
    """A task with its own repository and paths: known surface, no conflict with anything else."""
    return task(tid, after, repo=f"repo-{tid}", paths=[f"{tid}/**"], **kw)


def approved(text: str) -> tuple[sc.Plan, str]:
    digest = hashlib.sha256(text.encode()).hexdigest()
    return sc.load_plan(text, approved_sha256=digest), digest


class Harness:
    """Core + fakes + manual clock over any repository. `crash()` drops the core and returns a fresh one on the same
    repository, the way a restarted process would find it."""

    def __init__(self, tasks: list[dict], *, repository=None, parallel: int = 3, max_attempts: int = 1,
                 recovery=None, config: sc.Config | None = None, plan_id: str = "REQ-T", revision: int = 1,
                 executor=None, verifier=None, clock=None):
        self.text = plan_text(tasks, plan_id, revision)
        self.plan, self.sha = approved(self.text)
        self.repo = repository if repository is not None else sc.InMemoryRepository()
        self.executor = executor or sc.FakeExecutor()
        self.verifier = verifier or sc.FakeVerifier()
        self.clock = clock or ManualClock()
        self.recovery = recovery
        self.config = config or sc.Config(max_parallel_tasks=parallel, max_attempts=max_attempts)
        self.core = self.build()
        self.core.start()
        self.n = 0

    def build(self) -> sc.SchedulerCore:
        return sc.SchedulerCore(self.plan, self.repo, config=self.config, clock=self.clock,
                                ports=sc.Ports(execution=self.executor, verification=self.verifier, recovery=self.recovery))

    def crash(self) -> sc.SchedulerCore:
        self.core = self.build()
        self.core.start()
        return self.core

    # -- helpers
    def state(self, tid: str) -> str:
        return self.core.snapshot().tasks[tid]["state"]

    def states(self) -> dict[str, str]:
        return {k: v["state"] for k, v in self.core.snapshot().tasks.items()}

    def attempt(self, tid: str) -> str:
        return self.core.snapshot().tasks[tid]["attempt"]

    def token(self, attempt_id: str) -> int:
        return self.core.read(lambda c: c.state.attempts[attempt_id].token)

    def ev(self, tid: str, kind: str, attempt: str | None = None, *, event_id: str | None = None, token="auto", **payload):
        attempt = attempt or self.attempt(tid)
        self.n += 1
        return sc.Event(event_id or f"ev-{self.n}", self.plan.plan_id, self.plan.revision, tid, attempt, "executor-x",
                        kind, "", payload, self.token(attempt) if token == "auto" else token)

    def send(self, tid: str, kind: str, attempt: str | None = None, **kw) -> sc.IngestResult:
        return self.core.ingest(self.ev(tid, kind, attempt, **kw))

    def verdict(self, tid: str, accepted: bool = True, attempt: str | None = None, *, verifier: str = "validator",
                evidence: str = "checks passed", verdict_id: str | None = None) -> sc.IngestResult:
        attempt = attempt or self.attempt(tid)
        self.n += 1
        return self.core.submit_verdict(sc.Verdict(verdict_id or f"vd-{self.n}", self.plan.plan_id, self.plan.revision, tid,
                                                   attempt, accepted, verifier, evidence, self.token(attempt)))

    def finish_and_accept(self, tid: str) -> None:
        self.send(tid, "execution_finished")
        self.core.step()
        self.verdict(tid)
        self.core.step()

    def audit_kinds(self) -> list[str]:
        return [e.kind for e in self.core.audit_log()]


def sqlite_path() -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory(prefix="sched-core-")
    return tmp, Path(tmp.name) / "run.db"
