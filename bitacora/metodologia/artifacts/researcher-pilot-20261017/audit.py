"""Audit final once-only evidence and arithmetic without any native invocation."""
import ast
import hashlib
import json
from pathlib import Path

from records import load_records
from run import check_note, prompt, verify

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    verify()
    for name, wanted in read('original-evidence-hashes.json').items():
        assert digest(ROOT / name) == wanted, name
    auth = read('continuation-codex-luis/authorization.json')
    for name, wanted in auth['frozen_hashes'].items():
        assert digest(ROOT / name) == wanted, name
    rows, submissions = load_records()
    cases = {c['id']: c for c in read('cases.json')}
    protocol = read('protocol.json')
    expected = {cid + '-' + r['id'] for cid in cases for r in protocol['routes']}
    assert set(rows) == expected and len(rows) == 18
    for cell, row in rows.items():
        assert row['status'] == 'completed' and row['exit_code'] == 0, cell
        assert not row['limit_detected'] and not row['provider_errors'], cell
        assert 'workspace_before' in row and row['has_final_usage_event'], cell
        assert row['prompt_sha256'] == hashlib.sha256(prompt(cases[row['case']]).encode()).hexdigest()
        assert check_note(submissions[cell] / 'research.json', cases[row['case']])['valid'], cell
        assert not row['scope_violations'] and not row['unexpected_files'], cell
        for name, wanted in row['workspace_before'].items():
            assert digest(submissions[cell] / name) == wanted, cell + ':' + name
        route = row['route']
        original = next(r for r in protocol['routes'] if r['id'] == route['id'])
        assert route['model'] == original['model'] and route['effort'] == original['effort']
        wanted_profile = 'claude-work' if route['provider'] == 'claude' else 'codex-2' if row['case'] == 'R1' else 'codex-luis'
        assert route['profile'] == wanted_profile, cell
        argv = protocol['native_commands'][route['id']][row['mode']]
        assert row['argv'][-len(argv):] == argv, cell
        assert row['observed_models'] in ([], [route['model']]), cell
        usage = row['usage']
        fields = ['input_tokens', 'output_tokens']
        if route['provider'] == 'claude':
            fields += ['cache_read_tokens', 'cache_write_tokens']
        assert usage['comparable'] and usage['total'] == sum(usage[f] for f in fields), cell
    ids = []
    for name in ['execution.log', 'continuation-codex-luis/execution.log']:
        lines = (ROOT / name).read_text().splitlines()
        starts = [l.split()[1] + '-' + l.split()[2] for l in lines if l.startswith('START ')]
        dones = [l.split()[1] + '-' + l.split()[2] for l in lines if l.startswith('DONE ')]
        assert sorted(starts) == sorted(dones) and len(starts) == len(set(starts)), name
        ids.extend(starts)
    assert len(ids) == 18 and set(ids) == expected
    assert read('results/R2-luna-high.json')['status'] == 'quota_exhausted'
    assert 'workspace_before' not in read('results/R2-luna-high.json')
    assert read('continuation-codex-luis/execution-summary.json')['status'] == 'complete'
    original_grades = read('grades.json')
    grades = read('supplemental-grades.json')
    assert set(grades) == expected and set(original_grades) == expected
    for cell, grade in grades.items():
        assert {c['id'] for c in grade['criteria']} == {f'C{i}' for i in range(1, 7)}, cell
        assert all(c['rating'] in ('full', 'partial', 'missing') and isinstance(c['supported'], bool) for c in grade['criteria'])
    for cell, grade in read('partial-closeout/grades.json').items():
        assert original_grades[cell] == grade, cell
    for cell, grade in grades.items():
        for current, original in zip(grade['criteria'], original_grades[cell]['criteria'], strict=True):
            if not (cell.startswith('R6-') and current['id'] == 'C5'):
                assert current == original, cell
    comparison = read('comparison.json')
    assert comparison['started'] == 18 and comparison['graded'] == 18
    assert comparison['saved_records'] == 19 and comparison['unattempted_native_cells'] == 0
    assert comparison['complete_comparison'] and comparison['matched_cases'] == list(cases)
    for group in comparison['configurations']:
        own = [r for r in rows.values() if r['route']['id'] == group['route']['id']]
        assert len(own) == 6
        assert group['tokens'] == sum(r['usage']['total'] for r in own)
        assert group['seconds'] == round(sum(r['seconds'] for r in own), 3)
        assert group['token_coverage'] == '6/6'
        assert group['full_criteria'] == sum(c['rating'] == 'full' for r in own for c in grades[r['case'] + '-' + r['route']['id']]['criteria'])
    for path in ROOT.glob('*.py'):
        ast.parse(path.read_text())
    for path in ROOT.rglob('*.json'):
        json.loads(path.read_text())
    evidence = [*ROOT.joinpath('results').rglob('*.json'), *ROOT.joinpath('submissions').rglob('*'),
                *ROOT.joinpath('continuation-codex-luis/results').rglob('*.json'),
                *ROOT.joinpath('continuation-codex-luis/submissions').rglob('*')]
    manifest = {str(p.relative_to(ROOT)): digest(p) for p in evidence if p.is_file()}
    (ROOT / 'all-native-evidence-hashes.json').write_text(json.dumps(manifest, indent=2) + '\n')
    receipt = {'status': 'passed_complete_pilot', 'native_calls': 18, 'original_native_calls': 8,
        'continuation_native_calls': 10, 'preflight_only_records': 1, 'unattempted_calls': 0,
        'frozen_hashes_valid': True, 'original_evidence_preserved': True, 'same_prompts_commands_models_efforts': True,
        'profiles': {'claude-work': 6, 'codex-2': 2, 'codex-luis': 10}, 'all_native_exits': 0,
        'json_ast_contract_and_scope_checks': True, 'all18_usage_complete': True,
        'time_token_criterion_arithmetic': True, 'original8_grades_preserved': True,
        'uniform_r6_c5_source_supplement_separate': True,
        'no_native_retry_repair_or_model_substitution': True,
        'effective_codex_model_identity_and_all_efforts_unattested': True,
        'artifact_hashes': {name: digest(ROOT / name) for name in ['REPORT.md', 'comparison.json', 'grades.json', 'supplemental-grades.json', 'supplemental-source-adjudication.json', 'all-native-evidence-hashes.json']}}
    (ROOT / 'closeout-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('AUDIT PASS:18 unique native calls; original8 preserved; one quota-only preflight; no repeat; matched6 cases; all usage/time checked.')


if __name__ == '__main__':
    audit()
