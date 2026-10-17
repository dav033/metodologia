# Scheduler M4 monitor operations

M4 is an advisory observer. M1 owns authorization and task/attempt state; M3 owns process lifetime and output capture.
M4 cannot launch, stop, signal, retry, resume, or declare an attempt successful or dead. A quiet source is not proof
that its process exited.

## M1–M4 Scheduler owner integration

The supported Scheduler owner runtime (`scheduler-run` and `launch --scheduler`) always supplies a separate M4 store.
After each M1 step it calls `bt_scheduler_m4_wiring.drain_pending_streams()`, which drains one bounded batch for each
active M3 attempt through `Wiring.drain_stream(attempt_id, run_id)`. The adapter validates the M1 run identity and
commits normalized events and gaps before acknowledging queued frames. It also delivers the durable incident outbox
through M1 with a stable run-scoped claim token. No global poller or background ingestion loop is activated; the
owner polls every 0.1 seconds while M3 attempts can still create or write to a stream, then drains terminal output.
The M3 shim gives the owner a bounded 0.5-second reader-start grace after creating its FIFO. The adapter queue has no
restart-safe raw-frame spool.

The lower-level `bt_scheduler_executor_adapter.wire(..., monitor_store_path=PATH)` seam remains optional for isolated
tests and explicit custom compositions. Omitting M4 there leaves that custom M1–M3 composition unchanged; the
supported Scheduler owner does not omit it.

M2 can request route-scoped metric history through `MonitorRuntime.metric_snapshots_for_route()`; this reads M4
without changing it. The standard owner keeps the existing deterministic M2 routing policy and does not use that
optional history. M1 records only the versioned audit reference and remains authoritative for task and attempt state.

## Read-only SSH queries

The methodology command `bt-scheduler-monitor` only opens the M4 database in read-only mode. It emits one JSON object
per invocation; a nonzero exit code means the query failed. Run it on the scheduler host over SSH, using a disposable
fixture database when learning the interface or checking an upgrade:

```sh
ssh scheduler-host 'bt-scheduler-monitor status --store /srv/bitacora/fixtures/monitor.sqlite3'
ssh scheduler-host 'bt-scheduler-monitor activity --store /srv/bitacora/fixtures/monitor.sqlite3 --limit 20'
ssh scheduler-host 'bt-scheduler-monitor incidents --store /srv/bitacora/fixtures/monitor.sqlite3 --state open'
ssh scheduler-host 'bt-scheduler-monitor metrics --store /srv/bitacora/fixtures/monitor.sqlite3 --limit 25'
```

The store argument is required. `events`, `activity`, `incidents`, and `metrics` accept a positive `--limit` capped at
100; `events` and `activity` can filter by `--execution-id`. `incidents` accepts `--state open|resolved`. Query
commands do not run retention, migrations, delivery, provider refreshes, or process controls. Use a separately made
fixture copy for operational rehearsal; never point a fixture check at a live database.

Typical errors are stable JSON on stderr: `M4_INVALID_ARGUMENT` (exit 2) or `M4_STORE_ERROR` (exit 3). A missing,
corrupt, locked, or unreadable store is an error, never an empty successful result.

## Contracts and compatibility

| Boundary | Contract | Compatibility behavior |
| --- | --- | --- |
| M3 stream frame → M4 | `ExecutionOutputFrame` 1.0.0; FIFO data ≤3,840 bytes, whole wire frame ≤4,096 bytes | Missing M3 stream summary means completeness is `unknown`; invalid FIFO framing/schema raises a visible adapter error and is not normalized. |
| M4 records | normalized event, incident, metric sample schema 1.0.0 | Unknown provider fields are counted/digested, not copied; unsupported provider event shapes produce parser gap metadata. |
| M4 incident → M1 | `incident_observed` contract 1.2.0 | M1 without declared 1.2 capability leaves the durable outbox pending and unclaimed. |
| M4 metrics → M2 | validated metric snapshot schema 1.0.0 | Optional read-only history; missing snapshots leave M2's existing policy in effect. |
| Gemini | fixture parser only | Gemini CLI is not wired as an M3 launch provider and must not be treated as supported live input. |

