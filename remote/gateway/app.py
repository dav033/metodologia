"""Production composition for polling, liveness and durable notifications."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Mapping

from config import GatewayConfig
<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
from commands import validate_command
=======
from commands import CommandValidationError, validate_command
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935
from liveness import LaptopStatus, LivenessMonitor
from notifications import NotificationOutbox, TelegramSender, notification_for_event
from upstream import LaptopClient, UpstreamError, UpstreamTimeout

logger = logging.getLogger(__name__)
OFFLINE_ALERT_DELAY_SECONDS = 15 * 60
ACTIVE_RUN_STATES = frozenset({"running", "waiting", "paused"})
CHALLENGED_COMMANDS = frozenset({"revise", "approve", "launch", "cancel-plan", "delete-plan", "edit-brief"})
TELEGRAM_REQ_ID = re.compile(r"^REQ-[0-9]{3,}$")


<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
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
                 "note": "note", "attemptId": "attempt", "taskId": "task"}
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
        params["route"] = route.get("id") or route.get("routeId") or route.get("route")
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
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
class CommandRelayError(RuntimeError):
    def __init__(self, status: int, code: str, message: str, idempotency_key: str):
        super().__init__(message)
        self.status = status
        self.code = code
        self.idempotency_key = idempotency_key
=======
class CommandRelayError(RuntimeError):
    def __init__(self, status: int, code: str, message: str, idempotency_key: str | None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.idempotency_key = idempotency_key
>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935


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
        command_type = request.get("type")
        target = request.get("target")
        precondition = request.get("precondition")
        if (isinstance(request.get("schemaVersion"), bool)
                or set(request) != {"schemaVersion", "idempotencyKey", "type", "target", "precondition"}
                or not isinstance(key, str) or not 16 <= len(key) <= 128
                or not re.fullmatch(r"[A-Za-z0-9._:-]+", key)
                or not isinstance(command_type, str) or command_type not in {"pause", "resume"}
                or not isinstance(target, Mapping)
                or set(target) != {"kind", "project", "req"} or target.get("kind") != "run"
                or not isinstance(target.get("project"), str) or not 1 <= len(target["project"]) <= 80
                or not isinstance(target.get("req"), str) or not TELEGRAM_REQ_ID.fullmatch(target["req"])
                or not isinstance(precondition, Mapping)
                or set(precondition) != {"state"}
                or not isinstance(precondition.get("state"), str)
                or not 1 <= len(precondition["state"]) <= 80):
            return {"status": "REJECTED", "code": "INVALID_COMMAND", "stored": False}
        ledger_request = {
            "idempotency_key": key,
            "command": command_type,
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
            notification = notification_for_event(event)
            if notification:
                self.outbox.enqueue(*notification)
        next_cursor = result.get("nextCursor")
        if isinstance(next_cursor, str):
            self.event_cursor = next_cursor

<<<<<<< 4afe24b9701478e708836c2a834fe7e817773f1d
||||||| c04d03849ef5c7dc6c4e925a2221829c531ea8d3
    def submit_command(self, value: object) -> tuple[int, dict[str, Any]]:
        command = validate_command(value)
        target = command["target"]
        params = {key: item for key, item in command.items()
                  if key not in {"schemaVersion", "idempotencyKey", "type", "target", "precondition"}}
        if "taskId" in target:
            params["task"] = target["taskId"]
        if "attemptId" in target:
            params["attempt"] = target["attemptId"]
        if "requestId" in params:
            params["request_id"] = params.pop("requestId")
        if "typedReq" in params:
            params["typed_req"] = params.pop("typedReq")
        if "answer" in params and command["type"] == "answer-round":
            params["answers"] = params.pop("answer")
        if "confirmation" in params and isinstance(params["confirmation"], dict):
            confirmation = params["confirmation"]
            params["confirmation"] = {
                "challenge_id": confirmation.get("challengeId", confirmation.get("challenge_id")),
                "typed_req": confirmation.get("typedReq", confirmation.get("typed_req")),
            }
        ledger_command = {
            "idempotency_key": command["idempotencyKey"],
            "command": command["type"],
            "target": f'{target["project"]}/{target["req"]}',
            "origin": "web",
            "params": params,
            "precondition": command["precondition"],
        }
        return self._relay_command(ledger_command)

    def submit_telegram_command(self, value: object) -> tuple[int, dict[str, Any]]:
        command = validate_command(value)
        if command["type"] not in {"pause", "resume"} or command["target"]["kind"] != "run":
            raise CommandValidationError("INVALID_COMMAND", "Telegram command target or type is not allowed")
        target = command["target"]
        ledger_command = {
            "idempotency_key": command["idempotencyKey"],
            "command": command["type"],
            "target": f"{target['project']}/{target['req']}",
            "origin": "telegram",
            "params": {},
            "precondition": {"state": command["precondition"]["state"]},
        }
        return self._relay_command(ledger_command)

    def _relay_command(self, command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        key = command.get("idempotencyKey", command.get("idempotency_key", ""))
        if self.liveness.status is LaptopStatus.OFFLINE:
            raise CommandRelayError(410, "LAPTOP_OFFLINE", "Laptop is offline; command was not queued", key)
        try:
            return self.laptop.command(command)
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

=======
    def submit_command(self, value: object) -> tuple[int, dict[str, Any]]:
        command = validate_command(value)
        target = command["target"]
        params = {key: item for key, item in command.items()
                  if key not in {"schemaVersion", "idempotencyKey", "type", "target", "precondition"}}
        if "taskId" in target:
            params["task"] = target["taskId"]
        if "attemptId" in target:
            params["attempt"] = target["attemptId"]
        if "requestId" in params:
            params["request_id"] = params.pop("requestId")
        if "typedReq" in params:
            params["typed_req"] = params.pop("typedReq")
        if "answer" in params and command["type"] == "answer-round":
            params["answers"] = params.pop("answer")
        confirmation = params.pop("confirmation", None)
        ledger_command = {
            "idempotency_key": command["idempotencyKey"],
            "command": command["type"],
            "target": f'{target["project"]}/{target["req"]}',
            "origin": "web",
            "params": params,
            "precondition": command["precondition"],
        }
        if isinstance(confirmation, dict):
            ledger_command["confirmation"] = {
                "challenge_id": confirmation.get("challengeId", confirmation.get("challenge_id")),
                "typed_req": confirmation.get("typedReq", confirmation.get("typed_req")),
            }
        return self._relay_command(ledger_command)

    def issue_challenge(self, target: str, typed_req: str) -> dict[str, Any]:
        if (not isinstance(target, str) or target.count("/") != 1 or not isinstance(typed_req, str)
                or target.rsplit("/", 1)[-1] != typed_req):
            raise CommandValidationError("INVALID_CHALLENGE", "Typed request id must match its target")
        if self.liveness.status is LaptopStatus.OFFLINE:
            raise CommandRelayError(410, "LAPTOP_OFFLINE", "Laptop is offline; challenge was not issued", None)
        try:
            challenge = self.laptop.challenge({"target": target, "typedReq": typed_req})
        except UpstreamResponseError as exc:
            code = exc.payload.get("code")
            safe_code = code if isinstance(code, str) and code in {"INVALID_CHALLENGE", "LAPTOP_OFFLINE"} else "CHALLENGE_REJECTED"
            raise CommandValidationError(safe_code, "Laptop rejected the confirmation challenge", exc.status) from exc
        except UpstreamError as exc:
            raise CommandRelayError(503, "CHALLENGE_UNAVAILABLE", "Could not issue confirmation challenge", None) from exc
        if not isinstance(challenge, dict) or not isinstance(challenge.get("challengeId"), str):
            raise CommandRelayError(503, "CHALLENGE_UNAVAILABLE", "Laptop returned an invalid confirmation challenge", None)
        return challenge

    def submit_telegram_command(self, value: object) -> tuple[int, dict[str, Any]]:
        command = validate_command(value)
        if command["type"] not in {"pause", "resume"} or command["target"]["kind"] != "run":
            raise CommandValidationError("INVALID_COMMAND", "Telegram command target or type is not allowed")
        target = command["target"]
        ledger_command = {
            "idempotency_key": command["idempotencyKey"],
            "command": command["type"],
            "target": f"{target['project']}/{target['req']}",
            "origin": "telegram",
            "params": {},
            "precondition": {"state": command["precondition"]["state"]},
        }
        return self._relay_command(ledger_command)

    def _relay_command(self, command: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        key = command.get("idempotencyKey", command.get("idempotency_key", ""))
        if self.liveness.status is LaptopStatus.OFFLINE:
            raise CommandRelayError(410, "LAPTOP_OFFLINE", "Laptop is offline; command was not queued", key)
        try:
            return self.laptop.command(command)
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

>>>>>>> 8a050424a13d0335b6f496bee2e6edb1152be935
    def run_forever(self) -> None:
        while True:
            started = time.monotonic()
            self.poll_once()
            time.sleep(max(0.0, self.config.probe_interval - (time.monotonic() - started)))


def create_runtime(config: GatewayConfig, laptop: Any | None = None, sender: Any | None = None) -> GatewayRuntime:
    """Build the same runtime used by the production command and integration tests."""
    return GatewayRuntime(config, laptop=laptop, sender=sender)
