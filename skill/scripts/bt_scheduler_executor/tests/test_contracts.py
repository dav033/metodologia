"""T1: own types round-trip and reject malformed input; the five ports are structural."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[2])]
import bt_scheduler_executor as ex
import support
from bt_scheduler_executor import model as m


class Types(unittest.TestCase):
    def test_a_start_request_round_trips_through_json(self):
        req = support.order(3, "ok", timeout=12.5)
        again = ex.StartRequest.from_dict(json.loads(json.dumps(req.to_dict())))
        self.assertEqual(again, req)

    def test_malformed_orders_are_refused_with_a_stable_code(self):
        good = support.order(1).to_dict()
        for field, bad in (("attempt_id", ""), ("attempt_id", 5), ("revision", "1"), ("revision", True), ("token", None),
                           ("executor", "  "), ("timeout_seconds", -1), ("timeout_seconds", "x"), ("repository", "a\0b"),
                           ("acceptance_criteria", [1]), ("verification", ["x"])):
            with self.subTest(field=field, bad=bad), self.assertRaises(ex.ExecutorError) as caught:
                ex.StartRequest.from_dict({**good, field: bad})
            self.assertEqual(caught.exception.code, "ORDER_INVALID")

    def test_missing_fields_and_non_objects_are_refused(self):
        for value in (None, [], "x", {}):
            with self.assertRaises(ex.ExecutorError):
                ex.StartRequest.from_dict(value)
        good = support.order(1).to_dict()
        del good["token"]
        with self.assertRaises(ex.ExecutorError) as caught:
            ex.StartRequest.from_dict(good)
        self.assertIn("token", caught.exception.detail)

    def test_a_route_needs_provider_and_model_and_never_defaults_them(self):
        with self.assertRaises(ex.ExecutorError):
            ex.Route.from_dict({"provider": "p"})
        with self.assertRaises(ex.ExecutorError):
            ex.Route.from_dict({"model": "m"})
        route = ex.Route.from_dict({"provider": "p", "model": "m"})
        self.assertEqual((route.profile, route.effort), ("", ""))

    def test_receipt_and_status_vocabularies_are_closed(self):
        with self.assertRaises(ValueError):
            ex.Receipt("maybe")
        with self.assertRaises(ValueError):
            ex.AttemptStatus("done")
        for state in m.STATUS_STATES:
            ex.AttemptStatus(state)

    def test_events_round_trip_and_ids_are_plain_text(self):
        event = ex.TechnicalEvent("a:started", m.EV_STARTED, "P", 1, "T1", "a", 7, "2026-01-01T00:00:00+00:00", {"x": 1})
        self.assertEqual(ex.TechnicalEvent.from_dict(json.loads(json.dumps(event.to_dict()))), event)

    def test_launch_never_shows_its_secrets_or_prompt(self):
        launch = ex.Launch(argv=("/usr/bin/agent", "PROMPT-TEXT"), stdin="STDIN-TEXT", env_set=(("TOKEN", "s3cret"),))
        self.assertNotIn("s3cret", repr(launch))
        self.assertNotIn("PROMPT-TEXT", repr(launch))
        red = launch.redacted()
        self.assertNotIn("s3cret", json.dumps(red))
        self.assertEqual(red["env_set"], ["TOKEN"])

    def test_the_state_machine_has_no_edge_out_of_a_terminal_state(self):
        for state in m.TERMINAL:
            self.assertEqual(m.TRANSITIONS[state], frozenset())
        for state in m.LIVE:
            self.assertTrue(m.TRANSITIONS[state])

    def test_error_codes_are_closed(self):
        with self.assertRaises(ValueError):
            ex.ExecutorError("MADE_UP")
        self.assertIn("QUEUE_FULL", ex.CODES)

    def test_config_rejects_nonsense(self):
        for bad in (dict(max_running=0), dict(poll_seconds=-1), dict(timeout_seconds=10, max_timeout_seconds=5),
                    dict(max_queued=True)):
            with self.subTest(bad=bad), self.assertRaises(ex.ExecutorError):
                ex.Config(**bad).validate()
        ex.Config().validate()


class Ports(unittest.TestCase):
    def test_plain_objects_satisfy_every_port_structurally(self):
        class Anything:
            def resolve(self, request): ...
            def brief(self, request): ...
            def prepare(self, route, prompt, workspace, timeout_seconds): ...
            def classify(self, route, raw, returncode, *, timed_out=False, cancelled=False): ...
            def allocate(self, request): ...
            def check(self, request): ...
            def deliver(self, event): ...
        thing = Anything()
        for port in (ex.RouteResolver, ex.BriefSource, ex.AgentDriver, ex.WorkspaceManager, ex.EventSink):
            self.assertIsInstance(thing, port)

    def test_the_test_doubles_satisfy_the_ports_too(self):
        self.assertIsInstance(support.FakeResolver(), ex.RouteResolver)
        self.assertIsInstance(support.FakeDriver(), ex.AgentDriver)
        self.assertIsInstance(support.Sink(), ex.EventSink)

    def test_the_public_surface_is_listed_and_importable(self):
        for name in ex.__all__:
            self.assertTrue(hasattr(ex, name), name)


if __name__ == "__main__":
    unittest.main()
