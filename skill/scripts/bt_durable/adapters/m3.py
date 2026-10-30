"""Preparer, Reader and Capturer ports over the legacy executor's domain pieces (CONSERVAR in the M0 matrix).

What is reused unchanged: `GitWorkspaces` (one worktree per attempt, idempotent), the brief built from the frozen
plan task (`PlanBriefs`), `build_prompt`, the provider drivers behind `MethodologyDriver` (account gates, session
environment, argv) and `handoff.capture` (deterministic snapshot commit). What is gone: the M3 ledger, its loop and
the shim — the DBOS workflow is the state, and bt_supervisor runs the process.
"""
from __future__ import annotations

import json
import os
import re
import sys
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

from . import size_guard
from .files import atomic_write

DEFAULT_TIMEOUT = 2 * 3600
# the engine's own configuration (the DBOS database URL carries its password) never reaches an agent
ENGINE_ONLY_PREFIXES = ("BT_DURABLE_", "DBOS_")
# the engine's own interpreter, which `uv run` (the unit's ExecStart) puts in front of everything: VIRTUAL_ENV and PATH
# name the live checkout's .venv. An agent that inherited them ran `python`, `pip install` or `uv pip install` in the
# engine's environment: a product task could change the interpreter of the engine that runs it.
ENGINE_INTERPRETER_ENV = frozenset({"VIRTUAL_ENV", "VIRTUAL_ENV_PROMPT", "UV_RUN_RECURSION_DEPTH"})
ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")       # bt_supervisor.model.ENV_NAME_PATTERN
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

    telemetry = None            # set by the wiring: where the capture-time file guard reports (adapters/size_guard)

    def __init__(self, *, root: Path, repositories_for: Callable[[str], Mapping[str, Path] | Callable[[str], Path | None]],
                 plan_for: Callable[[AttemptRef], Plan], driver_for: Callable[[str], object],
                 briefs_for: Callable[[AttemptRef, Plan, str], object] | None = None, prompt_rtk: bool = False):
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
        test_env = agent_test_env(attempt.run.project)
        brief = self._brief(attempt, request, "\n\n".join(x for x in (_continuation(ws), _test_env_note(test_env), note) if x))
        prompt = build_prompt(brief, request, workdir=ws.path, branch=ws.branch,
                              report_path=str(adir / "report.json"), handoff_mode="snapshot", rtk=self.prompt_rtk)
        atomic_write(adir / "prompt.txt", prompt.encode("utf-8"), 0o600)
        atomic_write(adir / "workspace.json", json.dumps(ws.to_dict(), sort_keys=True).encode(), 0o600)
        launch = self.driver(attempt.run.project).prepare(_m3_route(route), prompt, ws, float(timeout))
        # names a process environment may hold but an agent's cannot (an exported bash function: BASH_FUNC_x%%)
        env = {k: v for k, v in inherited_env().items()
               if k not in launch.env_remove and not k.startswith(ENGINE_ONLY_PREFIXES) and ENV_NAME.match(k)}
        env.update(test_env)
        env.update(dict(launch.env_set))
        env["BITACORA_ATTEMPT"] = attempt.attempt_key      # a task attempt: the bitácora hooks leave it its task (D-168)
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
        if self.briefs_for is not None:                  # the legacy owner's sections (adapters/briefs.py)
            brief = self.briefs_for(attempt, plan, note).brief(request)
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
        total = budget_tokens(dict(found.usage or {}), route.provider)
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
        oversized = size_guard.check(attempt, prepared.repository, prepared.base_sha, manifest.get("snapshot_sha"),
                                     self.telemetry)
        return Snapshot(snapshot_sha=manifest.get("snapshot_sha"), base_sha=prepared.base_sha, changed_paths=changed[:500],
                        manifest_path=prepared.attempt_dir / "handoff" / "manifest.json", oversized=oversized)


def inherited_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """The engine's environment without its own interpreter (`ENGINE_INTERPRETER_ENV`, and the virtual environment's
    `bin` directories removed from PATH): what an agent may inherit before its driver and the owner add theirs."""
    environ = dict(os.environ if environ is None else environ)
    venvs = {environ.get("VIRTUAL_ENV", "")}
    if sys.prefix != sys.base_prefix:                    # this process runs inside a virtual environment
        venvs.add(sys.prefix)
    own = {str(Path(v) / "bin") for v in venvs if v}
    out = {k: v for k, v in environ.items() if k not in ENGINE_INTERPRETER_ENV}
    if "PATH" in out:
        out["PATH"] = os.pathsep.join(p for p in out["PATH"].split(os.pathsep) if p and p.rstrip("/") not in own)
    return out


def _continuation(ws) -> str:
    """What the legacy retry continuation tells an agent whose tree is an earlier attempt's snapshot (`m3 snapshot
    <attempt>` commits, written by `handoff.capture`): its files are kept and must be checked, not redone."""
    import subprocess
    done = subprocess.run(["git", "-C", str(ws.repo), "log", "-1", "--format=%s", ws.base_sha], capture_output=True,
                          text=True, check=False)
    subject = done.stdout.strip() if done.returncode == 0 else ""
    if not subject.startswith("m3 snapshot "):
        return ""
    return (f"Continue the preserved files of this task's earlier attempt {subject.split()[-1]} (snapshot "
            f"{ws.base_sha[:12]}): your tree starts from its result. Fix what the notes say failed, keep what is "
            "correct, and recheck the complete frozen acceptance and verification instructions. No private "
            "conversation or agent reasoning is transferred.")


def _count(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None


def budget_tokens(usage: Mapping[str, object], provider: str = "") -> int | None:
    """Tokens an attempt counts against its task's budget: fresh input and output in full, cache reads a tenth, as
    providers bill them. The driver hands over its split (`input_tokens`, `output_tokens`, `cache_read_tokens`) plus a
    `total_tokens` that sums input and output; Codex's input INCLUDES its cache reads (pictures REQ-021 T6.3: 23.86 M
    input, 23.54 M cached, 80 k output, so one session used the task's whole 8 M budget and stopped for a person; T4.2
    and T5.2 too), Claude's leaves them out. Only the total when there is no split."""
    fresh, output = _count(usage.get("input_tokens")), _count(usage.get("output_tokens"))
    cached = _count(usage.get("cache_read_tokens")) or _count(usage.get("cached_input_tokens")) or 0
    if fresh is None:
        total = usage.get("total_tokens")
        return int(total) if isinstance(total, (int, float)) and not isinstance(total, bool) else None
    if provider == "codex":
        cached = min(cached, fresh)
        fresh -= cached
    return fresh + cached // 10 + (output or 0)


def agent_test_env(project: str) -> dict[str, str]:
    """The owner's test variables for this project's agents (`execution.agent_env_file`); {} when unset or missing."""
    import bt_config
    import bt_verifier_env
    environment, _ = bt_verifier_env.load(bt_verifier_env.path_for(bt_config.get("execution.agent_env_file", ""), project))
    return dict(environment)


def _test_env_note(env: Mapping[str, str]) -> str:
    if not env:
        return ""
    return ("Test environment: " + ", ".join(sorted(env)) + (" is" if len(env) == 1 else " are") + " set in your "
            "environment by the owner for testing (a disposable database, never production). Run the verification "
            "commands that need them yourself before you finish; never print, copy or commit their values.")


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
