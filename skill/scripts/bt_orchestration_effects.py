"""Deterministic approved actions; reasoning never receives native worker output."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import bt_runstate as rs
from bt_orchestration_actions import ActionEngine, ActionError
from bt_orchestration_context import encode
from bt_orchestration_storage import atomic_json
from bt_requirements_gate import require_ready


class Executor:
    def __init__(self, project: str, rdir: Path, state: dict, unit: list[dict], n: int,
                 workdir: Path, engine: ActionEngine) -> None:
        self.project, self.rdir, self.state = project, rdir, state
        self.unit, self.n, self.workdir, self.engine = unit, n, workdir, engine
        self.started = time.time()

    def reconcile(self, action: dict) -> dict:
        from bt_runsession import _gone
        state = rs.load(self.rdir)
        if any(not _gone(pid) for pid in (state.get('heartbeat', {}).get('session_pids') or {}).values()):
            raise ActionError('LIVE_DELEGATION: reconcile owned process before resumption')
        path = self._evidence_path(action)
        if path.exists():
            raw = path.read_bytes()
            if len(raw) > 8192:
                raise ActionError('OVERSIZED_RECONCILIATION_EVIDENCE')
            envelope = json.loads(raw)
            if (not isinstance(envelope, dict) or set(envelope) != {'identity', 'result'}
                    or envelope['identity'] != self._identity(action) or not isinstance(envelope['result'], dict)):
                raise ActionError('MISMATCHED_EFFECT_EVIDENCE')
            result = envelope['result']
            return {**result, 'evidence': str(path), 'recovered': True}
        if action['kind'] == 'delegate':
            dispatch = self._dispatch(action, state)
            task = rs.get_task(state, action['task'])
            report = self._report(dispatch['started_at']) if action['task'] == 'FINAL' else None
            claim = bool(task and task.get('claimed_done')) if task else report is not None
            return {**dispatch['route'], 'session': dispatch['session'], 'rc': None, 'early_exit': False,
                    'stopped': False, 'timed_out': False, 'report': report,
                    'ok': claim, 'recovered': True, 'code': 'INTERRUPTED_DELEGATION_NOT_REPLAYED_EXIT_UNKNOWN',
                    'evidence': str(self.rdir / 'RUN.json')}
        if action['kind'] == 'finish' and action['task'] == 'FINAL':
            self.engine._require_evidence('FINAL')
            return self(action)
        return {'ok': False, 'recovered': True, 'code': 'INTERRUPTED_EFFECT_NOT_REPLAYED'}

    def __call__(self, action: dict) -> dict:
        require_ready(self.rdir)
        kind, task_id = action['kind'], action['task']
        task = next((item for item in self.unit if item['id'] == task_id), None)
        if kind == 'read':
            return self._read(action)
        if kind == 'delegate':
            return self._delegate(action, task)
        if kind == 'verify':
            return self._verify(action, task)
        if kind == 'document':
            return self._document(action)
        if kind == 'finish':
            if task is not None:
                live = rs.get_task(rs.load(self.rdir), task_id)
                if not live.get('claimed_done'):
                    raise ActionError('UNVERIFIED_WORKER_CLAIM: worker must report completion')
            else:
                from bt_orchestration_completion import report_matches
                delegate = next(effect for effect in reversed(self.engine.active_effects())
                                if effect['action']['kind'] == 'delegate' and effect['action']['task'] == 'FINAL')
                binding = delegate['receipt'].get('report')
                if not report_matches(self.rdir, self.state['context_run_id'], binding):
                    raise ActionError('VALIDATED_FINAL_REPORT_REQUIRED')
                result = {'ok': True, 'report': binding}
                self._write_evidence(action, result)
                return result
            return {'ok': True}
        return {'ok': True, 'reason': 'explicit context rotation'}

    def _read(self, action: dict) -> dict:
        snapshot = require_ready(self.rdir)['snapshot']
        name = action['reference']
        if name not in snapshot['fingerprints']:
            raise ActionError('UNAPPROVED_READ_REFERENCE')
        path = self.rdir / name
        if path.is_symlink() or not path.resolve().is_relative_to(self.rdir.parents[1].resolve()):
            raise ActionError('UNSAFE_READ_REFERENCE')
        with path.open('rb') as stream:
            raw = stream.read(2001)
        if len(raw) > 2000:
            return {'ok': False, 'code': 'OVERSIZED_REFERENCE', 'reference': name,
                    'detail': 'Delegate scoped exploration; mandatory authority cannot be truncated.'}
        return {'ok': True, 'reference': name, 'text': raw.decode('utf-8')}

    def _delegate(self, action: dict, task: dict | None) -> dict:
        from bt_orchestration_context import build_package, byte_size
        from bt_runsession import run_session, session_route
        state = rs.load(self.rdir)
        if task and any(dependency not in self.engine.completed()
                        and (rs.get_task(state, dependency) or {}).get('status') != 'done'
                        for dependency in task.get('after', [])):
            return {'ok': False, 'code': 'DEPENDENCIES_NOT_FINISHED'}
        if state['sessions'] >= state['limits']['max_sessions']:
            return {'ok': False, 'code': 'DELEGATION_SESSION_CAP'}
        unit = [task] if task else []
        route = session_route(self.project, state, task, unit)
        recorded_route = {key: route.get(key) for key in ('agent', 'profile', 'model', 'effort', 'kind', 'tier')}
        self._validate_route(recorded_route)
        dispatched_at = time.time()
        def reserve(current):
            if current['sessions'] >= current['limits']['max_sessions']:
                raise ActionError('DELEGATION_SESSION_CAP')
            current['sessions'] += 1
            if task:
                live = rs.get_task(current, task['id'])
                live.pop('claimed_done', None)
                live['status'] = 'in_progress'
            current.setdefault('orchestration_delegations', {})[self._key(action)] = {
                'identity': self._identity(action), 'session': current['sessions'],
                'route': recorded_route, 'started_at': dispatched_at}
        state = rs.update(self.rdir, reserve)
        delegate_n = state['sessions']
        package = build_package(self.rdir, state, unit, self.engine.milestone, self.engine.budget.policy)
        package['delegation'] = {'id': action['action_id'], 'ownership': sorted(self.engine.ids & {action['task']}),
                                 'brief': action['text'],
                                 'constraints': 'No commits, push, merge, deletion, global installation/configuration '
                                 'or security/credential changes. Preserve concurrent edits. '
                                 'Return only assigned task verdicts and persist verification/documentation.'}
        if byte_size(package) > self.engine.budget.policy.entry_bytes:
            raise ActionError('OVERSIZED_DELEGATION_BRIEF')
        if (rs.load(self.rdir) or {}).get('control') == 'stop':
            raise ActionError('USER_STOP: native worker was not dispatched')
        info = run_session(self.project, self.rdir, state, task, delegate_n, self.workdir, None, unit, route,
                           prompt_override=encode(package), execution_policy='restricted-v1')
        # Full logs stay in the existing session log. Receipts contain only the
        # outcome and exact evidence reference, never raw worker conversations.
        path = self._evidence_path(action)
        receipt = {key: info.get(key) for key in ('rc', 'stopped', 'timed_out', 'early_exit', 'agent', 'profile', 'model', 'effort')}
        receipt['session'] = delegate_n
        report = self._report(dispatched_at) if task is None else None
        claimed = bool((rs.get_task(rs.load(self.rdir), task['id']) or {}).get('claimed_done')) if task else report is not None
        receipt['ok'] = (info['rc'] == 0 or (info.get('early_exit') and claimed)) and not info.get('stopped') and not info.get('timed_out')
        receipt['report'] = report
        self._write_evidence(action, receipt)
        return {**receipt, 'evidence': str(path), 'session': delegate_n,
                'ownership': [task['id']] if task else ['FINAL']}

    def _verify(self, action: dict, task: dict | None) -> dict:
        from bt_orchestration_verify import run_check
        from bt_runsettle import verify_task
        evidence = self._evidence_path(action).with_suffix('.log')
        check = lambda command, cwd: run_check(command, cwd, evidence, self.project, self.rdir, self.state)
        if task:
            ok, detail = verify_task(self.project, task, self.workdir, rs.load(self.rdir), run_check=check)
        else:
            results = [verify_task(self.project, member, self.workdir, rs.load(self.rdir), run_check=check)
                       for member in self.state['tasks'] if not member.get('synthetic')]
            ok = all(result[0] for result in results)
            detail = '\n'.join(result[1] for result in results if not result[0])
        path = self._evidence_path(action)
        self._write_evidence(action, {'ok': ok, 'detail': detail})
        # A large error is referenced and rejected; never erase decisive errors
        # simply to fit a receipt into the reasoning boundary.
        return {'ok': ok, 'detail': detail, 'evidence': str(path)}

    def _document(self, action: dict) -> dict:
        path = self._evidence_path(action)
        self._write_evidence(action, {'ok': True, 'task': action['task'], 'summary': action['text'],
                                     'completed': self.engine.completed(), 'effects': str(self.engine.path)})
        return {'ok': True, 'evidence': str(path)}

    def _evidence_path(self, action: dict) -> Path:
        digest = self._key(action)
        return self.rdir / f'ORCHESTRATION-{digest}.json'

    def _identity(self, action: dict) -> dict:
        return {'schema': 1, 'run_id': self.state['context_run_id'], 'milestone': self.engine.milestone,
                'task': action['task'], 'action_digest': hashlib.sha256(encode(action).encode()).hexdigest()}

    def _key(self, action: dict) -> str:
        return hashlib.sha256(encode(self._identity(action)).encode()).hexdigest()

    def _write_evidence(self, action: dict, result: dict) -> None:
        atomic_json(self._evidence_path(action), {'identity': self._identity(action), 'result': result})

    def _report(self, started_at: float) -> dict | None:
        from bt_orchestration_completion import report_binding
        return report_binding(self.rdir, self.state['context_run_id'], started_at=started_at)

    def _validate_route(self, route: dict) -> None:
        import bt_profiles
        if (set(route) != {'agent', 'profile', 'model', 'effort', 'kind', 'tier'}
                or route['agent'] not in bt_profiles.LAUNCHABLE or type(route['tier']) is not int
                or not 0 <= route['tier'] <= 3):
            raise ActionError('INVALID_DURABLE_WORKER_ROUTE')
        for field in ('profile', 'model', 'effort', 'kind'):
            value = route[field]
            if value is not None and (not isinstance(value, str) or not 0 < len(value) <= 128):
                raise ActionError('INVALID_DURABLE_WORKER_ROUTE')
        if route['profile']:
            bt_profiles.authorize(route['profile'], self.project)
            if bt_profiles.provider_of(route['profile']) != route['agent']:
                raise ActionError('MISMATCHED_DURABLE_WORKER_PROFILE')

    def _dispatch(self, action: dict, state: dict) -> dict:
        import math
        dispatch = state.get('orchestration_delegations', {}).get(self._key(action))
        if (not isinstance(dispatch, dict) or set(dispatch) != {'identity', 'session', 'route', 'started_at'}
                or dispatch['identity'] != self._identity(action) or type(dispatch['session']) is not int
                or not 1 <= dispatch['session'] <= state['sessions']
                or type(dispatch['started_at']) not in (float, int) or not math.isfinite(dispatch['started_at'])
                or not isinstance(dispatch['route'], dict)):
            raise ActionError('UNVERIFIED_DURABLE_DELEGATION')
        self._validate_route(dispatch['route'])
        return dispatch
