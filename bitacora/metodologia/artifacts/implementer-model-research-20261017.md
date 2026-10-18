# Implementer candidate research and six-case pilot proposal

Status: research complete; owner-approved experiment now running under `implementer-pilot-20261017/protocol.json`.
Owner's final matrix supersedes the proposal below: Luna and Haiku medium/high/xhigh, plus Sol and Sonnet medium; eight configurations x six cases = 48 target cells. No Astra/Opus/Gemini calls. The seven-model matrix below is retained as research history, not execution authority.
Scope: owner asked to research implementer candidates first, then compare them on six progressively harder tests. Separate from the formal REQ-024 Planner benchmark. No role configuration changes.

## Current primary sources

Retrieved 2026-10-17:
- OpenAI: https://learn.chatgpt.com/docs/models — recommends GPT-6.1 Sol for complex coding, Luna for focused repeatable coding, Astra for the most demanding sustained work. Explicit guidance starts Luna at high; effort labels are not equivalent across generations.
- Anthropic Sonnet: https://www.anthropic.com/claude-sonnet-5-5 — positions Sonnet for scoped everyday implementation and bug fixes, and Opus for complex open-ended judgment. Reports Sonnet FrontierCode 46.2% at max versus 52.1% at xhigh: more effort is not a guaranteed monotonic gain.
- Anthropic Opus: https://www.anthropic.com/claude-opus-5-5 — positions Opus for long migrations and multi-file work; reports FrontierCode 54.6% at default medium. Provider-reported evidence, not a controlled comparison against current Sol 6.1.
- Google: https://deepmind.google/models/gemini/flash/ and https://deepmind.google/models/model-cards/gemini-3-8-flash/ — explicitly positions Flash 3.8 for coding, agents, long-horizon software engineering. Does not establish the quality or speed of our native Antigravity low route.

Inference: compare everyday Sol/Sonnet, inexpensive Luna, and Gemini as a third-provider alternative; include Astra and Opus to measure whether harder cases justify stronger routes. Do not infer a universal winner from separate provider benchmark tables. Owner follow-up asks about Haiku. Include Haiku 5.5 medium as another economical Implementer candidate, especially against Luna; exclusion from the Explorer policy is not evidence about implementation. Official source https://www.anthropic.com/claude-haiku-5-5 explicitly recommends it for coding subagent work, while preferring Sonnet/Opus for complex agentic coding. Effort medium is an experimental proposal, not a permanent assignment.

## Proposed fixed matrix

| Cell route | Model | Effort | Proposed profile | Purpose |
|---|---|---|---|---|
| haiku | claude-haiku-5-5 | medium | claude-work | economical scoped coding subagent |
| luna | gpt-6-luna | high | codex-2 | focused economical implementation |
| sol | gpt-6.1-sol | medium | codex-2 | routine general implementation |
| sonnet | claude-sonnet-5-5 | medium | claude-work | routine general implementation |
| gemini | gemini-3.8-flash-low | low | antigravity | third-provider alternative |
| opus | claude-opus-5-5 | medium | claude-work | complex implementation at default effort |
| astra | gpt-6-astra | high | codex-2 | high-capability reference |

Efforts are experimental proposals, not a permanent owner policy. Six cases per route = 42 target implementation sessions, one sample per cell. Fixed effort across levels avoids confounding difficulty and automatic escalation. Do not silently substitute models, change efforts, rotate accounts, or retry a quality failure. Defer effort-specific follow-ups to a separately bounded experiment.

## Proposed cases and acceptance contracts

All cases use independent Python/SQLite standard-library repository fixtures. They test backend implementation, not frontend quality or every programming language. Later fixtures increase coupled behavior, persistence, concurrency and failure-recovery requirements. The difficulty ordering is designed, not empirically established until results exist.

