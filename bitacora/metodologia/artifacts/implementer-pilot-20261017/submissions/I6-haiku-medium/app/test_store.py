import json
import os
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


class InitAndEnqueueTests(StoreTestCase):
    def test_init_is_idempotent_and_preserves_data(self):
        enqueue(self.path, "a", "work")
        init(self.path)
        self.assertEqual(inspect(self.path, "a")["payload"], "work")

    def test_schema_columns(self):
        enqueue(self.path, "a", "work")
        row = inspect(self.path, "a")
        self.assertEqual(
            sorted(row),
            sorted(["id", "payload", "state", "token", "lease_until",
                    "attempts", "depends_on", "result"]),
        )
        self.assertEqual(row["state"], "pending")
        self.assertEqual(row["token"], 0)
        self.assertEqual(row["attempts"], 0)
        self.assertIsNone(row["lease_until"])

    def test_duplicate_enqueue_keeps_first_payload(self):
        enqueue(self.path, "a", "first")
        enqueue(self.path, "a", "second")
        self.assertEqual(inspect(self.path, "a")["payload"], "first")

    def test_inspect_missing_returns_none(self):
        self.assertIsNone(inspect(self.path, "nope"))

    def test_wrong_types_raise_type_error(self):
        with self.assertRaises(TypeError):
            enqueue(self.path, 1, "work")
        with self.assertRaises(TypeError):
            claim(self.path, "0", 10)


class ClaimTests(StoreTestCase):
    def test_claim_selects_smallest_id_and_sets_lease(self):
        enqueue(self.path, "b", "pb")
        enqueue(self.path, "a", "pa")
        self.assertEqual(claim(self.path, 0, 10), ("a", "pa", 1))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["lease_until"], row["attempts"]), ("running", 10, 1))

    def test_claim_returns_none_when_nothing_eligible(self):
        self.assertIsNone(claim(self.path, 0, 10))

    def test_ttl_must_be_positive_without_mutation(self):
        enqueue(self.path, "a", "work")
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                claim(self.path, 0, ttl)
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["token"], row["attempts"]), ("pending", 0, 0))

    def test_active_lease_blocks_then_expiry_allows_reclaim(self):
        enqueue(self.path, "a", "work")
        self.assertEqual(claim(self.path, 0, 10), ("a", "work", 1))
        self.assertIsNone(claim(self.path, 5, 10))
        # Expiry is lease_until <= now, so the lease expires exactly at 10.
        self.assertEqual(claim(self.path, 10, 10), ("a", "work", 2))
        row = inspect(self.path, "a")
        self.assertEqual((row["token"], row["attempts"], row["lease_until"]), (2, 2, 20))

    def test_concurrent_claims_yield_single_lease(self):
        enqueue(self.path, "a", "work")
        results = []
        lock = threading.Lock()

        def worker():
            got = claim(self.path, 0, 100)
            with lock:
                results.append(got)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        winners = [r for r in results if r is not None]
        self.assertEqual(len(winners), 1)
        self.assertEqual(winners[0], ("a", "work", 1))


class CompleteTests(StoreTestCase):
    def setUp(self):
        super().setUp()
        enqueue(self.path, "a", "work")
        self.assertEqual(claim(self.path, 0, 10), ("a", "work", 1))

    def test_complete_with_valid_lease(self):
        self.assertTrue(complete(self.path, "a", 1, "out", 5))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["result"], row["lease_until"]), ("done", "out", None))

    def test_stale_token_is_rejected_without_mutation(self):
        before = inspect(self.path, "a")
        self.assertFalse(complete(self.path, "a", 0, "out", 5))
        self.assertEqual(inspect(self.path, "a"), before)

    def test_expired_lease_is_rejected(self):
        self.assertFalse(complete(self.path, "a", 1, "out", 10))
        self.assertEqual(inspect(self.path, "a")["state"], "running")

    def test_missing_job_returns_false(self):
        self.assertFalse(complete(self.path, "zzz", 1, "out", 5))

    def test_fenced_older_claimant_after_reclaim(self):
        retry(self.path, "a", 1, 5)
        self.assertEqual(claim(self.path, 5, 10), ("a", "work", 2))
        self.assertFalse(complete(self.path, "a", 1, "old", 6))
        self.assertTrue(complete(self.path, "a", 2, "new", 6))
        self.assertEqual(inspect(self.path, "a")["result"], "new")

    def test_completion_publishes_exactly_one_event(self):
        complete(self.path, "a", 1, "out", 5)
        self.assertFalse(complete(self.path, "a", 1, "again", 5))
        events = []
        self.assertEqual(publish(self.path, lambda i, b: events.append((i, b))), 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(json.loads(events[0][1]), {"id": "a", "result": "out"})

    def test_hook_exception_rolls_back_and_propagates(self):
        for point in ("after_result", "before_commit"):
            seen = []

            def hook(name, point=point):
                seen.append(name)
                if name == point:
                    raise RuntimeError(name)

            with self.assertRaises(RuntimeError):
                complete(self.path, "a", 1, "out", 5, fault=hook)
            row = inspect(self.path, "a")
            self.assertEqual((row["state"], row["result"]), ("running", None))
            self.assertEqual(publish(self.path, lambda i, b: None), 0)

    def test_stale_completion_does_not_invoke_hooks(self):
        calls = []
        self.assertFalse(complete(self.path, "a", 9, "out", 5, fault=calls.append))
        self.assertEqual(calls, [])


class CrashRecoveryTests(StoreTestCase):
    def _crash_at(self, point):
        enqueue(self.path, "a", "work")
        self.assertEqual(claim(self.path, 0, 100), ("a", "work", 1))
        code = (
            "import os, sys\n"
            "from app.store import complete\n"
            "p, w = sys.argv[1], sys.argv[2]\n"
            "complete(p, 'a', 1, 'out', 5, fault=lambda s: os._exit(3) if s == w else None)\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code, self.path, point],
            cwd=REPO_ROOT,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 3, proc.stderr.decode())

    def test_crash_after_result_leaves_nothing(self):
        self._crash_at("after_result")
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["result"]), ("running", None))
        self.assertEqual(publish(self.path, lambda i, b: None), 0)

    def test_crash_before_commit_leaves_nothing(self):
        self._crash_at("before_commit")
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["result"]), ("running", None))
        self.assertEqual(publish(self.path, lambda i, b: None), 0)


