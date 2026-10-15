"""Private JSON-lines worker run only inside the pinned, offline Laya environment."""
from __future__ import annotations

import argparse
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

MAX_MESSAGE_BYTES = 32_768
MAX_OPTIONS = 8
CHECKPOINTS = {
    "english": ("55cf4c4ebb4ebe31b2550e8bdf3bd21b99753851",
                "891102d372688fc2a094dac56a384bc537b87c63f21f9f3dac0be2b7cbc8d86c"),
    "multilingual": ("e4e9ddf21a7b1903b7acffd8814ad4307bf63a67",
                     "9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204"),
    "typed-decisions": ("1a793eb568e6718f15941d08f85432581df534e3",
                        "4fa56de72383a9d3efa9cfa78955733c81b9fc8067a587ca4beb82c78107a24e"),
}


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _invalid_constant(_value: str) -> None:
    raise ValueError("non-finite JSON number")


def _select_device(requested: str, cuda_available: bool) -> str:
    if requested not in {"auto", "cpu", "cuda"} or not isinstance(cuda_available, bool):
        raise ValueError("invalid Laya device selection")
    if requested == "auto":
        return "cuda" if cuda_available else "cpu"
    return requested


def _verify_memory_boundary(expected_limit: int, *, cgroup_file: Path = Path("/proc/self/cgroup"),
                            cgroup_root: Path = Path("/sys/fs/cgroup")) -> tuple[int, int]:
    """Refuse inference unless the worker is inside a finite, no-swap cgroup memory boundary."""
    if not isinstance(expected_limit, int) or isinstance(expected_limit, bool) or expected_limit <= 0:
        raise ValueError("invalid worker memory limit")
    entries = cgroup_file.read_text(encoding="ascii").splitlines()
    unified = [line.partition("::")[2] for line in entries if line.startswith("0::")]
    if len(unified) != 1 or ".." in Path(unified[0]).parts:
        raise ValueError("worker must run in a unified cgroup")
    root = cgroup_root.resolve()
    scope = (root / unified[0].lstrip("/")).resolve()
    try:
        scope.relative_to(root)
        memory_limit = (scope / "memory.max").read_text(encoding="ascii").strip()
        swap_limit = (scope / "memory.swap.max").read_text(encoding="ascii").strip()
    except (OSError, ValueError) as exc:
        raise ValueError("worker cgroup memory boundary is unavailable") from exc
    if memory_limit == "max" or swap_limit == "max":
        raise ValueError("worker cgroup memory and swap must be finite")
    actual_limit, actual_swap = int(memory_limit), int(swap_limit)
    if actual_limit > expected_limit or actual_swap != 0:
        raise ValueError("worker cgroup memory boundary is weaker than configured")
    return actual_limit, actual_swap


def _is_cuda_oom(error: Exception, torch: Any) -> bool:
    out_of_memory = getattr(torch.cuda, "OutOfMemoryError", None)
    return (isinstance(out_of_memory, type) and isinstance(error, out_of_memory)) or \
        "out of memory" in str(error).casefold()


def _validate_request(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"request_id", "state", "questions", "lang"}:
        raise ValueError("invalid request shape")
    if not isinstance(value["request_id"], int) or isinstance(value["request_id"], bool) or value["request_id"] < 1:
        raise ValueError("invalid request id")
    state = value["state"]
    if not isinstance(state, (str, dict, list)):
        raise TypeError("invalid state")
    questions = value["questions"]
    if not isinstance(questions, dict) or len(questions) != 1:
        raise ValueError("one typed question is required")
    question = next(iter(questions.values()))
    if not isinstance(question, dict) or question.get("type") != "choice" or \
            not isinstance(question.get("criteria"), dict) or not 2 <= len(question["criteria"]) <= MAX_OPTIONS or \
            any(not isinstance(key, str) or not key or not isinstance(label, str) for key, label in
                question["criteria"].items()) or not isinstance(question.get("instructions"), str):
        raise ValueError("invalid choice question")
    if value["lang"] not in {"en", "es"}:
        raise ValueError("unsupported language")
    return value


