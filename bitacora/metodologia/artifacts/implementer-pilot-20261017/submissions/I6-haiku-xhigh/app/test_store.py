"""Behavioral tests for app.store. Run: python -m unittest app.test_store -v"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from contextlib import closing

from app.store import claim, complete, consume, enqueue, init, inspect, publish, retry

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOB_COLUMNS = ['id', 'payload', 'state', 'token', 'lease_until', 'attempts', 'depends_on', 'result']
CRASH_SCRIPT = (
    'import os, sys\n'
    'from app.store import complete\n'
    'def crash_at(point):\n'
    '    if point == sys.argv[3]:\n'
    '        os._exit(1)\n'
    'complete(sys.argv[1], sys.argv[2], 1, "R", 5, fault=crash_at)\n'
)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, 'queue.db')
        init(self.path)

    def query(self, sql, params=()):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(sql, params).fetchall()

    def finish_jobs(self, job_ids):
        for job_id in job_ids:
            enqueue(self.path, job_id, 'P')
        for _ in job_ids:
            job_id, _, token = claim(self.path, 0, 100)
            self.assertTrue(complete(self.path, job_id, token, 'result-' + job_id, 5))


class SchemaTests(StoreTestCase):
    def test_init_is_idempotent_and_keeps_data(self):
        enqueue(self.path, 'a', 'work')
        init(self.path)
        init(self.path)
        self.assertEqual(inspect(self.path, 'a')['payload'], 'work')

    def test_tables_match_spec(self):
        def columns(table):
            return [row[1] for row in self.query(f'PRAGMA table_info({table})')]

        self.assertEqual(columns('jobs'), JOB_COLUMNS)
        self.assertEqual(columns('outbox'), ['id', 'body', 'delivered'])
        self.assertEqual(columns('inbox'), ['id', 'body'])

    def test_inspect_returns_all_columns_or_none(self):
        self.assertIsNone(inspect(self.path, 'missing'))
        enqueue(self.path, 'a', 'work', depends_on='p')
        self.assertEqual(set(inspect(self.path, 'a')), set(JOB_COLUMNS))

    def test_enqueue_duplicate_keeps_first_payload(self):
        enqueue(self.path, 'a', 'first')
        enqueue(self.path, 'a', 'second')
        self.assertEqual(inspect(self.path, 'a')['payload'], 'first')

    def test_invalid_argument_types_raise_type_error(self):
        with self.assertRaises(TypeError):
            enqueue(self.path, 1, 'A')
        with self.assertRaises(TypeError):
            claim(self.path, '0', 10)


class ClaimTests(StoreTestCase):
    def test_claim_picks_smallest_id_and_records_lease(self):
        enqueue(self.path, 'b', 'B')
        enqueue(self.path, 'a', 'A')
        self.assertEqual(claim(self.path, 5, 10), ('a', 'A', 1))
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['token'], job['lease_until'], job['attempts']), ('running', 1, 15, 1))

    def test_non_positive_ttl_is_rejected_without_mutation(self):
        enqueue(self.path, 'a', 'A')
        for ttl in (0, -1):
            with self.subTest(ttl=ttl), self.assertRaises(ValueError):
                claim(self.path, 0, ttl)
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['token'], job['attempts']), ('pending', 0, 0))

    def test_live_lease_blocks_and_expired_lease_is_reclaimed(self):
        enqueue(self.path, 'a', 'A')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'A', 1))
        self.assertIsNone(claim(self.path, 9, 10))
        self.assertEqual(claim(self.path, 10, 10), ('a', 'A', 2))
        self.assertEqual(inspect(self.path, 'a')['attempts'], 2)


class CompleteTests(StoreTestCase):
    def test_valid_completion_stores_result_and_one_event(self):
        enqueue(self.path, 'a', 'A')
        token = claim(self.path, 0, 10)[2]
        calls = []
        self.assertTrue(complete(self.path, 'a', token, 'R', 5, fault=calls.append))
        self.assertEqual(calls, ['after_result', 'before_commit'])
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['result'], job['lease_until']), ('done', 'R', None))
        rows = self.query('SELECT id, body, delivered FROM outbox')
        self.assertEqual([(row[0], row[2]) for row in rows], [('a', 0)])
        self.assertEqual(json.loads(rows[0][1]), {'job_id': 'a', 'result': 'R'})

    def test_stale_expired_and_missing_completions_do_nothing(self):
        enqueue(self.path, 'a', 'A')
        token = claim(self.path, 0, 10)[2]
        calls = []
        self.assertFalse(complete(self.path, 'a', token + 1, 'R', 5, fault=calls.append))
        self.assertFalse(complete(self.path, 'a', token, 'R', 10, fault=calls.append))
        self.assertFalse(complete(self.path, 'missing', token, 'R', 5, fault=calls.append))
        self.assertEqual(calls, [])
        self.assertEqual(self.query('SELECT COUNT(*) FROM outbox'), [(0,)])
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['result'], job['token']), ('running', None, 1))

    def test_hook_exception_rolls_back_result_and_event(self):
        for point in ('after_result', 'before_commit'):
            job_id = 'hook-' + point
            enqueue(self.path, job_id, 'A')
            token = claim(self.path, 0, 100)[2]

            def boom(name, point=point):
                if name == point:
                    raise RuntimeError(name)

            with self.subTest(point=point):
                with self.assertRaises(RuntimeError):
                    complete(self.path, job_id, token, 'R', 5, fault=boom)
                job = inspect(self.path, job_id)
                self.assertEqual((job['state'], job['result']), ('running', None))
                self.assertEqual(self.query('SELECT id FROM outbox WHERE id=?', (job_id,)), [])

    def test_process_crash_at_either_hook_leaves_no_result_or_event(self):
        for point in ('after_result', 'before_commit'):
            job_id = 'crash-' + point
            enqueue(self.path, job_id, 'A')
            self.assertEqual(claim(self.path, 0, 100), (job_id, 'A', 1))
            with self.subTest(point=point):
                proc = subprocess.run(
                    [sys.executable, '-c', CRASH_SCRIPT, self.path, job_id, point],
                    cwd=ROOT, capture_output=True, text=True,
                )
                self.assertEqual(proc.returncode, 1, proc.stderr)
                job = inspect(self.path, job_id)
                self.assertEqual((job['state'], job['result']), ('running', None))
                self.assertEqual(self.query('SELECT id FROM outbox WHERE id=?', (job_id,)), [])
                self.assertTrue(complete(self.path, job_id, 1, 'R', 5))


class DependencyTests(StoreTestCase):
    def test_child_waits_for_done_parent(self):
        enqueue(self.path, 'child', 'C', depends_on='parent')
        enqueue(self.path, 'parent', 'P')
        self.assertEqual(claim(self.path, 0, 10), ('parent', 'P', 1))
        self.assertIsNone(claim(self.path, 0, 10))
        self.assertTrue(complete(self.path, 'parent', 1, 'R', 5))
        self.assertEqual(claim(self.path, 6, 10), ('child', 'C', 1))

    def test_missing_parent_and_cycles_stay_blocked(self):
        enqueue(self.path, 'orphan', 'O', depends_on='ghost')
        enqueue(self.path, 'c1', 'X', depends_on='c2')
        enqueue(self.path, 'c2', 'Y', depends_on='c1')
        self.assertIsNone(claim(self.path, 0, 10))


class RetryTests(StoreTestCase):
    def test_retry_releases_lease_and_next_claim_advances_counters(self):
        enqueue(self.path, 'a', 'A')
        self.assertEqual(claim(self.path, 0, 10), ('a', 'A', 1))
        self.assertTrue(retry(self.path, 'a', 1, 1))
        job = inspect(self.path, 'a')
        self.assertEqual((job['state'], job['token'], job['attempts'], job['lease_until']), ('pending', 1, 1, None))
        self.assertFalse(retry(self.path, 'a', 1, 1))
        self.assertEqual(claim(self.path, 2, 10), ('a', 'A', 2))
        self.assertEqual(inspect(self.path, 'a')['attempts'], 2)

    def test_retry_rejects_stale_token_or_expired_lease(self):
        enqueue(self.path, 'a', 'A')
        claim(self.path, 0, 10)
        self.assertFalse(retry(self.path, 'a', 0, 1))
        self.assertFalse(retry(self.path, 'a', 1, 10))
        self.assertEqual(inspect(self.path, 'a')['state'], 'running')


class FencingTests(StoreTestCase):
    def test_old_token_is_fenced_after_reopen(self):
        enqueue(self.path, 'a', 'A')
        old = claim(self.path, 0, 10)[2]
        init(self.path)
        new = claim(self.path, 10, 10)[2]
        self.assertEqual((old, new), (1, 2))
        self.assertFalse(complete(self.path, 'a', old, 'stale', 11))
        self.assertTrue(complete(self.path, 'a', new, 'fresh', 11))
        self.assertEqual(inspect(self.path, 'a')['result'], 'fresh')


class ConcurrencyTests(StoreTestCase):
    def test_racing_claims_give_each_job_one_lease(self):
        job_ids = [f'job-{i:03d}' for i in range(40)]
        for job_id in job_ids:
            enqueue(self.path, job_id, 'P')
        claimed, errors = [], []
        lock = threading.Lock()

        def worker():
            try:
                while True:
                    job = claim(self.path, 0, 1000)
                    if job is None:
                        return
                    with lock:
                        claimed.append(job[0])
            except Exception as exc:
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(sorted(claimed), job_ids)
        self.assertEqual(self.query('SELECT COUNT(*) FROM jobs WHERE attempts=1'), [(40,)])


class OutboxTests(StoreTestCase):
    def test_publish_delivers_by_id_once(self):
        self.finish_jobs(['c', 'a', 'b'])
        delivered = []
        self.assertEqual(publish(self.path, lambda event_id, body: delivered.append(event_id)), 3)
        self.assertEqual(delivered, ['a', 'b', 'c'])
        self.assertEqual(publish(self.path, lambda event_id, body: delivered.append(event_id)), 0)
        self.assertEqual(delivered, ['a', 'b', 'c'])

    def test_callback_error_stops_publish_and_replay_resumes(self):
        self.finish_jobs(['a', 'b', 'c'])
        state = {'failed': False}

        def flaky(event_id, body):
            if event_id == 'b' and not state['failed']:
                state['failed'] = True
                raise RuntimeError('boom')

        with self.assertRaises(RuntimeError):
            publish(self.path, flaky)
        self.assertEqual(self.query('SELECT id, delivered FROM outbox ORDER BY id'), [('a', 1), ('b', 0), ('c', 0)])
        replayed = []
        self.assertEqual(publish(self.path, lambda event_id, body: replayed.append(event_id)), 2)
        self.assertEqual(replayed, ['b', 'c'])

    def test_callback_may_consume_on_same_database(self):
        self.finish_jobs(['a'])
        self.assertEqual(publish(self.path, lambda event_id, body: consume(self.path, event_id, body)), 1)
        self.assertEqual([row[0] for row in self.query('SELECT id FROM inbox')], ['a'])


class InboxTests(StoreTestCase):
    def test_consume_is_first_wins(self):
        self.assertTrue(consume(self.path, 'evt', 'first'))
        self.assertFalse(consume(self.path, 'evt', 'second'))
        self.assertEqual(self.query('SELECT body FROM inbox WHERE id=?', ('evt',)), [('first',)])


if __name__ == '__main__':
    unittest.main()
