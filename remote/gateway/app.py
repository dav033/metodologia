"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Mapping

from config import GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from stream import StreamHub
from notifications import NotificationOutbox, TelegramSender, event_timestamp, notification_for_event
<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
<<<<<<< a82720ecf6dc19a4b38cdab385315351a90c5c52
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| 7bbf41f3848b323c12af604ffeb9255ba1e71e8e
<<<<<<< fdc224e41c20baaf18251239055e505699e9db6a
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| abc942f14b9a0fa0d84e36f8efa479328584534c
<<<<<<< f05f8fd659ac343b89d326952a27e078aab647c1
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| bb8d45c1c426152ebc0ce48c79c6b29d739fa631
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| 9c190842d7f30c6178e9794e196264c85b92bba2
from notifications import NotificationOutbox, TelegramSender, notification_for_event
<<<<<<< 6048a7cab2664fbc1ed484e52a4a784570976dce
from upstream import LaptopClient, UpstreamError, UpstreamTimeout
||||||| a86df111448409a7063f992bae2d9ccdfe498fa4
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
from commands import COMMAND_TYPES
=======
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> 4273ff48ab3b1b2c2ef13b15ffc7e756d2fef067
=======
from notifications import NotificationOutbox, TelegramSender, notification_for_event
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> 70de5f62178587b71e15d40677732fb4dc3cae8c
=======
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
=======
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> d58d5211dfbc3de3567c96dfad21cbe074ff5303
=======
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> 2aa3a1885b93515f6a7eaa307a9fb85ab1f1392a
=======
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
SUPPORTED_COMMANDS = frozenset({"pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
                                "launch", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note"})
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})
TELEGRAM_REQ_ID = re.compile(r"REQ-[0-9]{3,6}\Z")


