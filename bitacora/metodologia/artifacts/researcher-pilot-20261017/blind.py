"""Copy completed notes without route/usage labels for content evaluation."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    key = {}
    for case in json.loads((ROOT / 'cases.json').read_text()):
        notes = []
        for record in sorted((ROOT / 'results').glob(case['id'] + '-*.json')):
            row = json.loads(record.read_text())
            path = ROOT / 'submissions' / record.stem / 'research.json'
            if row['status'] == 'completed' and path.is_file() and not path.is_symlink():
                notes.append((record.stem, row, path))
        random.Random('researcher-hidden-' + case['id']).shuffle(notes)
        for i, (cell, row, path) in enumerate(notes):
            bid = case['id'] + '-' + chr(65 + i)
            target = ROOT / 'blind' / (bid + '.json')
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps({'blind_id': bid, 'case': case['id'],
                'note': json.loads(path.read_text()), 'contract_valid': row['contract']['valid'],
                'tool_calls': row.get('research_tool_calls', []),
                'tool_result_evidence': row.get('tool_result_evidence', [])}, indent=2) + '\n')
            key[bid] = cell
    (ROOT / 'blind-key.json').write_text(json.dumps(key, indent=2) + '\n')
    print('Prepared', len(key), 'notes with route labels hidden; coordinator holds key')


if __name__ == '__main__':
    build()
