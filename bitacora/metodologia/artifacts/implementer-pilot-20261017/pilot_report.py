"""Summarize native evidence without treating unknown usage as zero."""
from __future__ import annotations

import json
from collections import Counter

from pilot_common import ROOT, ROUTES, save


def summarize() -> dict:
    rows = [json.loads(p.read_text()) for p in sorted((ROOT / 'results').glob('*.json'))]
    resources_path = ROOT / 'supplement-resources.json'
    semantic_path = ROOT / 'supplement-semantics.json'
    resources = {r['cell']: r for r in json.loads(resources_path.read_text())} if resources_path.exists() else {}
    semantic = {r['cell']: r for r in json.loads(semantic_path.read_text())} if semantic_path.exists() else {}
    result = []
    for route in ROUTES:
        own = [r for r in rows if r['route']['id'] == route['id']]
        done = [r for r in own if r['status'] != 'running']
        coverage = [r for r in done if r.get('usage', {}).get('comparable')]
        partial = [r for r in done if r.get('usage', {}).get('quality') == 'partial']
        complete = len(coverage) == len(done) and bool(done)
        parts = {}
        for field in ('input_tokens', 'output_tokens', 'cache_read_tokens',
                      'cache_write_tokens', 'reasoning_tokens'):
            values = [r.get('usage', {}).get(field) for r in done]
            parts[field] = sum(values) if values and all(v is not None for v in values) else None
        per_case = {}
        for row in own:
            grade = row.get('grade', {})
            key = row['case'] + '-' + route['id']
            resource = resources.get(key, {}).get('status')
            sem = semantic.get(key, {}).get('grade', {}).get('acceptance_passed')
            revised = grade.get('acceptance_passed')
            if row['case'] in ('I4', 'I5'):
                revised = revised and resource == 'passed' if resource is not None else None
            if row['case'] == 'I6':
                revised = sem and resource == 'passed' if sem is not None and resource is not None else None
            per_case[row['case']] = {
                'status': row['status'], 'passed': grade.get('acceptance_passed'),
                'adjudicated_passed': revised, 'resource_status': resource,
                'supplement_semantic_passed': sem,
                'tests': grade.get('tests'), 'failures': grade.get('failures'),
                'errors': grade.get('errors'), 'scope_violations': grade.get('scope_violations'),
                'seconds': row.get('elapsed_seconds'), 'tokens': row.get('usage', {}).get('total'),
                'usage_quality': row.get('usage', {}).get('quality'),
                'observed_models': row.get('observed_models'),
                'observed_efforts': row.get('observed_efforts')}
        result.append({'route': route, 'started': len(own), 'returned': len(done),
                       'fully_passed_cases': sum(r.get('grade', {}).get('acceptance_passed') is True for r in done),
                       'adjudicated_passed_cases': sum(c['adjudicated_passed'] is True for c in per_case.values()),
                       'statuses': dict(Counter(r['status'] for r in own)),
                       'seconds': round(sum(r.get('elapsed_seconds', 0) for r in done), 3),
                       'token_coverage': f'{len(coverage)}/{len(done)}',
                       'tokens': sum(r['usage']['total'] for r in coverage) if complete else None,
                       'usage_parts': parts,
                       'complete_usage_subtotal': sum(r['usage']['total'] for r in coverage),
                       'partial_usage_lower_bound': sum(r['usage']['total'] or 0 for r in partial),
                       'tool_calls': sum(len(r.get('tool_calls', [])) for r in done),
                       'turns': sum(r.get('turns') or 0 for r in done),
                       'per_case': per_case})
    return {'planned_calls': 48, 'started': len(rows), 'returned': sum(r['status'] != 'running' for r in rows),
            'configurations': result}


