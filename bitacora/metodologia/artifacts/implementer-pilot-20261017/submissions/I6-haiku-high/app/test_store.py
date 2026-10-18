import os
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest

from app.store import claim, complete, consume, enqueue, init, inspect, publish, retry

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "db")
        init(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def raw(self, sql, params=()):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()


class InitAndEnqueueTests(StoreTestCase):
    def test_init_is_idempotent_and_preserves_data(self):
        enqueue(self.path, "a", "work")
        init(self.path)
        self.assertEqual(inspect(self.path, "a")["payload"], "work")

    def test_schema_tables_exist(self):
        names = {row[0] for row in self.raw("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertTrue({"jobs", "outbox", "inbox"} <= names)

    def test_duplicate_enqueue_keeps_first_payload(self):
        enqueue(self.path, "a", "first")
        enqueue(self.path, "a", "second")
        self.assertEqual(inspect(self.path, "a")["payload"], "first")

    def test_inspect_returns_all_columns_or_none(self):
        enqueue(self.path, "a", "work")
        row = inspect(self.path, "a")
        self.assertEqual(
            set(row),
            {"id", "payload", "state", "token", "lease_until", "attempts", "depends_on", "result"},
        )
        self.assertEqual(row["state"], "pending")
        self.assertEqual(row["token"], 0)
        self.assertIsNone(inspect(self.path, "missing"))

    def test_missing_database_is_not_created_by_inspect(self):
        missing = os.path.join(self._tmp.name, "nope")
        with self.assertRaises(sqlite3.OperationalError):
            inspect(missing, "a")
        self.assertFalse(os.path.exists(missing))

    def test_non_str_arguments_raise_type_error(self):
        with self.assertRaises(TypeError):
            enqueue(self.path, 1, "work")
        with self.assertRaises(TypeError):
            claim(self.path, "0", 10)


class ClaimTests(StoreTestCase):
    def test_claim_returns_smallest_eligible_id_with_token_one(self):
        enqueue(self.path, "b", "B")
        enqueue(self.path, "a", "A")
        self.assertEqual(claim(self.path, 0, 10), ("a", "A", 1))
        self.assertEqual(claim(self.path, 0, 10), ("b", "B", 1))
        self.assertIsNone(claim(self.path, 0, 10))

    def test_claim_sets_lease_and_attempts(self):
        enqueue(self.path, "a", "work")
        claim(self.path, 5, 10)
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["lease_until"], row["attempts"]), ("running", 15, 1))

    def test_non_positive_ttl_raises_before_mutation(self):
        enqueue(self.path, "a", "work")
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                claim(self.path, 0, ttl)
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["token"], row["attempts"]), ("pending", 0, 0))

    def test_lease_expiry_is_inclusive_and_reclaim_increments_token(self):
        enqueue(self.path, "a", "work")
        self.assertEqual(claim(self.path, 0, 10), ("a", "work", 1))
        self.assertIsNone(claim(self.path, 9, 10))
        self.assertEqual(claim(self.path, 10, 10), ("a", "work", 2))
        self.assertEqual(inspect(self.path, "a")["attempts"], 2)

    def test_token_persists_across_reopen(self):
        enqueue(self.path, "a", "work")
        claim(self.path, 0, 10)
        self.assertEqual(inspect(self.path, "a")["token"], 1)
        self.assertEqual(claim(self.path, 10, 10)[2], 2)


