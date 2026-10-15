"""Bounded offline Laya chooser process; third-party ML dependencies stay outside M2's stdlib core."""
from __future__ import annotations

import json
import math
import os
import selectors
import shutil
import subprocess
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from bt_scheduler_decision import Candidate, ChooserFailure, DecisionRequest, LayaChoice

CHECKPOINTS = {
    "english": ("convaiinnovations/laya", "55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
                "891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c"),
    "multilingual": ("convaiinnovations/laya-multilingual", "e4e9ddf21a7b1903b7acffd8814ad4307bf63a67",
                     "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204"),
    "typed-decisions": ("convaiinnovations/laya-typed-decisions", "1a793eb568e6718f15941d08f85432581df534e3",
                        "4fa56de72383a9d3efa9cfa78955733c81b9fc8067a587ca4beb82c78107a24e"),
}
WORKER = Path(__file__).with_name("bt_scheduler_laya_worker.py")
MAX_REQUEST_BYTES = 32_768
MAX_RESPONSE_BYTES = 16_384
DEFAULT_WORKER_MEMORY_LIMIT_BYTES = 5 * 1024**3


@dataclass(frozen=True)
class LocalLayaConfig:
    root: Path
    checkpoint: str
    deadline_seconds: float = 90.0
    circuit_failures: int = 2
    circuit_open_seconds: float = 60.0
    device: str = "auto"
    worker_memory_limit_bytes: int = DEFAULT_WORKER_MEMORY_LIMIT_BYTES

    def __post_init__(self) -> None:
        if self.checkpoint not in CHECKPOINTS or self.device not in {"auto", "cpu", "cuda"}:
            raise ValueError("unsupported Laya checkpoint or device")
        if not isinstance(self.deadline_seconds, (int, float)) or isinstance(self.deadline_seconds, bool) or \
                not 0 < self.deadline_seconds <= 300:
            raise ValueError("Laya deadline must be between 0 and 300 seconds")
        if not isinstance(self.circuit_failures, int) or isinstance(self.circuit_failures, bool) or \
                not 1 <= self.circuit_failures <= 10 or not 0 < self.circuit_open_seconds <= 3600:
            raise ValueError("invalid Laya circuit breaker bounds")
        if not isinstance(self.worker_memory_limit_bytes, int) or isinstance(self.worker_memory_limit_bytes, bool) or \
                not 1024**3 <= self.worker_memory_limit_bytes <= 16 * 1024**3:
            raise ValueError("Laya worker memory limit must be between 1 and 16 GiB")


