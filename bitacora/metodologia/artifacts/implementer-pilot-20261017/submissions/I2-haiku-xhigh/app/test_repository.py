import copy
import unittest

from app.cursor import encode_cursor
from app.repository import Repository
from app.service import list_items


def _ids(page):
    return [row['id'] for row in page['items']]


class PageTest(unittest.TestCase):
    def test_orders_by_timestamp_then_id(self):
        rows = [
            {'timestamp': 2, 'id': 'a'},
            {'timestamp': 1, 'id': 'z'},
            {'timestamp': 1, 'id': 'b'},
        ]
        self.assertEqual(_ids(Repository(rows).page()), ['b', 'z', 'a'])

    def test_empty_repository(self):
        self.assertEqual(Repository([]).page(), {'items': [], 'next_cursor': None})

    def test_next_cursor_only_when_more_rows_exist(self):
        rows = [{'timestamp': i, 'id': str(i)} for i in range(3)]
        repo = Repository(rows)
        first = repo.page(limit=2)
        self.assertEqual(_ids(first), ['0', '1'])
        self.assertEqual(first['next_cursor'], encode_cursor(1, '1'))
        last = repo.page(limit=2, cursor=first['next_cursor'])
        self.assertEqual(_ids(last), ['2'])
        self.assertIsNone(last['next_cursor'])

    def test_exact_fit_has_no_next_cursor(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}, {'timestamp': 2, 'id': 'b'}])
        page = repo.page(limit=2)
        self.assertEqual(_ids(page), ['a', 'b'])
        self.assertIsNone(page['next_cursor'])

    def test_static_traversal_visits_every_row_once_for_every_page_size(self):
        rows = [{'timestamp': i // 3, 'id': f'id-{i:02d}', 'payload': {'n': i}} for i in range(25)[::-1]]
        expected = [row['id'] for row in sorted(rows, key=lambda r: (r['timestamp'], r['id']))]
        repo = Repository(rows)
        for limit in range(1, 101):
            with self.subTest(limit=limit):
                seen, cursor = [], None
                while True:
                    page = repo.page(limit=limit, cursor=cursor)
                    seen.extend(_ids(page))
                    cursor = page['next_cursor']
                    if cursor is None:
                        break
                self.assertEqual(seen, expected)

    def test_cursor_is_strictly_after_even_when_its_row_was_deleted(self):
        rows = [{'timestamp': 1, 'id': 'a'}, {'timestamp': 2, 'id': 'b'}, {'timestamp': 3, 'id': 'c'}]
        cursor = Repository(rows).page(limit=2)['next_cursor']
        remaining = Repository([rows[0], rows[2]])
        self.assertEqual(_ids(remaining.page(cursor=cursor)), ['c'])

    def test_cursor_between_existing_rows_and_past_the_end(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}, {'timestamp': 5, 'id': 'b'}])
        self.assertEqual(_ids(repo.page(cursor=encode_cursor(3, 'x'))), ['b'])
        self.assertEqual(repo.page(cursor=encode_cursor(9, 'x')), {'items': [], 'next_cursor': None})
        self.assertEqual(_ids(repo.page(cursor=encode_cursor(1, 'a'))), ['b'])

    def test_unicode_ids_round_trip_through_pages(self):
        rows = [{'timestamp': 1, 'id': 'ü'}, {'timestamp': 1, 'id': '名前'}, {'timestamp': 1, 'id': '😀'}]
        repo = Repository(rows)
        first = repo.page(limit=1)
        second = repo.page(limit=1, cursor=first['next_cursor'])
        self.assertEqual(_ids(first) + _ids(second), ['ü', '名前'])


class LimitValidationTest(unittest.TestCase):
    def test_accepts_bounds(self):
        repo = Repository([{'timestamp': 1, 'id': 'a'}])
        self.assertEqual(len(repo.page(limit=1)['items']), 1)
        self.assertEqual(len(repo.page(limit=100)['items']), 1)

    def test_rejects_invalid_limits(self):
        repo = Repository([])
        for limit in [0, -1, 101, True, False, 1.0, '5', None]:
            with self.subTest(limit=limit):
                with self.assertRaises(ValueError):
                    repo.page(limit=limit)
                with self.assertRaises(ValueError):
                    repo.list_items(limit=limit)

    def test_rejects_invalid_cursor(self):
        with self.assertRaises(ValueError):
            Repository([]).page(cursor='')


class SnapshotTest(unittest.TestCase):
    def test_construction_does_not_mutate_or_alias_supplied_rows(self):
        rows = [{'timestamp': 2, 'id': 'b', 'payload': {'tags': ['x']}}, {'timestamp': 1, 'id': 'a', 'payload': {}}]
        original = copy.deepcopy(rows)
        repo = Repository(rows)
        rows[0]['payload']['tags'].append('mutated')
        rows.append({'timestamp': 0, 'id': 'late'})
        self.assertEqual(_ids(repo.page()), ['a', 'b'])
        self.assertEqual(repo.page()['items'][1]['payload'], {'tags': ['x']})
        self.assertEqual(original[1], {'timestamp': 1, 'id': 'a', 'payload': {}})

    def test_reads_do_not_mutate_stored_rows_or_leak_references(self):
        repo = Repository([{'timestamp': 1, 'id': 'a', 'payload': {'n': [1]}}])
        first = repo.page()
        first['items'][0]['payload']['n'].append(2)
        first['items'][0]['id'] = 'changed'
        first['items'].append({'timestamp': 9, 'id': 'extra'})
        self.assertEqual(repo.page(), {'items': [{'timestamp': 1, 'id': 'a', 'payload': {'n': [1]}}], 'next_cursor': None})
        repo.list_items()[0]['payload'] = None
        self.assertEqual(repo.page()['items'][0]['payload'], {'n': [1]})


class LegacyAndServiceTest(unittest.TestCase):
    def test_list_items_returns_first_page_only(self):
        rows = [{'timestamp': i, 'id': str(i)} for i in range(30)]
        self.assertEqual(Repository(rows).list_items(), Repository(rows).page()['items'])
        self.assertEqual(len(Repository(rows).list_items(5)), 5)

    def test_service_forwards_cursor(self):
        rows = [{'timestamp': i, 'id': str(i)} for i in range(5)]
        repo = Repository(rows)
        first = list_items(repo, limit=2)
        second = list_items(repo, limit=2, cursor=first['next_cursor'])
        self.assertEqual(_ids(second), ['2', '3'])

    def test_service_defaults(self):
        self.assertEqual(list_items(Repository([])), {'items': [], 'next_cursor': None})


if __name__ == '__main__':
    unittest.main()
