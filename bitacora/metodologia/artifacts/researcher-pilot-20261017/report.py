"""Derive a transparent report from native cells and separate content grades."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def summarize():
    protocol = read('protocol.json')
    rows = {p.stem: json.loads(p.read_text()) for p in (ROOT / 'results').glob('*.json')}
    grades = read('grades.json') if (ROOT / 'grades.json').exists() else {}
    output = []
    for route in protocol['routes']:
        own = {k: v for k, v in rows.items() if v['route']['id'] == route['id']}
        attempted = [r for r in own.values() if 'workspace_before' in r]
        complete = [r for r in attempted if r.get('usage', {}).get('comparable')]
        cases = []
        for case in read('cases.json'):
            key = case['id'] + '-' + route['id']
            row, grade = rows.get(key, {}), grades.get(key)
            criteria = grade.get('criteria', []) if grade else []
            content_full = len(criteria) == 6 and all(c['rating'] == 'full' for c in criteria)
            evidence_full = len(criteria) == 6 and all(c['supported'] for c in criteria)
            cases.append({'case': case['id'], 'mode': case['mode'], 'status': row.get('status', 'unstarted'),
                          'contract_valid': row.get('contract', {}).get('valid'), 'grade': grade,
                          'content_full': content_full if grade else None,
                          'evidence_full': evidence_full if grade else None,
                          'scope_valid': not row.get('scope_violations') and not row.get('unexpected_files'),
                          'seconds': row.get('seconds'), 'tokens': row.get('usage', {}).get('total')})
        quality = [c for c in cases if c['content_full'] and c['evidence_full'] and c['scope_valid']]
        output.append({'route': route, 'started': len(attempted), 'saved_records': len(own), 'native_statuses': dict(Counter(r['status'] for r in own.values())),
                       'content_and_evidence_cases': len(quality), 'graded_cases': sum(c['grade'] is not None for c in cases),
                       'frozen_pass': sum(c['mode'] == 'frozen' for c in quality),
                       'live_pass': sum(c['mode'] == 'live' for c in quality),
                       'full_criteria': sum(c['rating'] == 'full' for v in cases if v['grade'] for c in v['grade']['criteria']),
                       'partial_criteria': sum(c['rating'] == 'partial' for v in cases if v['grade'] for c in v['grade']['criteria']),
                       'supported_criteria': sum(c['supported'] for v in cases if v['grade'] for c in v['grade']['criteria']),
                       'contract_cases': sum(c['contract_valid'] is True for c in cases),
                       'seconds': round(sum(r.get('seconds', 0) for r in own.values()), 3),
                       'token_coverage': f'{len(complete)}/{len(attempted)}',
                       'tokens': sum(r['usage']['total'] for r in complete) if len(complete) == len(attempted) and attempted else None,
                       'measured_token_subtotal': sum(r['usage']['total'] for r in complete),
                       'unattested_model_cells': [k for k, r in own.items() if not r.get('observed_models')],
                       'unattested_effort_cells': [k for k, r in own.items() if not r.get('observed_efforts')],
                       'per_case': cases})
    started = sum('workspace_before' in row for row in rows.values())
    matched = [case['id'] for case in read('cases.json')
               if all(case['id'] + '-' + r['id'] in grades for r in protocol['routes'])]
    return {'planned_calls': 18, 'saved_records': len(rows), 'started': started,
            'unattempted_native_cells': 18 - started, 'graded': len(grades),
            'matched_cases': matched, 'complete_comparison': started == 18 and len(grades) == 18,
            'configurations': output}


def report(result):
    lines = ['# Researcher pilot: native matched comparison', '',
             f"Native calls: {result['started']}/18; saved operational records: {result['saved_records']}; content evaluations: {result['graded']}/18.", '',
             ('Complete comparison.' if result['complete_comparison'] else
              'INCOMPLETE: provider quota/operational stops leave unattempted cells. Unequal task coverage prevents ranking route totals. '
              + 'Matched cases only: ' + ', '.join(result['matched_cases']) + '.'), '',
             '| Configuration | Native calls | Frozen content+cites | Live content+cites | Full criteria (graded) | Supported criteria (graded) | JSON contract | Seconds | Tokens (coverage) |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in result['configurations']:
        token = f"{r['tokens']:,}" if r['tokens'] is not None else 'unknown'
        n = 6 * r['graded_cases']
        lines.append(f"| {r['route']['id']} | {r['started']}/6 | {r['frozen_pass']}/4 | {r['live_pass']}/2 | {r['full_criteria']}/{n} | {r['supported_criteria']}/{n} | {r['contract_cases']}/6 | {r['seconds']:.3f} | {token} ({r['token_coverage']}) |")
    lines += ['', '## Protocol and grading', '',
              'Owner authorized this comparison after the web-research proposal. Three pinned routes, six tasks each, one call/cell; no retries, repair turns or route substitution. Profiles: Sonnet claude-work; Sol/Luna codex-2, one active call per account. Native results are preserved independently from content judgements.', '',
              'R1 asyncio concurrency; R2 cross-version SQLite lifetime; R3 Node HTTP deadlines; R4 PostgreSQL concurrent-index failures; R5 Node release dates as of2026-10-17; R6 uv synchronization and network guarantees. Frozen extracts have original line numbers. Live tools differ by provider; interpret frozen and live results separately.', '',
              'Each of36 criteria per route is graded full/partial/missing and separately source-supported or unsupported. A content+citation case passes only when all six criteria are full and supported, with no scope violations. JSON contract is a separate column; original responses are never repaired. Labels are hidden for content grading where practical; coordinator may know routes, so this is not a fully blind or statistical comparison.', '',
              'Case-pass and JSON columns use the six planned cases as denominators; unattempted cases are unknown, not model failures. Full/supported criterion columns use only graded cases. See grades.json for exact criterion judgements and citations; protocol.json for hashes/commands; results/ for native status/usage/tool evidence; submissions/ for original notes.', '',
              '## Per-cell outcomes', '', '| Cell | Native status | Content full | Evidence full | JSON |', '|---|---|---|---|---|']
    for r in result['configurations']:
        for c in r['per_case']:
            lines.append(f"| {c['case']}-{r['route']['id']} | {c['status']} | {c['content_full']} | {c['evidence_full']} | {c['contract_valid']} |")
    lines += ['', '## Limits', '',
              '- One sample per synthetic task. This does not establish general model superiority or a permanent Researcher assignment.',
              '- Full/partial/missing content judgements are evaluation decisions, not deterministic benchmark test results. Live sources may change; retrieval/tool errors must not be relabeled as model factual defects.',
              '- Tokens include cached context under provider-specific definitions. Codex input already includes cache reads; Claude input/cache counters are added once. Missing usage remains unknown. No invoice price or equivalent subscription quota is inferred.',
              '- Codex streams may not attest effective model identity; absent reported identity is unknown, not confirmation. Effective effort is unknown without an explicit native attestation.',
              '- Provider/account/runtime/tools differ. Account quota can include unrelated concurrent sessions. No security-control or credential changes were made.', '']
    (ROOT / 'REPORT.md').write_text('\n'.join(lines))


if __name__ == '__main__':
    result = summarize()
    (ROOT / 'comparison.json').write_text(json.dumps(result, indent=2) + '\n')
    report(result)
    print(json.dumps({k: result[k] for k in ('planned_calls', 'started', 'graded')}))
