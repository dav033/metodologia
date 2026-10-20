"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from config import GatewayConfig
from commands import to_laptop_command, validate_command
from liveness import LaptopStatus, LivenessMonitor
from notifications import NotificationOutbox, TelegramSender, notification_for_event
from stream import SnapshotEventStream
from upstream import LaptopClient, UpstreamError, UpstreamResponseError, UpstreamTimeout

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})


class CommandRelayError(RuntimeError):
    def __init__(self, status: int, code: str, message: str, idempotency_key: str | None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.idempotency_key = idempotency_key


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
        self.has_cached_active_run = bool(self.outbox.state_value("laptop_has_cached_active_run"))
        self.stream = SnapshotEventStream()

    def poll_once(self) -> None:
        try:
            health = self.laptop.health()
            if health.get("status") != "ok":
                raise UpstreamError("laptop health check was not successful")
        except UpstreamError:
            transition = self.liveness.record_failure()
            self.stream.update_laptop_status(
                self.liveness.status is LaptopStatus.ONLINE,
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            )
            if transition and transition.current is LaptopStatus.OFFLINE:
                self.offline_generation = self.outbox.next_sequence("laptop_outage_generation")
                self._publish_snapshot_changed("laptop.offline")
        else:
            transition = self.liveness.record_success()
            self._refresh_active_run_cache()
            if transition and transition.current is LaptopStatus.ONLINE:
                self._publish_snapshot_changed("laptop.online")
            self._poll_events()
        if self.liveness.status is LaptopStatus.OFFLINE:
            self._notify_long_offline_with_active_run()
        self.outbox.deliver_due(self.sender)

    def _publish_snapshot_changed(self, reason: str) -> None:
        """Wake open panels when liveness changes the cached snapshot outside the laptop event feed."""
        self.stream.publish([{
            "schemaVersion": 1,
            "type": "snapshot.updated",
            "occurredAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": {"reason": reason},
        }])

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
        has_active_run = any(
            isinstance(run, dict) and (run.get("active") is True or run.get("status") in ACTIVE_RUN_STATES)
            for run in runs
        )
        self.stream.update_snapshot(snapshot, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
        self.stream.update_laptop_status(
            True, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
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
        valid_events = [event for event in events if isinstance(event, dict)]
        self.stream.publish(valid_events)
        for event in valid_events:
            notification = notification_for_event(event)
            if notification:
                self.outbox.enqueue(*notification)
        next_cursor = result.get("nextCursor")
        if isinstance(next_cursor, str):
            self.event_cursor = next_cursor

    def submit_command(self, value: object) -> tuple[int, dict[str, Any]]:
        command = validate_command(value)
        key = command["idempotencyKey"]
        if self.liveness.status is LaptopStatus.OFFLINE:
            raise CommandRelayError(410, "LAPTOP_OFFLINE", "Laptop is offline; command was not queued", key)
        try:
            return self.laptop.command(to_laptop_command(command))
        except UpstreamResponseError as exc:
            code = exc.payload.get("code")
            safe_codes = {
                "INVALID_COMMAND", "STALE_PRECONDITION", "IDEMPOTENCY_CONFLICT", "CONFIRMATION_REQUIRED",
                "CONFIRMATION_EXPIRED", "LAPTOP_OFFLINE", "BODY_TOO_LARGE", "COMMAND_NOT_APPLICABLE",
            }
            safe_code = code if isinstance(code, str) and code in safe_codes else "COMMAND_REJECTED"
            raise CommandRelayError(exc.status, safe_code, "Laptop rejected the command", key) from exc
        except (UpstreamTimeout, UpstreamError) as exc:
            raise CommandRelayError(503, "UNKNOWN_OUTCOME", "Command outcome is unknown; retry with the same idempotency key", key) from exc

    def issue_challenge(self, value: object) -> tuple[int, dict[str, Any]]:
        from commands import validate_challenge

        challenge = validate_challenge(value)
        try:
            return self.laptop.issue_challenge(challenge)
        except UpstreamResponseError as exc:
            code = exc.payload.get("code")
            safe_code = code if isinstance(code, str) and code in {
                "INVALID_CHALLENGE", "CONFIRMATION_REQUIRED",
            } else "CHALLENGE_REJECTED"
            raise CommandRelayError(exc.status, safe_code, "Laptop rejected the confirmation challenge", None) from exc
        except (UpstreamTimeout, UpstreamError) as exc:
            raise CommandRelayError(503, "CHALLENGE_UNAVAILABLE", "Could not issue a confirmation challenge", None) from exc

    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            self.poll_once()
            time.sleep(max(0.0, self.config.probe_interval - (time.monotonic() - started)))


def create_runtime(config: GatewayConfig, laptop: Any | None = None, sender: Any | None = None) -> GatewayRuntime:
    """Build the same runtime used by the production command and integration tests."""
    return GatewayRuntime(config, laptop=laptop, sender=sender)
