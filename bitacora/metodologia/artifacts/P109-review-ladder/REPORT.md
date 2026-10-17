# Five-model synthetic plan-review ladder

## Protocol

The owner authorized five additional reviews of increasing complexity, first with three models and then with Haiku and Luna added at max effort. Each case has identical user input across models, a predeclared hidden defect oracle, correct baseline guarantees as decoys, at most eight findings and 900 visible words. Five cases contain 20 independent planted defects. The oracle was frozen before provider calls; its SHA-256 is `71beefc22baf08191b47165dc10bc36d22a2ba104f74d58bc37f9f82574d32dd`.

This is a self-contained synthetic reviewer pilot outside REQ-024's formal corpus, manifest and 66 T19 review records. Its C1–C5 labels are local to this pilot. No repository exploration or implementation was requested. One run per cell cannot establish general model superiority. Adjudication is an explicit, non-blind coordinator mapping; complete final responses and mappings are provided for audit.

Original routes use high effort; the two additional routes use max as requested. CLI versions: Codex 0.163.0, Claude Code 2.1.301, Antigravity 1.4.0. Codex runs on Codex-2; both Claude models on Claude Work; Gemini on the single Antigravity account. Calls on the same account do not overlap within this experiment. No fallback model was configured.

## Increasing complexity

| Case | Level | Topic | Predeclared defects |
|---|---:|---|---:|
| C1 | 1 | Product filter coverage | 2 |
| C2 | 2 | Dependency and verification safety | 3 |
| C3 | 3 | Tenant migration and rollback | 4 |
| C4 | 4 | Payments under retries and crashes | 5 |
| C5 | 5 | M1/M2 durable account routing | 6 |

## Defect coverage and time per case

Each cell shows unique planted defects found / expected, then CLI wall seconds. Asterisk means manual recovery was required and the machine output contract failed.

| Case | GPT-6.1 Sol high | Claude Sonnet 5.5 high | Gemini 3.8 Flash high | GPT-6 Luna max | Claude Haiku 5.5 max |
|---|---|---|---|---|---|
| C1 | 2/2 · 13.4s | 2/2 · 16.8s | 2/2 · 38.1s | 2/2 · 10.8s | 2/2 · 115.2s |
| C2 | 3/3 · 14.5s | 3/3 · 21.6s | 3/3 · 32.4s | 3/3 · 14.5s | 3/3 · 127.8s |
| C3 | 4/4 · 22.0s | 4/4 · 23.1s | 4/4 · 80.5s | 4/4 · 23.9s | 4/4 · 201.1s |
| C4 | 5/5 · 31.9s | 5/5 · 24.2s | 5/5 · 46.0s | 5/5 · 22.0s | 5/5 · 221.6s |
| C5 | 6/6 · 28.5s | 6/6 · 29.7s* | 6/6 · 39.4s | 6/6 · 30.6s | 6/6 · 227.5s |

## Aggregate measured usage

Time is the sum of five independent CLI calls, including startup/provider latency; it is not the elapsed duration of the whole parallel experiment. Input includes cache reads/creation. Output includes thinking, so thinking is a subset and must not be added again. Provider tokenizers and hidden system contexts differ; these are measurements of the local model/CLI/account routes.

| Model | Defects | Usable JSON | Input | Cache-read subset | Output | Thinking subset | Total | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GPT-6.1 Sol high | 20/20 | 5/5 | 76,902 | 61,440 | 4,576 | 1,025 | 81,478 | 110.3 |
| Claude Sonnet 5.5 high | 20/20 | 4/5 | 25,981 | 8,310 | 14,864 | 5,090 | 40,845 | 115.4 |
| Gemini 3.8 Flash high | 20/20 | 5/5 | 63,222 | 0 | 30,572 | 26,603 | 93,794 | 236.4 |
| GPT-6 Luna max | 20/20 | 5/5 | 74,406 | 58,240 | 11,248 | 8,264 | 85,654 | 101.8 |
| Claude Haiku 5.5 max | 20/20 | 5/5 | 29,865 | 9,768 | 224,598 | 215,254 | 254,463 | 893.1 |

## Focus and efficiency

