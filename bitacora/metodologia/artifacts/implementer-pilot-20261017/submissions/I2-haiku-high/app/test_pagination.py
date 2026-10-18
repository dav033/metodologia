import base64
import contextlib
import io
import json
import unittest

from app import cli
from app.repository import Repository, decode_cursor, encode_cursor
from app.service import list_items


def make_rows(count):
    return [{'timestamp': i // 2, 'id': f'id-{i:03d}', 'payload': {'n': i}} for i in range(count)]


def walk(repo, limit):
    seen, cursor = [], None
    while True:
        page = repo.page(limit=limit, cursor=cursor)
        seen.extend(row['id'] for row in page['items'])
        cursor = page['next_cursor']
        if cursor is None:
            return seen


class EncodingTests(unittest.TestCase):
    def test_round_trip_unicode(self):
        token = encode_cursor(5, 'café-😀')
        self.assertEqual(decode_cursor(token), (5, 'café-😀'))

    def test_token_is_unpadded_urlsafe_compact_json(self):
        token = encode_cursor(1, 'a?>')
        self.assertNotIn('=', token)
        self.assertRegex(token, r'^[A-Za-z0-9_-]+$')

    def test_invalid_cursors_rejected(self):
        bad = [
            '', None, 5, b'abc', 'a=', 'a+b/', 'not base64!', 'A',
            encode_cursor(1, 'a') + '=', 'W10', 'WzEsIiJd', 'WzEsMl0',
            'WyJhIiwxXQ', 'eyJhIjoxfQ', 'WzEuMCwiYSJd', 'WyJhIiwiYiJd',
            'WzEsImEiLDNd',
        ]
        for cursor in bad:
            with self.subTest(cursor=cursor):
                with self.assertRaises(ValueError):
                    decode_cursor(cursor)

    def test_bool_timestamp_rejected(self):
        payload = base64.urlsafe_b64encode(b'[true,"a"]').rstrip(b'=').decode()
        with self.assertRaises(ValueError):
            decode_cursor(payload)
        self.assertEqual(decode_cursor(encode_cursor(1, 'a')), (1, 'a'))

    def test_encode_rejects_invalid_parts(self):
        for args in [(True, 'a'), (1, ''), (1.0, 'a'), (1, None)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):
                    encode_cursor(*args)


class PageTests(unittest.TestCase):
    def test_limit_validation(self):
        repo = Repository(make_rows(3))
        for limit in [0, 101, -1, True, False, 1.0, '5', None]:
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    repo.page(limit=limit)
        self.assertEqual(len(repo.page(limit=1)['items']), 1)
        self.assertEqual(len(repo.page(limit=100)['items']), 3)

    def test_ordering_by_timestamp_then_id(self):
        rows = [{'timestamp': 2, 'id': 'a'}, {'timestamp': 1, 'id': 'z'}, {'timestamp': 1, 'id': 'b'}]
        ids = [row['id'] for row in Repository(rows).page(limit=10)['items']]
        self.assertEqual(ids, ['b', 'z', 'a'])

    def test_full_traversal_no_duplicates_or_gaps(self):
        rows = make_rows(45)
        repo = Repository(rows)
        for limit in [1, 2, 7, 20, 45, 100]:
            with self.subTest(limit=limit):
                self.assertEqual(walk(repo, limit), [r['id'] for r in rows])

    def test_no_next_cursor_when_exhausted(self):
        repo = Repository(make_rows(4))
        page = repo.page(limit=4)
        self.assertEqual(len(page['items']), 4)
        self.assertIsNone(page['next_cursor'])

    def test_cursor_after_nonexistent_tuple(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}, {'timestamp': 3, 'id': 'c'}])
        page = repo.page(limit=10, cursor=encode_cursor(2, 'zzz'))
        self.assertEqual([r['id'] for r in page['items']], ['c'])

    def test_cursor_is_strictly_after_existing_row(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}, {'timestamp': 1, 'id': 'b'}])
        page = repo.page(limit=10, cursor=encode_cursor(1, 'a'))
        self.assertEqual([r['id'] for r in page['items']], ['b'])

    def test_cursor_past_end_gives_empty_page(self):
        repo = Repository(make_rows(2))
        self.assertEqual(repo.page(limit=5, cursor=encode_cursor(10**9, 'x')),
                         {'items': [], 'next_cursor': None})

    def test_snapshot_isolated_from_input_and_outputs(self):
        rows = [{'timestamp': 1, 'id': 'a', 'payload': {'tags': ['x']}}]
        repo = Repository(rows)
        rows[0]['payload']['tags'].append('mutated')
        rows.append({'timestamp': 0, 'id': 'late'})
        first = repo.page(limit=5)
        first['items'][0]['payload']['tags'].append('out')
        first['items'][0]['id'] = 'changed'
        again = repo.page(limit=5)
        self.assertEqual(again['items'], [{'timestamp': 1, 'id': 'a', 'payload': {'tags': ['x']}}])

    def test_construction_does_not_mutate_input(self):
        rows = [{'timestamp': 2, 'id': 'b'}, {'timestamp': 1, 'id': 'a'}]
        before = json.dumps(rows)
        Repository(rows).page(limit=1)
        self.assertEqual(json.dumps(rows), before)

    def test_legacy_list_items_matches_first_page(self):
        repo = Repository(make_rows(30))
        self.assertEqual(repo.list_items(7), repo.page(limit=7)['items'])
        self.assertEqual(len(repo.list_items()), 20)
        with self.assertRaises(ValueError):
            repo.list_items(0)


