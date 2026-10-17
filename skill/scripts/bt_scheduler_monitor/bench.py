"""Deterministic, offline SQLite benchmark for the M4 monitor."""
from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from .contracts import ExecutionOutputFrame, NormalizedEvent, ProcessIdentity
from .retention import apply_retention
from .store import MonitorStore, SourceCursor
from .stream import BoundedFrameQueue

FIXTURE_REVISION = "scheduler-monitor-fixtures-v1"


def _sampled_peak_rss_kib(proc_status: Path = Path("/proc/self/status")) -> int:
    """Read Linux's peak RSS directly; fall back to getrusage on other platforms."""
    try:
        for line in proc_status.read_text(encoding="ascii").splitlines():
            if line.startswith("VmHWM:"):
                fields = line.split()
                if len(fields) == 3 and fields[2] == "kB" and fields[1].isdigit():
                    return int(fields[1])
                break
    except OSError:
        pass
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes; Linux and the other supported Unix platforms report KiB.
    return int(peak / 1024) if sys.platform == "darwin" else int(peak)


def _frame(agent: int, sequence: int) -> ExecutionOutputFrame:
    execution = f"fixture-execution-{agent}"
    stamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return ExecutionOutputFrame("1.0.0", f"fixture-run-{agent}", 1, f"fixture-task-{agent}",
        f"fixture-attempt-{agent}", execution, ProcessIdentity("fixture", "fixture-boot", agent + 1,
        1000 + agent), "codex", "stdout", sequence, sequence * 32, stamp, b"fixture heartbeat",
        profile_id="fixture-profile", model="fixture-model", received_monotonic_ns=time.monotonic_ns(),
        host_boot_id="fixture-boot")


def _event(frame: ExecutionOutputFrame) -> NormalizedEvent:
    return NormalizedEvent(
        "1.0.0", f"sha256:{int(frame.execution_id.rsplit('-', 1)[1]):04x}{frame.sequence:060x}",
        "fixture-jsonl/1", "1.0.0", frame.run_id, frame.plan_revision, frame.task_id, frame.attempt_id,
        frame.execution_id, frame.process_identity, frame.provider, frame.profile_id, frame.model,
        "heartbeat", "heartbeat", frame.received_at, frame.stream, frame.sequence, frame.offset_bytes,
        (("status", "started"),), "reported", received_monotonic_ns=frame.received_monotonic_ns,
        host_boot_id=frame.host_boot_id)