The M4 store is a separate project-owned SQLite WAL database; it is not an M1 or M3 database. Store path ownership,
schema migration, and write lifecycle belong to the scheduler owner, not this query command. M4 retains at most 100
rows per query (and activity reconstruction is capped at 1,000 events), stream frames at 3,840 data bytes, and
evidence excerpts at 4 KiB. The approved 512 MiB database-plus-WAL value is a hard ceiling. Before each ordinary
durable mutation, M4 measures the database and WAL and reserves 256 KiB for the bounded transaction, page splits, and
WAL growth. Retention and compaction process up to four records per transaction, reserve up to 64 KiB from the
remaining capacity, and verify projected database-plus-WAL size against the hard ceiling before commit. If even one
bounded retention batch cannot fit, cleanup stops and storage is reported as degraded; M4 never raises the ceiling or
changes the journal mode to make room. Cleanup vacuums when the normal write reserve is exhausted or a prior attempt
left free pages, provided the maintenance reserve fits, the database filesystem has up to twice the database size free,
and each SQLite temporary-directory candidate has at least one database size plus the reserve free. The isolated M4
package does not read environment variables: callers must pass the complete list of writable SQLite temporary
directories through `apply_retention(..., sqlite_temp_dirs=...)`, including any configured `SQLITE_TMPDIR`. The default
empty list safely defers VACUUM; if a declared candidate lacks room, M4 defers VACUUM and reports pressure.
Open incidents and pending or claimed outbox entries are never evicted to satisfy the limit. If the measured size plus
reserve would exceed the configured ceiling, an ordinary write raises `StoreError` with `storage_pressure`; it does not
advance a source cursor or acknowledge queued input.
`max_store_bytes` is injectable
for deterministic tests and defaults to 512 MiB. Retention is 90 days for event detail, 365 days for resolved incident
detail, and 730 days for daily aggregates.

## Gaps, pressure, and recovery

M3's stream summary reports sent/dropped byte counts and ranges to the adapter; the operator CLI does not expose that
summary. Adapter queue overflow, source drops, truncation, and decoder failures produce bounded gap metadata in the
current process. Pending gap metadata is capped at 10,000 entries across all executions. At that limit, the reader
keeps the next FIFO frame buffered and raises `GapCapacityError`; persist pending gaps and retry the drain. The M3
summary tracker is also capped at 10,000 ranges. `M3StreamAdapter.persist_gaps()` records each observed range with an idempotency key, then removes it
from the queue only after the SQLite transaction commits. Busy/full errors leave the gap queued for retry. The
normalized frame consumer uses `persist_frame_event()`: it peeks without releasing queue capacity and acknowledges
only after the event/cursor transaction commits. `MonitorStore.list_stream_gaps()` reads durable ranges after restart;
operator status reports `stream_status=degraded` when any are present and `unknown` otherwise. A gap means some stream
evidence is unavailable; M4 does not persist raw M3 artifacts. A changed host boot identity must not be silently
joined to unrelated process output.

`apply_retention()` prunes eligible details, compacts aggregates, checkpoints the WAL, and persists a measured health
state. It must run successfully for `status` to show that state; a read-only query never performs maintenance. If
protected data prevents recovery below the ceiling, status remains degraded and new mutations remain rejected.
`append_event()` commits the event and source cursor in one transaction. On a capacity, SQLite busy/full, or write
error it raises `StoreError`, and that transaction does not advance the durable cursor. The caller must retain the
uncommitted event for retry and must not claim it was persisted. `persist_frame_event()` retains the frame in its
bounded queue on write failure; `persist_gaps()` does the same for a loss range. There is no raw-frame spool: frames
still in the adapter queue can be lost on process restart. After restart, `drain()` reconstructs known gaps from M3's
read-only dropped-range summary; persist those ranges before removing them from memory. Gap replay is idempotent even
if recovery produces a later timestamp. If M3 cannot prove continuity, completeness remains unknown. SQLite errors
remain visible; neither ingestion nor delivery success is fabricated. Pending M1 outbox work is retried with stable
idempotency keys after the store and compatible M1 contract are available.

