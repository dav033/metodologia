import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError

from notifications import NotificationOutbox


class TelegramOutboxDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.outbox = NotificationOutbox(str(Path(self.temporary_directory.name) / "gateway.sqlite"))
        self.addCleanup(self.outbox._db.close)

    def test_server_error_retries_with_backoff_and_records_each_attempt(self):
        self.outbox.enqueue("event:retry", "hello")
        now = time.time()
        attempts = []

        def send(message):
            attempts.append(message)
            if len(attempts) == 1:
                raise HTTPError("https://api.telegram.org/sendMessage", 503, "unavailable", {}, None)

        self.assertEqual(self.outbox.deliver_due(send, now=now), 0)
        row = self.outbox._db.execute(
            "SELECT status, attempts, next_attempt FROM telegram_outbox WHERE dedupe_key = ?", ("event:retry",)
        ).fetchone()
        self.assertEqual(row[:2], ("pending", 1))
        self.assertAlmostEqual(row[2], now + 5)
        self.assertEqual(self.outbox.deliver_due(send, now=now + 4), 0)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(self.outbox.deliver_due(send, now=now + 5), 1)
        self.assertEqual(self.outbox.history("event:retry"), [
            {"dedupe_key": "event:retry", "recorded_at": now, "outcome": "retry", "error": "HTTP503"},
            {"dedupe_key": "event:retry", "recorded_at": now + 5, "outcome": "sent", "error": None},
        ])

    def test_message_older_than_one_hour_is_dropped_and_marked(self):
        self.outbox.enqueue("event:stale", "old message")
        now = time.time()
        self.outbox._db.execute(
            "UPDATE telegram_outbox SET created_at = ?, next_attempt = ? WHERE dedupe_key = ?",
            (now - 3601, now + 1000, "event:stale"),
        )
        self.outbox._db.commit()
        sent = []

        self.assertEqual(self.outbox.deliver_due(sent.append, now=now), 0)
        self.assertEqual(sent, [])
        state = self.outbox._db.execute(
            "SELECT status, last_error FROM telegram_outbox WHERE dedupe_key = ?", ("event:stale",)
        ).fetchone()
        self.assertEqual(state, ("dropped", "MessageExpired"))
        self.assertEqual(self.outbox.history("event:stale"), [
            {"dedupe_key": "event:stale", "recorded_at": now, "outcome": "dropped", "error": "MessageExpired"},
        ])

    def test_successful_delivery_is_recorded(self):
        self.outbox.enqueue("event:sent", "hello")
        now = time.time()

        self.assertEqual(self.outbox.deliver_due(lambda message: None, now=now), 1)
        self.assertEqual(self.outbox.history("event:sent")[0]["outcome"], "sent")


if __name__ == "__main__":
    unittest.main()
