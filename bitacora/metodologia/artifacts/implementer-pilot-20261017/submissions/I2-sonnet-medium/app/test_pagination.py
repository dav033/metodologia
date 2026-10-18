import unittest
from app.repository import Repository, encode_cursor, decode_cursor
from app.cli import main


class Pagination(unittest.TestCase):
    def test_traverse(self):
        rows = [{'timestamp': i // 2, 'id': 'é%d' % i, 'p': {'x': [i]}} for i in range(7)]
        repo, seen, cur = Repository(rows), [], None
        while True:
            p = repo.page(3, cur)
            seen += [r['id'] for r in p['items']]
            cur = p['next_cursor']
            if cur is None:
                break
        self.assertEqual(seen, [r['id'] for r in rows])

    def test_cursor(self):
        self.assertEqual(decode_cursor(encode_cursor(5, 'ü')), (5, 'ü'))
        for bad in ['', 'a=', '!!', 'e30', None, 5, encode_cursor(1, 'a') + '=']:
            with self.assertRaises(ValueError):
                decode_cursor(bad)
        for lim in (0, 101, True, '1'):
            with self.assertRaises(ValueError):
                Repository([]).page(lim)

    def test_cli(self):
        self.assertEqual(main([]), 0)
        self.assertEqual(main(['--limit', 'x']), 2)
        self.assertEqual(main(['--cursor', '']), 2)
        self.assertEqual(main(['--bogus']), 2)


if __name__ == '__main__':
    unittest.main()
