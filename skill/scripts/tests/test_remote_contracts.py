"""Producer/consumer verification of the remote contract (REQ-030 M1).

Runs in the uv environment (pydantic): `uv run python -m unittest test_remote_contracts`. Every check builds the REAL
output of a stdlib producer (laptop listener, gateway, Telegram relay) over a disposable bitácora root and validates
it against the Pydantic models in bt_contracts.remote; the shared fixtures the phone and gateway tests read are
validated the same way, and the generated JSON Schema / TypeScript must be fresh.
"""
from __future__ import annotations

import datetime as dt
import http.client
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydantic import ValidationError

REPO = Path(__file__).resolve().parents[3]
FIXTURES = REPO / "remote" / "contract" / "fixtures"
sys.path.insert(0, str(REPO / "remote" / "gateway"))

import app as gateway_app
import bt_remote_api
import bt_remote_commands as commands
import bt_remote_events
import remote_fixture_root
from bt_contracts import remote, schemas

KEY = "contract-test-gateway-key"


def fixture(name: str):
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


class Handler:
    """The minimal request object bt_remote_api's routes read."""

    def __init__(self, path: str):
        self.path = path
        self.headers = {"Authorization": f"Bearer {KEY}"}

    def send(self, body, status, content_type):
        self.body, self.status, self.content_type = body, status, content_type


def candidate(route_id: str, quota_status: str = "available"):
    return SimpleNamespace(route_id=route_id, provider="codex", model="gpt-6.1-sol", profile="codex-work",
                           account_ref="acct:a", source_status="available", runtime_status="available",
                           profile_authorized=True, auth_status="valid", quota_status=quota_status)


class GeneratedArtifacts(unittest.TestCase):
    def test_generated_schemas_and_typescript_are_fresh(self):
        stale = [str(path.relative_to(REPO)) for path in schemas.stale()]
        self.assertEqual(stale, [], "run `uv run python -m bt_contracts.schemas` (from skill/scripts)")

    def test_contract_vocabularies_match_the_stdlib_code(self):
        self.assertEqual(set(remote.COMMAND_TYPES), set(commands.COMMANDS))
        self.assertEqual(set(remote.COMMAND_TYPES), set(gateway_app.SUPPORTED_COMMANDS))
        self.assertEqual(set(remote.CHALLENGED_COMMANDS), set(commands.CHALLENGED))
        self.assertEqual(set(remote.CHALLENGED_COMMANDS), set(gateway_app.CHALLENGED_COMMANDS))
        self.assertEqual(set(remote.EVENT_TYPES), set(bt_remote_events.NOTIFICATION_KINDS))
        accepts = gateway_app.IDEMPOTENCY_KEY.fullmatch
        self.assertTrue(accepts("k" * remote.IDEMPOTENCY_KEY_MIN) and accepts("k" * remote.IDEMPOTENCY_KEY_MAX))
        self.assertFalse(accepts("k" * (remote.IDEMPOTENCY_KEY_MIN - 1)) or accepts("k" * (remote.IDEMPOTENCY_KEY_MAX + 1)))

    def test_shared_fixtures_validate_against_the_contract(self):
        snapshot = fixture("snapshot")
        remote.RemoteSnapshot.model_validate_json(json.dumps(snapshot))
        # What the phone mock (and the real StreamHub) serves: the laptop snapshot flattened with liveness.
        remote.GatewaySnapshot.model_validate_json(json.dumps(
            {**snapshot, "laptop": {"online": True}, "online": True, "cachedAt": 1.0, "lastEventId": "mock:0"}))
        for event in fixture("events"):
            remote.RemoteEvent.model_validate_json(json.dumps(event))
        remote.QuotasResponse.model_validate_json(json.dumps(fixture("quotas")))
        remote.RoutesResponse.model_validate_json(json.dumps(fixture("routes")))
        remote.FailureReview.model_validate_json(json.dumps(fixture("review")))
        kinds = [remote.RemoteCommand.model_validate_json(json.dumps(item)).root.type for item in fixture("commands")]
        self.assertEqual(sorted(kinds), sorted(remote.COMMAND_TYPES))


