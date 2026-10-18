"""Posthoc, uniform SQLite lifecycle witness; original benchmark is immutable."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pilot_common import ROOT, materialize, save
from pilot_grade import run_tests

TEST_SOURCE = '''import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = os.path.join(self.tmp.name, 'db')
        self.created = []
        self.real_connect = sqlite3.connect
        def tracked(*args, **kwargs):
            connection = self.real_connect(*args, **kwargs)
            self.created.append(connection)
            return connection
        self.patch = patch('sqlite3.connect', tracked)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        for name in list(sys.modules):
            if name == 'app' or name.startswith('app.'):
                del sys.modules[name]
        self.store = importlib.import_module('app.store')
        self.addCleanup(self.close_all)

    def close_all(self):
        for connection in self.created:
            connection.close()

    def check_operation(self, label, function, error=None):
        with self.subTest(operation=label):
            before = len(self.created)
            try:
                if error is None:
                    function()
                else:
                    with self.assertRaises(error):
                        function()
                leaked = []
                for connection in self.created[before:]:
                    try:
                        connection.execute('SELECT 1')
                    except sqlite3.ProgrammingError:
                        pass
                    else:
                        leaked.append(connection)
                self.assertFalse(leaked, f'{label}: {len(leaked)} connection(s) usable after API return')
            finally:
                for connection in self.created[before:]:
                    connection.close()

    def legacy(self, path):
        connection = self.real_connect(path)
        try:
            connection.execute('CREATE TABLE items(id INTEGER PRIMARY KEY,value TEXT NOT NULL)')
            connection.execute("INSERT INTO items VALUES(7,' HELLO ')")
            connection.commit()
        finally:
            connection.close()

    def test_success_paths_close(self):
        s, p = self.store, self.path
        if hasattr(s, 'migrate'):
            self.legacy(p)
            self.check_operation('migrate', lambda: s.migrate(p))
            self.check_operation('migrate_noop', lambda: s.migrate(p))
            self.check_operation('read_items', lambda: s.read_items(p))
            return
        self.check_operation('init', lambda: s.init(p))
        self.check_operation('enqueue', lambda: s.enqueue(p, 'a', 'data'))
        self.check_operation('duplicate_enqueue', lambda: s.enqueue(p, 'a', 'other'))
        self.check_operation('claim', lambda: s.claim(p, 0, 5))
        self.check_operation('inspect', lambda: s.inspect(p, 'a'))
        self.check_operation('complete', lambda: s.complete(p, 'a', 1, 'ok', 1))
        self.check_operation('empty_claim', lambda: s.claim(p, 1, 5))
        self.check_operation('stale_complete', lambda: s.complete(p, 'a', 1, 'bad', 1))
        self.check_operation('missing_inspect', lambda: s.inspect(p, 'missing'))
        if HAS_OUTBOX:
            self.check_operation('publish', lambda: s.publish(p, lambda i, b: s.consume(p, i, b)))
            self.check_operation('consume_duplicate', lambda: s.consume(p, 'a', 'other'))
            self.check_operation('enqueue_retry_job', lambda: s.enqueue(p, 'b', 'data'))
            self.check_operation('claim_retry_job', lambda: s.claim(p, 2, 5))
            self.check_operation('retry', lambda: s.retry(p, 'b', 1, 3))
            self.check_operation('stale_retry', lambda: s.retry(p, 'b', 1, 3))

    def test_error_paths_close(self):
        s, p = self.store, self.path
        def fail(*_):
            raise RuntimeError('injected resource witness')
        if hasattr(s, 'migrate'):
            self.legacy(p)
            self.check_operation('migrate_fault', lambda: s.migrate(p, fail), RuntimeError)
            return
        self.check_operation('init', lambda: s.init(p))
        self.check_operation('enqueue', lambda: s.enqueue(p, 'a', 'data'))
        self.check_operation('invalid_ttl', lambda: s.claim(p, 0, 0), ValueError)
        if HAS_OUTBOX:
            self.check_operation('claim', lambda: s.claim(p, 0, 10))
            self.check_operation('complete_fault', lambda: s.complete(p, 'a', 1, 'ok', 1, fail), RuntimeError)
            self.check_operation('complete_success', lambda: s.complete(p, 'a', 1, 'ok', 1))
            self.check_operation('publish_fault', lambda: s.publish(p, lambda i, b: fail(i)), RuntimeError)
'''


def check_submission(case: dict, directory: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix='implementer-resource-') as temporary:
        root = Path(temporary)
        sources = {str(p.relative_to(directory)): p.read_text()
                   for p in (directory / 'app').rglob('*.py') if not p.is_symlink()}
        materialize(root, sources)
        materialize(root, {'test_resources.py': f'HAS_OUTBOX = {case["id"] == "I6"!r}\n' + TEST_SOURCE})
        result = run_tests(root, 'test_resources.py')
    result['case'] = case['id']
    result['posthoc'] = True
    return result


def validate_reference() -> None:
    cases = json.loads((ROOT / 'cases.json').read_text())
    evidence = []
    for case in cases:
        if case['id'] not in ('I4', 'I5', 'I6'):
            continue
        with tempfile.TemporaryDirectory(prefix='implementer-resource-reference-') as directory:
            root = Path(directory)
            materialize(root, {**case['starter'], **case['reference']})
            result = check_submission(case, root)
            assert result['status'] == 'passed', result
            evidence.append({'case': case['id'], 'tests': result['tests'], 'passed': True})
    save(ROOT / 'supplement-resource-validation.json', evidence)


if __name__ == '__main__':
    validate_reference()
    cases = {c['id']: c for c in json.loads((ROOT / 'cases.json').read_text())}
    rows = []
    for path in sorted((ROOT / 'submissions').iterdir()):
        case = cases[path.name.split('-')[0]]
        if case['id'] not in ('I4', 'I5', 'I6'):
            continue
        result = check_submission(case, path)
        result['cell'] = path.name
        rows.append(result)
        print(path.name, result['status'], result.get('failures'), result.get('errors'))
    save(ROOT / 'supplement-resources.json', rows)
