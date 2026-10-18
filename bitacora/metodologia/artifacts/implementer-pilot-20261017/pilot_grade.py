"""Grade code in a clean subprocess with coordinator-owned tests."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pilot_common import file_map, materialize


def run_tests(root: Path, pattern: str = 'test_*.py') -> dict:
    env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'PYTHONDONTWRITEBYTECODE': '1'}
    cmd = [sys.executable, '-m', 'unittest', 'discover', '-s', '.', '-p', pattern, '-v']
    try:
        sandbox = ['bwrap', '--ro-bind', '/usr', '/usr', '--ro-bind', '/lib', '/lib',
                   '--ro-bind', '/lib64', '/lib64', '--symlink', 'usr/bin', '/bin',
                   '--tmpfs', '/tmp', '--bind', str(root), '/tmp/work',
                   '--chdir', '/tmp/work', '--proc', '/proc', '--dev', '/dev',
                   '--unshare-pid', '--unshare-net', '--die-with-parent']
        proc = subprocess.run(sandbox + cmd, cwd=root, env=env, text=True,
                              capture_output=True, timeout=90, check=False)
        output = proc.stdout + proc.stderr
        completed = re.search(r'Ran (\d+) tests?', output)
        tests = int(completed.group(1)) if completed else None
        errors = re.search(r'FAILED \(([^)]+)\)', output)
        totals = dict(re.findall(r'(failures|errors|skipped|expected failures|unexpected successes)=(\d+)',
                                 errors.group(1) if errors else ''))
        methods = re.findall(r'^(test_\S+) \(([^\n]+)\) \.\.\. (ok|FAIL|ERROR|skipped[^\n]*)$',
                             output, re.MULTILINE)
        return {'command': cmd, 'exit_code': proc.returncode, 'tests': tests,
                'failures': int(totals.get('failures', 0)),
                'errors': int(totals.get('errors', 0)),
                'methods': [{'method': a, 'class': b, 'result': c} for a, b, c in methods],
                'output': output, 'status': 'passed' if proc.returncode == 0 and tests else 'failed'}
    except subprocess.TimeoutExpired as exc:
        def decoded(v):
            return v.decode(errors='replace') if isinstance(v, bytes) else v or ''
        return {'command': cmd, 'exit_code': None, 'tests': None, 'status': 'timeout',
                'output': decoded(exc.stdout) + decoded(exc.stderr)}


def grade(case: dict, submitted: Path) -> dict:
    """Private tests are absent from candidate's tree until its session exits."""
    expected = {k: v for k, v in case['starter'].items() if not k.startswith('app/')}
    actual = file_map(submitted)
    violations = []
    for name, content in expected.items():
        path = submitted / name
        if not path.is_file() or path.is_symlink() or path.read_text() != content:
            violations.append('protected_file_changed:' + name)
    for name in actual:
        if name not in case['starter'] and not name.startswith('app/'):
            violations.append('unexpected_file:' + name)
    for path in submitted.rglob('*'):
        if path.is_symlink():
            violations.append('symlink:' + str(path.relative_to(submitted)))
    if any(v.startswith('symlink:') for v in violations):
        return {'status': 'rejected', 'acceptance_passed': False,
                'scope_violations': violations, 'output': 'Symlinks are outside the fixture contract.'}
    with tempfile.TemporaryDirectory(prefix='implementer-grade-') as directory:
        root = Path(directory)
        materialize(root, case['starter'])
        app = submitted / 'app'
        if app.is_dir() and not app.is_symlink():
            shutil.rmtree(root / 'app')
            shutil.copytree(app, root / 'app', symlinks=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        materialize(root, case['private_tests'])
        result = run_tests(root)
    result['scope_violations'] = sorted(set(violations))
    result['acceptance_passed'] = result['status'] == 'passed' and not violations
    return result
