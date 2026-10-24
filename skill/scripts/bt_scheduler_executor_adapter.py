"""The only place where the methodology touches the agent executor (`bt_scheduler_executor`, M3).

Dependency direction: methodology -> this adapter -> bt_scheduler_executor. The module knows no provider, profile,
catalogue, bitácora path or scheduler type; everything it needs arrives through the five ports implemented here, and
everything it answers is translated back into the scheduler core's own classes (reached through `bt_scheduler_adapter`,
the only file that imports the core). Nothing in the existing commands changes: the executor is opt-in, by calling
`wire()`.

What lives here, and what does not:
- `RouteResolver`: an M2 route reference -> provider/model/profile/effort, validated against the one catalogue
  (`bt_agents`) and the profile policy (`bt_profiles`). M2 does not exist yet: `route:<id>` is delegated to a lookup the
  caller supplies, and `direct:<provider>/<model>[@profile][#effort]` is an explicit, operator-written reference. Anything
  else (including the core's FIFO label `local`) is unresolvable: **M3 never picks a model**.
- `MethodologyDriver`: launch (argv, account environment, gates) and output reading through `bt_driver`/`bt_profiles`.
- `PlanBriefs`: the frozen plan's task as the agent's brief.
- `workspaces`: `GitWorkspaces` over the project's registered repositories (`bt_workspace`).
- `CoreExecutionPort` / `CoreEventSink`: the core's `ExecutionPort` and the way technical events enter it.
- `PinnedRoute`: an `AssignmentPort` that hands every ready task the operator's pinned reference, a stand-in for M2.
"""
from __future__ import annotations

import contextlib
import json
import math
import os
import re
import shutil
import signal
import sqlite3
import time
from collections.abc import Callable, Mapping
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import bt_agents
from bt_design_scope import designer_scope_refusal  # noqa: F401  (public through this adapter)
import bt_agy
import bt_core
import bt_driver
import bt_profiles
import bt_scheduler_adapter as sched
from bt_scheduler_recovery_adapter import start_rejection_detail
import bt_scheduler_executor as m3
from bt_scheduler_executor import gitutil  # noqa: F401 - re-exported: the only door to the executor module
from bt_scheduler_executor.workspace import dirname_of  # noqa: F401 - re-exported, same reason
import bt_scheduler_integrator as integrator
import bt_workspace
from bt_scheduler_m4_wiring import (  # noqa: F401 - exported to the composition module
    M3StreamCandidates,
    MonitorRuntime,
    create_monitor_runtime,
    seed_terminal_streams,
)
from bt_scheduler_m4_wiring import drain_stream as drain_m3_stream
from bt_scheduler_stream_adapter import M3StreamAdapter

core = sched.core                      # the core's classes, through the one adapter that imports it
SOURCE = "executor"
PROVIDER_ALIASES = {"gemini": "antigravity", "agy": "antigravity"}   # Gemini = Antigravity `agy` (D-004)
BINARIES = {"claude": "claude", "codex": "codex", "antigravity": bt_agy.BIN}
DIRECT = re.compile(r"^direct:(?P<provider>[a-z]+)/(?P<model>[A-Za-z0-9._:-]+)(?:@(?P<profile>[A-Za-z0-9._-]+))?"
                    r"(?:#(?P<effort>[a-z]+))?$")
_PLAN_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
# efforts each provider accepts: Claude takes the catalogue ladder; Codex has no "max"; an Antigravity effort is part of the model id
EFFORTS_OF = {"claude": tuple(bt_agents.EFFORTS), "codex": tuple(e for e in bt_agents.EFFORTS if e != "max"), "antigravity": ()}
# Parent-session state is never handed down to an agent (the profile layer already does this for Antigravity), and a route
# that names a profile runs with THAT account: credentials the executor itself happened to inherit do not follow it.
SESSION_PREFIXES = ("CLAUDE_CODE_", "CODEX_", "ANTIGRAVITY_")
SESSION_KEEP = frozenset({"CODEX_HOME"})
SESSION_VARS = frozenset({"CLAUDECODE"})
CREDENTIAL_VARS = frozenset({"ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY", "GEMINI_API_KEY",
                             "GOOGLE_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"})
