"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import time
from collections import deque
from datetime import datetime, timezone
from threading import Condition
from typing import Any

from config import GatewayConfig
from liveness import LaptopStatus, LivenessMonitor
from notifications import NotificationOutbox, TelegramSender, notification_for_event, review_url
from upstream import LaptopClient, UpstreamError

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
SUPPORTED_COMMANDS = frozenset({"pause", "resume", "cancel-attempt", "reopen", "retry", "revise", "approve",
                                "launch", "answer-round", "answer-decision", "cancel-plan", "delete-plan", "edit-brief", "note"})


def _camel_key(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def _camelize(value: Any) -> Any:
    if isinstance(value, list):
        return [_camelize(item) for item in value]
    if isinstance(value, dict):
        return {_camel_key(key) if isinstance(key, str) else key: _camelize(item)
                for key, item in value.items()}
    return value


def _laptop_command(payload: dict[str, Any]) -> dict[str, Any]:
    """Translate the browser v1 command shape to the laptop ledger's accepted request shape."""
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
    if command in {"reopen", "retry", "note", "edit-brief"} and isinstance(target.get("taskId"), str):
        params["task"] = target["taskId"]
    if command == "retry" and isinstance(payload.get("route"), str):
        params["route"] = payload["route"]
    if command == "answer-round":
        round_id = target.get("roundId", "")
        digits = "".join(character for character in round_id if character.isdigit()) if isinstance(round_id, str) else ""
        if digits:
            params["round"] = int(digits)
        params["answers"] = payload.get("answer")
    if command == "answer-decision":
        params["request_id"] = payload.get("requestId")
        params["option"] = payload.get("option")
    if command in {"cancel-plan", "delete-plan"} and isinstance(payload.get("confirmation"), dict):
        params["typed_req"] = payload["confirmation"].get("typedReq")
    if command == "edit-brief":
        # The laptop edits a task's `objective` and optionally its `acceptance_criteria`.
        params["objective"] = payload.get("brief")
        if "acceptanceCriteria" in payload:
            params["acceptance_criteria"] = payload["acceptanceCriteria"]
    if command == "note":
        params["note"] = payload.get("note")
    if "reason" in payload:
        params["reason"] = payload["reason"]
    precondition = payload.get("precondition")
    confirmation = payload.get("confirmation")
    request: dict[str, Any] = {
        "idempotency_key": payload.get("idempotencyKey"),
        "command": command,
        "target": f"{project}/{req}",
        "origin": "web",
        "params": params,
        "precondition": precondition,
    }
    if isinstance(confirmation, dict):
        request["confirmation"] = {"challengeId": confirmation.get("challengeId"),
                                   "typedReq": confirmation.get("typedReq")}
    return request


def _browser_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Shape laptop event rows as the documented stable browser event contract."""
    event_type = event.get("type", event.get("kind"))
    if event_type not in {"attempt.failed", "attempt.blocked", "run.finished", "round.waiting", "plan.waiting",
                          "quota.exhausted", "attempt.stalled", "laptop.offline", "command.updated"}:
        return None
    if all(key in event for key in ("schemaVersion", "id", "cursor", "occurredAt", "target", "data", "dedupeKey")):
        return _camelize(event)
    run = event.get("run", "")
    project, separator, req = run.partition("/") if isinstance(run, str) else ("", "", "")
    if not separator:
        return None
    occurred_at = event.get("occurredAt", event.get("occurred_at"))
    identifier = event.get("id") or f"{run}/{event.get('ord', event.get('cursor', ''))}"
    cursor = event.get("cursor", event.get("ord", identifier))
    excluded = {"id", "cursor", "ord", "type", "kind", "occurredAt", "occurred_at", "run", "task", "attempt"}
    target = {"kind": "run", "project": project, "req": req}
    if isinstance(event.get("task"), str):
        target["taskId"] = event["task"]
    if isinstance(event.get("attempt"), str):
        target["attemptId"] = event["attempt"]
    return {"schemaVersion": 1, "id": str(identifier), "cursor": str(cursor), "type": event_type,
            "occurredAt": occurred_at, "target": target,
            "data": _camelize({key: value for key, value in event.items() if key not in excluded}),
            "dedupeKey": str(event.get("dedupeKey", identifier))}


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
        self.offline_generation = self.outbox.state_value("laptop_outage_generation")
        self.offline_alerted_generation = self.outbox.state_value("laptop_outage_alerted")
        self.snapshot_cache: dict[str, Any] | None = None
        self.snapshot_cached_at: str | None = None
        self._stream_condition = Condition()
        self._stream_events: deque[tuple[int, dict[str, Any]]] = deque(maxlen=5000)
        self._stream_sequence = 0
        self._seen_upstream_events: deque[str] = deque(maxlen=10000)
        self._seen_upstream_event_keys: set[str] = set()

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
            self._poll_snapshot()
            self._poll_events()
        if self.liveness.status is LaptopStatus.OFFLINE:
            self._notify_long_offline_with_active_run()
        self.outbox.deliver_due(self.sender)

    def _poll_snapshot(self) -> None:
        try:
            snapshot = self.laptop.snapshot()
        except UpstreamError:
            logger.warning("Laptop snapshot unavailable; retaining cached snapshot")
            return
        if not isinstance(snapshot, dict):
            return
        generated_at = snapshot.get("generatedAt")
        with self._stream_condition:
            self.snapshot_cache = _camelize(snapshot)
            self.snapshot_cached_at = generated_at if isinstance(generated_at, str) else datetime.now(timezone.utc).isoformat()
            self._stream_condition.notify_all()

    def cached_snapshot(self) -> dict[str, Any] | None:
        with self._stream_condition:
            if self.snapshot_cache is None:
                return None
            return {**self.snapshot_cache, "laptopStatus": self.liveness.status.value,
                    "cachedAt": self.snapshot_cached_at}

    def stream_position(self) -> int:
        with self._stream_condition:
            return self._stream_sequence

    def events_after(self, sequence: int) -> tuple[list[tuple[int, dict[str, Any]]], int, bool]:
        with self._stream_condition:
            expired = bool(self._stream_events and sequence < self._stream_events[0][0] - 1)
            events = [] if expired else [(seq, event) for seq, event in self._stream_events if seq > sequence]
            return events, self._stream_sequence, expired

    def wait_for_events(self, sequence: int, timeout: float) -> None:
        with self._stream_condition:
            if self._stream_sequence <= sequence:
                self._stream_condition.wait(timeout)

    def relay_command(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if self.liveness.status is LaptopStatus.OFFLINE:
            return 410, {"code": "LAPTOP_OFFLINE", "message": "El portátil está desconectado.",
                         "idempotencyKey": payload.get("idempotencyKey")}
        ledger_payload = _laptop_command(payload)
        if not ledger_payload or not ledger_payload.get("idempotency_key"):
            return 400, {"code": "INVALID_COMMAND", "message": "El comando remoto no es válido."}
        try:
            status, result = self.laptop.command(ledger_payload)
            if "idempotency_key" in result:
                result = {**result, "idempotencyKey": result.pop("idempotency_key")}
            return status, result
        except UpstreamError:
            return 503, {"code": "UNKNOWN_OUTCOME", "message": "No se pudo confirmar el resultado del comando.",
                         "idempotencyKey": payload.get("idempotencyKey")}

    def relay_ledger_command(self, ledger_payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        """Send an already ledger-shaped command (e.g. from the Telegram bot) to the laptop."""
        if self.liveness.status is LaptopStatus.OFFLINE:
            return 410, {"code": "LAPTOP_OFFLINE"}
        try:
            return self.laptop.command(ledger_payload)
        except UpstreamError:
            return 503, {"code": "UNKNOWN_OUTCOME"}

    def relay_challenge(self, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        if self.liveness.status is LaptopStatus.OFFLINE:
            return 410, {"code": "LAPTOP_OFFLINE", "message": "El portátil está desconectado."}
        target = payload.get("target")
        if not isinstance(target, dict) or not isinstance(target.get("project"), str) \
                or not isinstance(target.get("req"), str) or not isinstance(payload.get("typedReq"), str):
            return 400, {"code": "INVALID_CHALLENGE", "message": "El desafío de confirmación no es válido."}
        try:
            return self.laptop.challenge({"target": f"{target['project']}/{target['req']}",
                                          "typedReq": payload["typedReq"]})
        except UpstreamError:
            return 503, {"code": "UNKNOWN_OUTCOME", "message": "No se pudo confirmar el desafío."}

    def _notify_long_offline_with_active_run(self) -> None:
        offline_since = self.liveness.offline_since
        if offline_since is None or time.monotonic() - offline_since < OFFLINE_ALERT_DELAY_SECONDS:
            return
        if self.offline_generation <= self.offline_alerted_generation:
            return
        try:
            snapshot = self.laptop.snapshot()
        except UpstreamError:
            return
        runs = snapshot.get("runs")
        if not isinstance(runs, list) or not any(
            isinstance(run, dict) and (run.get("active") is True or run.get("status") in ACTIVE_RUN_STATES)
            for run in runs
        ):
            return
        key = f"liveness:laptop:offline:{self.offline_generation}"
        self.outbox.enqueue(key, "El portátil lleva más de 15 minutos desconectado mientras hay una ejecución activa.",
                            review_url(self.config.frontend_origin))
        self.outbox.set_state_value("laptop_outage_alerted", self.offline_generation)
        self.offline_alerted_generation = self.offline_generation

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
            browser_event = _browser_event(event)
            if browser_event is None:
                continue
            stable_id = event.get("id") or event.get("cursor")
            if stable_id:
                upstream_key = str(stable_id)
            elif event.get("ord"):
                upstream_key = f"{event.get('run', '')}/{event['ord']}"
            else:
                upstream_key = ""
            with self._stream_condition:
                if upstream_key and upstream_key in self._seen_upstream_event_keys:
                    continue
                if upstream_key:
                    if len(self._seen_upstream_events) == self._seen_upstream_events.maxlen:
                        expired = self._seen_upstream_events.popleft()
                        self._seen_upstream_event_keys.discard(expired)
                    self._seen_upstream_events.append(upstream_key)
                    self._seen_upstream_event_keys.add(upstream_key)
                self._stream_sequence += 1
                self._stream_events.append((self._stream_sequence, browser_event))
                self._stream_condition.notify_all()
            notification = notification_for_event(event, self.config.frontend_origin)
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
