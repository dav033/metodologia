# Planner candidates: Opus 5.5, GPT-6 Astra and GPT-6.1 Sol

Research date: 2026-10-17. Read-only web research; no provider inference, account-quota refresh, model selection or runtime change. Prices are USD, API Standard processing, per million tokens. Verify rates again before spending. This is separate from D-063's selected reviewers and does not expand the approved REQ-024 benchmark.

## API rates and capacity

| Model | Uncached input | Cache read | Cache write | Output | Context / max output |
|---|---:|---:|---:|---:|---|
| GPT-6.1 Sol | $2 | $0.10 | $2.50 | $10 | 1,050,000 / 128,000 |
| Claude Opus 5.5 | $4 | $0.20 | $5 (5min), $8 (1h) | $20 | 1,000,000 / 128,000 |
| GPT-6 Astra | $10 | $1 | $12.50 | $50 | 1,050,000 / 128,000 |

Sources: [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol), [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra), [Opus specifications](https://platform.claude.com/docs/en/models/opus-5-5/overview), [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).

For identical uncached input/output counts, Opus's rates are twice Sol's; Astra's are five times Sol's and 2.5 times Opus's. Cache-read ratios differ. Illustrative arithmetic only: 100,000 uncached input plus 20,000 total billable output tokens, with no cache writes or other surcharges, costs $0.40/$0.80/$2.00 respectively. This is not a measured plan or a subscription-quota forecast.

OpenAI prompts above 272,000 input tokens charge 2x input/cache and 1.5x output for the full request. API Fast is 2x Standard for Astra/Sol; Ultrafast 6x. Opus Fast is $8/$40 input/output. Avoid mixing these modes when comparing model costs. Tool fees and cache writes can add costs.

## What matters for planning

- Opus is documented for long-running agentic coding/knowledge work. Its thinking is always adaptive; default effort is medium. Anthropic explicitly recommends recalibrating effort rather than carrying over settings from earlier Opus versions. [Migration guide](https://platform.claude.com/docs/en/models/opus-5-5/migration-guide).
- OpenAI positions Astra for its most demanding reasoning and Sol as a lower-cost near-Astra option. This is provider positioning, not measured equality on our Planner. [Model selection](https://developers.openai.com/api/docs/guides/model-selection).
- Same effort labels across providers do not equate reasoning-token budgets. Actual plan quality, evidence gathering, coverage, dependencies, interface ownership, uncertainty, verification design and correction passes need measurement. A valid PLAN.json alone does not prove a sound plan.
- OpenAI reasoning tokens are billed as output even when not visible; output ceilings must allow for reasoning. [Reasoning guide](https://developers.openai.com/api/docs/guides/reasoning). Review results from our prior pilots are not evidence of equivalent plan-generation quality.

## Independent high-effort reference

Artificial Analysis Intelligence Index v4.3.2, accessed on the research date:

| Configuration exactly as labeled | Index | API cost per Index task | Output tokens/s | Output across Index |
|---|---:|---:|---:|---:|
| Opus 5.5 high, default fallback | 54 | $1.82 | 83.5 | 53M |
| Astra high | 51 | $1.73 | 52.9 | 26M |
| Sol 6.1 high | 50 | $0.32 | 57.5 | 25M |

Sources: [Opus high](https://artificialanalysis.ai/models/claude-opus-5-5-high), [Astra high](https://artificialanalysis.ai/models/gpt-6-astra-high), [Sol high](https://artificialanalysis.ai/models/gpt-6-1-sol-high).

Opus is explicitly measured with the evaluator's default fallback protocol; do not label this a strict single-model/no-fallback controlled comparison. These aggregate evaluations are not our PLAN.json workflow. Scores are not probabilities of success, and output throughput excludes much of end-to-end reasoning/tool latency. The published task-cost ordering differs from price-per-token ordering because token consumption differs. Max-effort figures (such as Opus58/Astra53) must not be silently substituted into this high-effort table.

## Subscription and quota

Codex Standard paid-credit rates per million tokens: Astra250 input /25 cached /1,250 output; Sol50 /2.5 /250. There is no separate cache-write charge in Codex credit billing. Included subscription allowance is not determined by those rates alone. [Official Codex pricing](https://learn.chatgpt.com/docs/pricing).

Claude/Claude Code share account usage windows; use depends on context, task complexity, model and selected effort. API rates cannot establish how many plans a Claude subscription supports, or predict a precise before/after percentage. [Claude subscription usage](https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), [usage factors](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work).

## Proposal, not an applied decision

Prioritize a matched Opus-versus-Sol planning comparison: Opus is the local qualitative reference and Sol the economical challenger. Astra is a useful third capability reference, but neither its API price nor its high-effort aggregate score justifies declaring it a superior Planner. Hold requirement, repository snapshot, Planner instructions, tools, service speed and output contract constant; record cache/input/output/thinking, tool turns, elapsed time, quota and grounded plan quality. No additional model execution is authorized or performed by this research-only request.
