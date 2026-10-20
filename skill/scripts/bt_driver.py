"""Provider driver contract v1 (REQ-007 T7): one invocation/result shape over the three CLI providers.

It wraps the existing argv builders and output parsers (bt_runprompt.agent_argv, bt_runsettle.parse_output/
detect_limit, bt_agy) so there is one implementation of each. The supervisor consumes it in two read-only ways
(D-015): bt_runsession records what the contract would call each session, and bt_runsettle adds that status to the
diagnosis of a session that ended without a verdict. Neither changes a decision: claims, verify, timeout and limit
checks stay where they were, and the real-provider samples under tests/migration/fixtures/providers pin the parsing.

A driver owns argv/stdin, the environment boundary, timeout and cancellation, and stream normalization. It never
decides that work is *verified*: `Outcome.status == "completed"` only means the provider finished a turn cleanly.
The supervisor's own verify step is the only source of "done".

Known limits (pinned by tests): Codex has no end-of-turn event, so `completed` there means "exit 0 with output";
a SIGTERM to the supervisor is not translated (only KeyboardInterrupt gives `cancelled`); `limit` follows
bt_runsettle.detect_limit, which needs a failing exit or is_error to call a message a limit.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import bt_agents
import bt_agy
import bt_events
import bt_runprompt
import bt_runsettle

CONTRACT_VERSION = 1
STATUSES = ("completed", "failed", "limit", "partial", "timeout", "cancelled")
PROVIDERS = ("claude", "codex", "antigravity")


@dataclass(frozen=True)
class Invocation:
    provider: str
    argv: tuple[str, ...] = field(repr=False)        # carries the prompt for Claude/Antigravity
    stdin: str | None = field(repr=False)            # carries the prompt for Codex
    cwd: str = ""
    env_remove: tuple[str, ...] = ()
    env_set: tuple[tuple[str, str], ...] = field(default=(), repr=False)  # values may be secrets

    def environment(self, base: dict[str, str]) -> dict[str, str]:
        env = {k: v for k, v in base.items() if k not in self.env_remove}
        env.update(dict(self.env_set))
        return env

    def redacted(self) -> dict:
        """What may be logged: no prompt text, no environment values."""
        return {"provider": self.provider, "argv0": Path(self.argv[0]).name, "argc": len(self.argv),
                "stdin_bytes": len(self.stdin.encode()) if self.stdin else 0, "cwd": self.cwd,
                "env_removed": list(self.env_remove), "env_set": [k for k, _ in self.env_set]}


@dataclass(frozen=True)
class Outcome:
    version: int
    provider: str
    status: str                       # one of STATUSES
    text: str = ""
    returncode: int | None = None
    is_error: bool = False
    terminal_event: bool = False      # the provider's own end-of-turn result was seen
    reset_epoch: int | None = None    # None = unknown, never a guess
    cost_usd: float | None = None     # reported only
    usage: dict | None = field(default=None, hash=False)  # as reported; None = not reported

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in ("version", "provider", "status", "text", "returncode", "is_error",
                                              "terminal_event", "reset_epoch", "cost_usd", "usage")}


def _terminal_event(provider: str, raw: str) -> dict | None:
    """The provider's own end-of-turn event, or None (a cut stream has none)."""
    for line in reversed((raw or "").splitlines()):
        if not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if provider == "claude" and isinstance(obj, dict) and obj.get("type") == "result":
            return obj
        if (provider == "antigravity" and isinstance(obj, dict) and obj.get("event") == "result"
                and isinstance(obj.get("result"), dict)):  # the shape bt_agy.parse_result can read
            return obj
    return None


