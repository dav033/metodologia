"""Derive a transparent report from native cells and separate content grades."""
import json
from collections import Counter
from pathlib import Path

from records import load_records

ROOT = Path(__file__).resolve().parent


def read(name):
    return json.loads((ROOT / name).read_text())


def summarize():
    protocol = read('protocol.json')
    rows, _ = load_records()
    raw_record_count = sum(1 for folder in (ROOT / 'results', ROOT / 'continuation-codex-luis' / 'results') for _ in folder.glob('*.json'))
    original_grades = read('grades.json') if (ROOT / 'grades.json').exists() else {}
    supplemented = (ROOT / 'supplemental-grades.json').exists()
    grades = read('supplemental-grades.json') if supplemented else original_grades
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
                          'profile': row.get('route', {}).get('profile'),
                          'contract_valid': row.get('contract', {}).get('valid'), 'grade': grade,
                          'original_grade': original_grades.get(key),
                          'content_full': content_full if grade else None,
                          'evidence_full': evidence_full if grade else None,
                          'scope_valid': not row.get('scope_violations') and not row.get('unexpected_files'),
                          'seconds': row.get('seconds'), 'tokens': row.get('usage', {}).get('total')})
        quality = [c for c in cases if c['content_full'] and c['evidence_full'] and c['scope_valid']]
        profiles = dict(Counter(r['route']['profile'] for r in attempted))
        original_passes = sum(len(v['criteria']) == 6 and all(c['rating'] == 'full' and c['supported'] for c in v['criteria'])
                              for k, v in original_grades.items() if k in own)
        output.append({'route': route, 'effective_profiles': profiles, 'started': len(attempted), 'saved_records': len(own), 'native_statuses': dict(Counter(r['status'] for r in own.values())),
                       'original_content_and_evidence_cases': original_passes,
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
                       'unattested_model_cells': [k for k, r in own.items() if 'workspace_before' in r and not r.get('observed_models')],
                       'unattested_effort_cells': [k for k, r in own.items() if 'workspace_before' in r and not r.get('observed_efforts')],
                       'per_case': cases})
    started = sum('workspace_before' in row for row in rows.values())
    matched = [case['id'] for case in read('cases.json')
               if all(case['id'] + '-' + r['id'] in grades for r in protocol['routes'])]
    return {'planned_calls': 18, 'saved_records': raw_record_count, 'effective_cell_records': len(rows), 'started': started,
            'unattempted_native_cells': 18 - started, 'graded': len(grades),
            'matched_cases': matched, 'complete_comparison': started == 18 and len(grades) == 18,
            'posthoc_source_adjudication': supplemented,
            'configurations': output}


