---
id: REQ-030
status: in-progress
created: 2026-10-28
track: deep
---
# REQ-030 — Operation Metamorfosis: durable, self-healing, Linux-native execution engine

The owner's full requirement is kept verbatim in [REQUEST.raw.md](REQUEST.raw.md); it is the spec. By the owner's
instruction this requirement is executed directly (one session plus subagents), without the Scheduler, handoff or the
planning flow, because those are what it replaces.

## Problem & goal
Too much generic infrastructure (state persistence, outboxes, retries, recovery, process control) is hand-built, and
its failures end as owner interventions (pictures REQ-021: 29 interventions, 71 attempts, 24 on one task).
**Success looks like:** runs that recover from crashes and infrastructure failures without the owner, with the owner
asked only for product, permission or budget decisions — proven by executable tests.

## Status
- Baseline and map: [M0-ARCHAEOLOGY.md](M0-ARCHAEOLOGY.md). Result and acceptance evidence: [REPORT.md](REPORT.md).
- Code: branch `metamorfosis` (worktree `~/dev/metodologia-metamorfosis`), not merged, not pushed.

## Clarifications
- Q: Follow the methodology flow (interview, plan, scheduler)? → A (owner, 2026-10-28): no; use the bitácora and broad
  engineering standards only, and keep the raw requirement.
- Q: Pause the running executions first? → A (owner): yes; pictures REQ-021 was put on hold, att-0094 left to finish.