class RetryTests(StoreTestCase):
    def test_retry_releases_valid_lease_and_preserves_counters(self):
        enqueue(self.path, "a", "work")
        claim(self.path, 0, 10)
        self.assertTrue(retry(self.path, "a", 1, 5))
        row = inspect(self.path, "a")
        self.assertEqual((row["state"], row["lease_until"], row["token"], row["attempts"]),
                         ("pending", None, 1, 1))
        self.assertEqual(claim(self.path, 5, 10), ("a", "work", 2))

    def test_retry_rejects_expired_or_stale_lease(self):
        enqueue(self.path, "a", "work")
        claim(self.path, 0, 10)
        self.assertFalse(retry(self.path, "a", 1, 10))
        self.assertFalse(retry(self.path, "a", 0, 5))
        self.assertEqual(inspect(self.path, "a")["state"], "running")


class DependencyTests(StoreTestCase):
    def test_child_waits_for_done_parent(self):
        enqueue(self.path, "p", "parent")
        enqueue(self.path, "c", "child", depends_on="p")
        self.assertEqual(claim(self.path, 0, 10), ("p", "parent", 1))
        self.assertIsNone(claim(self.path, 1, 10))
        complete(self.path, "p", 1, "r", 2)
        self.assertEqual(claim(self.path, 3, 10), ("c", "child", 1))

    def test_missing_parent_blocks(self):
        enqueue(self.path, "c", "child", depends_on="ghost")
        self.assertIsNone(claim(self.path, 0, 10))

    def test_cycle_stays_blocked(self):
        enqueue(self.path, "a", "x", depends_on="b")
        enqueue(self.path, "b", "y", depends_on="a")
        self.assertIsNone(claim(self.path, 0, 10))


class PublishConsumeTests(StoreTestCase):
    def _complete_jobs(self, *ids):
        for job_id in ids:
            enqueue(self.path, job_id, "p")
            claim_result = claim(self.path, 0, 100)
            self.assertEqual(claim_result[0], job_id)
            complete(self.path, job_id, claim_result[2], "r-" + job_id, 1)

    def test_publish_delivers_in_order_and_marks_delivered(self):
        self._complete_jobs("b", "a")
        seen = []
        self.assertEqual(publish(self.path, lambda i, b: seen.append(i)), 2)
        self.assertEqual(seen, ["a", "b"])
        self.assertEqual(publish(self.path, lambda i, b: seen.append(i)), 0)

    def test_callback_error_stops_and_replays_remaining(self):
        self._complete_jobs("a", "b", "c")
        delivered = []

        def flaky(event_id, body):
            if event_id == "b":
                raise OSError("boom")
            delivered.append(event_id)

        with self.assertRaises(OSError):
            publish(self.path, flaky)
        self.assertEqual(delivered, ["a"])
        replayed = []
        self.assertEqual(publish(self.path, lambda i, b: replayed.append(i)), 2)
        self.assertEqual(replayed, ["b", "c"])

    def test_callback_may_consume_on_same_database(self):
        self._complete_jobs("a")

        def deliver(event_id, body):
            self.assertTrue(consume(self.path, event_id, body))

        self.assertEqual(publish(self.path, deliver), 1)

    def test_consume_is_idempotent_and_keeps_first_body(self):
        self.assertTrue(consume(self.path, "m", "first"))
        self.assertFalse(consume(self.path, "m", "second"))
        with self.assertRaises(TypeError):
            consume(self.path, "m", None)


if __name__ == "__main__":
    unittest.main()
