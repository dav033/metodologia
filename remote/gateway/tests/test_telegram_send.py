import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from notifications import NotificationOutbox


def telegram_error(status):
    return HTTPError("https://api.telegram.org/bot/token/sendMessage", status, "failed", {}, None)


class TelegramDeliveryTests(unittest.TestCase):
    def test_5xx_retries_with_exponential_backoff_and_records_each_attempt(self):
        outbox = NotificationOutbox(":memory:")
        outbox.enqueue("event:one", "message", created_at=1000)
        calls = []

        def send(message):
            calls.append(message)
            if len(calls) < 3:
                raise telegram_error(503)

        self.assertEqual(outbox.deliver_due(send, now=1000), 0)
        self.assertEqual(outbox.deliver_due(send, now=1004), 0)
        self.assertEqual(len(calls), 1)
        self.assertEqual(outbox.deliver_due(send, now=1005), 0)
        self.assertEqual(outbox.deliver_due(send, now=1014), 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(outbox.deliver_due(send, now=1015), 1)

        history = outbox.history()
        self.assertEqual([row["outcome"] for row in history], ["retry", "retry", "sent"])
        self.assertEqual([row["attempt"] for row in history], [1, 2, 3])
        self.assertEqual([row["error"] for row in history], ["HTTPError:503", "HTTPError:503", None])

    def test_message_older_than_one_hour_is_dropped_and_marked(self):
        outbox = NotificationOutbox(":memory:")
        outbox.enqueue("event:old", "message", created_at=1000)
        sent = []

        self.assertEqual(outbox.deliver_due(sent.append, now=4601), 0)
        self.assertEqual(sent, [])
        self.assertEqual(outbox.history(), [{
            "dedupeKey": "event:old", "outcome": "dropped", "attempt": 0,
            "at": 4601, "error": "expired",
        }])
        self.assertEqual(outbox.deliver_due(sent.append, now=5000), 0)
        self.assertEqual(sent, [])

    def test_history_survives_restart_and_permanent_rejection_is_dropped(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "gateway.sqlite"
            outbox = NotificationOutbox(str(database))
            outbox.enqueue("event:bad", "message", created_at=1000)
            self.assertEqual(outbox.deliver_due(lambda _message: (_ for _ in ()).throw(telegram_error(400)), now=1000), 0)
            outbox = NotificationOutbox(str(database))

            self.assertEqual([row["outcome"] for row in outbox.history()], ["dropped"])
            self.assertEqual(outbox.history()[0]["error"], "HTTPError:400")


if __name__ == "__main__":
    unittest.main()
