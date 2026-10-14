"""Supervisor entry, capability preflight and runtime selection."""
from __future__ import annotations

from pathlib import Path

from bt_runloop import run_loop
from bt_runutil import keep_awake


def isolation_of(state: dict | None, options: dict) -> str:
    import bt_config
    if options.get('isolation') is not None:
        return options['isolation']
    return state.get('limits', {}).get('isolation', 'off') if state else bt_config.get('run.isolation', 'off')


def supervise(project: str, req: str, **options) -> int:
    import bt_run as engine
    from bt_requirements_gate import require_ready

    rdir = engine.find_req(engine.ROOT / project, req)
    from bt_scheduler_adapter import refuse_legacy_run
    refuse_legacy_run(rdir)            # one authority per requirement: a scheduler-owned run is not ours to take over
    require_ready(rdir)
    existing = engine.rs.load(rdir)
    runtime = None
    if existing and existing.get('orchestration_mode') == 'foreground-v1' and not options.get('foreground'):
        raise SystemExit('FOREGROUND_RESUME_REQUIRED: resume with --foreground; native fallback is forbidden')
    if options.get('foreground'):
        from bt_orchestration_terminal import (
            TerminalError,
            configured_runtime,
            preflight,
        )
        try:
            runtime = preflight(options.get('foreground_runtime') or configured_runtime())
        except TerminalError as exc:
            raise SystemExit(str(exc)) from exc
        if require_ready(rdir)['status'] != 'ready':
            raise SystemExit('FOREGROUND_REQUIREMENTS_REQUIRED: record requirements-v1 authority first')
        limits = (existing or {}).get('limits', {})
        workers = options.get('workers') or limits.get('workers', 1)
        isolation = isolation_of(existing, options)
        if options.get('agent_cmd') or workers != 1 or isolation == 'worktree':
            raise SystemExit('FOREGROUND_SERIAL_REQUIRED: one coordinator; worker isolation belongs to its delegates')
    if existing and existing['status'] == 'done':
        print(f"{existing['req']} already finished (RUN.json status done).")
        return 0
    state = engine._open(project, rdir, options)
    if state is None:
        return 1
    if runtime:
        from bt_orchestration_identity import recover
        from bt_orchestration_runtime import adopt_run
        recover(rdir, project, state)
        state = adopt_run(rdir, state)
        state = engine.rs.update(rdir, lambda current: current.update(orchestration_mode='foreground-v1'))
    once, agent_cmd = bool(options.get('once')), options.get('agent_cmd')
    install = not once and not agent_cmd and not runtime and not options.get('no_autostart')
    if install:
        engine.autostart('install', project, state['req'])
    keep_awake()
    workdir = engine.ws.workdir(engine.ROOT, project) or (Path.cwd() if agent_cmd else None)
    if workdir is None:
        raise SystemExit(f"No repos registered for '{project}': bitacora.py --project {project} workspace add <role> <path>")
    who = f"pool {', '.join(state['pool'])}" if state.get('pool') else f"{state['agent']}/{state['model']}"
    engine.say(state, f"{project} {state['req']} marathon started ({who}, "
               f"ultracode={state['ultracode']}, workdir {workdir})")
    ctx = {'install': install, 'once': once, 'agent_cmd': agent_cmd, 'workdir': workdir, 'notified_wait': False}
    if runtime:
        ctx['foreground_runtime'] = runtime
    return run_loop(project, rdir, state, ctx, engine._step, engine._reset_in_progress)
