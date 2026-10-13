"""Collect only designated benchmark-agent usage and public evaluation answers."""
from __future__ import annotations

import json
from pathlib import Path

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens", "total_tokens")


def parse_session(path: Path, targets: set[str]) -> dict | None:
    with path.open() as handle:
        first = json.loads(next(handle))
    meta = first.get("payload", {})
    agent = meta.get("agent_path")
    if first.get("type") != "session_meta" or agent not in targets:
        return None
    usage = None
    calls, final, models, records = [], [], [], []
    completed = False
    previous_total = None
    for line in path.read_text().splitlines():
        event = json.loads(line)
        payload = event.get("payload", {})
        if event["type"] == "turn_context":
            models.append({key: payload.get(key) for key in ("model", "effort", "reasoning_effort")})
        if event["type"] == "event_msg" and payload.get("type") == "task_complete":
            completed = True
        if event["type"] == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info")
            if info:
                usage = info["total_token_usage"]
                if usage != previous_total:
                    records.append(info["last_token_usage"])
                    previous_total = usage
        if event["type"] == "response_item":
            if payload.get("type") in ("custom_tool_call", "function_call", "tool_call"):
                calls.append({key: payload.get(key) for key in ("name", "input", "arguments")})
            if (payload.get("type") == "message" and payload.get("role") == "assistant"
                    and payload.get("phase") == "final_answer"):
                final.extend(item.get("text", "") for item in payload.get("content", [])
                             if item.get("type") == "output_text")
    if completed and usage:
        if usage["input_tokens"] + usage["output_tokens"] != usage["total_tokens"]:
            raise ValueError(f"Invalid total for {agent}")
        for key in FIELDS:
            if sum(record[key] for record in records) != usage[key]:
                raise ValueError(f"Inconsistent accumulated {key} for {agent}")
    answer = "\n".join(final)
    return {"agent": agent, "session_file": str(path), "completed": completed, "settings": models,
            "usage": usage, "uncached_input": usage["input_tokens"] - usage["cached_input_tokens"] if usage else None,
            "calls": calls, "call_count": len(calls), "records": records,
            "answer": answer, "answer_words": len(answer.split())}


def collect(folder: Path, targets: set[str]) -> dict:
    found = {}
    for path in folder.glob("*.jsonl"):
        result = parse_session(path, targets)
        if result:
            if result["agent"] in found:
                raise ValueError(f"Duplicate trial session: {result['agent']}")
            found[result["agent"]] = result
    return found


if __name__ == "__main__":
    import sys
    root = Path(__file__).resolve().parent
    targets = {"/root/" + item for item in sys.argv[1:]}
    found = collect(Path("/home/david/.codex/sessions/2026/10/12"), targets)
    (root / "metrics.json").write_text(json.dumps(found, indent=2, ensure_ascii=False))
    for name, result in found.items():
        (root / (name.rsplit("/", 1)[1] + "-response.md")).write_text(result["answer"])
        print(json.dumps({"agent": name, "completed": result["completed"], "usage": result["usage"],
                          "uncached_input": result["uncached_input"], "calls": result["call_count"]}))
