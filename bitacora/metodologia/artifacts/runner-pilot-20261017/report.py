"""Audit saved Runner evidence and publish measured comparisons without model calls."""
import argparse
import json

from native import ROOT, ROUTES, digest, save
from run import verify


def read(path):
    return json.loads(path.read_text())


def snapshot():
    records = sorted((ROOT / 'results').glob('*.json'))
    evidence = [*records, *(p for p in (ROOT / 'submissions').rglob('*') if p.is_file()), ROOT / 'execution.log', ROOT / 'execution-summary.json']
    if (ROOT / 'original-evidence-hashes.json').exists():
        raise RuntimeError('Original evidence manifest already exists')
    save(ROOT / 'original-evidence-hashes.json', {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in evidence})
    answers = []
    for path in records:
        row = read(path)
        if 'workspace_before' not in row:
            continue
        answers.append({'original': path.stem, 'response_text': row.get('response_text', ''),
                        'case': row['case'], 'fixture_events': row.get('fixture_events', []),
                        'tool_evidence': row.get('tool_evidence', []), 'scope_violations': row.get('scope_violations', []),
                        'unexpected_files': row.get('unexpected_files', []), 'native_status': row['status']})
    # Content reviewers receive separate anonymous files and a case/rubric contract.
    answers.sort(key=lambda r: digest(r['original'].encode()))
    mapping = {}
    for index, row in enumerate(answers, 1):
        label = f'B{index:02d}'
        mapping[label] = row.pop('original')
        save(ROOT / 'blind' / (label + '.json'), row)
    save(ROOT / 'blind-map.json', mapping)
    print('Original evidence sealed; anonymous submissions prepared:', len(answers))


def audit():
    verify()
    originals = read(ROOT / 'original-evidence-hashes.json')
    for name, wanted in originals.items():
        assert digest((ROOT / name).read_bytes()) == wanted, name
    cases = read(ROOT / 'cases.json')
    records = {p.stem: read(p) for p in (ROOT / 'results').glob('*.json')}
    expected = {c['id'] + '-' + r['id'] for c in cases for r in ROUTES}
    assert set(records) <= expected
    started = [line.split()[1] for line in (ROOT / 'execution.log').read_text().splitlines() if line.startswith('START ')]
    done = [line.split()[1] for line in (ROOT / 'execution.log').read_text().splitlines() if line.startswith('DONE ')]
    assert len(started) == len(set(started)) and len(done) == len(set(done))
    assert set(done) <= set(started) <= set(records)
    attempted = {k for k, row in records.items() if 'workspace_before' in row}
    assert set(started) == attempted
    for key in attempted:
        row = records[key]
        assert row['prompt_sha256'] == read(ROOT / 'protocol.json')['prompt_hashes'][row['case']]
        output = ROOT / 'submissions' / key
        if output.exists():
            for name, wanted in row['workspace_after'].items():
                assert digest((output / name).read_bytes()) == wanted, (key, name)
    result = {'records': len(records), 'attempted_native_calls': len(attempted), 'expected': 24,
              'missing': sorted(expected - set(records)), 'unique_start_done_pairs': set(started) == set(done),
              'never_invoked': sorted(expected - attempted),
              'frozen_and_original_hashes_valid': True,
              'native_status_counts': {s: sum(r['status'] == s for r in records.values()) for s in sorted({r['status'] for r in records.values()})},
              'lanes': read(ROOT / 'execution-summary.json'),
              'grading_review': read(ROOT / 'final-review.json').get('verdict', 'pending') if (ROOT / 'final-review.json').exists() else 'pending'}
    save(ROOT / 'closeout-audit.json', result)
    print(json.dumps(result))
    return records