class Driver:
    """Base behaviour; the provider differences are the three small methods below."""

    provider = ""

    def __init__(self, executable: str | None = None) -> None:
        self.executable = executable

    # -- invocation -----------------------------------------------------------------------------------------
    def invocation(self, prompt: str, workdir: Path, model: str | None = None, effort: str | None = None,
                   timeout_sec: int | None = None, env_remove: tuple[str, ...] = (),
                   env_set: tuple[tuple[str, str], ...] = (), structured: bool = False,
                   max_turns: int | None = None) -> Invocation:
        state = {"agent": self.provider,
                 "limits": {"session_timeout_min": timeout_sec / 60} if timeout_sec else {}}
        argv, stdin = bt_runprompt.agent_argv(state, Path(workdir), prompt, model, effort, structured=structured,
                                           max_turns=max_turns)
        if self.executable:
            argv[0] = self.executable
        return Invocation(self.provider, tuple(argv), stdin, str(workdir), env_remove, env_set)

    # -- result ---------------------------------------------------------------------------------------------
    def normalize(self, raw: str, returncode: int | None, *, timed_out: bool = False, cancelled: bool = False,
                  now: float | None = None) -> Outcome:
        base = {"version": CONTRACT_VERSION, "provider": self.provider, "returncode": returncode}
        if cancelled:
            return Outcome(status="cancelled", text=(raw or "")[-4000:], **base)
        if timed_out:
            return Outcome(status="timeout", text=(raw or "")[-4000:], **base)
        parsed = bt_runsettle.parse_output(raw)
        info = {"rc": returncode if returncode is not None else 1, "text": raw or "", "parsed": parsed}
        terminal = self._terminal(raw, returncode)
        usage = self._usage(raw)
        cost = parsed.get("cost") if isinstance(parsed.get("cost"), (int, float)) else None
        limit = bt_runsettle.detect_limit(info)
        if limit is not None:
            reset = int(limit) if limit else None
            return Outcome(status="limit", text=parsed["text"], is_error=True, terminal_event=terminal,
                           reset_epoch=reset, cost_usd=cost, usage=usage, **base)
        failed = bool(returncode) or bool(parsed.get("is_error"))
        if failed:
            return Outcome(status="failed", text=parsed["text"], is_error=True, terminal_event=terminal,
                           cost_usd=cost, usage=usage, **base)
        if not terminal:
            return Outcome(status="partial", text=parsed["text"], terminal_event=False, cost_usd=cost, usage=usage,
                           **base)
        return Outcome(status="completed", text=parsed["text"], terminal_event=True, cost_usd=cost, usage=usage,
                       **base)

    def _terminal(self, raw: str, returncode: int | None) -> bool:
        return _terminal_event(self.provider, raw) is not None

    def _usage(self, raw: str) -> dict | None:
        return None

    # -- execution ------------------------------------------------------------------------------------------
    def run(self, invocation: Invocation, timeout_sec: float, base_env: dict[str, str] | None = None) -> Outcome:
        """Run to completion, kill the whole process group on timeout, normalize. Never raises on provider
        failure; a binary that cannot start is a `failed` outcome with returncode None."""
        env = invocation.environment(dict(os.environ if base_env is None else base_env))
        try:
            process = subprocess.Popen(invocation.argv, stdin=subprocess.PIPE if invocation.stdin is not None
                                       else subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       cwd=invocation.cwd, env=env, text=True, start_new_session=True)
        except OSError as error:
            return Outcome(version=CONTRACT_VERSION, provider=self.provider, status="failed",
                           text=f"cannot start provider: {type(error).__name__}", is_error=True)
        try:
            out, _ = process.communicate(invocation.stdin, timeout=timeout_sec)
            return self.normalize(out, process.returncode)
        except subprocess.TimeoutExpired as expired:
            os.killpg(process.pid, signal.SIGKILL)
            try:
                tail, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:  # a descendant that left the group still holds the pipe
                process.stdout.close()
                tail = ""
            head = expired.stdout.decode("utf-8", "replace") if isinstance(expired.stdout, bytes) else expired.stdout
            return self.normalize((head or "") + (tail or ""), process.returncode, timed_out=True)
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGKILL)
            try:
                out, _ = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.stdout.close()
                out = ""
            return self.normalize(out, process.returncode, cancelled=True)


class ClaudeDriver(Driver):
    provider = "claude"

    def _usage(self, raw: str) -> dict | None:
        event = _terminal_event("claude", raw)
        usage = (event or {}).get("usage")
        return usage if isinstance(usage, dict) else None


class CodexDriver(Driver):
    provider = "codex"

    def _terminal(self, raw: str, returncode: int | None) -> bool:
        # With `--json` the stream ends in a `turn.completed` event: that is the provider's own end of turn. In text
        # mode `codex exec` has no such event, so a clean exit with output is the only evidence there is; that is best
        # effort, a truncated message that exits 0 or a printed error with rc 0 is `completed`. The supervisor's own
        # verification is what decides success, never this status.
        if bt_runsettle.codex_events(raw):
            return bt_runsettle.codex_turn(raw) == "completed"
        return returncode == 0 and bool((raw or "").strip())

    def _usage(self, raw: str) -> dict | None:
        # `--json` reports the split (input, cached input, output, reasoning); text mode only the closing "tokens used"
        # total, a total and never a split.
        if bt_runsettle.codex_events(raw):
            usage = bt_events.extract_usage("codex", raw)
            fields = {key: usage[key] for key in ("input_tokens", "output_tokens", "cache_read_tokens", "total_tokens")
                      if usage.get(key) is not None}
            return fields or None
        found = bt_events._CODEX_TOTAL.findall(raw or "")
        digits = "".join(ch for ch in found[-1] if ch.isdigit()) if found else ""
        return {"total_tokens": int(digits)} if digits else None


class AntigravityDriver(Driver):
    provider = "antigravity"

    def _usage(self, raw: str) -> dict | None:
        return bt_agy.usage_of(raw)


DRIVERS = {"claude": ClaudeDriver, "codex": CodexDriver, "antigravity": AntigravityDriver}


def driver_for(provider: str, executable: str | None = None) -> Driver:
    if provider not in DRIVERS:
        raise ValueError(f"unknown provider {provider!r}")
    return DRIVERS[provider](executable)


def capabilities(provider: str) -> dict:
    """Models and efforts the router may select for this provider (from the one catalogue, bt_agents)."""
    models = [m for m, spec in bt_agents.MODELS.items() if spec["provider"] == provider]
    return {"version": CONTRACT_VERSION, "provider": provider, "models": models,
            "efforts": sorted({e for ladder in (bt_agents.LADDER, bt_agents.AUDIT_LADDER)
                               for _, e in ladder.get(provider, ()) if e})}
