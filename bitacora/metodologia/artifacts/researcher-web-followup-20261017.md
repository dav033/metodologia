# Researcher web evidence follow-up — 2026-10-17

Status: recommendation only; owner has not selected Researcher. No model trial, quota refresh, runtime change, installation, commit or push. This refines the earlier research proposal without rewriting its historical evidence.

## Recommendation

For broad web research, compare Sonnet5.5 medium as the leading default candidate against Sol6.1 medium as the cross-provider alternative. Keep Luna high for narrow official-document/API/version checks. Haiku high is an optional small-model challenger. Gemini3.8 Flash low/medium is an optional third-provider candidate once actual search and citation tooling is verified. These effort assignments are workload hypotheses for local evaluation, not the settings attested by an external leaderboard. No role policy is installed by this note.

## Direct research evaluation evidence

Parallel's own Search Capability Leaderboard, updated October17, reports these composite scores with search:

| Model | Search score |
|---|---:|
| Opus5.5 |75.4|
| Sonnet5.5 |74.1|
| GPT6.1 Sol |70.4|
| Gemini3.8 Flash |65.1|
| Haiku5.5 |62.9|
| GPT6 Luna |61.9|

Scores combine DSQA F1, HLE accuracy and WISER accuracy equally,100 questions each. Each model uses Parallel Search Fast/Extract with fixed tool budgets; reasoning settings/token limits can differ. Costs can omit recovery attempts. This is the evaluator's report, not our native CLI result or a controlled medium/high comparison. It does not establish source-citation faithfulness separately or a subscription-quota ranking. Sonnet's higher score supports its candidacy for synthesis; Luna's narrower official-doc recommendation remains relevant to a different workload. Source: [Parallel leaderboard and methodology](https://parallel.ai/leaderboard).

## Official role/effort guidance

- OpenAI explicitly demonstrates docs_researcher with gpt-6-luna/high and a docs MCP. It positions gpt-6.1-sol for ambiguous multi-step work and medium as balancing speed/depth. This supports Luna for bounded documentation retrieval and Sol for harder reasoning, not a Researcher quality ranking. [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).
- Anthropic recommends Sonnet5.5 medium for well-specified agentic tasks, high for harder/longer ones. Haiku5.5 high is recommended for knowledge work and longer tasks; low can skip searches/checks in long prompts. This updates the earlier optional Haiku-medium hypothesis. [Effort](https://platform.claude.com/docs/en/build-with-claude/effort).
- Anthropic's June2025 research-system result uses Opus4 lead/Sonnet4 workers; its90.2% improvement is a system comparison, not proof for Sonnet5.5 medium. [Historical research architecture](https://www.anthropic.com/engineering/multi-agent-research-system).
- Google documents real-time Search grounding with citations for Gemini3.8 Flash. Low targets latency; medium is recommended for complex agentic tasks. API capability does not prove grounding is available through our Antigravity CLI harness. [Search grounding](https://ai.google.dev/gemini-api/docs/google-search), [exact-model reasoning guidance](https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8).

## Limits and next action

Public research scores do not attest our requested effort, CLI tools, accounts, latency, tokens, invoice costs or subscription headroom. Implementation/Explorer results remain separate. For selection, assess supported claims, valid citations, dates/versions, contradictory sources and justified unknowns. A future local pilot needs separately approved cases/call cap; none is launched here.

Sources above were searched and opened in this session. The Sonnet5.5 launch article and Gemini3.8 model card were also opened; neither was used to infer a native Researcher score. Primary evaluator model pages opened: [Sonnet](https://parallel.ai/leaderboard/claude-sonnet-5-5), [Sol](https://parallel.ai/leaderboard/gpt-6-1-sol), [Luna](https://parallel.ai/leaderboard/gpt-6-luna), [Haiku](https://parallel.ai/leaderboard/claude-haiku-5-5), [Gemini](https://parallel.ai/leaderboard/gemini-3-8-flash).
