# Runner model research — 2026-10-17

Status: research proposal only. No model selection, native trial, account switch or runtime configuration change.

## Workload and existing configuration

`skill/agents/runner.md` executes specified commands, preserves real exit codes, extracts failures from noisy output and reports blocked or hung commands. It must not fix code or install dependencies without a brief. Its existing metadata says Claude `haiku` and Codex effort `low`; these are existing settings, not a newly approved selection or an attested version.

## Official evidence

- [OpenAI subagent guidance](https://learn.chatgpt.com/docs/agent-configuration/subagents), accessed 2026-10-17: GPT-6 Luna targets narrow, repeatable, high-volume agent work. The explicit Luna starting recommendation is high effort; medium balances depth and speed, and low targets straightforward tasks. Higher effort can increase latency and token use. This supports Luna candidacy, not a measured Runner win.
- [Anthropic Haiku product page](https://www.anthropic.com/claude/haiku), accessed 2026-10-17: Haiku 5.5 targets fast subagent and summarization work. Marketing examples are not our command-runner evaluation.
- [Anthropic Haiku prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5), accessed 2026-10-17: medium is the default; low suits short tool tasks but has greater omission/early-stop risk in long prompts. The guide specifically documents skipped verification after coding at low/medium. That is a related risk, not evidence that our Runner failed. Keep explicit execution/evidence requirements; do not import the guide's dependency-install permission into this role.
- [Anthropic effort reference](https://platform.claude.com/docs/en/build-with-claude/effort), accessed 2026-10-17, independently confirms the Haiku effort guidance.

## Recommendation and uncertainty

Provisional first candidate: **Luna high**, following OpenAI's starting guidance and matching the role's narrow scope. Compare **Luna medium** as an efficiency challenger and **Haiku 5.5 medium** as the cross-provider alternative. Haiku low could be a later efficiency experiment; neither provider's guidance proves it meets this role's reporting contract. Sonnet medium is a possible future escalation candidate if the small models fail, not a selected fallback.

No matched Runner benchmark was established in the sources inspected. The completed Implementer/Researcher pilots do not establish Runner quality, relative latency or subscription cost. No price or quota equivalence is inferred from tokens. Runner-specific latency, token totals, effective identities and available-account conditions remain unmeasured.

## Proposed validation, not authorized execution

If the owner requests a pilot, use the same frozen six cases for the three configurations (18 native calls), without retries or repairs. Cases: successful command with warnings; failing command printing misleading PASS text; multiple test failures with repeated diagnostics; long log with failures in the middle; timeout plus a command that cannot start; multi-command/pipeline failures with explicit per-command status.

Grade against deterministic process evidence: required commands actually invoked, real exit status, exact failure identification, no fabricated PASS, no unauthorized edits/installs, honest timeout/missing-dependency disclosure, concise summaries and retained raw logs. Freeze the shell/pipeline contract explicitly; do not grade an unspecified pipefail assumption. Distinguish total command wall time from model overhead, and compare equal case coverage. Save missing usage or model/effort attestation as unknown.

Research is complete; choosing a model, authorizing this matrix, pinning accounts and applying runtime policy remain separate actions.