M2_PREFIXES = ("m2:v1:", "route:")      # M2's executor references (`m2:v1:<decision>:<route>`) and the generic `route:<id>` form
M2_LOOKUP = Callable[..., Mapping[str, Any] | None]    # (reference, request) -> route fields | None
STATE_OF = {"queued": "running", "preparing": "running", "running": "running", "settling": "running",
            "finished": "finished", "failed": "failed", "cancelled": "cancelled", "not_found": "not_found"}


def _policy(call: Callable[[], Any]) -> Any:
    """Profile policy raises ProfileError (a SystemExit): a refusal of THIS order, never an exit of the process."""
    try:
        return call()
    except SystemExit as refusal:
        raise m3.ExecutorError("POLICY_DENIED", str(refusal.code or refusal)[:300]) from None


def _max_turns() -> int:
    """Turns one Claude attempt may use (`scheduler.max_turns`)."""
    import bt_config

    value = bt_config.get("scheduler.max_turns", 120)
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else 120


def _quota_deadline_is_fresh(value: object, now: float) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(float(value)) and value > now
    except OverflowError:
        return False


# ------------------------------------------------------------------------------------------------------ route
def validate_route(route: m3.Route, project: str) -> None:
    """Is this route launchable under the catalogue and the profile policy? Run at start() AND again at launch: a route can
    wait in the queue or survive a restart while profiles change underneath it."""
    provider = PROVIDER_ALIASES.get(route.provider, route.provider)
    if route.single_use and not _quota_deadline_is_fresh(route.quota_valid_until, time.time()):
        raise m3.ExecutorError("ROUTE_INVALID", "the selected route has missing or expired quota evidence")
    if provider not in bt_profiles.LAUNCHABLE:
        raise m3.ExecutorError("ROUTE_INVALID", f"provider {route.provider!r} is not launchable "
                               f"({', '.join(bt_profiles.LAUNCHABLE)})")
    if bt_agents.provider_of_model(route.model) != provider:
        raise m3.ExecutorError("ROUTE_INVALID", f"model {route.model!r} does not belong to provider {provider!r}")
    if provider == "antigravity" and route.effort:
        raise m3.ExecutorError("ROUTE_INVALID", "an Antigravity effort is part of the model id, not a separate setting")
    if route.effort and route.effort not in EFFORTS_OF[provider]:
        raise m3.ExecutorError("ROUTE_INVALID", f"effort {route.effort!r} is not valid for {provider!r} "
                               f"({', '.join(EFFORTS_OF[provider]) or 'none'})")
    if route.profile:
        try:
            spec = bt_profiles.get(route.profile)
        except SystemExit as unknown:
            raise m3.ExecutorError("ROUTE_INVALID", str(unknown.code or unknown)[:300]) from None
        if spec.get("provider") != provider:
            raise m3.ExecutorError("ROUTE_INVALID", f"profile {route.profile!r} belongs to {spec.get('provider')!r}, "
                                   f"not {provider!r}")
        _policy(lambda: bt_profiles.authorize(route.profile, project))
        _policy(lambda: bt_profiles.require_launchable(route.profile))
    else:
        _policy(lambda: bt_profiles.authorize_ambient(provider, project))
        if not shutil.which(BINARIES[provider]):
            raise m3.ExecutorError("POLICY_DENIED", f"the {provider} executable is not installed")
    if route.account_ref:                       # the account M2 evaluated must still be the one this profile selects
        expected = m2_account_ref(provider, route.profile)
        if expected and expected != route.account_ref:
            raise m3.ExecutorError("ROUTE_INVALID", "the account behind this profile changed since the route was selected")


def m2_account_ref(provider: str, profile: str) -> str:
    """M2's identity of the account a (provider, profile) selects; '' when M2 is not importable here."""
    try:
        import bt_scheduler_decision as m2
    except ImportError:
        return ""
    return m2.account_reference(bt_agents.account_key(profile or None, provider))


