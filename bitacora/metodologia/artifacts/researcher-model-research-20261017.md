# Researcher model proposal — 2026-10-17

Status: proposal for owner consideration. No Researcher selection, benchmark call, runtime/configuration change, quota refresh, commit or push was performed. D-065 records the separately approved Explorer choice.

## Recommendation and reasoning

Propose GPT-6 Luna **high** as the starting candidate for bounded documentation research: confirm APIs, versions, options and source-backed facts. Compare GPT-6.1 Sol **medium** and Claude Sonnet 5.5 **medium** for synthesis across conflicting sources, version migrations and decisions with several interacting constraints. This is a workload hypothesis, not a measured Researcher ranking or an automatic escalation rule. Sol comparisons must use `codex-2` by owner instruction; no new account is selected for the other candidates.

Official OpenAI subagent guidance actually includes a `docs_researcher` configured with Luna high and a docs MCP. It distinguishes narrow/repeatable tasks from demanding multi-step reasoning, for which it suggests Sol. Its `medium` guidance balances speed and depth. This supports the candidate split, not demonstrated performance on our web Researcher role. [S1]

Anthropic describes Sonnet 5.5 as balancing speed and intelligence and recommends medium for well-specified agentic workflows, high for harder/longer work. Haiku medium remains an optional cost challenger: its exclusion from Explorer is not a ban on considering it for another role. No new Haiku call is proposed in the initial core comparison. [S3, S4]

Keep Gemini 3.8 Flash low as an optional third-provider candidate, not the initial recommendation. Its low setting targets latency and medium targets complex agentic work. The local Explorer integration had permissions/telemetry incidents and a repaired-lane format failure; those observations justify checking the harness before any Researcher trial, not claiming inferior research quality. Do not silently substitute the newer Gemini model behind a generic latest-model page. [S5, S6]

Astra high and Opus xhigh are already the selected Planner policy. There is no Researcher evidence here that warrants their cost/effort as routine starting candidates. The labels medium/high are not equal compute budgets across vendors.

## Comparable candidates (not selected)

| Candidate | Proposed research workload | Quality / speed uncertainty |
|---|---|---|
| GPT-6 Luna high | Bounded official-document lookup and source extraction | Explicit official docs-researcher example; cross-source synthesis unmeasured |
| GPT-6.1 Sol medium | Ambiguous multi-source synthesis and version-specific tradeoffs | Official demanding-agent positioning; no local Researcher result |
| Claude Sonnet 5.5 medium | Alternative synthesis candidate and existing Claude role baseline | Medium is an explicit proposal; existing local Claude effort is not pinned in the role |
| Claude Haiku 5.5 medium (optional) | Short extraction / cost challenger | Long-context surcharge and tool iteration can erase per-token savings |
| Gemini 3.8 Flash low (optional) | Bounded third-provider research | Native search/tool availability under Antigravity must be verified; local incidents are not Researcher scores |

No measured Researcher latency, cost per successful task or quota per task is available. Explorer and reviewer results must not be relabeled as Researcher measurements.

## API reference prices

USD per million tokens, Standard base/global rates checked on 2026-10-17. These are reference rates, not subscription charges or a subscription-quota conversion. [S2, S3, S6]

| Model | Uncached input | Cache read | Output |
|---|---:|---:|---:|
| Luna | 0.10 short / 0.20 long | 0.01 / 0.02 | 0.50 / 0.75 |
| Sol 6.1 | 2.00 short / 4.00 long | 0.10 / 0.20 | 10.00 / 15.00 |
| Sonnet 5.5 | 2.00 | 0.10 | 10.00 |
| Haiku 5.5 | 0.10 at <=100k / 0.50 above | 0.01 / 0.05 | 0.50 / 2.50 |
| Gemini 3.8 Flash | 0.75 | 0.075 | 3.75 |

Haiku's threshold counts cached input too and is applied per request. Gemini rates are introductory through 2026-12-31; from 2027-01-01 the listed token rates double. Cache writes, storage, regional/service-tier modifiers and tools are additional where applicable. OpenAI's pricing page has several service-tier tables; the first Standard table supplies the base rates above, not the cheaper Batch/Flex rows. Exact OpenAI long-context threshold applicability was not independently re-established here; avoid pricing a long task from an aggregate token total.

API web search also costs money: OpenAI and Claude list $10/1,000 searches/calls plus the content tokens; Gemini lists 5,000 shared free search requests monthly then $14/1,000 individual search queries. These APIs and charging units differ. They do not establish how Codex, Claude Code or Antigravity subscription tools are charged. [S2, S3, S6]

