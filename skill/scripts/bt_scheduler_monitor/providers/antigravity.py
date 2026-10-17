"""Antigravity stream-json fixture normalizer."""
from __future__ import annotations

from . import ParseResult, decode_line, result, safe_tool_label

SCHEMA = "antigravity-stream-json/1"
_ROOT = {"event", "init", "step_update", "result", "timestamp", "event_id"}
_STEP_FIELDS = {"step_index", "state", "step_type", "text_delta", "usage", "duration_seconds", "tool_name"}
_USAGE_FIELDS = {"input_tokens", "output_tokens", "thinking_tokens", "cache_read_tokens", "total_tokens"}
_RESULT_FIELDS = {"conversation_id", "status", "response", "duration_seconds", "num_turns", "usage", "error_code",
                  "error"}


def _normalize_one(raw: bytes | str) -> ParseResult:
    obj, failure = decode_line(raw, SCHEMA)
    if failure:
        return failure
    assert obj is not None
    kind = obj.get("event")
    event_id = obj.get("event_id")
    timestamp = obj.get("timestamp")
    if kind == "init":
        return ParseResult("ignored", "initialization_event", SCHEMA, str(kind))
    if kind == "step_update":
        update = obj.get("step_update")
        if not isinstance(update, dict):
            return ParseResult("malformed", "invalid_step_update", SCHEMA)
        nested = (("step_update", update, _STEP_FIELDS),)
        if isinstance(update.get("usage"), dict):
            nested += (("step_update.usage", update["usage"], _USAGE_FIELDS),)
        state = update.get("state")
        step_type = update.get("step_type")
        delta = update.get("text_delta")
        if isinstance(delta, str) and delta:
            return result(SCHEMA, kind, "message_delta", {"message_count": 1,
                          "byte_count": len(delta.encode("utf-8", "replace"))}, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp, nested=nested)
        usage = update.get("usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
                return result(SCHEMA, kind, "usage_reported", {"metric_name": "total_tokens", "value": total,
                              "unit": "tokens", "source": "provider_reported", "sample_count": 1}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp, nested=nested)
        if step_type in ("tool", "tool_use"):
            label = update.get("tool_name")
            payload = {"tool_label": safe_tool_label(label)}
            event_type = "tool_finished" if state == "DONE" else "tool_started"
            return result(SCHEMA, kind, event_type, payload, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp,
                          nested=nested)
        return ParseResult("ignored", "step_without_activity", SCHEMA, str(kind))
    if kind == "result":
        final = obj.get("result")
        if not isinstance(final, dict):
            return ParseResult("malformed", "invalid_result", SCHEMA)
        status = final.get("status")
        usage = final.get("usage")
        nested = (("result", final, _RESULT_FIELDS),)
        if isinstance(usage, dict):
            nested += (("result.usage", usage, _USAGE_FIELDS),)
        if status in ("FAILURE", "ERROR"):
            code = final.get("error_code")
            if code in ("RESOURCE_EXHAUSTED", "QUOTA_EXCEEDED"):
                return result(SCHEMA, kind, "quota_error", {"source_code": str(code)}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp, nested=nested)
            if code in ("UNAUTHENTICATED", "PERMISSION_DENIED"):
                return result(SCHEMA, kind, "auth_error", {"source_code": str(code)}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp, nested=nested)
            return result(SCHEMA, kind, "transport_error", {"source_code": "provider_error"}, obj, _ROOT,
                          event_id=event_id, occurred_at=timestamp, nested=nested)
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
                return result(SCHEMA, kind, "usage_reported", {"metric_name": "total_tokens", "value": total,
                              "unit": "tokens", "source": "provider_reported", "sample_count": 1}, obj, _ROOT,
                              event_id=event_id, occurred_at=timestamp, nested=nested)
        return ParseResult("ignored", "result_without_usage", SCHEMA, str(kind))
    return ParseResult("unsupported", "unknown_event_type", SCHEMA, "unsupported")


def normalize(raw: bytes | str) -> tuple[ParseResult, ...]:
    return (_normalize_one(raw),)


__all__ = ["normalize"]
