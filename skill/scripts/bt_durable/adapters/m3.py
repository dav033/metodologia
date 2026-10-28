"""Preparer, Reader and Capturer ports over the legacy executor's domain pieces (CONSERVAR in the M0 matrix).

What is reused unchanged: `GitWorkspaces` (one worktree per attempt, idempotent), the brief built from the frozen
plan task (`PlanBriefs`), `build_prompt`, the provider drivers behind `MethodologyDriver` (account gates, session
environment, argv) and `handoff.capture` (deterministic snapshot commit). What is gone: the M3 ledger, its loop and
the shim — the DBOS workflow is the state, and bt_supervisor runs the process.
"""
from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from pathlib import Path

from bt_contracts.execution import (
    AgentReport,
    AttemptRef,
    Prepared,
    ProcessRecord,
    Route,
    Snapshot,
)

from ..legacy import GitWorkspaces, Plan, TaskSpec, build_prompt, handoff
from ..legacy import m3 as _m3

m3 = _m3.model

from .files import atomic_write

DEFAULT_TIMEOUT = 2 * 3600
PATCH_MAX = 16 << 20
OUTPUT_READ_MAX = 8 << 20


def start_request(attempt: AttemptRef, task: TaskSpec, *, base_ref: str, timeout: int) -> m3.StartRequest:
    run = attempt.run
    return m3.StartRequest(idempotency_key=attempt.attempt_key, plan_id=run.plan_id, revision=run.revision,
                           task_id=attempt.task_id, attempt_id=attempt.attempt_key, token=attempt.number,
                           executor="bt_durable", repository=task.repository, project=run.project,
                           base_ref=base_ref or "HEAD", timeout_seconds=float(timeout),
                           acceptance_criteria=tuple(task.acceptance_criteria),
                           verification=tuple(task.verification))


