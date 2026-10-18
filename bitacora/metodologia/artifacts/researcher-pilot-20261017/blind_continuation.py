"""Hide labels for new notes without changing the original blind artifacts."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build():
    folder = ROOT / 'continuation-codex-luis'
    mapping = {}
    for case in json.loads((ROOT / 'cases.json').read_text()):
        notes = []
        for record in sorted((folder / 'results').glob(case['id'] + '-*.json')):
            row = json.loads(record.read_text())
            path = folder / 'submissions' / record.stem / 'research.json'
            if row['status'] == 'completed' and path.is_file() and not path.is_symlink():
                notes.append((record.stem, row, path))
        random.Random('researcher-cont-hidden-' + case['id']).shuffle(notes)
        for index, (cell, row, path) in enumerate(notes):
            bid = case['id'] + '-' + chr(65 + index)
            target = folder / 'blind' / (bid + '.json')
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps({'blind_id': bid, 'case': case['id'],
                'note': json.loads(path.read_text()), 'contract_valid': row['contract']['valid'],
                'tool_calls': row.get('research_tool_calls', []),
                'tool_result_evidence': row.get('tool_result_evidence', [])}, indent=2) + '\n')
            mapping[bid] = cell
    (folder / 'blind-key.json').write_text(json.dumps(mapping, indent=2) + '\n')
    print('Prepared', len(mapping), 'new route-hidden notes; original blind artifacts unchanged')


if __name__ == '__main__':
    build()
