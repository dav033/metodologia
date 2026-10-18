import os
import sqlite3
import tempfile
from contextlib import closing
import threading
import unittest

from app.store import claim, complete, enqueue, init, inspect


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, 'db')
        init(self.path)


class SchemaTests(StoreTestCase):
    def test_init_is_idempotent_and_keeps_data(self):
        enqueue(self.path, 'a', 'work')
        init(self.path)
        self.assertEqual(inspect(self.path, 'a')['payload'], 'work')

    def test_schema_columns_match_contract(self):
        with closing(sqlite3.connect(self.path)) as conn:
            columns = [
                (row[1], row[2], row[3], row[5])
                for row in conn.execute('PRAGMA table_info(jobs)')
            ]
        self.assertEqual(columns, [
            ('id', 'TEXT', 0, 1),
            ('payload', 'TEXT', 1, 0),
            ('state', 'TEXT', 1, 0),
            ('token', 'INTEGER', 1, 0),
            ('lease_until', 'INTEGER', 0, 0),
            ('attempts', 'INTEGER', 1, 0),
            ('depends_on', 'TEXT', 0, 0),
            ('result', 'TEXT', 0, 0),
        ])

    def test_inspect_returns_all_columns_and_none_when_missing(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(inspect(self.path, 'a'), {
            'id': 'a', 'payload': 'work', 'state': 'pending', 'token': 0,
            'lease_until': None, 'attempts': 0, 'depends_on': None, 'result': None,
        })
        self.assertIsNone(inspect(self.path, 'missing'))


class EnqueueTests(StoreTestCase):
    def test_duplicate_id_keeps_first_payload(self):
        enqueue(self.path, 'a', 'first')
        enqueue(self.path, 'a', 'second')
        self.assertEqual(inspect(self.path, 'a')['payload'], 'first')


class ClaimTests(StoreTestCase):
    def test_claims_lexicographically_smallest_pending_job(self):
        enqueue(self.path, 'b', 'pb')
        enqueue(self.path, 'a', 'pa')
        self.assertEqual(claim(self.path, 5, 10), ('a', 'pa', 1))
        self.assertEqual(claim(self.path, 5, 10), ('b', 'pb', 1))
        self.assertIsNone(claim(self.path, 5, 10))

    def test_claim_sets_running_lease_and_attempts(self):
        enqueue(self.path, 'a', 'work')
        claim(self.path, 100, 30)
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['token'], job['lease_until'], job['attempts']),
                         ('running', 1, 130, 1))

    def test_active_lease_is_not_reclaimed(self):
        enqueue(self.path, 'a', 'work')
        claim(self.path, 0, 10)
        self.assertIsNone(claim(self.path, 9, 10))

    def test_expired_lease_is_reclaimed_with_new_token(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'work', 1))
        self.assertEqual(claim(self.path, 10, 10), ('a', 'work', 2))
        job = inspect(self.path, 'a')
        self.assertEqual((job['token'], job['lease_until'], job['attempts']), (2, 20, 2))

    def test_non_positive_ttl_raises_without_mutation(self):
        enqueue(self.path, 'a', 'work')
        for ttl in (0, -1):
            with self.subTest(ttl=ttl):
                with self.assertRaises(ValueError):
                    claim(self.path, 0, ttl)
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['token'], job['attempts']), ('pending', 0, 0))

    def test_rejects_wrong_types(self):
        with self.assertRaises(TypeError):
            claim(self.path, 1.5, 10)
        with self.assertRaises(TypeError):
            claim(self.path, 0, True)
        with self.assertRaises(TypeError):
            claim(123, 0, 10)


class CompleteTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        enqueue(self.path, 'a', 'work')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'work', 1))

    def test_completes_with_current_token_and_live_lease(self):
        self.assertTrue(complete(self.path, 'a', 1, 'out', 5))
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['result'], job['lease_until']), ('done', 'out', None))
        self.assertEqual(job['token'], 1)

    def test_lease_expiring_exactly_now_is_rejected(self):
        before = inspect(self.path, 'a')
        self.assertFalse(complete(self.path, 'a', 1, 'out', 10))
        self.assertEqual(inspect(self.path, 'a'), before)

    def test_wrong_token_is_rejected_without_mutation(self):
        before = inspect(self.path, 'a')
        self.assertFalse(complete(self.path, 'a', 2, 'out', 5))
        self.assertEqual(inspect(self.path, 'a'), before)

    def test_missing_or_pending_job_is_rejected(self):
        enqueue(self.path, 'b', 'pending-work')
        self.assertFalse(complete(self.path, 'missing', 1, 'out', 5))
        self.assertFalse(complete(self.path, 'b', 0, 'out', 5))
        self.assertEqual(inspect(self.path, 'b')['state'], 'pending')

    def test_done_job_cannot_be_completed_again(self):
        self.assertTrue(complete(self.path, 'a', 1, 'first', 5))
        self.assertFalse(complete(self.path, 'a', 1, 'second', 6))
        self.assertEqual(inspect(self.path, 'a')['result'], 'first')

    def test_fault_hook_failure_rolls_back_completion(self):
        def crash():
            raise RuntimeError('injected')

        before = inspect(self.path, 'a')
        with self.assertRaises(RuntimeError):
            complete(self.path, 'a', 1, 'out', 5, fault=crash)
        self.assertEqual(inspect(self.path, 'a'), before)

    def test_fault_hook_that_returns_lets_completion_commit(self):
        calls = []
        self.assertTrue(complete(self.path, 'a', 1, 'out', 5, fault=lambda: calls.append(1)))
        self.assertEqual(calls, [1])
        self.assertEqual(inspect(self.path, 'a')['state'], 'done')

    def test_non_callable_fault_is_rejected(self):
        with self.assertRaises(TypeError):
            complete(self.path, 'a', 1, 'out', 5, fault='crash')
        self.assertEqual(inspect(self.path, 'a')['state'], 'running')


class FencingTests(StoreTestCase):
    def test_stale_claimant_is_fenced_after_reopen(self):
        enqueue(self.path, 'a', 'work')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'work', 1))
        self.assertEqual(claim(self.path, 10, 10), ('a', 'work', 2))

        # Fresh connections (each call opens its own) see the persisted token.
        self.assertFalse(complete(self.path, 'a', 1, 'stale', 11))
        self.assertTrue(complete(self.path, 'a', 2, 'fresh', 11))
        self.assertEqual(inspect(self.path, 'a')['result'], 'fresh')


class ConcurrencyTests(StoreTestCase):
    def test_racing_claimants_each_get_each_job_once(self):
        job_count = 60
        for i in range(job_count):
            enqueue(self.path, f'job-{i:03d}', f'payload-{i}')

        claimed = []
        errors = []
        lock = threading.Lock()

        def worker():
            try:
                while True:
                    result = claim(self.path, 0, 100)
                    if result is None:
                        return
                    with lock:
                        claimed.append(result)
            except Exception as exc:  # surfaced by the assertion below
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        self.assertEqual(len(claimed), job_count)
        self.assertEqual(len({job_id for job_id, _, _ in claimed}), job_count)
        self.assertTrue(all(token == 1 for _, _, token in claimed))


if __name__ == '__main__':
    unittest.main()
