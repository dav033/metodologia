"""CLI for the unattended Scheduler: `scheduler-watch` keeps a run alive, `scheduler-op` is the operator's hand on it."""
from __future__ import annotations

import argparse
import json

import bt_scheduler_adapter as adapter

ACTIONS = ("status", "decisions", "decide", "diagnose", "recovery-preview", "recovery-status", "stop", "resume", "cancel-attempt", "reopen", "retry", "rework", "withdraw-rework", "continue-from", "attest", "coordinator", "heal", "revise", "remediate")


def register(subparsers) -> None:
    watch = subparsers.add_parser("scheduler-watch", help="vigilar un plan: reanuda el scheduler si muere, hasta que termine")
    watch.add_argument("req", help="REQ-NNN")
    watch.add_argument("--detach", action="store_true", help="correr en segundo plano (log en .state/watch/)")
    evolve = subparsers.add_parser("scheduler-evolve", help="aprender de las intervenciones: analizar, proponer, probar con A/B y aplicar lo seguro")
    evolve.add_argument("--propose", action="store_true", help="escribir las propuestas de riesgo alto como P-NNN en PENDING.md")
    evolve.add_argument("--apply", action="store_true", help="aplicar los cambios de bajo riesgo que el A/B sobre las réplicas probó")
    evolve.add_argument("--revert", action="store_true", help="deshacer los cambios que la evolución aplicó")
    evolve.add_argument("--capture", default="", metavar="REQ", help="guardar la réplica de un run (su plan y sus tiempos) para futuros A/B")
    op = subparsers.add_parser("scheduler-op", help="mover un plan en marcha: cancelar intento, reabrir tarea, revisar el plan")
    op.add_argument("req", help="REQ-NNN")
    op.add_argument("action", choices=ACTIONS)
    op.add_argument("target", nargs="?", default="",
                    help="attempt id for cancel-attempt, task id for reopen and retry, comma-separated task ids for rework "
                         "(they and everything downstream go back to be redone; with --only just them) and withdraw-rework "
                         "(take the rework back for tasks that redid nothing), status|stop|start|run|revert for heal (self-healing of the run; revert takes "
                         "the case id as the second argument), task id for attest (--reason is the evidence: what you did and saw; "
                         "the optional second argument picks one manual check by purpose text or number), request id for decide and diagnose (diagnose: a cheap model reads why it stopped, config diagnosis.*)")
    op.add_argument("option", nargs="?", default="",
                    help="the option to take, for decide; the accepted attempt to continue from, for continue-from")
    op.add_argument("--reason", default="", help="why (kept in the run's audit trail)")
    op.add_argument("--hold", action="store_true", help="leave the run stopped; `resume` releases it")
    op.add_argument("--confirm", action="store_true",
                    help="rework and revise: go ahead although it would throw away more accepted tasks than gates.rework_confirm_over")
    op.add_argument("--only", action="store_true",
                    help="rework: send back only the tasks named, not what depends on them")


def _heal(project: str, args: argparse.Namespace, rdir) -> int:
    """`scheduler-op REQ heal [status|stop|start|run|revert CASE]`: the owner's hand on the self-healing of one run."""
    import bt_scheduler_healing as healing

    what = args.target or "status"
    if what == "status":
        print(json.dumps(healing.status(rdir), indent=1, ensure_ascii=False))
    elif what == "stop":
        print(healing.stop(rdir))
    elif what == "start":
        print(healing.start(rdir))
    elif what == "run":
        print(f"healing cycle: {healing.cycle(project, args.req, rdir, log=print)} repair(s)")
    elif what == "revert":
        if not args.option:
            print("heal revert needs a case id: scheduler-op REQ heal revert <case> (see `heal status`)")
            return 2
        try:
            for line in healing.revert(project, args.req, rdir, args.option):
                print(line)
        except (ValueError, adapter.core.SchedulerError) as exc:
            print(exc)
            return 2
    else:
        print("heal takes status, stop, start, run or revert <case>")
        return 2
    return 0


def evolve(args: argparse.Namespace, project: str, pdir) -> int:
    """`scheduler-evolve`: the deterministic analysis of the project's interventions (see `bt_evolution`)."""
    from pathlib import Path

    import bt_config
    import bt_core
    import bt_evolution as evolution

    state_dir = Path(bt_core.STATE)
    replicas_dir = Path(pdir) / "replicas"
    if args.capture:
        import bt_scheduler_replica as replica
        rdir = bt_core.find_req(pdir, args.capture)
        replicas_dir.mkdir(parents=True, exist_ok=True)
        fixture = replica.extract(adapter.run_db_path(rdir), rdir / "PLAN.json", name=args.capture)
        target = replicas_dir / f"{args.capture}.json"
        target.write_text(json.dumps(fixture, indent=1, sort_keys=True), encoding="utf-8")
        print(f"replica of {args.capture} saved in {target} ({fixture['recorded']['attempts']} attempts)")
        return 0
    setter = bt_config.set_value
    if args.revert:
        for line in evolution.revert(state_dir, setter) or ["nothing to revert"]:
            print(line)
        return 0
    replicas = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(replicas_dir.glob("*.json"))]
    current = {key: bt_config.get(key) for key in ("scheduler.max_parallel_tasks", "scheduler.exclusive_scopes")}
    rows = evolution.collect(pdir)
    proposals = evolution.analyse(rows, plans=replicas, current=current)
    ab = evolution.propose_settings(replicas, current)
    print(json.dumps({"interventions": len(rows), "by_class": evolution.summary(rows), "proposals": proposals, "ab": ab},
                     indent=1, ensure_ascii=False, default=str))
    if args.apply:
        for line in evolution.apply_proven(ab, state_dir, setter) or ["nothing proven by the A/B: no setting changed"]:
            print(line)
    if args.propose:
        print("filed:", ", ".join(evolution.file_proposals(pdir, proposals)) or "nothing new")
    return 0