def report():
    records = audit()
    mapping = read(ROOT / 'blind-map.json')
    grades = read(ROOT / 'grades.json')
    assert set(grades) == set(mapping)
    by_original = {}
    original_grades = read(ROOT / 'grades-original.json')
    assert set(original_grades) == set(grades)
    for label, grade in grades.items():
        assert set(grade['criteria']) == {'execution', 'exits', 'status', 'diagnostic', 'detail', 'contract'}
        assert all(v in ('full', 'partial', 'missing') for v in grade['criteria'].values())
        assert isinstance(grade['evidence'], str) and grade['evidence'].strip()
        by_original[mapping[label]] = grade
    comparison = []
    for route in ROUTES:
        rows = [(key, row) for key, row in records.items() if row['route']['id'] == route['id'] and 'workspace_before' in row]
        content = strict = full = contract = 0
        failures = []
        for key, row in rows:
            g = by_original[key]
            full += sum(v == 'full' for v in g['criteria'].values())
            content_ok = all(v == 'full' for k, v in g['criteria'].items() if k != 'contract')
            content += content_ok
            contract += g['criteria']['contract'] == 'full'
            strict += content_ok and g['criteria']['contract'] == 'full' and row['status'] == 'completed'
            if not content_ok or g['criteria']['contract'] != 'full':
                failures.append({'case': row['case'], **g})
        complete_usage = [row['usage']['total'] for _, row in rows if row.get('usage', {}).get('quality') == 'complete' and row['usage'].get('total') is not None]
        command_durations = [e['seconds'] for _, row in rows for e in row.get('fixture_events', []) if e.get('event') == 'end']
        comparison.append({'route': route, 'cases_recorded': len(rows), 'strict_cases': strict, 'content_cases': content,
                           'original_strict_cases': sum(all(v == 'full' for v in original_grades[label]['criteria'].values())
                                                        for label, key in mapping.items() if key in dict(rows)),
                           'contract_cases': contract, 'full_criteria': full, 'criteria_evaluated': 6 * len(rows),
                           'seconds': round(sum(row.get('seconds', 0) for _, row in rows), 3),
                           'complete_usage_cases': len(complete_usage), 'tokens_available': sum(complete_usage) if complete_usage else None,
                           'completed_fixture_command_seconds': round(sum(command_durations), 6),
                           'models_observed': sorted({m for _, row in rows for m in row.get('observed_models', [])}),
                           'efforts_observed': sorted({m for _, row in rows for m in row.get('observed_efforts', [])}), 'findings': failures})
    save(ROOT / 'comparison.json', comparison)
    attempted = sum(row['cases_recorded'] for row in comparison)
    lines = ['# Runner pilot — partial closeout report', '',
             f'PARTIAL: {attempted}/24 authorized native cells executed; nine never invoked. Claude stopped on an HTTP429 from its usage telemetry endpoint before N2 Haiku, not a native model limit. Codex completed its lane. No native repair/retry or account switch. See RESUME.md and pending-cells.json.', '',
             'Owner-authorized four configurations × six local cases. Original results and full fixture logs are preserved separately from grades. The table uses the explicit adjudicated semantic assessment.', '',
             '| Configuration | Content passed/evaluated | Strict passed/evaluated | Full criteria/evaluated | Native time (s) | Recorded tokens | Cases/6 |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for row in comparison:
        tokens = f'{row["tokens_available"]:,}' if row['tokens_available'] is not None else 'unknown'
        lines.append(f'| {row["route"]["id"]} | {row["content_cases"]}/{row["cases_recorded"]} | {row["strict_cases"]}/{row["cases_recorded"]} | {row["full_criteria"]}/{row["criteria_evaluated"]} | {row["seconds"]:.3f} | {tokens} | {row["cases_recorded"]}/6 |')
    lines += ['', 'Content requires execution, real exit codes, aggregate status and both semantic findings. Strict also requires the frozen scope/format contract and a completed native call. Partial criteria do not count as full. See rubric.json and grades.json for individual evidence.', '',
              'Original blind grades are preserved in grades-original.json. Correction-only blind review withdrew hidden successful-test-count requirements and unsupported1.89s timing penalties; grading-adjudications.json records the four corrections without altering fixtures or native outputs. Original strict cases: ' + '; '.join(r['route']['id'] + ' ' + str(r['original_strict_cases']) + '/' + str(r['cases_recorded']) for r in comparison) + '.', '', '## Concrete findings']
    for row in comparison:
        for finding in row['findings']:
            lines.append('- ' + row['route']['id'] + '/' + finding['case'] + ': ' + finding['evidence'])
    if not any(row['findings'] for row in comparison):
        lines.append('- No missing or partial criterion in the evaluated cases.')
    lines += ['', '## Measurement limits',
              '- Preflight-only blocked records are not native attempts and are never graded as model failures. Missing cells are unknown; unequal coverage prevents a four-model ranking. See closeout-audit.json for never-invoked cells and lane reasons.',
              '- Single sample on six synthetic standard-library fixtures; no production repository/network workload or statistical quality ranking. No permanent model selection.',
              '- Native wall time includes CLI/model/tool work; quota reads are excluded. Fixture end-event duration excludes shell startup and the killed hang; it is not model-only overhead. N5 intentionally waits two seconds per configuration.',
              '- Both Luna N6 summaries report microsecond command durations below the contained fixture runtime. These are unreliable complete-command timings. Native tool wall-time metadata was not retained, so responsibility between the model and native CLI measurement is unknown; fabrication is not established. Content and strict contract results remain separate.',
              '- Same account per provider, alternating within-provider route order by case; different providers have different native tools, caching and subscriptions. Raw tokens are not invoices, cost estimates or quota equivalents.',
              '- Requested model/effort are pinned in protocol.json. Effective identity/effort is only attested when native events report it; absent fields remain unknown. Codex may not attest its effective model; no inference from its answer.',
              '- Tool calls/results are retained without private thinking. Fixture logs corroborate invocation and full outputs; immutable fixture/task mounts prevent their edits. Post-run hashes and tool review detect scope breaches, not every possible malicious transient action.',
              '- grades.json contains the anonymous semantic assessment; blind-map.json restores route identities after grading. Original evidence hashes are in original-evidence-hashes.json; frozen hashes in protocol.json. See final-review.json for independent closeout review status.', '', '## Identity evidence']
    for row in comparison:
        lines.append('- ' + row['route']['id'] + ': observed models=' + str(row['models_observed']) + '; observed efforts=' + str(row['efforts_observed']) + '. Empty means unattested.')
    (ROOT / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    print('REPORT/comparison regenerated')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['snapshot', 'audit', 'report'])
    action = parser.parse_args().action
    {'snapshot': snapshot, 'audit': audit, 'report': report}[action]()
