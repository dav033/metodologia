"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import time
from typing import Any

from config import GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from stream import StreamHub
from notifications import NotificationOutbox, TelegramSender, event_timestamp, notification_for_event
from upstream import LaptopClient, UpstreamError, UpstreamTimeout

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
SUPPORTED_COMMANDS = frozenset({"pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
                                "launch", "answer-round", "cancel-plan", "delete-plan", "edit-brief", "note"})
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})


def _ledger_command(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate a browser command into the laptop ledger's versioned request shape."""
    command = payload.get("type")
    target = payload.get("target")
    if command not in SUPPORTED_COMMANDS or not isinstance(target, dict):
        return {}
    project, req = target.get("project"), target.get("req")
    if not isinstance(project, str) or not isinstance(req, str):
        return {}
    params: dict[str, Any] = {}
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
        self.hub.update_snapshot(snapshot)
        has_active_run = any(
            isinstance(run, dict) and (run.get("active") is True or run.get("status") in ACTIVE_RUN_STATES)
            for run in runs
        )
        self.has_cached_active_run = has_active_run
        self.outbox.set_state_value("laptop_has_cached_active_run", int(has_active_run))

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
