# Explorer model research — 2026-10-17

Status: researched proposal, not an owner selection or runtime change. No inference calls or account quota refreshes.

## Workload and recommendation
Read-only code discovery, exact file/line evidence, real call paths, consumers and explicit unknowns. Search depth (quick/medium/very thorough) is independent of model reasoning effort. Use targeted searches and reads; do not substitute a large context dump for navigation.

Proposed default: GPT-6 Luna high. Same-tier alternative/fallback: Claude Haiku 5.5 medium. Short, tightly bounded lookup candidates: Luna low/medium and Haiku low, pending evidence. Longer Haiku explorations: high. Gemini 3.8 Flash low is a third-provider candidate for fast bounded scans; medium for multi-step exploration. Escalate genuinely ambiguous cross-module tracing to Sol 6.1 medium or Sonnet 5.5 medium, then high only if needed. No proposed xhigh/max default. These effort labels are not equal compute/intelligence budgets across providers.

OpenAI's current subagent guidance explicitly recommends Luna high and includes read-only explorer/code-mapper examples with that configuration. Anthropic recommends Haiku medium for most agentic coding, low for short tool tasks, high for longer agent tasks, warning that low can skip searches/checks in long prompts. Google recommends low for low latency and medium for complex code/agentic work. These establish candidates, not a measured winner on our Explorer workload. Earlier local review benchmarks do not establish Explorer performance.

## API reference prices (USD per million tokens, Standard base)
| Model | Uncached input | Output | Notes |
|---|---:|---:|---|
| GPT-6 Luna | 0.10 | 0.50 | Above 272k input: input/cache 2x, output 1.5x for full request |
| Haiku 5.5 | 0.10 | 0.50 | Up to 100k prompt; above it: 0.50 input / 2.50 output for that request |
| Gemini 3.8 Flash | 0.75 | 3.75 | Introductory through 2026-12-31; 1.50 / 7.50 from 2027-01-01 |
| Sol 6.1 | 2.00 | 10.00 | Escalation candidate |
| Sonnet 5.5 | 2.00 | 10.00 | Escalation candidate |

Cache, service tier, regional and other modifiers are separate. API prices do not specify subscription quota debits; fresh before/after per-account observations are needed. No current available quota or measured Explorer latency is claimed.

## Suggested later evaluation (not launched)
Compare Luna high, Haiku medium and Flash low on identical source-backed lookup and multi-hop tracing cases; include Luna medium and Haiku high on harder cases. Score correct references, consumer coverage, false relationships, justified unknowns, wall time, tools, uncached/cache/output/thinking usage and account quota before/after. Avoid treating raw token count as cost or quota.

## Official sources fetched
- https://learn.chatgpt.com/docs/agent-configuration/subagents — explicit Luna high recommendation and explorer examples.
- https://developers.openai.com/api/docs/models/gpt-6-luna — supported efforts, context and prices/modifiers.
- https://platform.claude.com/docs/en/build-with-claude/effort — Haiku/Sonnet workload-specific effort recommendations.
- https://platform.claude.com/docs/en/about-claude/pricing — Haiku prompt threshold and Sonnet prices.
- https://www.anthropic.com/claude-haiku-5-5 — coding subagent positioning; publisher benchmarks are not Explorer tests.
- https://code.claude.com/docs/en/sub-agents — read-only Explore, custom Haiku override, independent thoroughness levels.
- https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8 — exact model effort and promotional pricing. Generic latest-model now resolves to Gemini 4 Argon; exact 3.8 page used.
- https://developers.openai.com/api/docs/models/gpt-6.1-sol — medium effort and escalation price reference.
