# REQ-017 — Reuse, adaptation and compatibility inventory

Checked against the live `skill` checkout on 2026-10-15. Source code and tests are the authority for local behavior; CLI versions and `--help` were inspected without launching an agent task. No provider API or quota was used.

## Current modules and intended treatment

| Existing component | Current responsibility and evidence | M4 treatment |
|---|---|---|
| `bt_scheduler_core` | M1 owns authorized task/attempt state and its transactional audit. `contracts.py` defines Event v1.1 and lifecycle/heartbeat kinds; `events.py` applies event behavior; `scheduler.py` exposes pending orders, status snapshots, audit and ingest. SQLite uses WAL and append-only audit records. | **Adapt additively in T9.** Add a versioned `incident_observed` audit fact and idempotency key. It records an M4 reference but cannot alter task or attempt state. Keep the existing lifecycle event contract and validation intact. |
| `bt_scheduler_adapter.py` | The methodology boundary stores M1 state under the scheduler state directory and translates existing scheduler calls. | **Adapt in T9** with a narrow incident-reference port. M4 does not write M1 SQLite files directly. |
| `bt_scheduler_decision` / `bt_scheduler_decision_adapter.py` | M2 reads agent/profile/subscription/event catalogs and historical usage inputs, builds routing decisions and records its own route-choice ledger. `RouteHistory` includes duration/token samples and medians; M2 only routes work that M1 validates. | **Adapt read-only in T10.** Add metric snapshots with source, unit, quality, sample count and comparability key. Do not make M4 an M2 decision owner or mix route-choice records with provider observations. |
| `bt_scheduler_executor` / `bt_scheduler_executor_adapter.py` | M3 starts and supervises provider processes through a detached `shim`, owns process identity and bounded output artifacts, and sends lifecycle `CoreEvent`s to M1. The current adapter's `CoreEventSink` calls `scheduler.ingest`; a slow sink can delay the supervisor thread. | **Adapt the stream boundary in T2 only.** An in-process M4 queue cannot receive from the detached shim. Keep lifecycle delivery separate; use a private per-execution POSIX FIFO with `O_NONBLOCK` frames no larger than `PIPE_BUF`, explicit offsets/gaps and an M3-owned stream summary. Never enqueue M4 work on the direct lifecycle callback. M3 continues to own raw output artifacts and process signaling. |
| `bt_scheduler_executor/shim.py` | Current `Popen` wiring merges stderr into stdout. The shim reads 65,536-byte chunks, writes a bounded private `output.log`/`output.tail`, and reports total/dropped bytes. Config includes 10,000 pending lifecycle events, delivery batches of 100, 30-second heartbeat, 0.5-second poll and concurrency 2. | **Adapt in T2** to preserve independent stdout/stderr labels while keeping existing artifact limits and M3 behavior. A bounded nonblocking stream queue reports dropped offsets/counts; pipes continue draining when M4 is slow. Measure before setting final CPU/RSS limits. |
| `bt_runprompt.py`, `bt_driver.py`, `bt_agy.py` | M3 routes Claude, Codex and Antigravity (`agy`). Claude currently requests `stream-json`; Codex currently receives plain text and the normalizer only extracts textual total usage; Antigravity uses stream JSON and has fixture coverage. M3 does not route Gemini. | **Adapt CLI invocation and normalizers in T3** behind the M4 stream contract. Codex JSONL support requires an explicit M3 argv change. Gemini remains fixture-only until M3 adds a supported route. `agy` is absent locally, so use a simulator. |
| Legacy `bt_monitor.py`, `RUN.json`, `bt_runstate.py` | The legacy monitor is an interactive session monitor for legacy run state. Legacy `bt_runstate.heartbeat` records PID/machine/time. M1 also emits a read projection `RUN.projection.json`, but no M4 monitor consumer was found. | **Do not reuse as M4 state or rewrite.** Provide a new headless status/query adapter against M1/M3 read APIs. Preserve existing legacy bytes and behavior. |
| Legacy `bt_events.py` | `record_attempt` appends idempotent monthly JSONL history for legacy attempts, including duration/result/usage. M3 attempts are not mirrored there today. | **Read-only compatibility input for historical M2 data only.** Do not make it the M4 cursor, incident store or delivery outbox; it has no M4 restart cursor or transactional outbox contract. |
| `bt_trace` | Tracks requirements/decisions/commits, not process telemetry. | **Do not extend for runtime observations.** Keep M4 operational history in its own store. |
| `bt_subscriptions`, `bt_quota_live`, `bt_relay` | Subscription catalogs and provider-facing live quota reads/launch transport. `bt_quota_live.read_all_live` performs provider-facing quota refreshes with caching. | **Do not call quota refresh or relay from M4.** Use M2's already available catalog labels only through read-only adapters; never read credentials. |

## Existing fixture coverage and gaps

