import os
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from app.store import claim, complete, enqueue, init, inspect


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, 'db')
        init(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_is_idempotent_and_keeps_data(self):
        enqueue(self.path, 'a', 'work')
        init(self.path)
        self.assertEqual(inspect(self.path, 'a')['payload'], 'work')

    def test_schema_columns_match_contract(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(
            set(inspect(self.path, 'a')),
            {'id', 'payload', 'state', 'token', 'lease_until', 'attempts', 'depends_on', 'result'},
        )

    def test_enqueue_duplicate_keeps_first_payload(self):
        enqueue(self.path, 'a', 'first')
        enqueue(self.path, 'a', 'second')
        self.assertEqual(inspect(self.path, 'a')['payload'], 'first')

    def test_claim_empty_queue_returns_none(self):
        self.assertIsNone(claim(self.path, 0, 10))

    def test_claim_selects_lexicographically_smallest_pending_id(self):
        enqueue(self.path, 'b', 'B')
        enqueue(self.path, 'a', 'A')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'A', 1))
        self.assertEqual(claim(self.path, 0, 10), ('b', 'B', 1))
        self.assertIsNone(claim(self.path, 0, 10))

    def test_claim_sets_running_lease_and_attempts(self):
        enqueue(self.path, 'a', 'work')
        claim(self.path, 5, 10)
        row = inspect(self.path, 'a')
        self.assertEqual((row['state'], row['lease_until'], row['attempts'], row['token']),
                         ('running', 15, 1, 1))

    def test_nonpositive_ttl_raises_before_mutation(self):
        enqueue(self.path, 'a', 'work')
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                claim(self.path, 0, ttl)
        row = inspect(self.path, 'a')
        self.assertEqual((row['state'], row['token'], row['attempts']), ('pending', 0, 0))

    def test_expired_lease_is_reclaimed_with_new_token(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'work', 1))
        self.assertIsNone(claim(self.path, 9, 10))
        self.assertEqual(claim(self.path, 10, 10), ('a', 'work', 2))
        self.assertEqual(inspect(self.path, 'a')['attempts'], 2)

    def test_stale_token_cannot_complete_after_reclaim(self):
        enqueue(self.path, 'a', 'work')
        claim(self.path, 0, 10)
        claim(self.path, 10, 10)
        self.assertFalse(complete(self.path, 'a', 1, 'old', 11))
        self.assertTrue(complete(self.path, 'a', 2, 'new', 11))
        self.assertEqual(inspect(self.path, 'a')['result'], 'new')

    def test_complete_succeeds_for_current_unexpired_lease(self):
        enqueue(self.path, 'a', 'work')
        _, _, token = claim(self.path, 0, 10)
        self.assertTrue(complete(self.path, 'a', token, 'out', 9))
        row = inspect(self.path, 'a')
        self.assertEqual((row['state'], row['result'], row['lease_until']), ('done', 'out', None))

    def test_complete_rejects_expired_lease_without_mutation(self):
        enqueue(self.path, 'a', 'work')
        _, _, token = claim(self.path, 0, 10)
        self.assertFalse(complete(self.path, 'a', token, 'out', 10))
        row = inspect(self.path, 'a')
        self.assertEqual((row['state'], row['result'], row['lease_until']), ('running', None, 10))

    def test_complete_missing_or_pending_job_returns_false(self):
        self.assertFalse(complete(self.path, 'missing', 1, 'x', 0))
        enqueue(self.path, 'a', 'work')
        self.assertFalse(complete(self.path, 'a', 1, 'x', 0))
        self.assertEqual(inspect(self.path, 'a')['state'], 'pending')

    def test_complete_fault_rolls_back(self):
        enqueue(self.path, 'a', 'work')
        _, _, token = claim(self.path, 0, 10)

        def boom():
            raise RuntimeError('injected')

        with self.assertRaises(RuntimeError):
            complete(self.path, 'a', token, 'out', 1, fault=boom)
        row = inspect(self.path, 'a')
        self.assertEqual((row['state'], row['result']), ('running', None))
        self.assertTrue(complete(self.path, 'a', token, 'out', 1))

    def test_token_fencing_survives_reopen(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(claim(self.path, 0, 1)[2], 1)
        self.assertEqual(claim(self.path, 1, 1)[2], 2)
        # A fresh connection (reopen) must still see the persisted token.
        self.assertEqual(inspect(self.path, 'a')['token'], 2)
        self.assertFalse(complete(self.path, 'a', 1, 'old', 1))

    def test_inspect_missing_returns_none(self):
        self.assertIsNone(inspect(self.path, 'nope'))

    def test_missing_database_raises_and_is_not_created(self):
        missing = os.path.join(self._tmp.name, 'absent')
        with self.assertRaises(sqlite3.OperationalError):
            claim(missing, 0, 10)
        self.assertFalse(os.path.exists(missing))

    def test_type_errors_are_explicit(self):
        with self.assertRaises(TypeError):
            enqueue(self.path, 1, 'work')
        with self.assertRaises(TypeError):
            claim(self.path, 0.5, 10)
        with self.assertRaises(TypeError):
            complete(self.path, 'a', 1, 'x', 0, fault='not callable')

    def test_concurrent_claimants_never_share_a_job(self):
        jobs = 60
        for i in range(jobs):
            enqueue(self.path, f'job{i:03d}', 'work')

        def drain(_):
            got = []
            while True:
                item = claim(self.path, 0, 1000)
                if item is None:
                    return got
                got.append(item)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = [item for part in pool.map(drain, range(8)) for item in part]

        ids = [item[0] for item in results]
        self.assertEqual(len(ids), jobs)
        self.assertEqual(len(set(ids)), jobs)
        self.assertTrue(all(item[2] == 1 for item in results))


if __name__ == '__main__':
    unittest.main()
