---
id: REQ-017
status: in-progress
created: 2026-10-15
track: deep
---
# REQ-017 — Scheduler M4 Agent Monitor

## Problem & goal

Scheduler M1 owns authorized task and attempt state; M2 proposes routes; M3 starts and supervises processes. There is
no independent, deterministic monitor for live provider activity, usage reports, stream loss, or corroborated
execution incidents. The legacy monitor is an interactive AI session over `RUN.json`, and does not observe the new
Scheduler path.

**Goal:** add M4 as a headless, concurrent observer that normalizes evidence from M3, records incidents and comparable
measurements, and gives M1/M2 read-only information without controlling processes, changing task state, or invoking AI.

**Success looks like:** all authorized attempts are represented by an explicit activity view; structured provider events
retain their source/version; lost or duplicate events are observable and replay-safe; incidents include evidence and
confidence; quiet-but-live or disconnected sources never become an automatic process-death verdict; secrets and raw
project text do not enter M4 persistence; offline tests cover the failure matrix in `M4-TEST-MATRIX.md`.

## Users / actors / stakeholders

- David, operating a persistent Arch Linux Scheduler over SSH without a graphical terminal.
- M1, which remains the only authority for task and attempt state.
- M2, which may consume provenance-aware usage/history measurements.
- M3, which owns process lifetime, output capture, and process identity.
- Future M5, receiving evidence only through M1; future M6, which owns result verification.

## Scope (in)

### US-1 (P1, Must) — Observe each authorized execution

As the Scheduler operator, I want M4 to correlate stream activity with M1's run/task/attempt and M3's execution/process
identity so I can see which agent is active, what observable operation it reported, its last activity, and reported usage.

**Acceptance:** with three simulated concurrent attempts, each view retains its own provider, opaque profile, model,
sequence/offset, last received/source activity and process observation; missing values remain explicitly unknown.

### US-2 (P1, Must) — Normalize safely

As a maintainer, I want versioned provider adapters and bounded stream handling so partial, malformed, late, duplicated,
and out-of-order events produce normalized evidence or an explicit gap without blocking M3.

**Acceptance:** the offline fixtures for launchable M3 providers and the installed-but-not-M3-wired Gemini CLI parse
or report unsupported input without inventing event fields; truncation and decoder failures produce a gap record.

### US-3 (P1, Must) — Surface corroborated incidents

As an operator and M1 consumer, I want deterministic incident records with severity, confidence, evidence and resolution
so failures are visible without M4 making recovery or state decisions.

**Acceptance:** every detector in `M4-ARCHITECTURE.md` emits a stable, deduplicated incident or an explicit no-incident
result; silence with a confirmed live process is informational only and cannot block or fail the attempt.

### US-4 (P1, Must) — Persist and query bounded history

As the operator and M2, I want restart-safe normalized events, incidents and provenance-aware metrics with finite
retention so history survives process restarts without unbounded disk growth or false cross-provider comparisons.

**Acceptance:** replay after M4 restart is idempotent; the incident outbox retries at least once; a partial source gap is
visible; usage reports keep unit, source, quality and comparability; retention/size limits are exercised by tests.

### US-5 (P1, Must) — Preserve module authority and headless operation

As the Scheduler, I want M4 integrated through versioned ports so M1 remains authoritative, M3 remains the process
owner, and an operator can inspect status over SSH without an AI session or GUI.

**Acceptance:** only M1 applies task-state transitions; M4 has no start/cancel/process-signal API and no AI dependency;
legacy `RUN.json` bytes and behavior are unchanged; headless status/query commands work against fixture stores.

## Out of scope

- Choosing providers/models/accounts/effort (M2), changing the DAG or task/attempt state (M1), starting/cancelling/
  terminating processes (M3), retry/recovery policy (M5), and code/result verification or integration (M6).
- Reading or interpreting agent reasoning, assigning percentage completion, or treating a message/tool label as proof of
  code progress or task success.
- Calling provider APIs for quota refresh, reading provider credentials, sending external notifications, launching real
  agents, or deploying services as part of this planning requirement.
- Wiring the installed Gemini CLI into M3 route selection. M3 currently exposes Claude, Codex and Antigravity (`agy`);
  Gemini CLI remains a fixture/contract target until M3 adds an authorized provider route.
- Replacing or rewriting legacy `RUN.json`, `bt_monitor`, `bt_events`, M1/M2/M3 modules wholesale, adding a remote
  service, or migrating historical records.

## Requirements

- **R1.** When M1 authorizes an attempt and M3 reports it, M4 shall correlate every observation to the approved run,
  plan revision, task, attempt, execution and stable process identity; unknown identities stay null/unknown.
- **R2.** M3-to-M4 stream frames, M4 normalized events, M4 incidents/evidence, and M4-to-M1 incident references shall
  have explicit versions and compatibility rules. Existing M1/M2/M3 lifecycle contracts remain valid during migration.
