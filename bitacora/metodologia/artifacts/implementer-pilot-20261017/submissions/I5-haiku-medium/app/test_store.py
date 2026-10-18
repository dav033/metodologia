import multiprocessing
import os
import sqlite3
import tempfile
import unittest

from app.store import claim, complete, enqueue, init, inspect

COLUMNS = [
    "id", "payload", "state", "token", "lease_until",
    "attempts", "depends_on", "result",
]


def _drain(path, now):
    """Worker body: claim until the queue is empty, return claimed ids."""
    claimed = []
    while True:
        got = claim(path, now, 1000)
        if got is None:
            return claimed
        claimed.append(got[0])


class StoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "db")
        init(self.path)

    def tearDown(self):
        self._tmp.cleanup()

    def test_init_is_idempotent_and_schema_is_exact(self):
        init(self.path)
        with sqlite3.connect(self.path) as c:
            cols = [r[1] for r in c.execute("PRAGMA table_info(jobs)")]
        self.assertEqual(cols, COLUMNS)

    def test_inspect_missing_returns_none(self):
        self.assertIsNone(inspect(self.path, "nope"))

    def test_enqueue_duplicate_keeps_first_payload(self):
        enqueue(self.path, "a", "first")
        enqueue(self.path, "a", "second")
        job = inspect(self.path, "a")
        self.assertEqual(job["payload"], "first")
        self.assertEqual(job["state"], "pending")
        self.assertEqual(job["token"], 0)
        self.assertEqual(job["attempts"], 0)
        self.assertIsNone(job["lease_until"])
        self.assertIsNone(job["result"])

    def test_claim_returns_smallest_id_first(self):
        enqueue(self.path, "b", "pb")
        enqueue(self.path, "a", "pa")
        self.assertEqual(claim(self.path, 0, 10), ("a", "pa", 1))
        self.assertEqual(claim(self.path, 0, 10), ("b", "pb", 1))
        self.assertIsNone(claim(self.path, 0, 10))

    def test_claim_sets_lease_and_attempts(self):
        enqueue(self.path, "a", "w")
        claim(self.path, 5, 10)
        job = inspect(self.path, "a")
        self.assertEqual(job["state"], "running")
        self.assertEqual(job["lease_until"], 15)
        self.assertEqual(job["attempts"], 1)
        self.assertEqual(job["token"], 1)

    def test_live_lease_is_not_claimable(self):
        enqueue(self.path, "a", "w")
        claim(self.path, 0, 10)
        self.assertIsNone(claim(self.path, 9, 10))

    def test_expired_lease_is_reclaimed_with_new_token(self):
        enqueue(self.path, "a", "w")
        self.assertEqual(claim(self.path, 0, 10), ("a", "w", 1))
        # Expiry is lease_until <= now, so now=10 expires the lease.
        self.assertEqual(claim(self.path, 10, 10), ("a", "w", 2))
        job = inspect(self.path, "a")
        self.assertEqual(job["attempts"], 2)
        self.assertEqual(job["lease_until"], 20)

    def test_invalid_ttl_raises_before_mutation(self):
        enqueue(self.path, "a", "w")
        for ttl in (0, -1):
            with self.assertRaises(ValueError):
                claim(self.path, 0, ttl)
        job = inspect(self.path, "a")
        self.assertEqual(job["state"], "pending")
        self.assertEqual(job["token"], 0)
        self.assertEqual(job["attempts"], 0)

    def test_complete_with_current_token_stores_result(self):
        enqueue(self.path, "a", "w")
        _, _, token = claim(self.path, 0, 10)
        self.assertTrue(complete(self.path, "a", token, "out", 5))
        job = inspect(self.path, "a")
        self.assertEqual(job["state"], "done")
        self.assertEqual(job["result"], "out")
        self.assertIsNone(job["lease_until"])
        # A done job cannot be completed again.
        self.assertFalse(complete(self.path, "a", token, "again", 5))
        self.assertEqual(inspect(self.path, "a")["result"], "out")

    def test_stale_token_cannot_complete_after_reclaim(self):
        enqueue(self.path, "a", "w")
        _, _, old = claim(self.path, 0, 10)
        _, _, new = claim(self.path, 10, 10)
        self.assertFalse(complete(self.path, "a", old, "stale", 11))
        self.assertTrue(complete(self.path, "a", new, "fresh", 11))
        self.assertEqual(inspect(self.path, "a")["result"], "fresh")

    def test_expired_lease_cannot_complete(self):
        enqueue(self.path, "a", "w")
        _, _, token = claim(self.path, 0, 10)
        self.assertFalse(complete(self.path, "a", token, "late", 10))
        job = inspect(self.path, "a")
        self.assertEqual(job["state"], "running")
        self.assertIsNone(job["result"])

    def test_missing_job_completion_returns_false(self):
        self.assertFalse(complete(self.path, "ghost", 1, "x", 0))
        self.assertIsNone(inspect(self.path, "ghost"))

    def test_tokens_survive_reopening_the_store(self):
        enqueue(self.path, "a", "w")
        _, _, first = claim(self.path, 0, 10)
        # Each call opens a fresh connection, simulating a restarted client.
        init(self.path)
        _, _, second = claim(self.path, 10, 10)
        self.assertEqual((first, second), (1, 2))
        self.assertFalse(complete(self.path, "a", first, "x", 11))
        self.assertTrue(complete(self.path, "a", second, "y", 11))

    def test_type_errors_are_explicit(self):
        with self.assertRaises(TypeError):
            enqueue(self.path, 1, "w")
        with self.assertRaises(TypeError):
            claim(self.path, "0", 10)
        with self.assertRaises(TypeError):
            complete(self.path, "a", True, "x", 0)

    def test_concurrent_claimers_never_double_lease(self):
        total = 60
        for i in range(total):
            enqueue(self.path, f"job{i:03d}", "w")
        with multiprocessing.Pool(4) as pool:
            results = pool.starmap(_drain, [(self.path, 0)] * 4)
        claimed = [job_id for part in results for job_id in part]
        self.assertEqual(len(claimed), total)
        self.assertEqual(len(set(claimed)), total)
        self.assertEqual(sorted(claimed), [f"job{i:03d}" for i in range(total)])


if __name__ == "__main__":
    unittest.main()