class RouteResolver:
    """M2's reference (or an operator-written `direct:` one) -> a validated route. With an M2 lookup configured `direct:` is
    refused unless `allow_direct` says the operator really wants it: M2's decision and quota check are the point."""

    def __init__(self, project: str, *, m2_lookup: M2_LOOKUP | None = None,
                 repos: Callable[[str], Path | None] | None = None, allow_direct: bool | None = None):
        self.project = project
        self.m2_lookup = m2_lookup
        self.repos = repos                 # role -> checkout, so the work-only gate can run BEFORE any side effect
        self.allow_direct = (m2_lookup is None) if allow_direct is None else allow_direct

    def resolve(self, request: m3.StartRequest) -> m3.Route:
        ref = request.executor
        if ref.startswith(M2_PREFIXES):
            found = self.m2_lookup(ref, request) if self.m2_lookup else None
            if not found:
                raise m3.ExecutorError("ROUTE_UNRESOLVABLE", f"{ref!r}: no M2 route lookup knows this reference")
            self.check_context(found, request)
            route = m3.Route.from_dict({**found, "reference": ref, "single_use": True})
        else:
            if not self.allow_direct:
                raise m3.ExecutorError("ROUTE_UNRESOLVABLE", "direct references are not accepted while M2 selects routes")
            match = DIRECT.match(ref)
            if not match:
                raise m3.ExecutorError("ROUTE_UNRESOLVABLE", f"{ref!r} is neither route:<id> nor direct:<provider>/<model>")
            provider = PROVIDER_ALIASES.get(match["provider"], match["provider"])
            route = m3.Route(provider, match["model"], match["profile"] or "", match["effort"] or "", ref)
        validate_route(route, self.project)
        self.gate_repository(route, request)
        return m3.Route(PROVIDER_ALIASES.get(route.provider, route.provider), route.model, route.profile, route.effort,
                        route.reference, route.account_ref, route.single_use, route.quota_valid_until)

    @staticmethod
    def check_context(found: Mapping[str, Any], request: m3.StartRequest) -> None:
        """When the selector says which plan/task/revision/time a route belongs to, it must be THIS order's."""
        for key, wanted in (("plan_id", request.plan_id), ("revision", request.revision), ("task_id", request.task_id)):
            if key in found and found[key] != wanted:
                raise m3.ExecutorError("ROUTE_INVALID", f"the route was selected for another {key} ({found[key]!r})")
        if (not _PLAN_SHA256.fullmatch(request.plan_sha256 or "") or
                found.get("plan_sha256") != request.plan_sha256):
            raise m3.ExecutorError("ROUTE_INVALID", "the route was selected for another plan_sha256")
        if found.get("superseded_by"):                   # only the most recent decision for a task may launch an attempt
            raise m3.ExecutorError("ROUTE_INVALID", f"the decision was replaced by {str(found['superseded_by'])[:16]}")
        valid_until = found.get("quota_valid_until")
        if not _quota_deadline_is_fresh(valid_until, time.time()):
            raise m3.ExecutorError("ROUTE_INVALID", "the selector's quota evidence for this route has expired")

    def gate_repository(self, route: m3.Route, request: m3.StartRequest) -> None:
        """The work-only gate looks at the project's repository (not at a worktree that does not exist yet)."""
        repo = self.repos(request.repository) if self.repos else None
        if repo is None:
            return                          # an unknown repository is refused by the workspace check with its own code
        provider = PROVIDER_ALIASES.get(route.provider, route.provider)
        if route.profile:
            ok, why = _policy(lambda: bt_profiles.gate_cwd(route.profile, repo))
            if not ok:
                raise m3.ExecutorError("POLICY_DENIED", why[:300])
        else:
            _policy(lambda: bt_profiles.authorize_ambient(provider, self.project, repo))

    def validate(self, route: m3.Route) -> None:           # kept for callers that validate a bare route
        validate_route(route, self.project)


