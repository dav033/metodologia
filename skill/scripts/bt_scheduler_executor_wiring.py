"""Opt-in composition of Scheduler ports; the executor adapter remains the single importer of M3."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

import bt_scheduler_executor_adapter as api
from bt_scheduler_recovery_adapter import EvidenceUnavailable, RecoveryAdapter
from bt_scheduler_retry import RetryContinuation
from bitacora_platform import conflict_publisher


def close(wiring: api.Wiring) -> None:
    """Close required verification, recovery, stream and executor resources in dependency order."""
    try:
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
    finally:
        owner_composition = getattr(wiring, "composition_runtime", None)
        if owner_composition is not None:
            owner_composition.close()


LINE_MARKER = "RUN.integration-line"


def _line_enabled(rdir: Path, accepted: Mapping[str, str], probe: Callable[[], str] | None = None) -> bool:
    """`gates.integration_line` (REQ-028) is on for every run that BEGINS with it (the default since REQ-030). The run
    records the choice in `RUN.integration-line` and keeps it: switching a run between two integration models mid-way
    would change what its tasks start from. A run that already accepted tasks without the line is MIGRATED only when the
    line can hold all of them (`probe()` -> '' when every accepted contribution applies cleanly and no file is lost,
    else the reason): their snapshots were never integrated with each other, so a run whose accepted work overlaps stays
    on the predecessor merge and says why in `RUN.integration-line.skipped`. `gates.integration_line_migrate` = False
    turns the migration off. An unreadable configuration means off."""
    marker = Path(rdir) / LINE_MARKER
    skipped = Path(str(marker) + ".skipped")
    try:
        if marker.exists():
            return True
        import bt_config
        if bt_config.get("gates.integration_line", True) is not True:
            return False
        if not accepted:
            marker.write_text("integration line on since the run began\n", encoding="utf-8")
            return True
        if bt_config.get("gates.integration_line_migrate", True) is not True or probe is None:
            return False
        reason = probe()
        if reason:
            skipped.write_text(f"not migrated to the integration line: {reason}\n", encoding="utf-8")
            return False
        marker.write_text(f"integration line on since the run was migrated with {len(accepted)} accepted tasks\n",
                          encoding="utf-8")
        skipped.unlink(missing_ok=True)
        return True
    except Exception:  # noqa: BLE001 - configuration trouble must not stop a run from starting
        return False


def _migration_probe(line) -> Callable[[], str]:
    """'' when the line holds every accepted task of every role (dry run: computed in memory, no ref moves)."""
    def probe() -> str:
        try:
            for role in line.roles():
                state = line.state(role)
                if state.unresolved:
                    task, files = next(iter(state.unresolved.items()))
                    return f"{task} does not fit the integrated tree ({', '.join(files[:4])})"
        except Exception as error:  # noqa: BLE001 - any trouble means "do not migrate"
            return f"the line cannot be computed ({type(error).__name__})"
        return ""
    return probe


def _with_owner_notes(rdir, plan, base):
    """The prompt notes of a retry, preceded by what the owner wrote for the task in answer to a decision request, by
    the open audit findings of a task sent back, and, for an audit task, by how to write its findings ledger."""
    import bt_attempt_history
    import bt_audit_gate
    import bt_scheduler_decisions

    def _history(task_id: str) -> str:
        try:
            return bt_attempt_history.prompt(rdir, task_id, bt_scheduler_decisions._state(rdir))
        except Exception:  # noqa: BLE001 - a prompt without its history is still a prompt
            return ""

    def _analysis(task_id: str) -> str:
        try:
            import bt_attempt_analyst

            return bt_attempt_analyst.prompt(rdir, task_id)
        except Exception:  # noqa: BLE001 - an opinion that cannot be read is simply not in the prompt
            return ""

    def notes(request):
        parts = [bt_scheduler_decisions.operator_notes(rdir, request.task_id),
                 bt_scheduler_decisions.audit_notes(rdir, request.task_id),
                 _history(request.task_id),
                 _analysis(request.task_id),
                 bt_scheduler_decisions.verify_notes(rdir, request.task_id)]
        try:
            task = plan.task(request.task_id)
            if task.meta.get("kind") == "audit":
                ledgers = tuple(path for path in task.expected_paths if isinstance(path, str)
                                and path.endswith(bt_audit_gate.LEDGER_SUFFIX))
                parts.append(bt_audit_gate.ledger_help(ledgers[0] if len(ledgers) == 1 else None))
                if len(ledgers) > 1:
                    parts.append("This audit has independent ledgers; write one complete audit-findings/1 record to each: "
                                 + ", ".join(f"`{path}`" for path in ledgers) + ".")
        except api.core.SchedulerError:
            pass
        parts.append(base(request) if base else "")
        from bt_prompt_context import compact

        return compact("\n\n".join(part for part in parts if part))
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
         quality_policy: Mapping[str, object] | None = None,
         composition_base: Callable[..., str | None] | None = None,
         composition_runtime=None) -> api.Wiring:
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
        mb = bt_config.get("verifier.max_workspace_mb", 2048)
        if isinstance(mb, int) and not isinstance(mb, bool) and mb >= 64:
            configured["max_workspace_bytes"] = mb << 20
        configured["cache_ignores_outputs"] = bt_config.get("verifier.cache_ignores_outputs", True)
        rerun = bt_config.get("verifier.rerun_failed_checks", 1)
        if isinstance(rerun, int) and not isinstance(rerun, bool) and 0 <= rerun <= 3:
            configured["rerun_failed_checks"] = rerun
        import bt_verifier_env

        environment, secrets = bt_verifier_env.load(bt_verifier_env.path_for(bt_config.get("verifier.env_file", ""), project))
        quality_runtime_policy = QualityPolicy(**{**{k: v for k, v in configured.items() if isinstance(v, (bool, int))},
                                                  **({"environment": environment, "secret_values": secrets}
                                                     if environment else {}),
                                                  **dict(quality_policy or {})})
    if m2_ledger is not None and m2_lookup is None:
        m2_lookup = api.m2_ledger_lookup(m2_ledger)
    plan = api.sched.approved_plan(rdir)
    repo_of = api.repositories(project, repos)
    port = api.CoreExecutionPort(None, plan, project=project, base_ref=base_ref,
                                 default_repository=default_repository, composition_base=composition_base,
                                 repo_of=repo_of)
    routing = assignment if callable(getattr(assignment, "plan", None)) else None
    scheduler = api.sched.open_scheduler(rdir, ports=api.core.Ports(assignment=assignment, routing=routing,
                                                            execution=port, verification=verification,
                                                            recovery=recovery),
                                     config=config, clock=clock)
    port.plan = scheduler.plan                         # one plan object for the api.core, the brief and the repository roles
    root = api.executor_root(rdir, api.run_identity(scheduler))
    def designer_scope_check(event):
        try:
            task = scheduler.plan.task(event.task_id)
        except api.core.SchedulerError:
            return None
        task_role = (event.payload or {}).get("role", task.meta.get("role", ""))
        try:
            plan_version = tuple(int(part) for part in scheduler.plan.schema_version.split("."))
        except (AttributeError, ValueError):
            return None
        if plan_version < (1, 3, 0) or (task.meta.get("kind") != "design" and task_role != "designer"):
            return None
        handoff = (event.payload or {}).get("handoff") or {}
        base_sha, snapshot_sha = handoff.get("base_sha"), handoff.get("snapshot_sha")
        if not base_sha or not snapshot_sha:
            return "DESIGN_SCOPE_UNAVAILABLE", ()
        repository = repo_of(task.repository or default_repository)
        import bt_config
        preview_projects = bt_config.get("design.preview_projects", [])
        preview_enabled = bt_config.get("design.preview", False) is True or project in preview_projects
        return api.designer_scope_refusal(repository, base_sha, snapshot_sha,
                                          kind=task.meta.get("kind", ""),
                                          role=task_role,
                                          preview_enabled=preview_enabled,
                                          plan_version=scheduler.plan.schema_version)
    sink = api.CoreEventSink(scope_check=designer_scope_check)
    import bt_config
    from dataclasses import replace

    executor_config = replace(executor_config or api.m3.Config(), prompt_rtk=bt_config.get("prompts.rtk", True))
    executor = api.m3.AgentExecutor(
        root, resolver=resolver or api.RouteResolver(project, m2_lookup=m2_lookup, repos=repo_of, allow_direct=allow_direct),
        briefs=api.PlanBriefs(scheduler.plan), driver=driver or api.MethodologyDriver(project),
        workspaces=api.m3.GitWorkspaces(root / "ws", repo_of), sink=sink, config=executor_config, autostart=False)
    stream_adapter = api.M3StreamAdapter(executor.attempts_dir, max_open_streams=executor.cfg.max_running)
    wiring = api.Wiring(scheduler, executor, port, sink, stream_adapter)
    wiring.composition_runtime = composition_runtime
    port.on_accepted_attempt = wiring.stream_candidates.track
    try:
        if composition_runtime is not None:
            composition_runtime.bind_scheduler(scheduler)
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
            import bt_interventions
            identity = api.run_identity(scheduler)

            def heard(kind, **fields):
                bt_interventions.record(rdir, kind=kind, run=identity, **fields)

            integrate.bind(plan=scheduler.plan, repo_of=repo_of, default_repository=default_repository,
                           identity=identity,
                           accepted=lambda: api._accepted_attempts(scheduler),
                           snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                           earlier_of=lambda task: api._earlier_attempts(scheduler, task),
                           start_base_of=lambda attempt: api._start_base_sha(executor, attempt), on_event=heard)
            port.base_ref = integrate.base_ref
            import bt_config
            integrate.check_files = bt_config.get("gates.integration_check_files", True) is not False
            if scheduler.plan.schema_version == "1.3.0" and scheduler.plan.subplans:
                import bt_integration_line
                line = bt_integration_line.SubplanLineRouter(
                    plan=scheduler.plan, repo_of=repo_of, default_repository=default_repository, identity=identity,
                    accepted=lambda: api._accepted_attempts(scheduler),
                    snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                    start_base_of=lambda attempt: api._start_base_sha(executor, attempt), on_event=heard,
                    check_files=integrate.check_files,
                    base_of=lambda role: base_ref if isinstance(base_ref, str) else "HEAD")
            else:
                import bt_integration_line
                line = bt_integration_line.Line(
                    plan=scheduler.plan, repo_of=repo_of, default_repository=default_repository,
                    identity=identity, accepted=lambda: api._accepted_attempts(scheduler),
                    snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                    start_base_of=lambda attempt: api._start_base_sha(executor, attempt), on_event=heard,
                    check_files=integrate.check_files,
                    base_of=lambda role: base_ref if isinstance(base_ref, str) else "HEAD")
            subplan_plan = scheduler.plan.schema_version == "1.3.0" and bool(scheduler.plan.subplans)
            if subplan_plan or _line_enabled(rdir, api._accepted_attempts(scheduler), _migration_probe(line)):
                integrate.attach_line(line)
                integrate.recompute_line()
                if subplan_plan:
                    (Path(rdir) / LINE_MARKER).write_text("integration line on for frozen subplan scopes\n", encoding="utf-8")
        if recovery_store_path is not None:
            import bt_recovery_pipeline
            import bt_recovery_runtime
            m6_evidence_reader = (lambda reference: wiring.verification_store.get_result_manifest(reference)
                                  if wiring.verification_store is not None else None)
            continuation = RetryContinuation(scheduler, executor, repo_of, port.base_ref,
                                             default_repository=default_repository,
                                             snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                                             run_dir=rdir, integrator=integrate)
            wiring.recovery = RecoveryAdapter(
                recovery_store_path, scheduler=scheduler, run_id=api.run_identity(scheduler),
                describe=continuation.describe, policy=recovery_policy, rdir=rdir,
                recovery_sources=lambda: bt_recovery_runtime.sources(rdir, api.run_identity(scheduler)),
                diagnostic_pipeline=bt_recovery_pipeline.owner_pipeline(rdir),
                m6_evidence_reader=m6_evidence_reader,
                composition_propagation=(getattr(composition_runtime, "demonstrated_frontier", None)
                                         if composition_runtime is not None else None))
            wiring.recovery.metrics()
            scheduler.ports.recovery = wiring.recovery
            if integrate is not None:
                integrate.bind(plan=scheduler.plan, repo_of=repo_of, default_repository=default_repository,
                               identity=api.run_identity(scheduler), accepted=lambda: api._accepted_attempts(scheduler),
                               snapshot_of=lambda attempt: api._snapshot_sha(executor, attempt),
                               earlier_of=lambda task: api._earlier_attempts(scheduler, task),
                               # bind() replaces the whole binding: everything the first call set must be said again
                               start_base_of=lambda attempt: api._start_base_sha(executor, attempt), on_event=heard,
                               on_conflict=lambda **fields: bt_interventions.record_conflict(
                                   rdir, run=api.run_identity(scheduler), **fields),
                               conflict_sink=wiring.recovery.publish_conflict_observation)
            port.base_ref = continuation.base_ref
            base_notes = continuation.notes
        executor.briefs.notes = _with_owner_notes(rdir, scheduler.plan, base_notes)
        if quality_store_path is not None:
            import bt_attempt_history
            import bt_attestation
            import bt_audit_gate
            import bt_config
            import bt_remediation
            import bt_scheduler_decisions
            from bt_scheduler_quality.store import QualityStore
            from bt_scheduler_quality_adapter import QualityVerificationPort

            if quality_path is None or quality_runtime_policy is None:
                raise RuntimeError("M6 composition was not fully validated")
            wiring.verification_store = QualityStore(quality_path)
            if composition_runtime is not None:
                composition_runtime.bind_quality_policy(quality_runtime_policy)

            def repository_for_order(order):
                try:
                    task = scheduler.plan.task(order.task_id)
                except api.core.SchedulerError:
                    return None
                role = task.repository or default_repository
                return repo_of(role) if role else None

            def publish_conflict_observation(order, clash, refusal, detail):
                return conflict_publisher.publish(wiring.recovery, scheduler.plan, order, clash, refusal, detail)
            wiring.verification_runtime = QualityVerificationPort(
                scheduler, executor, wiring.verification_store, quality_runtime_policy, repository_for_order,
                attempts_root=executor.attempts_dir,
                rework_notes=lambda task_id, text: bt_scheduler_decisions.write_audit_notes(rdir, task_id, text),
                verify_notes=lambda task_id, text: bt_scheduler_decisions.write_verify_notes(rdir, task_id, text),
                verify_history=lambda task_id, attempt, text: bt_attempt_history.record(rdir, task_id, attempt, text),
                publish_audit_observation=lambda task_id, attempt, observation: bt_attempt_history.record_observation(
                    rdir, task_id, attempt, observation),
                audit_policy=bt_audit_gate.policy_from(bt_config.get),
                integration_check=(integrate.would_conflict
                                   if integrate is not None and bt_config.get("gates.integration_check", True) is True
                                   else None),
                publish_conflict_observation=publish_conflict_observation,
                unresolved_check=getattr(integrate, "unresolved", None),
                revert_check=getattr(integrate, "reverted", None),
                remediate=bt_remediation.hook(rdir, bt_audit_gate.policy_from(bt_config.get)),
                attestations=bt_attestation.lookup(rdir, bind_attempt=bt_config.get("gates.attestation_bind_attempt", True) is True),
                integration_retries=(lambda v: v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else 0)(
                    bt_config.get("gates.integration_retries", 0)),
                integration_rework_limit=(lambda v: v if isinstance(v, int) and not isinstance(v, bool) and v >= 1 else 6)(
                    bt_config.get("gates.integration_rework_limit", 6)),
                composition_identity=(getattr(composition_runtime, "verification_identity", None)
                                      if composition_runtime is not None else None))
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