def dispatch(args: argparse.Namespace, project: str, pdir) -> int:
    from bt_core import find_req

    if args.cmd == "scheduler-evolve":
        return evolve(args, project, pdir)

    import bt_scheduler_ops as ops

    rdir = find_req(pdir, args.req)
    if args.cmd == "scheduler-watch":
        import bt_scheduler_watch
        return bt_scheduler_watch.watch(project, args.req, rdir, detach=args.detach)
    if adapter.authority(rdir) != adapter.AUTHORITY:
        print(f"{args.req} has no Scheduler run")
        return 2
    if args.action == "status":
        print(json.dumps(ops.status(project, args.req, rdir), indent=1))
        return 0
    if args.action == "recovery-preview":
        print(json.dumps(ops.recovery_preview(rdir), ensure_ascii=False, indent=1))
        return 0
    if args.action == "recovery-status":
        print(json.dumps(ops.recovery_status(rdir), ensure_ascii=False, indent=1))
        return 0
    if args.action == "decisions":
        import bt_scheduler_decisions as decisions
        print(decisions.render(decisions.open_requests(rdir), args.req))
        return 0
    if args.action == "diagnose":
        import bt_block_agent
        import bt_scheduler_decisions as decisions
        request = next((r for r in decisions.open_requests(rdir) if r["id"] == args.target), None)
        if request is None:
            print(f"no open request {args.target!r}")
            return 2
        result = bt_block_agent.diagnose(project, rdir, request, decisions.evidence(rdir, request))
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 0 if result["state"] == "done" else 1
    if args.action == "decide":
        import bt_scheduler_decisions as decisions
        if not args.target or not args.option:
            print("decide needs a request id and an option: scheduler-op REQ decide <request> <option> [--reason …]")
            return 2
        try:
            for line in decisions.answer(project, args.req, rdir, args.target, args.option, args.reason):
                print(line)
        except (ValueError, adapter.core.SchedulerError) as exc:
            print(exc)
            return 2
        return 0
    if args.action == "resume":
        print(ops.resume(project, args.req, rdir))
        return 0
    if args.action == "heal":
        return _heal(project, args, rdir)
    if args.action in {"cancel-attempt", "reopen", "retry", "rework", "withdraw-rework", "continue-from", "attest", "coordinator"} and not args.target:
        print(f"{args.action} needs a target (attempt id, or task id(s) for reopen, retry and rework)")
        return 2
    try:
        if args.action == "stop":
            ops.hold_path(rdir).write_text('{"why": "operator stop"}\n', encoding="utf-8")
            print(f"owner stopped: {ops.stop_owner(project, args.req)}; held — `scheduler-op {args.req} resume` releases it")
            return 0
        if args.action == "coordinator":
            import bt_coordinator

            for line in bt_coordinator.attest_task(project, args.req, rdir, args.target):
                print(line)
            print(ops.resume(project, args.req, rdir))
            return 0
        if args.action == "attest":
            for line in ops.attest(project, args.req, rdir, args.target, args.option, args.reason):
                print(line)
            print(ops.resume(project, args.req, rdir))
            return 0
        if args.action == "retry":
            for line in ops.retry(project, args.req, rdir, args.target, args.reason):
                print(line)
            print(ops.resume(project, args.req, rdir))
            return 0
        for line in ops.apply(project, args.req, rdir, args.action, args.target, args.reason, keep_held=args.hold,
                           only=args.only, option=args.option, confirm=args.confirm):
            print(line)
        if args.action in {"cancel-attempt", "reopen", "rework", "withdraw-rework", "continue-from", "revise", "remediate"}:
            import bt_interventions
            bt_interventions.record(rdir, kind="unknown", source="manual", task=args.target, evidence=args.reason,
                                    repair=f"scheduler-op {args.action} {args.target}".strip(), result="fixed",
                                    run=f"{project}-{args.req}")
    except adapter.core.SchedulerError as exc:
        print(f"{exc.code}: {exc}")
        ops.resume(project, args.req, rdir) if not args.hold else None
        return 2
    print("held" if args.hold else ops.resume(project, args.req, rdir))
    return 0