- **R3.** The collector shall accept incremental stdout/stderr frames, partial UTF-8, partial/truncated JSONL, malformed
  objects, duplicate/out-of-order offsets and abrupt stream closure. It shall record source gaps and never treat a
  missing terminal event as proof that the process stopped.
- **R4.** The output reader shall drain provider pipes independently from M4 persistence. Queue and frame bytes shall
  have explicit limits; overflow or store failure shall increment a loss counter and emit a gap when delivery resumes.
- **R5.** A normalized event shall include `schema_version`, `run_id`, `task_id`, `attempt_id`, `execution_id`,
  `process_identity`, `provider`, opaque `profile_id`, optional `model`, normalized and source event types, source and
  receive timestamps, monotonic receive time/boot identity where known, sequence/offset, evidence reference, and a
  typed allowlisted payload. Provider event IDs may be absent.
- **R6.** Raw provider bytes/objects shall be treated as untrusted input and shall not be copied to M4 storage. M4 shall
  persist only allowlisted normalized fields and bounded redacted evidence; malformed/unknown payloads may retain a
  digest, byte count and source offset, never the raw contents. Secret-filter failure shall withhold text.
- **R7.** The activity view shall expose last source event, last received I/O, last observed tool label, pending observable
  tool events, provider-reported metrics, stream integrity, and process status separately. It shall distinguish active,
  tool-pending, silent-but-live, source-disconnected, process-confirmed-dead and unknown.
- **R8.** Deterministic detectors shall cover unexpected process exit, explicit/probable quota exhaustion, authentication
  failure, connection errors, timeout, missed heartbeat, silent-but-live process, repetitive observable activity,
  oversized output, provider-stream silence, PID reuse, stale post-cancel events, and disagreement among M1/M3/stream
  evidence. Each rule shall specify evidence, threshold, severity, confidence, false-positive risk, deduplication,
  suppression and resolution.
- **R9.** An incident shall have a versioned stable ID, run/task/attempt/execution identity, detector/type, severity,
  qualitative confidence, first/last-seen times, observed facts, redacted evidence references, occurrence count and
  resolution state. Incidents inform M1; they never authorize transitions or recovery.
- **R10.** M1 shall accept an additive, versioned incident-reference fact as audit-only evidence. It shall not change
  task/attempt state from that fact; normal M1 transition validation remains in force. M4's full incident record remains
  M4-owned; M1 stores only the idempotent reference and minimal correlation fields needed by future M5.
- **R11.** M4 shall expose read-only provider usage/history to M2 with value, unit, source, observation time, quality
  (`reported`, `partial`, `estimated`, `unavailable`, or `unknown`), sample count and comparability key. Unknown quota
  is never infinity; cross-provider token totals are not comparable by default.
- **R12.** M4 persistence shall use a local, project-isolated, restart-safe store with transactions, deduplication,
  bounded incident outbox, explicit retention/compaction and recovery. M4 shall not edit `RUN.json` or assume ownership
  of M1/M3 state files.
- **R13.** Runtime source timestamps shall be preserved as provider-reported evidence; received timestamps use UTC wall
  time; elapsed thresholds use monotonic time plus boot identity. Clock skew/reboot produces explicit uncertainty.
- **R14.** M4 shall query M1/M3 read-only status and offer status, incident and metric queries usable over SSH. It shall
  not launch, cancel, signal, resume or recover an execution.
- **R15.** The implementation shall keep resource bounds explicit: bounded frame/queue size, maximum normalized event
  and evidence size, retention, store cap, and measured throughput/latency/RSS/disk under three concurrent simulated
  agents. The numeric CPU/RSS throughput budget shall be set from that reproducible baseline, not guessed in advance.
- **R16.** M4 shall be deterministic and use no model, token, provider inference, semantic interpretation or network
  call in its normal operation. Provider structured output is parsed as data, never instructions.
- **R17.** Tests shall cover the 15 scenarios in `M4-TEST-MATRIX.md`; ordinary automated verification uses fixtures and
  simulators with no live provider quota. Real CLI smoke tests are opt-in and shall be reported separately.
- **R18.** The rollout shall preserve legacy behavior and M1/M2/M3 contracts via additive, versioned ports/adapters;
  provider/plan states unsupported by current M3 remain explicit preconditions, not fabricated compatibility.

## Edge cases & errors

- Provider bytes are split across reads; one JSON object spans reads; the stream ends mid-object; invalid UTF-8 or an
  event exceeds the frame cap.
- Source sequence repeats, reverses, skips, restarts at a new process identity, or arrives after an authorized cancel.
- M4 or M3 restarts while an agent remains alive; M4 store is busy/full; source and process status disagree.
- A heartbeat is late while the process is alive, or the monitor itself is unreachable. This is an observation gap,
  not an agent-death fact.
- A legitimate long operation emits no output; repeated tool labels are expected; a message merely contains the word
  “limit”; provider output includes credentials or project text.