def _reply(request_id: int | None, *, result: dict[str, Any] | None = None,
           metrics: dict[str, Any] | None = None, ok: bool = True) -> None:
    body = {"request_id": request_id, "ok": ok}
    if result is not None:
        body["result"] = result
    if metrics is not None:
        body["metrics"] = metrics
    sys.stdout.buffer.write(json.dumps(body, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n")
    sys.stdout.buffer.flush()


def run(root: Path, checkpoint: str, device: str, memory_limit_bytes: int) -> int:
    cgroup_memory_limit, cgroup_swap_limit = _verify_memory_boundary(memory_limit_bytes)
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import torch
    from laya import Agent

    torch.set_num_threads(2)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        pass
    _revision, digest = CHECKPOINTS[checkpoint]
    model_path = root / "checkpoints" / checkpoint
    selected_device = _select_device(device, torch.cuda.is_available())
    agent = None
    while True:
        raw = sys.stdin.buffer.readline(MAX_MESSAGE_BYTES + 1)
        if not raw:
            break
        request_id = None
        try:
            if len(raw) > MAX_MESSAGE_BYTES or not raw.endswith(b"\n"):
                raise ValueError("oversized request")
            request = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_invalid_constant)
            request = _validate_request(request)
            request_id = request["request_id"]
            load_ms = 0.0
            peak_load_allocated = peak_load_reserved = 0
            fallback_reason = None
            if agent is None:
                if selected_device == "cuda":
                    torch.cuda.reset_peak_memory_stats()
                started = time.perf_counter()
                try:
                    agent = Agent(model_id_or_path=str(model_path), device=selected_device,
                                  expected_sha256={"model.safetensors": digest})
                except Exception as error:
                    if selected_device != "cuda" or not _is_cuda_oom(error, torch):
                        raise
                    import gc
                    gc.collect()
                    torch.cuda.empty_cache()
                    fallback_reason = "cuda_out_of_memory"
                    selected_device = "cpu"
                    agent = Agent(model_id_or_path=str(model_path), device=selected_device,
                                  expected_sha256={"model.safetensors": digest})
                load_ms = (time.perf_counter() - started) * 1000
                if selected_device == "cuda" and agent.device.type != "cuda":
                    fallback_reason = "cuda_placement_fallback"
                    selected_device = "cpu"
                if agent.device.type == "cuda":
                    peak_load_allocated = torch.cuda.max_memory_allocated(agent.device)
                    peak_load_reserved = torch.cuda.max_memory_reserved(agent.device)
            if agent.device.type == "cuda":
                torch.cuda.reset_peak_memory_stats(agent.device)
            started = time.perf_counter()
            try:
                result = agent.system_one(request["state"], request["questions"], lang=request["lang"],
                                          max_len=1536, head_max_len=512)
            except Exception as error:
                if agent.device.type != "cuda" or not _is_cuda_oom(error, torch):
                    raise
                agent.__exit__(None, None, None)
                agent = None
                import gc
                gc.collect()
                torch.cuda.empty_cache()
                fallback_reason = "cuda_out_of_memory"
                selected_device = "cpu"
                fallback_started = time.perf_counter()
                agent = Agent(model_id_or_path=str(model_path), device=selected_device,
                              expected_sha256={"model.safetensors": digest})
                load_ms += (time.perf_counter() - fallback_started) * 1000
                result = agent.system_one(request["state"], request["questions"], lang=request["lang"],
                                          max_len=1536, head_max_len=512)
            if agent.device.type == "cuda":
                torch.cuda.synchronize(agent.device)
            inference_ms = (time.perf_counter() - started) * 1000
            metrics = {
                "load_ms": round(load_ms, 3),
                "inference_ms": round(inference_ms, 3),
                "device": str(agent.device),
                "requested_device": device,
                "device_fallback": fallback_reason,
                "memory_limit_bytes": memory_limit_bytes,
                "cgroup_memory_limit_bytes": cgroup_memory_limit,
                "cgroup_swap_limit_bytes": cgroup_swap_limit,
                "cuda_load_peak_allocated_bytes": peak_load_allocated,
                "cuda_load_peak_reserved_bytes": peak_load_reserved,
                "cuda_inference_peak_allocated_bytes": torch.cuda.max_memory_allocated(agent.device)
                if agent.device.type == "cuda" else 0,
                "cuda_inference_peak_reserved_bytes": torch.cuda.max_memory_reserved(agent.device)
                if agent.device.type == "cuda" else 0,
                "rss_peak_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                "usage": result.get("usage", {}) if isinstance(result, dict) else {},
            }
            _reply(request_id, result=result, metrics=metrics)
        except Exception:  # noqa: BLE001 - contain model/library failures and return a stable, redacted worker error.
            _reply(request_id, ok=False)
            if request_id is not None:
                break
    if agent is not None:
        agent.__exit__(None, None, None)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--checkpoint", choices=tuple(CHECKPOINTS), required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--memory-limit-bytes", type=int, required=True)
    args = parser.parse_args()
    try:
        return run(args.root, args.checkpoint, args.device, args.memory_limit_bytes)
    except Exception:  # noqa: BLE001 - keep third-party startup diagnostics and paths out of the protocol response.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
