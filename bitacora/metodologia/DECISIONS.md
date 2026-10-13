# metodologia — Decision log

_Append-only. Newest at the bottom. Never delete or rewrite an entry: when a decision changes, add a new one
with `Supersedes: D-xxx` and edit only the old entry's `Status` line to `Superseded by D-yyy`._

<!-- Entry format:
## D-001 — <short title>
- **Date:** YYYY-MM-DD · **Status:** Accepted | Superseded by D-xxx | Reverted
- **Context:** why this came up
- **Decision:** what we chose
- **Alternatives:** option — why rejected
- **Consequences:** + good / − cost or risk
- **Source:** [day log](YYYY-MM/Wn/YYYY-MM-DD.md) · REQ-xxx (if any)
-->

## D-001 — Adapt agent orchestration patterns without importing external runtimes
- **Date:** 2026-10-10 · **Status:** Accepted
- **Context:** The methodology skill needed stronger concurrent subagent orchestration and long-running autonomous development. Public repositories offer useful patterns but vary in safety defaults and external dependencies.
- **Decision:** Adapt dependency-aware task waves, explicit ownership, bounded concurrency, worktree isolation, durable checkpoints, and independent verification into methodology references. Attribute source repositories; do not copy files or adopt external runtimes, credential handling, permission bypasses, or global configuration.
- **Alternatives:** Install a public orchestration framework — rejected because it adds runtime/config/security surface beyond the user's request. Copy an entire skill — rejected in favor of a small, attributed adaptation.
- **Consequences:** + portable workflow with no new dependency; + preserves current safety gates; − orchestration remains instruction-driven and uses only capabilities available in the active harness.
- **Source:** [day log](2026-10/W2/2026-10-10.md) · REQ-002

## D-002 — Do not integrate Laya into the router now; collect labelled telemetry first
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** The plan proposed Laya (local typed classifier, ModernBERT-based, CLI/MCP) as the router's task classifier. A researcher, an advocate, a critic (two rounds) and an independent judge evaluated it; notes and verdict: /tmp/claude-1000/laya/ (NOTES, PRO-1/2, CON-1/2, VERDICT).
- **Decision:** No Laya service, MCP or zero-shot shadow now. Do instead: deterministic rules for risk/scope/verifiable (computable from the repo), a fixed 7-field JSON classification by the orchestrating agent with David's corrections, and an attempt log (`bt_events`). Reopen only if all hold: (A) >=150 blind human labels, an embedding+logistic baseline trained on the same split, and a seed-averaged fine-tuned Laya whose paired-bootstrap IC95 lower bound beats the baseline, plus ECE<=0.10, p95<=500 ms and VRAM<=3 GB measured on the A3000; and (B) >~50 tasks/day or measurable quota spent on agent classification, or (C) a replay showing Laya routing improves outcomes over rules+agent. Also check that the weights load without the `laya` package.
- **Alternatives:** Laya in shadow mode from day one — rejected: shadow without ground truth teaches nothing and execution labels measure success, not type/ambiguity/complexity. Embedding+LR now — deferred until labels exist.
- **Consequences:** + no multi-GB dependency or always-on service; + router effort goes to measurement; − no learned classification until data exists; − still unverified: A3000 latency/VRAM, telemetry/torch.load audit of the repo.
- **Source:** [day log](2026-10/W3/2026-10-12.md) · REQ-006

## D-003 — One router for every provider: capability tiers, account pool, milestone sessions and independent audits
- **Date:** 2026-10-12 · **Status:** Accepted
- **Context:** The owner wants a requirement to run to the end without interaction: sized automatically, planned in milestones, each milestone in a clean session, with tests, documentation, implementation and audit handled by the system, switching agent and effort on its own, aware of subscription quotas, and learning about the project and the owner. The marathon was pinned to one agent per run and Codex could not change model.
- **Decision:** (1) Tiers 0–2 are capability levels shared by Claude (haiku → sonnet xhigh → opus xhigh) and Codex (gpt-6-luna medium → gpt-6.1-sol high → gpt-6.1-sol xhigh); `bt_agents` routes each session to an account of a pool by tier, kind of work, usage-limit cooldowns, measured success and recent load, preferring another provider after a failure and for audits. (2) A plan's `### Mn` group is one fresh session; each task is still verified on its own; every milestone is closed by a synthetic audit task run by an agent that did not build it, whose verification is every verify of the milestone again. (3) `handoff` approves and launches in the background unless it finds a stated risk reason. (4) Learnings are candidates with evidence, promoted by the owner or by three independent sightings, and only confirmed ones are injected. (5) Gemini/Antigravity support is removed: its free quota made it unusable (exhausted for ~7 days by a handful of sessions).
- **Alternatives:** A learned classifier/router — rejected for now (D-002: no labelled data). An audit that can only report and reopen the milestone — rejected: more states and loops for the same outcome; the auditor fixes contained problems itself and the supervisor re-verifies. Reopen if audits rewrite too much. Per-provider ladders with different depths — rejected: one tier scale makes "climb and switch provider" a single rule. Trusting a milestone session's own "all done" — rejected: per-task verdict and verify are kept.
- **Consequences:** + no user interaction between plan and report in the safe case; + a usage limit on one subscription no longer stops a run; + telemetry per agent/model/effort/kind feeds both the owner and the router; − more real sessions per plan (one audit per milestone); − the risk gate is lexical and conservative: plans that mention credentials, production or money always ask; − success-rate routing needs 5 judged attempts per (agent, model, kind) before it has any say, compared in 20-point bands so quota balancing wins ties.
- **Source:** [day log](2026-10/W3/2026-10-12.md) · REQ-006