- A process ID is reused after exit/reboot; profile/model/usage fields are absent or use provider-specific units.

## Constraints

- Target: Linux/Arch, unattended and accessible over SSH; portable event contracts, with Linux PID/start-time identity
  strongest on the first implementation.
- New `bt_scheduler_monitor` package follows `references/modules.md`: Python standard library, one public API, isolated
  tests, one methodology adapter, no imports of sibling `bt_*` modules and no subprocess/network ownership.
- M1 owns state and transactional audit; M2 owns route proposals and consumes optional metrics; M3 owns processes and
  emits source frames; M4 owns normalized telemetry/incidents; M5 owns recovery; M6 owns verification.
- Existing M3 uses private bounded output artifacts (8 MiB head + 256 KiB tail) and a SQLite event outbox capped at
  10,000 pending events; its current lifecycle sink can delay the supervisor thread. M4 must not enlarge or bypass
  those limits silently.
- Current supported CLI versions and compatibility limits are documented in `M4-INVENTORY.md`; no live agent run is
  authorized by this planning deliverable.
- No distributed service/database. A separate local SQLite file is approved only for M4-owned cursors, incidents and
  delivery outbox; `M4-ARCHITECTURE.md` records the alternatives and accepted retention policy.

## Priorities & phases

Must: M4.1 contracts; M4.2 M3 stream adapter and provider normalizers; M4.3 activity/detectors; M4.4 durable store and
queries; M4.5 M1/M2/M3 integration; M4.6 adversarial verification and operational documentation. The plan has six
milestones and 12 tasks with DAG dependencies in `PLAN.md`/`PLAN.json`.

## Timeline & dependencies

No calendar deadline was supplied. The critical path is versioned contracts → M3 bounded stream interface → provider
normalizers/redaction → activity/incidents → M4 store/outbox → M1/M2 read-only integration → full matrix. T2 depends on
M3 stream/channel metadata that does not exist yet; the fixture simulator is the executable precondition until that
contract lands. Gemini CLI parsing remains fixture-only until M3 authorizes a `gemini` route; `agy` live verification
remains unavailable while its binary is absent.

## Assumptions

- **A1 — local storage:** one M4-owned SQLite WAL file per Scheduler run/project, outside the legacy `RUN.json` and
  M1/M3 databases. This avoids cross-module writes while keeping deployment local and single-host.
- **A2 — data minimization:** M4 persists no raw JSONL/stdout/stderr. It stores allowlisted event names/fields, counts,
  hashes, offsets and redacted excerpts only. Existing M3 private output artifacts remain M3-owned and are not copied.
- **A3 — owner-approved retention:** normalized event detail 90 days; resolved incident detail 365 days; daily
  aggregates 730 days; open incidents remain until resolved. The database plus WAL cap is 512 MiB, normalized records
  are limited to 16 KiB, and evidence excerpts to 4 KiB. See D-033.
- **A4 — buffering:** start from M3's existing 64 KiB read chunk and 10,000-event pending ceiling, add a global byte
  ceiling and a normalized record cap, then measure actual RSS/disk/CPU/latency. The absolute resource budget is a
  deliverable of T12, not a fabricated claim in this plan.
- **A5 — quiet process:** after five minutes without stream output while M3 confirms the process alive, M4 may emit only
  a low-confidence informational `silent_but_alive` incident. The threshold is configurable; it never changes M1
  state or labels the execution blocked/dead.
- **A6 — provider activation:** parse fixtures for installed Gemini CLI 0.63.0, but do not present it as a launchable M3
  provider. Use simulated Antigravity events until `agy` is installed and an opt-in smoke is separately authorized.

## Coverage

| Topic | State |
|---|---|
| Goal & problem | Clear — concurrent headless observation without IA or process authority |
| Users / actors | Clear — operator, M1, M2, M3; M5/M6 future boundaries |
| Scope | Clear — R1–R18 and US-1..US-5 |
| Out of scope | Clear — M5/M6 decisions, process control, live providers, legacy rewrite |
| Flows & behavior | Clear — contracts and Mermaid flow in `M4-ARCHITECTURE.md` |
| Edge cases | Clear — partial/reordered streams, restarts, PID reuse, silence, storage pressure |
| Acceptance criteria | Clear — objective gates in this spec, plan and test matrix |
| Constraints | Clear — module boundaries, local SQLite, security and current provider limits |
| Priorities & phases | Clear — six named milestones |
| Timeline | Deferred — no date supplied; DAG and estimates are in `PLAN.json` |

## Clarifications

- Q: Should this session implement M4? → A: No. The supplied prompt explicitly limits this session to planning,
  deterministic plan validation and artifacts; it forbids implementation, real provider runs, quota use and deployment.
- Q: How should missing CLI support be represented? → A: As a versioned precondition plus simulator/fixture; no claim
  that the installed Gemini CLI is wired through M3.
