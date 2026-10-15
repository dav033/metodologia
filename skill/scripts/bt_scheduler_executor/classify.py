"""Turn the end of a process into a cause class. Facts only: nothing here retries, switches provider or accepts work."""
from __future__ import annotations

import re
from typing import Any

from . import model as m
from .ports import AgentDriver
from .procinfo import signal_name

# Evidence of a lost connection. Applied only to the tail of the output of a FAILING exit: the same words in the output of
# a process that exited 0 are text the agent printed (it may be fixing a network bug), never a failure.
CONNECTION_PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"\bECONNRESET\b", r"\bECONNREFUSED\b", r"\bETIMEDOUT\b", r"\bENOTFOUND\b", r"\bEAI_AGAIN\b", r"\bEPIPE\b",
    r"getaddrinfo", r"socket hang up", r"fetch failed", r"unable to connect", r"could not resolve host",
    r"network (?:is )?(?:unreachable|error|down)", r"connection (?:was )?(?:reset|refused|closed|lost|timed out|error)",
    r"(?:stream|connection) (?:disconnected|closed before|dropped)", r"tls handshake", r"\boffline\b.*\bnetwork\b",
))
TAIL_BYTES = 8192


def looks_like_connection_loss(raw: str) -> bool:
    tail = raw[-TAIL_BYTES:]
    return any(p.search(tail) for p in CONNECTION_PATTERNS)


def outcome(driver: AgentDriver, route: m.Route, raw: str, exit_info: dict[str, Any], *,
            cancel_requested: bool, state_before: str, totals: tuple[int, int]) -> dict[str, Any]:
    """The persisted outcome of an attempt: final state, cause class and the facts behind it."""
    reason = str(exit_info.get("reason", ""))
    rc = exit_info.get("returncode")
    base: dict[str, Any] = {"reason": reason, "returncode": rc, "signal": signal_name(rc), "reset_epoch": None,
                            "detail": "", "usage": None, "cost_usd": None, "terminal_event": False,
                            "output": {"bytes": totals[0], "dropped": totals[1]}}

    def done(final: str, cause: str, detail: str = "", **extra: Any) -> dict[str, Any]:
        return {**base, "final": final, "cause": cause, "detail": detail or base["detail"], **extra}

    if (reason == "cancelled" and cancel_requested) or (cancel_requested and state_before in (m.QUEUED, m.PREPARING)):
        return done(m.CANCELLED, m.CANCEL_CAUSE)
    if reason == "cancelled":            # the shim was stopped by someone else (shutdown, pkill): not our cancellation
        return done(m.FAILED, m.KILLED, "the supervising shim was terminated from outside")
    if reason in ("spawn_error", "start_failed"):
        text = str(exit_info.get("error", ""))[:300]
        return done(m.FAILED, m.ARTIFACT if text.startswith("ARTIFACT_ERROR") else m.START_FAILED, text)
    if reason == "lost" and cancel_requested:     # the operator wanted it stopped and the supervisor is gone: stopped
        return done(m.CANCELLED, m.CANCEL_CAUSE, "the supervising shim vanished after the cancel was requested")
    if reason == "lost":
        return done(m.FAILED, m.LOST, str(exit_info.get("error", "")) or "the supervising shim vanished without an exit record")
    try:
        cls = driver.classify(route, raw, rc, timed_out=reason == "timeout", cancelled=False)
    except Exception as error:
        cls = None
        base["detail"] = f"classifier error: {type(error).__name__}"
    if cls is not None:
        base.update(usage=dict(cls.usage) if cls.usage else None, cost_usd=cls.cost_usd,
                    terminal_event=cls.terminal_event)
    if reason == "timeout":
        return done(m.FAILED, m.TIMEOUT)
    if cls is not None and cls.status == "limit":
        return done(m.FAILED, m.QUOTA, reset_epoch=cls.reset_epoch)
    if cls is not None and cls.status == "completed" and rc == 0:
        return done(m.FINISHED, m.CLEAN)
    if cls is not None and cls.status == "partial":
        return done(m.FAILED, m.INCOMPLETE, "exited cleanly without the provider's end-of-turn evidence")
    if isinstance(rc, int) and rc < 0:
        return done(m.FAILED, m.KILLED, f"terminated by {signal_name(rc)}")
    if isinstance(rc, int) and rc != 0 and looks_like_connection_loss(raw):
        return done(m.FAILED, m.CONNECTION)
    return done(m.FAILED, m.AGENT_ERROR, base["detail"] or (f"exit code {rc}" if rc else "provider reported an error"))