## D-004 — Complement methodology with interface quality and evidence-driven review
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** David requested extracting the complementary best practices from Antislop and Thermos into methodology, without duplicating its existing engineering standards or review workflow.
- **Decision:** Route UI/copy work to an on-demand interface-quality reference covering owner direction, purposeful composition, truthful content and recorded interaction/accessibility coverage. Strengthen the existing spec/standards reviews with traced consumer/setup/feature-gate impact, evidence-based severity and root-cause deduplication. Keep optional structural simplifications as proposals, not new blockers. Pin upstream source revisions; adapt ideas independently rather than copying files or installing plugins.
- **Alternatives:** Install both upstream frameworks — rejected because recurring mode/approval gates and duplicate review passes conflict with the existing workflow. Copy their full rubrics — rejected because style bans, the 1k-line threshold and speculative refactor blockers would replace existing owner rules.
- **Consequences:** + focused UI acceptance and review evidence with no runtime dependency; + explicit limits on unverified delivery claims; − instruction-driven behavior still needs real-session evaluation, not just static validation and simulations.
- **Rollback:** Revert only this integration's router/reference links, interface-quality reference, review-protocol section and eval cases; preserve unrelated workflow and runtime code. No external configuration or data migration is involved.
- **Source:** [day log](2026-10/W3/2026-10-13.md), session `01a1356b`; Antislop `b1cdf87d49b1653293d58424516fd80394008345`, Thermos `1dcc2bacde73ddd284803b7af28164d0436198fc`.

## D-005 — Budget-specific audit routing
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** David rejected xhigh flagship audits as excessive for finite subscription quotas and approved Sonnet medium as the normal auditor, Opus high for escalation/high risk, and Sol medium fallback.
- **Decision:** Give audit tasks their own model/effort ladder. Prefer an eligible available Claude account even when it built the milestone; independence comes from a clean session. Routine audits use Sonnet medium; tier 2 uses Opus high. Codex fallback uses Sol medium (high at tier 2). Do not inherit the builder's model or effort. Explicit delegation flags remain overrides. High-risk/architecture milestone members promote the audit; preserve escalation on resume. Consolidate existing audits at final close rather than spawning duplicate full reviews. Keep small changes inline and follow-up review scoped to corrections.
- **Alternatives:** Opus xhigh by default — rejected by the owner for excessive budget. Provider diversity ahead of budget preference — replaced for audits only. Lower every implementation model's effort — outside this request.
- **Consequences:** + explicit audit budget and quota fallback across pooled/fixed routing; + no audit default at xhigh/max; − model capability remains a starting policy to validate with actual findings/rework/consumption. Native Codex reviewers inherit the parent model under the existing installer contract; exact Sol selection uses routed delegation.
- **Rollback:** Revert audit-specific routing, risk inheritance, final-review consolidation and reviewer defaults; restore prior generated reviewer definitions through the existing generator. No runtime state migration or credential change.
- **Source:** [day log](2026-10/W3/2026-10-13.md), session `01a1356b`; owner: “excelent, persistelo”.

## D-006 — Deterministic subscription usage collection and quota-aware routing
- **Date:** 2026-10-13 · **Status:** Accepted
- **Context:** David wants hourly 5-hour/weekly subscription readings without agents, including usage outside methodology, and account selection that favors unused capacity (e.g. codex-luis over a heavily used default Codex account).
- **Decision:** Poll unique registered account configurations sequentially through read-only metadata: Codex app-server rateLimits RPC and Claude OAuth usage endpoint, never a model turn or credential refresh. Store versioned current samples and monthly metadata history outside Git. A user-systemd timer samples hourly on this Arch host. Route from the local cache, using the bottleneck utilization before historical success/local load and after existing provider preferences, audit policy and work gates. Samples older than two hours/error/incomplete are unknown; confirmed exhaustion remains blocking until reset. Track per-model Claude weekly windows where available. Keep account pins explicit. Bound requests and response sizes; respect Retry-After and stop on browser challenges.
- **Alternatives:** Agent-driven hourly checks — rejected: waste inference quota and introduce nondeterminism. Local token estimates — rejected as authoritative because they miss other tools/devices and do not measure subscription limits. A persistent custom daemon — rejected in favor of systemd's existing scheduler. Automatic OAuth refresh — excluded as an unnecessary credential mutation.
- **Consequences:** + live subscription balancing with no inference; + observable errors and durable historical percentages; − Claude endpoint is undocumented/unstable and claude-work currently returns 401; − one-hour sampling is not real-time; − automatic timer installation currently targets Linux/systemd, while manual polling/cache routing remain portable.
- **Rollback:** Disable `metodologia-subscription-usage.timer` through user systemd and revert the quota-cache routing key/collector CLI modules. Preserve cached metadata/history; existing cooldown and local telemetry ranking remain the fallback. No credentials or provider settings change.
- **Source:** [day log](2026-10/W3/2026-10-13.md), session `01a1356b`; owner explicitly requested implementation after D-005.