## Quota by account: cached observations only

`bitacora.py usage show` was read without polling, authenticating or launching a model. Values below are stored used percentages, not verified current remaining capacity. Current OpenAI documentation says model, task complexity, context, reasoning, retrieval, tool use and caching affect usage; API dollars cannot supply a cross-provider quota exchange rate. [S7]

| Profile | Cached status | Observation UTC | 5h used % | 7d used % |
| claude | http_401 | 2026-10-17T03:00:19.944703+00:00 | 0.0 | 99.0 |
| codex | app_server_unavailable | 2026-10-16T03:33:47.160660+00:00 | 21.0 | 37.0 |
| claude-personal | http_401 | 2026-10-17T03:00:19.944703+00:00 | 0.0 | 99.0 |
| claude-work | ok | 2026-10-17T15:00:36.576194+00:00 | 28.0 | 91.0 |
| codex-1 | app_server_unavailable | 2026-10-16T03:33:47.160660+00:00 | 21.0 | 37.0 |
| codex-luis | app_server_unavailable | 2026-10-16T03:33:48.167785+00:00 | 10.0 | 25.0 |
| codex-2 | app_server_unavailable | unknown | unknown | unknown |

`claude` and `claude-personal`, and `codex` and `codex-1`, are aliases in the inspected registry context; do not add their apparent capacities. `codex-2` has no successful observation in this cache. Antigravity is absent from this collector output, which does not prove zero quota or account absence. Claude Work's successful observation is historical, not proof of availability now. No quota-aware winner can be named from this snapshot. A later authorized comparison should obtain fresh before/after observations per effective account; unavailable or coarse deltas stay unknown, especially when the account has concurrent use.

## Effective configuration inspected

- `skill/agents/researcher.md`: Claude `model: sonnet`; Codex `codex_effort: medium`. Tools include web search/fetch and note writing; no project-code edits.
- Checked `/home/david/.claude/agents/researcher.md`: `model: sonnet`, no explicit effort. The alias is not an attestation of the exact model returned by a future call.
- Checked `/home/david/.codex-luis/agents/researcher.toml`: medium effort, no explicit model; runtime/parent selection governs the actual model.
- `skill/scripts/install_agents.py:generated_codex` does not emit an explicit model from the source frontmatter. Existing `bt_agents.py` research routes use the generic builder ladder, not this proposed role policy.
- Explorer source/checked installs retain Claude Haiku / Codex low; D-065 does not install its chosen models. Planner remains caller-selected. D-063/D-064 are documented selections, not proof of runtime enforcement.

## Suggested next comparison, subject to separate approval

First compare Luna high, Sol medium and Sonnet medium on the same research tasks, including straightforward version lookup and harder reconciliation of contradictory/versioned sources. Use frozen source documents for content comparison, plus a separately reported live-search/tool check so changing pages and search results are not confused with reasoning quality. Pin exact model, effort, CLI/tool version and effective account before each lane; use `codex-2` for Sol. No exact run count, budget or launch is approved by this note.

Assess source support for every material claim, correct version/date, genuine contradictions, justified unknowns, recommendation quality and completion. Evaluate note-file and final-summary contracts separately. Measure wall time, tool calls, cached/uncached input, cache writes, output/thinking and per-account quota observations. Include failed/repair attempts in operational cost and preserve missing telemetry. Any fixed caps and runtime tool permissions belong in the concrete protocol presented before launch.

Remaining role policies: Researcher (this proposal), Implementer, Runner and Antagonist. P-110 experimental closure remains separate; no completed Explorer calls were repeated.

## Official sources opened

- [S1] https://learn.chatgpt.com/docs/agent-configuration/subagents — model/effort guidance and literal docs-researcher example.
- [S2] https://developers.openai.com/api/docs/pricing ; https://developers.openai.com/api/docs/models/gpt-6-luna ; https://developers.openai.com/api/docs/models/gpt-6.1-sol — Standard/long-context rates and tool charges.
- [S3] https://platform.claude.com/docs/en/about-claude/pricing — token/cache rates, Haiku threshold, search and fetch charges.
- [S4] https://platform.claude.com/docs/en/build-with-claude/effort — Sonnet/Haiku effort guidance; labels vary by model.
- [S5] https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8 — exact-model thinking levels, not generic latest alias.
- [S6] https://ai.google.dev/gemini-api/docs/pricing — Flash introductory rates and search grounding charges.
- [S7] https://learn.chatgpt.com/docs/pricing — subscription usage depends on workload/model/tool/context, not message/token count alone.
