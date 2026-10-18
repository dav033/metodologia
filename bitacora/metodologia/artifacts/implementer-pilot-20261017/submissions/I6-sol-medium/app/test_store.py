"""Behavioral and recovery checks for the queue."""

from concurrent.futures import ThreadPoolExecutor
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from app import store


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = os.path.join(self.directory.name, 'queue.db')
        store.init(self.path)

    def rows(self, table):
        connection = sqlite3.connect(self.path)
        try:
            return connection.execute('SELECT * FROM ' + table).fetchall()
        finally:
            connection.close()

    def test_leases_retry_and_fencing_persist(self):
        store.enqueue(self.path, 'a', 'first')
        store.enqueue(self.path, 'a', 'second')
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                store.claim(self.path, 0, ttl)
        self.assertEqual(store.inspect(self.path, 'a')['attempts'], 0)
        self.assertEqual(store.claim(self.path, 0, 10), ('a', 'first', 1))
        self.assertIsNone(store.claim(self.path, 9, 10))
        original = store.inspect(self.path, 'a')
        self.assertFalse(store.retry(self.path, 'a', 2, 9))
        self.assertFalse(store.complete(self.path, 'a', 1, 'late', 10))
        self.assertEqual(store.inspect(self.path, 'a'), original)
        store.init(self.path)
        self.assertEqual(store.claim(self.path, 10, 10), ('a', 'first', 2))
        self.assertFalse(store.complete(self.path, 'a', 1, 'old', 11))
        self.assertTrue(store.retry(self.path, 'a', 2, 11))
        self.assertEqual(store.inspect(self.path, 'a')['attempts'], 2)
        self.assertEqual(store.claim(self.path, 11, 10), ('a', 'first', 3))
        self.assertTrue(store.complete(self.path, 'a', 3, 'result', 12))
        store.init(self.path)
        job = store.inspect(self.path, 'a')
        self.assertEqual((job['state'], job['result'], job['lease_until']),
                         ('done', 'result', None))
        self.assertEqual(self.rows('outbox'), [('a', 'result', 0)])
        self.assertIsNone(store.inspect(self.path, 'missing'))

    def test_dependencies_and_order(self):
        store.enqueue(self.path, 'a', 'child', 'z')
        store.enqueue(self.path, 'b', 'missing', 'absent')
        store.enqueue(self.path, 'c', 'cycle', 'd')
        store.enqueue(self.path, 'd', 'cycle', 'c')
        store.enqueue(self.path, 'z', 'parent')
        self.assertEqual(store.claim(self.path, 0, 10)[0], 'z')
        self.assertIsNone(store.claim(self.path, 0, 10))
        self.assertTrue(store.complete(self.path, 'z', 1, 'done', 1))
        self.assertEqual(store.claim(self.path, 1, 10)[0], 'a')
        self.assertIsNone(store.claim(self.path, 1, 10))

    def test_concurrent_claims_and_consumers(self):
        for index in range(12):
            store.enqueue(self.path, str(index), 'work')
        with ThreadPoolExecutor(max_workers=8) as pool:
            claims = list(pool.map(lambda _: store.claim(self.path, 0, 10),
                                   range(24)))
            consumed = list(pool.map(
                lambda _: store.consume(self.path, 'event', 'body'), range(16)))
        claimed = [row for row in claims if row is not None]
        self.assertEqual(len(claimed), 12)
        self.assertEqual(len({row[0] for row in claimed}), 12)
        self.assertTrue(all(row[2] == 1 for row in claimed))
        self.assertEqual(sum(consumed), 1)
        self.assertFalse(store.consume(self.path, 'event', 'replacement'))
        self.assertEqual(self.rows('inbox'), [('event', 'body')])

    def test_hook_errors_roll_back_and_stale_calls_skip_hooks(self):
        store.enqueue(self.path, 'a', 'work')
        store.claim(self.path, 0, 10)
        original = store.inspect(self.path, 'a')
        for stage in ('after_result', 'before_commit'):
            calls = []

            def fault(current):
                calls.append(current)
                if current == stage:
                    raise RuntimeError(stage)

            with self.assertRaisesRegex(RuntimeError, stage):
                store.complete(self.path, 'a', 1, 'result', 1, fault)
            self.assertIn(stage, calls)
            self.assertEqual(store.inspect(self.path, 'a'), original)
            self.assertEqual(self.rows('outbox'), [])
        calls = []
        for id, token, now in [('a', 2, 1), ('a', 1, 10), ('missing', 1, 1)]:
            self.assertFalse(store.complete(
                self.path, id, token, 'result', now, calls.append))
        self.assertEqual(calls, [])

    def test_process_crash_rolls_back_at_both_hooks(self):
        store.enqueue(self.path, 'a', 'work')
        store.claim(self.path, 0, 10)
        original = store.inspect(self.path, 'a')
        script = (
            'import os,sys\n'
            'from app import store\n'
            'def fault(stage):\n'
            '    if stage == sys.argv[2]: os._exit(27)\n'
            'store.complete(sys.argv[1], "a", 1, "result", 1, fault)\n'
        )
        for stage in ('after_result', 'before_commit'):
            process = subprocess.run([sys.executable, '-c', script,
                                      self.path, stage], check=False)
            self.assertEqual(process.returncode, 27)
            store.init(self.path)
            self.assertEqual(store.inspect(self.path, 'a'), original)
            self.assertEqual(self.rows('outbox'), [])

    def test_publication_replays_failed_callback_with_inbox_deduplication(self):
        for id in ('b', 'a', 'c'):
            store.enqueue(self.path, id, 'work')
        for _ in range(3):
            id, _, token = store.claim(self.path, 0, 10)
            store.complete(self.path, id, token, id + ' result', 1)
        calls = []

        def failing_delivery(id, body):
            calls.append(id)
            store.consume(self.path, id, body)
            if id == 'b':
                raise RuntimeError('delivery failed after side effect')

        with self.assertRaises(RuntimeError):
            store.publish(self.path, failing_delivery)
        self.assertEqual(calls, ['a', 'b'])
        self.assertEqual(dict((row[0], row[2]) for row in self.rows('outbox')),
                         {'a': 1, 'b': 0, 'c': 0})
        first_deliveries = []

        def replay(id, body):
            first_deliveries.append(store.consume(self.path, id, body))

        self.assertEqual(store.publish(self.path, replay), 2)
        self.assertEqual(first_deliveries, [False, True])
        self.assertEqual(store.publish(self.path, replay), 0)
        self.assertEqual(len(self.rows('inbox')), 3)


if __name__ == '__main__':
    unittest.main()
