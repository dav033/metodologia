---
id: REQ-004
status: implemented
created: 2026-10-12
track: standard
---
# REQ-004 — Measured context efficiency

## Goal
Explore additional token savings in metodologia, benchmark against the current integrated skill and adopt only changes supported by evidence without quality or permission regressions.

## Requirements
- R1. Research just-in-time reference loading, batching independent reads, bounded tool output and compact routing using primary sources and previous measured traces.
- R2. Preserve a frozen current baseline and test two isolated candidates: selective reference/output guidance; compact entrypoint plus the same guidance.
- R3. Run two fresh-context repetitions per variant on the same conversational and noisy-artifact suite, with fixed quality criteria and identical model/effort. Report input, cache, uncached input, output, reasoning, calls and failures separately.
- R4. Validate the selected candidate on a different held-out task against baseline. Do not adopt a candidate with critical quality regression or no measured benefit; preserve unsuccessful candidates/results in the benchmark evidence.
- R5. Integrate the smallest supported change, retain existing permission/language/memory/verification rules and licenses, and document checks and limits.

## Acceptance
No omitted failure, invented successful check, repeated side effect for diagnostics, changed approval gate or discarded user constraint. Benchmarks use disposable fixtures, no production or external actions. Improvements are reported as observations from a small repeated sample, not guaranteed monetary savings.

## Scope exclusions
No models/effort changes, RTK binary installation, global harness/tool/config changes, commits/pushes, paid external eval CLIs or root-level permissions. No fixing unrelated previous review findings.

## Method
Screen 3 variants × 2 fresh runs = 6 subagents, then baseline vs selected candidate on a held-out fixture = 2 more. At most 3 benchmark workers concurrently. Common startup/final response harness, neutral labels and same prompts. Include both conversational scenarios and reading existing synthetic log artifacts. Manual quality checks are predeclared; real runtime counters are collected after completion. Any SDK/harness limitation is reported.

## Sources
- https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- https://www.anthropic.com/engineering/writing-tools-for-agents
- https://developers.openai.com/api/docs/guides/agents-api/observability
- Prior local two-subagent A/B evidence: artifacts/metodologia-ab-2026-10-12/
