"""Gemini CLI fixture-only parser; M3 does not advertise or launch this provider."""
from __future__ import annotations

from . import ParseResult, decode_line, digest_json, result, safe_tool_label

SCHEMA = "gemini-cli-0.63-jsonl-fixture/1"
_ROOT = {"type", "timestamp", "id", "role", "content", "tool_name", "tool_input", "tool_output",
         "stats", "status", "error_code"}
_STATS_FIELDS = {"total_tokens", "input_tokens", "output_tokens", "cached_tokens", "thought_tokens"}


def _normalize_one(raw: bytes | str) -> ParseResult:
    obj, failure = decode_line(raw, SCHEMA)
    if failure:
        return failure
    assert obj is not None
    kind = obj.get("type")
    event_id = obj.get("id")
    timestamp = obj.get("timestamp")
    if kind == "message":
        content = obj.get("content")
        if not isinstance(content, str):
            return ParseResult("malformed", "invalid_message", SCHEMA)
        return result(SCHEMA, kind, "message_delta", {"message_count": 1,
                      "byte_count": len(content.encode("utf-8", "replace"))}, obj, _ROOT,
                      event_id=event_id, occurred_at=timestamp)
    if kind == "tool_use":
        name = obj.get("tool_name")
        raw_input = obj.get("tool_input", {})
        try:
            byte_count, digest = digest_json(raw_input)
        except (TypeError, ValueError, UnicodeError, RecursionError):
            return ParseResult("malformed", "invalid_tool_input", SCHEMA)
        return result(SCHEMA, kind, "tool_started", {"tool_label": safe_tool_label(name), "argument_bytes": byte_count,
                      "argument_digest": digest}, obj, _ROOT,
                      event_id=event_id, occurred_at=timestamp)
    if kind == "result":
        status = obj.get("status")
        if status in ("error", "failed"):
            code = obj.get("error_code")
            if code in ("quota_exceeded", "rate_limit"):
                return result(SCHEMA, kind, "quota_error", {"source_code": str(code)}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp)
            return result(SCHEMA, kind, "transport_error", {"source_code": "provider_error"}, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp)
        stats = obj.get("stats")
        if isinstance(stats, dict):
            value = stats.get("total_tokens")
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                return result(SCHEMA, kind, "usage_reported", {"metric_name": "total_tokens", "value": value,
                              "unit": "tokens", "source": "provider_reported", "sample_count": 1}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp,
                              nested=(("stats", stats, _STATS_FIELDS),))
        return ParseResult("ignored", "result_without_usage", SCHEMA, str(kind))
    if kind == "init":
        return ParseResult("ignored", "initialization_event", SCHEMA, str(kind))
    return ParseResult("unsupported", "unknown_event_type", SCHEMA, "unsupported")


def normalize(raw: bytes | str) -> tuple[ParseResult, ...]:
    return (_normalize_one(raw),)


__all__ = ["normalize"]