Duplicate test-coverage restatements count once with the underlying defect. Additional concerns without enough evidence are tracked as unconfirmed, not automatically declared false positives. Precision/F1 bounds are conservative/optimistic adjudication bounds, not statistical confidence intervals.

| Model | Duplicate findings | Unconfirmed concerns | Precision bounds | F1 bounds | Tokens / planted defect | Seconds / planted defect |
|---|---:|---:|---:|---:|---:|---:|
| GPT-6.1 Sol high | 0 | 0 | 100.0–100% | 100.0–100.0% | 4,073.9 | 5.52 |
| Claude Sonnet 5.5 high | 3 | 2 | 90.9–100% | 95.2–100.0% | 2,042.2 | 5.77 |
| Gemini 3.8 Flash high | 5 | 1 | 95.2–100% | 97.6–100.0% | 4,689.7 | 11.82 |
| GPT-6 Luna max | 2 | 1 | 95.2–100% | 97.6–100.0% | 4,282.7 | 5.09 |
| Claude Haiku 5.5 max | 5 | 5 | 80.0–100% | 88.9–100.0% | 12,723.1 | 44.65 |

## Interpretation

All five routes found all 20 planted roots. Sol high was the most focused: no separate duplicate/unconfirmed findings, the fewest output tokens, and five usable outputs. Luna max was 7.8% faster in summed time, with 2.46x Sol's output tokens. Sonnet had the smallest reported total including cache, but its C5 response broke both JSON-only and 900-word requirements. Gemini took 2.14x Sol's time. Haiku max took 8.1x Sol's time and generated 49.08x its output tokens, with no additional planted-root coverage; 215,254 of its 224,598 output tokens were thinking. This does not establish general capability rankings or dollar/subscription cost equivalence.

## Per-model account quota observations

Percentages are USED, not remaining. Each row uses the reading just before the first model call and immediately after its last call. Readings are coarse, can lag, and may include other account activity. The two excluded alias calls occurred between the Sonnet and Haiku batches; their delayed reporting may affect Claude account deltas even though their tokens/time are excluded from the model table. Reset changes must be inspected before attributing a delta.

| Model | Account | 5h used before → after | 7d used before → after | Read status |
|---|---|---:|---:|---|
| GPT-6.1 Sol high | codex-2 | 1.0 → 2.0% | 0.0 → 0.0% | ok / ok |
| Claude Sonnet 5.5 high | claude-work | 2.0 → 3.0% | 87.0 → 87.0% | ok / ok |
| Gemini 3.8 Flash high | antigravity | 0.0 → 2.0% | 0.0 → 1.0% | ok / ok |
| GPT-6 Luna max | codex-2 | 2.0 → 2.0% | 0.0 → 0.0% | ok / ok |
| Claude Haiku 5.5 max | claude-work | 5.0 → 6.0% | 87.0 → 87.0% | ok / ok |

Every per-call before/after sample, observation time and reset time is retained in its result JSON. The final delayed account snapshot (more than two minutes after the last call) reports Codex-2 at 2%/0%, Claude Work at 7%/87%, and Antigravity Gemini at 2%/1% used in 5h/7d. In particular, Haiku's last immediate read was 6% but Claude later reported 7%. See `quota-final.json`; unchanged displayed usage does not establish zero consumption.

## Model identity incident and exclusions

Two calls requested the `haiku` alias at max, but assistant metadata reported `claude-sonnet-5-5`. The coordinator was interrupted after the in-flight C2 calls completed; no third alias call occurred. Both attempts are preserved and excluded from Haiku and Sonnet-high scores. The five replacement calls use the full `claude-haiku-5-5` identifier and check effective metadata after each case. This makes 27 actual model calls for 25 target cells. Exact cause of alias resolution remains unconfirmed; no global account settings were changed.

