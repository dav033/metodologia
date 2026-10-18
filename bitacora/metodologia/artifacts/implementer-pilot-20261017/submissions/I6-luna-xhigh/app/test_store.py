import os
import sqlite3
import tempfile
import threading
import unittest

from app.store import claim, complete, consume, enqueue, init, inspect, publish, retry


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.directory.name, "queue.sqlite")
        init(self.path)

    def tearDown(self):
        self.directory.cleanup()

    def test_init_schema_is_exact_and_idempotent(self):
        init(self.path)
        with sqlite3.connect(self.path) as connection:
            schemas = {
                name: [row[1] for row in connection.execute(f"PRAGMA table_info({name})")]
                for name in ("jobs", "outbox", "inbox")
            }
        self.assertEqual(
            schemas,
            {
                "jobs": [
                    "id", "payload", "state", "token", "lease_until",
                    "attempts", "depends_on", "result",
                ],
                "outbox": ["id", "body", "delivered"],
                "inbox": ["id", "body"],
            },
        )

    def test_dependencies_order_expiration_and_fencing(self):
        enqueue(self.path, "b", "child", depends_on="a")
        enqueue(self.path, "z", "later")
        enqueue(self.path, "a", "parent")
        enqueue(self.path, "a", "changed payload")
        self.assertEqual(claim(self.path, 0, 5), ("a", "parent", 1))
        self.assertEqual(claim(self.path, 0, 5), ("z", "later", 1))
        self.assertIsNone(claim(self.path, 4, 5))
        self.assertEqual(claim(self.path, 5, 5), ("a", "parent", 2))
        self.assertFalse(complete(self.path, "a", 1, "old", 5))
        self.assertTrue(complete(self.path, "a", 2, "done", 5))
        self.assertEqual(claim(self.path, 5, 5), ("b", "child", 1))
        self.assertEqual(inspect(self.path, "a")["attempts"], 2)

    def test_retry_preserves_token_and_attempt_count(self):
        enqueue(self.path, "a", "work")
        self.assertEqual(claim(self.path, 0, 10), ("a", "work", 1))
        self.assertFalse(retry(self.path, "a", 1, 10))
        self.assertTrue(retry(self.path, "a", 1, 9))
        before = inspect(self.path, "a")
        self.assertEqual((before["token"], before["attempts"], before["lease_until"]), (1, 1, None))
        self.assertEqual(claim(self.path, 10, 1), ("a", "work", 2))

    def test_complete_rolls_back_both_fault_points_and_publishes_once(self):
        enqueue(self.path, "a", "work")
        _, _, token = claim(self.path, 0, 5)
        for stop_at in ("after_result", "before_commit"):
            with self.assertRaises(RuntimeError):
                complete(
                    self.path,
                    "a",
                    token,
                    "value",
                    1,
                    fault=lambda stage: (_ for _ in ()).throw(RuntimeError(stage))
                    if stage == stop_at
                    else None,
                )
            init(self.path)
            self.assertEqual(inspect(self.path, "a")["state"], "running")
            with sqlite3.connect(self.path) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM outbox").fetchone()[0], 0)

        self.assertTrue(complete(self.path, "a", token, "value", 1))
        self.assertFalse(complete(self.path, "a", token, "again", 1))
        seen = []

        def deliver(event_id, body):
            seen.append((event_id, body))
            self.assertTrue(consume(self.path, event_id, body))

        self.assertEqual(publish(self.path, deliver), 1)
        self.assertEqual(seen, [("a", "value")])
        self.assertEqual(publish(self.path, deliver), 0)
        self.assertFalse(consume(self.path, "a", "different first body"))
        with sqlite3.connect(self.path) as connection:
            self.assertEqual(connection.execute("SELECT body FROM inbox WHERE id='a'").fetchone()[0], "value")

    def test_publish_replays_callback_that_raises(self):
        enqueue(self.path, "a", "a")
        enqueue(self.path, "b", "b")
        for job_id in ("a", "b"):
            _, _, token = claim(self.path, 0, 10)
            self.assertTrue(complete(self.path, job_id, token, job_id.upper(), 1))

        calls = []

        def flaky(event_id, body):
            calls.append((event_id, body))
            if event_id == "b":
                raise RuntimeError("delivery failed")

        with self.assertRaises(RuntimeError):
            publish(self.path, flaky)
        self.assertEqual(calls, [("a", "A"), ("b", "B")])
        replayed = []
        self.assertEqual(publish(self.path, lambda event_id, body: replayed.append((event_id, body))), 1)
        self.assertEqual(replayed, [("b", "B")])

    def test_claims_are_exclusive_across_threads(self):
        enqueue(self.path, "a", "work")
        barrier = threading.Barrier(3)
        results = []
        result_lock = threading.Lock()

        def worker():
            barrier.wait()
            result = claim(self.path, 0, 10)
            with result_lock:
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for thread in threads:
            thread.start()
        barrier.wait()
        for thread in threads:
            thread.join()
        self.assertCountEqual(results, [("a", "work", 1), None])

    def test_nonpositive_ttl_does_not_change_job(self):
        enqueue(self.path, "a", "work")
        before = inspect(self.path, "a")
        with self.assertRaises(ValueError):
            claim(self.path, 0, 0)
        self.assertEqual(inspect(self.path, "a"), before)


if __name__ == "__main__":
    unittest.main()