class LaptopProducers(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        remote_fixture_root.build(self.root)
        env = patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY, "BITACORA_ROOT": str(self.root)})
        env.start()
        self.addCleanup(env.stop)
        producing = remote_fixture_root.producing(self.root)
        self.base = producing.__enter__()
        self.addCleanup(producing.__exit__, None, None, None)

    def get(self, path: str):
        handler = Handler(path)
        bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200, handler.body)
        return handler.body

    def test_real_snapshot_route_validates(self):
        snapshot = remote.RemoteSnapshot.model_validate_json(self.get("/api/remote/v1/snapshot"))
        run = snapshot.runs[0]
        self.assertEqual((run.req, run.state, run.status), ("REQ-001", "running", "running"))
        self.assertEqual([task.state for task in run.tasks], ["running", "rejected", "blocked"])
        self.assertEqual(run.tasks[2].review_attempt.id, "A-failed")
        self.assertNotIn("sk-synthetic", run.tasks[2].review_attempt.failure)
        self.assertEqual(snapshot.decision_requests[0].options[1].id, "rework_conflict")
        self.assertEqual(snapshot.rounds[0].questions[1].type, "open")

    def test_real_events_route_validates(self):
        ledger = commands.Ledger()
        ledger.submit({"idempotency_key": "contract-pause-0001", "command": "pause", "target": "demo/REQ-001",
                       "origin": "web", "params": {}, "precondition": {"state": "running"}},
                      {"pause": lambda _target, _params: {"messages": []}}, lambda _target: {"state": "running"})
        quota = [{"profile": "codex-work", "exhausted_until": "2026-10-20T15:00:00Z", "observed_at": "2026-10-20T10:00:00Z"}]
        with patch("bt_subscriptions.summary", return_value=quota):
            page = remote.EventsPage.model_validate_json(self.get("/api/remote/v1/events?limit=100"))
        kinds = {event.type for event in page.events}
        self.assertTrue({"attempt.failed", "plan.waiting", "round.waiting", "quota.exhausted", "command.updated"} <= kinds,
                        kinds)
        command = next(event for event in page.events if event.type == "command.updated")
        self.assertNotEqual(command.occurred_at, "1970-01-01T00:00:00Z")

    def test_real_quotas_route_validates(self):
        import bt_quota_live

        reset = dt.datetime(2026, 10, 20, 15, tzinfo=dt.UTC).timestamp()
        windows = {"five_hour": {"used_percent": 27, "resets_at": reset, "window_minutes": 300},
                   "seven_day": {"used_percent": 64.5, "resets_at": None}}
        with patch("bt_subscriptions.read_codex", return_value=windows), \
                patch("bt_subscriptions.read_claude", side_effect=RuntimeError("expired")):
            rows = [bt_quota_live.read_row("codex-work", "codex"), bt_quota_live.read_row("claude-work", "claude")]
        with patch("bt_quota_live.read_all_live", return_value=rows):
            quotas = remote.QuotasResponse.model_validate_json(self.get("/api/remote/v1/quotas"))
        self.assertEqual([window.window for window in quotas.accounts[0].windows], ["five_hour", "seven_day"])
        self.assertEqual((quotas.accounts[1].status, quotas.accounts[1].windows), ("RuntimeError", []))

    def test_real_routes_route_validates_with_one_availability_rule(self):
        rows = (candidate("route-ok"), candidate("route-unknown", "unknown"))
        with patch("bt_route_pins.candidates_for", return_value=rows):
            routes = remote.RoutesResponse.model_validate_json(
                self.get("/api/remote/v1/routes?target=demo/REQ-001&task=T1")).routes
        self.assertEqual([(route.route_id, route.available) for route in routes],
                         [("route-ok", True), ("route-unknown", False)])

    def test_real_failure_review_and_command_history_validate(self):
        review = remote.FailureReview.model_validate_json(
            self.get("/api/remote/v1/attempts/A-failed/review?target=demo/REQ-001"))
        self.assertEqual((review.attempt_id, review.diff.files), ("A-failed", []))
        commands.Ledger().submit({"idempotency_key": "contract-history-01", "command": "pause", "target": "demo/REQ-001",
                                  "origin": "telegram", "params": {}, "precondition": {"state": "running"}},
                                 {"pause": lambda _target, _params: {"messages": []}}, lambda _target: {"state": "running"})
        history = remote.CommandHistoryResponse.model_validate_json(self.get("/api/remote/v1/commands?limit=10"))
        self.assertEqual(history.commands[0].origin, "telegram")