def m2_ledger_lookup(ledger_path: Path | str) -> M2_LOOKUP:
    """M2's public lookup over its decision ledger: only the route M2 SELECTED resolves (alternatives, exclusions, malformed
    and unknown references are `None`). Accepts the `route:`-prefixed form M1's assignment port emits. The ledger is opened
    read-only; M2 is imported lazily, so this adapter works without it. An unreadable ledger is a transient PORT_ERROR
    (not a sticky "unknown"). The answer carries the decision's plan/revision/task and, when a later decision for that task exists, `superseded_by`."""
    def lookup(reference: str, request: m3.StartRequest | None = None) -> Mapping[str, Any] | None:
        import bt_scheduler_decision as m2
        raw = reference.removeprefix("route:")
        try:
            bound = m2.resolve_executor_binding(ledger_path, raw)
        except m2.DecisionLedgerError:
            raise m3.ExecutorError("PORT_ERROR", "the M2 decision ledger is unavailable") from None
        if bound is None:
            return None
        found = bound.route
        out = {"provider": found.provider, "model": found.model, "profile": found.profile or "",
               "effort": found.effort or "", "account_ref": found.account_ref or "",
               "quota_valid_until": found.quota_valid_until,
               "plan_id": bound.plan_id, "revision": bound.revision, "plan_sha256": bound.plan_sha256,
               "task_id": bound.task_id}
        if bound.superseded_by:
            out["superseded_by"] = bound.superseded_by
        return out
    return lookup


# ------------------------------------------------------------------------------------------------------ driver
class MethodologyDriver:
    """Launch and read output through the existing provider drivers; enforce the account gates at launch time."""

    def __init__(self, project: str):
        self.project = project

    def prepare(self, route: m3.Route, prompt: str, workspace: m3.Workspace, timeout_seconds: float) -> m3.Launch:
        validate_route(route, self.project)       # the route may have waited in a queue or crossed a restart: check again
        provider, pid = route.provider, route.profile or None
        base = dict(os.environ)                   # one source for the gates, the account selection and the child
        if pid:
            _policy(lambda: bt_profiles.authorize(pid, self.project))
            ok, why = _policy(lambda: bt_profiles.gate_cwd(pid, workspace.repo))     # the project's repository, not the worktree
            if not ok:
                raise m3.ExecutorError("POLICY_DENIED", why)
        else:
            _policy(lambda: bt_profiles.authorize_ambient(provider, self.project, workspace.repo))
        # Parent-session state and (for a profile route) foreign credentials are dropped BEFORE the profile's own environment
        # is applied, so what the profile itself sets always wins.
        base = {k: v for k, v in base.items()
                if k in SESSION_KEEP or not (k in SESSION_VARS or k.startswith(SESSION_PREFIXES)
                                             or (pid and k in CREDENTIAL_VARS))}
        env = _policy(lambda: bt_profiles.session_env(pid, provider, base, self.project))
        executable = None
        if pid:                                    # a profile may name its own launcher (a token wrapper)
            wanted = bt_profiles.get(pid).get("bin")
            if wanted and wanted != bt_profiles.DEFAULT_BIN.get(provider):
                executable = shutil.which(wanted) or wanted
        invocation = bt_driver.driver_for(provider, executable).invocation(
            prompt, Path(workspace.path), route.model, route.effort or None, int(timeout_seconds), structured=True,
            max_turns=_max_turns())
        current = dict(os.environ)
        removed = tuple(k for k in current if k not in env)
        added = tuple((k, v) for k, v in env.items() if current.get(k) != v)
        return m3.Launch(argv=invocation.argv, stdin=invocation.stdin, env_remove=removed, env_set=added)

    def classify(self, route: m3.Route, raw: str, returncode: int | None, *, timed_out: bool = False,
                 cancelled: bool = False) -> m3.Classification:
        outcome = bt_driver.driver_for(route.provider).normalize(raw, returncode, timed_out=timed_out, cancelled=cancelled)
        return m3.Classification(outcome.status, outcome.reset_epoch, outcome.terminal_event, outcome.text,
                                 outcome.usage, outcome.cost_usd)