def _ledger_command(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate a browser command into the laptop ledger's versioned request shape."""
    command = payload.get("type")
    target = payload.get("target")
    if command not in SUPPORTED_COMMANDS or not isinstance(target, dict):
        return {}
    project, req = target.get("project"), target.get("req")
    if not isinstance(project, str) or not isinstance(req, str):
<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
        return {}
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
        return None
    command = request.get("type")
    if not isinstance(command, str) or command not in COMMAND_TYPES:
        return None
    field_map = {"reason": "reason", "route": "route", "brief": "brief", "answer": "answers",
<<<<<<< a82720ecf6dc19a4b38cdab385315351a90c5c52
||||||| 7bbf41f3848b323c12af604ffeb9255ba1e71e8e
<<<<<<< fdc224e41c20baaf18251239055e505699e9db6a
||||||| abc942f14b9a0fa0d84e36f8efa479328584534c
<<<<<<< f05f8fd659ac343b89d326952a27e078aab647c1
||||||| bb8d45c1c426152ebc0ce48c79c6b29d739fa631
<<<<<<< e6088af660026d2e861b496d907f514eef10722f
||||||| 9c190842d7f30c6178e9794e196264c85b92bba2
<<<<<<< 6048a7cab2664fbc1ed484e52a4a784570976dce
||||||| a86df111448409a7063f992bae2d9ccdfe498fa4
<<<<<<< a474fe7810a1d2a36f9a5f0474a49e4d4dadd236
=======
                 "requestId": "request_id", "answers": "answers", "option": "option",
>>>>>>> 4273ff48ab3b1b2c2ef13b15ffc7e756d2fef067
=======
                 "requestId": "request_id", "answers": "answers", "option": "option",
>>>>>>> 70de5f62178587b71e15d40677732fb4dc3cae8c
=======
                 "requestId": "request_id", "answers": "answers", "option": "option",
>>>>>>> 7d0156fc3acf8afdbcdf78e19160f8fd15f17368
=======
                 "requestId": "request_id", "answers": "answers", "option": "option",
>>>>>>> d58d5211dfbc3de3567c96dfad21cbe074ff5303
=======
                 "requestId": "request_id", "answers": "answers", "option": "option",
>>>>>>> 2aa3a1885b93515f6a7eaa307a9fb85ab1f1392a
                 "note": "note", "attemptId": "attempt", "taskId": "task", "round": "round",
                 "field": "field", "value": "value"}
=======
        return None
    command = request.get("type")
    if not isinstance(command, str) or command not in COMMAND_TYPES:
        return None
    field_map = {"reason": "reason", "route": "route", "brief": "brief", "answer": "answers",
                 "requestId": "request_id", "answers": "answers", "option": "option",
                 "note": "note", "attemptId": "attempt", "taskId": "task", "round": "round",
                 "field": "field", "value": "value"}
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
    params: dict[str, Any] = {}
<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
    if command == "cancel-attempt" and isinstance(target.get("attemptId"), str):
        params["attempt"] = target["attemptId"]
    if command in {"reopen", "retry", "edit-brief"} and isinstance(target.get("taskId"), str):
        params["task"] = target["taskId"]
    if command == "retry":
        route = payload.get("route")
        if isinstance(route, str):
            params["route"] = route
        elif isinstance(route, dict):
            route_id = route.get("id", route.get("route_id"))
            if isinstance(route_id, str):
                params["route"] = route_id
            for key in ("model", "account"):
                if isinstance(route.get(key), str):
                    params[key] = route[key]
    if command == "answer-round":
        round_id = target.get("roundId")
        digits = "".join(char for char in round_id if char.isdigit()) if isinstance(round_id, str) else ""
        if digits:
            params["round"] = int(digits)
        elif isinstance(payload.get("round"), int):
            params["round"] = payload["round"]
        params["answers"] = payload.get("answer", payload.get("answers"))
    if command == "edit-brief":
        params.update({"field": payload.get("field", "brief"), "value": payload.get("value", payload.get("brief"))})
    if command == "note":
        params["note"] = payload.get("note")
    if "reason" in payload:
        params["reason"] = payload["reason"]
    request: dict[str, Any] = {"idempotency_key": payload.get("idempotencyKey"), "command": command,
                               "target": f"{project}/{req}", "origin": "web", "params": params,
                               "precondition": payload.get("precondition")}
    confirmation = payload.get("confirmation")
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
    for source, destination in field_map.items():
        if source in request:
            params[destination] = request[source]
    if isinstance(target.get("taskId"), str):
        params.setdefault("task", target["taskId"])
    if isinstance(target.get("attemptId"), str):
        params.setdefault("attempt", target["attemptId"])
    route = request.get("route")
    if isinstance(route, dict):
        # Laptop recovery dispatch accepts selectors, while the web contract carries a route object.
        params["route"] = (route.get("id") or route.get("routeId") or route.get("route_id")
                           or route.get("route"))
        for selector in ("model", "account"):
            if selector in route:
                params[selector] = route[selector]
    confirmation = request.get("confirmation")
    ledger: dict[str, Any] = {
        "idempotency_key": request.get("idempotencyKey"), "command": command,
        "target": f"{project}/{req}", "origin": "web", "params": params,
        "precondition": request.get("precondition"),
    }
=======
    for source, destination in field_map.items():
        if source in request:
            params[destination] = request[source]
    if "request_id" in request:
        params["request_id"] = request["request_id"]
    if isinstance(target.get("taskId"), str):
        params.setdefault("task", target["taskId"])
    if isinstance(target.get("attemptId"), str):
        params.setdefault("attempt", target["attemptId"])
    route = request.get("route")
    if isinstance(route, dict):
        # Laptop recovery dispatch accepts selectors, while the web contract carries a route object.
        params["route"] = (route.get("id") or route.get("routeId") or route.get("route_id")
                           or route.get("route"))
        for selector in ("model", "account"):
            if selector in route:
                params[selector] = route[selector]
    confirmation = request.get("confirmation")
    ledger: dict[str, Any] = {
        "idempotency_key": request.get("idempotencyKey"), "command": command,
        "target": f"{project}/{req}", "origin": "web", "params": params,
        "precondition": request.get("precondition"),
    }
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
    if isinstance(confirmation, dict):
        request["confirmation"] = {"challenge_id": confirmation.get("challengeId"),
                                   "typed_req": confirmation.get("typedReq")}
    return request


class GatewayRuntime:
    def __init__(self, config: GatewayConfig, laptop: Any | None = None, sender: Any | None = None):
        self.config = config
        self.laptop = laptop or LaptopClient(config.laptop_origin, config.gateway_key, config.request_timeout)
        self.sender = sender or TelegramSender(
            config.telegram_bot_token, config.telegram_chat_id, config.request_timeout
        )
        self.outbox = NotificationOutbox(str(config.database_path))
        self.liveness = LivenessMonitor()
        self.hub = StreamHub()
        self.event_cursor = ""
        self.snapshot_cache: dict[str, Any] | None = None
        self.offline_generation = self.outbox.state_value("laptop_outage_generation")
        self.offline_alerted_generation = self.outbox.state_value("laptop_outage_alerted")
        self.has_cached_active_run = bool(self.outbox.state_value("laptop_has_cached_active_run"))
        outage_started_at = self.outbox.state_value("laptop_outage_started_at")
        if outage_started_at:
            # LivenessMonitor uses monotonic time in-process. Reconstruct its clock from the
            # persisted wall-clock outage start so a gateway restart does not reset the alert.
            self.liveness.status = LaptopStatus.OFFLINE
            self.liveness.consecutive_failures = self.liveness.failures_before_offline
            elapsed = max(0.0, time.time() - outage_started_at)
            self.liveness.offline_since = time.monotonic() - elapsed

    def submit_command(self, payload: dict[str, Any]) -> dict[str, Any]:
        status, result = self.relay_command(payload)
        return {**result, "http_status": status}

    def issue_challenge(self, payload: dict[str, Any]) -> dict[str, Any]:
        status, result = self.relay_challenge(payload)
        return {**result, "http_status": status}

    def relay_command(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        key = payload.get("idempotencyKey") if isinstance(payload, dict) else None
        if self.liveness.status is LaptopStatus.OFFLINE:
            return 503, {"code": "LAPTOP_OFFLINE", "idempotency_key": key}
        request = _ledger_command(payload) if isinstance(payload, dict) else {}
        if not request or not isinstance(key, str) or len(key) < 16:
            return 400, {"code": "INVALID_COMMAND"}
        confirmation = payload.get("confirmation")
        if payload.get("type") in CHALLENGED_COMMANDS and (
                not isinstance(confirmation, dict)
                or not isinstance(confirmation.get("challengeId"), str)
                or not confirmation["challengeId"]
                or confirmation.get("typedReq") != payload.get("target", {}).get("req")):
            return 400, {"code": "CONFIRMATION_REQUIRED", "idempotency_key": key}
        try:
            status, result = self.laptop.command(request)
        except UpstreamTimeout:
            return 503, {"code": "UNKNOWN_OUTCOME", "idempotency_key": key}
        except UpstreamError:
            return 503, {"code": "LAPTOP_UNAVAILABLE"}
        if result.get("code") == "CONFIRMATION_REQUIRED":
            status = 400
        if result.get("code") == "UNKNOWN_OUTCOME" and "idempotency_key" not in result:
            result = {**result, "idempotency_key": key}
        return status, result

    def relay_challenge(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        target = payload.get("target") if isinstance(payload, dict) else None
        typed_req = payload.get("typedReq") if isinstance(payload, dict) else None
        if isinstance(target, dict):
            project, req = target.get("project"), target.get("req")
            target = f"{project}/{req}" if isinstance(project, str) and isinstance(req, str) else None
        if not isinstance(target, str) or not isinstance(typed_req, str):
            return 400, {"code": "INVALID_CHALLENGE"}
        try:
            return self.laptop.challenge({"target": target, "typedReq": typed_req})
        except UpstreamError:
            return 503, {"code": "LAPTOP_UNAVAILABLE"}

    def poll_once(self) -> None:
        try:
            health = self.laptop.health()
            if health.get("status") != "ok":
                raise UpstreamError("laptop health check was not successful")
        except UpstreamError:
            transition = self.liveness.record_failure()
            if transition:
                self.hub.set_online(False)
            if transition and transition.current is LaptopStatus.OFFLINE:
                self.offline_generation = self.outbox.next_sequence("laptop_outage_generation")
                self.outbox.set_state_value("laptop_outage_started_at", int(time.time()))
        else:
            transition = self.liveness.record_success()
            self.hub.set_online(True)
            if transition and transition.current is LaptopStatus.ONLINE:
                self.outbox.set_state_value("laptop_outage_started_at", 0)
            self._refresh_active_run_cache()
            self._poll_events()
        if self.liveness.status is LaptopStatus.OFFLINE:
            self._notify_long_offline_with_active_run()
        self.outbox.deliver_due(self.sender)

    def submit_telegram_command(self, request: Any) -> dict[str, Any]:
        """Relay only owner-safe run pause/resume commands to the laptop ledger."""
        if not isinstance(request, Mapping) or request.get("schemaVersion") != 1:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "stored": False}
        key = request.get("idempotencyKey")
        command = request.get("type")
        target = request.get("target")
        precondition = request.get("precondition")
        if (isinstance(request.get("schemaVersion"), bool)
                or set(request) != {"schemaVersion", "idempotencyKey", "type", "target", "precondition"}
                or not isinstance(key, str) or not 16 <= len(key) <= 128
                or not re.fullmatch(r"[A-Za-z0-9._:-]+", key)
                or not isinstance(command, str) or command not in {"pause", "resume"}
                or not isinstance(target, Mapping)
                or set(target) != {"kind", "project", "req"} or target.get("kind") != "run"
                or not isinstance(target.get("project"), str) or not 1 <= len(target["project"]) <= 80
                or not isinstance(target.get("req"), str) or not TELEGRAM_REQ_ID.fullmatch(target["req"])
                or not isinstance(precondition, Mapping)
                or set(precondition) != {"state"}
                or not isinstance(precondition.get("state"), str)
                or precondition.get("state") != ("running" if command == "pause" else "paused")):
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "stored": False}
        ledger_request = {
            "idempotency_key": key,
            "command": command,
            "target": f"{target['project']}/{target['req']}",
            "origin": "telegram",
            "params": {},
            "precondition": {"state": precondition["state"]},
        }
        return self._submit_ledger_command(ledger_request)

    def _submit_ledger_command(self, ledger_request: dict[str, Any]) -> dict[str, Any]:
        if self.liveness.status is LaptopStatus.OFFLINE:
            return {"status": "REJECTED", "code": "LAPTOP_OFFLINE",
                    "idempotency_key": ledger_request.get("idempotency_key")}
        try:
            command = getattr(self.laptop, "command", None)
            response = (command(ledger_request) if callable(command)
                        else self.laptop.post_json("/api/remote/v1/commands", ledger_request))
        except UpstreamTimeout:
            return {"status": "UNKNOWN", "code": "UNKNOWN_OUTCOME",
                    "idempotency_key": ledger_request.get("idempotency_key")}
        except UpstreamError:
            self.liveness.record_failure()
            if self.liveness.status is LaptopStatus.OFFLINE:
                return {"status": "REJECTED", "code": "LAPTOP_OFFLINE",
                        "idempotency_key": ledger_request.get("idempotency_key")}
            return {"status": "FAILED", "code": "LAPTOP_UNAVAILABLE",
                    "idempotency_key": ledger_request.get("idempotency_key")}
        if isinstance(response, tuple) and len(response) == 2:
            status, result = response
        else:
            status, result = 200, response
        if not isinstance(result, dict):
            return {"status": "FAILED", "code": "INVALID_UPSTREAM_RESPONSE"}
        if result.get("code") == "UNKNOWN_OUTCOME":
            result["idempotency_key"] = ledger_request.get("idempotency_key")
        result.setdefault("http_status", status)
        return result

    def _notify_long_offline_with_active_run(self) -> None:
        offline_since = self.liveness.offline_since
        if offline_since is None or time.monotonic() - offline_since < OFFLINE_ALERT_DELAY_SECONDS:
            return
        if self.offline_generation <= self.offline_alerted_generation:
            return
        if not self.has_cached_active_run:
            return
        key = f"liveness:laptop:offline:{self.offline_generation}"
        self.outbox.enqueue(key, "El portátil lleva más de 15 minutos desconectado mientras hay una ejecución activa.")
        self.outbox.set_state_value("laptop_outage_alerted", self.offline_generation)
        self.offline_alerted_generation = self.offline_generation

    def _refresh_active_run_cache(self) -> None:
        try:
            snapshot = self.laptop.snapshot()
        except UpstreamError:
            logger.warning("Laptop snapshot unavailable; retaining cached active-run state")
            return
        runs = snapshot.get("runs")
        if not isinstance(runs, list):
            logger.warning("Laptop snapshot response was invalid; retaining cached active-run state")
            return
<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
<<<<<<< a82720ecf6dc19a4b38cdab385315351a90c5c52
||||||| 7bbf41f3848b323c12af604ffeb9255ba1e71e8e
<<<<<<< fdc224e41c20baaf18251239055e505699e9db6a
        self.hub.update_snapshot(snapshot)
||||||| abc942f14b9a0fa0d84e36f8efa479328584534c
=======
        self.snapshot_cache = snapshot
>>>>>>> d58d5211dfbc3de3567c96dfad21cbe074ff5303
=======
        self.snapshot_cache = snapshot
>>>>>>> 2aa3a1885b93515f6a7eaa307a9fb85ab1f1392a
=======
        self.snapshot_cache = snapshot
>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
        self.hub.update_snapshot(snapshot)
        has_active_run = any(
            isinstance(run, dict) and (run.get("active") is True or run.get("status") in ACTIVE_RUN_STATES)
            for run in runs
        )
        self.has_cached_active_run = has_active_run
        self.outbox.set_state_value("laptop_has_cached_active_run", int(has_active_run))

<<<<<<< bfa41a71c3071e38a990cad13eb732a5ba9e52a5
||||||| 2bedcb11d2d5783266fb3a9f9602d8bf82e99a3f
<<<<<<< a82720ecf6dc19a4b38cdab385315351a90c5c52
||||||| 7bbf41f3848b323c12af604ffeb9255ba1e71e8e
    def web_snapshot(self) -> dict[str, Any] | None:
        """Return the last laptop snapshot with gateway liveness for authenticated web clients."""
        snapshot = self.snapshot_cache
        if snapshot is None and self.liveness.status is LaptopStatus.ONLINE:
            try:
                snapshot = self.laptop.snapshot()
            except UpstreamError:
                return None
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("runs"), list):
                return None
            self.snapshot_cache = snapshot
        if snapshot is None:
            return None
        result = dict(snapshot)
        result.setdefault("schemaVersion", 1)
        result.setdefault("plans", [])
        result["laptop"] = {"online": self.liveness.status is LaptopStatus.ONLINE}
        return result

    def read_model(self, path: str) -> dict[str, Any]:
        """Relay an authenticated gateway read route to the laptop's v1 API."""
        return self.laptop.read_model(path)