class DurableRunProducers(unittest.TestCase):
    """A durable run (REQ-030 M7) through the real snapshot and events routes, from the projection a REAL lab run
    produced: real git, DBOS on SQLite, the engine process, the fake provider through the real driver."""

    def setUp(self):
        from durable_support import SYSTEMD, Lab
        self.lab = Lab(backend="systemd" if SYSTEMD else "pgroup")
        self.addCleanup(self.lab.cleanup)
        env = patch.dict(os.environ, {"FLOW_GATEWAY_KEY": KEY})
        env.start()
        self.addCleanup(env.stop)
        producing = remote_fixture_root.producing(self.lab.bitacora)
        producing.__enter__()
        self.addCleanup(producing.__exit__, None, None, None)

    def get(self, path: str):
        handler = Handler(path)
        bt_remote_api.route_get(handler)
        self.assertEqual(handler.status, 200, handler.body)
        return handler.body

    def test_snapshot_and_events_of_a_real_durable_run_validate(self):
        import bt_durable_panel
        from bt_contracts.execution import RunRef
        from bt_durable.settings import Settings
        from durable_support import engine_client, task, wait_until

        data = self.lab.freeze([task("T1", scenario="neverfix"), task("T2"), task("T3", after=["T2"])])
        self.lab.own(data)
        run = RunRef.model_validate(data)
        settings = Settings(max_parallel=2, poll_seconds=0.5, run_poll_seconds=5, owner_wait_seconds=5)
        _, client = engine_client(self, self.lab)
        client.start(run, settings.model_copy(update={"budget": settings.budget.model_copy(
            update={"max_attempts": 1})}))
        self.addCleanup(client.cancel, run)

        def asked():
            doc = bt_durable_panel.read(self.lab.rdir)
            return doc if doc and doc["decisions"] else None
        doc = wait_until(asked, 180, interval=0.5, what="a durable decision in the projection")
        snapshot = remote.RemoteSnapshot.model_validate_json(self.get("/api/remote/v1/snapshot"))
        shown = next(r for r in snapshot.runs if r.req == "REQ-900")
        states = {t.id: t.state for t in shown.tasks}
        self.assertEqual((shown.state, shown.revision), ("running", doc["status_seq"]))
        self.assertEqual(states["T1"], "rejected")                        # needs a decision (the M1 "recovering")
        self.assertEqual(states["T2"], "ready")                           # queued: T1 holds the shared out.txt
        self.assertEqual(states["T3"], "pending")                         # its dependency is not done
        self.assertTrue(all(isinstance(t.revision, int) for t in shown.tasks))
        t1 = next(t for t in shown.tasks if t.id == "T1")
        self.assertEqual((t1.review_attempt.state, t1.review_attempt.verdict), ("rejected", "FAIL"))
        decision = next(d for d in snapshot.decision_requests if d.req == "REQ-900")
        self.assertEqual((decision.id, decision.task), ("T1:d1@k1", "T1"))
        self.assertEqual([o.id for o in decision.options], ["retry", "retry_with_note", "retry_other_route", "stop"])
        page = remote.EventsPage.model_validate_json(self.get("/api/remote/v1/events?limit=100"))
        self.assertIn("attempt.failed", {event.type for event in page.events})


