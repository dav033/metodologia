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
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})


def _ledger_command(request: Any) -> dict[str, Any] | None:
    """Translate the public v1 command envelope into the laptop ledger contract."""
    if not isinstance(request, dict) or request.get("schemaVersion") != 1:
        return None
    target = request.get("target")
    if not isinstance(target, dict):
        return None
    project, req = target.get("project"), target.get("req")
    if not isinstance(project, str) or not isinstance(req, str):
        return None
    command = request.get("type")
    if not isinstance(command, str):
        return None
    field_map = {"reason": "reason", "route": "route", "brief": "brief", "answer": "answers",
                 "note": "note", "attemptId": "attempt", "taskId": "task", "round": "round",
                 "field": "field", "value": "value"}
    params: dict[str, Any] = {}
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
    if isinstance(confirmation, dict):
        ledger["confirmation"] = {"challenge_id": confirmation.get("challengeId"),
                                  "typed_req": confirmation.get("typedReq")}
    return ledger


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

    def submit_command(self, request: Any) -> dict[str, Any]:
        ledger_request = _ledger_command(request)
        if ledger_request is None:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "stored": False}
        idempotency_key = ledger_request.get("idempotency_key")
        if ledger_request["command"] in CHALLENGED_COMMANDS:
            confirmation = ledger_request.get("confirmation")
            target = request.get("target") if isinstance(request, dict) else None
            req = target.get("req") if isinstance(target, dict) else None
            if (not isinstance(confirmation, dict)
                    or not isinstance(confirmation.get("challenge_id"), str)
                    or not confirmation["challenge_id"].strip()
                    or confirmation.get("typed_req") != req):
                return {"status": "REJECTED", "code": "CONFIRMATION_REQUIRED", "stored": False}
        if self.liveness.status is LaptopStatus.OFFLINE:
            return {"status": "REJECTED", "code": "LAPTOP_OFFLINE", "idempotency_key": idempotency_key}
        try:
            result = self.laptop.post_json("/api/remote/v1/commands", ledger_request)
        except UpstreamTimeout:
            return {"status": "UNKNOWN", "code": "UNKNOWN_OUTCOME", "idempotency_key": idempotency_key}
        except UpstreamError:
            self.liveness.record_failure()
            if self.liveness.status is LaptopStatus.OFFLINE:
                return {"status": "REJECTED", "code": "LAPTOP_OFFLINE", "idempotency_key": idempotency_key}
            return {"status": "FAILED", "code": "LAPTOP_UNAVAILABLE", "idempotency_key": idempotency_key}
        if result.get("code") == "UNKNOWN_OUTCOME":
            result["idempotency_key"] = idempotency_key
        return result

    def issue_challenge(self, request: Any) -> dict[str, Any]:
        if not isinstance(request, dict):
            return {"code": "INVALID_CHALLENGE"}
        target = request.get("target")
        if isinstance(target, dict):
            project, req = target.get("project"), target.get("req")
            target = f"{project}/{req}" if isinstance(project, str) and isinstance(req, str) else None
        typed_req = request.get("typedReq")
        if not isinstance(target, str) or not isinstance(typed_req, str):
            return {"code": "INVALID_CHALLENGE"}
        if self.liveness.status is LaptopStatus.OFFLINE:
            return {"code": "LAPTOP_OFFLINE"}
        try:
            return self.laptop.post_json("/api/remote/v1/challenges", {"target": target, "typedReq": typed_req})
        except UpstreamTimeout:
            return {"code": "UNKNOWN_OUTCOME"}
        except UpstreamError:
            self.liveness.record_failure()
            return {"code": "LAPTOP_OFFLINE" if self.liveness.status is LaptopStatus.OFFLINE
                    else "LAPTOP_UNAVAILABLE"}

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
