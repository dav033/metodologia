# REQ-017 — Offline acceptance and failure matrix

All ordinary checks use deterministic fixtures, fake process identities, a temporary SQLite store and simulated streams. No test calls provider APIs, reads live credentials, starts a real agent, or consumes quota. The matrix is a future implementation gate; no suite was run during planning.

## Required deterministic scenarios

| ID | Scenario and setup | Required assertion | Planned coverage |
|---|---|---|---|
| S01 | Three simultaneous simulated attempts with different providers, profiles and process identities. | Activity, offsets, last I/O and metrics stay correlated to the correct run/task/attempt/execution; missing fields remain unknown. | `test_activity.py`, `test_integration.py` |
| S02 | Claude stream-json split across reads, including partial UTF-8 and a partial JSON object followed by completion. | Frames reassemble without blocking; source schema/type is recorded; normalized events omit message/reasoning text. | `test_provider_claude.py`, `test_stream.py` |
| S03 | Codex `codex exec --json` fixture with thread/turn/item events, completed usage and cached/reasoning token fields. | Supported allowlisted fields and token units are retained; command/agent/MCP contents and file paths are not. | `test_provider_codex.py` |
| S04 | Antigravity `agy` simulator emits start, usage, result, structured quota/auth error and malformed event fixtures. | Known fields normalize deterministically; unsupported shapes produce a gap/unknown event; no real `agy` executable is required. | `test_provider_antigravity.py` |
| S05 | Gemini CLI 0.63.0 headless JSONL fixture is presented while M3 route capability says unsupported. | Parser contract fixture may normalize known event metadata, but M3 cannot advertise or launch Gemini; unsupported schema remains explicit. | `test_provider_gemini.py`, `test_capabilities.py` |
| S06 | Oversized frame, invalid UTF-8, truncated JSONL, malformed object, decoder exception and abrupt stream close. | Reader continues draining; each loss has bounded counts/digest/offset range and a `stream_gap`; no raw malformed bytes persist. | `test_stream.py`, `test_detectors.py` |
| S07 | Repeated, reordered, skipped and replayed sequences/offsets, including M4 restart between duplicates. | Cursor and event dedupe are stable; missing ranges are explicit; no duplicate incident or false new execution is created. | `test_store.py`, `test_stream.py` |
| S08 | Secret-like values in provider fields, nested unknown objects, stderr and diagnostic text; secret-filter failure injected. | Only the allowlist is retained; redacted excerpts stay within cap; filter failure withholds text; tests verify raw values are absent from DB/WAL-facing query output. | `test_redaction.py`, `test_store.py` |
| S09 | Process remains alive with no output for five minutes; separately, M3 heartbeat continues while no valid provider event arrives. | `silent_but_alive` and `provider_stream_silence` are low-confidence informational observations only; neither marks dead, blocked, failed or complete. | `test_activity.py`, `test_detectors.py` |
| S10 | Unexpected nonzero exit, explicit structured quota code, probable quota diagnostic with failing exit, auth error, connection error and M3 timeout fact. | Each detector emits its documented severity/confidence and stable dedupe key; a word such as “limit” in unrelated text is not enough; no detector changes M1 state. | `test_detectors.py` |
| S11 | Heartbeat crosses 3× configured period; exact same observable tool signature repeats 20 times in five minutes; output/event/evidence caps are crossed. | Heartbeat miss, repetitive activity and oversize/gap are visible with their configured confidence; repetitive behavior never blocks; limits cause drops/summary only. | `test_detectors.py`, `test_activity.py` |
| S12 | PID is reused with changed start ticks or boot ID; a delayed frame arrives after M1 cancel and the 2s drain grace; M1/M3/stream snapshots disagree. | PID reuse cannot join executions; stale frames are isolated; disagreement is reported only after reconciliation; unknown identity stays unknown. | `test_identity.py`, `test_detectors.py` |
| S13 | M4 stops after event insert, before cursor update/outbox ack, or during M1 delivery; then restarts. | Store transaction preserves event/cursor consistency; M1 delivery is at-least-once and idempotent; pending outbox resumes without duplicate audit effects. | `test_store.py`, `tests/test_scheduler_monitor_m1_adapter.py` |
| S14 | Retention crosses the approved 90/365/730-day limits; database approaches 512 MiB cap; queue hits frame/byte limit; SQLite busy/full is injected. | Expired detail compacts/deletes according to the approved policy; open incidents are never falsely resolved; queue remains bounded; pressure/loss is surfaced and measured. | `test_retention.py`, `test_store.py`, `test_stream.py`, benchmark |
| S15 | M1 receives an incident reference; M2 receives same-provider and cross-provider usage samples with reported/partial/unknown quality. | M1 appends audit evidence but reducer state is unchanged; outbox dedupe holds; M2 never compares incompatible tokens and unknown quota is not infinity/zero. | M1 core integration tests, `tests/test_scheduler_monitor_m1_adapter.py`, `tests/test_scheduler_monitor_m2_adapter.py` |

## Detector coverage map

| Detector | Scenario |
|---|---|
| `unexpected_exit`, `quota_explicit`, `quota_probable`, `auth_failure`, `connection_error`, `timeout` | S10 |
| `missed_heartbeat`, `repetitive_activity`, `oversized_output` | S11 |
| `silent_but_alive`, `provider_stream_silence` | S09 |
| `pid_reuse`, `stale_post_cancel`, `source_disagreement` | S12 |
| `stream_gap` | S06, S07, S11, S14 |

Each test asserts both the positive trigger and a nearby negative case. Detector tests compare stable IDs, not exact wall-clock strings. Clock fixtures provide UTC and monotonic time plus boot identity explicitly; elapsed assertions never depend on the host clock.

The package-convention gate is also required: `bt_scheduler_monitor/tests/test_boundaries.py` rejects imports of sibling modules, environment lookups, sockets and subprocess use inside the package; `test_isolation.py` copies the package alone and runs its suite/CLI with an isolated interpreter. `tests/test_scheduler_monitor_integration.py` verifies that exactly one methodology adapter imports the package and that M1/M2/M3 state files remain owned by their current modules.

## Acceptance commands after implementation

The plan's task-level `verify:` fields are the focused commands. The final offline gate is:

```bash
cd skill/scripts
python3 -m unittest discover -s bt_scheduler_monitor/tests -v
python3 -m unittest discover -s tests -p 'test_scheduler*.py' -v
python3 -m bt_scheduler_monitor.bench --concurrency 3 --fixtures tests/fixtures/scheduler-monitor --report /tmp/req-017-m4-benchmark.json
```

The benchmark must report environment and fixture revision, attempts/events per second, maximum queue frames/bytes, dropped ranges, p50/p95 frame-to-query latency, CPU time, sampled peak RSS, database/WAL size, and retention/compaction behavior. Set the operational CPU/RSS/throughput/p95 thresholds only from this reproducible result; do not assert guessed budgets before measuring.

## Optional live smoke (not part of ordinary acceptance)

Any real CLI smoke is a separate, later opt-in operation that requires an explicit provider, profile and bounded prompt. Report its exact CLI version, argv mode, event schema observed, elapsed time and usage result separately from fixture tests. Do not refresh quota or inspect credentials. Gemini remains ineligible until M3 authorizes its route; Antigravity cannot be smoke-tested while `agy` is unavailable. Nothing in this planning session ran such a smoke.
