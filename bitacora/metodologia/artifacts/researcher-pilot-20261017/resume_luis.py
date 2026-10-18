"""Owner-authorized profile override for only the ten never-invoked cells."""
import argparse
import fcntl
import json
import subprocess
import tempfile
from pathlib import Path

import run as frozen_runner
from native import ROOT, environment, wrapper

CONT = ROOT / 'continuation-codex-luis'


def read(path):
    return json.loads(path.read_text())


def verify_originals():
    frozen_runner.verify()
    for name, wanted in read(ROOT / 'original-evidence-hashes.json').items():
        if frozen_runner.digest((ROOT / name).read_bytes()) != wanted:
            raise RuntimeError('Original evidence changed: ' + name)


def eligible(originals, pending):
    all_ids = {c['id'] + '-' + r['id'] for c in read(ROOT / 'cases.json') for r in read(ROOT / 'protocol.json')['routes']}
    attempted = {k for k, r in originals.items() if 'workspace_before' in r}
    wanted = {row['cell'] for row in pending}
    if len(wanted) != len(pending) or wanted != all_ids - attempted:
        raise RuntimeError('Pending queue must be exactly the never-invoked cells')
    if len(attempted) != 8 or len(wanted) != 10:
        raise RuntimeError('Expected original eight calls and ten pending cells')
    if any(row['route']['provider'] != 'codex' or row['case'] == 'R1' for row in pending):
        raise RuntimeError('Only original pending Codex R2-R6 cells are authorized')
    return wanted


def originals():
    return {p.stem: read(p) for p in (ROOT / 'results').glob('*.json')}


def ordered(pending):
    return sorted(pending, key=lambda row: (row['case'],
        row['route']['id'] == ('sol-medium' if int(row['case'][1:]) % 2 == 0 else 'luna-high')))


def validate():
    verify_originals()
    pending = read(ROOT / 'pending-cells.json')
    eligible(originals(), pending)
    expected_order = ['R2-luna-high', 'R2-sol-medium', 'R3-sol-medium', 'R3-luna-high',
                      'R4-luna-high', 'R4-sol-medium', 'R5-sol-medium', 'R5-luna-high',
                      'R6-luna-high', 'R6-sol-medium']
    if [r['cell'] for r in ordered(pending)] != expected_order:
        raise AssertionError('Route order must alternate by case')
    mutant = {**originals(), pending[0]['cell']: {'workspace_before': {}}}
    try:
        eligible(mutant, pending)
    except RuntimeError:
        pass
    else:
        raise AssertionError('Would repeat a started call')
    route = {**pending[0]['route'], 'profile': 'codex-luis'}
    env = environment(route)
    with tempfile.TemporaryDirectory(prefix='researcher-luis-smoke-') as tmp:
        args = wrapper(route, Path(tmp), 'frozen', env)
        args = args[:args.index('--die-with-parent') + 1] + ['/bin/sh', '-c',
            'test ! -e /home/david/bitacora/metodologia/artifacts/researcher-pilot-20261017/rubric.json && test -w /tmp/work && echo SANDBOX_OK']
        proc = subprocess.run(args, env=env, capture_output=True, text=True, timeout=20, check=False)
        if proc.returncode != 0 or 'SANDBOX_OK' not in proc.stdout:
            raise RuntimeError('Sandbox profile smoke failed: ' + proc.stderr[:500])
    frozen_runner.save(CONT / 'validation.json', {'eligible_cells': 10, 'original_calls': 8,
        'duplicate_attempt_mutant_rejected': True, 'codex_luis_sandbox_smoke': True,
        'alternating_case_order': expected_order, 'native_calls': 0})
    print('VALIDATION PASS:10 never-invoked cells; no native calls')


def freeze():
    verify_originals()
    path = CONT / 'authorization.json'
    if path.exists():
        raise RuntimeError('Continuation is already authorized/frozen')
    fixed = ['resume_luis.py', 'pending-cells.json', 'original-evidence-hashes.json', 'protocol.json']
    frozen_runner.save(path, {'schema_version': 1, 'authorization': 'Owner: utiliza codex-luis after the partial8/18 Researcher pilot.',
        'profile_override': {'from': 'codex-2', 'to': 'codex-luis'},
        'total_native_cap': 18, 'original_native_calls': 8, 'additional_native_cap': 10,
        'pending_cells': read(ROOT / 'pending-cells.json'),
        'frozen_hashes': {name: frozen_runner.digest((ROOT / name).read_bytes()) for name in fixed},
        'unchanged': ['cases', 'rubric', 'source extracts', 'prompts', 'models', 'efforts', 'commands', 'deadlines'],
        'output': 'Separate continuation results/submissions; original preflight and native evidence preserved.',
        'comparison_caveat': 'Sol/Luna R1 on codex-2, R2-R6 on codex-luis; report effective profiles per cell, no quota equivalence.'})
    print('Frozen owner-authorized codex-luis continuation')


def execute():
    verify_originals()
    auth = read(CONT / 'authorization.json')
    for name, wanted in auth['frozen_hashes'].items():
        if frozen_runner.digest((ROOT / name).read_bytes()) != wanted:
            raise RuntimeError('Continuation authorization drift: ' + name)
    pending = auth['pending_cells']
    eligible(originals(), pending)
    cases = {c['id']: c for c in read(ROOT / 'cases.json')}
    queue = ordered(pending)
    outcome = {'provider': 'codex', 'profile': 'codex-luis', 'status': 'complete'}
    # Reuse the exact frozen collector in this isolated interpreter. Only its
    # output root changes; native isolation, prompts and commands stay frozen.
    prior_root = frozen_runner.ROOT
    try:
        frozen_runner.ROOT = CONT
        for entry in queue:
            route = {**entry['route'], 'profile': 'codex-luis'}
            row = frozen_runner.run_one(cases[entry['case']], route)
            if row.get('limit_detected') or row['status'] != 'completed':
                outcome.update(status='stopped', cell=entry['cell'], reason=row['status'])
                break
    finally:
        frozen_runner.ROOT = prior_root
    frozen_runner.save(CONT / 'execution-summary.json', outcome)
    verify_originals()
    print('CONTINUATION', json.dumps(outcome), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'freeze', 'run'])
    action = parser.parse_args().action
    if action == 'validate':
        validate()
    elif action == 'freeze':
        freeze()
    else:
        with (ROOT / 'execution.lock').open('a') as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            execute()