class LocalLayaClient:
    """One lazily started, persistent, single-model worker with serialized bounded requests."""

    def __init__(self, config: LocalLayaConfig, *, command: tuple[str, ...] | None = None):
        self.config = config
        self._command = command
        self._lock = threading.Lock()
        self._process: subprocess.Popen[bytes] | None = None
        self._failure_count = 0
        self._invalid_choice_count = 0
        self._opened_until = 0.0
        self._request_id = 0
        self.last_metrics: dict[str, object] = {}

    def _argv(self) -> list[str]:
        if self._command is not None:
            return list(self._command)
        python = self.config.root / "venv" / "bin" / "python"
        systemd_run = shutil.which("systemd-run")
        if not python.is_file() or not WORKER.is_file() or systemd_run is None:
            raise ChooserFailure("laya_unavailable")
        return [systemd_run, "--user", "--scope", "--quiet",
                f"--property=MemoryMax={self.config.worker_memory_limit_bytes}",
                "--property=MemorySwapMax=0", "--property=OOMPolicy=kill", "--", str(python), "-I",
                str(WORKER), "--root", str(self.config.root), "--checkpoint", self.config.checkpoint,
                "--device", self.config.device, "--memory-limit-bytes",
                str(self.config.worker_memory_limit_bytes)]

    def _environment(self) -> dict[str, str]:
        env = {
            "HOME": str(Path.home()),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HF_HOME": str(self.config.root / "hf-cache"),
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "TOKENIZERS_PARALLELISM": "false",
        }
        for name in ("CUDA_VISIBLE_DEVICES", "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS", "SYSTEMD_BUS_ADDRESS"):
            if os.environ.get(name):
                env[name] = os.environ[name]
        return env

    def _start(self) -> subprocess.Popen[bytes]:
        process = self._process
        if process is not None and process.poll() is None:
            return process
        try:
            process = subprocess.Popen(self._argv(), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL, cwd=self.config.root,
                                       env=self._environment(), bufsize=0, close_fds=True)
        except (OSError, ChooserFailure) as exc:
            raise ChooserFailure("laya_unavailable") from exc
        if process.stdin is None or process.stdout is None:
            process.kill()
            raise ChooserFailure("laya_unavailable")
        self._process = process
        return process

    def _exchange(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            encoded = (json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        except (TypeError, ValueError, UnicodeEncodeError) as exc:
            raise ChooserFailure("laya_runtime_error") from exc
        if len(encoded) > MAX_REQUEST_BYTES:
            raise ChooserFailure("laya_runtime_error")
        process = self._start()
        assert process.stdin is not None and process.stdout is not None
        try:
            view = memoryview(encoded)
            while view:
                written = os.write(process.stdin.fileno(), view)
                view = view[written:]
        except OSError as exc:
            raise ChooserFailure("laya_unavailable") from exc

        deadline = time.monotonic() + self.config.deadline_seconds
        buffer = bytearray()
        selector = selectors.DefaultSelector()
        try:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise ChooserFailure("laya_timeout")
                if not selector.select(remaining):
                    raise ChooserFailure("laya_timeout")
                chunk = os.read(process.stdout.fileno(), 4096)
                if not chunk:
                    raise ChooserFailure("laya_unavailable")
                buffer.extend(chunk)
                if len(buffer) > MAX_RESPONSE_BYTES:
                    raise ChooserFailure("laya_runtime_error")
                if b"\n" not in buffer:
                    continue
                line, _separator, remainder = buffer.partition(b"\n")
                if remainder:
                    raise ChooserFailure("laya_runtime_error")
                try:
                    result = json.loads(line.decode("utf-8"), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
                    raise ChooserFailure("laya_runtime_error") from exc
                if not isinstance(result, dict) or result.get("request_id") != payload["request_id"]:
                    raise ChooserFailure("laya_runtime_error")
                if result.get("ok") is not True:
                    raise ChooserFailure("laya_runtime_error")
                return result
        finally:
            selector.close()

    @staticmethod
    def _language(brief: str) -> str:
        words = set(brief.lower().split())
        return "es" if words & {"que", "para", "con", "una", "del", "los", "las", "por", "tarea",
                                 "cambio", "revisar", "implementar"} else "en"

    def _decision_payload(self, request: DecisionRequest,
                          candidates: tuple[Candidate, ...]) -> tuple[dict[str, Any], dict[str, str]]:
        if len(candidates) > 8 or not candidates:
            raise ChooserFailure("laya_runtime_error")
        ordered = tuple(sorted(candidates, key=lambda item: item.route_id))
        account_aliases = {key: f"account-{index + 1}" for index, key in
                           enumerate(sorted({item.account_ref for item in ordered}))}
        profile_aliases = {key: f"profile-{index + 1}" for index, key in
                           enumerate(sorted({item.profile for item in ordered}))}
        labels = {candidate.route_id: f"option-{index + 1}" for index, candidate in enumerate(ordered)}
        options = {}
        for item in ordered:
            history = item.history
            verified = history.verified_successes + history.verified_failures
            verified_rate = history.verified_successes / verified if verified else None
            details = [f"provider={item.provider}", f"model={item.model}", f"effort={item.effort or 'provider-default'}",
                       f"{profile_aliases[item.profile]}", f"{account_aliases[item.account_ref]}"]
            if item.quota_used_percent is not None:
                details.append(f"quota_used_percent={item.quota_used_percent:.1f}")
            details.append(f"verified_outcomes={verified}")
            if verified_rate is not None:
                details.append(f"verified_success_rate={verified_rate:.3f}")
            if history.median_duration_seconds is not None:
                details.append(f"median_duration_seconds={history.median_duration_seconds:.1f}")
            if history.median_total_tokens is not None:
                details.append(f"median_total_tokens={history.median_total_tokens}")
            options[labels[item.route_id]] = "; ".join(details)
        task = request.task
        evidence_summary = {}
        for dimension, entry in task.classification_evidence.items():
            if isinstance(entry, Mapping) and entry.get("valid") is True:
                kinds = entry.get("reference_kinds", ())
                if isinstance(kinds, (tuple, list)) and all(isinstance(kind, str) for kind in kinds):
                    evidence_summary[dimension] = {"validated": True, "reference_kinds": sorted(set(kinds))}
        state = {
            "task": task.brief,
            "classifications": {key: task.classifications.get(key) for key in
                                ("complexity", "scope", "estimated_minutes", "risk", "coupling", "confidence")},
            "classification_evidence": evidence_summary,
            "dependencies_count": len(task.dependencies),
            "shared_resources_count": len(task.shared_resources),
            "expected_paths_count": len(task.expected_paths),
            "eligible_routes": list(options.items()),
        }
        questions = {"route": {
            "type": "choice",
            "instructions": "Choose the eligible route that best fits the task facts and measured route data. "
                            "Use the validated evidence summary to judge classification reliability; a model or account "
                            "identity is not itself a quality guarantee. Return one listed option.",
            "criteria": options,
        }}
        return ({"state": state, "questions": questions, "lang": self._language(task.brief)}, labels)

    def predict(self, state: object, questions: dict[str, object], lang: str) -> dict[str, Any]:
        """Raw typed local inference seam used by the benchmark and ``choose``."""
        with self._lock:
            now = time.monotonic()
            if self._opened_until > now:
                self._stop(kill=True)
                raise ChooserFailure("laya_circuit_open")
            if self._opened_until:
                self._opened_until = 0.0  # one half-open probe after the bounded cool-down
            self._request_id += 1
            payload = {"request_id": self._request_id, "state": state, "questions": questions, "lang": lang}
            try:
                response = self._exchange(payload)
            except ChooserFailure:
                self._failure_count += 1
                if self._failure_count >= self.config.circuit_failures:
                    self._opened_until = time.monotonic() + self.config.circuit_open_seconds
                self._stop(kill=True)
                raise
            self._failure_count = 0
            self.last_metrics = response.get("metrics") if isinstance(response.get("metrics"), dict) else {}
            result = response.get("result")
            if not isinstance(result, dict):
                raise ChooserFailure("laya_runtime_error")
            return result

    def choose(self, request: DecisionRequest, candidates: tuple[Candidate, ...]) -> LayaChoice:
        _, revision, _ = CHECKPOINTS[self.config.checkpoint]
        if request.checkpoint_revision != revision:
            raise ChooserFailure("laya_unavailable")
        payload, labels = self._decision_payload(request, candidates)
        result = self.predict(payload["state"], payload["questions"], payload["lang"])
        answer = result.get("answers", {}).get("route") if isinstance(result.get("answers"), dict) else None
        if not isinstance(answer, dict) or answer.get("type") != "choice" or \
                not isinstance(answer.get("choice"), str):
            self._invalid_choice()
        reverse = {label: route_id for route_id, label in labels.items()}
        route_id = reverse.get(answer["choice"])
        confidence = answer.get("answer_confidence")
        if route_id is None or not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            self._invalid_choice()
        try:
            score = float(confidence)
        except (OverflowError, ValueError):
            self._invalid_choice()
        if not math.isfinite(score) or not 0 <= score <= 1:
            self._invalid_choice()
        with self._lock:
            self._invalid_choice_count = 0
        return LayaChoice(route_id, score, revision)

    def _invalid_choice(self) -> None:
        """Treat malformed model answers as consecutive local failures, without trusting their option text."""
        with self._lock:
            self._invalid_choice_count += 1
            if self._invalid_choice_count >= self.config.circuit_failures:
                self._opened_until = time.monotonic() + self.config.circuit_open_seconds
        raise ChooserFailure("laya_runtime_error")

    def _stop(self, *, kill: bool) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        if process.poll() is None and kill:
            process.kill()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        if process.stdin is not None:
            process.stdin.close()
        if process.stdout is not None:
            process.stdout.close()

    def close(self) -> None:
        with self._lock:
            self._stop(kill=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