| Source | Existing evidence | Planning consequence |
|---|---|---|
| Claude Code stream JSON | `skill/scripts/tests/test_telemetry.py` and `test_telemetry_v2.py` exercise local stream-json samples. | Reuse fixture shapes, then map only an allowlisted subset to M4 events. Do not persist message text or tool arguments. |
| Antigravity | `skill/scripts/tests/test_agy.py` and M3 fake-provider tests cover parser/argv conventions; `agy` and `antigravity` executables are absent from local `PATH`. | Use sanitized simulator fixtures. A live Antigravity smoke remains unavailable unless the CLI is installed and later authorized. |
| Codex CLI | M3 currently launches plain text; installed Codex help documents `codex exec --json`, but no local JSONL fixture was found. | T3 adds fixtures based on the versioned public event contract. A fixture is not evidence of a locally observed live event. |
| Gemini CLI | Installed CLI has `--output-format stream-json`, but M3 has no Gemini route and no M4 fixture was found. | Add a clearly labeled parser fixture only. Do not claim M3 compatibility or expose Gemini as launchable. |
| M3 process/lifecycle | `bt_scheduler_executor/tests` covers shim, start, workspace and recovery; current outbox/replay behavior covers lifecycle events, not provider stream frames. | T2 adds bounded stream-frame tests without weakening lifecycle tests. T12 runs focused integration suites after implementation. |

## Local CLI inventory (2026-10-15)

| CLI | Local version / availability | Relevant local help | M4 planning status |
|---|---|---|---|
| Claude Code | `2.1.300` | Supports `--output-format stream-json` and `--include-partial-messages` for print/stream-json modes. | Existing M3 route; fixtures first. |
| Codex CLI | `0.162.1` | `codex exec --json` emits JSONL. Current M3 argv does not enable it. | Existing M3 route; versioned JSONL support requires a planned argv adaptation. |
| Gemini CLI | `0.63.0` | `--output-format stream-json` is available. | Installed, but not routed by M3; fixture-only. |
| Antigravity | `agy` / `antigravity` not found on `PATH` | Repository code/tests describe stream-json argv; no local executable to query. | Simulator-only; do not run. |

Local version and help checks are compatibility observations, not real provider executions. Upstream event details can evolve independently of these installed versions. The planned fixtures pin the documented version/shape and identify whether a sample is locally observed, repository-authored, or derived from upstream documentation.

## External format references

- [Claude Code CLI reference](https://code.claude.com/docs/en/cli-usage) — stream-json and partial-message options.
- [Gemini CLI headless documentation](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/headless.md) — JSONL event stream and usage/result examples.
- [Codex CLI exec arguments](https://github.com/openai/codex/blob/main/codex-rs/exec/src/cli.rs) and [Codex execution event types](https://github.com/openai/codex/blob/main/codex-rs/exec/src/exec_events.rs) — `--json` and event/usage shapes.

These upstream documents are useful for authoring isolated fixtures, not proof that the locally installed version emitted each event. The parser must reject or mark unknown fields without guessing.

## Compatibility and reuse inventory

| Concern | Reuse | Adapt | Create | Keep untouched |
|---|---|---|---|---|
| Process identity and lifecycle | M3 execution/identity facts; M1 transition rules | Add a read-only identity snapshot to the monitor port | M4 correlation/activity view | M1 state machine and M3 signaling ownership |
| Provider telemetry | Existing Claude/Antigravity fixture conventions and M3 fake providers | Separate stderr/stdout and enable Codex JSONL | Provider normalizers and M4 stream contract | Legacy telemetry semantics and raw artifacts ownership |
| Usage history | M2's existing metric/route history types where compatible | Add provenance and comparability rules | M4 metric snapshot store/read port | `bt_events` ownership and M2 route-choice ledger |
| Incidents | M1 audit/idempotency patterns | Add an additive audit-only M1 fact | M4 detector and incident lifecycle | Task/attempt transition semantics |
| Persistence | Python `sqlite3` conventions and WAL | None across module ownership boundaries | M4-owned SQLite schema, cursor and outbox | M1/M3 SQLite files and legacy JSONL |
| Operator inspection | Existing CLI conventions | Add SSH-safe read-only command | M4 status/incident/metric queries | Legacy interactive `bt_monitor` |

## Preconditions and open compatibility points

1. T1 freezes the exact versioned field allowlists and compatibility policy before code changes.
2. T2 must deliver separate stdout/stderr metadata. Today M3 merges them, so provider diagnostics cannot be assigned a source stream without this adaptation.
3. M3's detached shim prevents an in-process queue from carrying stream bytes. T2 uses a private POSIX FIFO and M3 durable byte/drop summaries; M4's isolated package receives in-memory frames through its one methodology adapter and contains no FIFO/socket/subprocess code.
4. T2 must keep the output-drain path decoupled from the current direct M1 lifecycle sink. The M4 store must never run in a subprocess callback.
5. T3 adds Codex `--json`; the adapter must recognize the installed/provider contract version and persist only normalized allowlisted metadata.
6. Gemini remains unsupported by the M3 launch route until an independent M3 authorization changes that boundary.
7. T9 requires an additive M1 Event contract revision and tests proving that an incident reference changes audit history only, not projection/state.
8. T10 consumes M4 metric snapshots as optional read-only evidence. Unknown quota stays unknown; provider/model/profile comparability is explicit.
9. Owner-approved defaults are a per-project SQLite store, 90/365/730-day retention, 512 MiB store cap and bounded FIFO/queue/evidence sizes (D-030–D-033). T12 replaced pre-measurement CPU/RSS/throughput guesses with host-local budgets recorded in D-037; it did not change the accepted storage caps.
