import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from app import GatewayRuntime, _ledger_command
from config import GatewayConfig
from liveness import LaptopStatus
from upstream import UpstreamTimeout


def config(path: Path) -> GatewayConfig:
    return GatewayConfig("http://127.0.0.1:18765", "test-key", "test-token", "test-chat", path)


<<<<<<< 8215116a0d8672bc33521ae7b5c78c687c2dc2af
def command(**changes):
    request = {
        "schemaVersion": 1,
        "idempotencyKey": "retry-key-00000001",
        "type": "retry",
        "target": {"kind": "task", "project": "demo", "req": "REQ-027", "taskId": "T4"},
        "precondition": {"state": "rejected", "revision": 3},
        "route": {"id": "route:abc", "model": "sonnet", "account": "work"},
    }
    return {**request, **changes}
||||||| a4b1272680674f62f24a90bc81051e89eed85270
    def snapshot(self):
        return {"runs": []}

    def events(self, after):
        return {"events": [], "nextCursor": after}

    def command(self, command):
        self.command_calls.append(command)
        if self.command_error:
            raise self.command_error
        return 202, {"commandId": "command-1", "status": "accepted", "idempotencyKey": command["idempotencyKey"]}
=======
    def snapshot(self):
        return {"runs": []}

    def events(self, after):
        return {"events": [], "nextCursor": after}

    def command(self, command):
        self.command_calls.append(command)
        if self.command_error:
            raise self.command_error
        key = command.get("idempotencyKey", command.get("idempotency_key"))
        return 202, {"commandId": "command-1", "status": "accepted", "idempotencyKey": key}
>>>>>>> 810c665590f52068f21a3721a13f80c47bdb0710


class CommandRelayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.laptop = Mock()
        self.laptop.post_json.return_value = {"status": "OK", "code": None}
        self.runtime = GatewayRuntime(config(Path(self.temp.name) / "gateway.sqlite"), laptop=self.laptop,
                                      sender=lambda _: None)

    def test_destructive_command_without_challenge_is_refused_without_forwarding(self):
        result = self.runtime.submit_command(command(type="launch", route=None))
        self.assertEqual(result["code"], "CONFIRMATION_REQUIRED")
        self.laptop.post_json.assert_not_called()

    def test_offline_laptop_returns_laptop_offline_without_forwarding(self):
        self.runtime.liveness.status = LaptopStatus.OFFLINE
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "LAPTOP_OFFLINE")
        self.laptop.post_json.assert_not_called()

    def test_timeout_returns_unknown_outcome_with_idempotency_key(self):
        self.laptop.post_json.side_effect = UpstreamTimeout("late response")
        result = self.runtime.submit_command(command())
        self.assertEqual(result["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(result["idempotency_key"], "retry-key-00000001")

    def test_confirmation_challenge_is_relayed_with_string_target(self):
        self.laptop.post_json.return_value = {"challengeId": "challenge-token", "expiresIn": 120}
        result = self.runtime.issue_challenge({
            "target": {"kind": "run", "project": "demo", "req": "REQ-027"},
            "typedReq": "REQ-027",
        })
        self.assertEqual(result["challengeId"], "challenge-token")
        self.laptop.post_json.assert_called_once_with("/api/remote/v1/challenges", {
            "target": "demo/REQ-027", "typedReq": "REQ-027"})

<<<<<<< 8215116a0d8672bc33521ae7b5c78c687c2dc2af
    def test_route_object_is_translated_to_string_selectors_for_laptop_ledger(self):
        translated = _ledger_command(command())
        self.assertEqual(translated["target"], "demo/REQ-027")
        self.assertEqual(translated["params"], {
            "task": "T4", "route": "route:abc", "model": "sonnet", "account": "work"})
        self.runtime.submit_command(command())
        forwarded = self.laptop.post_json.call_args.args[1]
        self.assertEqual(forwarded["params"]["route"], "route:abc")
        self.assertEqual(forwarded["params"]["model"], "sonnet")
        self.assertEqual(forwarded["params"]["account"], "work")
||||||| a4b1272680674f62f24a90bc81051e89eed85270
    def test_destructive_command_without_challenge_is_refused(self) -> None:
        status, content_type, body = self.post(self.command("approve"))

        self.assertEqual(status, 409)
        self.assertTrue(content_type.startswith("application/problem+json"))
        self.assertEqual(body["code"], "CONFIRMATION_REQUIRED")
        self.assertEqual(self.laptop.command_calls, [])

    def test_destructive_command_with_matching_challenge_reaches_laptop(self) -> None:
        command = self.command("approve")
        command["confirmation"] = {"challengeId": "challenge-token-1234", "typedReq": "REQ-027"}

        status, _content_type, body = self.post(command)

        self.assertEqual(status, 202)
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(self.laptop.command_calls, [command])

    def test_offline_laptop_refuses_command_without_queueing(self) -> None:
        for _ in range(3):
            self.runtime.liveness.record_failure()

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 410)
        self.assertEqual(body["code"], "LAPTOP_OFFLINE")
        self.assertEqual(self.laptop.command_calls, [])

    def test_timeout_reports_unknown_outcome_with_idempotency_key(self) -> None:
        self.laptop.command_error = UpstreamTimeout("timeout")

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 503)
        self.assertEqual(body["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(body["idempotencyKey"], "command-key-000001")
=======
    def test_destructive_command_without_challenge_is_refused(self) -> None:
        status, content_type, body = self.post(self.command("approve"))

        self.assertEqual(status, 409)
        self.assertTrue(content_type.startswith("application/problem+json"))
        self.assertEqual(body["code"], "CONFIRMATION_REQUIRED")
        self.assertEqual(self.laptop.command_calls, [])

    def test_destructive_command_with_matching_challenge_reaches_laptop(self) -> None:
        command = self.command("approve")
        command["confirmation"] = {"challengeId": "challenge-token-1234", "typedReq": "REQ-027"}

        status, _content_type, body = self.post(command)

        self.assertEqual(status, 202)
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(self.laptop.command_calls, [{
            "idempotency_key": command["idempotencyKey"],
            "command": "approve",
            "target": "demo/REQ-027",
            "origin": "web",
            "params": {"confirmation": {"challenge_id": "challenge-token-1234", "typed_req": "REQ-027"}},
            "precondition": {"state": "running"},
        }])

    def test_offline_laptop_refuses_command_without_queueing(self) -> None:
        for _ in range(3):
            self.runtime.liveness.record_failure()

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 410)
        self.assertEqual(body["code"], "LAPTOP_OFFLINE")
        self.assertEqual(self.laptop.command_calls, [])

    def test_timeout_reports_unknown_outcome_with_idempotency_key(self) -> None:
        self.laptop.command_error = UpstreamTimeout("timeout")

        status, _content_type, body = self.post(self.command())

        self.assertEqual(status, 503)
        self.assertEqual(body["code"], "UNKNOWN_OUTCOME")
        self.assertEqual(body["idempotencyKey"], "command-key-000001")
>>>>>>> 810c665590f52068f21a3721a13f80c47bdb0710


if __name__ == "__main__":
    unittest.main()
