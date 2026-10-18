"""Separate posthoc adjudication; never rewrite original native/test evidence."""
from __future__ import annotations

import json

from pilot_common import INSTRUCTION, ROOT, ROUTES, digest, save
from pilot_grade import grade
from supplement_encoding import adjusted_case


def evaluate() -> list[dict]:
    case = next(c for c in json.loads((ROOT / 'cases.json').read_text()) if c['id'] == 'I6')
    semantic_case = adjusted_case(case)
    semantic_case['starter']['TASK.md'] = INSTRUCTION + case['prompt']
    evidence = []
    for route in ROUTES:
        submitted = ROOT / 'submissions' / f'I6-{route["id"]}'
        if not submitted.exists():
            continue
        result = grade(semantic_case, submitted)
        evidence.append({'cell': submitted.name, 'posthoc': True, 'grade': result})
        print(submitted.name, 'semantic', result['status'], result.get('failures'), result.get('errors'))
    save(ROOT / 'supplement-semantics.json', evidence)
    save(ROOT / 'supplement-provenance.json', {
        'posthoc': True,
        'trigger': 'I6 Luna medium and Haiku xhigh produced valid alternative JSON envelopes, revealing unspecified body encoding/key names; separate explicit connection-close requirement was untested.',
        'rule': 'Accept exact raw result or minimal JSON with correct result and optional matching id/job_id; preserve actual delivered body byte-for-byte in inbox; no other assertions relaxed.',
        'scope': 'Apply semantic adjustment to all eight I6 submissions; resource witness to all24 I4/I5/I6 submissions, gating required APIs by case ID.',
        'original_scores_preserved': True, 'candidate_edits': False, 'additional_native_calls': 0,
        'files': {name: digest((ROOT / name).read_bytes()) for name in (
            'supplement_encoding.py', 'supplement_resources.py', 'pilot_supplement.py')},
        'limitations': 'Posthoc supplemental evidence is not the predeclared benchmark score. Extra resource checks do not certify every possible leak/error path.'})
    return evidence


if __name__ == '__main__':
    evaluate()