def report(result):
    lines = ['# Researcher pilot: native matched comparison', '',
             f"Native calls: {result['started']}/18; saved operational records: {result['saved_records']}; content evaluations: {result['graded']}/18.", '',
             ('Complete comparison.' if result['complete_comparison'] else
              'INCOMPLETE: execution or grading is missing. Unequal task coverage prevents ranking route totals. '
              + 'Matched cases only: ' + ', '.join(result['matched_cases']) + '.'), '',
             'The table includes the separately labeled posthoc source adjudication below; original reviewer grades remain preserved.', '',
             '| Configuration | Native calls | Frozen content+cites | Live content+cites | Full criteria (adjudicated) | Supported criteria (adjudicated) | JSON contract | Seconds | Tokens (coverage) |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in result['configurations']:
        token = f"{r['tokens']:,}" if r['tokens'] is not None else 'unknown'
        n = 6 * r['graded_cases']
        lines.append(f"| {r['route']['id']} | {r['started']}/6 | {r['frozen_pass']}/4 | {r['live_pass']}/2 | {r['full_criteria']}/{n} | {r['supported_criteria']}/{n} | {r['contract_cases']}/6 | {r['seconds']:.3f} | {token} ({r['token_coverage']}) |")
    lines += ['', '## Protocol and grading', '',
              'Owner authorized this comparison after the web-research proposal. Three pinned models/efforts, six tasks each, one call/cell; no retries, repair turns or model substitution. Profiles: Sonnet claude-work; Sol/Luna R1 on codex-2. Owner then explicitly authorized codex-luis for the ten never-invoked R2-R6 cells. One active call per account. Native results and original quota preflight are preserved independently from content judgements.', '',
              'R1 asyncio concurrency; R2 cross-version SQLite lifetime; R3 Node HTTP deadlines; R4 PostgreSQL concurrent-index failures; R5 Node release dates as of2026-10-17; R6 uv synchronization and network guarantees. Frozen extracts have original line numbers. Live tools differ by provider; interpret frozen and live results separately.', '',
              'Each of36 criteria per route is graded full/partial/missing and separately source-supported or unsupported. A content+citation case passes only when all six criteria are full and supported, with no scope violations. JSON contract is a separate column; original responses are never repaired. Labels are hidden for content grading where practical; coordinator may know routes, so this is not a fully blind or statistical comparison.', '',
              'Case-pass and JSON columns use planned cases as denominators; unattempted cases are unknown, not model failures. Full/supported criterion columns use only graded cases. See grades.json for original criterion judgements, supplemental-grades.json for source adjudication, protocol.json for hashes/commands, results/ and continuation-codex-luis/results/ for native evidence, and corresponding submissions/ for original notes.', '',
              '## Operational stop and concrete findings', '',
              ('Codex-2 reached100% five-hour usage (weekly16%) before R2 Luna. That original preflight record is not a native invocation or a model failure. '
               'The original lane stopped with ten unattempted cells. The owner explicitly authorized codex-luis, recorded in continuation-codex-luis/authorization.json. '
               f"Current native calls: {result['started']}/18; unattempted: {result['unattempted_native_cells']}. "
               'Original execution-summary.json is historical; continuation status is separate. The eight initial calls, original preflight and partial report remain preserved; no call was repeated.'), '',
              'Sonnet R1 covers all six requested facts, but adds historical ExceptionGroup/except* details unsupported by the frozen extract while acknowledging that limitation: full content, one unsupported-evidence criterion. Sonnet live cases each record two successful WebFetch calls with no tool errors; R6 CLI reference was truncated and the candidate disclosed this. Codex records search/open/find events but not full page bodies; exact retrieval and rendered locators cannot all be independently attested from saved native events. Coordinator primary-source checks corroborated the requested facts and extra Node patch/Docker claims without new native calls.', '',
              'A separate coordinator adjudication makes R2/C5 full: the answer correctly handles the explicitly asked Python3.11 compatibility/version question; an extra hidden-rubric distinction about SQLite autocommit was not an explicit question. Frozen rubric, source, candidate response and initial reviewer partial remain preserved in grading-spec-original.json and grading-adjudications.json. No native response was repaired.', '',
              '## Separate posthoc published-source adjudication', '',
              'Initial source reviewers marked R6/C5 partial for Sonnet and Luna because their wording differed from the upstream GitHub snapshot. Direct coordinator verification found that the published official concepts page uses the lockfile wording and the published CLI page uses the project-dependency wording, including the stated conflict/build-isolation qualifications. These LIVE responses should not be penalized for accurately reflecting those published sources. All three routes therefore receive full/supported R6/C5 in a separate supplement; frozen rubric, source snapshots, original grades and native responses remain unchanged. This is source adjudication, not proof of all runtime synchronization edge cases.', '',
              '[Published concepts](https://docs.astral.sh/uv/concepts/projects/sync/), [published CLI](https://docs.astral.sh/uv/reference/cli/). See supplemental-source-adjudication.json for exact coordinator checks, source drift and limitations.', '',
              '| Configuration | Original content+citation cases | After source adjudication |', '|---|---:|---:|']
    for r in result['configurations']:
        lines.append(f"| {r['route']['id']} | {r['original_content_and_evidence_cases']}/6 | {r['content_and_evidence_cases']}/6 |")
    lines += ['',
              '## Effective accounts', '', '| Configuration | Effective profile: native calls |', '|---|---|']
    for r in result['configurations']:
        profiles = ', '.join(f'{p}: {n}' for p, n in r['effective_profiles'].items())
        lines.append(f"| {r['route']['id']} | {profiles} |")
    lines += ['', 'The account change is a comparison limitation: Sol/Luna totals combine two profiles. Model/effort, prompts and frozen corpora remain fixed; no account-quota equivalence or controlled account-effect claim is made.', '',
              '## Per-cell outcomes', '', '| Cell | Profile | Native status | Content full | Evidence full | JSON |', '|---|---|---|---|---|---|']
    for r in result['configurations']:
        for c in r['per_case']:
            lines.append(f"| {c['case']}-{r['route']['id']} | {c['profile']} | {c['status']} | {c['content_full']} | {c['evidence_full']} | {c['contract_valid']} |")
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