def write_report(summary: dict) -> None:
    lines = ['# Implementer pilot: eight configurations, six increasing-difficulty cases', '',
             ('Owner-authorized native implementation pilot; outside formal REQ-024. '
              'Single repetition per cell. No role assignment or runtime policy change.'), '',
             f"Evidence: {summary['returned']}/48 calls returned; {summary['started']} started.", '',
             '| Configuration | I1 | I2 | I3 | I4 | I5 | I6 | Fully passed | Seconds | Tokens (coverage) |',
             '|---|---|---|---|---|---|---|---:|---:|---:|']
    for row in summary['configurations']:
        cells = []
        for case in ('I1', 'I2', 'I3', 'I4', 'I5', 'I6'):
            cell = row['per_case'].get(case)
            cells.append('—' if not cell else 'PASS' if cell['passed'] else
                         'FAIL' if cell['passed'] is False else cell['status'])
        token = f"{row['tokens']:,}" if row['tokens'] is not None else 'unknown'
        lines.append('| ' + ' | '.join([row['route']['id'], *cells,
                     f"{row['fully_passed_cases']}/6", f"{row['seconds']:.3f}",
                     f"{token} ({row['token_coverage']})"]) + ' |')
    lines.extend(['', '## Cases and verification', '',
                  ('I1 interval bugfix; I2 repository/service/CLI cursor pagination; I3 deterministic DAG state; '
                  'I4 atomic SQLite migration; I5 concurrent lease claims/fencing; '
                  'I6 crash recovery/dependencies/retry/atomic outbox/replay/deduplication.'), '',
                  ('Frozen reference suite: 12 + 14 + 14 + 11 + 11 + 17 = 79 tests. '
                  'Every reference passes and every starting fixture fails intended behavior. '
                  'Representative mutants fail. Fresh spec/standards audit corrections were applied before freezing.'), '',
                  ('Candidate runs receive the same prompt/code per case in independent working trees. '
                  'Native Bubblewrap masks benchmark artifacts/oracles and sibling /tmp cells; '
                  'other host files remain read-only, and CLI profile state is writable. '
                  'The shared instructions prohibit inspecting other repositories/accounts. '
                  'The coordinator grades submitted app/ with original public and withheld private tests in a separate, '
                  'minimal, networkless sandbox. Protected-file/scope violations prevent a full pass. '
                  'Per-cell test output, native status, identity evidence, quota observations, patch and source hashes are retained.'), '',
                  '## Interpretation limits', '',
                  ('- These are synthetic Python/SQLite backend cases. Results do not establish general superiority, '
                  'frontend quality or equivalent performance in other languages.'),
                  '- Native tools, caches, tokenizers and harness prompts differ. Equal effort names are not equal compute.',
                  ('- Model/effort requests are pinned. Claude stream-reported model identities are retained; '
                  'absence of runtime attestation is not proof of an effective model/effort.'),
                  ('- Tokens include cached context. Codex total = input + output; Claude total also includes cache read/write. '
                  'Partial counters are lower bounds, unknown counters are null. Tokens are not subscription quota or invoices.'),
                  ('- Time/consumption comparisons are meaningful among equally successful configurations; '
                  'account quota may include simultaneous unrelated sessions.'),
                  ('- No coordinator code repairs, quality retries or silent route substitutions. '
                  'Read execution-summary.json for operational incidents before ranking results.'), '',
                  '## Separate posthoc adjudication', '',
                  ('The original table above is unchanged. I6 did not explicitly fix outbox.body encoding; '
                  'Luna medium and Haiku medium used JSON {id,result}; Haiku xhigh used {job_id,result}, '
                  'while five original assertions per candidate expected the raw result. '
                  'Those mismatches reflect one oracle ambiguity, not five demonstrated model defects each. '
                  'A separate, uniformly applied supplement accepts raw results or minimal JSON with exact result '
                  'and an optional matching id/job_id, while preserving '
                  'atomicity, order, replay and byte-for-byte inbox deduplication. No submissions were repaired '
                  'and no native model calls repeated.'), '',
                  ('A second posthoc witness tracks real SQLite connections and checks closure on return/error, '
                  'as explicitly required in I4–I6. This reveals an independent I6 Luna medium defect: '
                  'sqlite3.Connection used as a context manager commits/rolls back but does not close. '
                  'References pass both supplements; an incorrect JSON-result mutant fails. '
                  'An initial optional-I5-API resource probe was excluded and preserved in '
                  'supplement-resources-excluded-v1.json; the valid witness gates APIs by case ID.'), '',
                  '| Configuration | Original cases | Cases after semantic/resource adjudication | I6 semantic | I6 connection closure |',
                  '|---|---:|---:|---|---|'])
    for row in summary['configurations']:
        c = row['per_case'].get('I6', {})
        lines.append(f"| {row['route']['id']} | {row['fully_passed_cases']}/6 | "
                     f"{row['adjudicated_passed_cases']}/6 | {c.get('supplement_semantic_passed')} | "
                     f"{c.get('resource_status')} |")
    resource_rows = json.loads((ROOT / 'supplement-resources.json').read_text())
    leaking = [r for r in resource_rows if r['status'] != 'passed']
    for witness in leaking:
        import re
        connection_counts = re.findall(r': (\d+) connection\(s\) usable after API return', witness['output'])
        lines.extend(['', f"Resource witness `{witness['cell']}`: {witness['failures']} failing subtests, "
                      f"{sum(map(int, connection_counts))} usable connection observations across operations. "
                      'These are distinct counts: the publish operation leaves three connections usable.'])
    unattested = [r['route']['id'] for r in summary['configurations']
                  if any(not c['observed_models'] for c in r['per_case'].values())]
    lines.extend(['', 'Runtime model identity is unattested in saved CLI output for: '
                  + ', '.join(unattested) + '. Requested identities are preserved; no effective identity is inferred. '
                  'Claude streams report claude-haiku-5-5 or claude-sonnet-5-5 as requested. '
                  'No CLI stream attests effective effort for any configuration.', '',
                  'Closure audit: all 48 result cells, 48 START/DONE pairs, eight complete six-case configurations, '
                  '79 mandatory methods per configuration and frozen input hashes verified. '
                  'All eight I6 semantic supplements pass; 23/24 resource witnesses pass, '
                  'with only I6 Luna medium failing. Original native results are immutable. '
                  'See closeout-audit.json for integrity checks and regeneration exit codes.'])
    lines.extend(['', ('Supplemental evidence is labeled posthoc and is distinct from the frozen benchmark score. '
                  'See supplement-provenance.json, supplement-semantics.json and supplement-resources.json.'), ''])
    (ROOT / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    result = summarize()
    save(ROOT / 'comparison.json', result)
    write_report(result)
    print(json.dumps({'returned': result['returned'], 'started': result['started'],
                      'configurations': [{k: r[k] for k in ('route', 'fully_passed_cases', 'seconds', 'tokens', 'token_coverage')}
                                         for r in result['configurations']]}, indent=2))