class ServiceTests(unittest.TestCase):
    def test_service_passes_cursor_through(self):
        repo = Repository(make_rows(5))
        first = list_items(repo, limit=2)
        second = list_items(repo, limit=2, cursor=first['next_cursor'])
        self.assertEqual([r['id'] for r in second['items']], ['id-002', 'id-003'])


class CliTests(unittest.TestCase):
    def run_cli(self, argv, repo=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = cli.main(argv, repo=repo)
        return status, out.getvalue(), err.getvalue()

    def test_default_page_printed(self):
        status, out, err = self.run_cli([], repo=Repository(make_rows(3)))
        self.assertEqual(status, 0)
        self.assertEqual(err, '')
        self.assertEqual(json.loads(out)['items'][0]['id'], 'id-000')

    def test_default_repo_is_empty(self):
        status, out, _ = self.run_cli([])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out), {'items': [], 'next_cursor': None})

    def test_cursor_round_trip_through_cli(self):
        repo = Repository(make_rows(5))
        _, out, _ = self.run_cli(['--limit', '2'], repo=repo)
        token = json.loads(out)['next_cursor']
        status, out, _ = self.run_cli(['--limit=2', '--cursor', token], repo=repo)
        self.assertEqual(status, 0)
        self.assertEqual([r['id'] for r in json.loads(out)['items']], ['id-002', 'id-003'])

    def test_invalid_inputs_return_2_silently_on_stdout(self):
        bad_argvs = [
            ['--limit', 'abc'], ['--limit', '1.5'], ['--limit', ''], ['--limit', '1_0'],
            ['--limit', '0'], ['--limit', '101'], ['--limit', '-3'],
            ['--cursor', 'bad!'], ['--cursor', ''], ['--cursor', encode_cursor(1, 'a') + '='],
            ['--bogus'], ['positional'], ['--limit'],
        ]
        for argv in bad_argvs:
            with self.subTest(argv=argv):
                status, out, err = self.run_cli(argv, repo=Repository(make_rows(3)))
                self.assertEqual(status, 2)
                self.assertEqual(out, '')
                self.assertTrue(err.strip())

    def test_help_returns_zero_without_system_exit(self):
        status, _, _ = self.run_cli(['--help'])
        self.assertEqual(status, 0)


if __name__ == '__main__':
    unittest.main()
