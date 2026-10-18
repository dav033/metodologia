"""Verify frozen input parity and mandatory test coverage of every full pass."""
from __future__ import annotations

import ast
import json
import re

from pilot_common import INSTRUCTION, ROOT, digest, save


def expected_methods(case: dict) -> set[str]:
    files = {**case['starter'], **case['private_tests']}
    result = set()
    for filename, source in files.items():
        if not filename.startswith('test_') or not filename.endswith('.py'):
            continue
        for node in ast.parse(source).body:
            if isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name.startswith('test_'):
                        result.add(f'{filename[:-3]}.{node.name}.{method.name}')
    return result


def check() -> dict:
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    for name, expected in protocol['frozen_hashes'].items():
        assert digest((ROOT / name).read_bytes()) == expected, f'Frozen input drift: {name}'
    assert digest((ROOT / 'cases.json').read_bytes()) == protocol['cases_sha256']
    coverage = []
    for path in sorted((ROOT / 'results').glob('*.json')):
        row = json.loads(path.read_text())
        case = cases[row['case']]
        required = expected_methods(case)
        assert len(required) == protocol['validation_counts'][row['case']]
        assert row['prompt_sha256'] == digest((INSTRUCTION + case['prompt']).encode())
        grade = row.get('grade', {})
        successes = {m['class'] for m in grade.get('methods', []) if m['result'] == 'ok'}
        noisy_recovered = []
        # A failed suite can still contain a successful method whose final ok
        # was separated from its announcement by SQLite ResourceWarnings.
        for method, segment in re.findall(
                r'^test_\S+ \(([^)\n]+)\) \.\.\.(.*?)(?=^test_\S+ \(|^={10,}|\Z)',
                grade.get('output', ''), re.MULTILINE | re.DOTALL):
            if re.search(r'(?:^|\n)ok\s*\Z', segment.strip()) and method in required:
                if method not in successes:
                    noisy_recovered.append(method)
                successes.add(method)
        if grade.get('status') == 'passed' and grade.get('exit_code') == 0:
            output = grade['output']
            announced = set(re.findall(r'^test_\S+ \(([^)\n]+)\) \.\.\.', output, re.MULTILINE))
            skipped = set(re.findall(r'^test_\S+ \(([^)\n]+)\) \.\.\. skipped', output, re.MULTILINE))
            # ResourceWarning can split unittest's method line from its final ok.
            # Successful process + emitted method + no skip proves its completion.
            recovered = announced - skipped - successes
            noisy_recovered = sorted(set(noisy_recovered) | (recovered & required))
            successes |= recovered
        missing = sorted(required - successes)
        if grade.get('acceptance_passed'):
            assert not missing, f'Incomplete mandatory coverage: {path.name}: {missing}'
            assert not grade['scope_violations'], path.name
            assert row['status'] == 'completed', path.name
            assert not row.get('limit_detected'), path.name
        coverage.append({'cell': path.stem, 'mandatory_count': len(required),
                         'mandatory_passed': len(required & successes), 'not_proven_passing': missing,
                         'noisy_line_recovered': noisy_recovered,
                         'full_pass': grade.get('acceptance_passed')})
    evidence = {'frozen_input_hashes_valid': True, 'same_prompt_per_case': True,
                'mandatory_tests_per_route': sum(len(expected_methods(c)) for c in cases.values()),
                'cells': coverage}
    save(ROOT / 'mandatory-coverage.json', evidence)
    return evidence


if __name__ == '__main__':
    result = check()
    print(json.dumps({'cells_checked': len(result['cells']),
                      'mandatory_tests_per_route': result['mandatory_tests_per_route'],
                      'valid': True}))
