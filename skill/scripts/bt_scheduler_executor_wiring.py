"""Opt-in composition of Scheduler ports; the executor adapter remains the single importer of M3."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

import bt_scheduler_executor_adapter as api
from bt_scheduler_recovery_adapter import RecoveryAdapter
from bt_scheduler_retry import RetryContinuation


def close(wiring: api.Wiring) -> None:
    """Close required verification, recovery, stream and executor resources in dependency order."""
    try:
        if wiring.verification_runtime is not None:
            wiring.verification_runtime.close(wait=True)
    finally:
        try:
            if wiring.verification_store is not None:
                wiring.verification_store.close()
        finally:
            if wiring.recovery is not None:
                try:
                    wiring.recovery.close()
                finally:
                    try:
                        wiring.stream_adapter.close_all()
                    finally:
                        wiring.executor.close()
            else:
                try:
                    wiring.stream_adapter.close_all()
                finally:
                    wiring.executor.close()


def _with_owner_notes(rdir, plan, base):
    """The prompt notes of a retry, preceded by what the owner wrote for the task in answer to a decision request, by
    the open audit findings of a task sent back, and, for an audit task, by how to write its findings ledger."""
    import bt_audit_gate
    import bt_scheduler_decisions

    def notes(request):
        parts = [bt_scheduler_decisions.operator_notes(rdir, request.task_id),
                 bt_scheduler_decisions.audit_notes(rdir, request.task_id),
                 bt_scheduler_decisions.verify_notes(rdir, request.task_id)]
        try:
            task = plan.task(request.task_id)
            if task.meta.get("kind") == "audit":
                parts.append(bt_audit_gate.ledger_help(bt_audit_gate.ledger_path(task.expected_paths)))
        except api.core.SchedulerError:
            pass
        parts.append(base(request) if base else "")
        return "\n\n".join(part for part in parts if part)
    return notes


def wire(rdir: Path, *, project: str, assignment=None, verification=None, recovery=None, config=None,
         executor_config: api.m3.Config | None = None, resolver: api.m3.RouteResolver | None = None,
         m2_lookup: api.M2_LOOKUP | None = None, m2_ledger: Path | str | None = None, allow_direct: bool | None = None,
         repos: Mapping[str, Path | str] | None = None, base_ref: str | Callable[[str], str] = "HEAD",
         default_repository: str = "", clock: Callable[[], float] | None = None, driver: api.m3.AgentDriver | None = None,
         autostart: bool = True, integrate_predecessors: bool = True,
         monitor_store_path: Path | str | None = None, recovery_store_path: Path | str | None = None,
         recovery_policy: Mapping[str, object] | None = None,
         quality_store_path: Path | str | None = None,
         quality_policy: Mapping[str, object] | None = None) -> api.Wiring:
    """A Scheduler core with optional decision, monitor, recovery, and quality-verification ports.

    Opt-in and non-destructive: refuses a requirement already run by the legacy supervisor (the api.core's own rule). The
    executor's local state lives in `api.executor_root(rdir, api.run_identity)`: one root per api.core RUN and plan revision.
    `verification` remains caller-owned. Supplying `quality_store_path` opts into M6 and is mutually exclusive with it;
    M6 uses its own durable store and the unchanged M1 VerificationPort. With an M2 ledger/lookup `direct:` references are
    refused unless `allow_direct=True`. `base_ref` (a ref or `task_id -> ref`) is where each task's worktree starts. The
    executor does not integrate accepted prerequisite work; by default (`integrate_predecessors=True`) a task starts from
    a commit that merges its accepted same-repository predecessors' handoff snapshots (`bt_scheduler_integrator`;
    `base_ref` stays the fallback for tasks with nothing to integrate), and a conflict or missing snapshot rejects the
    order with its cause. Pass `integrate_predecessors=False` to start every task from `base_ref` alone."""
    if recovery is not None and recovery_store_path is not None:
        raise ValueError("supply recovery or recovery_store_path, not both")
    if quality_store_path is not None and verification is not None:
        raise ValueError("supply verification or quality_store_path, not both")
    if quality_policy is not None and quality_store_path is None:
        raise ValueError("quality_policy requires quality_store_path")
    if quality_policy is not None and not isinstance(quality_policy, Mapping):
        raise TypeError("quality_policy must be a mapping")
    if quality_store_path is not None and not isinstance(quality_store_path, (str, Path)):
        raise TypeError("quality_store_path must be a filesystem path")
    rdir = Path(rdir)
    quality_path = (_quality_store_path(quality_store_path, rdir=rdir, monitor_store_path=monitor_store_path,
                                        recovery_store_path=recovery_store_path)
                    if quality_store_path is not None else None)
    quality_runtime_policy = None
    if quality_path is not None:
        from bt_scheduler_quality.policy import QualityPolicy

        import bt_config

        configured = {key: bt_config.get(f"verifier.{key}", True) for key in ("network", "allow_production_actions")}
        import bt_verifier_env

        environment, secrets = bt_verifier_env.load(bt_config.get("verifier.env_file", ""))
        quality_runtime_policy = QualityPolicy(**{**{k: v for k, v in configured.items() if isinstance(v, bool)},
                                                  **({"environment": environment, "secret_values": secrets}
                                                     if environment else {}),
                                                  **dict(quality_policy or {})})
    if m2_ledger is not None and m2_lookup is None:
        m2_lookup = api.m2_ledger_lookup(m2_ledger)
    port = api.CoreExecutionPort(None, api.sched.approved_plan(rdir), project=project, base_ref=base_ref,
                             default_repository=default_repository)
    sink = api.CoreEventSink()
    routing = assignment if callable(getattr(assignment, "plan", None)) else None
    scheduler = api.sched.open_scheduler(rdir, ports=api.core.Ports(assignment=assignment, routing=routing,
                                                            execution=port, verification=verification,
                                                            recovery=recovery),
                                     config=config, clock=clock)
    port.plan = scheduler.plan                         # one plan object for the api.core, the brief and the repository roles
    root = api.executor_root(rdir, api.run_identity(scheduler))
    repo_of = api.repositories(project, repos)
    executor = api.m3.AgentExecutor(
        root, resolver=resolver or api.RouteResolver(project, m2_lookup=m2_lookup, repos=repo_of, allow_direct=allow_direct),
        briefs=api.PlanBriefs(scheduler.plan), driver=driver or api.MethodologyDriver(project),
        workspaces=api.m3.GitWorkspaces(root / "ws", repo_of), sink=sink, config=executor_config, autostart=False)
    stream_adapter = api.M3StreamAdapter(executor.attempts_dir, max_open_streams=executor.cfg.max_running)
    wiring = api.Wiring(scheduler, executor, port, sink, stream_adapter)
    port.on_accepted_attempt = wiring.stream_candidates.track
    try:
        monitor = api.create_monitor_runtime(stream_adapter, monitor_store_path, api.sched.run_db_path(rdir), scheduler)
        wiring.monitor = monitor
    except Exception:
        wiring.close()
        raise
    port.executor = executor
    base_notes = None
    integrate = None
    try:
        if integrate_predecessors:
            integrate = api.integrator.PredecessorIntegrator(fallback=base_ref)
            integrate.bind(plan=scheduler.plan, repo_of=repo_of, default_repository=default_repository,
                           identity=api.run_identity(scheduler),
                           accepted=lambda: api._accepted_attempts(scheduler),
                           snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                           earlier_of=lambda task: api._earlier_attempts(scheduler, task))
            port.base_ref = integrate.base_ref
        if recovery_store_path is not None:
            continuation = RetryContinuation(scheduler, executor, repo_of, port.base_ref,
                                             default_repository=default_repository,
                                             snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                                             run_dir=rdir, integrator=integrate)
            wiring.recovery = RecoveryAdapter(
                recovery_store_path, scheduler=scheduler, run_id=api.run_identity(scheduler),
                describe=continuation.describe, policy=recovery_policy)
            wiring.recovery.metrics()
            scheduler.ports.recovery = wiring.recovery
            port.base_ref = continuation.base_ref
            base_notes = continuation.notes
        executor.briefs.notes = _with_owner_notes(rdir, scheduler.plan, base_notes)
        if quality_store_path is not None:
            import bt_audit_gate
            import bt_config
            import bt_remediation
            import bt_scheduler_decisions
            from bt_scheduler_quality.store import QualityStore
            from bt_scheduler_quality_adapter import QualityVerificationPort

            if quality_path is None or quality_runtime_policy is None:
                raise RuntimeError("M6 composition was not fully validated")
            wiring.verification_store = QualityStore(quality_path)

            def repository_for_order(order):
                try:
                    task = scheduler.plan.task(order.task_id)
                except api.core.SchedulerError:
                    return None
                role = task.repository or default_repository
                return repo_of(role) if role else None

            wiring.verification_runtime = QualityVerificationPort(
                scheduler, executor, wiring.verification_store, quality_runtime_policy, repository_for_order,
                attempts_root=executor.attempts_dir,
                rework_notes=lambda task_id, text: bt_scheduler_decisions.write_audit_notes(rdir, task_id, text),
                verify_notes=lambda task_id, text: bt_scheduler_decisions.write_verify_notes(rdir, task_id, text),
                audit_policy=bt_audit_gate.policy_from(bt_config.get),
                integration_check=(integrate.would_conflict
                                   if integrate is not None and bt_config.get("gates.integration_check", True) is True
                                   else None),
                unresolved_check=getattr(integrate, "unresolved", None),
                remediate=bt_remediation.hook(rdir, bt_audit_gate.policy_from(bt_config.get)),
                integration_retries=(lambda v: v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0)(
                    bt_config.get("gates.integration_retries", 0)))
            scheduler.ports.verification = wiring.verification_runtime
            wiring.verification_runtime.start()
        sink.bind(scheduler)
        api.seed_terminal_streams(wiring)
        if autostart:
            executor.start_loop()
    except Exception:
        wiring.close()
        raise
    return wiring


def _quality_store_path(value: Path | str, *, rdir: Path, monitor_store_path: Path | str | None,
                        recovery_store_path: Path | str | None) -> Path:
    raw = str(value)
    if not raw.strip() or raw == ":memory:":
        raise ValueError("quality_store_path must name a durable file")
    resolved = Path(value).expanduser().resolve()
    owned = {api.sched.run_db_path(rdir).resolve()}
    for other in (monitor_store_path, recovery_store_path):
        if other is not None:
            owned.add(Path(other).expanduser().resolve())
    if resolved in owned:
        raise ValueError("M6 quality store must be separate from M1, M4, and M5 stores")
    return resolved