# ------------------------------------------------------------------------------------------------------ brief
# A task whose approved verification requires the branch to be on origin/main is the plan's publication step: the owner
# approved that push with the plan, so only that task's prompt allows it (once, fast-forward, to main).
PUBLISH_CHECK = "git merge-base --is-ancestor HEAD origin/main"
# A task that itself says to create its GitHub repository or push to it (david-ui REQ-001 T1: the agent was told never to push and the
# criterion "scaffold is pushed" could not pass): the owner approved that with the plan, so its prompt allows those remote actions.
REMOTE_ACTION = re.compile(r"\bcreate\b[^.\n]{0,40}\bgithub\b[^.\n]{0,20}\brepo\w*|\bgh repo create\b|"
                           r"\bpush(?:ed|es)?\s+(?:\w+\s+){0,3}?(?:to|into)\s+(?:the\s+|its\s+|a\s+)?(?:github|origin|remote|repo\w*)|"
                           r"\b(?:is|are|and)\s+pushed\b|\band\s+push\b", re.IGNORECASE)


class PlanBriefs:
    """The task of the frozen plan, as the agent's brief."""

    def __init__(self, plan, notes=None):
        self.plan = plan
        self.notes = notes

    def brief(self, request: m3.StartRequest) -> m3.Brief:
        try:
            spec = self.plan.task(request.task_id)
        except core.SchedulerError:
            raise m3.ExecutorError("ORDER_INVALID", f"{request.task_id} is not a task of the approved plan") from None
        checks = tuple(f"{v.get('purpose') or v.get('type', 'check')}: {v.get('value', '')}" for v in spec.verification)
        publishes = any(str(v.get("value", "")).strip() == PUBLISH_CHECK for v in spec.verification)
        return m3.Brief(title=str(spec.meta.get("title", spec.id)), objective=str(spec.meta.get("objective", "")),
                        acceptance_criteria=tuple(spec.acceptance_criteria), verification=checks,
                        expected_paths=tuple(spec.expected_paths), notes=self.notes(request) if self.notes else "",
                        publishes=publishes,
                        remote_actions=bool(REMOTE_ACTION.search(" ".join((str(spec.meta.get("objective", "")), *spec.acceptance_criteria)))))


# ------------------------------------------------------------------------------------------------------ core ports
TRANSIENT = frozenset({"PORT_ERROR", "LEDGER_ERROR", "ARTIFACT_ERROR"})   # refusals that say nothing about the order itself


class CoreExecutionPort:
    """The core's `ExecutionPort`: translates its orders into the module's and the module's answers into the core's.

    A transient failure of the executor is RAISED, not answered with a rejection: the core records a port error and tries
    again (then asks `query`), whereas a rejection closes the attempt as failed and burns its attempt budget."""

    def __init__(self, executor: m3.AgentExecutor | None, plan, *, project: str,
                 base_ref: str | Callable[[str], str] = "HEAD", default_repository: str = ""):
        self.executor, self.plan, self.project = executor, plan, project
        self.base_ref, self.default_repository = base_ref, default_repository
        self.on_accepted_attempt: Callable[[str], None] | None = None

    def start(self, order):
        if (order.plan_id, order.revision) != (self.plan.plan_id, self.plan.revision):
            return core.Ack("rejected", "ORDER_INVALID: the order is for another plan revision than the one wired")
        try:
            repo = self.plan.task(order.task_id).repository or self.default_repository
        except Exception:  # noqa: BLE001
            return core.Ack("rejected", "ORDER_INVALID: unknown task")
        if not repo:
            return core.Ack("rejected", "REPOSITORY_UNKNOWN: the task names no repository")
        try:
            base = self.base_ref(order.task_id) if callable(self.base_ref) else self.base_ref
        except integrator.IntegrationError as error:
            if not error.permanent:                         # a hiccup says nothing about the plan: retry, don't burn an attempt
                raise RuntimeError(f"{error.code}: {error.detail}"[:300]) from None
            return core.Ack("rejected", start_rejection_detail(error))   # never run without accepted predecessor work
        request = m3.StartRequest(
            idempotency_key=order.idempotency_key, plan_id=order.plan_id, revision=order.revision, task_id=order.task_id,
            attempt_id=order.attempt_id, token=order.token, executor=order.executor, repository=repo,
            project=self.project, base_ref=base, acceptance_criteria=tuple(order.acceptance_criteria),
            verification=tuple(order.verification), plan_sha256=self.plan.sha256)
        receipt = self.executor.start(request)
        if receipt.status == "rejected" and receipt.code in TRANSIENT:
            raise RuntimeError(f"{receipt.code}: {receipt.detail}")
        if receipt.status in {"accepted", "duplicate"} and self.on_accepted_attempt is not None:
            self.on_accepted_attempt(order.attempt_id)
        return core.Ack(receipt.status, f"{receipt.code}: {receipt.detail}".strip(": ")[:300])

    def cancel(self, order):
        receipt = self.executor.cancel(order.attempt_id, order.token, order.idempotency_key, order.reason)
        return core.Ack(receipt.status, f"{receipt.code}: {receipt.detail}".strip(": ")[:300])

    def query(self, attempt_id: str):
        if self.executor is None:      # `start()` reconciles while the executor is still being composed
            raise core.PortNotReady("the executor is not composed yet")
        status = self.executor.query(attempt_id)
        return core.ExecutionStatus(STATE_OF[status.state], (status.cause or status.detail)[:300])