class CompleteTests(StoreTestCase):
    def test_complete_stores_result_and_one_outbox_event(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        self.assertTrue(complete(self.path, "a", token, "out", 5))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["result"], row["lease_until"]), ("done", "out", None))
        self.assertEqual(self.raw("SELECT id, body, delivered FROM outbox"), [("a", "out", 0)])

    def test_stale_expired_wrong_token_and_missing_return_false_without_mutation(self):
        enqueue(self.path, "a", "work")
        _, _, first = claim(self.path, 0, 10)
        _, _, second = claim(self.path, 10, 10)
        self.assertFalse(complete(self.path, "a", first, "old", 11))  # stale token
        self.assertFalse(complete(self.path, "a", second, "late", 20))  # lease expired
        self.assertFalse(complete(self.path, "a", second + 5, "bad", 11))  # wrong token
        self.assertFalse(complete(self.path, "missing", 1, "x", 0))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["result"]), ("running", None))
        self.assertEqual(self.raw("SELECT COUNT(*) FROM outbox"), [(0,)])

    def test_second_complete_is_rejected(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        self.assertTrue(complete(self.path, "a", token, "out", 1))
        self.assertFalse(complete(self.path, "a", token, "again", 1))
        self.assertEqual(self.raw("SELECT COUNT(*) FROM outbox"), [(1,)])

    def test_stale_completion_does_not_invoke_hooks(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        calls = []
        self.assertFalse(complete(self.path, "a", token + 1, "x", 1, fault=calls.append))
        self.assertEqual(calls, [])

    def test_hook_exception_rolls_back_and_propagates(self):
        for stage in ("after_result", "before_commit"):
            with self.subTest(stage=stage):
                enqueue(self.path, stage, "work")
                _, _, token = claim(self.path, 0, 10)

                def fail(name):
                    if name == stage:
                        raise RuntimeError(name)

                with self.assertRaises(RuntimeError):
                    complete(self.path, stage, token, "out", 1, fault=fail)
                row = inspect(self.path, stage)
                self.assertEqual((row["state"], row["result"]), ("running", None))
                self.assertEqual(self.raw("SELECT COUNT(*) FROM outbox WHERE id = ?", (stage,)), [(0,)])

    def test_hooks_run_in_order_on_success(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        seen = []
        self.assertTrue(complete(self.path, "a", token, "out", 1, fault=seen.append))
        self.assertEqual(seen, ["after_result", "before_commit"])

    def test_process_crash_at_each_hook_leaves_nothing_committed(self):
        for stage in ("after_result", "before_commit"):
            with self.subTest(stage=stage):
                enqueue(self.path, stage, "work")
                _, _, token = claim(self.path, 0, 10)
                script = (
                    "import os, sys\n"
                    "from app.store import complete\n"
                    "def crash(name):\n"
                    "    if name == sys.argv[4]:\n"
                    "        os._exit(9)\n"
                    "complete(sys.argv[1], sys.argv[2], int(sys.argv[3]), 'out', 1, fault=crash)\n"
                )
                proc = subprocess.run(
                    [sys.executable, "-c", script, self.path, stage, str(token), stage],
                    cwd=REPO_ROOT,
                    capture_output=True,
                )
                self.assertEqual(proc.returncode, 9, proc.stderr)
                row = inspect(self.path, stage)
                self.assertEqual((row["state"], row["result"]), ("running", None))
                self.assertEqual(self.raw("SELECT COUNT(*) FROM outbox WHERE id = ?", (stage,)), [(0,)])


class DependencyTests(StoreTestCase):
    def test_child_waits_for_done_parent(self):
        enqueue(self.path, "child", "C", depends_on="parent")
        enqueue(self.path, "parent", "P")
        self.assertEqual(claim(self.path, 0, 10), ("parent", "P", 1))
        self.assertIsNone(claim(self.path, 0, 10))
        self.assertTrue(complete(self.path, "parent", 1, "done", 1))
        self.assertEqual(claim(self.path, 2, 10), ("child", "C", 1))

    def test_missing_parent_and_cycles_block(self):
        enqueue(self.path, "orphan", "O", depends_on="missing")
        enqueue(self.path, "x", "X", depends_on="y")
        enqueue(self.path, "y", "Y", depends_on="x")
        self.assertIsNone(claim(self.path, 0, 10))


class RetryTests(StoreTestCase):
    def test_retry_releases_valid_lease_and_preserves_counters(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        self.assertTrue(retry(self.path, "a", token, 5))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["lease_until"], row["token"], row["attempts"]), ("pending", None, 1, 1))
        self.assertEqual(claim(self.path, 5, 10), ("a", "work", 2))
        self.assertEqual(inspect(self.path, "a")["attempts"], 2)

    def test_retry_rejects_stale_expired_or_missing(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 10)
        self.assertFalse(retry(self.path, "a", token + 1, 5))
        self.assertFalse(retry(self.path, "a", token, 10))  # expired
        self.assertFalse(retry(self.path, "missing", token, 5))
        self.assertEqual(inspect(self.path, "a")["state"], "running")


class OutboxInboxTests(StoreTestCase):
    def test_publish_delivers_in_id_order_and_marks_delivered(self):
        for job_id in ("b", "a"):
            enqueue(self.path, job_id, "w")
            _, _, token = claim(self.path, 0, 10)
            complete(self.path, job_id, token, f"r-{job_id}", 1)
        got = []
        self.assertEqual(publish(self.path, lambda i, b: got.append((i, b))), 2)
        self.assertEqual(got, [("a", "r-a"), ("b", "r-b")])
        self.assertEqual(publish(self.path, lambda i, b: got.append((i, b))), 0)

    def test_callback_error_stops_and_replays_remaining(self):
        for job_id in ("a", "b", "c"):
            enqueue(self.path, job_id, "w")
            _, _, token = claim(self.path, 0, 10)
            complete(self.path, job_id, token, job_id, 1)

        def fail_on_b(event_id, body):
            if event_id == "b":
                raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            publish(self.path, fail_on_b)
        self.assertEqual(self.raw("SELECT id, delivered FROM outbox ORDER BY id"), [("a", 1), ("b", 0), ("c", 0)])
        replayed = []
        self.assertEqual(publish(self.path, lambda i, b: replayed.append(i)), 2)
        self.assertEqual(replayed, ["b", "c"])

    def test_consume_is_once_and_keeps_first_body(self):
        self.assertTrue(consume(self.path, "m", "first"))
        self.assertFalse(consume(self.path, "m", "second"))
        self.assertEqual(self.raw("SELECT body FROM inbox WHERE id = 'm'"), [("first",)])

    def test_consume_is_allowed_inside_publish_callback(self):
        enqueue(self.path, "a", "w")
        _, _, token = claim(self.path, 0, 10)
        complete(self.path, "a", token, "r", 1)
        results = []
        publish(self.path, lambda i, b: results.append(consume(self.path, i, b)))
        self.assertEqual(results, [True])


class ConcurrencyTests(StoreTestCase):
    def test_racing_claims_yield_one_lease_per_job(self):
        enqueue(self.path, "only", "w")
        results = []
        lock = threading.Lock()

        def worker():
            got = claim(self.path, 0, 100)
            with lock:
                results.append(got)

        threads = [threading.Thread(target=worker) for _ in range(12)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        winners = [r for r in results if r is not None]
        self.assertEqual(winners, [("only", "w", 1)])

    def test_racing_consumes_insert_once(self):
        results = []
        lock = threading.Lock()

        def worker(n):
            got = consume(self.path, "same", f"body-{n}")
            with lock:
                results.append(got)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(len(self.raw("SELECT body FROM inbox")), 1)


if __name__ == "__main__":
    unittest.main()