1. I1 — Repair a local interval-merging bug. Merge unsorted half-open integer intervals, including touching boundaries; preserve inputs, drop empty intervals, reject reversed bounds. Tests cover empty/singleton/nested/duplicate/negative inputs and randomized agreement with a simple oracle.
2. I2 — Add stable cursor pagination through a repository/service/CLI. Sort by timestamp and unique ID, handle tied timestamps and deleted cursor rows, enforce page limits, reject malformed cursors and preserve the old first-page API. Tests exercise each layer and no duplicate/missing rows across a static traversal.
3. I3 — Refactor a dependency scheduler across modules without changing its public API. Validate unknown dependencies, detect cycles before dispatch, preserve deterministic ready ordering, enforce max parallelism and correct failed-dependency propagation. Tests cover DAG shapes, input order permutations and existing compatibility behavior.
4. I4 — Implement transactional SQLite persistence with a schema migration. Upgrade a legacy job schema, preserve IDs/data, apply migration atomically/idempotently, support rollback on injected faults and reopen the database successfully. Tests verify old fixtures, fresh databases, repeated initialization and failed migration recovery.
5. I5 — Fix concurrent claims and stale worker completion in a leased queue. Use transactional claims and monotonic fencing tokens, enforce expiry, prevent double ownership and reject completion from superseded workers. Tests coordinate two independent connections/processes with barriers, rather than relying on arbitrary sleeps.
6. I6 — Implement recovery across a crash boundary for a scheduler and durable outbox. Commit job results and outbox events atomically, resume after crashes at declared fault points, deduplicate event IDs, preserve retry/dependency semantics and make replay idempotent. Delivery is at-least-once; no unsupported exactly-once external side-effect promise. Tests include subprocess termination/restart, replay, duplicates, failed dependencies and end-to-end compatibility.

## Execution and grading plan

1. Build independent starting fixtures, public tests, private acceptance tests and reference implementations. Freeze prompt, fixtures, oracle and hashes before native candidate sessions. Demonstrate that baseline fixtures fail intended checks and the reference passes all checks; test grader sensitivity to representative wrong patches. These artifacts must exist before any target cell starts.
2. Check native runtime versions, configured profile access and current quotas. Unknown/error quota stays unknown. Stop a lane on quota/auth/model identity failures and report unrun cells. Any unavailable candidate stays unavailable, not replaced.
3. Give each native implementer the identical task and source tree for that case, its own fresh working copy and permission to edit only that fixture. Candidate may inspect, implement and run public checks. No network, package installs, nested delegation, original repo edits or access to experiment/oracle/other cells. Preserve the actual native tool configuration in the manifest. Hidden tests are withheld from the task tree; record the isolation method and do not overclaim adversarial isolation.
4. Execute in increasing case order per route, serially per effective account. Rotate route order between levels to reduce order effects. Use a 25-minute hard timeout per session; Claude max-turns 45 where supported. Preserve partial usage and timeout diagnostics. No automatic effort escalation or repairs by the coordinator.
5. After each session, run private acceptance and regression suites on its patch; retain command, exit code, failure totals, diff and artifact hashes. A prose claim of success does not count. Check protected files and compare submitted tests with originals to detect test weakening. Review critical persistence/concurrency behavior against the frozen contract.
6. Publish per-case pass/fail/partial criteria, regression and scope violations, elapsed time, tool turns and actual reported input/output/cache/reasoning counters with coverage. Keep API-equivalent estimates separate from subscription quota. Missing usage is null. Judge correctness first, then compare time/consumption among equally passing candidates. Report both number of fully passed cases and criteria-level results; do not hide I6 failure in an average.

A single sample on six synthetic cases cannot establish statistical superiority or a universal production routing policy. Model and native harness effects are combined unless a separate controlled harness experiment is run. This pilot chooses candidates for later real-project validation; it does not automatically assign the Implementer role.

## Approval and next action

The owner approved a revised 48-cell matrix: Luna/Haiku medium/high/xhigh and Sol/Sonnet medium. Six fixtures and graders were built, reference/baseline/mutant checks completed, and fresh spec/standards reviews approved before freezing and launching native calls. Follow `implementer-pilot-20261017/protocol.json`, `execution.log`, `results/` and `execution-summary.json` for live evidence. This experiment does not change any permanent role-model assignment.
