import base64
import contextlib
import copy
import io
import json
import subprocess
import sys
import unittest

from app.cli import main
from app.repository import Repository, decode_cursor, encode_cursor
from app.service import list_items


class PaginationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {'timestamp': 2, 'id': 'z', 'payload': {'values': [1]}},
            {'timestamp': 1, 'id': 'b'},
            {'timestamp': 1, 'id': 'a'},
            {'timestamp': -1, 'id': 'é雪'},
        ]

    def test_static_traversal(self):
        for size in (1, 2, 3, 4, 100):
            with self.subTest(size=size):
                repo = Repository(self.rows)
                cursor = None
                items = []
                for _ in range(5):
                    page = list_items(repo, size, cursor)
                    self.assertTrue(page['items'])
                    items.extend(page['items'])
                    cursor = page['next_cursor']
                    if cursor is None:
                        break
                self.assertIsNone(cursor)
                self.assertEqual(items, sorted(self.rows, key=lambda r: (r['timestamp'], r['id'])))
                self.assertEqual(repo.list_items(size), items[:size])

    def test_absent_boundary(self):
        repo = Repository(self.rows)
        cursor = repo.page(2)['next_cursor']
        repo.rows = [r for r in repo.rows if r['id'] != 'a']
        self.assertEqual([r['id'] for r in repo.page(100, cursor)['items']], ['b', 'z'])
        self.assertEqual(repo.page(cursor=encode_cursor(99, 'gone')),
                         {'items': [], 'next_cursor': None})
        self.assertEqual(Repository([]).page(), {'items': [], 'next_cursor': None})

    def test_snapshot_and_return_isolation(self):
        original = copy.deepcopy(self.rows)
        repo = Repository(self.rows)
        self.assertEqual(self.rows, original)
        self.rows[0]['payload']['values'].append(2)
        self.rows.clear()
        page = repo.page()
        self.assertEqual(page['items'][-1]['payload']['values'], [1])
        page['items'][-1]['payload']['values'].append(3)
        page['items'][0]['id'] = 'changed'
        self.assertEqual(repo.page()['items'], sorted(original, key=lambda r: (r['timestamp'], r['id'])))

    def test_limit_validation(self):
        for limit in (True, False, 0, -1, 101, 1.0, '2', None):
            for method in (Repository([]).page, Repository([]).list_items):
                with self.subTest(limit=limit), self.assertRaises(ValueError):
                    method(limit)
        for limit in (1, 100):
            self.assertEqual(Repository([]).page(limit)['items'], [])

    def test_cursor_wire_format(self):
        for key in ((1, 'a'), (-3, 'é雪😀'), (0, 'x/+= ')):
            expected = base64.urlsafe_b64encode(
                json.dumps(list(key), separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            ).decode('ascii').rstrip('=')
            self.assertEqual(encode_cursor(*key), expected)
            self.assertEqual(decode_cursor(expected), key)

    def test_invalid_cursors(self):
        tokens = [None, '', 1, b'abc', 'a', '***', 'ab+c', 'ab/c', 'WzEsImEiXQ==', ' abc']
        for data in (b'\xff', b'no json', b'{}', b'null', b'[]', b'[1]', b'[1,"a",2]',
                     b'[true,"a"]', b'[1.0,"a"]', b'["1","a"]', b'[1,""]', b'[1,2]'):
            tokens.append(base64.urlsafe_b64encode(data).decode('ascii').rstrip('='))
        for token in tokens:
            with self.subTest(token=token), self.assertRaises(ValueError):
                decode_cursor(token)

    def invoke(self, args, repo=None):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            result = main(args, repo=repo)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_cli_success(self):
        repo = Repository(self.rows)
        cursor = encode_cursor(1, 'a')
        result, out, err = self.invoke(['--limit', '1', '--cursor', cursor], repo)
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(out), repo.page(1, cursor))
        self.assertEqual(err, '')
        self.assertEqual(json.loads(self.invoke([])[1]), {'items': [], 'next_cursor': None})

    def test_cli_errors(self):
        for args in (['--limit', 'x'], ['--limit', '1.0'], ['--limit', '1_0'],
                     ['--limit', '0'], ['--limit', '101'], ['--limit'],
                     ['--cursor', 'bad!'], ['--cursor', ''], ['--cursor'],
                     ['--unknown'], ['--lim', '2'], ['positional']):
            with self.subTest(args=args):
                result, out, err = self.invoke(args)
                self.assertEqual(result, 2)
                self.assertEqual(out, '')
                self.assertTrue(err.strip())

    def test_module_exit_status(self):
        for args, code in (([], 0), (['--limit', '0'], 2)):
            result = subprocess.run([sys.executable, '-m', 'app.cli', *args],
                                    capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, code)
            if code:
                self.assertEqual(result.stdout, '')
                self.assertTrue(result.stderr)
            else:
                self.assertEqual(json.loads(result.stdout), {'items': [], 'next_cursor': None})


if __name__ == '__main__':
    unittest.main()
