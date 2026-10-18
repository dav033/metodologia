"""Merge effective cells while preserving original operational history."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load_records():
    rows, submissions = {}, {}
    for path in (ROOT / 'results').glob('*.json'):
        rows[path.stem] = json.loads(path.read_text())
        submissions[path.stem] = ROOT / 'submissions' / path.stem
    pending = {r['cell']: r for r in json.loads((ROOT / 'pending-cells.json').read_text())}
    for path in (ROOT / 'continuation-codex-luis' / 'results').glob('*.json'):
        cell = path.stem
        if cell not in pending or 'workspace_before' in rows.get(cell, {}):
            raise RuntimeError('Duplicate or unauthorized continuation cell: ' + cell)
        row = json.loads(path.read_text())
        expected = {**pending[cell]['route'], 'profile': 'codex-luis'}
        if row.get('route') != expected or row.get('case') != pending[cell]['case']:
            raise RuntimeError('Continuation route/case drift: ' + cell)
        rows[cell] = row
        submissions[cell] = ROOT / 'continuation-codex-luis' / 'submissions' / cell
    return rows, submissions