class CoreEventSink:
    """Technical events -> `SchedulerCore.ingest`. Until M4 exists this is the whole path from executor to core."""

    def __init__(self, scheduler=None, *, scope_check=None):
        self.scheduler = scheduler
        self.scope_check = scope_check
        self.dropped: list[str] = []

    def bind(self, scheduler) -> None:
        self.scheduler = scheduler

    def deliver(self, event: m3.TechnicalEvent) -> None:
        if self.scheduler is None:
            raise RuntimeError("no scheduler bound yet")
        payload = dict(event.payload)
        if event.kind == m3.EVENT_KINDS[1] and self.scope_check is not None:
            refusal = self.scope_check(event)
            if refusal is not None:
                code, paths = refusal
                payload.update(cause=code, detail=("changed paths: " + ", ".join(paths))[:300])
                payload["reason"] = f"{code}: {payload['detail']}"
                event = m3.TechnicalEvent(event.event_id, m3.EVENT_KINDS[2], event.plan_id, event.revision,
                                          event.task_id, event.attempt_id, event.token, event.occurred_at, payload)
        if event.kind in (m3.EVENT_KINDS[2], m3.EVENT_KINDS[3]):          # failed / cancelled: the core reads `reason`
            payload["reason"] = f"{payload.get('cause', '')}: {payload.get('detail', '')}".strip(": ")[:300]
        message = core.Event(event_id=event.event_id, plan_id=event.plan_id, revision=event.revision,
                             task_id=event.task_id, attempt_id=event.attempt_id, source=SOURCE, kind=event.kind,
                             occurred_at=event.occurred_at, payload=payload, token=event.token)
        result = self.scheduler.ingest(message)
        if result.status == "invalid":      # malformed for this run: retrying cannot help and would block the outbox
            self.dropped.append(f"{event.event_id}: {result.reason}")


class PinnedRoute:
    """AssignmentPort: every ready task gets the route reference the OPERATOR wrote. Not a decision engine (that is M2)."""

    def __init__(self, reference: str):
        self.reference = reference

    def propose(self, request):
        return [core.Assignment(task.id, self.reference, "operator-pinned route")
                for task in request.ready[:max(0, request.free_slots)]]


# ------------------------------------------------------------------------------------------------------ wiring
def executor_root(rdir: Path, identity: str = "") -> Path:
    """`<bitácora root>/.state/executor/<project>-<REQ>[-<identity>]/` next to the scheduler's database (local, untracked),
    else `<requirement>/EXECUTOR[-<identity>]/`. The identity (plan revision + hash + the core run's birth) keeps a NEW run of
    the same requirement, or a later plan revision, from inheriting another run's attempts: the core numbers attempts and
    builds idempotency keys per run, so two runs would otherwise collide on `att-0001`."""
    db = sched.run_db_path(Path(rdir))
    suffix = f"-{identity}" if identity else ""
    if db.parent.name == "scheduler":
        return db.parent.parent / "executor" / f"{db.stem}{suffix}"
    return Path(rdir) / f"EXECUTOR{suffix}"