The reproducible three-agent baseline is generated offline with `python3 -m bt_scheduler_monitor.bench --concurrency 3
--fixtures tests/fixtures/scheduler-monitor --report /tmp/req-017-m4-benchmark.json`. It uses metadata-only events and
the bounded queue → normalized event → SQLite commit → ACK path; it does not launch provider processes. Its report
includes environment, fixture revision, attempts/events per second, actual peak queue occupancy and drops,
frame-to-query latency, sampled RSS, CPU, database/WAL size, and retention results. Queue capacity is 10,000 frames /
16 MiB. Across 14 recorded queue runs on Linux 7.2.6 x86_64, Python 3.14.7 and 16 logical CPUs, each run processed 300
metadata-only events: throughput was 823.60–961.40 events/s, p50 latency 155.35–202.57 ms, p95 latency
289.45–339.40 ms, CPU 0.309–0.361 s and peak RSS 26,344–26,640 KiB. Every run peaked at 300 queued frames / 5,100
bytes with zero drops; the database was 503,808 bytes before retention and 536,576 bytes after schema/health
initialization, with zero WAL bytes after checkpointing. The runs varied materially in speed, so the initial same-host
fixture budget rounds beyond the slowest or highest observed edge: throughput ≥800 events/s, p95 ≤350 ms, CPU ≤0.38 s,
RSS ≤27,000 KiB, and zero loss for this 300-event fixture. The queue consumer was not active while producers emitted
events, so these measurements cover producer burst and consumer drain, not sustained SQLite contention. These are
synthetic host-local budgets, not production SLOs; recalculate them when the workload or host changes.

Only matching M3 process identity plus terminal observation can corroborate process death. Silence, a missed
heartbeat, a missing FIFO reader, or a disconnected provider remains an observation/gap and never triggers process
control. Preserve the M4 database for audit/export before any owner-managed recovery or schema migration.

### Offline archive and recovery candidate

Stop every M4 writer before exporting. `bt-scheduler-monitor-recovery archive --store STORE --archive ARCHIVE
--manifest MANIFEST` copies the SQLite database and any WAL sidecars into a temporary snapshot, verifies that the
source bytes did not change during the copy, and publishes a standalone full archive and bounded JSON manifest
without replacing either destination. Database and manifest artifacts are owner-only (`0600`).
`verify-archive --archive ARCHIVE --manifest MANIFEST` checks the SHA-256,
SQLite integrity, M4 schema identity, table counts, and digests for open incidents and undelivered M1 outbox rows.
The manifest contains counts and hashes, not event bodies or provider output.

`prepare-candidate --archive ARCHIVE --archive-manifest MANIFEST --candidate CANDIDATE
--candidate-manifest CANDIDATE_MANIFEST --sqlite-temp-dir DIR` builds from the verified archive, applies the existing
retention rules only to a disposable copy, then runs the recovery VACUUM after checking free space in the candidate
directory and every explicitly supplied SQLite temporary directory. Repeat `--sqlite-temp-dir` for the complete
caller-owned list; no environment variable or implicit SQLite temp path is read. The candidate records the active
512 MiB cap (or an explicitly supplied test cap), must leave the existing write reserve, and is rejected if open
incidents or unacknowledged/claimed outbox records differ from the archive. No command replaces or activates the
candidate: inspect and verify it before an operator-managed restore. An existing archive, manifest, or candidate
path is never overwritten.

```sh
bt-scheduler-monitor-recovery archive --store ~/.local/share/bitacora/m4.sqlite3 \
  --archive /path/to/recovery/m4.sqlite3 --manifest /path/to/recovery/m4.json
bt-scheduler-monitor-recovery verify-archive --archive /path/to/recovery/m4.sqlite3 \
  --manifest /path/to/recovery/m4.json
bt-scheduler-monitor-recovery prepare-candidate --archive /path/to/recovery/m4.sqlite3 \
  --archive-manifest /path/to/recovery/m4.json --candidate /path/to/recovery/candidate.sqlite3 \
  --candidate-manifest /path/to/recovery/candidate.json --sqlite-temp-dir /path/to/sqlite-temp
bt-scheduler-monitor-recovery verify-candidate --candidate /path/to/recovery/candidate.sqlite3 \
  --manifest /path/to/recovery/candidate.json
```
