"""Codex `exec --json` fixture normalizer."""
from __future__ import annotations

from . import ParseResult, decode_line, digest_json, result

SCHEMA = "codex-exec-json/1"
_ROOT = {"type", "thread_id", "turn_id", "item", "item_id", "usage", "input_tokens", "output_tokens",
         "cached_input_tokens", "reasoning_output_tokens", "timestamp", "id", "error_code", "status"}


def _normalize_one(raw: bytes | str) -> ParseResult:
    obj, failure = decode_line(raw, SCHEMA)
    if failure:
        return failure
    assert obj is not None
    kind = obj.get("type")
    event_id = obj.get("id")
    timestamp = obj.get("timestamp")
    if kind == "turn.started":
        return result(SCHEMA, kind, "heartbeat", {"status": "started"}, obj, _ROOT,
                      event_id=event_id, occurred_at=timestamp)
    if kind == "turn.completed":
        usage = obj.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if total is None:
                input_tokens = usage.get("input_tokens")
                output_tokens = usage.get("output_tokens")
                if all(isinstance(value, int) and not isinstance(value, bool) and value >= 0
                       for value in (input_tokens, output_tokens)):
                    total = input_tokens + output_tokens
            if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
                return result(SCHEMA, kind, "usage_reported", {"metric_name": "total_tokens", "value": total,
                              "unit": "tokens", "source": "provider_reported", "sample_count": 1}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp,
                              nested=(("usage", usage, {"total_tokens", "input_tokens", "output_tokens",
                                                        "cached_input_tokens", "reasoning_output_tokens"}),))
        return ParseResult("ignored", "usage_unavailable", SCHEMA, kind)
    if kind == "item.started" or kind == "item.completed":
        item = obj.get("item")
        if not isinstance(item, dict):
            return ParseResult("malformed", "invalid_item", SCHEMA)
        item_type = item.get("type")
        label = {"command_execution": "command", "file_change": "file_change", "mcp_tool_call": "mcp_tool"}.get(
            item_type, "item")
        if kind == "item.started":
            raw_args = item.get("command", item.get("input", ""))
            try:
                byte_count, digest = digest_json(raw_args)
            except (ValueError, TypeError, UnicodeError, RecursionError):
                return ParseResult("malformed", "invalid_tool_input", SCHEMA)
            payload = {"tool_label": label, "argument_bytes": byte_count, "argument_digest": digest}
            return result(SCHEMA, kind, "tool_started", payload, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp,
                          nested=(("item", item, {"type", "id", "command", "input", "cwd", "status", "tool_name",
                                                  "exit_code", "duration_ms", "aggregated_output"}),))
        exit_code = item.get("exit_code")
        payload = {"tool_label": label}
        if isinstance(exit_code, int) and not isinstance(exit_code, bool) and 0 <= exit_code <= 255:
            payload["exit_code"] = exit_code
        return result(SCHEMA, kind, "tool_finished", payload, obj, _ROOT,
                      event_id=event_id, occurred_at=timestamp,
                      nested=(("item", item, {"type", "id", "command", "input", "cwd", "status", "tool_name",
                                              "exit_code", "duration_ms", "aggregated_output"}),))
    if kind == "error" or kind == "turn.failed":
        code = obj.get("error_code")
        if code in ("quota_exceeded", "rate_limit"):
            return result(SCHEMA, kind, "quota_error", {"source_code": str(code)}, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp)
        if code in ("unauthorized", "authentication"):
            return result(SCHEMA, kind, "auth_error", {"source_code": str(code)}, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp)
        return result(SCHEMA, kind, "transport_error", {"source_code": "provider_error"}, obj, _ROOT,
                      event_id=event_id, occurred_at=timestamp)
    if kind in ("thread.started", "turn.started", "item.updated"):
        return ParseResult("ignored", "non_activity_event", SCHEMA, str(kind))
    return ParseResult("unsupported", "unknown_event_type", SCHEMA, "unsupported")


def normalize(raw: bytes | str) -> tuple[ParseResult, ...]:
    return (_normalize_one(raw),)


__all__ = ["normalize"]
