"""Run the owner-approved 8-by-6 native implementation matrix once."""
from __future__ import annotations

import argparse
import difflib
import json
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pilot_common import (
    INSTRUCTION,
    ROOT,
    ROUTES,
    bt_subscriptions,
    cases,
    digest,
    file_map,
    materialize,
    save,
)
from pilot_grade import grade, run_tests
from pilot_native import commands, invoke, quota


def validate() -> list[dict]:
    rows = []
    for case in cases():
        row = {'case': case['id']}
        for name in ('starter', 'reference'):
            with tempfile.TemporaryDirectory(prefix='implementer-validation-') as directory:
                root = Path(directory)
                files = {**case['starter'], **(case['reference'] if name == 'reference' else {})}
                materialize(root, {**files, **case['private_tests']})
                row[name] = run_tests(root)
        assert row['reference']['status'] == 'passed', row
        assert row['starter']['status'] == 'failed', row
        assert not any(s in row['starter']['output'] for s in
                       ('ModuleNotFoundError', 'ImportError', 'SyntaxError')), row
        rows.append(row)
    save(ROOT / 'validation.json', rows)
    return rows


def freeze() -> dict:
    assert not (ROOT / 'protocol.json').exists(), 'Already frozen; do not overwrite'
    validation = validate()
    all_cases = cases()
    assert [c['id'] for c in all_cases] == ['I1', 'I2', 'I3', 'I4', 'I5', 'I6']
    save(ROOT / 'cases.json', all_cases)
    versions = {}
    for binary in ('codex', 'claude', 'bwrap'):
        p = subprocess.run([binary, '--version'], capture_output=True, text=True, timeout=15, check=False)
        versions[binary] = {'exit_code': p.returncode, 'version': (p.stdout or p.stderr).strip()[:250]}
    save(ROOT / 'runtime-versions.json', versions)
    before = {r['provider']: quota(r) for r in (ROUTES[0], ROUTES[-1])}
    manifest = {'schema_version': 1, 'status': 'approved',
                'authorization': 'Owner: Luna and Haiku medium/high/xhigh; Sol and Sonnet medium; dale con las pruebas.',
                'scope': 'Six increasing-difficulty synthetic backend implementation tasks, outside formal REQ-024.',
                'planned_calls': 48, 'repetitions': 1, 'routes': ROUTES,
                'instruction': INSTRUCTION, 'deadline_seconds': 1500,
                'account_concurrency': 1, 'provider_lanes': 2,
                'quota_before': before, 'frozen_at': time.time(),
                'validation_counts': {r['case']: r['reference']['tests'] for r in validation},
                'native_commands': {r['id']: commands(r) for r in ROUTES},
                'frozen_hashes': {p.name: digest(p.read_bytes()) for p in sorted(ROOT.glob('*.py'))},
                'cases_sha256': digest((ROOT / 'cases.json').read_bytes()),
                'isolation': 'Bubblewrap read-only host, masked artifacts and /tmp, one writable cell at /tmp/work; CLI profile state writable; native sandbox/permissions retained. Grade code in separate networkless bubblewrap.',
                'limitations': ['Single sample/cell; no statistical superiority or frontend/language-wide conclusion.',
                               'Native harness and tokenizer differ; effort names are not equal compute budgets.',
                               'Requested effort pinned; reported effective identity retained where available.',
                               'Account quota can include other sessions and coarse/delayed updates.',
                               'No automatic repair, retry, account rotation or route substitution.']}
    save(ROOT / 'protocol.json', manifest)
    return manifest


def verify_freeze() -> dict:
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    assert protocol['cases_sha256'] == digest((ROOT / 'cases.json').read_bytes())
    for name, expected in protocol['frozen_hashes'].items():
        assert digest((ROOT / name).read_bytes()) == expected, 'Frozen source drift: ' + name
    return protocol


