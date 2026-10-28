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
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
SUPPORTED_COMMANDS = frozenset({"pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
                                "launch", "answer-decision", "answer-round", "cancel-plan", "delete-plan",
                                "edit-brief", "note"})
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})
TELEGRAM_REQ_ID = re.compile(r"REQ-[0-9]{3,6}\Z")
# Idempotency keys of the phone/Telegram envelope: remote/contract/command.schema.json (16..120, the ledger's cap).
IDEMPOTENCY_KEY = re.compile(r"[A-Za-z0-9._:-]{16,120}\Z")
TASK_COMMANDS = frozenset({"reopen", "retry", "edit-brief"})


def _ledger_command(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate a browser command into the laptop ledger's versioned request shape."""
    command = payload.get("type")
    target = payload.get("target")
    if command not in SUPPORTED_COMMANDS or not isinstance(target, dict):
        return {}
    project, req = target.get("project"), target.get("req")
    if not isinstance(project, str) or not isinstance(req, str):
        return {}
    # Task-scoped moves name their task and cancel names its attempt (F21): without it the laptop would compare the
    # precondition against nothing, so the command is refused here instead of being relayed.
    if command in TASK_COMMANDS and not (isinstance(target.get("taskId"), str) and target["taskId"]):
        return {}
    if command == "cancel-attempt" and not (isinstance(target.get("attemptId"), str) and target["attemptId"]):
        return {}

    params: dict[str, Any] = {}
    if command == "cancel-attempt":
        params["attempt"] = target["attemptId"]
    if command in TASK_COMMANDS:
        params["task"] = target["taskId"]
    if command == "retry":
        route = payload.get("route")
        if isinstance(route, str):
            params["route"] = route
        elif isinstance(route, dict):
            # `routeId` is the contract name; `route_id`/`id`/`route` are the alias window of phones built before it.
            route_id = route.get("routeId", route.get("route_id", route.get("id", route.get("route"))))
            if isinstance(route_id, str):
                params["route"] = route_id
            for key in ("model", "account"):
                if isinstance(route.get(key), str):
                    params[key] = route[key]
    if command == "answer-decision":
        request_id = payload.get("requestId", payload.get("request_id"))
        if isinstance(request_id, str):
            params["request_id"] = request_id
        if "option" in payload:
            params["option"] = payload["option"]
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
    if isinstance(confirmation, dict):
        request["confirmation"] = {"challenge_id": confirmation.get("challengeId"),
                                   "typed_req": confirmation.get("typedReq")}
    return request


def run_state(run: Mapping[str, Any]) -> Any:
    """A snapshot run's state: `state` is canonical; `status` is the alias window of laptops before the contract."""
    return run.get("state", run.get("status"))


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
        if not request or not isinstance(key, str) or not IDEMPOTENCY_KEY.fullmatch(key):
            return 400, {"code": "INVALID_COMMAND"}
        confirmation = payload.get("confirmation")
        if payload.get("type") in CHALLENGED_COMMANDS and (
                not isinstance(confirmation, dict)
                or not isinstance(confirmation.get("challengeId"), str)
                or not confirmation["challengeId"]
                or confirmation.get("typedReq") != payload.get("target", {}).get("req")):
            return 400, {"code": "CONFIRMATION_REQUIRED", "idempotency_key": key}
        try:
            command_method = getattr(self.laptop, "command", None)
            response = (self.laptop.command(request) if callable(command_method) else None)
            if not (isinstance(response, tuple) and len(response) == 2) and not isinstance(response, dict):
                response = self.laptop.post_json("/api/remote/v1/commands", request)
            status, result = response if isinstance(response, tuple) and len(response) == 2 else (200, response)
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
            challenge_method = getattr(self.laptop, "challenge", None)
            challenge_payload = {"target": target, "typedReq": typed_req}
            response = self.laptop.challenge(challenge_payload) if callable(challenge_method) else None
            if not (isinstance(response, tuple) and len(response) == 2) and not isinstance(response, dict):
                response = self.laptop.post_json("/api/remote/v1/challenges", challenge_payload)
            return response if isinstance(response, tuple) and len(response) == 2 else (200, response)
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

    def read_remote(self, path: str) -> dict[str, Any]:
        """Read an allow-listed laptop v1 endpoint for an authenticated phone session."""
        return self.laptop.get_json(path)

    def read_model(self, path: str) -> dict[str, Any]:
        """Relay an authenticated gateway read route to the laptop's v1 API."""
        return self.laptop.read_model(path)
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
                or not isinstance(key, str) or not IDEMPOTENCY_KEY.fullmatch(key)
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
        self.snapshot_cache = snapshot
        self.hub.update_snapshot(snapshot)
        has_active_run = any(
            isinstance(run, dict) and (run.get("active") is True or run_state(run) in ACTIVE_RUN_STATES)
            for run in runs
        )
        self.has_cached_active_run = has_active_run
        self.outbox.set_state_value("laptop_has_cached_active_run", int(has_active_run))

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

    def _poll_events(self) -> None:
        try:
            result = self.laptop.events(self.event_cursor)
        except UpstreamResponseError as exc:
            if exc.status == 400 and exc.payload.get("code") == "INVALID_CURSOR":
                self.event_cursor = ""
                logger.info("Laptop event cursor expired; restarting feed from the beginning")
                return
            logger.warning("Laptop event feed unavailable")
            return
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
            notification = notification_for_event(event, self.config.frontend_origin)
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
