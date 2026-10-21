"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Mapping

from config import GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from notifications import NotificationOutbox, TelegramSender, notification_for_event
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})
COMMAND_TYPES = frozenset({"pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
                           "launch", "answer-decision", "answer-round", "cancel-plan", "delete-plan",
                           "edit-brief", "note"})
TELEGRAM_REQ_ID = re.compile(r"^REQ-[0-9]{3,}$")


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
                 "requestId": "request_id", "answers": "answers", "option": "option",
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
        self.event_cursor = ""
        self.snapshot_cache: dict[str, Any] | None = None
        self.offline_generation = self.outbox.state_value("laptop_outage_generation")
        self.offline_alerted_generation = self.outbox.state_value("laptop_outage_alerted")
        self.has_cached_active_run = bool(self.outbox.state_value("laptop_has_cached_active_run"))

    def poll_once(self) -> None:
        try:
            health = self.laptop.health()
            if health.get("status") != "ok":
                raise UpstreamError("laptop health check was not successful")
        except UpstreamError:
            transition = self.liveness.record_failure()
            if transition and transition.current is LaptopStatus.OFFLINE:
                self.offline_generation = self.outbox.next_sequence("laptop_outage_generation")
        else:
            self.liveness.record_success()
            self._refresh_active_run_cache()
            self._poll_events()
        if self.liveness.status is LaptopStatus.OFFLINE:
            self._notify_long_offline_with_active_run()
        self.outbox.deliver_due(self.sender)

    def submit_command(self, request: Any) -> dict[str, Any]:
        ledger_request = _ledger_command(request)
        if ledger_request is None:
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "stored": False}
        command = ledger_request["command"]
        if command in CHALLENGED_COMMANDS and not isinstance(ledger_request.get("confirmation"), dict):
            return {"status": "REJECTED", "code": "CONFIRMATION_REQUIRED", "stored": False}
        return self._submit_ledger_command(ledger_request)

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
            return {"status": "REJECTED", "code": "LAPTOP_OFFLINE", "idempotency_key": ledger_request.get("idempotency_key")}
        try:
            result = self.laptop.post_json("/api/remote/v1/commands", ledger_request)
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
        code = result.get("code")
        if code == "UNKNOWN_OUTCOME":
            result["idempotency_key"] = ledger_request.get("idempotency_key")
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
        self.snapshot_cache = snapshot
        has_active_run = any(
            isinstance(run, dict) and (run.get("active") is True or run.get("status") in ACTIVE_RUN_STATES)
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

    def read_model(self, path: str) -> dict[str, Any]:
        """Relay an authenticated gateway read route to the laptop's v1 API."""
        return self.laptop.read_model(path)

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
            notification = notification_for_event(event)
            if notification:
                self.outbox.enqueue(*notification)
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
