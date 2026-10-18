import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

from app.cli import main
from app.cursor import encode_cursor
from app.repository import Repository

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(argv=None, repo=None):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv, repo=repo)
    return code, out.getvalue(), err.getvalue()


class MainTest(unittest.TestCase):
    def setUp(self):
        self.rows = [{'timestamp': i, 'id': f'id{i}', 'payload': {'n': i}} for i in range(5)]

    def test_prints_first_page_as_json(self):
        code, out, err = _run(['--limit', '2'], repo=Repository(self.rows))
        self.assertEqual(code, 0)
        self.assertEqual(err, '')
        page = json.loads(out)
        self.assertEqual([row['id'] for row in page['items']], ['id0', 'id1'])
        self.assertEqual(page['next_cursor'], encode_cursor(1, 'id1'))
        self.assertEqual(out.count('\n'), 1)

    def test_default_repository_is_empty_and_default_limit_is_20(self):
        code, out, err = _run([])
        self.assertEqual((code, err), (0, ''))
        self.assertEqual(json.loads(out), {'items': [], 'next_cursor': None})

    def test_default_limit_is_20(self):
        rows = [{'timestamp': i, 'id': str(i)} for i in range(25)]
        _, out, _ = _run([], repo=Repository(rows))
        page = json.loads(out)
        self.assertEqual(len(page['items']), 20)
        self.assertIsNotNone(page['next_cursor'])

    def test_cursor_traversal_through_cli(self):
        repo = Repository(self.rows)
        seen, cursor = [], None
        while True:
            argv = ['--limit', '2'] + (['--cursor', cursor] if cursor else [])
            code, out, _ = _run(argv, repo=repo)
            self.assertEqual(code, 0)
            page = json.loads(out)
            seen.extend(row['id'] for row in page['items'])
            cursor = page['next_cursor']
            if cursor is None:
                break
        self.assertEqual(seen, [row['id'] for row in self.rows])

    def test_help_returns_zero_without_raising(self):
        code, out, err = _run(['--help'])
        self.assertEqual(code, 0)
        self.assertIn('--cursor', out)
        self.assertEqual(err, '')

    def test_invalid_input_returns_two_with_stderr_only(self):
        cases = [
            ['--limit', 'abc'],
            ['--limit', '1.5'],
            ['--limit'],
            ['--limit', '0'],
            ['--limit', '101'],
            ['--limit', '-3'],
            ['--cursor', ''],
            ['--cursor', 'not*base64'],
            ['--cursor', 'W'],
            ['--cursor', encode_cursor(1, 'id1') + '='],
            ['--cursor'],
            ['--unknown'],
            ['extra-positional'],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                code, out, err = _run(argv, repo=Repository(self.rows))
                self.assertEqual(code, 2)
                self.assertEqual(out, '')
                self.assertTrue(err.strip())

    def test_invalid_cursor_payload_returns_two(self):
        bad = encode_cursor(1, 'id1')[:-1] + 'R'
        code, out, err = _run(['--cursor', bad], repo=Repository(self.rows))
        self.assertEqual((code, out), (2, ''))
        self.assertTrue(err.startswith('error: '))


class ModuleEntryPointTest(unittest.TestCase):
    def _run_module(self, *args):
        return subprocess.run(
            [sys.executable, '-m', 'app.cli', *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_python_dash_m_exits_with_main_return_code(self):
        result = self._run_module()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), {'items': [], 'next_cursor': None})

    def test_python_dash_m_invalid_option_exits_two_silently_on_stdout(self):
        result = self._run_module('--limit', '0')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, '')
        self.assertTrue(result.stderr.strip())


if __name__ == '__main__':
    unittest.main()
