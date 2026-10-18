import contextlib
import io
import json
import unittest

from app.cli import main
from app.cursor import decode_cursor, encode_cursor
from app.repository import Repository
from app.service import list_items


def _rows(n):
    return [{'timestamp': i // 2, 'id': f'id{i:03d}', 'payload': {'n': i}} for i in range(n)]


def _run_cli(argv, repo=None):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        status = main(argv, repo=repo)
    return status, out.getvalue(), err.getvalue()


class CursorCodecTests(unittest.TestCase):
    def test_round_trip_unicode(self):
        token = encode_cursor(5, 'ключ-🔑')
        self.assertEqual(decode_cursor(token), (5, 'ключ-🔑'))
        self.assertNotIn('=', token)

    def test_encoding_is_compact_utf8_json(self):
        import base64
        token = encode_cursor(1, 'é')
        padded = token + '=' * (-len(token) % 4)
        self.assertEqual(base64.urlsafe_b64decode(padded), '[1,"é"]'.encode('utf-8'))

    def test_rejects_invalid_cursors(self):
        bad = [
            '',
            'a',                 # invalid base64 length
            'W10=',              # padding not allowed
            'W1 0',              # outside alphabet
            'W10+',              # standard base64 char not allowed
            'not base64!',
        ]
        for token in bad:
            with self.subTest(token=token), self.assertRaises(ValueError):
                decode_cursor(token)

    def test_rejects_malformed_payloads(self):
        import base64

        def tok(text):
            return base64.urlsafe_b64encode(text.encode('utf-8')).decode('ascii').rstrip('=')

        for text in ['{', '[1]', '[1,"a",2]', '[true,"a"]', '[1.0,"a"]',
                     '[1,""]', '[1,2]', '"x"', '[1,null]', '\xff']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                decode_cursor(tok(text))

    def test_rejects_non_string_cursor(self):
        for value in [None, 1, b'W10', ['W10']]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                decode_cursor(value)

    def test_encode_rejects_invalid_keys(self):
        with self.assertRaises(ValueError):
            encode_cursor(True, 'a')
        with self.assertRaises(ValueError):
            encode_cursor(1, '')


class RepositoryPageTests(unittest.TestCase):
    def test_full_traversal_has_no_duplicates_or_gaps(self):
        rows = _rows(25)
        repo = Repository(rows)
        seen, cursor, pages = [], None, 0
        while True:
            page = repo.page(limit=7, cursor=cursor)
            pages += 1
            seen.extend(row['id'] for row in page['items'])
            cursor = page['next_cursor']
            if cursor is None:
                break
        self.assertEqual(seen, [r['id'] for r in sorted(rows, key=lambda r: (r['timestamp'], r['id']))])
        self.assertEqual(pages, 4)

    def test_next_cursor_only_when_more_rows(self):
        repo = Repository(_rows(3))
        page = repo.page(limit=3)
        self.assertEqual(len(page['items']), 3)
        self.assertIsNone(page['next_cursor'])
        page = repo.page(limit=2)
        self.assertIsNotNone(page['next_cursor'])

    def test_cursor_is_strictly_after_deleted_row(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}, {'timestamp': 3, 'id': 'c'}])
        token = encode_cursor(2, 'b')  # tuple not present in the repository
        self.assertEqual([r['id'] for r in repo.page(cursor=token)['items']], ['c'])

    def test_cursor_past_end_gives_empty_page(self):
        repo = Repository(_rows(2))
        page = repo.page(cursor=encode_cursor(10**9, 'z'))
        self.assertEqual(page, {'items': [], 'next_cursor': None})

    def test_ordering_is_by_timestamp_then_id(self):
        repo = Repository([{'timestamp': 2, 'id': 'a'}, {'timestamp': 1, 'id': 'z'},
                           {'timestamp': 1, 'id': 'b'}])
        self.assertEqual([r['id'] for r in repo.page()['items']], ['b', 'z', 'a'])

    def test_limit_validation(self):
        repo = Repository(_rows(1))
        for limit in [0, 101, -1, True, False, 1.0, '5', None]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                repo.page(limit=limit)
        self.assertEqual(len(repo.page(limit=1)['items']), 1)
        self.assertEqual(len(repo.page(limit=100)['items']), 1)

    def test_snapshot_isolated_from_input_and_outputs(self):
        source = [{'timestamp': 1, 'id': 'a', 'payload': {'tags': ['x']}}]
        repo = Repository(source)
        source[0]['payload']['tags'].append('mutated')
        source.append({'timestamp': 0, 'id': 'late'})
        first = repo.page()
        first['items'][0]['payload']['tags'].append('out')
        first['items'][0]['id'] = 'changed'
        self.assertEqual(repo.page()['items'], [{'timestamp': 1, 'id': 'a', 'payload': {'tags': ['x']}}])

    def test_legacy_list_items(self):
        rows = [{'timestamp': 2, 'id': 'b'}, {'timestamp': 1, 'id': 'a'}]
        repo = Repository(rows)
        self.assertEqual(repo.list_items(1), [rows[1]])
        self.assertEqual(repo.list_items(), [rows[1], rows[0]])
        with self.assertRaises(ValueError):
            repo.list_items(0)


class ServiceTests(unittest.TestCase):
    def test_service_delegates_to_page(self):
        repo = Repository(_rows(5))
        page = list_items(repo, limit=2)
        self.assertEqual(page, repo.page(limit=2))
        self.assertEqual(list_items(repo, limit=2, cursor=page['next_cursor']),
                         repo.page(limit=2, cursor=page['next_cursor']))


class CliTests(unittest.TestCase):
    def test_success_prints_one_json_page(self):
        status, out, err = _run_cli(['--limit', '1'], repo=Repository(_rows(2)))
        self.assertEqual(status, 0)
        self.assertEqual(err, '')
        page = json.loads(out)
        self.assertEqual(len(page['items']), 1)
        self.assertIsNotNone(page['next_cursor'])

    def test_empty_default_repo(self):
        status, out, _ = _run_cli([])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out), {'items': [], 'next_cursor': None})

    def test_cursor_round_trip_through_cli(self):
        repo = Repository(_rows(3))
        _, out, _ = _run_cli(['--limit=2'], repo=repo)
        cursor = json.loads(out)['next_cursor']
        status, out, _ = _run_cli(['--limit', '2', '--cursor', cursor], repo=repo)
        self.assertEqual(status, 0)
        self.assertEqual([r['id'] for r in json.loads(out)['items']], ['id002'])

    def test_invalid_inputs_return_2_without_stdout(self):
        cases = [
            ['--limit', 'abc'],
            ['--limit', '1.5'],
            ['--limit', '0'],
            ['--limit', '101'],
            ['--limit', '-3'],
            ['--cursor', 'not!valid'],
            ['--cursor', ''],
            ['--bogus'],
            ['positional'],
            ['--limit'],
        ]
        for argv in cases:
            with self.subTest(argv=argv):
                status, out, err = _run_cli(argv, repo=Repository(_rows(3)))
                self.assertEqual(status, 2)
                self.assertEqual(out, '')
                self.assertTrue(err.strip())

    def test_help_returns_zero_without_raising(self):
        status, _, _ = _run_cli(['--help'])
        self.assertEqual(status, 0)


if __name__ == '__main__':
    unittest.main()