Official model identifier: [Haiku 5.5 overview](https://platform.claude.com/docs/en/models/haiku-5-5/overview). Supported max effort: [Anthropic effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort). Claude assistant metadata confirms the effective Haiku/Sonnet model IDs. Codex and Gemini record explicit requested IDs; the collector did not retain a provider-confirmed effective ID for them.

## Detailed adjudication notes

- `C1-claude-work.json`: Finding 4 raises missing HTTP-400 translation, but the supplied parser contract does not establish its error signaling or the existing HTTP translation. Track as unconfirmed, not a proven false positive or an additional proven defect.
- `C2-claude-work.json`: The cycle is proven. The extra claim that snapshot-after-DTO is intrinsically semantically wrong is not established; it is not needed to establish the cycle.
- `C3-claude-work.json`: Finding 5 proposes pre-cutover validation ordering. The mission does not explicitly require T6 before T5, and T5 has its own verification period; retain as an unconfirmed planning concern.
- `C3-antigravity.json`: Findings 2/4/6 restate coverage for existing roots. Finding 8 is the same unconfirmed pre-cutover gate concern as Sonnet. The title says unvalidated tenant, but the evidence correctly distinguishes UUID validation from missing authorization.
- `C5-claude-work.json`: Output contains two JSON documents plus prose and 1105 whitespace-delimited words. Content recovery is for manual scoring only, never a successful machine contract. Finding 7 restates verification coverage and adds an unproven task-order concern. Its claim that reservations can change while BEGIN IMMEDIATE holds the write transaction is incorrect under the stated database locking; the network-in-transaction defect remains correct.
- `C5-antigravity.json`: All six roots are correct. The stale-quota scenario overstates execution impact: baseline M1 correctly revalidates at dispatch, so the evidence establishes a bad M2 recommendation, not that a depleted-provider call necessarily occurs.
- `C1-claude-work-haiku55.json`: Findings 3/4 restate tests for the two roots. Finding 5 assumes the named tenant isolation test has no foreign-tenant fixture, which is not established. Finding 6 repeats coverage and treats unspecified HTTP assertions as missing; the invalid-input tests are already named. Track these caveats without inventing additional proven defects.
- `C2-claude-work-haiku55.json`: Finding 4 raises unspecified API deployment ordering. The task ordering and staged deployment facts do not prove the API will ship before the database migration; track as an unconfirmed plan concern. Sonnet raised the same point as an uncertainty, rather than as a finding.
- `C3-claude-work-haiku55.json`: Finding 5 raises the same unconfirmed T6-before-cutover concern as Sonnet/Gemini, adding a rollback rehearsal proposal. The predeclared defects already account for the broken rollback. The optional trigger/canary uncertainties are not counted as findings.
- `C4-claude-work-haiku55.json`: Finding 6 repeats coverage for seeded roots. Finding 7 raises rollback draining and the 72-hour retry boundary; whether the disabled new worker includes the outbox dispatcher, or jobs will be retried after 72h, is not specified. Retain as an unconfirmed concern, not a false positive. The generation finding also proposes provider-path ordering beyond the demonstrated finalization defect.
- `C5-codex-2-luna.json`: Finding 6 correctly observes that the T5 revalidation list does not explicitly name the required budget check. This is a useful additional traceability concern outside the predeclared oracle. As with the HTTP-400 translation concern, omitted plan text does not prove an existing runtime guard is absent; retain separately from the 20 proven seeded defects, without silently expanding the frozen denominator or declaring the observation false.
- `C5-claude-work-haiku55.json`: All six planted roots are found. Finding 7 duplicates their test coverage; finding 8 is the same budget traceability concern as Luna, with an explicit uncertainty about budget versus quota. Two auxiliary claims are incorrect: the contract does define fresh quota, and the baseline explicitly guarantees v1 preservation. The overwritten startup map is defective, but claiming it necessarily mutates v1 evidence contradicts that baseline.

## Evidence and remaining work

`cases.json` contains requirements, plans and the frozen oracle; model prompts use only each case's `input`, never its oracle. `protocol.json`, the two additional protocols and `runtime-versions.json` define invocation conditions. Result JSONs retain final answers, reported usage, hashes, elapsed time and quota, excluding private reasoning text/raw CLI streams. `adjudication.json` and `adjudicate.py` provide the exact manual mapping and calculations. `run.py` and `run_additional.py` reproduce missing cells without rerunning existing records.

No product code, Scheduler lifecycle, formal benchmark manifest, reviewer pair, approval state or frozen plan changed. P-109 remains open. The exact T17 Claude Planner isolation check and formal T17–T22 work remain separate. No general quality-parity claim follows from these seeded cases.
