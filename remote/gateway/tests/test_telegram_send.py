import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from app import GatewayRuntime
from main import main
from notifications import NotificationOutbox
from test_notify import FakeLaptop, FakeResponse, failed_event
import test_notify


def http_error(code):
    return HTTPError("https://api.telegram.org/x", code, "err", {}, None)


class OutboxDeliveryTests(unittest.TestCase):
    def test_5xx_is_retried_with_growing_backoff_then_sent(self):
        outbox = NotificationOutbox(":memory:")
        outbox.enqueue("k", "m", None, now=1000.0)
        calls = []

        def send(message, url=None):
            calls.append(1)
            if len(calls) < 3:
                raise http_error(502)

        self.assertEqual(outbox.deliver_due(send, now=1000.0), 0)
        self.assertEqual(outbox.deliver_due(send, now=1002.0), 0)  # still backing off (5s)
        self.assertEqual(len(calls), 1)
        self.assertEqual(outbox.deliver_due(send, now=1005.0), 0)  # second failure -> 10s
        self.assertEqual(outbox.deliver_due(send, now=1014.0), 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(outbox.deliver_due(send, now=1015.0), 1)
        self.assertEqual([h["outcome"] for h in outbox.history()], ["retry", "retry", "sent"])
        self.assertEqual(outbox.history()[0]["error"], "HTTPError:502")

    def test_message_older_than_one_hour_is_dropped_and_marked(self):
        outbox = NotificationOutbox(":memory:")
        outbox.enqueue("old", "m", None, now=1000.0)
        sent = []
        self.assertEqual(outbox.deliver_due(lambda m, url=None: sent.append(m), now=1000.0 + 3601), 0)
        self.assertEqual(sent, [])
        self.assertEqual(outbox.history()[-1]["outcome"], "dropped")
        self.assertEqual(outbox.history()[-1]["error"], "expired")
        self.assertEqual(outbox.deliver_due(lambda m, url=None: sent.append(m), now=1000.0 + 4000), 0)
        self.assertEqual(sent, [])

    def test_permanent_4xx_is_dropped_but_429_is_retried(self):
        outbox = NotificationOutbox(":memory:")
        outbox.enqueue("a", "m", None, now=1.0)
        outbox.enqueue("b", "m", None, now=1.0)

        def send(message, url=None):
            raise http_error(429 if not outbox.history() or len(outbox.history()) % 2 == 0 else 400)

        outbox.deliver_due(send, now=1.0)
        outcomes = {h["dedupeKey"]: h["outcome"] for h in outbox.history()}
        self.assertEqual(sorted(outcomes.values()), ["dropped", "retry"])


class ProductionHistoryTests(unittest.TestCase):
    env = test_notify.NotifyTests.env
    def test_main_retries_5xx_and_history_records_each_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            laptop = FakeLaptop()
            laptop.feed = [failed_event()]
            attempts = []

            def fake_urlopen(request, timeout=None):
                attempts.append(1)
                if len(attempts) == 1:
                    raise http_error(503)
                return FakeResponse()

            clock = [10_000.0]

            def cycle(runtime):
                runtime.poll_once()
                clock[0] += 6
                runtime.outbox.deliver_due(runtime.sender, now=clock[0])
                self.history = runtime.outbox.history()

            with patch.dict(os.environ, self.env(directory), clear=True), \
                    patch("app.LaptopClient", return_value=laptop), \
                    patch("notifications.urlopen", fake_urlopen), \
                    patch("notifications.time.time", lambda: 10_000.0), \
                    patch.object(GatewayRuntime, "run_forever", cycle):
                self.assertEqual(main(), 0)
            self.assertEqual(len(attempts), 2)
            self.assertEqual([h["outcome"] for h in self.history], ["retry", "sent"])



if __name__ == "__main__":
    unittest.main()