def run_one(case: dict, route: dict) -> dict:
    path = ROOT / 'results' / f'{case["id"]}-{route["id"]}.json'
    if path.exists():
        return json.loads(path.read_text())
    prompt = INSTRUCTION + case['prompt']
    record = {'schema_version': 1, 'case': case['id'], 'route': route,
              'prompt_sha256': digest(prompt.encode()), 'prompt_characters': len(prompt),
              'started_at': time.time(), 'status': 'prepared'}
    before = quota(route)
    record['quota_before'] = before
    model_key = 'sonnet' if route['model'].startswith('claude-sonnet') else route['model']
    pressure, _ = bt_subscriptions.capacity(before, model_key)
    record['quota_pressure_before'] = pressure
    if pressure is not None and pressure >= 100:
        record['status'] = 'quota_exhausted'
        save(path, record)
        return record
    with tempfile.TemporaryDirectory(prefix='implementer-cell-') as directory:
        cwd = Path(directory)
        materialize(cwd, case['starter'])
        (cwd / 'TASK.md').write_text(prompt)
        # TASK.md is protected and equal across routes for this case.
        initial = file_map(cwd)
        record.update(status='running', workspace_before=initial)
        save(path, record)
        print('START', case['id'], route['id'], flush=True)
        try:
            record.update(invoke(route, cwd, prompt))
            save(path, record)
            submitted = ROOT / 'submissions' / f'{case["id"]}-{route["id"]}'
            shutil.copytree(cwd, submitted, symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            final = file_map(cwd)
            record['changed_files'] = sorted(k for k in set(initial) | set(final)
                                             if initial.get(k) != final.get(k))
            task_bad = not (cwd / 'TASK.md').is_file() or (cwd / 'TASK.md').read_text() != prompt
            grading_case = {**case, 'starter': {**case['starter'], 'TASK.md': prompt}}
            record['grade'] = grade(grading_case, submitted)
            if task_bad:
                record['grade']['scope_violations'].append('protected_file_changed:TASK.md')
                record['grade']['acceptance_passed'] = False
            diff = []
            for name in record['changed_files']:
                old = case['starter'].get(name, prompt if name == 'TASK.md' else '')
                target = cwd / name
                new = target.read_text(errors='replace') if target.is_file() and not target.is_symlink() else ''
                diff.extend(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                                 fromfile='before/' + name, tofile='after/' + name))
            patch = ROOT / 'patches' / f'{case["id"]}-{route["id"]}.diff'
            patch.parent.mkdir(exist_ok=True)
            patch.write_text(''.join(diff))
            record['workspace_after'] = final
        except Exception as exc:  # noqa: BLE001 -- durable per-cell failure evidence, never success
            record.update(status='harness_error', harness_error=type(exc).__name__ + ': ' + str(exc))
    record['quota_after'] = quota(route)
    record['finished_at'] = time.time()
    save(path, record)
    g = record.get('grade', {})
    print('DONE', case['id'], route['id'], record['status'],
          record.get('elapsed_seconds'), 'passed', g.get('acceptance_passed'),
          'tests', g.get('tests'), 'failures', g.get('failures'), 'errors', g.get('errors'), flush=True)
    return record


def lane(provider: str, all_cases: list[dict]) -> dict:
    own = [r for r in ROUTES if r['provider'] == provider]
    incidents = []
    for case in all_cases:
        # Balanced cyclic order, while every route's task difficulty rises.
        shift = (case['difficulty'] - 1) % len(own)
        for route in own[shift:] + own[:shift]:
            row = run_one(case, route)
            if row['status'] == 'quota_exhausted' or row.get('limit_detected'):
                return {'provider': provider, 'status': 'stopped', 'case': case['id'],
                        'route': route['id'], 'reason': row['status']}
            if row['status'] != 'completed':
                incidents.append({'case': case['id'], 'route': route['id'], 'status': row['status']})
    return {'provider': provider, 'status': 'complete_with_incidents' if incidents else 'complete',
            'incidents': incidents}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['validate', 'freeze', 'run'])
    args = parser.parse_args()
    if args.action == 'validate':
        print(json.dumps([{r['case']: {'reference': r['reference']['tests'],
                                      'starter': r['starter']['status']}} for r in validate()]))
    elif args.action == 'freeze':
        print(json.dumps({'frozen': freeze()['planned_calls']}))
    else:
        verify_freeze()
        all_cases = json.loads((ROOT / 'cases.json').read_text())
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda p: lane(p, all_cases), ('codex', 'claude')))
        save(ROOT / 'execution-summary.json', results)
        print('LANES', json.dumps(results), flush=True)