class M3Attempts:
    """One object for the three attempt ports, sharing the workspace manager and the attempt directories."""

    def __init__(self, *, root: Path, repositories_for: Callable[[str], Mapping[str, Path] | Callable[[str], Path | None]],
                 plan_for: Callable[[AttemptRef], Plan], driver_for: Callable[[str], object],
                 briefs_for: Callable[[Plan], object] | None = None, prompt_rtk: bool = False):
        self.root = Path(root)
        self.repositories_for = repositories_for
        self.plan_for = plan_for
        self.driver_for = driver_for
        self.briefs_for = briefs_for
        self.prompt_rtk = prompt_rtk
        self._workspaces: dict[str, GitWorkspaces] = {}
        self._drivers: dict[str, object] = {}

    def workspaces(self, project: str) -> GitWorkspaces:
        if project not in self._workspaces:
            self._workspaces[project] = GitWorkspaces(self.root / "ws" / project, self.repositories_for(project))
        return self._workspaces[project]

    def driver(self, project: str):
        if project not in self._drivers:
            self._drivers[project] = self.driver_for(project)
        return self._drivers[project]

    def attempt_dir(self, attempt: AttemptRef) -> Path:
        path = self.root / "attempts" / attempt.attempt_key
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
        return path

    # ------------------------------------------------------------------------------------------------ Preparer
    def prepare(self, attempt: AttemptRef, task: TaskSpec, route: Route, *, base_ref: str, note: str,
                limits: dict) -> Prepared:
        timeout = int(limits.get("runtime_max_seconds") or DEFAULT_TIMEOUT)
        request = start_request(attempt, task, base_ref=base_ref, timeout=timeout)
        workspaces = self.workspaces(attempt.run.project)
        workspaces.check(request)
        ws = workspaces.allocate(request)
        adir = self.attempt_dir(attempt)
        brief = self._brief(attempt, request, note)
        prompt = build_prompt(brief, request, workdir=ws.path, branch=ws.branch,
                              report_path=str(adir / "report.json"), handoff_mode="snapshot", rtk=self.prompt_rtk)
        atomic_write(adir / "prompt.txt", prompt.encode("utf-8"), 0o600)
        atomic_write(adir / "workspace.json", json.dumps(ws.to_dict(), sort_keys=True).encode(), 0o600)
        launch = self.driver(attempt.run.project).prepare(_m3_route(route), prompt, ws, float(timeout))
        env = {k: v for k, v in os.environ.items() if k not in launch.env_remove}
        env.update(dict(launch.env_set))
        env_file = adir / "agent.env.json"
        atomic_write(env_file, _env_file(env), 0o600)            # secrets live only in this 0600 file
        stdin_path = None
        if launch.stdin is not None:
            stdin_path = adir / "stdin.txt"
            atomic_write(stdin_path, launch.stdin.encode("utf-8"), 0o600)
        return Prepared(worktree=Path(ws.path), branch=ws.branch, base_sha=ws.base_sha, repository=Path(ws.repo),
                        attempt_dir=adir, prompt_path=adir / "prompt.txt", argv=tuple(launch.argv),
                        env_file=env_file, stdin_path=stdin_path, timeout_seconds=timeout)

    def _brief(self, attempt: AttemptRef, request: m3.StartRequest, note: str) -> m3.Brief:
        plan = self.plan_for(attempt)
        if self.briefs_for is not None:
            brief = self.briefs_for(plan).brief(request)
        else:
            spec = next(t for t in plan.tasks if t.id == attempt.task_id)
            brief = m3.Brief(title=str(spec.meta.get("title", spec.id)), objective=str(spec.meta.get("objective", "")),
                             acceptance_criteria=tuple(spec.acceptance_criteria),
                             verification=tuple(f"{v.get('purpose') or v.get('type')}: {v.get('value', '')}"
                                                for v in spec.verification),
                             expected_paths=tuple(spec.expected_paths))
        if note:
            from dataclasses import replace
            brief = replace(brief, notes="\n\n".join(x for x in (brief.notes, note) if x))
        return brief

    # -------------------------------------------------------------------------------------------------- Reader
    def read(self, attempt: AttemptRef, route: Route, process: ProcessRecord) -> AgentReport:
        raw = _read_capped(process.log_path)
        timed_out = process.result == "timeout"
        cancelled = process.result in ("cancelled", "signal") and process.exit_code is None
        found = self.driver(attempt.run.project).classify(_m3_route(route), raw, process.exit_code, timed_out=timed_out, cancelled=cancelled)
        usage = dict(found.usage or {})
        total = usage.get("total_tokens")
        if total is None and isinstance(usage.get("input_tokens"), int):
            total = int(usage.get("input_tokens") or 0) + int(usage.get("output_tokens") or 0)
        return AgentReport(status=found.status, reset_epoch=found.reset_epoch, text=(found.text or "")[-4000:],
                           total_tokens=int(total) if isinstance(total, (int, float)) else None)

    # ------------------------------------------------------------------------------------------------ Capturer
    def capture(self, attempt: AttemptRef, prepared: Prepared, task: TaskSpec) -> Snapshot:
        ws = m3.Workspace(path=str(prepared.worktree), branch=prepared.branch, base_sha=prepared.base_sha,
                          repo=str(prepared.repository))
        # `when` is fixed per attempt so a re-run of this step writes the same commit (same tree, same parents)
        when = 1_700_000_000.0 + attempt.number
        manifest = handoff.capture(ws, prepared.attempt_dir, dirname=attempt.attempt_key, attempt_id=attempt.attempt_key,
                                   when=when, patch_max=PATCH_MAX, mode="snapshot",
                                   declared_paths=tuple(task.expected_paths))
        changed = tuple(line.split("\t", 1)[-1] for line in manifest.get("changed", ()) if isinstance(line, str))
        return Snapshot(snapshot_sha=manifest.get("snapshot_sha"), base_sha=prepared.base_sha, changed_paths=changed[:500],
                        manifest_path=prepared.attempt_dir / "handoff" / "manifest.json")


def _m3_route(route: Route) -> m3.Route:
    return m3.Route(provider=route.provider, model=route.model, profile=route.profile, effort=route.effort or "",
                    reference=route.reference or f"{route.provider}:{route.profile}:{route.model}")


def _env_file(env: Mapping[str, str]) -> bytes:
    """The agent environment as JSON (0600): the runtime turns it into the unit's own environment file."""
    return json.dumps({k: v for k, v in env.items() if isinstance(v, str)}, sort_keys=True).encode("utf-8")


def _read_capped(path: Path) -> str:
    try:
        with open(path, "rb") as stream:
            size = os.fstat(stream.fileno()).st_size
            if size > OUTPUT_READ_MAX:
                head = stream.read(OUTPUT_READ_MAX // 2)
                stream.seek(size - OUTPUT_READ_MAX // 2)
                return (head + b"\n...\n" + stream.read()).decode("utf-8", "replace")
            return stream.read().decode("utf-8", "replace")
    except OSError:
        return ""
