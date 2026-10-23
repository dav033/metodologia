"""Build a bounded additive remediation candidate without changing the live run."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import bt_plan_adapter

RDIR = Path('/home/david/bitacora/pictures/requirements/REQ-020-happia-chat-v2-event-advisor-that-ends-i')
OUT = Path(__file__).parent / 'remediation-r18.json'
plan = bt_plan_adapter.latest_plan(RDIR)
assert plan and plan['revision'] == 17
candidate = copy.deepcopy(plan)
candidate['revision'] = 18
by_id = {task['id']: task for task in plan['tasks']}


def task(identifier, title, objective, paths, after, criteria, commands, covers, *, kind='implement', minutes=180):
    result = copy.deepcopy(by_id['T4'])
    result.update(id=identifier, milestone_id='M4', title=title, objective=objective,
                  expected_paths=paths, after=after, acceptance_criteria=criteria,
                  verification=[], covers=covers, kind=kind, shared_resources=[],
                  estimated_minutes=minutes, complexity='high', scope='full_feature',
                  risk='high', coupling='high', confidence='medium',
                  estimate_rationale=f'Provisional bounded repair estimate {minutes} minutes: implementation and regression evidence on the existing integrated tree; human release wait excluded.')
    reasons = {
        'complexity': 'High: reconciles structured asynchronous state and independent acceptance across existing advisor contracts; a local label change cannot close the sealed findings.',
        'scope': 'Full feature repair: one declared corrective surface with executable behavior checks, while all original accepted task specifications remain unchanged.',
        'duration': f'Provisional {minutes} minutes for implementation and fresh checks on the integrated tree; no measured comparable duration is claimed and external owner wait is excluded.',
        'risk': 'High: false closure could expose private conversation data or approve stale summary/release evidence, so checks must fail closed.',
        'coupling': 'High: consumes existing SSE/restore, media, offers and brief contracts; dependencies explicitly order corrective work before release evidence and final audits.',
        'confidence': 'Medium: sealed independent audits and current source establish the defects, while exact repaired behavior and owner-only acceptance remain unverified.'}
    for axis in result['classification_evidence']:
        result['classification_evidence'][axis] = {
            'evidence': ['task:T15', 'task:T15b', 'spec:SPEC.md#scope-in'],
            'justification': reasons[axis]}
    for criterion in criteria:
        for command in commands:
            result['verification'].append({'type': 'command', 'value': command, 'purpose': criterion,
                                           'created_by': identifier, 'category': 'functional'})
    return result


ui = task('T15.3', 'Repair customer photo, offer-card and authoritative summary flows',
    'Repair sealed att-0123 F5/F6/F8 and att-0124 X1/X2/X3 on the current integrated tree. '
    'Wire camera/gallery upload through the existing authenticated photo API, persisted attachments, structured direction/package state, '
    'authoritative summary/correction/approval and printable-brief navigation. Validate SSE and restore payloads before use. '
    'Keep Spanish product language and existing Pictures visual conventions. Preserve voice, privacy, retries and happie. '
    'First reproduce each defect using the actual ChatView/useConversation in deterministic browser tests with controlled authenticated API/SSE fixtures '
    '(system Chromium /usr/bin/chromium is available). Test real DOM interactions, upload failure/retry, SSE and reload, card selection/image/source/price, '
    'summary correction invalidating approval, and approved brief link. Replace obsolete static tests asserting photo=false/cards=[] with behavior tests; '
    'retain their original privacy/retry invariants. Do not treat emulation as physical-phone acceptance. '
    'No deployment, production writes, commits, pushes, or changes outside the declared advisor surface. No new dependency without justification.',
    ['src/components/asesor', 'scripts/test/asesor/chat-ui.test.ts', 'scripts/test/asesor/ui-remediation.test.ts',
     'scripts/e2e/asesor/ui-remediation.ts', 'scripts/e2e/asesor/scenarios/text.ts'],
    ['T14a', 'T15.1', 'T15.2'],
    ['Actual chat UI supports photo upload/display, sourced offer cards and current summary approval/brief navigation through both streaming and restore, with privacy and idempotent retry preserved.'],
    ['npm run asesor:test', 'npx tsx --test scripts/test/asesor/ui-remediation.test.ts',
     'npx tsx scripts/e2e/asesor/ui-remediation.ts', 'npx tsc --noEmit', 'npm run build'], ['R4', 'R5', 'R7', 'R9', 'R10', 'R11'])

evaluation = task('T15.4', 'Repair nine-scenario evaluation and negative/privacy acceptance coverage',
    'Close automatable portions of att-0123 F4 and att-0124 X5 without asserting missing production/phone acceptance. '
    'Preserve all nine versioned scenarios and separate fake-port deterministic invariants from real-model outcomes. '
    'Extend deterministic harness coverage for contact/address refusal, off-topic/injection, vendor redaction, sourced direction/package price and fallback freshness, '
    'and provider failure/retry without duplicated turns. Add regression tests that fail if a required scenario/assertion is omitted. '
    'Use existing selected model and ports; keep outcome artifacts redacted and explicitly report unexecuted live checks. '
    'Prepare exact coordinator commands for the full live matrix on the repaired snapshot; never relabel fake-model results as live. '
    'Modify prompts only when a reproduced failing behavioral assertion needs it. No deployment, production mutation, commits or pushes.',
    ['scripts/eval/asesor', 'scripts/e2e/asesor/scenarios/m1.ts', 'scripts/e2e/asesor/scenarios/m2.ts',
     'scripts/test/asesor/evaluation-remediation.test.ts', 'src/lib/asesor/prompts', 'docs/req-020/remediation-evaluation.md'],
    ['T15.3'],
    ['All nine versioned scenarios and required negative/privacy/provider-failure invariants have executable deterministic coverage, with live evaluation explicitly distinguished and pending where unexecuted.'],
    ['npm run asesor:test', 'npx tsx --conditions=react-server --test scripts/test/asesor/evaluation-remediation.test.ts',
     'npx tsx --conditions=react-server scripts/eval/asesor/run.ts --fake-model', 'npx tsc --noEmit', 'npm run build'], ['R3', 'R7', 'R9', 'R10', 'R11', 'R13'])

evidence = task('T15.5', 'Prepare repaired-tree evidence and exact owner release checklist',
    'Run local deterministic UI/evaluation checks for T15.3/T15.4 and prepare docs/req-020/remediation-readiness.md. '
    'Bind every result to the resulting revision/tree, record exact commands, exit codes and redacted artifact references. '
    'Reconcile historical F10 against the exact immutable local-live-receipt.json in bitacora/pictures/artifacts/req020-supervisor-root-cause: '
    'the supervisor restored original bytes at 13:18 and its digest is sha256:56f81d7d1cba375a911244c6d621a61b32574cb9e984a04e6adc917d26e9ec30. '
    'Do not edit sealed audit results or assert that old receipts cover this repaired tree. '
    'Write exact local live nine-scenario coordinator command and release/deployed/physical-phone checklist. '
    'Keep deployed c25a5f42 evidence historical; repaired source is not released. No deploy, production writes, commits or pushes. '
    'This task prepares evidence, not acceptance of missing phone or release checks.',
    ['docs/req-020/remediation-readiness.md'], ['T15.4'],
    ['Repaired-tree readiness report preserves provenance and distinguishes local checks, historical receipts, pending live evaluation and owner-only release/physical-phone evidence.'],
    ['test -s docs/req-020/remediation-readiness.md', 'npx tsx scripts/e2e/asesor/ui-remediation.ts',
     'npx tsx --conditions=react-server scripts/eval/asesor/run.ts --fake-model', 'npm run happie:test-webhook'],
    ['R3', 'R7', 'R9', 'R10', 'R11', 'R13', 'R14'], kind='test', minutes=90)

release = task('T15.6', 'Await owner-authorized release and physical-phone acceptance evidence',
    'Prepare docs/req-020/remediation-release-evidence.md from T15.5, explicitly pending. '
    'No new production deployment is authorized. Only David can authorize release and provide physical-phone observations. '
    'Do not execute deployment commands or claim a release/phone check happened. '
    'The independent verifier must leave the manual criterion pending until real owner evidence is supplied for the repaired revision. '
    'Required evidence: released revision and fresh deployed M1/M2 plus full real-model nine-scenario/negative/privacy/provider retry matrix, '
    'and physical-phone login/notices, keyboard, camera/gallery/microphone allow/deny/recovery, media display, same-device reload, summary approval/print/admin. '
    'Report failures as failures. Preserve historic evidence. No commits or pushes.',
    ['docs/req-020/remediation-release-evidence.md'], ['T15.5'],
    ['Owner-authorized repaired release, full live acceptance matrix and physical-phone observations are supplied with revision-bound redacted evidence; unexecuted checks remain unaccepted.'],
    [], ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14'], kind='test', minutes=45)
criterion = release['acceptance_criteria'][0]
release['verification'] = [
    {'type': 'command', 'value': 'test -s docs/req-020/remediation-release-evidence.md', 'purpose': criterion,
     'created_by': 'T15.6', 'category': 'static'},
    {'type': 'manual', 'value': 'David supplies explicit release authorization and revision-bound physical-phone observations; verify fresh deployed M1/M2 and full live scenario/negative/privacy/provider-retry evidence on that repaired release.',
     'purpose': criterion, 'expected': 'Actual owner authorization and complete revision-bound release/live/physical-phone evidence, with no unresolved high findings. Pending or absent evidence must not pass.', 'category': 'product'}]

candidate['tasks'].extend([ui, evaluation, evidence, release])
for row in candidate['tasks']:
    if row['id'] in ('T15', 'T15b'):
        row['after'] = list(dict.fromkeys([*row['after'], 'T15.6']))
assert all(next(t for t in candidate['tasks'] if t['id'] == old['id']) == old
           for old in plan['tasks'] if old['id'] not in ('T15', 'T15b'))
errors = bt_plan_adapter.plan_errors(candidate)
if errors:
    raise SystemExit('\n'.join(map(str, errors)))
OUT.write_text(json.dumps(candidate, indent=1, ensure_ascii=False) + '\n')
print(f'Prepared {OUT}: four additive tasks, all 22 accepted specifications unchanged; final audits await owner evidence.')
