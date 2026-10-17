"""Claude stream-json fixture normalizer."""
from __future__ import annotations

from . import ParseResult, decode_line, digest_json, result, safe_tool_label

SCHEMA = "claude-stream-json/1"
_ROOT = {"type", "subtype", "message", "result", "usage", "is_error", "total_cost_usd", "num_turns",
         "session_id", "uuid", "timestamp", "error_code", "stop_reason", "terminal_reason"}
_USAGE_FIELDS = {"input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
                 "server_tool_use", "service_tier", "cache_creation", "iterations", "speed", "fallback_credit"}


def _normalize_one(raw: bytes | str) -> ParseResult | tuple[ParseResult, ...]:
    obj, failure = decode_line(raw, SCHEMA)
    if failure:
        return failure
    assert obj is not None
    kind = obj.get("type")
    if kind == "assistant":
        message = obj.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            return ParseResult("malformed", "invalid_assistant_content", SCHEMA)
        events: list[ParseResult] = []
        for block_index, block in enumerate(content):
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "tool_use":
                name = block.get("name")
                args = block.get("input", {})
                try:
                    byte_count, digest = digest_json(args)
                except (ValueError, TypeError, UnicodeError, RecursionError):
                    return ParseResult("malformed", "invalid_tool_input", SCHEMA)
                payload: dict[str, object] = {"tool_label": safe_tool_label(name), "argument_bytes": byte_count,
                                              "argument_digest": digest}
                events.append(result(SCHEMA, str(kind), "tool_started", payload, obj, _ROOT | {"message"},
                                    event_id=_block_event_id(obj.get("uuid"), block_index),
                                    occurred_at=obj.get("timestamp"),
                                    nested=(("message", message, {"role", "content", "model", "stop_reason", "usage"}),)))
            if block_type == "text" and isinstance(block.get("text"), str):
                text = block["text"]
                events.append(result(SCHEMA, str(kind), "message_delta", {"message_count": 1,
                                    "byte_count": len(text.encode("utf-8", "replace"))}, obj, _ROOT | {"message"},
                                    event_id=_block_event_id(obj.get("uuid"), block_index),
                                    occurred_at=obj.get("timestamp"),
                                    nested=(("message", message, {"role", "content", "model", "stop_reason", "usage"}),)))
        return tuple(events) if events else (ParseResult("ignored", "no_supported_content", SCHEMA),)
    if kind == "result" and obj.get("is_error") is True:
        code = obj.get("error_code") or obj.get("subtype")
        nested = (("usage", obj["usage"], _USAGE_FIELDS),) if isinstance(obj.get("usage"), dict) else ()
        if code in ("rate_limit", "quota_exceeded"):
            return result(SCHEMA, "result", "quota_error", {"source_code": str(code)}, obj, _ROOT,
                          event_id=obj.get("uuid"), occurred_at=obj.get("timestamp"), nested=nested)
        if code in ("authentication", "unauthorized"):
            return result(SCHEMA, "result", "auth_error", {"source_code": str(code)}, obj, _ROOT,
                          event_id=obj.get("uuid"), occurred_at=obj.get("timestamp"), nested=nested)
        return result(SCHEMA, "result", "transport_error", {"source_code": "provider_error"}, obj, _ROOT,
                      event_id=obj.get("uuid"), occurred_at=obj.get("timestamp"), nested=nested)
    if kind == "result" and isinstance(obj.get("usage"), dict):
        usage = obj["usage"]
        value = usage.get("output_tokens")
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            return result(SCHEMA, "result", "usage_reported", {"metric_name": "output_tokens", "value": value,
                          "unit": "tokens", "source": "provider_reported", "sample_count": 1}, obj, _ROOT,
                          event_id=obj.get("uuid"), occurred_at=obj.get("timestamp"),
                          nested=(("usage", usage, _USAGE_FIELDS),))
    if kind in ("system", "result"):
        return ParseResult("ignored", "non_activity_event", SCHEMA)
    return ParseResult("unsupported", "unknown_event_type", SCHEMA, "unsupported")


def _block_event_id(value: object, index: int) -> object:
    return f"{value}:{index}" if isinstance(value, str) else None


def normalize(raw: bytes | str) -> tuple[ParseResult, ...]:
    parsed = _normalize_one(raw)
    return parsed if isinstance(parsed, tuple) else (parsed,)


__all__ = ["normalize"]
