"""Durable no-retry execution of the owner-authorized 24 Runner cells."""
import argparse
import fcntl
import json
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from native import (
    BASE,
    ROOT,
    ROUTES,
    bt_subscriptions,
    commands,
    digest,
    environment,
    invoke,
    quota,
    save,
    wrapper,
)
from prepare import CASES, FIXTURE, prepare, prompt


def materialize(cwd, case):
    (cwd / 'check.py').write_text(FIXTURE)
    (cwd / 'TASK.md').write_text(prompt(case))


def files(cwd):
    return {str(p.relative_to(cwd)): digest(p.read_bytes()) for p in cwd.rglob('*') if p.is_file() and not p.is_symlink()}


def quota_blocked(data):
    return data.get('status') in (401, 403, 429, 'http_401', 'http_403', 'http_429', 'auth', 'challenge',
                                  'challenge_required', 'auth_unavailable', 'invalid_credentials',
                                  'manual_challenge', 'rate_limited')


def validate():
    if (ROOT / 'protocol.json').exists():
        raise RuntimeError('Validation cannot regenerate frozen cases')
    prepare()
    baseline = []
    for case in CASES:
        with tempfile.TemporaryDirectory(prefix='runner-baseline-') as tmp:
            cwd = Path(tmp)
            materialize(cwd, case)
            codes = []
            for command in case['commands']:
                p = subprocess.run(['/bin/bash', '-c', command], cwd=cwd, capture_output=True, text=True, timeout=12, check=False)
                codes.append(p.returncode)
            assert codes == case['exits'], (case['id'], codes)
            events = [json.loads(line) for line in (cwd / '.runner-events.jsonl').read_text().splitlines()]
            assert [e['mode'] for e in events if e['event'] == 'start'] == case['modes']
            if case['id'] == 'N4':
                body = (cwd / 'logs/long.log').read_text()
                assert 'TS2322' in body and len(body.splitlines()) == 1801
            baseline.append({'case': case['id'], 'exits': codes, 'events': events})
    smokes = []
    for route in ROUTES:
        with tempfile.TemporaryDirectory(prefix='runner-sandbox-') as tmp:
            cwd = Path(tmp)
            materialize(cwd, CASES[0])
            env = environment(route)
            argv = wrapper(route, cwd, env)
            shell = 'test ! -e ' + str(ROOT / 'rubric.json') + ' && test ! -w /tmp/work/check.py && test ! -w /tmp/work/TASK.md && test -w /tmp/work && python /tmp/work/check.py success'
            smoke = subprocess.run(argv[:argv.index('--die-with-parent') + 1] + ['/bin/sh', '-c', shell],
                                   env=env, capture_output=True, text=True, timeout=20, check=False)
            assert smoke.returncode == 0, (route['id'], smoke.stderr)
            smokes.append(route['id'])
    # Native parsers must retain actual tool evidence and discard thinking.
    from native import evidence
    synthetic = '\n'.join(json.dumps(v) for v in [
        {'type': 'item.completed', 'item': {'type': 'command_execution', 'command': 'python check.py success', 'exit_code': 0, 'aggregated_output': '12 tests passed'}},
        {'message': {'content': [{'type': 'thinking', 'thinking': 'private'}, {'type': 'tool_result', 'content': 'exit3', 'tool_use_id': 'one'}]}}])
    kept = evidence(synthetic)
    assert len(kept) == 2 and 'private' not in json.dumps(kept)
    with (ROOT / 'execution.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        conflict = subprocess.run(['python', '-c', 'import fcntl,sys; f=open(sys.argv[1],"a"); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)', str(ROOT / 'execution.lock')], capture_output=True, text=True, timeout=10, check=False)
        assert conflict.returncode != 0 and 'BlockingIOError' in conflict.stderr
    guards = ['auth_unavailable', 'invalid_credentials', 'manual_challenge', 'http_429', 401, 403, 429]
    for status in guards:
        with tempfile.TemporaryDirectory(prefix='runner-auth-guard-') as tmp, patch.dict(
            globals(), {'ROOT': Path(tmp), 'quota': lambda route, s=status: {'status': s},
                        'invoke': lambda *args: (_ for _ in ()).throw(AssertionError('native invocation forbidden'))}
        ):
            row = run_one(CASES[0], ROUTES[0])
            assert row['status'] == 'quota_auth_blocked' and 'workspace_before' not in row
    save(ROOT / 'validation.json', {'baseline': baseline, 'sandbox_profiles': smokes,
                                   'tool_evidence_without_thinking': True, 'lock_conflict': True,
                                   'auth_challenge_guard_statuses': guards, 'native_calls': 0})
    print('VALIDATION PASS:6 subprocess cases,4 sandbox smokes,tool evidence,process lock; zero native calls')