def run_identity(scheduler) -> str:
    """`r<revision>-<plan sha8>-<run birth>`: stable for one core run, different for a new run or a new revision."""
    snap = scheduler.snapshot()
    born = next((e.at for e in scheduler.audit_log() if e.kind == "run_created"), 0.0)
    return f"r{snap.revision}-{snap.plan_sha256[:8]}-{int(born * 1000)}"


def repositories(project: str, overrides: Mapping[str, Path | str] | None = None) -> Callable[[str], Path | None]:
    """role -> checkout of the project's registered repositories, resolved on every call (clones can appear later)."""
    def find(role: str) -> Path | None:
        if overrides and role in overrides:
            return Path(overrides[role])
        found = bt_workspace.repos(bt_core.ROOT, project, False)
        return found.get(role)
    return find


def worktree_allocation(attempt: Mapping[str, Any]) -> dict[str, Any]:
    """An attempt's workspace in the shape `bt_worktree` consumes (`check_scope`, `candidate`, `integrate`), so the existing
    scope and integration tooling can work on what M3 produced. Nothing here integrates anything."""
    ws = attempt["workspace"]
    return {"task_id": attempt["request"]["task_id"], "branch": ws["branch"], "worktree": ws["path"],
            "base_sha": ws["base_sha"], "repo": ws["repo"], "journal": ws.get("journal", ""), "state": "allocated",
            "allowed_roots": [str(Path(ws["journal"]).parent)] if ws.get("journal") else [str(Path(ws["path"]).parent)]}


@dataclass
class Wiring:
    scheduler: Any
    executor: m3.AgentExecutor
    port: CoreExecutionPort
    sink: CoreEventSink
    stream_adapter: M3StreamAdapter
    monitor: MonitorRuntime | None = None
    recovery: Any = None
    verification_runtime: Any = None
    verification_store: Any = None
    stream_candidates: M3StreamCandidates = field(default_factory=M3StreamCandidates)

    def drain_stream(self, attempt_id: str, run_id: str, *, description: Mapping[str, Any] | None = None) -> int:
        """Drain one bounded M3 batch through the M4-owned FIFO bridge."""
        return drain_m3_stream(self, attempt_id, run_id, description=description)

    def close(self) -> None:
        from bt_scheduler_executor_wiring import close

        close(self)


def _accepted_attempts(scheduler) -> dict[str, str]:
    """{task id: the attempt the core accepted} for every completed task, from ONE snapshot of the run."""
    def read(ctx):
        # the attempt that was ACCEPTED, not the task's last one: a rework taken back (`withdraw-rework`) leaves the failed attempt of the
        # redo after it, and the next task then looked for the snapshot of an attempt that never produced one (REQ-020 T15, 07:28)
        found = {}
        for tid, rec in ctx.state.tasks.items():
            if rec.state == "completed":
                attempt = next((a for a in reversed(rec.attempts) if ctx.state.attempts[a].state == "accepted"), None)
                if attempt:
                    found[tid] = attempt
        return found
    return scheduler.read(read)


def _earlier_attempts(scheduler, task_id: str) -> list[str]:
    """Attempts of the task whose accepted result was later sent back (newest first): the results a redo replaced."""
    def read(ctx):
        rec = ctx.state.tasks[task_id]
        current = next((a for a in reversed(rec.attempts) if ctx.state.attempts[a].state == "accepted"), None) \
            if rec.state == "completed" else None
        return [a for a in reversed(rec.attempts) if ctx.state.attempts[a].state == "accepted" and a != current]
    return scheduler.read(read)


