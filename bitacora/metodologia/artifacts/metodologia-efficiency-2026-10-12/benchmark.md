# REQ-004 — Additional context-efficiency benchmarks

## Adopted change
Added only the tested selective-context policy to SKILL.md: references for the next action, relevant sections with prerequisites, no repeated unchanged reads, batching independent queries, bounded noisy output with failure/status preservation, and exact relevant contracts/code before edits or approval. No root sections removed, no runtime/tool/model/config changes, and no weaker checks or approval gates.

## Research and candidates
The prior pilot suggested that redundant reads and repeated context mattered more than terse prose. Primary sources describe just-in-time context retrieval and focused tools:
- [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic effective tools](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [OpenAI usage accounting](https://developers.openai.com/api/docs/guides/agents-api/observability)

Three frozen variants were screened twice each: X current baseline, Y selective-context policy, Z compact entrypoint plus that policy. Z moved startup/HQ/helper details into a conditional reference while preserving them. Neutral labels and identical evaluation prompts were used; only package paths differed. Same default role/model/effort in fresh contexts; three workers maximum. Root startup/task read was standardized for all. Protocol, original packages, tasks, criteria, replies and raw counters are retained.

## Screening results — median of two runs per variant
| Runtime measure | Current | Selective (adopted) | Compact (rejected) |
|---|---:|---:|---:|
| Input | 158,689.5 | 149,586 | 159,353.5 |
| Cached input subset | 134,400 | 132,096 | 127,616 |
| Uncached input | 24,289.5 | 17,490 | 31,737.5 |
| Output, including reasoning/tool arguments | 1,377.5 | 1,603.5 | 1,585.5 |
| Reasoning output subset | 17.5 | 27.5 | 12.5 |
| Total | 160,067 | 151,189.5 | 160,939 |
| Tool calls | 4 | 4 | 4 |

Selective policy: **5.55% fewer total tokens, 5.74% fewer input tokens and 27.99% fewer uncached input tokens**. Output increased **16.41%**. Compact root: total increased 0.54%, and uncached input increased 30.66%; not adopted. Root-file length alone was not predictive of overall efficiency.

All six trials met the 18 predeclared manual criteria. They recovered all three failures scattered through a 1,200-test saved log, kept exit 1 and NOT_RUN fields, retained error text, stopped the interview on request and did not rerun a simulated migration. Exact file reading was real; the underlying tests/deployments were not executed. Some broad reads were truncated and then recovered with focused reads; all final failure evidence was present. Traces retain those inefficient reads rather than hiding them.

## Held-out access-control review
A different task required reading an exact tenant-authorization contract, finding an AND/OR precedence defect and proposing a minimal correction against a 400-test saved log.

| Runtime measure | Current | Selective |
|---|---:|---:|
| Input | 104,357 | 105,212 |
| Cached input subset | 89,472 | 92,544 |
| Uncached input | 14,885 | 12,668 |
| Output | 592 | 643 |
| Total | 104,949 | 105,855 |
| Tool calls | 3 | 3 |

Selective policy used **14.89% less uncached input but 0.86% more total tokens** and 8.61% more output. Cache hit variation can explain the uncached-input difference; it is not proof of less context or lower cost. Both proposals met the nine review criteria and separately passed **6/6 actual deterministic permission-matrix checks** run by the coordinator in an isolated scope after AST validation. The archived product suite was not run. No new permission, global-admin role, project edit or fabricated successful check was introduced.

## Selection and interpretation
Adopt Y because its smaller read set improved both screening repetitions while preserving quality. It avoided rereading whole manuals and reduced context consumed after broad-output truncation. This is a conditional improvement for the tested mixed workload, not universal: the held-out review had no total-token gain. Do not claim the uncached difference as a causal or monetary saving, particularly on the single held-out pair. More output and identical tool-call counts were also observed. Z was retained in the evidence and rejected.

## Verification and limits
- Actual post-completion runtime token counters were collected for all eight agents; accumulated records reconcile, cached input is not double-counted, and model/effort match.
- Collector behavioral tests: 5/5 pass (real counters, duplicates, incomplete runs, invalid totals, unrelated sessions).
- Manual quality: 18/18 per screening run; 9/9 per held-out run. This is coordinator grading, not a blinded independent judge or statistical estimate.
- Held-out proposed functions: both 6/6 deterministic permission cases pass. No tests in the real project were run.
- Source integration matches the exact measured Y policy. All original reference bodies and existing local work remain intact.
- Small sample: two runs per candidate and one held-out pair. Shared harness/style/tool metadata, scheduling, cache warmth and model variability remain confounders. Candidates are bundles, so savings cannot be attributed individually to batching, section retrieval or reuse.
- RTK absent; no binary-output compression or billing-price experiment occurred. No paid external eval CLI, model/effort changes, security/global configuration changes, commits or pushes.

Independent final spec and standards reviews approved the incremental change without findings; see `reviews.md`.

## Benchmark overhead
The eight participant runs consumed 1,155,195 total tokens (including cached repeated context), of which 10,368 were output. Coordinator/research/review overhead is additional and is not included. Benchmark spend must not be mistaken for tokens saved in production.

## Evidence
`metrics.json` contains per-run counters, read traces and answers; `summary.json` holds medians; `quality.json` and the two rubrics record grading. `packages/` preserves every tested variant; `fixtures/` and `heldout/` preserve inputs. `collect.py` and `test_collect.py` provide the collector and its behavioral tests. The collector's session directory is pinned to this experiment date and requires adjustment for a new run.