def freeze():
    if (ROOT / 'protocol.json').exists():
        raise RuntimeError('Protocol already frozen')
    fixed = ['PLAN.md', 'prepare.py', 'native.py', 'run.py', 'cases.json', 'rubric.json', 'validation.json']
    hashes = {name: digest((ROOT / name).read_bytes()) for name in fixed}
    dependencies = {str(BASE / name): digest((BASE / name).read_bytes()) for name in ('pilot_common.py', 'pilot_native.py')}
    scripts = Path('/home/david/dev/metodologia/skill/scripts')
    dependencies.update({str(scripts / name): digest((scripts / name).read_bytes()) for name in ('bt_usage.py', 'bt_profiles.py', 'bt_quota_live.py', 'bt_subscriptions.py')})
    versions = {name: subprocess.run([name, '--version'], capture_output=True, text=True, timeout=15, check=True).stdout.strip() for name in ('codex', 'claude', 'bwrap', 'python', 'timeout')}
    save(ROOT / 'protocol.json', {'schema_version': 1, 'authorization': 'Owner: haz las prubas, tambien intentemos con sonnet medium',
         'planned_calls': 24, 'repetitions': 1, 'cases': 6, 'criteria_per_case': 6, 'routes': ROUTES,
         'deadline_seconds': 300, 'max_claude_turns': 25, 'account_concurrency': 1, 'provider_lanes': 2,
         'frozen_at': time.time(), 'frozen_hashes': hashes, 'dependency_hashes': dependencies,
         'prompt_hashes': {c['id']: digest(prompt(c).encode()) for c in CASES},
         'native_commands': {r['id']: commands(r) for r in ROUTES}, 'versions': versions,
         'limits': ['No retry/repair/substitution/account rotation or automatic quota wait.',
                    'Stop affected lane on limit/auth/challenge/collector failure; preserve all records.',
                    'No role/runtime rollout, commit or push.',
                    'One sample per case; missing usage/effective identity stays unknown; tokens are not invoices/quota equivalents.',
                    'Fixture start/end logs are corroborated with native tool evidence; sandbox blocks fixture edits. This is not a malicious-agent security benchmark.']})
    print('FROZEN24-call protocol')


def verify():
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    for name, wanted in protocol['frozen_hashes'].items():
        assert digest((ROOT / name).read_bytes()) == wanted, name
    for name, wanted in protocol['dependency_hashes'].items():
        assert digest(Path(name).read_bytes()) == wanted, name
    for case in json.loads((ROOT / 'cases.json').read_text()):
        assert digest(prompt(case).encode()) == protocol['prompt_hashes'][case['id']]
    return protocol


def run_one(case, route):
    target = ROOT / 'results' / f'{case["id"]}-{route["id"]}.json'
    if target.exists():
        return json.loads(target.read_text())
    row = {'schema_version': 1, 'case': case['id'], 'route': route, 'status': 'prepared',
           'started_at': time.time(), 'prompt_sha256': digest(prompt(case).encode())}
    row['quota_before'] = quota(route)
    pressure, _ = bt_subscriptions.capacity(row['quota_before'], 'sonnet' if route['provider'] == 'claude' else route['model'])
    row['quota_pressure_before'] = pressure
    if pressure is not None and pressure >= 100:
        row['status'] = 'quota_exhausted'
        save(target, row)
        return row
    if quota_blocked(row['quota_before']):
        row['status'] = 'quota_auth_blocked'
        save(target, row)
        return row
    with tempfile.TemporaryDirectory(prefix='runner-cell-') as tmp:
        cwd = Path(tmp)
        materialize(cwd, case)
        row['workspace_before'] = files(cwd)
        row['status'] = 'running'
        save(target, row)
        print('START', target.stem, flush=True)
        try:
            row.update(invoke(route, cwd, prompt(case)))
            output = ROOT / 'submissions' / target.stem
            shutil.copytree(cwd, output, symlinks=True)
            row['workspace_after'] = files(cwd)
            row['scope_violations'] = [name for name, wanted in row['workspace_before'].items()
                                       if row['workspace_after'].get(name) != wanted]
            row['scope_violations'] += ['symlink:' + str(p.relative_to(cwd)) for p in cwd.rglob('*') if p.is_symlink()]
            allowed = {'.runner-events.jsonl', *row['workspace_before'], *('logs/' + m + '.log' for m in case['modes'])}
            row['unexpected_files'] = sorted(set(row['workspace_after']) - allowed)
            row['fixture_events'] = [json.loads(line) for line in (cwd / '.runner-events.jsonl').read_text().splitlines()] if (cwd / '.runner-events.jsonl').is_file() else []
        except (OSError, ValueError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
            row.update(status='collector_error', error_type=type(exc).__name__, error=str(exc)[:1000])
        save(target, row)
        row['quota_after'] = quota(route)
        row['finished_at'] = time.time()
        save(target, row)
    print('DONE', target.stem, row['status'], row.get('seconds'), flush=True)
    return row


def lane(provider):
    routes = [r for r in ROUTES if r['provider'] == provider]
    for index, case in enumerate(json.loads((ROOT / 'cases.json').read_text())):
        for route in routes if index % 2 == 0 else list(reversed(routes)):
            row = run_one(case, route)
            if row.get('limit_detected') or row['status'] not in ('completed',):
                return {'provider': provider, 'status': 'stopped', 'cell': case['id'] + '-' + route['id'], 'reason': row['status']}
    return {'provider': provider, 'status': 'complete'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'freeze', 'verify', 'run', 'quota'])
    action = parser.parse_args().action
    if action == 'validate':
        validate()
    elif action == 'freeze':
        freeze()
    elif action == 'verify':
        verify()
        print('Frozen hashes valid')
    elif action == 'quota':
        for provider in ('codex', 'claude'):
            route = next(r for r in ROUTES if r['provider'] == provider)
            data = quota(route)
            print(route['profile'], json.dumps(data))
    else:
        with (ROOT / 'execution.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            verify()
            with ThreadPoolExecutor(max_workers=2) as executor:
                result = list(executor.map(lane, ('claude', 'codex')))
            save(ROOT / 'execution-summary.json', result)
            print('LANES', json.dumps(result), flush=True)