class GatewayProducers(unittest.TestCase):
    def runtime(self, laptop=None):
        from config import GatewayConfig

        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        runtime = gateway_app.GatewayRuntime(
            GatewayConfig("http://127.0.0.1:18765", KEY, "token", "chat", Path(temp.name) / "gateway.sqlite"),
            laptop=laptop, sender=lambda _message: None)
        self.addCleanup(runtime.outbox._db.close)
        return runtime

    def test_gateway_relays_every_contract_command_as_a_ledger_body_the_laptop_accepts(self):
        for item in fixture("commands"):
            with self.subTest(type=item["type"]):
                body = gateway_app._ledger_command(item)
                remote.LedgerCommand.model_validate_json(json.dumps(body))
                self.assertIsNone(commands.validate(body))

    def test_telegram_relay_emits_a_valid_ledger_body(self):
        sent = []
        laptop = SimpleNamespace(command=lambda body: (sent.append(body), (200, {"status": "OK"}))[1])
        runtime = self.runtime(laptop)
        request = {"schemaVersion": 1, "idempotencyKey": "t" * 32, "type": "pause",
                   "target": {"kind": "run", "project": "lotm", "req": "REQ-027"}, "precondition": {"state": "running"}}
        remote.RemoteCommand.model_validate_json(json.dumps(request))
        self.assertEqual(runtime.submit_telegram_command(request)["status"], "OK")
        remote.LedgerCommand.model_validate_json(json.dumps(sent[0]))

    def test_gateway_snapshot_and_stream_frames_validate_on_the_contract_path(self):
        from auth import SESSION_COOKIE, OAuthConfig, SessionStore
        from server import create_server

        runtime = self.runtime()
        runtime.hub.update_snapshot(fixture("snapshot"))
        remote.GatewaySnapshot.model_validate_json(json.dumps(runtime.hub.read_snapshot_response()))
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        secret = "contract-session-secret-with-more-than-32-bytes"
        db = str(Path(temp.name) / "sessions.sqlite")
        server = create_server(OAuthConfig(client_id="i", client_secret="s", session_secret=secret,
                                           frontend_origin="https://flow.example.test", database_path=db),
                               ("127.0.0.1", 0), hub=runtime.hub, runtime=runtime)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        self.addCleanup(runtime.hub.close)
        cookie = f"{SESSION_COOKIE}={SessionStore(db, secret).create_session('dav033')}"
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        self.addCleanup(connection.close)
        connection.request("GET", remote.STREAM_PATH, headers={"Cookie": cookie, "Last-Event-ID": "stale:9"})
        response = connection.getresponse()
        self.assertEqual(response.status, 200)
        threading.Timer(0.2, lambda: runtime.hub.publish(fixture("events")[0])).start()
        frames = []
        block: dict[str, str] = {}
        while len(frames) < 2:
            line = response.fp.readline().decode().rstrip("\n")
            if not line:
                if "event" in block:
                    frames.append(block)
                block = {}
                continue
            if not line.startswith(":"):
                key, _, value = line.partition(": ")
                block[key] = value
        self.assertEqual([frame["event"] for frame in frames], [remote.STREAM_RESYNC, remote.STREAM_EVENT])
        remote.GatewaySnapshot.model_validate_json(frames[0]["data"])
        remote.RemoteEvent.model_validate_json(frames[1]["data"])
        self.assertRegex(frames[1]["id"], r"^[0-9a-f]+:[0-9]+$")


class ContractRefusesTheAuditedDialects(unittest.TestCase):
    """Each audited mismatch, expressed as data the contract now refuses."""

    def refused(self, model, value):
        with self.assertRaises(ValidationError):
            model.model_validate_json(json.dumps(value))

    def test_snake_case_and_page_only_fields_are_refused(self):
        snapshot = fixture("snapshot")
        run = dict(snapshot["runs"][0])
        run["req_id"] = run.pop("req")                                                    # F11 dialect
        self.refused(remote.RemoteSnapshot, {**snapshot, "runs": [run]})
        decision = {**snapshot["decisionRequests"][0], "diagnosis_html": "<div></div>"}   # HTML leak
        self.refused(remote.RemoteSnapshot, {**snapshot, "decisionRequests": [decision]})

    def test_quota_windows_object_and_numeric_times_are_refused(self):                    # F41
        account = {**fixture("quotas")["accounts"][0], "windows": {"five_hour": {"used_percent": 27}}}
        self.refused(remote.QuotasResponse, {"accounts": [account], "checkedAt": "2026-10-19T12:00:00Z"})
        self.refused(remote.QuotasResponse, {"accounts": [{**account, "windows": [], "observedAt": 1792411200}],
                                             "checkedAt": "2026-10-19T12:00:00Z"})

    def test_reopen_without_task_and_overlong_keys_are_refused(self):                     # F21, F17
        reopen = next(item for item in fixture("commands") if item["type"] == "reopen")
        self.refused(remote.RemoteCommand, {**reopen, "target": {"kind": "run", "project": "demo", "req": "REQ-001"}})
        self.refused(remote.RemoteCommand, {**reopen, "idempotencyKey": "k" * 121})
        self.refused(remote.LedgerCommand, {"idempotency_key": "k" * 121, "command": "pause", "target": "demo/REQ-001",
                                            "origin": "web", "params": {}, "precondition": {"state": "running"}})


if __name__ == "__main__":
    unittest.main()
