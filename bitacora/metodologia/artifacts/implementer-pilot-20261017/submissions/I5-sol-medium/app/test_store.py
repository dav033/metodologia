import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from app.store import claim, complete, enqueue, init, inspect


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, 'jobs.db')
        init(self.path)

    def test_idempotence_and_duplicate_payload(self):
        enqueue(self.path, 'a', 'original')
        init(self.path)
        enqueue(self.path, 'a', 'replacement')
        self.assertEqual(inspect(self.path, 'a'), {
            'id': 'a', 'payload': 'original', 'state': 'pending',
            'token': 0, 'lease_until': None, 'attempts': 0,
            'depends_on': None, 'result': None,
        })
        self.assertIsNone(inspect(self.path, 'missing'))

    def test_order_expiry_and_fencing(self):
        enqueue(self.path, 'z', 'last')
        enqueue(self.path, 'a', 'first')
        self.assertEqual(claim(self.path, 10, 5), ('a', 'first', 1))
        self.assertEqual(claim(self.path, 10, 5), ('z', 'last', 1))
        self.assertIsNone(claim(self.path, 14, 5))
        before = inspect(self.path, 'a')
        self.assertFalse(complete(self.path, 'a', 1, 'late', 15))
        self.assertEqual(inspect(self.path, 'a'), before)
        self.assertEqual(claim(self.path, 15, 10), ('a', 'first', 2))
        before = inspect(self.path, 'a')
        self.assertFalse(complete(self.path, 'a', 1, 'stale', 16))
        self.assertEqual(inspect(self.path, 'a'), before)
        self.assertTrue(complete(self.path, 'a', 2, 'finished', 16))
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['result'], job['lease_until'],
                          job['attempts'], job['token']),
                         ('done', 'finished', None, 2, 2))
        self.assertFalse(complete(self.path, 'a', 2, 'again', 16))
        self.assertEqual(inspect(self.path, 'a'), job)
        self.assertFalse(complete(self.path, 'missing', 1, 'none', 16))

    def test_invalid_ttl_does_not_create_database(self):
        path = os.path.join(self.directory.name, 'absent.db')
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                claim(path, 0, ttl)
        self.assertFalse(os.path.exists(path))

    def test_bound_values_and_pending_completion(self):
        id = "a'; DROP TABLE jobs; --"
        enqueue(self.path, id, "payload's text")
        before = inspect(self.path, id)
        self.assertFalse(complete(self.path, id, 0, 'premature', 0))
        self.assertEqual(inspect(self.path, id), before)
        self.assertEqual(claim(self.path, 0, 10), (id, "payload's text", 1))
        self.assertTrue(complete(self.path, id, 1, "result's text", 1))
        self.assertEqual(inspect(self.path, id)['result'], "result's text")

    def test_concurrent_claims_have_one_winner(self):
        enqueue(self.path, 'a', 'work')
        for now, token in ((0, 1), (10, 2)):
            barrier = Barrier(8)

            def attempt(_):
                barrier.wait()
                return claim(self.path, now, 10)

            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(attempt, range(8)))
            self.assertEqual(results.count(('a', 'work', token)), 1)
            self.assertEqual(results.count(None), 7)
        self.assertEqual(inspect(self.path, 'a')['attempts'], 2)

    def test_sql_failure_rolls_back_claim(self):
        enqueue(self.path, 'a', 'work')
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "CREATE TRIGGER reject_claim BEFORE UPDATE ON jobs "
                "BEGIN SELECT RAISE(ABORT, 'rejected'); END"
            )
            connection.commit()
        finally:
            connection.close()
        before = inspect(self.path, 'a')
        with self.assertRaises(sqlite3.IntegrityError):
            claim(self.path, 0, 10)
        self.assertEqual(inspect(self.path, 'a'), before)


if __name__ == '__main__':
    unittest.main()