def run_benchmark(concurrency: int, fixtures: Path) -> dict[str, object]:
    if concurrency != 3:
        raise ValueError("the approved resource baseline requires exactly three simulated agents")
    if not fixtures.is_dir():
        raise ValueError("fixture directory does not exist")
    fixture_manifest = fixtures / "manifest.json"
    manifest = json.loads(fixture_manifest.read_text(encoding="utf-8"))
    if manifest.get("revision") != FIXTURE_REVISION:
        raise ValueError("fixture revision is unsupported")
    count = manifest["events_per_agent"]
    if type(count) is not int or not 1 <= count <= 100_000:
        raise ValueError("events_per_agent must be within 1..100000")
    cpu_start = time.process_time()
    latencies: list[float] = []
    queue = BoundedFrameQueue()
    enqueued_at: dict[str, int] = {}
    enqueued_at_lock = threading.Lock()
    producers_done = threading.Event()
    consumer_started = threading.Event()
    max_queue_frames = max_queue_bytes = 0
    consumer_active_during_production = False
    with tempfile.TemporaryDirectory(prefix="m4-bench-") as directory:
        path = Path(directory) / "monitor.sqlite3"
        store = MonitorStore(path)

        def simulate(agent: int) -> int:
            completed = 0
            for sequence in range(count):
                frame = _frame(agent, sequence)
                key = frame.execution_id + ":" + str(sequence)
                with enqueued_at_lock:
                    enqueued_at[key] = time.perf_counter_ns()
                if not queue.put(frame):
                    with enqueued_at_lock:
                        enqueued_at.pop(key, None)
                    continue
                completed += 1
            return completed

        def consume() -> int:
            nonlocal consumer_active_during_production
            queried = 0
            consumer_started.set()
            while not producers_done.is_set() or queue.peek_frame() is not None:
                frame = queue.peek_frame()
                if frame is None:
                    producers_done.wait(0.001)
                    continue
                item = _event(frame)
                cursor = SourceCursor(frame.execution_id, frame.stream, frame.host_boot_id,
                                      frame.sequence, frame.offset_bytes)
                queue.persist_event(store, frame, item, cursor)
                found = store.get_event(item.event_id)
                if found != item:
                    raise RuntimeError("fixture event did not round-trip from SQLite")
                key = frame.execution_id + ":" + str(frame.sequence)
                with enqueued_at_lock:
                    enqueued = enqueued_at.pop(key, None)
                if enqueued is None:
                    raise RuntimeError("queued frame has no producer timestamp")
                latencies.append((time.perf_counter_ns() - enqueued) / 1_000_000)
                consumer_active_during_production = consumer_active_during_production or not producers_done.is_set()
                queried += 1
            return queried

        wall_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency + 1) as executor:
            consumer = executor.submit(consume)
            consumer_started.wait()
            producers = [executor.submit(simulate, agent) for agent in range(concurrency)]
            try:
                queued_frames = sum(producer.result() for producer in producers)
            finally:
                producers_done.set()
            queried = consumer.result()
        max_queue_frames = queue.max_frames_observed
        max_queue_bytes = queue.max_bytes_observed
        elapsed = max(time.perf_counter() - wall_start, 1e-9)
        cpu_seconds = time.process_time() - cpu_start
        db_bytes = path.stat().st_size if path.exists() else 0
        wal_path = Path(str(path) + "-wal")
        wal_bytes_before_retention = wal_path.stat().st_size if wal_path.exists() else 0
        retention = apply_retention(path)
        db_bytes_after = path.stat().st_size if path.exists() else 0
        wal_bytes_after = wal_path.stat().st_size if wal_path.exists() else 0
        dropped_ranges = [gap.__dict__ for gap in queue.pending_gaps()]
        max_rss = _sampled_peak_rss_kib()
    return {
        "schema_version": "1.0.0", "environment": {"python": platform.python_version(),
            "platform": platform.platform(), "cpu_count": os.cpu_count()},
        "fixture_revision": manifest["revision"], "fixture_manifest": manifest,
        "matrix_execution": "The unittest suites run matrix assertions; three producer threads feed a concurrent bounded-queue consumer that persists and queries SQLite.",
        "consumer_active_during_production": consumer_active_during_production,
        "simulated_agents": concurrency,
        "attempts": concurrency, "events": queued_frames, "queries": queried,
        "elapsed_seconds": elapsed, "attempts_per_second": concurrency / elapsed,
        "events_per_second": queued_frames / elapsed, "max_queue_frames": max_queue_frames,
        "max_queue_bytes": max_queue_bytes, "dropped_ranges": dropped_ranges,
        "frame_to_query_latency_ms": {"p50": statistics.median(latencies),
            "p95": sorted(latencies)[max(0, int(len(latencies) * .95) - 1)]},
        "cpu_seconds": cpu_seconds, "sampled_peak_rss_kib": max_rss,
        "database_bytes_before_retention": db_bytes,
        "wal_bytes_before_retention": wal_bytes_before_retention,
        "database_bytes_after_retention": db_bytes_after, "wal_bytes_after_retention": wal_bytes_after,
        "retention": {"deleted_events": retention.deleted_events,
            "deleted_incidents": retention.deleted_incidents,
            "compacted_samples": retention.compacted_samples,
            "deleted_aggregates": retention.deleted_aggregates,
            "measured_bytes": retention.measured_bytes, "storage_pressure": retention.storage_pressure},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--concurrency", type=int, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = run_benchmark(args.concurrency, args.fixtures)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"report": str(args.report), "events": report["events"],
                      "events_per_second": report["events_per_second"],
                      "p95_ms": report["frame_to_query_latency_ms"]["p95"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
