"""Build the additive r19 candidate: repair C7/C8/C9, then release evidence and owner phone evidence before the audits."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import bt_plan_adapter

RDIR = Path('/home/david/bitacora/pictures/requirements/REQ-020-happia-chat-v2-event-advisor-that-ends-i')
OUT = Path(__file__).parent / 'remediation-r19.json'
plan = bt_plan_adapter.latest_plan(RDIR)
assert plan and plan['revision'] == 18
candidate = copy.deepcopy(plan)
candidate['revision'] = 19
by_id = {task['id']: task for task in plan['tasks']}


def task(identifier, title, objective, paths, after, criteria, covers, *, kind='implement', minutes=120):
    result = copy.deepcopy(by_id['T15.4'])
    result.update(id=identifier, title=title, objective=objective, expected_paths=paths, after=after,
                  acceptance_criteria=criteria, verification=[], covers=covers, kind=kind, shared_resources=[],
                  estimated_minutes=minutes,
                  estimate_rationale=f'Provisional bounded estimate {minutes} minutes on the existing integrated tree; owner wait excluded.')
    reasons = {
        'complexity': 'High: touches summary, brief and customer card contracts that already passed independent acceptance.',
        'scope': 'Bounded corrective surface; every accepted task specification is left unchanged.',
        'duration': f'Provisional {minutes} minutes; no measured comparable duration is claimed.',
        'risk': 'High: a lost price or freshness caveat misleads the customer, and false closure would hide missing release evidence.',
        'coupling': 'High: consumes the T4/T5/T13/T15.3 contracts; dependencies order repair, release evidence and audits.',
        'confidence': 'Medium: the sealed cross-check reproduced the defects, the repaired behavior is still unverified.'}
    for axis in result['classification_evidence']:
        result['classification_evidence'][axis] = {'evidence': ['task:T15b', 'spec:SPEC.md#scope-in'],
                                                   'justification': reasons[axis]}
    return result


def command(identifier, value, purpose, category='functional'):
    return {'type': 'command', 'value': value, 'purpose': purpose, 'created_by': identifier, 'category': category}


repair = task('T15.7', 'Repair package commercial facts, card disclosures and photo-only send',
    'Repair sealed T15b findings C7, C8 and C9 on the current integrated tree without reopening any accepted task. '
    'C7: the approved summary and the delivered brief must carry the package estimated COP price, its source and catalogue freshness, '
    'not only the package name and id (src/lib/asesor/tools.ts propose_summary stores name/id only; src/lib/asesor/brief.ts projects state.brief without standardPackage). '
    'C8: the customer package card must show catalogue freshness and the unknown event/theme/city/capacity disclosures the server sends '
    '(src/components/asesor/conversation-contract.ts strips and never renders them), also after restore. '
    'C9: a customer with a selected photo and an empty textarea must be able to send (Composer.tsx disables Enviar with !value.trim(); useConversation already supports photo-only turns). '
    'First reproduce each defect with a failing test (the sealed audit evidence names exact probes), then fix; add regression tests that fail if the price, source, freshness or disclosures are dropped again. '
    'Keep Spanish product language, privacy rules, idempotent retries and /happie unchanged. No deployment, production writes, commits or pushes.',
    ['src/lib/asesor', 'src/components/asesor', 'scripts/test/asesor/package-facts.test.ts',
     'scripts/test/asesor/ui-remediation.test.ts', 'scripts/e2e/asesor/ui-remediation.ts'],
    ['T15.6'],
    ['The approved summary and brief carry package price, source and freshness; the package card shows freshness and disclosures after streaming and restore; a selected photo can be sent without text.'],
    ['R4', 'R5', 'R7', 'R9', 'R10', 'R11'])
criterion = repair['acceptance_criteria'][0]
repair['verification'] = [command('T15.7', value, criterion) for value in (
    'npm run asesor:test', 'npx tsx --conditions=react-server --test scripts/test/asesor/package-facts.test.ts',
    'npx tsx scripts/e2e/asesor/ui-remediation.ts', 'npx tsc --noEmit', 'npm run build', 'npm run happie:test-webhook')]

evidence = task('T15.8', 'Install revision-bound release, deployed M1/M2 and live-matrix evidence',
    'Copy, unchanged, the supervisor-produced evidence for the repaired release from '
    '/home/david/bitacora/pictures/artifacts/req020-r19-release into docs/req-020: integration-results.json (deployed and local-live runs on the released revision, tree_digest equal to the source digest of this tree) '
    'and live-acceptance.md (full real-model nine-scenario, negative/privacy/provider-retry matrix with redacted outcomes). '
    'Verify the report with the approved checker. If the artifact directory or a file is missing, or its revision/tree_digest does not match this tree, stop with status blocked and say so; never edit evidence, never run live or deployment commands. '
    'No commits or pushes.',
    ['docs/req-020/integration-results.json', 'docs/req-020/live-acceptance.md'], ['T15.7'],
    ['docs/req-020 holds the revision-bound deployed and live evidence of the repaired release, unmodified from the supervisor artifact, with a passing report check.'],
    ['R1', 'R2', 'R3', 'R7', 'R9', 'R10', 'R11', 'R13', 'R14'], kind='test', minutes=45)
criterion = evidence['acceptance_criteria'][0]
evidence['verification'] = [
    command('T15.8', 'test -s docs/req-020/live-acceptance.md', criterion, 'static'),
    command('T15.8', 'npx tsx --conditions=react-server scripts/e2e/asesor/run.ts --check-results docs/req-020/integration-results.json', criterion),
    {'type': 'manual', 'value': 'Supervisor ran the deployed M1/M2 and the full live matrix against the released revision and attests the exact commands, revision and outcomes.',
     'purpose': criterion, 'expected': 'Revision-bound deployed and live evidence exists and every recorded run passed on the released revision; absent or failing runs must not pass.',
     'category': 'integration'}]

phone = task('T15.9', 'Install the owner physical-phone observations',
    'Copy, unchanged, the owner-supplied physical-phone observations for the released revision from '
    '/home/david/bitacora/pictures/artifacts/req020-r19-release/phone-observations.md into docs/req-020/phone-observations.md. '
    'If the file does not exist, stop with status blocked and say that only David can supply it; never write or infer observations. '
    'Required observations: login/notices, keyboard, camera/gallery/microphone allow/deny/recovery, media display, same-device reload, summary approval/print/admin. '
    'No commits or pushes.',
    ['docs/req-020/phone-observations.md'], ['T15.8'],
    ['docs/req-020/phone-observations.md holds David\'s revision-bound physical-phone observations, unmodified.'],
    ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9', 'R10', 'R11', 'R12', 'R13', 'R14'], kind='test', minutes=20)
criterion = phone['acceptance_criteria'][0]
phone['verification'] = [
    command('T15.9', 'test -s docs/req-020/phone-observations.md', criterion, 'static'),
    {'type': 'manual', 'value': 'David performed the physical-phone checks on the released revision and supplied the observations.',
     'purpose': criterion, 'expected': 'Actual owner observations tied to the released revision, covering every listed area; absent or partial evidence must not pass.',
     'category': 'product'}]

candidate['tasks'].extend([repair, evidence, phone])
for row in candidate['tasks']:
    if row['id'] in ('T15', 'T15b'):
        row['after'] = list(dict.fromkeys([*row['after'], 'T15.9']))
assert all(next(t for t in candidate['tasks'] if t['id'] == old['id']) == old
           for old in plan['tasks'] if old['id'] not in ('T15', 'T15b'))
errors = bt_plan_adapter.plan_errors(candidate)
if errors:
    raise SystemExit('\n'.join(map(str, errors)))
OUT.write_text(json.dumps(candidate, indent=1, ensure_ascii=False) + '\n')
print(f'Prepared {OUT}: three additive tasks, all accepted specifications unchanged.')