def _snapshot_sha(executor, attempt_id: str) -> str | None:
    """The snapshot commit the executor preserved for that attempt (None when the handoff failed or is absent).

    A rebase keeps accepted tasks but starts an executor root for the new plan revision. Their attempts stay in the
    roots of the same core run (same run birth), which are read here, read-only, when this one has no record."""
    described = executor.describe(attempt_id)
    if described is None:
        return _sibling_snapshot_sha(Path(executor.root), attempt_id)
    handoff = described.get("handoff") or {}
    return handoff.get("snapshot_sha") if handoff.get("status") == "captured" else None


def _start_base_sha(executor, attempt_id: str) -> str | None:
    """The commit the attempt started from (its handoff's `base_sha`): what its own work is measured against."""
    described = executor.describe(attempt_id)
    handoff = (described or {}).get("handoff") or {}
    base = handoff.get("base_sha")
    return base if isinstance(base, str) and base else None


def _sibling_snapshot_sha(root: Path, attempt_id: str) -> str | None:
    birth = root.name.rpartition("-")[2]
    if not birth.isdigit():
        return None
    stem = root.name.split("-r", 1)[0]
    for sibling in sorted(root.parent.glob(f"{stem}-r*-*-{birth}")):
        ledger = sibling / "ledger.db"
        if sibling == root or not ledger.is_file():
            continue
        try:
            with closing(sqlite3.connect(f"{ledger.resolve().as_uri()}?mode=ro", uri=True, timeout=0.5)) as db:
                row = db.execute("SELECT handoff FROM attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
            handoff = json.loads(row[0]) if row and row[0] else {}
        except (sqlite3.Error, OSError, ValueError, TypeError):
            continue
        if isinstance(handoff, dict) and handoff.get("status") == "captured":
            sha = handoff.get("snapshot_sha")
            return sha if isinstance(sha, str) else None
    return None


def wire(rdir: Path, **options) -> Wiring:
    """Compose optional M2/M4/M5 ports; see bt_scheduler_executor_wiring.wire for keyword options.

    Existing recovery= callers remain valid. recovery_store_path opts into durable M5 advice and snapshot continuation.
    """
    from bt_scheduler_executor_wiring import wire as compose
    return compose(rdir, **options)


def _executor_attempts(project: str, req: str, attempt_id: str) -> list[dict]:
    """Executor ledger rows of this attempt id, across every plan revision's executor root."""
    rows = []
    for ledger in (bt_core.ROOT / ".state" / "executor").glob(f"{project}-{req}-r*/ledger.db"):
        try:
            conn = sqlite3.connect(f"{ledger.resolve().as_uri()}?mode=ro", uri=True, timeout=2)
        except sqlite3.Error:
            continue
        try:
            for workspace, shim in conn.execute("SELECT workspace, shim FROM attempts WHERE attempt_id = ? "
                                                "AND state NOT IN ('finished', 'failed', 'cancelled')", (attempt_id,)):
                rows.append({"workspace": _json(workspace), "shim": _json(shim)})
        except sqlite3.Error:
            pass
        finally:
            conn.close()
    return rows


def _json(text) -> dict:
    try:
        value = json.loads(text) if text else {}
    except ValueError:
        return {}
    return value if isinstance(value, dict) else {}


def kill_attempt_processes(project: str, req: str, attempt_id: str) -> int:
    """Stop what the executor started for this attempt: its shim, its process group and any straggler left in its
    worktree, in every plan revision's executor root. Returns how many processes were signalled."""
    procinfo = m3.procinfo

    hit = 0
    for row in _executor_attempts(project, req, attempt_id):
        shim, workspace = row["shim"], row["workspace"]
        for key, send in (("pgid", procinfo.signal_group), ("pid", procinfo.signal_pid)):
            if isinstance(shim.get(key), int) and shim[key] > 1:
                with contextlib.suppress(Exception):
                    send(shim[key], signal.SIGKILL)
                    hit += 1
        if isinstance(workspace.get("path"), str) and workspace["path"].startswith("/") and Path(workspace["path"]).is_dir():
            hit += procinfo.kill_in_cwd(workspace["path"], signal.SIGKILL)
    return hit