=======
    def web_snapshot(self) -> dict[str, Any] | None:
        """Return the last laptop snapshot with gateway liveness for authenticated web clients."""
        snapshot = self.snapshot_cache
        if snapshot is None and self.liveness.status is LaptopStatus.ONLINE:
            try:
                snapshot = self.laptop.snapshot()
            except UpstreamError:
                return None
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("runs"), list):
                return None
            self.snapshot_cache = snapshot
        if snapshot is None:
            return None
        result = dict(snapshot)
        result.setdefault("schemaVersion", 1)
        result.setdefault("plans", [])
        result["laptop"] = {"online": self.liveness.status is LaptopStatus.ONLINE}
        return result

>>>>>>> 2aa3a1885b93515f6a7eaa307a9fb85ab1f1392a
=======
    def web_snapshot(self) -> dict[str, Any] | None:
        """Return the last laptop snapshot with gateway liveness for authenticated web clients."""
        snapshot = self.snapshot_cache
        if snapshot is None and self.liveness.status is LaptopStatus.ONLINE:
            try:
                snapshot = self.laptop.snapshot()
            except UpstreamError:
                return None
            if not isinstance(snapshot, dict) or not isinstance(snapshot.get("runs"), list):
                return None
            self.snapshot_cache = snapshot
        if snapshot is None:
            return None
        result = dict(snapshot)
        result.setdefault("schemaVersion", 1)
        result.setdefault("plans", [])
        result["laptop"] = {"online": self.liveness.status is LaptopStatus.ONLINE}
        return result

>>>>>>> 3023898c06ce29d14d9ab50f11757fe675920e9d
    def _poll_events(self) -> None:
        try:
            result = self.laptop.events(self.event_cursor)
        except UpstreamError:
            logger.warning("Laptop event feed unavailable")
            return
        events = result.get("events")
        if not isinstance(events, list):
            logger.warning("Laptop event feed response was invalid")
            return
        for event in events:
            if not isinstance(event, dict):
                continue
            self.hub.publish(event)
            notification = notification_for_event(event)
            if notification:
                self.outbox.enqueue(*notification, created_at=event_timestamp(event))
        next_cursor = result.get("nextCursor")
        if isinstance(next_cursor, str):
            self.event_cursor = next_cursor

    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            self.poll_once()
            time.sleep(max(0.0, self.config.probe_interval - (time.monotonic() - started)))


def create_runtime(config: GatewayConfig, laptop: Any | None = None, sender: Any | None = None) -> GatewayRuntime:
    """Build the same runtime used by the production command and integration tests."""
    return GatewayRuntime(config, laptop=laptop, sender=sender)
