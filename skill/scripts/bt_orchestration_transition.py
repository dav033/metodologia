"""Approved planning-to-foreground transition through the existing relay parent."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import uuid
from pathlib import Path

import bt_core as core
import bt_orchestration_terminal as terminal
import bt_plan_adapter as plan_adapter
import bt_relay as relay
import bt_relay_client as client
import bt_relay_launch as launcher
import bt_requirements_gate as gate
import bt_runstate as state_


def require_new_plan(rdir: Path) -> None:
    """Refuse a successor that cannot start before ending its planning session."""
    import bt_scheduler_adapter
    if not (rdir / 'PLAN.json').is_file():
        raise terminal.TerminalError('FOREGROUND_PLAN_REFUSED: PLAN_NOT_FROZEN: frozen PLAN.json required')
    if bt_scheduler_adapter.authority(rdir) != 'none':
        raise terminal.TerminalError('FOREGROUND_RUN_EXISTS: inspect existing state; no duplicate was started')


def successor_argv(project: str, req: str) -> list[str]:
    """The successor runs the Scheduler owner process in its own terminal; it takes no routing flags."""
    return [sys.executable, str(Path(__file__).with_name('bitacora.py')), '--project', project,
            'scheduler-run', req, '--no-autostart']


def prepare(handoff: Path, spec: dict, session: str, facts: dict) -> str:
    """The helper waits for verified turn end before claiming/writing the successor.

    No multiplexer fallback: a missing or changed direct-parent proof never signals
    a client and never types a command into a possibly active provider session.
    """
    if (not relay.valid_session(session) or not isinstance(spec.get('argv'), list)
            or not spec['argv'] or any(not isinstance(arg, str) or not arg or '\0' in arg for arg in spec['argv'])
            or not Path(spec['argv'][0]).is_absolute()
            or not os.access(spec['argv'][0], os.X_OK) or not Path(spec.get('cwd', '')).is_dir()):
        raise launcher.Refused('invalid foreground successor/session')
    wrapper = facts.get('wrapper')
    if (not isinstance(wrapper, dict)
            or any(type(value) is not int or value < 1 for value in
                   (facts.get('pid'), facts.get('start'), wrapper.get('pid'), wrapper.get('start')))
            or not client.verify_wrapper(facts['pid'], facts['start'], wrapper['pid'], wrapper['start'])):
        raise launcher.Refused('no compatible relay parent; current session was left intact')
    if (relay.relay_dir() / f"next-{wrapper['pid']}.json").exists():
        raise launcher.Refused('a successor is already prepared for this parent; current session was left intact')
    return launcher.run_wrapper(handoff, 'foreground-supervisor', spec['cwd'], session,
                                facts['pid'], facts['start'], (wrapper['pid'], wrapper['start']),
                                True, successor=spec)


def launch(project: str, req: str, *, dry_run: bool = False, profile: str | None = None,
           model: str | None = None, session: str | None = None) -> dict:
    if profile is not None or model is not None:
        raise terminal.TerminalError('SCHEDULER_ROUTING_REQUIRED: the Scheduler selects model and account through M2')
    rdir = core.find_req(core.ROOT / project, req)
    if gate.require_ready(rdir)['status'] != 'ready':
        raise terminal.TerminalError('FOREGROUND_REQUIREMENTS_REQUIRED: record requirements-v1 authority first')
    if core._front(rdir / 'PLAN.md', 'status') != 'approved':
        raise terminal.TerminalError('FOREGROUND_APPROVAL_REQUIRED: PLAN.md must be approved')
    require_new_plan(rdir)
    existing = state_.load(rdir)
    if existing and existing.get('status') in ('running', 'paused', 'waiting') and not state_.is_stale(existing, 3):
        raise terminal.TerminalError('FOREGROUND_RUN_EXISTS: inspect the existing run; no duplicate was started')
    workdir = core.ws.workdir(core.ROOT, project)
    if not workdir or not workdir.is_dir():
        raise terminal.TerminalError('FOREGROUND_WORKSPACE_REQUIRED')
    import bt_scheduler_adapter
    problem = plan_adapter.launch_problem(
        rdir, freeze=not dry_run,
        compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir),
    )  # same gate as every other launch path
    if problem:
        raise terminal.TerminalError('FOREGROUND_PLAN_REFUSED: ' + problem)
    argv = successor_argv(project, req)
    command = ('cd ' + shlex.quote(str(workdir)) + ' && env BITACORA_ROOT=' + shlex.quote(str(core.ROOT))
               + ' ' + shlex.join(argv))
    session = session or os.environ.get('CLAUDE_CODE_SESSION_ID')
    provider = 'claude' if os.environ.get('CLAUDE_CODE_SESSION_ID') else 'codex'
    facts = client.locate(dict(os.environ), session, provider)
    result = {'project': project, 'req': req, 'mode': 'foreground', 'command': command,
              'decision': 'manual', 'reason': facts.get('why'), 'activated': False}
    if not facts.get('wrapper') or not session or not relay.valid_session(session):
        return result
    # Never end a planner for a successor whose reasoning boundary is not yet available.
    terminal.preflight(terminal.configured_runtime())
    if dry_run:
        return {**result, 'decision': 'would_prepare'}
    request = relay.relay_dir() / ('foreground-' + uuid.uuid4().hex + '.json')
    relay.write_private(request, json.dumps({'schema': 1, 'project': project, 'req': req, 'session': session, 'facts': facts,
                                            'spec': {'argv': argv, 'cwd': str(workdir), 'env': {}, 'unset': []}}))
    with open(os.open(relay.relay_dir() / 'foreground.log', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600), 'ab') as out:
        subprocess.Popen([sys.executable, str(Path(__file__)), str(request)], stdin=subprocess.DEVNULL,
                         stdout=out, stderr=out, start_new_session=True)
    return {**result, 'decision': 'prepared', 'request': str(request),
            'reason': 'helper will wait for the turn-ended marker and reverify the parent before replacement'}


def main() -> int:
    request = Path(sys.argv[1])
    try:
        fd = os.open(request, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            stat = os.fstat(stream.fileno())
            if stat.st_uid != os.getuid() or stat.st_mode & 0o077 or stat.st_size > 16384:
                raise terminal.TerminalError('INVALID_TRANSITION_REQUEST: ownership/mode/size')
            data = json.loads(stream.read(16385))
        if (not isinstance(data, dict) or set(data) != {'schema', 'project', 'req', 'session', 'facts', 'spec'}
                or type(data.get('schema')) is not int or data['schema'] != 1):
            raise terminal.TerminalError('INVALID_TRANSITION_REQUEST: schema')
        if any(not isinstance(data[key], str) or not data[key] for key in ('project', 'req', 'session')):
            raise terminal.TerminalError('INVALID_TRANSITION_REQUEST: identity')
        if (not isinstance(data['spec'], dict) or not isinstance(data['facts'], dict)
                or not isinstance(data['spec'].get('argv'), list)
                or any(not isinstance(arg, str) or not arg or '\0' in arg for arg in data['spec']['argv'])
                or not isinstance(data['spec'].get('cwd'), str)
                or data['spec'].get('env') != {} or data['spec'].get('unset') != []):
            raise terminal.TerminalError('INVALID_TRANSITION_REQUEST: process contract')
        rdir = core.find_req(core.ROOT / data['project'], data['req'])
        if gate.require_ready(rdir)['status'] != 'ready' or core._front(rdir / 'PLAN.md', 'status') != 'approved':
            raise terminal.TerminalError('FOREGROUND_APPROVAL_REQUIRED: authority changed before transition')
        require_new_plan(rdir)
        import bt_scheduler_adapter
        problem = plan_adapter.launch_problem(
            rdir, freeze=False,
            compatibility_report=bt_scheduler_adapter.plan_compatibility_report(rdir),
        )  # the plan must still be the approved revision
        if problem:
            raise terminal.TerminalError('FOREGROUND_PLAN_REFUSED: ' + problem)
        prefix = successor_argv(data['project'], data['req'])
        if data['spec']['argv'][:len(prefix)] != prefix:
            raise terminal.TerminalError('INVALID_TRANSITION_REQUEST: successor checkout')
        # The detached helper has no TTY; capability validation was done by the foreground caller.
        runtime = terminal.configured_runtime()
        if runtime is None:
            raise terminal.TerminalError('FOREGROUND_RUNTIME_NOT_ACTIVATED')
        runtime.check_capabilities()
        print(prepare(request, data['spec'], data['session'], data['facts']), flush=True)
        return 0
    except (OSError, ValueError, KeyError, launcher.Refused) as exc:
        print(f'foreground transition refused: {exc}; current session was left intact', file=sys.stderr, flush=True)
        return 2


if __name__ == '__main__':
    sys.exit(main())
